# ClipsAI-JP

[![PyPI version](https://badge.fury.io/py/clipsai-jp.svg)](https://badge.fury.io/py/clipsai-jp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **注意:** このパッケージは[ClipsAI](https://github.com/ClipsAI/clipsai)の日本語専用フォーク版です。`whisperx`を`faster-whisper`に置き換え、依存関係の問題を解決しています。

## クイックスタート

Clips AIは、長い動画を自動的にクリップに変換するオープンソースのPythonライブラリです。数行のコードで、動画を複数のクリップに分割し、アスペクト比を16:9から9:16にリサイズできます。

> **注意:** Clips AIは、ポッドキャスト、インタビュー、スピーチ、説教などの音声中心のナラティブ動画向けに設計されています。

完全なドキュメントについては、[Clips AI Documentation](https://clipsai.com)をご覧ください。
このライブラリで生成されたクリップの[UIデモ](https://demo.clipsai.com)もご確認いただけます。

### インストール

**前提条件:**
- Python >= 3.9
- [libmagic](https://github.com/ahupp/python-magic?tab=readme-ov-file#debianubuntu)（Windows: `pip install python-magic-bin`、Mac: `brew install libmagic`）
- [ffmpeg](https://github.com/kkroening/ffmpeg-python/tree/master?tab=readme-ov-file#installing-ffmpeg)（Windows: [ffmpeg.org](https://ffmpeg.org/download.html)からダウンロード、Mac: `brew install ffmpeg`）

**推奨:** 依存関係の競合を避けるため、仮想環境（[venv](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/#create-and-use-virtual-environments)など）の使用を強く推奨します。

```bash
pip install clipsai-jp
```

**オプショナル依存関係:**
- GPUメモリ監視: `pip install clipsai-jp[gpu]`
- 開発・テスト用: `pip install clipsai-jp[dev]`

### クリップの作成

```python
from clipsai_jp import ClipFinder, Transcriber

transcriber = Transcriber()
transcription = transcriber.transcribe(audio_file_path="/abs/path/to/video.mp4")

clipfinder = ClipFinder()
clips = clipfinder.find_clips(transcription=transcription)

print("StartTime: ", clips[0].start_time)
print("EndTime: ", clips[0].end_time)
```

文字起こしは[faster-whisper](https://github.com/guillaumekln/faster-whisper)を使用して行われます。

### 動画のリサイズ

```python
from clipsai_jp import resize

crops = resize(
    video_file_path="/abs/path/to/video.mp4",
    pyannote_auth_token="pyannote_token",
    aspect_ratio=(9, 16)
)

print("Crops: ", crops.segments)
```

話者分離に[Pyannote](https://github.com/pyannote/pyannote-audio)が使用されるため、Hugging Faceのアクセストークンが必要です（無料）。手順については[Pyannote HuggingFace](https://huggingface.co/pyannote/speaker-diarization-3.0#requirements)ページを参照してください。
