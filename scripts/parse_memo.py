#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memo Parser - 解析 Flomo memo，提取结构化信息
"""

import re
from typing import Dict, List, Optional
from datetime import datetime

def parse_time(text: str) -> Optional[str]:
    """提取时间信息"""
    # 匹配 "下午3点"、"15:00"、"上午10点半" 等
    patterns = [
        r'(\d{1,2}:\d{2})',  # 15:00
        r'下午(\d{1,2})点(?:半)?',  # 下午3点/下午3点半
        r'上午(\d{1,2})点(?:半)?',  # 上午10点
        r'早上(\d{1,2})点(?:半)?',
        r'晚上(\d{1,2})点(?:半)?',
        r'(\d{1,2})点(?:半)?',  # 3点/3点半
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            time_str = match.group(0)
            # 标准化时间
            if '下午' in time_str or '晚上' in time_str:
                hour = int(re.search(r'\d+', time_str).group())
                if hour < 12:
                    return f"{hour + 12}:00"
            elif '上午' in time_str or '早上' in time_str:
                hour = int(re.search(r'\d+', time_str).group())
                return f"{hour:02d}:00"
            else:
                # 尝试解析数字时间
                if ':' in time_str:
                    return time_str
                else:
                    hour = int(re.search(r'\d+', time_str).group())
                    return f"{hour:02d}:00"
    
    return None

def parse_location(text: str) -> Optional[str]:
    """提取地点信息"""
    # 常见地点关键词
    location_keywords = [
        '星巴克', '咖啡', '万象城', '万达', '商场', '公司', '办公室',
        '家', '家里', '餐厅', '酒店', '健身房', '图书馆', '书店'
    ]
    
    # 匹配 "在XX" 或 "去XX"
    patterns = [
        r'在([^，。！？\s]+?)(?:见|见面|开会|吃饭|喝茶|喝咖啡)',
        r'去([^，。！？\s]+?)(?:买|逛|看|吃|喝)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    
    # 直接匹配关键词
    for keyword in location_keywords:
        if keyword in text:
            return keyword
    
    return None

def parse_people(text: str) -> List[str]:
    """提取人物信息"""
    people = []
    
    # 匹配 "和XX"、"跟XX"、"与XX"
    patterns = [
        r'[和跟与]([^，。！？\s]{2,4}?)(?:一起|见面|开会|吃饭|喝茶|喝咖啡|聊)',
        r'见([^，。！？\s]{2,4})',
        r'约([^，。！？\s]{2,4})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            person = match.group(1)
            # 过滤常见非人名
            if person not in ['一起', '大家', '他们', '她们', '她们']:
                people.append(person)
    
    return list(set(people))  # 去重

def parse_event(text: str) -> Optional[str]:
    """提取事件信息"""
    # 常见事件关键词
    events = {
        '开会': '会议',
        '会议': '会议',
        '吃饭': '用餐',
        '喝茶': '喝茶聊天',
        '喝咖啡': '喝咖啡聊天',
        '聊': '聊天',
        '讨论': '讨论',
        '面试': '面试',
        '培训': '培训',
        '写': '写作',
        '读': '阅读',
        '看': '观看',
        '买': '购物',
        '健身': '健身',
        '跑步': '运动',
        '游泳': '运动',
    }
    
    for keyword, event in events.items():
        if keyword in text:
            return event
    
    # 默认返回主要动词
    verbs = re.findall(r'[\u4e00-\u9fa5]{2}', text)
    if verbs:
        return verbs[0]
    
    return None

def parse_topic(text: str) -> Optional[str]:
    """提取话题信息"""
    # 匹配 "聊XX"、"讨论XX"
    patterns = [
        r'聊([^，。！？\s]{2,10})',
        r'讨论([^，。！？\s]{2,10})',
        r'谈([^，。！？\s]{2,10})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    
    return None

def parse_memo(content: str) -> Dict:
    """
    解析 Flomo memo
    
    Args:
        content: memo 内容
        
    Returns:
        {
            "time": Optional[str],
            "location": Optional[str],
            "people": List[str],
            "event": Optional[str],
            "topic": Optional[str],
            "raw_content": str
        }
    """
    # 清理 HTML 标签
    clean_content = re.sub(r'<[^>]+>', '', content)
    
    result = {
        "time": parse_time(clean_content),
        "location": parse_location(clean_content),
        "people": parse_people(clean_content),
        "event": parse_event(clean_content),
        "topic": parse_topic(clean_content),
        "raw_content": content
    }
    
    return result

def format_for_obsidian(parsed: Dict, date: str = None) -> str:
    """
    格式化为 Obsidian Markdown
    
    Args:
        parsed: 解析后的 memo
        date: 日期，默认今天
        
    Returns:
        Markdown 格式的日记条目
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    lines = [f"## {date}"]
    
    if parsed["time"]:
        lines.append(f"- 时间：{parsed['time']}")
    if parsed["location"]:
        lines.append(f"- 地点：{parsed['location']}")
    if parsed["people"]:
        lines.append(f"- 人物：{', '.join(parsed['people'])}")
    if parsed["event"]:
        lines.append(f"- 事件：{parsed['event']}")
    if parsed["topic"]:
        lines.append(f"- 话题：{parsed['topic']}")
    
    lines.append(f"- 原文：{parsed['raw_content']}")
    lines.append("")
    
    return "\n".join(lines)

if __name__ == "__main__":
    import sys
    import json
    sys.stdout.reconfigure(encoding='utf-8')
    
    # 测试用例
    test_cases = [
        "下午3点和国栋在星巴克喝茶聊孩子教育",
        "晚上7点和团队开会讨论Q3计划",
        "去万象城买了双鞋",
        "读《原则》第三章",
    ]
    
    print("=" * 50)
    print("Memo Parser 测试")
    print("=" * 50)
    
    for text in test_cases:
        print(f"\n输入：{text}")
        result = parse_memo(text)
        print(f"解析结果：{json.dumps(result, ensure_ascii=False, indent=2)}")
        print(f"\nObsidian 格式：\n{format_for_obsidian(result)}")
