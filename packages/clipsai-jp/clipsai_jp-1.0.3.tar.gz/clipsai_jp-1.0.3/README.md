# ClipsAI-JP

[![PyPI version](https://badge.fury.io/py/clipsai-jp.svg)](https://badge.fury.io/py/clipsai-jp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **注意:** このパッケージは[ClipsAI](https://github.com/ClipsAI/clipsai)の日本語専用フォーク版です。`whisperx`を`faster-whisper`に置き換え、依存関係の問題を解決しています。

## クイックスタート

Clips AIは、長い動画を自動的にクリップに変換するオープンソースのPythonライブラリです。数行のコードで、動画を複数のクリップに分割し、アスペクト比を16:9から9:16にリサイズできます。

> **注意:** Clips AIは、ポッドキャスト、インタビュー、スピーチ、説教などの音声中心のナラティブ動画向けに設計されています。

完全なドキュメントについては、[Clips AI Documentation](https://clipsai.com)をご覧ください。

### インストール

**前提条件:**
- Python >= 3.9
- [libmagic](https://github.com/ahupp/python-magic?tab=readme-ov-file#debianubuntu)（Windows: `pip install python-magic-bin`、Mac: `brew install libmagic`）
- [ffmpeg](https://github.com/kkroening/ffmpeg-python/tree/master?tab=readme-ov-file#installing-ffmpeg)（Windows: [ffmpeg.org](https://ffmpeg.org/download.html)からダウンロード、Mac: `brew install ffmpeg`）
- [MeCab](https://pypi.org/project/mecab/)（日本語の文分割精度向上のため推奨）
  - **全プラットフォーム（推奨）:** `pip install mecab`
    - MeCab本体も含まれており、システムレベルのインストールは不要です
    - Windows、Mac、Linuxすべてで`pip install`のみで使用可能
  - **Mac/Linux（代替方法）:** システムパッケージマネージャーを使用する場合
    - Mac: `brew install mecab mecab-ipadic`
    - Linux: `sudo apt-get install mecab libmecab-dev mecab-ipadic-utf8`
  - **注意:** MeCabがインストールされていない場合、自動的にNLTKにフォールバックします

**推奨:** 依存関係の競合を避けるため、仮想環境（[venv](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/#create-and-use-virtual-environments)など）の使用を強く推奨します。

```bash
pip install clipsai-jp
```

**オプショナル依存関係:**
- GPUメモリ監視: `pip install clipsai-jp[gpu]`
- 開発・テスト用: `pip install clipsai-jp[dev]`

## ドキュメント

使用方法、サンプルコード、パラメータ設定などの詳細については、[`doc/SAMPLE_CODE.md`](doc/SAMPLE_CODE.md)を参照してください。
