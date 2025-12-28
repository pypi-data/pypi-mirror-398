"""
ClipsAI-JP: 日本語専用動画クリップ自動生成ライブラリ

このパッケージは、長い動画を自動的にクリップに変換するオープンソースの
Pythonライブラリです。日本語の文字起こしと文分割に対応しています。
"""

# 標準ライブラリ
import warnings

# 警告フィルタの設定
# PyTorchのpynvml非推奨警告を非表示
warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    message=".*pynvml.*",
)

# pyannote.audioのtorchaudio非推奨API警告を非表示
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message=".*torchaudio.*list_audio_backends.*",
)

# Functions
from .clip.clipfinder import ClipFinder
from .media.audio_file import AudioFile
from .media.audiovideo_file import AudioVideoFile
from .media.editor import MediaEditor
from .media.video_file import VideoFile
from .resize.resize import resize
from .transcribe.transcriber import Transcriber

# Types
from .clip.clip import Clip
from .resize.crops import Crops
from .resize.segment import Segment
from .transcribe.transcription import Transcription
from .transcribe.transcription_element import Sentence, Word, Character

__all__ = [
    "AudioFile",
    "AudioVideoFile",
    "Character",
    "ClipFinder",
    "Clip",
    "Crops",
    "MediaEditor",
    "Segment",
    "Sentence",
    "Transcriber",
    "Transcription",
    "VideoFile",
    "Word",
    "resize",
]
