# Audio Books Maker

GUI tool to convert ebooks to audiobooks using Microsoft Edge TTS.

## Target

A simple, powerful audio book tool:

- Convert ebooks to chaptered MP3 files
- Merge all chapters into a single MP3
- Support multiple Chinese voices from Edge TTS

## Features

0. Python venv support (recommended name: `venv` in project root)
1. PySide6 GUI
2. Select multi-format ebook files: EPUB, TXT, PDF (MOBI not yet supported)
3. Choose Edge TTS voices, e.g.
	- zh-CN-YunjianNeural (male)
	- zh-CN-YunxiNeural (male)
	- zh-CN-YunxiaNeural (male)
	- zh-CN-YunyangNeural (male)
	- zh-CN-liaoning-XiaobeiNeural (female)
	- zh-HK-HiuGaaiNeural (female)
	- zh-HK-HiuMaanNeural (female)
	- zh-TW-HsiaoChenNeural (female)
	- zh-TW-HsiaoYuNeural (female)
	- zh-TW-YunJheNeural (male)
4. Configure conversion params: rate (default +5%), pitch (default +1Hz)
5. Select output folder
6. View a progress bar during conversion
7. Optional log panel (hidden by default)
8. Output format: MP3 chapters + optional merged MP3

## Install & Run (dev)

```bash
cd abooks-maker
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
pip install -r requirements.txt

python -m src.main
```

Requirements:

- Python 3.10+
- System `ffmpeg` available on PATH (for merge to single MP3)

## Build (PyInstaller)

```bash
cd abooks-maker
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pyinstaller

pyinstaller Audio-Books-Maker.spec
```

The built application will be under the `dist` directory.

## Tech Stack

- PySide6
- edge_tts
- ebooklib
- beautifulsoup4
- pypdf
- ffmpeg (external tool)

## Ref (FYI)

You can reference codes in current workspace:

~/yt-downloader: GUI main framework and packaging script
~/ebook2vbook: ebook conversion and merge scripts

-------------------------


## Implementation

### Project Structure
abooks-maker/
├── Audio-Books-Maker.spec    # PyInstaller spec
├── README.md                  # Documentation
├── requirements.txt           # Dependencies
├── src/
│   ├── main.py               # Entry point
│   └── app/
│       ├── __init__.py
│       ├── converter.py      # Ebook→TTS conversion logic
│       ├── main_window.py    # GUI (PySide6)
│       ├── translator.py    # i18n (zh/en)
│       ├── style.qss        # Dark theme
│       └── style_light.qss  # Light theme
└── venv/                      # Virtual environment


### Features Implemented
- Frameless window with custom title bar (minimize/maximize/close)
- Multi-format support: EPUB, TXT, PDF
- 10 Edge TTS voices: Chinese male/female, Cantonese, Taiwanese
- Rate/Pitch control: sliders with live preview (+5% / +1Hz default)
- Output folder selection with persistent settings
- Merge to single MP3 (requires ffmpeg on PATH)
- Progress bar during conversion
- Log panel (toggleable, hidden by default)
- Dark/Light themes with persistence
- English/Chinese languages


### Run (dev)
cd abooks-maker
source venv/bin/activate
python -m src.main


### Build (PyInstaller)
source venv/bin/activate
pip install pyinstaller
pyinstaller Audio-Books-Maker.spec
`Output: dist/Audio-Books-Maker`


------------------------------

## Enhancement
1. 当程序在转换章节时遇到异常（如 503 错误）中断后，应该有个重试机制，保证能够从上次已完成的章节继续，而不是从头开始
2. 设置-->关于 信息，增加作者信息： zengkai001@qq.com
3. 去掉“电子书转有声书”大标题
4. 新增一个“试听”按钮， 用来配置 语音/语速/音调。 试听信息：“欢迎使用老曾的电子书工具集。”
5. 为每个按钮前面增加一个合适的符合语义的图标icon.
6. UI布局优化， 语音/语速/音调/输出目录/合并为单个MP3/试听按钮/开始转换按钮 放置在一个BOX 里面，BOX 分为左右两栏， 左栏：语音/语速/音调/输出目录/合并为单个MP3 的配置； 右栏：试听按钮/开始转换按钮 
7. 检查并完善所有双语信息(中文/English)
8. 合并为单个MP3 默认为勾选状态
9. 把author.png 加到 设置-->关于信息BOX的右侧

