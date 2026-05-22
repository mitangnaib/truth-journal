# Objective Journal Skill

> "Record only facts, not emotions. So you can see yourself clearly when looking back."

A QClaw skill for objective journaling, inspired by UX expert **脱不花 (Tuohua)** and historian **马伯庸 (Ma Boyong)**.

---

## 🎯 Core Philosophy

Most people write diaries filled with emotions:
- ❌ "Today's meeting was terrible, what a waste of time"
- ✅ "Meeting: 2 hours, 5 attendees, no decision reached"

**Objective records let you observe your past self without emotional contamination.**

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📝 Fact Parser | Auto-extract time, location, people, events from entries |
| 🚫 Linter - Emotion Filter | Detects emotion words (terrible, happy, angry...) and alerts you |
| 💎 Quote Collector | Store golden sentences separately for knowledge grid analysis |
| 💡 Insight Logger | Capture insights that can become action items |
| 😴 Sleep Tracker | Record bedtime, wake time, duration, quality score |
| 📊 Weekly Review | Auto-generate weekly report: time distribution, knowledge grid, action conversion rate |
| 🕸️ Timeline View | Detective-board style visualization, connect the dots |
| ✓ Fact Verifier | Detect vague records and prompt for details |
| 🔍 Smart Search | Search by time, people, location, event type |

---

## 🏷️ Tag System

```
#日志/事实    → Triggers Linter detection
#输入/金句    → Quote collection
#输入/启发    → Insight logging
#睡眠         → Sleep quality tracking
#里程碑       → Major life events
#私密         → Excluded from weekly review
```

---

## 🚀 Quick Start

### Install

Drop `objective-journal` folder into your QClaw skills directory, then restart Gateway.

### Record

Simply chat with QClaw using tags:

```
Met with Guodong at Starbucks at 3pm, talked about kids' education #日志/事实
```

System auto-parses:
- **Time**: 15:00
- **Location**: Starbucks
- **People**: Guodong
- **Topic**: kids' education

### Linter in Action

**You write:**
```
Today was extremely frustrating, the meeting was a disaster #日志/事实
```

**System alerts:**
```
⚠️ Emotion words detected: "extremely", "frustrating", "disaster"
Try rewriting objectively:
"Meeting: 2 hours, 5 attendees, no decision reached"
```

---

## 📊 Weekly Review (Auto-generated every Sunday 21:00)

1. **Time Distribution** — Where did your time go?
2. **Social Network** — Who did you meet?
3. **Knowledge Grid** — What topics are you learning?
4. **Action Conversion** — How many insights became actions?

---

## 🕸️ Timeline View

Open `assets/timeline.html` in browser:

- Filter by: people / location / event type / time range
- Emotion word highlighting (red markers)
- Statistics: record count, people met, places visited, emotion pollution rate

---

## 📂 File Structure

```
objective-journal/
├── SKILL.md              # Skill definition
├── README.md             # This file
├── scripts/
│   ├── parse_memo.py    # Fact parser
│   ├── linter.py        # Emotion word detector
│   ├── sync_flomo.py    # Flomo → Obsidian sync
│   ├── weekly_review.py # Weekly review generator
│   └── search.py        # Smart search
├── assets/
│   └── timeline.html     # Timeline visualization
└── references/
    └── prompts.md       # Prompt templates
```

---

## 💡 Inspiration

This skill is born from a simple realization:

> When you record facts without judgment, you gain the superpower of observing yourself from the outside. Over time, patterns emerge. You see what truly matters.

Thanks to **脱不花** and **马伯庸** for the original inspiration.

---

## 📜 License

MIT License — free to use, modify, and share.

---

**Start recording facts today, thank yourself tomorrow.** 🌟
