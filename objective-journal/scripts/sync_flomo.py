#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flomo Sync - 从 Flomo IndexedDB 同步笔记到 Obsidian
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path

# 配置
OBSIDIAN_VAULT = r"D:\ObsidianVault"
DIARY_DIR = os.path.join(OBSIDIAN_VAULT, "日记")
GOLD_DIR = os.path.join(OBSIDIAN_VAULT, "金句")
INSIGHT_DIR = os.path.join(OBSIDIAN_VAULT, "启发")
SLEEP_DIR = os.path.join(OBSIDIAN_VAULT, "睡眠")

# 标签映射
TAG_MAPPING = {
    "日志/事实": "日记",
    "日志": "日记",
    "事实": "日记",
    "输入/金句": "金句",
    "金句": "金句",
    "输入/启发": "启发",
    "启发": "启发",
    "睡眠": "睡眠",
}

def clean_html(text):
    """清理 HTML 标签"""
    text = re.sub(r'<p>', '\n', text)
    text = re.sub(r'</p>', '', text)
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()

def parse_tags(memo):
    """解析 memo 的标签"""
    tags = memo.get("tags", [])
    return tags

def categorize_memo(memo):
    """根据标签分类 memo"""
    tags = parse_tags(memo)
    
    for tag in tags:
        if tag in TAG_MAPPING:
            return TAG_MAPPING[tag]
    
    # 默认返回日记
    return "日记"

def format_timestamp(ts):
    """格式化时间戳"""
    if ts is None:
        return datetime.now().strftime("%Y-%m-%d")
    
    # created_at_long 是秒级时间戳
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
    
    # created_at 是字符串 "2025-08-08 06:36:30"
    if isinstance(ts, str):
        return ts.split()[0]
    
    return datetime.now().strftime("%Y-%m-%d")

def generate_filename(memo, category):
    """生成文件名"""
    date = format_timestamp(memo.get("created_at_long"))
    slug = memo.get("slug", "")[:8]
    content = clean_html(memo.get("content", ""))
    
    # 从内容提取摘要（前20个字）
    summary = content[:20].replace("\n", " ").strip()
    # 移除特殊字符
    summary = re.sub(r'[\\/:*?"<>|]', '', summary)
    
    if category == "金句":
        return f"{date}-{summary}.md"
    elif category == "启发":
        return f"{date}-{summary}.md"
    elif category == "睡眠":
        return f"{date}.md"
    else:
        # 日记追加到日期文件
        return f"{date}.md"

def format_memo_for_obsidian(memo, category):
    """格式化 memo 为 Obsidian Markdown"""
    content = clean_html(memo.get("content", ""))
    tags = parse_tags(memo)
    date = format_timestamp(memo.get("created_at_long"))
    
    if category == "金句":
        return f"""---
date: {date}
tags: {json.dumps(tags, ensure_ascii=False)}
source: 
---

{content}
"""
    elif category == "启发":
        return f"""---
date: {date}
tags: {json.dumps(tags, ensure_ascii=False)}
---

{content}
"""
    elif category == "睡眠":
        return f"""---
date: {date}
tags: {json.dumps(tags, ensure_ascii=False)}
---

{content}
"""
    else:
        # 日记格式
        time_str = ""
        if memo.get("created_at_long"):
            dt = datetime.fromtimestamp(memo["created_at_long"])
            time_str = dt.strftime("%H:%M")
        
        return f"""### {time_str}

{content}

标签：{', '.join(['#' + t for t in tags]) if tags else '无'}

---

"""

def ensure_dirs():
    """确保目录存在"""
    for dir_path in [DIARY_DIR, GOLD_DIR, INSIGHT_DIR, SLEEP_DIR]:
        os.makedirs(dir_path, exist_ok=True)
        os.makedirs(os.path.join(dir_path, datetime.now().strftime("%Y")), exist_ok=True)

def sync_memo_to_obsidian(memo):
    """同步单个 memo 到 Obsidian"""
    category = categorize_memo(memo)
    
    # 跳过已删除的
    if memo.get("deleted_at_long"):
        return None
    
    # 跳过私密标签
    tags = parse_tags(memo)
    if "私密" in tags:
        return None
    
    # 确定目标目录
    if category == "日记":
        target_dir = os.path.join(DIARY_DIR, datetime.now().strftime("%Y"))
    elif category == "金句":
        target_dir = GOLD_DIR
    elif category == "启发":
        target_dir = INSIGHT_DIR
    elif category == "睡眠":
        target_dir = SLEEP_DIR
    else:
        target_dir = os.path.join(DIARY_DIR, datetime.now().strftime("%Y"))
    
    # 生成文件路径
    filename = generate_filename(memo, category)
    filepath = os.path.join(target_dir, filename)
    
    # 格式化内容
    content = format_memo_for_obsidian(memo, category)
    
    # 写入文件
    if category == "日记":
        # 日记追加到日期文件
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(content)
    else:
        # 其他类型创建新文件
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
    
    return filepath

def sync_memos_from_flomo_data(memos):
    """从 Flomo 数据同步所有 memo"""
    ensure_dirs()
    
    synced = 0
    skipped = 0
    files = []
    
    for memo in memos:
        result = sync_memo_to_obsidian(memo)
        if result:
            synced += 1
            files.append(result)
        else:
            skipped += 1
    
    return {
        "synced": synced,
        "skipped": skipped,
        "files": files
    }

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    # 测试：从 JSON 文件读取（实际使用时从 IndexedDB 读取）
    test_memo = {
        "content": "<p>下午3点和国栋在星巴克喝茶聊孩子教育</p>",
        "tags": ["日志/事实"],
        "created_at_long": 1747907400,  # 2026-05-22 15:30
        "slug": "test123",
    }
    
    print("测试 Flomo 同步...")
    print(f"Memo: {test_memo}")
    print(f"分类: {categorize_memo(test_memo)}")
    print(f"文件名: {generate_filename(test_memo, '日记')}")
    print(f"\n格式化输出:\n{format_memo_for_obsidian(test_memo, '日记')}")
