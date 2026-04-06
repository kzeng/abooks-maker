import asyncio
import edge_tts
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import re
import os
from PySide6.QtCore import QThread, Signal

try:
    from .translator import translator
except ImportError:
    translator = None


def t(key, default=None):
    if translator:
        result = translator.get(key)
        if result:
            return result
    return default if default else key


EDGE_TTS_VOICES = [
    ("zh-CN-YunjianNeural", "云健 (男)"),
    ("zh-CN-YunxiNeural", "云希 (男)"),
    ("zh-CN-YunxiaNeural", "云夏 (男)"),
    ("zh-CN-YunyangNeural", "云扬 (男)"),
    ("zh-CN-liaoning-XiaobeiNeural", "晓北 (女-东北)"),
    ("zh-HK-HiuGaaiNeural", "晓佳 (女-粤语)"),
    ("zh-HK-HiuMaanNeural", "晓曼 (女-粤语)"),
    ("zh-TW-HsiaoChenNeural", "晓臻 (女-台湾)"),
    ("zh-TW-HsiaoYuNeural", "晓雨 (女-台湾)"),
    ("zh-TW-YunJheNeural", "云哲 (男-台湾)"),
]


def get_ffmpeg_path():
    import sys
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
        ffmpeg_in_pkg = os.path.join(base, 'ffmpeg')
        if os.path.exists(ffmpeg_in_pkg):
            return ffmpeg_in_pkg
        return os.path.join(base, 'ffmpeg')
    return 'ffmpeg'


def extract_text_from_epub(epub_path):
    book = epub.read_epub(epub_path)
    chapters = []
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            text = soup.get_text()
            text = re.sub(r'\s+', ' ', text).strip()
            if len(text) > 10:
                chapters.append(text)
    return chapters


def extract_text_from_txt(txt_path):
    with open(txt_path, 'r', encoding='utf-8') as f:
        text = f.read()
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) > 10:
        return [text]
    return []


def extract_text_from_pdf(pdf_path):
    from pypdf import PdfReader
    reader = PdfReader(pdf_path)
    chapters = []
    current_chapter = ""
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            text = re.sub(r'\s+', ' ', text).strip()
            if len(text) > 10:
                if len(current_chapter) + len(text) > 50000:
                    if current_chapter:
                        chapters.append(current_chapter)
                    current_chapter = text
                else:
                    current_chapter += " " + text
    if current_chapter:
        chapters.append(current_chapter)
    return chapters


def extract_text_from_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.epub':
        return extract_text_from_epub(file_path)
    elif ext == '.txt':
        return extract_text_from_txt(file_path)
    elif ext == '.pdf':
        return extract_text_from_pdf(file_path)
    return []


async def convert_text_to_audio(text, output_file, voice, rate, pitch, retries=3, delay=2):
    last_error = None
    for attempt in range(retries):
        try:
            communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
            await communicate.save(output_file)
            return True
        except Exception as e:
            last_error = e
            error_str = str(e)
            if "503" in error_str or "rate limit" in error_str.lower() or "too many requests" in error_str.lower():
                import asyncio
                await asyncio.sleep(delay * (attempt + 1))
                continue
            raise
    raise last_error


class PreviewThread(QThread):
    finished = Signal()
    error = Signal(str)

    def __init__(self, voice, rate, pitch, preview_text="Welcome to the ebook toolset."):
        super().__init__()
        self.voice = voice
        self.rate = rate
        self.pitch = pitch
        self.preview_text = preview_text

    def run(self):
        import tempfile
        import platform
        try:
            text = self.preview_text
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                temp_file = f.name
            
            asyncio.run(convert_text_to_audio(text, temp_file, self.voice, self.rate, self.pitch))
            
            if platform.system() == "Windows":
                import winsound
                winsound.PlaySound(temp_file, winsound.SND_FILENAME)
            else:
                import subprocess
                subprocess.run(['ffplay', '-nodisp', '-autoexit', temp_file], check=True)
            
            os.remove(temp_file)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


class ConvertThread(QThread):
    progress = Signal(int)
    status = Signal(str)
    log = Signal(str)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, files, output_dir, voice, rate, pitch, merge, concurrency=1, delay=1.0):
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        self.voice = voice
        self.rate = rate
        self.pitch = pitch
        self.merge = merge
        self.concurrency = concurrency
        self.delay = delay
        self._stop = False
        self._completed_count = 0
        self._total_count = 0

    def stop(self):
        self._stop = True

    def run(self):
        chapter_list = []
        
        all_chunks = []
        for file_path in self.files:
            if self._stop:
                break
            filename = os.path.splitext(os.path.basename(file_path))[0]
            self.status.emit(t('status_reading', 'Reading: {filename}').format(filename=filename))
            self.log.emit(f"Reading: {file_path}")

            chapters = extract_text_from_file(file_path)
            if not chapters:
                self.log.emit(f"No content extracted from {filename}")
                continue

            for chapter_text in chapters:
                chunks = [chapter_text[j:j+2000] for j in range(0, len(chapter_text), 2000)]
                all_chunks.extend(chunks)
        
        self._total_count = len(all_chunks)
        self._completed_count = 0
        
        if self._total_count == 0:
            self.progress.emit(100)
            self.finished.emit("No content to convert")
            return
        
        async def convert_chunk_with_limit(chunk_data):
            if self._stop:
                return None
            
            file_path, tag, chunk = chunk_data
            output_file = os.path.join(self.output_dir, os.path.basename(file_path), f"chapter_{tag}.mp3")
            
            await asyncio.sleep(self.delay)
            
            if os.path.exists(output_file):
                return "skip"
            
            try:
                await convert_text_to_audio(chunk, output_file, self.voice, self.rate, self.pitch)
                return "success"
            except Exception as e:
                return f"error: {e}"
        
        async def process_all_chunks():
            semaphore = asyncio.Semaphore(self.concurrency)
            
            async def limited_convert(chunk_data):
                async with semaphore:
                    result = await convert_chunk_with_limit(chunk_data)
                    self._completed_count += 1
                    progress = int((self._completed_count / max(1, self._total_count)) * 100)
                    self.progress.emit(progress)
                    return result
            
            chunk_data_list = []
            for file_path in self.files:
                if self._stop:
                    break
                filename = os.path.splitext(os.path.basename(file_path))[0]
                book_output_dir = os.path.join(self.output_dir, filename)
                os.makedirs(book_output_dir, exist_ok=True)
                chapter_list.append(book_output_dir)
                
                chapters = extract_text_from_file(file_path)
                if not chapters:
                    continue
                
                for i, chapter_text in enumerate(chapters):
                    if self._stop:
                        break
                    chapter_num = i + 1
                    self.status.emit(t('status_converting', 'Converting {filename} - Chapter {chapter}/{total}').format(filename=filename, chapter=chapter_num, total=len(chapters)))
                    self.log.emit(f"Converting chapter {chapter_num}/{len(chapters)} of {filename}")
                    
                    chunks = [chapter_text[j:j+2000] for j in range(0, len(chapter_text), 2000)]
                    for chunk_num, chunk in enumerate(chunks):
                        tag = f"{chapter_num:03d}_{chunk_num:02d}"
                        chunk_data_list.append((book_output_dir, tag, chunk))
            
            tasks = [limited_convert(c) for c in chunk_data_list]
            results = await asyncio.gather(*tasks)
            
            for i, result in enumerate(results):
                if result == "success":
                    self.log.emit(f"Saved: {chunk_data_list[i]}")
                elif result == "skip":
                    self.log.emit(f"Skip existing: {chunk_data_list[i]}")
                elif result and result.startswith("error"):
                    self.log.emit(f"Error: {result}")
        
        if self._stop:
            self.finished.emit("Stopped")
            return
        
        try:
            asyncio.run(process_all_chunks())
        except Exception as e:
            self.log.emit(f"Conversion error: {e}")
            self.error.emit(str(e))
        
        if self._stop:
            self.finished.emit("Stopped")
            return

        if self.merge and chapter_list:
            self.status.emit(t('status_merging', 'Merging MP3 files...'))
            self.log.emit("Merging MP3 files...")
            self.merge_audio_files(chapter_list)

        self.progress.emit(100)
        self.finished.emit("Conversion complete!")

    def merge_audio_files(self, book_dirs):
        for book_dir in book_dirs:
            mp3_files = sorted([f for f in os.listdir(book_dir) if f.endswith('.mp3')])
            if not mp3_files:
                continue

            output_file = os.path.join(book_dir, "merged.mp3")
            list_file = os.path.join(book_dir, "files.txt")

            with open(list_file, 'w') as f:
                for mp3 in mp3_files:
                    f.write(f"file '{mp3}'\n")

            import subprocess
            try:
                ffmpeg = get_ffmpeg_path()
                subprocess.run([
                    ffmpeg, '-f', 'concat', '-safe', '0', '-i', list_file,
                    '-c', 'copy', output_file
                ], check=True)
                self.log.emit(f"Merged: {output_file}")
                os.remove(list_file)
            except Exception as e:
                self.log.emit(f"Merge failed: {e}")