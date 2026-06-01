#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Weekly Review - 生成每周复盘报告
"""

import os
import re
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

# 配置
OBSIDIAN_VAULT = r"D:\ObsidianVault"
DIARY_DIR = os.path.join(OBSIDIAN_VAULT, "日记")
GOLD_DIR = os.path.join(OBSIDIAN_VAULT, "金句")
INSIGHT_DIR = os.path.join(OBSIDIAN_VAULT, "启发")

def get_week_range():
    """获取本周的时间范围（周一到周日）"""
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    
    return {
        "start": monday.strftime("%Y-%m-%d"),
        "end": sunday.strftime("%Y-%m-%d"),
        "start_date": monday,
        "end_date": sunday
    }

def read_diary_entries(week_range):
    """读取本周日记条目"""
    entries = []
    
    year_dir = os.path.join(DIARY_DIR, str(week_range["start_date"].year))
    if not os.path.exists(year_dir):
        return entries
    
    current = week_range["start_date"]
    while current <= week_range["end_date"]:
        date_str = current.strftime("%Y-%m-%d")
        filepath = os.path.join(year_dir, f"{date_str}.md")
        
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                entries.append({
                    "date": date_str,
                    "content": content
                })
        
        current += timedelta(days=1)
    
    return entries

def read_gold_quotes(week_range):
    """读取本周金句"""
    quotes = []
    
    if not os.path.exists(GOLD_DIR):
        return quotes
    
    for filename in os.listdir(GOLD_DIR):
        if not filename.endswith(".md"):
            continue
        
        filepath = os.path.join(GOLD_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
            # 提取日期
            date_match = re.search(r'date:\s*(\d{4}-\d{2}-\d{2})', content)
            if date_match:
                date_str = date_match.group(1)
                if week_range["start"] <= date_str <= week_range["end"]:
                    quotes.append({
                        "date": date_str,
                        "content": content,
                        "filename": filename
                    })
    
    return quotes

def read_insights(week_range):
    """读取本周启发"""
    insights = []
    
    if not os.path.exists(INSIGHT_DIR):
        return insights
    
    for filename in os.listdir(INSIGHT_DIR):
        if not filename.endswith(".md"):
            continue
        
        filepath = os.path.join(INSIGHT_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
            # 提取日期
            date_match = re.search(r'date:\s*(\d{4}-\d{2}-\d{2})', content)
            if date_match:
                date_str = date_match.group(1)
                if week_range["start"] <= date_str <= week_range["end"]:
                    insights.append({
                        "date": date_str,
                        "content": content,
                        "filename": filename
                    })
    
    return insights

def extract_tags(text):
    """提取标签"""
    return re.findall(r'#([\u4e00-\u9fa5a-zA-Z0-9_/]+)', text)

def extract_people(text):
    """提取人物"""
    # 匹配 "和XX"、"跟XX"、"见XX"
    patterns = [
        r'[和跟与见]([^\s，。！？]{2,4})(?:一起|见面|开会|吃饭|喝茶)',
    ]
    
    people = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        people.extend(matches)
    
    return list(set(people))

def extract_locations(text):
    """提取地点"""
    location_keywords = [
        '星巴克', '咖啡', '万象城', '万达', '商场', '公司', '办公室',
        '家', '家里', '餐厅', '酒店', '健身房', '图书馆', '书店'
    ]
    
    locations = []
    for keyword in location_keywords:
        if keyword in text:
            locations.append(keyword)
    
    return list(set(locations))

def analyze_time_distribution(entries):
    """分析时间分布"""
    # 统计事件类型
    events = Counter()
    for entry in entries:
        content = entry["content"]
        if "会议" in content or "开会" in content:
            events["会议"] += 1
        if "聊天" in content or "喝茶" in content or "吃饭" in content:
            events["社交"] += 1
        if "读" in content or "看" in content:
            events["阅读"] += 1
        if "写" in content:
            events["写作"] += 1
        if "运动" in content or "健身" in content or "跑步" in content:
            events["运动"] += 1
    
    return events

def analyze_social_network(entries):
    """分析社交网络"""
    all_people = []
    all_topics = []
    
    for entry in entries:
        content = entry["content"]
        all_people.extend(extract_people(content))
        
        # 提取话题
        topics = re.findall(r'聊([^\s，。！？]{2,10})', content)
        all_topics.extend(topics)
    
    return {
        "people": Counter(all_people),
        "topics": Counter(all_topics)
    }

def analyze_knowledge_grid(quotes, insights):
    """分析知识网格"""
    all_tags = []
    sources = Counter()
    
    for quote in quotes:
        tags = extract_tags(quote["content"])
        all_tags.extend(tags)
        
        # 提取来源（书名号）
        books = re.findall(r'《([^》]+)》', quote["content"])
        for book in books:
            sources[f"《{book}》"] += 1
    
    for insight in insights:
        tags = extract_tags(insight["content"])
        all_tags.extend(tags)
        
        books = re.findall(r'《([^》]+)》', insight["content"])
        for book in books:
            sources[f"《{book}》"] += 1
    
    return {
        "tags": Counter(all_tags),
        "sources": sources,
        "quote_count": len(quotes),
        "insight_count": len(insights)
    }

def generate_weekly_review(week_range, entries, quotes, insights):
    """生成周复盘报告"""
    
    # 分析数据
    time_dist = analyze_time_distribution(entries)
    social = analyze_social_network(entries)
    knowledge = analyze_knowledge_grid(quotes, insights)
    
    # 生成报告
    report = f"""# 周复盘 · {week_range['start']} ~ {week_range['end']}

## 📊 时间分布

本周记录 {len(entries)} 天

| 类型 | 次数 |
|------|------|
"""
    for event, count in time_dist.most_common(10):
        report += f"| {event} | {count} |\n"
    
    report += f"""
## 👥 社交网络

### 见过的人
"""
    if social["people"]:
        for person, count in social["people"].most_common(10):
            report += f"- {person}（{count}次）\n"
    else:
        report += "_暂无记录_\n"
    
    report += f"""
### 聊过的话题
"""
    if social["topics"]:
        for topic, count in social["topics"].most_common(10):
            report += f"- {topic}（{count}次）\n"
    else:
        report += "_暂无记录_\n"
    
    report += f"""
## 📚 知识网格

### 本周数据
- 金句：{knowledge['quote_count']} 条
- 启发：{knowledge['insight_count']} 条

### 关注领域
"""
    if knowledge["tags"]:
        for tag, count in knowledge["tags"].most_common(10):
            report += f"- #{tag}（{count}次）\n"
    else:
        report += "_暂无记录_\n"
    
    report += f"""
### 来源分布
"""
    if knowledge["sources"]:
        for source, count in knowledge["sources"].most_common(10):
            report += f"- {source}（{count}次）\n"
    else:
        report += "_暂无记录_\n"
    
    report += f"""
## 🔄 知行转化

### 本周启发 → 下周行动

"""
    if insights:
        for i, insight in enumerate(insights[:5], 1):
            # 提取启发内容（移除 YAML frontmatter）
            content = re.sub(r'^---\n.*?---\n', '', insight["content"], flags=re.DOTALL)
            content = content.strip()[:100]
            report += f"{i}. [ ] {content}...（来源：{insight['date']}）\n"
    else:
        report += "_暂无启发_\n"
    
    report += f"""
## 💡 下周建议

_基于数据生成的个性化建议待 AI 补充_

---

*生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}*
"""
    
    return report

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    print("生成周复盘...")
    
    week_range = get_week_range()
    print(f"本周范围：{week_range['start']} ~ {week_range['end']}")
    
    entries = read_diary_entries(week_range)
    print(f"日记条目：{len(entries)} 条")
    
    quotes = read_gold_quotes(week_range)
    print(f"金句：{len(quotes)} 条")
    
    insights = read_insights(week_range)
    print(f"启发：{len(insights)} 条")
    
    report = generate_weekly_review(week_range, entries, quotes, insights)
    
    # 保存报告
    report_path = os.path.join(OBSIDIAN_VAULT, "复盘", f"周复盘-{week_range['start']}.md")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n报告已保存：{report_path}")
    print("\n" + "=" * 50)
    print(report)
