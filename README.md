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

