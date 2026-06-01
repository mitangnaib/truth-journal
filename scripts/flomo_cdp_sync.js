#!/usr/bin/env node
// flomo_cdp_sync.js - 通过 Chrome CDP 读取 Flomo IndexedDB 数据
// 用法: node flomo_cdp_sync.js [--port 9222] [--output stdout|json|obsidian] [--days 7] [--auto-start]
//
// 前置条件:
//   1. Chrome 以 --remote-debugging-port=9222 + Debug profile 启动
//   2. Flomo 已在 Debug Chrome 中打开并登录
//   3. Node.js + ws 包可用
//
// ⚠️ Chrome 148+ 默认 profile 无法开启 CDP！必须用 Debug profile
// ⚠️ CDP awaitPromise 在 Chrome 148 不可靠，用回调式+轮询

const WebSocket = require('ws');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

const args = process.argv.slice(2);
const PORT = parseInt(args[args.indexOf('--port') + 1]) || 9222;
const OUTPUT = args[args.indexOf('--output') + 1] || 'json';
const DAYS = parseInt(args[args.indexOf('--days') + 1]) || 7;
const AUTO_START = args.includes('--auto-start');
const OUT_FILE = path.join(process.env.TEMP || '/tmp', 'flomo_memos.json');

// ===== 可配置路径（通过环境变量或直接修改）=====
const OBSIDIAN_VAULT = process.env.OBSIDIAN_VAULT || 'D:\\ObsidianVault';
const CHROME_EXE = process.env.CHROME_EXE || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const DEBUG_PROFILE = process.env.DEBUG_PROFILE ||
    path.join(process.env.LOCALAPPDATA || '', 'Google', 'Chrome', 'User Data', 'Debug');

// 知行转化：洞察类标签 & 行动标签（可自定义）
const INSIGHT_TAGS = (process.env.INSIGHT_TAGS || '输入/金句,金句,输入/启发,启发,洞察').split(',');
const ACTION_TAG = process.env.ACTION_TAG || '知行转化';

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function waitForCDP(port, maxRetries = 15, intervalMs = 1000) {
    for (let i = 0; i < maxRetries; i++) {
        try {
            return await (await fetch(`http://127.0.0.1:${port}/json/version`)).json();
        } catch (e) {
            await sleep(intervalMs);
        }
    }
    return null;
}

async function main() {
    // 1. Try connecting to existing Chrome CDP
    let tabs;
    try {
        tabs = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json();
    } catch (e) {
        if (AUTO_START) {
            console.error('🔌 CDP 未就绪，自动启动 Debug Chrome...');
            if (!DEBUG_PROFILE) {
                console.error('❌ 无法确定 Debug Profile 路径，请设置 DEBUG_PROFILE 环境变量');
                process.exit(1);
            }
            exec(`start "" "${CHROME_EXE}" --remote-debugging-port=${PORT} --user-data-dir="${DEBUG_PROFILE}"`);
            const ver = await waitForCDP(PORT);
            if (!ver) { console.error('❌ Chrome 启动超时'); process.exit(1); }
            console.error('✅ Chrome CDP 就绪:', ver.Browser);
            await sleep(2000);
            tabs = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json();
        } else {
            console.error(`❌ 无法连接 CDP (端口 ${PORT})`);
            console.error('用法: node flomo_cdp_sync.js --auto-start --days 7 --output obsidian');
            process.exit(1);
        }
    }

    // Find flomo tab
    let tab = tabs.find(t => t.url.includes('flomoapp.com'));
    if (!tab) {
        console.error('📭 没有 Flomo 标签页，请先在 Debug Chrome 中打开 Flomo 并登录');
        process.exit(1);
    }

    console.error(`🔗 连接: ${tab.url}`);

    // 2. Build inject code for IndexedDB read
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - DAYS);
    const cutoffStr = cutoffDate.toISOString().replace('T', ' ').substring(0, 19);

    const injectCode = `(function(){
        window.__FLS = {done:false};
        var r = indexedDB.open('flomo', 39);
        r.onerror = function(){ window.__FLS = {done:true, err:'IDB open err: '+r.error}; };
        r.onsuccess = function(e){
            var db = e.target.result;
            var names = Array.from(db.objectStoreNames);
            if(!names.includes('memos')){
                window.__FLS = {done:true, err:'no memos store, have: '+names.join(',')};
                return;
            }
            var tx = db.transaction('memos', 'readonly');
            var store = tx.objectStore('memos');
            var req = store.getAll();
            req.onsuccess = function(){
                var all = req.result;
                var memos = [];
                for(var i=0; i<all.length; i++){
                    var m = all[i];
                    if(m.is_deleted) continue;
                    var ts = m.created_at || '';
                    if(ts < '${cutoffStr}') continue;
                    memos.push({
                        content: m.content,
                        tags: m.tags || m.tag_ids || [],
                        created_at: m.created_at,
                        slug: m.slug,
                        is_deleted: !!m.is_deleted,
                        source: m.source || ''
                    });
                }
                window.__FLS = {done:true, data:JSON.stringify(memos), count:memos.length, total:all.length};
            };
            req.onerror = function(){ window.__FLS = {done:true, err:'getAll err'}; };
        };
    })(); 'ok'`;

    // 3. Connect WebSocket and inject
    let msgId = 0;
    const idMap = new Map();

    function sendTracked(method, params, tag) {
        const id = ++msgId;
        idMap.set(id, tag);
        ws.send(JSON.stringify({ id, method, params }));
        return id;
    }

    const ws = new WebSocket(tab.webSocketDebuggerUrl);
    let injected = false;

    return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
            console.error('⏰ 超时（30秒）');
            ws.close();
            reject(new Error('timeout'));
        }, 30000);

        ws.on('open', () => {
            ws.send(JSON.stringify({ id: ++msgId, method: 'Runtime.enable' }));
        });

        ws.on('message', (raw) => {
            const msg = JSON.parse(raw.toString());

            if (msg.method === 'Runtime.executionContextCreated' && !injected) {
                const ctx = msg.params.context;
                if (ctx.auxData?.type === 'default') {
                    injected = true;
                    console.error('💉 注入 IndexedDB 读取代码...');
                    sendTracked('Runtime.evaluate', {
                        expression: injectCode,
                        contextId: ctx.id,
                        returnByValue: true
                    }, 'inject');
                }
            }

            if (idMap.get(msg.id) === 'inject') {
                idMap.delete(msg.id);
                console.error('⏳ 等待数据...');
                const iv = setInterval(() => {
                    sendTracked('Runtime.evaluate', {
                        expression: `JSON.stringify({done:window.__FLS&&window.__FLS.done, c:window.__FLS&&window.__FLS.count, err:window.__FLS&&window.__FLS.err})`,
                        returnByValue: true
                    }, 'poll');
                }, 800);
                ws._pollInterval = iv;
            }

            if (idMap.get(msg.id) === 'poll') {
                idMap.delete(msg.id);
                try {
                    const val = msg.result?.result?.value;
                    if (!val) return;
                    const fd = JSON.parse(val);
                    if (fd.done) {
                        clearInterval(ws._pollInterval);
                        if (fd.err) {
                            console.error('❌', fd.err);
                            ws.close(); reject(new Error(fd.err));
                        } else if (fd.c > 0) {
                            console.error(`📊 找到 ${fd.c} 条 memo，正在提取...`);
                            sendTracked('Runtime.evaluate', {
                                expression: `window.__FLS.data`,
                                returnByValue: true
                            }, 'fetch');
                        } else {
                            console.error('📭 没有符合条件的 memo');
                            ws.close(); resolve([]);
                        }
                    }
                } catch(e) {}
            }

            if (idMap.get(msg.id) === 'fetch') {
                idMap.delete(msg.id);
                const data = msg.result?.result?.value;
                if (!data) { reject(new Error('fetch empty')); ws.close(); return; }

                clearTimeout(timeout);
                ws.close();

                const memos = JSON.parse(data);

                // ===== 知行转化率统计 =====
                calcConversionRate(memos);

                if (OUTPUT === 'stdout') {
                    process.stdout.write(JSON.stringify(memos, null, 2));
                } else if (OUTPUT === 'json') {
                    fs.writeFileSync(OUT_FILE, JSON.stringify(memos, null, 2), 'utf8');
                    console.error(`✅ ${memos.length} 条 memo → ${OUT_FILE}`);
                } else if (OUTPUT === 'obsidian') {
                    const result = syncToObsidian(memos);
                    console.error(`✅ 同步 ${result.synced} 条，跳过 ${result.skipped} 条 → ${OBSIDIAN_VAULT}`);
                }

                resolve(memos);
            }
        });

        ws.on('error', (err) => { console.error('❌ WS:', err.message); reject(err); });
    });
}

/**
 * 计算知行转化率
 * 洞察类标签 → 后续跟了行动标签的 memo
 */
function calcConversionRate(memos) {
    let insightCount = 0;
    let actionCount = 0;
    const unconvertedMemos = [];

    for (const memo of memos) {
        const tags = memo.tags || [];
        const isInsight = INSIGHT_TAGS.some(t => tags.includes(t));
        const isAction = tags.includes(ACTION_TAG);

        if (isInsight) {
            insightCount++;
            if (isAction) { actionCount++; }
            else { unconvertedMemos.push(memo); }
        }
    }

    const rate = insightCount > 0 ? ((actionCount / insightCount) * 100).toFixed(1) : '100.0';

    console.error('\n═══ 📊 知行转化率 ═══');
    console.error(`  洞察总数：${insightCount}`);
    console.error(`  已转化为行动：${actionCount}`);
    console.error(`  转化率：${rate}%`);

    if (unconvertedMemos.length > 0 && unconvertedMemos.length <= 5) {
        console.error(`\n  ⚠️ 待转化的洞察：`);
        for (const m of unconvertedMemos) {
            const preview = (m.content || '').substring(0, 40).replace(/\n/g, ' ');
            console.error(`    • ${preview}... [${(m.created_at || '').split(' ')[0]}]`);
        }
    } else if (unconvertedMemos.length > 5) {
        console.error(`\n  ⚠️ ${unconvertedMemos.length} 条洞察待转化为行动`);
    }
    console.error('═════════════════\n');
}

function cleanHtml(text) {
    return text.replace(/<p>/g, '\n').replace(/<\/p>/g, '').replace(/<br\s*\/?>/g, '\n')
        .replace(/<[^>]+>/g, '').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').trim();
}

function syncToObsidian(memos) {
    let synced = 0, skipped = 0;
    const tagMapping = {
        '日志/事实': '日记', '日志': '日记', '事实': '日记',
        '输入/金句': '金句', '金句': '金句',
        '输入/启发': '启发', '启发': '启发',
        '睡眠': '睡眠'
    };

    for (const memo of memos) {
        if (memo.is_deleted) { skipped++; continue; }
        const tags = memo.tags || [];
        if (tags.includes('私密')) { skipped++; continue; }

        let category = '日记';
        for (const tag of tags) { if (tagMapping[tag]) { category = tagMapping[tag]; break; } }

        const date = (memo.created_at || '').split(' ')[0] || new Date().toISOString().split('T')[0];
        const content = cleanHtml(memo.content || '');
        const time = (memo.created_at || '').split(' ')[1] || '';

        let targetDir, filePath, fileContent;

        if (category === '日记') {
            targetDir = path.join(OBSIDIAN_VAULT, '日记', date.substring(0, 4));
            filePath = path.join(targetDir, `${date}.md`);
            fileContent = `### ${time}\n\n${content}\n\n标签：${tags.map(t => '#' + t).join(' ') || '无'}\n\n---\n\n`;
        } else {
            targetDir = path.join(OBSIDIAN_VAULT, category);
            const summary = content.substring(0, 20).replace(/[\n\r\\/:*?"<>|]/g, '');
            filePath = path.join(targetDir, `${date}-${summary}.md`);
            fileContent = `---\ndate: ${date}\ntags: ${JSON.stringify(tags)}\n---\n\n${content}\n`;
        }

        fs.mkdirSync(targetDir, { recursive: true });

        if (category === '日记') {
            fs.appendFileSync(filePath, fileContent, 'utf8');
        } else {
            if (!fs.existsSync(filePath)) {
                fs.writeFileSync(filePath, fileContent, 'utf8');
            } else { skipped++; continue; }
        }
        synced++;
    }
    return { synced, skipped };
}

main().catch(err => { console.error('Fatal:', err.message); process.exit(1); });
