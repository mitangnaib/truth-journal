#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Search - 搜索历史记录
"""

import os
import re
from datetime import datetime, timedelta
from pathlib import Path

# 配置
OBSIDIAN_VAULT = r"D:\ObsidianVault"
DIARY_DIR = os.path.join(OBSIDIAN_VAULT, "日记")

def search_by_date(date_str):
    """按日期搜索"""
    # 解析日期
    date_patterns = [
        (r'(\d{4}-\d{2}-\d{2})', lambda m: m.group(1)),  # 2026-05-22
        (r'(\d{1,2})月(\d{1,2})[日号]?', lambda m: f"{datetime.now().year}-{m.group(1).zfill(2)}-{m.group(2).zfill(2)}"),
        (r'今天', lambda m: datetime.now().strftime("%Y-%m-%d")),
        (r'昨天', lambda m: (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")),
        (r'前天', lambda m: (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")),
        (r'上周[一二三四五六日天]', lambda m: get_last_weekday(m.group(0))),
    ]
    
    for pattern, extractor in date_patterns:
        match = re.search(pattern, date_str)
        if match:
            target_date = extractor(match)
            return search_by_exact_date(target_date)
    
    return []

def get_last_weekday(text):
    """计算上周某天"""
    weekday_map = {
        '一': 0, '二': 1, '三': 2, '四': 3, '五': 4, '六': 5, '日': 6, '天': 6
    }
    
    for key, value in weekday_map.items():
        if key in text:
            today = datetime.now()
            days_since_monday = today.weekday()
            last_monday = today - timedelta(days=days_since_monday + 7)
            target = last_monday + timedelta(days=value)
            return target.strftime("%Y-%m-%d")
    
    return None

def search_by_exact_date(date_str):
    """按确切日期搜索"""
    year = date_str[:4]
    filepath = os.path.join(DIARY_DIR, year, f"{date_str}.md")
    
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return [{
                "date": date_str,
                "content": f.read(),
                "file": filepath
            }]
    
    return []

def search_by_person(person_name):
    """按人物搜索"""
    results = []
    
    # 遍历所有年份目录
    for year_dir in Path(DIARY_DIR).iterdir():
        if not year_dir.is_dir():
            continue
        
        for diary_file in year_dir.glob("*.md"):
            with open(diary_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 匹配人物
            patterns = [
                rf'[和跟与见]{person_name}',
                rf'{person_name}[一起见面开会吃饭喝茶]',
            ]
            
            for pattern in patterns:
                if re.search(pattern, content):
                    results.append({
                        "date": diary_file.stem,
                        "content": content,
                        "file": str(diary_file)
                    })
                    break
    
    return results

def search_by_location(location_name):
    """按地点搜索"""
    results = []
    
    for year_dir in Path(DIARY_DIR).iterdir():
        if not year_dir.is_dir():
            continue
        
        for diary_file in year_dir.glob("*.md"):
            with open(diary_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            if location_name in content:
                results.append({
                    "date": diary_file.stem,
                    "content": content,
                    "file": str(diary_file)
                })
    
    return results

def search_by_event(event_type):
    """按事件类型搜索"""
    event_keywords = {
        "会议": ["开会", "会议", "讨论"],
        "社交": ["吃饭", "喝茶", "喝咖啡", "聊天", "见面"],
        "阅读": ["读", "看", "阅读"],
        "运动": ["健身", "跑步", "游泳", "运动"],
        "写作": ["写", "写作"],
    }
    
    keywords = event_keywords.get(event_type, [event_type])
    results = []
    
    for year_dir in Path(DIARY_DIR).iterdir():
        if not year_dir.is_dir():
            continue
        
        for diary_file in year_dir.glob("*.md"):
            with open(diary_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            for keyword in keywords:
                if keyword in content:
                    results.append({
                        "date": diary_file.stem,
                        "content": content,
                        "file": str(diary_file),
                        "matched_keyword": keyword
                    })
                    break
    
    return results

def search(query):
    """智能搜索"""
    query = query.strip()
    
    # 判断搜索类型
    date_keywords = ["今天", "昨天", "前天", "上周", "月", "号", "日"]
    person_keywords = ["见了谁", "和谁", "跟谁", "见过哪些人"]
    location_keywords = ["去了哪", "在哪儿", "去过哪些"]
    event_keywords = ["开了什么会", "做了什么", "什么活动"]
    
    # 日期搜索
    if any(kw in query for kw in date_keywords):
        return {
            "type": "date",
            "results": search_by_date(query)
        }
    
    # 人物搜索
    if any(kw in query for kw in person_keywords):
        # 提取人物名
        match = re.search(r'[和跟与见]([^\s，。！？]{2,4})', query)
        if match:
            return {
                "type": "person",
                "person": match.group(1),
                "results": search_by_person(match.group(1))
            }
    
    # 地点搜索
    if any(kw in query for kw in location_keywords):
        match = re.search(r'([^\s，。！？]{2,4})[去在]', query)
        if match:
            return {
                "type": "location",
                "location": match.group(1),
                "results": search_by_location(match.group(1))
            }
    
    # 事件搜索
    if any(kw in query for kw in event_keywords):
        for event_type in ["会议", "社交", "阅读", "运动", "写作"]:
            if event_type in query:
                return {
                    "type": "event",
                    "event": event_type,
                    "results": search_by_event(event_type)
                }
    
    # 默认全文搜索
    results = []
    for year_dir in Path(DIARY_DIR).iterdir():
        if not year_dir.is_dir():
            continue
        
        for diary_file in year_dir.glob("*.md"):
            with open(diary_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            if query in content:
                results.append({
                    "date": diary_file.stem,
                    "content": content,
                    "file": str(diary_file)
                })
    
    return {
        "type": "fulltext",
        "query": query,
        "results": results
    }

def format_results(search_result, max_length=500):
    """格式化搜索结果"""
    output = []
    
    for result in search_result.get("results", []):
        date = result.get("date", "")
        content = result.get("content", "")
        
        # 截取相关片段
        if len(content) > max_length:
            content = content[:max_length] + "..."
        
        output.append(f"### {date}\n\n{content}\n")
    
    return "\n---\n".join(output)

if __name__ == "__main__":
    import sys
    import json
    sys.stdout.reconfigure(encoding='utf-8')
    
    # 测试
    test_queries = [
        "上周三做了什么",
        "见了国栋",
        "去了星巴克",
        "开会",
    ]
    
    print("=" * 50)
    print("搜索测试")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\n查询：{query}")
        result = search(query)
        print(f"类型：{result['type']}")
        print(f"结果数：{len(result.get('results', []))}")
