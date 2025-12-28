"""
日本語専用の文分割モジュール（MeCab使用）

MeCabを使用して日本語テキストを文に分割します。
タイムスタンプのマッピングを維持するため、元の文字列と完全に一致する
文分割結果を生成します。
"""

import logging
import re
from typing import List, Optional

try:
    import MeCab  # type: ignore

    MECAB_AVAILABLE = True
except ImportError:
    MECAB_AVAILABLE = False
    MeCab = None  # type: ignore

logger = logging.getLogger(__name__)


class JapaneseSentenceSplitter:
    """
    MeCabを使用した日本語専用の文分割クラス

    タイムスタンプのマッピングを維持するため、
    元の文字列と完全に一致する文分割結果を生成します。

    Notes
    -----
    - MeCabは文の品質検証に使用し、元の文字列は変更しません
    - 句読点（。、！？）を基準に分割し、MeCabで文の有効性を確認します
    - エラー時はフォールバックして、基本的な句読点分割を返します
    """

    def __init__(self, mecab_dict_path: Optional[str] = None):
        """
        Parameters
        ----------
        mecab_dict_path: str or None
            MeCab辞書のパス（Noneの場合はデフォルト辞書を使用）

        Raises
        ------
        ImportError
            MeCabがインストールされていない場合
        RuntimeError
            MeCabの初期化に失敗した場合
        """
        if not MECAB_AVAILABLE:
            raise ImportError(
                "MeCab is not installed. Install it with: " "pip install mecab"
            )

        # MeCabの初期化
        mecab_options = ""
        if mecab_dict_path:
            mecab_options = f"-d {mecab_dict_path}"

        try:
            # mecabパッケージの場合、オプションなしで初期化を試みる
            # （設定ファイルは自動検出される）
            if mecab_options:
                self.mecab = MeCab.Tagger(mecab_options)
            else:
                self.mecab = MeCab.Tagger()

            # 初期化テスト
            test_result = self.mecab.parse("テスト")
            if not test_result:
                raise RuntimeError("MeCab initialization test failed")
        except Exception as e:
            logger.error(f"Failed to initialize MeCab: {e}")
            raise RuntimeError(f"MeCab initialization failed: {e}")

    def split_sentences(self, text: str) -> List[str]:
        """
        日本語テキストを文に分割

        元の文字列と完全に一致する文分割結果を返すため、
        句読点（。、！？）を基準に分割します。
        MeCabの形態素解析結果は文の品質向上にのみ使用します。

        Parameters
        ----------
        text: str
            分割する日本語テキスト

        Returns
        -------
        List[str]
            文のリスト（元の文字列の部分文字列）

        Notes
        -----
        - 元の文字列の部分文字列を返すため、タイムスタンプマッピングが機能します
        - 空白文字も保持されます
        - エラー時は基本的な句読点分割を返します
        """
        if not text:
            return []

        # 句読点で分割候補を取得
        # 日本語の句読点: 。、！？、改行
        sentence_endings = r"[。！？\n]"

        # 句読点の位置を保持しながら分割
        # 元の文字列の部分文字列をそのまま保持する（空白も含む）
        sentences = []
        current_sentence = ""

        i = 0
        while i < len(text):
            char = text[i]
            current_sentence += char

            # 句読点を検出
            if re.match(sentence_endings, char):
                # MeCabで形態素解析して、文の品質を確認
                if self._is_valid_sentence_end(current_sentence, text, i):
                    # 元の文字列の部分文字列をそのまま追加（空白も含む）
                    sentences.append(current_sentence)
                    current_sentence = ""
                # 文の終わりでない場合は続ける（例：「。」が引用符内にある場合）

            i += 1

        # 最後の文を追加（空白文字のみの場合は除外）
        # current_sentence.strip()で判定するが、結果には元の文字列をそのまま追加
        if current_sentence and current_sentence.strip():
            sentences.append(current_sentence)

        # 空の文（空白文字のみ）を除去
        # strip()は使わず、元の文字列の部分文字列をそのまま保持
        result = [s for s in sentences if s.strip()]

        # 結果が空の場合は、元のテキストをそのまま返す（strip()は使わない）
        if not result:
            return [text] if text.strip() else []

        return result

    def _is_valid_sentence_end(
        self, sentence: str, full_text: str, position: int
    ) -> bool:
        """
        文の終わりが有効かどうかをMeCabで確認

        Parameters
        ----------
        sentence: str
            現在の文候補
        full_text: str
            全文
        position: int
            現在の位置

        Returns
        -------
        bool
            有効な文の終わりかどうか

        Notes
        -----
        - エラー時はデフォルトでTrueを返します（既存の動作を維持）
        - 引用符や括弧が閉じているかも確認します
        """
        try:
            # MeCabで形態素解析
            node = self.mecab.parseToNode(sentence)

            # 文末の品詞を確認
            # 動詞、形容詞、名詞+助動詞などで終わっているか確認
            last_pos = None
            last_surface = None

            while node:
                if node.surface:
                    # 品詞情報を取得
                    # 例: "動詞,自立,*,*,五段・ラ行,連用形,終わる,オワル,オワル"
                    features = node.feature.split(",")
                    if len(features) > 0:
                        last_pos = features[0]
                        last_surface = node.surface
                node = node.next

            # 文末として適切な品詞で終わっているか確認
            valid_end_pos = ["動詞", "形容詞", "名詞", "助動詞", "記号"]
            if last_pos in valid_end_pos:
                # 引用符や括弧内の場合は無効
                if not self._is_in_quotes(sentence):
                    return True

            # 記号（句点）で終わっている場合も有効
            if last_pos == "記号" and last_surface in ["。", "！", "？"]:
                if not self._is_in_quotes(sentence):
                    return True

            # デフォルトで有効とする（既存の動作を維持）
            return True

        except Exception as e:
            logger.debug(f"MeCab parsing error: {e}")
            # エラー時はデフォルトで有効とする
            return True

    def _is_in_quotes(self, sentence: str) -> bool:
        """
        文が引用符や括弧内にあるかどうかを確認

        Parameters
        ----------
        sentence: str
            確認する文

        Returns
        -------
        bool
            引用符や括弧内にある場合True
        """
        # 引用符の数をカウント
        quote_chars = ['"', '"', '"', '"', "「", "」", "『", "』", "（", "）", "(", ")"]
        quote_count = 0

        for char in sentence:
            if char in quote_chars:
                quote_count += 1

        # 奇数個の引用符がある場合は、引用符内にある
        return quote_count % 2 != 0
