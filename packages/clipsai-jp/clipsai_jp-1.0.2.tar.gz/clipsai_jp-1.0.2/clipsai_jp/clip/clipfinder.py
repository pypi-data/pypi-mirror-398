"""
Finding clips with AudioFiles using the TextTiling algorithm.
"""
# standard library imports
import logging
from typing import List

# current package imports
from .clip import Clip
from .exceptions import ClipFinderError
from .gemini_clipfinder import GeminiClipFinder
from .text_embedder import TextEmbedder
from .texttiler import TextTiler
from .texttiler import TextTilerConfigManager

# local package imports
from clipsai_jp.transcribe.transcription import Transcription
from clipsai_jp.utils.pytorch import get_compute_device, assert_compute_device_available
from clipsai_jp.utils.utils import find_missing_dict_keys

# 3rd party imports
import torch

BOUNDARY = 1


class ClipFinder:
    """
    A class for finding clips within some audio file using the TextTiling Algorithm.
    """

    def __init__(
        self,
        device: str = None,
        min_clip_duration: int = 15,
        max_clip_duration: int = 900,
        cutoff_policy: str = "high",
        embedding_aggregation_pool_method: str = "max",
        smoothing_width: int = 3,
        window_compare_pool_method: str = "mean",
        embedding_model: str = None,
        use_gemini: bool = False,
        gemini_api_key: str = None,
        gemini_model: str = "gemini-2.5-flash",
        gemini_priority: float = 0.5,
    ) -> None:
        """
        Parameters
        ----------
        device: str
            PyTorch device to perform computations on. Ex: 'cpu', 'cuda'. Default is
            None (auto detects the correct device)
        min_clip_duration: int
            Minimum duration in seconds for a clip
        max_clip_duration: int
            Maximum duration in seconds for a clip
        cutoff_policy: str
            The policy used to determine how dissimilar adjacent embedding windows must
            be to consider them to be from different segments (a boundary).
            Possible values: 'average', 'high', or 'low'
        embedding_aggregation_pool_method: str
            the method used to pool embeddings within a segment to create a single
            embedding for the segment.
            Possible values: 'mean', 'max'
        smoothing_width: int
            The width of the window used by the smoothing method
        window_compare_pool_method: str
            the method used to pool embeddings within windows (of size k) for comparison
            to adjacent windows.
            Possible values: 'mean', 'max'
        embedding_model: str or None
            SentenceTransformer model name for text embeddings. If None, uses default.
            Can use shortcuts: 'japanese' (日本語最適化), 'high_accuracy' (高精度),
            'large' (最高精度、遅い), or full model names.
            See TextEmbedder.RECOMMENDED_MODELS for available options.
        use_gemini: bool
            Gemini APIを使用するかどうか（デフォルト: False）
        gemini_api_key: str or None
            Gemini APIキー。Noneの場合は環境変数 GEMINI_API_KEY から取得
        gemini_model: str
            使用するGeminiモデル名（デフォルト: "gemini-2.5-flash"）
        gemini_priority: float
            Geminiの提案の重み（0.0=TextTilingのみ, 1.0=Geminiのみ、デフォルト: 0.5）
        """
        # configuration check
        config_manager = ClipFinderConfigManager()
        config_manager.assert_valid_config(
            {
                "cutoff_policy": cutoff_policy,
                "embedding_aggregation_pool_method": embedding_aggregation_pool_method,
                "max_clip_duration": max_clip_duration,
                "min_clip_duration": min_clip_duration,
                "smoothing_width": smoothing_width,
                "window_compare_pool_method": window_compare_pool_method,
            }
        )
        if device is None:
            device = get_compute_device()
        assert_compute_device_available(device)
        self._device = device
        self._cutoff_policy = cutoff_policy
        self._embedding_aggregation_pool_method = embedding_aggregation_pool_method
        self._min_clip_duration = min_clip_duration
        self._max_clip_duration = max_clip_duration
        self._smoothing_width = smoothing_width
        self._window_compare_pool_method = window_compare_pool_method
        self._embedding_model = embedding_model

        # Gemini統合の初期化
        if use_gemini:
            try:
                self._gemini_finder = GeminiClipFinder(
                    api_key=gemini_api_key,
                    model=gemini_model,
                )
                self._use_gemini = True
                self._gemini_priority = gemini_priority
                logging.info("Gemini clip finder initialized")
            except Exception as e:
                logging.warning(
                    f"Failed to initialize Gemini: {e}. "
                    "Falling back to TextTiling only."
                )
                self._use_gemini = False
        else:
            self._use_gemini = False

    def find_clips(
        self,
        transcription: Transcription,
    ) -> list[Clip]:
        """
        Finds clips in an audio file's transcription using the TextTiling Algorithm.

        Parameters
        ----------
        transcription: Transcription
            the transcription of the source media to find clips within

        Returns
        -------
        list[dict]
            list of tuples containing data about clips
        """
        # get the transcription as a list of sentences
        sentences = []
        sentences_info = transcription.get_sentence_info()
        for sentence_info in sentences_info:
            sentences.append(sentence_info["sentence"])

        # embed sentences
        text_embedder = TextEmbedder(model_name=self._embedding_model)
        sentence_embeddings = text_embedder.embed_sentences(sentences)

        # add full media as clip
        clips = []
        if transcription.end_time <= self._max_clip_duration:
            full_media_clip = {}
            full_media_clip["start_char"] = 0
            full_media_clip["end_char"] = len(transcription.get_char_info())
            full_media_clip["start_time"] = 0
            full_media_clip["end_time"] = transcription.end_time
            full_media_clip["norm"] = 1.0
            clips.append(full_media_clip)

        # <3 min clips
        k_vals = [5, 7]
        for k in k_vals:
            clips = self._text_tile_multiple_rounds(
                sentences_info,
                sentence_embeddings,
                k,
                self._min_clip_duration,
                self._max_clip_duration,
                clips,
            )

        # 3+ min clips
        k_vals = [11, 17]
        min_duration_secs = 180  # 3 minutes
        for k in k_vals:
            clips = self._text_tile_multiple_rounds(
                sentences_info,
                sentence_embeddings,
                k,
                min_duration_secs,
                self._max_clip_duration,
                clips,
            )

        # 10+ min clips
        k_vals = [37, 53, 73, 97]
        min_duration_secs = 600  # 10 minutes
        for k in k_vals:
            clips = self._text_tile_multiple_rounds(
                sentences_info,
                sentence_embeddings,
                k,
                min_duration_secs,
                self._max_clip_duration,
                clips,
            )

        # Geminiを使用する場合
        if self._use_gemini:
            try:
                gemini_boundaries = self._gemini_finder.suggest_clip_boundaries(
                    transcription.text,
                    sentences_info,
                    self._min_clip_duration,
                    self._max_clip_duration,
                )

                # Geminiの提案をクリップ形式に変換
                gemini_clips = self._convert_gemini_boundaries_to_clips(
                    gemini_boundaries,
                    transcription,
                )

                # TextTilingとGeminiの結果を統合
                clips = self._merge_clip_proposals(
                    clips,  # TextTilingの結果
                    gemini_clips,  # Geminiの結果
                    self._gemini_priority,
                )

                logging.info(
                    f"Combined {len(clips)} clips from TextTiling and Gemini "
                    f"(Gemini suggested {len(gemini_clips)} clips)"
                )

            except Exception as e:
                logging.error(
                    f"Gemini processing failed: {e}. "
                    "Using TextTiling results only."
                )
                # Gemini失敗時はTextTilingの結果のみを使用

        clip_objects = []
        for clip_info in clips:
            clip_objects.append(
                Clip(
                    clip_info["start_time"],
                    clip_info["end_time"],
                    clip_info["start_char"],
                    clip_info["end_char"],
                )
            )

        return clip_objects

    def _text_tile_multiple_rounds(
        self,
        clips: list[dict],
        clip_embeddings: torch.tensor,
        k: int,
        min_clip_duration: int,
        max_clip_duration: int,
        final_clips: list[dict] = [],
    ) -> tuple[list, torch.Tensor]:
        """
        Segments the embeddings multiple rounds using the TextTiling algorithm.

        Parameters
        ----------
        clips: list[dict]
            list of dictionaries containing information about clips' transcript
        clip_embeddings: torch.tensor
            clip embeddings used to segment the clips into larger clips
        k: int
            text tiling window size
        min_duration_secs: int
            minimum clip length for a clip to be created
        max_duration_secs: int
            max clip length for a clip to be created
        final_clips: list[dict]
            list of dictionaries containing information about already chosen clips

        Returns
        -------
        list[dict]
            list of dictionaries containing information about the chosen clips
        """
        self._text_tile_round = 0
        while len(clip_embeddings) > 8:
            self._text_tile_round += 1
            # segment the embeddings using the TextTiling algorithm
            super_clips, super_clip_embeddings = self._text_tile(
                clips, clip_embeddings, k
            )
            # filter clips based on length
            new_clips = self._remove_duplicates(
                super_clips,
                final_clips,
                min_clip_duration,
                max_clip_duration,
            )
            final_clips += new_clips
            clips = super_clips
            clip_embeddings = super_clip_embeddings

        return final_clips

    def _text_tile(
        self,
        clips: list[dict],
        clip_embeddings: torch.tensor,
        k: int,
    ) -> tuple[list, torch.Tensor]:
        """
        Segments the embeddings using the TextTiling algorithm.

        Parameters
        ----------
        clips: list[dict]
            list of dictionaries containing information about clips' transcript
        clip_embeddings: torch.tensor
            clip embeddings used to segment the clips into larger clips

        Returns
        -------
        tuple[list, torch.Tensor]
            list of dictionaries containing information about clips and the embeddings
            of the super clips
        """
        # check that the number of embeddings matches the number of clips
        if len(clip_embeddings) != len(clips):
            err = (
                "Length of embeddings ({}) does not match length of clip ({})"
                "".format(len(clip_embeddings), len(clips))
            )
            logging.error(err)
            raise ClipFinderError(err)

        # execute text tiling
        texttiler = TextTiler(self._device)

        # use smaller k value if number of clips is small
        if k >= len(clip_embeddings):
            k = 3

        boundaries, super_clip_embeddings = texttiler.text_tile(
            clip_embeddings,
            k,
            self._window_compare_pool_method,
            self._embedding_aggregation_pool_method,
            self._smoothing_width,
            self._cutoff_policy,
        )

        # combine clips into super clips (larger clips composed of smaller clips)
        num_clips = len(clips)
        super_clips = []
        clip_start_idx = 0
        clip_end_idx = None
        super_clip_num = 0

        for i in range(num_clips):
            if boundaries[i] == BOUNDARY:
                clip_end_idx = i
                super_clip = {}
                super_clip["start_char"] = clips[clip_start_idx]["start_char"]
                super_clip["end_char"] = clips[clip_end_idx]["end_char"]
                super_clip["start_time"] = clips[clip_start_idx]["start_time"]
                super_clip["end_time"] = clips[clip_end_idx]["end_time"]
                super_clip["norm"] = torch.linalg.norm(
                    super_clip_embeddings[super_clip_num], dim=0, ord=2
                ).item()

                super_clips.append(super_clip)
                clip_start_idx = clip_end_idx

                super_clip_num += 1

        return super_clips, super_clip_embeddings

    def _remove_duplicates(
        self,
        potential_clips: dict,
        clips_to_check_against: list[dict],
        min_duration_secs: int,
        max_duration_secs: int,
    ) -> tuple:
        """
        Removes duplicate clips from 'potential_clips' that are within the
        'clips_to_check_against' list.

        Parameters
        ----------
        potential_clips: dict
            list of potential clips
        clips_to_check_against: list[dict]
            list of clips to check against
        min_duration_secs: int
            minimum clip length for a clip to be created
        max_duration_secs: int
            max clip length for a clip to be created

        Returns
        -------
        list[dict]
            list of potential clips with duplicates removed
        """
        filtered_clips = []

        # create clip objects
        for clip in potential_clips:
            clip_duration = clip["end_time"] - clip["start_time"]
            if clip_duration < min_duration_secs:
                continue
            if clip_duration > max_duration_secs:
                continue

            if self._is_duplicate(clip, clips_to_check_against):
                continue

            filtered_clips.append(clip)

        return filtered_clips

    def _is_duplicate(
        self, potential_clip: dict, clips_to_check_against: list[dict]
    ) -> bool:
        """
        Checks if 'potential_clip' is a duplicate of any clip in clips.

        Parameters
        ----------
        potential_clip: dict
            a potential clip
        clips_to_check_against: list[dict]
            list of clips to check against

        Returns
        -------
        bool
            True if 'potential_clip' is a duplicate, False otherwise.
        """
        for clip in clips_to_check_against:
            start_time_diff = abs(potential_clip["start_time"] - clip["start_time"])
            end_time_diff = abs(potential_clip["end_time"] - clip["end_time"])

            if (start_time_diff + end_time_diff) < 15:
                return True

        return False

    def _convert_gemini_boundaries_to_clips(
        self,
        gemini_boundaries: List[dict],
        transcription: Transcription,
    ) -> List[dict]:
        """
        Geminiの境界提案をクリップ形式に変換

        Parameters
        ----------
        gemini_boundaries: List[dict]
            Gemini APIから返された境界提案リスト
        transcription: Transcription
            文字起こしオブジェクト

        Returns
        -------
        List[dict]
            クリップ形式の辞書リスト
        """
        clips = []
        for boundary in gemini_boundaries:
            start_time = boundary.get("start_time", 0)
            end_time = boundary.get("end_time", 0)

            # 時間制約をチェック
            duration = end_time - start_time
            if duration < self._min_clip_duration or duration > self._max_clip_duration:
                continue

            # 時間から文字インデックスを取得
            try:
                start_char_index = transcription.find_char_index(
                    start_time, type_of_time="start"
                )
                end_char_index = transcription.find_char_index(
                    end_time, type_of_time="end"
                )
            except Exception as e:
                logging.warning(
                    f"Failed to convert time to char index for "
                    f"clip ({start_time:.2f}s - {end_time:.2f}s): {e}"
                )
                continue

            clips.append(
                {
                    "start_time": start_time,
                    "end_time": end_time,
                    "start_char": start_char_index,
                    "end_char": end_char_index,
                    "norm": 1.0,
                    "source": "gemini",  # ソースを記録
                }
            )

        return clips

    def _merge_clip_proposals(
        self,
        texttiling_clips: List[dict],
        gemini_clips: List[dict],
        gemini_priority: float,
    ) -> List[dict]:
        """
        TextTilingとGeminiの提案を統合

        Parameters
        ----------
        texttiling_clips: List[dict]
            TextTilingアルゴリズムで検出されたクリップリスト
        gemini_clips: List[dict]
            Gemini APIで提案されたクリップリスト
        gemini_priority: float
            Geminiの提案の重み（0.0-1.0）

        Returns
        -------
        List[dict]
            統合されたクリップリスト
        """
        if gemini_priority == 0.0:
            return texttiling_clips
        if gemini_priority == 1.0:
            return gemini_clips

        # 重複を除去してマージ
        merged_clips = []

        # TextTilingのクリップを追加
        for clip in texttiling_clips:
            clip_with_weight = clip.copy()
            clip_with_weight["weight"] = 1.0 - gemini_priority
            merged_clips.append(clip_with_weight)

        # Geminiのクリップを追加（重複チェック）
        for gemini_clip in gemini_clips:
            # 時間範囲が重複するクリップをチェック
            is_duplicate = False
            for existing_clip in merged_clips:
                overlap = self._calculate_overlap(
                    gemini_clip["start_time"],
                    gemini_clip["end_time"],
                    existing_clip["start_time"],
                    existing_clip["end_time"],
                )
                if overlap > 0.8:  # 80%以上重複している場合は重複とみなす
                    is_duplicate = True
                    # 重複している場合は、重み付き平均で更新
                    existing_weight = existing_clip["weight"]
                    total_weight = existing_weight + gemini_priority

                    existing_clip["start_time"] = (
                        existing_clip["start_time"] * existing_weight
                        + gemini_clip["start_time"] * gemini_priority
                    ) / total_weight
                    existing_clip["end_time"] = (
                        existing_clip["end_time"] * existing_weight
                        + gemini_clip["end_time"] * gemini_priority
                    ) / total_weight
                    existing_clip["weight"] = 1.0
                    break

            if not is_duplicate:
                gemini_clip_with_weight = gemini_clip.copy()
                gemini_clip_with_weight["weight"] = gemini_priority
                merged_clips.append(gemini_clip_with_weight)

        # 重みを削除して返す
        return [
            {k: v for k, v in clip.items() if k != "weight"}
            for clip in merged_clips
        ]

    def _calculate_overlap(
        self,
        start1: float,
        end1: float,
        start2: float,
        end2: float,
    ) -> float:
        """
        2つの時間範囲の重複率を計算（0.0-1.0）

        Parameters
        ----------
        start1: float
            最初のクリップの開始時間（秒）
        end1: float
            最初のクリップの終了時間（秒）
        start2: float
            2番目のクリップの開始時間（秒）
        end2: float
            2番目のクリップの終了時間（秒）

        Returns
        -------
        float
            重複率（0.0-1.0）。0.0は重複なし、1.0は完全に重複
        """
        overlap_start = max(start1, start2)
        overlap_end = min(end1, end2)
        if overlap_end <= overlap_start:
            return 0.0

        overlap_duration = overlap_end - overlap_start
        duration1 = end1 - start1
        duration2 = end2 - start2

        # 2つのクリップの平均長さに対する重複率
        avg_duration = (duration1 + duration2) / 2
        return overlap_duration / avg_duration if avg_duration > 0 else 0.0


class ClipFinderConfigManager(TextTilerConfigManager):
    """
    A class for getting information about and validating TextTiler configuration
    settings.
    """

    def __init__(self) -> None:
        """
        Parameters
        ----------
        None
        """
        super().__init__()

    def impute_default_config(self, config: dict) -> dict:
        """
        Populates input data with default values if they are not provided.

        Parameters
        ----------
        config: dict
            The input data to be imputed.

        Returns
        -------
        dict
            The imputed input data.
        """
        default_values = {
            "compute_device": "cpu",
            "cutoff_policy": "high",
            "embedding_aggregation_pool_method": "max",
            "min_clip_time": 15,
            "max_clip_time": 900,
            "smoothing_width": 3,
            "window_compare_pool_method": "mean",
        }

        for key in default_values.keys():
            if key not in config:
                config[key] = default_values[key]

        return config

    def check_valid_config(
        self,
        texttile_config: dict,
    ) -> str or None:
        """
        Checks that 'texttile_config' contains valid configuration settings. Returns
        None if valid, a descriptive error message if invalid.

        Parameters
        ----------
        texttile_config: dict
            A dictionary containing the configuration settings for TextTiler.

        Returns
        -------
        str or None
            None if the inputs are valid, otherwise an error message.
        """
        # existence check
        required_keys = [
            "cutoff_policy",
            "embedding_aggregation_pool_method",
            "max_clip_duration",
            "min_clip_duration",
            "smoothing_width",
            "window_compare_pool_method",
        ]
        missing_keys = find_missing_dict_keys(texttile_config, required_keys)
        if len(missing_keys) != 0:
            return "TextTiler missing configuration settings: {}".format(missing_keys)

        # value checks
        err = self.check_valid_clip_times(
            texttile_config["min_clip_duration"],
            texttile_config["max_clip_duration"],
        )
        if err is not None:
            return err

        setting_checkers = {
            "cutoff_policy": self.check_valid_cutoff_policy,
            "embedding_aggregation_pool_method": self.check_valid_embedding_aggregation_pool_method,
            "smoothing_width": self.check_valid_smoothing_width,
            "window_compare_pool_method": self.check_valid_window_compare_pool_method,
        }
        for setting, checker in setting_checkers.items():
            err = checker(texttile_config[setting])
            if err is not None:
                return err

        return None

    def check_valid_clip_times(
        self, min_clip_duration: float, max_clip_duration: float
    ) -> str or None:
        """
        Checks the clip times are valid. Returns None if the clip times are valid, a
        descriptive error message if invalid.

        Parameters
        ----------
        min_clip_duration: float
            The minimum clip time in seconds
        max_clip_duration: float
            The maximum clip time in seconds

        Returns
        -------
        str or None
            None if the clip times are valid, otherwise an error message.
        """
        # type check
        self._type_checker.check_type(
            min_clip_duration, "min_clip_duration", (float, int)
        )
        self._type_checker.check_type(
            max_clip_duration, "max_clip_duration", (float, int)
        )

        # minimum clip time
        if min_clip_duration < 0:
            error = "min_clip_duration must be 0 or greater, not {}" "".format(
                min_clip_duration
            )
            return error

        # maximum clip time
        if max_clip_duration <= min_clip_duration:
            error = (
                "max_clip_duration of {} must be greater than "
                "min_clip_duration of {}"
                "".format(max_clip_duration, min_clip_duration)
            )
            return error

        return None
