#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Linter - 情绪词检测
检测 #日志/事实 标签的记录中是否包含情绪词
"""

import re
import json
from typing import Tuple, List, Dict

# 情绪词表
EMOTION_WORDS = {
    # 负面情绪词
    "糟糕", "愤怒", "讨厌", "极其", "太慢了", "崩溃", "烦死", 
    "恶心", "无语", "绝望", "压抑", "焦虑", "恐惧", "悲伤",
    "痛苦", "郁闷", "烦躁", "恼火", "气愤", "心烦",
    
    # 正面情绪词
    "开心", "太棒了", "超级", "完美", "幸福死了", "爽",
    "兴奋", "激动", "愉悦", "满足", "快乐", "幸福",
    
    # 程度副词（配合上下文判断）
    "极其", "非常", "特别", "超级", "太", "相当", "十分"
}

# 需要上下文判断的模式
PATTERNS = {
    "太...了": r"太.+了",
    "好...啊": r"好.+[啊呀]",
}

def detect_emotion_words(text: str) -> Dict:
    """
    检测文本中的情绪词
    
    Args:
        text: 待检测的文本
        
    Returns:
        {
            "has_emotion": bool,
            "emotion_words": List[str],
            "patterns": List[str],
            "suggestion": str
        }
    """
    detected_words = []
    detected_patterns = []
    
    # 检测词汇
    for word in EMOTION_WORDS:
        if word in text:
            detected_words.append(word)
    
    # 检测模式
    for pattern_name, pattern in PATTERNS.items():
        if re.search(pattern, text):
            detected_patterns.append(pattern_name)
    
    has_emotion = len(detected_words) > 0 or len(detected_patterns) > 0
    
    # 生成建议
    suggestion = ""
    if has_emotion:
        suggestion = generate_suggestion(text, detected_words, detected_patterns)
    
    return {
        "has_emotion": has_emotion,
        "emotion_words": detected_words,
        "patterns": detected_patterns,
        "suggestion": suggestion
    }

def generate_suggestion(text: str, words: List[str], patterns: List[str]) -> str:
    """生成改写建议"""
    all_issues = words + patterns
    
    suggestion = f"⚠️ 检测到情绪词：{all_issues}\n"
    suggestion += "💡 提示：试试改成客观描述，只记录事实（时间、地点、人物、事件）\n"
    suggestion += "示例：\"会议用时2小时，参与者5人，未达成决议\""
    
    return suggestion

def lint_memo(content: str, tags: List[str]) -> Dict:
    """
    对 Flomo memo 进行 Linter 检查
    
    Args:
        content: memo 内容
        tags: 标签列表
        
    Returns:
        {
            "needs_lint": bool,  # 是否需要检测
            "result": Dict       # 检测结果
        }
    """
    # 只对 #日志/事实 标签的记录进行检测
    needs_lint = "日志/事实" in tags or "日志" in tags or "事实" in tags
    
    if not needs_lint:
        return {"needs_lint": False, "result": None}
    
    result = detect_emotion_words(content)
    
    return {
        "needs_lint": True,
        "result": result
    }

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    # 测试用例
    test_cases = [
        "下午3点和国栋喝茶聊孩子教育",
        "今天开会极其糟糕，浪费时间",
        "太开心了，终于完成了！",
        "会议用时2小时，参与者5人，未达成决议"
    ]
    
    print("=" * 50)
    print("Linter 情绪词检测测试")
    print("=" * 50)
    
    for text in test_cases:
        print(f"\n输入：{text}")
        result = detect_emotion_words(text)
        # 移除 emoji 避免编码问题
        result_copy = {
            "has_emotion": result["has_emotion"],
            "emotion_words": result["emotion_words"],
            "patterns": result["patterns"],
            "suggestion": result["suggestion"].replace("⚠️", "[警告]").replace("💡", "[提示]")
        }
        print(f"检测结果：{json.dumps(result_copy, ensure_ascii=False, indent=2)}")
