"""
Gemini APIを使用したクリップ検出の補助機能
公式SDK: google-genai を使用
参考: https://ai.google.dev/gemini-api/docs/quickstart?hl=ja#python
"""

# standard library imports
import json
import logging
import os
import re
from typing import Dict, List, Optional

# 3rd party imports
try:
    from google import genai
except ImportError:
    genai = None

logger = logging.getLogger(__name__)


class GeminiClipFinder:
    """
    Gemini APIを使用してトピックセグメンテーションを補助するクラス

    Gemini API公式SDK (google-genai) を使用
    参考: https://ai.google.dev/gemini-api/docs/quickstart?hl=ja#python
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash"):
        """
        Parameters
        ----------
        api_key: str or None
            Google Gemini APIキー。Noneの場合は環境変数 GEMINI_API_KEY から取得
        model: str
            使用するGeminiモデル名
            - "gemini-2.5-flash" (推奨、高速)
            - "gemini-2.5-pro" (高精度、遅い)

        Raises
        ------
        ImportError
            google-genaiパッケージがインストールされていない場合
        ValueError
            APIキーが設定されていない場合
        """
        if genai is None:
            raise ImportError(
                "google-genai package is required for Gemini integration. "
                "Install it with: pip install google-genai"
            )

        # APIキーの取得
        # 引数で指定された場合はそれを使用、そうでなければ環境変数から取得
        if api_key:
            final_api_key = api_key
        else:
            final_api_key = os.environ.get("GEMINI_API_KEY")

        if not final_api_key:
            # APIキーが設定されていない場合
            raise ValueError(
                "GEMINI_API_KEY is not set. "
                "Please set it as an environment variable or pass it as api_key parameter. "
                "Get your API key from: https://aistudio.google.com/app/apikey"
            )

        # クライアントの初期化（APIキーを明示的に渡す）
        try:
            self.client = genai.Client(api_key=final_api_key)
            self.model_name = model
        except Exception as e:
            # エラーメッセージから、APIキーの問題かどうかを判断
            error_str = str(e)
            if "Missing key inputs" in error_str or "api_key" in error_str.lower():
                raise ValueError(
                    f"Failed to initialize Gemini client: API key is missing or invalid. "
                    f"Please set GEMINI_API_KEY environment variable or pass api_key parameter. "
                    f"Get your API key from: https://aistudio.google.com/app/apikey. "
                    f"Error details: {e}"
                )
            else:
                raise ValueError(f"Failed to initialize Gemini client. Error: {e}")

    def suggest_clip_boundaries(
        self,
        transcription_text: str,
        sentences: List[Dict],
        min_clip_duration: int = 10,
        max_clip_duration: int = 60,
    ) -> List[Dict]:
        """
        Gemini APIを使用してクリップ境界を提案

        Parameters
        ----------
        transcription_text: str
            文字起こしテキスト（最初の4000文字程度を使用）
        sentences: List[Dict]
            センテンス情報のリスト（start_time, end_time, sentence含む）
        min_clip_duration: int
            最小クリップ長（秒）
        max_clip_duration: int
            最大クリップ長（秒）

        Returns
        -------
        List[Dict]
            クリップ境界の提案リスト（start_time, end_time, topic含む）
            エラー時は空リストを返す
        """
        # テキストを適切な長さに切り詰め（Geminiの入力制限を考慮）
        text_preview = transcription_text[:4000]

        # センテンス情報から時間情報を抽出（インデックスも含める）
        sentences_summary = [
            {
                "index": i,
                "start_time": s.get("start_time", 0),
                "end_time": s.get("end_time", 0),
                "sentence": s.get("sentence", "")[:200],  # より長い文を保持
            }
            for i, s in enumerate(sentences[:150])  # より多くの文を考慮
        ]

        prompt = f"""あなたは動画編集の専門家です。以下の動画の文字起こしテキストを分析して、自然なトピック境界を見つけてください。

【文字起こしテキスト】
{text_preview}

【文分割結果（MeCabで日本語最適化済み）】
{json.dumps(sentences_summary, ensure_ascii=False, indent=2)}

【要件】
1. 各クリップは{min_clip_duration}秒以上{max_clip_duration}秒以下であること
2. トピックが明確に変わる箇所を境界として提案
3. 文の途中で分割しないこと（文の境界で分割）
4. 自然な会話の流れを考慮すること
5. 日本語の文構造（主述関係、修飾関係）を考慮すること

【重要な注意点】
- 提供された文分割結果は、MeCabで日本語の文構造を考慮して分割されています
- 各文の境界（start_time, end_time）を尊重してください
- 文の途中で分割すると、不自然な動画分割になります
- 文のインデックス（index）を参考にして、文の境界で分割してください

【出力形式】
JSON配列形式で返答してください:
[
  {{
    "start_time": 開始時間（秒）,
    "end_time": 終了時間（秒）,
    "topic": "トピック名の説明",
    "reason": "この境界を選んだ理由",
    "sentence_indices": [開始文のインデックス, 終了文のインデックス]
  }},
  ...
]

各クリップの start_time と end_time は、提供されたセンテンス情報の start_time と end_time を使用してください。
文のインデックス（index）を参考にして、文の境界で分割してください。
"""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )

            # レスポンステキストからJSONを抽出
            response_text = response.text
            boundaries = self._parse_json_response(response_text)

            logger.info(f"Gemini suggested {len(boundaries)} clip boundaries")
            return boundaries

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return []

    def _parse_json_response(self, text: str) -> List[Dict]:
        """
        レスポンステキストからJSON配列を抽出・パース

        Parameters
        ----------
        text: str
            Gemini APIのレスポンステキスト

        Returns
        -------
        List[Dict]
            パースされたJSON配列。エラー時は空リスト
        """
        if not text or not text.strip():
            logger.warning("Empty response from Gemini API")
            return []

        try:
            # 1. コードブロック内のJSONを抽出
            json_match = re.search(
                r"```(?:json)?\s*(\[[\s\S]*?\])\s*```", text, re.DOTALL
            )
            if json_match:
                json_text = json_match.group(1).strip()
                try:
                    return json.loads(json_text)
                except json.JSONDecodeError:
                    # コードブロック内のJSONが不完全な場合、次の方法を試す
                    pass

            # 2. 最初の [ から最後の ] までを抽出（ネストした括弧も考慮）
            start_idx = text.find("[")
            if start_idx != -1:
                bracket_count = 0
                end_idx = start_idx
                for i in range(start_idx, len(text)):
                    if text[i] == "[":
                        bracket_count += 1
                    elif text[i] == "]":
                        bracket_count -= 1
                        if bracket_count == 0:
                            end_idx = i + 1
                            break

                if bracket_count == 0:
                    json_text = text[start_idx:end_idx].strip()
                    try:
                        return json.loads(json_text)
                    except json.JSONDecodeError as e:
                        logger.debug(f"Failed to parse extracted JSON: {e}")
                        logger.debug(f"Extracted text: {json_text[:200]}...")

            # 3. より柔軟なパターンマッチング（複数行のJSON配列）
            json_match = re.search(r"\[[\s\S]*\]", text)
            if json_match:
                json_text = json_match.group(0).strip()
                # 末尾の余分な文字を削除
                json_text = json_text.rstrip(",.。、")
                try:
                    return json.loads(json_text)
                except json.JSONDecodeError:
                    pass

            # 4. 全体をJSONとして試行
            cleaned_text = text.strip()
            # 前後の説明文を削除
            cleaned_text = re.sub(r"^[^[]*", "", cleaned_text)
            cleaned_text = re.sub(r"[^\]]*$", "", cleaned_text)
            if cleaned_text.startswith("[") and cleaned_text.endswith("]"):
                try:
                    return json.loads(cleaned_text)
                except json.JSONDecodeError:
                    pass

            # 5. すべての方法が失敗した場合
            logger.warning(
                f"Failed to parse JSON from Gemini response. "
                f"Response preview: {text[:300]}..."
            )
            logger.debug(f"Full response text: {text}")
            return []

        except Exception as e:
            logger.warning(f"Unexpected error parsing JSON response: {e}")
            logger.debug(f"Response text: {text[:500]}")
            return []
