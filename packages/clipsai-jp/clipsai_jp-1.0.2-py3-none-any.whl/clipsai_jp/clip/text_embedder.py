"""
Embed text using sentence-transformers models.

Supports multiple models for different use cases including Japanese-optimized models.
"""
# 3rd party imports
import torch
from sentence_transformers import SentenceTransformer


class TextEmbedder:
    """
    A class for embedding text using sentence-transformers models.
    Supports multiple models for different use cases.
    """

    # 推奨モデルのリスト
    RECOMMENDED_MODELS = {
        "default": "all-roberta-large-v1",  # 既存（高速、英語特化）
        "japanese": "paraphrase-multilingual-mpnet-base-v2",  # 日本語最適化（多言語対応）
        "high_accuracy": "intfloat/multilingual-e5-base",  # 高精度（多言語対応）
        "large": "intfloat/multilingual-e5-large",  # 最高精度（多言語対応、遅い）
    }

    def __init__(self, model_name: str = None) -> None:
        """
        Initialize TextEmbedder with specified model.

        Parameters
        ----------
        model_name: str or None
            SentenceTransformer model name. If None, uses default.
            Can also use shortcut: "japanese", "high_accuracy", "large"
            Full model names can be used directly (e.g., "all-roberta-large-v1")

        Returns
        -------
        None
        """
        if model_name is None:
            model_name = self.RECOMMENDED_MODELS["default"]
        elif model_name in self.RECOMMENDED_MODELS:
            model_name = self.RECOMMENDED_MODELS[model_name]

        self.__model = SentenceTransformer(model_name)
        self.model_name = model_name

    def embed_sentences(self, sentences: list) -> torch.Tensor:
        """
        Creates embeddings for each sentence in sentences

        Parameters
        ----------
        sentences: list
            a list of N sentences

        Returns
        -------
        - sentence_embeddings: torch.tensor
            a tensor of N x E where n is a sentence and e
            is an embedding for that sentence
        """
        return torch.tensor(self.__model.encode(sentences))
