"""
Transcribe audio files using faster-whisper.

Notes
-----
- Faster-Whisper GitHub: https://github.com/guillaumekln/faster-whisper
- Faster-Whisper is a faster implementation of OpenAI's Whisper model using CTranslate2
"""
# standard library imports
from datetime import datetime
import logging

# current package imports
from .exceptions import NoSpeechError
from .exceptions import TranscriberConfigError
from .transcription import Transcription

# local imports
from clipsai_jp.media.audio_file import AudioFile
from clipsai_jp.media.editor import MediaEditor
from clipsai_jp.utils.config_manager import ConfigManager
from clipsai_jp.utils.pytorch import assert_valid_torch_device, get_compute_device
from clipsai_jp.utils.type_checker import TypeChecker
from clipsai_jp.utils.utils import find_missing_dict_keys

# third party imports
import torch
from faster_whisper import WhisperModel


class Transcriber:
    """
    A class to transcribe using faster-whisper.
    """

    def __init__(
        self,
        model_size: str = None,
        device: str = None,
        precision: str = None,
    ) -> None:
        """
        Parameters
        ----------
        model_size: str
            One of the model sizes implemented by whisper/whisperx. Default is None,
            which selects large-v2 if cuda is available and small if not (cpu).
            For better accuracy, use larger models: large-v2 > medium > small > base > tiny
        device: str
            PyTorch device to perform computations on. Default is None, which auto
            detects the correct device.
        precision: 'float32' | 'float16' | 'int8'
            Precision to perform prediction with. Default is None, which selects
            float32 if cuda is available (for better accuracy) and int8 if not (cpu).
        """
        self._config_manager = TranscriberConfigManager()
        self._type_checker = TypeChecker()

        if device is None:
            device = get_compute_device()
        if precision is None:
            # Use float32 for GPU for better accuracy (uses more memory)
            precision = "float32" if torch.cuda.is_available() else "int8"
        if model_size is None:
            # Use small instead of tiny for CPU to improve accuracy
            # For GPU, use large-v2 (best accuracy)
            model_size = "large-v2" if torch.cuda.is_available() else "small"

        # check valid inputs
        assert_valid_torch_device(device)
        self._config_manager.assert_valid_model_size(model_size)
        self._config_manager.assert_valid_precision(precision)

        self._precision = precision
        self._device = device
        self._model_size = model_size
        # faster-whisper uses "cpu" or "cuda" for device
        device_str = "cuda" if self._device.startswith("cuda") else "cpu"
        self._model = WhisperModel(
            self._model_size,
            device=device_str,
            compute_type=self._precision,
        )

    def transcribe(
        self,
        audio_file_path: str,
        iso6391_lang_code: str or None = "ja",
        batch_size: int = None,
    ) -> Transcription:
        """
        Transcribes the media file

        Parameters
        ----------
        audio_file_path: str
            Absolute path to the audio or video file to transcribe.
        iso6391_lang_code: str or None
            ISO 639-1 language code to transcribe the media in. Default is "ja" (Japanese)
            for better accuracy. Set to None to auto-detect (not recommended for Japanese-focused use).
        batch_size: int = None
            Batch size for transcription. Default is None, which selects:
            - 32 for GPU (better accuracy, uses more memory)
            - 16 for CPU
            Reduce if low in GPU memory.
        Returns
        -------
        Transcription
            the media file transcription
        """
        editor = MediaEditor()
        media_file = editor.instantiate_as_temporal_media_file(audio_file_path)
        media_file.assert_exists()
        media_file.assert_has_audio_stream()

        if iso6391_lang_code is not None:
            self._config_manager.assert_valid_language(iso6391_lang_code)

        # Auto-adjust batch size for better accuracy on GPU
        if batch_size is None:
            batch_size = 32 if torch.cuda.is_available() else 16

        # Use faster-whisper to transcribe with word timestamps
        segments, info = self._model.transcribe(
            media_file.path,
            language=iso6391_lang_code,
            beam_size=5,
            batch_size=batch_size,
            word_timestamps=True,
        )

        # Convert faster-whisper segments to our format
        detected_language = info.language if hasattr(info, "language") else iso6391_lang_code or "en"
        
        # Collect all segments (segments is a generator)
        all_segments = []
        for segment in segments:
            all_segments.append(segment)
        
        if len(all_segments) == 0:
            err = "Media file '{}' contains no active speech.".format(media_file.path)
            logging.error(err)
            raise NoSpeechError(err)

        # Build character-level timestamps from word-level timestamps
        char_info = []
        
        for seg_idx, segment in enumerate(all_segments):
            segment_text = segment.text.strip()
            if not segment_text:
                continue
                
            # Get words from segment (words is a list when word_timestamps=True)
            words = list(segment.words) if hasattr(segment, "words") and segment.words else []
            
            # If we have word timestamps, use them to create character timestamps
            if words:
                for word in words:
                    word_text = word.word
                    word_start = word.start
                    word_end = word.end
                    
                    # Calculate duration per character in this word
                    word_duration = word_end - word_start
                    num_chars = len(word_text)
                    
                    if num_chars > 0:
                        char_duration = word_duration / num_chars
                        for i, char in enumerate(word_text):
                            char_start = word_start + (i * char_duration)
                            char_end = word_start + ((i + 1) * char_duration)
                            
                            char_info.append({
                                "char": char,
                                "start_time": char_start,
                                "end_time": char_end,
                                "speaker": None,
                            })
                    else:
                        # Handle empty word (shouldn't happen, but just in case)
                        char_info.append({
                            "char": " ",
                            "start_time": word_start,
                            "end_time": word_end,
                            "speaker": None,
                        })
            else:
                # Fallback: distribute segment time evenly across characters
                segment_start = segment.start
                segment_end = segment.end
                segment_duration = segment_end - segment_start
                num_chars = len(segment_text)
                
                if num_chars > 0:
                    char_duration = segment_duration / num_chars
                    for i, char in enumerate(segment_text):
                        char_start = segment_start + (i * char_duration)
                        char_end = segment_start + ((i + 1) * char_duration)
                        
                        char_info.append({
                            "char": char,
                            "start_time": char_start,
                            "end_time": char_end,
                            "speaker": None,
                        })
                else:
                    # Empty segment
                    char_info.append({
                        "char": " ",
                        "start_time": segment_start,
                        "end_time": segment_end,
                        "speaker": None,
                    })
            
            # Add space after segment if not the last segment
            if seg_idx < len(all_segments) - 1:
                char_info.append({
                    "char": " ",
                    "start_time": segment.end,
                    "end_time": segment.end + 0.1,  # Small gap
                    "speaker": None,
                })

        transcription_dict = {
            "source_software": "faster-whisper",
            "time_created": datetime.now(),
            "language": detected_language,
            "num_speakers": None,
            "char_info": char_info,
        }
        return Transcription(transcription_dict)

    def detect_language(self, media_file: AudioFile) -> str:
        """
        Detects the language of the media file

        Parameters
        ----------
        media_file: AudioFile
            the media file to detect the language of

        Returns
        -------
        str
            the ISO 639-1 language code of the media file
        """
        self._type_checker.assert_type(media_file, "media_file", (AudioFile))
        media_file.assert_exists()
        media_file.assert_has_audio_stream()

        # faster-whisper detects language during transcription
        segments, info = self._model.transcribe(
            media_file.path,
            language=None,  # Auto-detect
            beam_size=5,
        )
        # Consume the generator to get language info
        list(segments)  # Consume generator
        return info.language if hasattr(info, "language") else "en"


class TranscriberConfigManager(ConfigManager):
    """
    A class for getting information about and validating Transcriber
    configuration settings.
    """

    def __init__(self):
        """
        Parameters
        ----------
        None
        """
        super().__init__()

    def check_valid_config(self, config: dict) -> str or None:
        """
        Checks that 'config' contains valid configuration settings. Returns None if
        valid, a descriptive error message if invalid.

        Parameters
        ----------
        config: dict
            A dictionary containing the configuration settings for WhisperXTranscriber.

        Returns
        -------
        str or None
            None if the inputs are valid, otherwise an error message.
        """
        # type check inputs
        setting_checkers = {
            "language": self.check_valid_language,
            "model_size": self.check_valid_model_size,
            "precision": self.check_valid_precision,
        }

        # existence check
        missing_keys = find_missing_dict_keys(config, setting_checkers.keys())
        if len(missing_keys) != 0:
            return "WhisperXTranscriber missing configuration settings: {}".format(
                missing_keys
            )

        # value checks
        for setting, checker in setting_checkers.items():
            # None values = default values (depends on the compute device)
            if config[setting] is None:
                continue
            err = checker(config[setting])
            if err is not None:
                return err

        return None

    def get_valid_model_sizes(self) -> list[str]:
        """
        Returns the valid model sizes to transcribe with whisperx

        Parameters
        ----------
        None

        Returns
        -------
        list[str]
            list of valid model sizes to transcribe with whisperx
        """
        valid_model_sizes = [
            "tiny",
            "base",
            "small",
            "medium",
            "large-v1",
            "large-v2",
        ]
        return valid_model_sizes

    def check_valid_model_size(self, model_size: str) -> str or None:
        """
        Checks if 'model_size' is valid

        Parameters
        ----------
        model_size: str
            The transcription model size

        Returns
        -------
        str or None
            None if 'model_size' is valid. A descriptive error message if 'model_size'
            is invalid
        """
        if model_size not in self.get_valid_model_sizes():
            msg = "Invalid whisper model size '{}'. Must be one of: {}." "".format(
                model_size, self.get_valid_model_sizes()
            )
            return msg

        return None

    def is_valid_model_size(self, model_size: str) -> bool:
        """
        Returns True is 'model_size' is valid, False if not

        Parameters
        ----------
        model_size: str
            The transcription model size

        Returns
        -------
        bool
            True is 'model_size' is valid, False if not
        """
        msg = self.check_valid_model_size(model_size)
        if msg is None:
            return True
        else:
            return False

    def assert_valid_model_size(self, model_size: str) -> None:
        """
        Raises an Error if 'model_size' is invalid

        Parameters
        ----------
        model_size: str
            The transcription model size

        Raises
        ------
        WhisperXTranscriberConfigError: 'model_size' is invalid
        """
        msg = self.check_valid_model_size(model_size)
        if msg is not None:
            raise TranscriberConfigError(msg)

    def get_valid_languages(self) -> list[str]:
        """
        Returns the valid languages to transcribe with whisperx

        - See https://github.com/m-bain/whisperX#other-languages for updated lang info

        Parameters
        ----------
        None

        Returns
        -------
        list[str]:
            list of ISO 639-1 language codes of languages that can be transcribed
        """
        valid_languages = [
            "en",  # english
            "fr",  # french
            "de",  # german
            "es",  # spanish
            "it",  # italian
            "ja",  # japanese
            "zh",  # chinese
            "nl",  # dutch
            "uk",  # ukrainian
            "pt",  # portuguese
        ]
        return valid_languages

    def check_valid_language(self, iso6391_lang_code: str) -> str or None:
        """
        Checks if 'iso6391_lang_code' is a valid ISO 639-1 language code for whisperx to
        transcribe

        Parameters
        ----------
        iso6391_lang_code: str
            The language code to check

        Returns
        -------
        str or None
            None if 'iso6391_lang_code' is a valid ISO 639-1 language code for whisperx
            to transcribe. A descriptive error message if 'iso6391_lang_code' is invalid
        """
        if iso6391_lang_code not in self.get_valid_languages():
            msg = "Invalid ISO 639-1 language '{}'. Must be one of: {}." "".format(
                iso6391_lang_code, self.get_valid_languages()
            )
            return msg

        return None

    def is_valid_language(self, iso6391_lang_code: str) -> bool:
        """
        Returns True if 'iso6391_lang_code' is a valid ISO 639-1 language code for
        whisperx to transcribe, False if not

        Parameters
        ----------
        iso6391_lang_code: str
            The language code to check

        Returns
        -------
        bool
            True if 'iso6391_lang_code' is a valid ISO 639-1 language code for whisperx
            to transcribe, False if not
        """
        msg = self.check_valid_language(iso6391_lang_code)
        if msg is None:
            return True
        else:
            return False

    def assert_valid_language(self, iso6391_lang_code: str) -> None:
        """
        Raises TranscriptionError if 'iso6391_lang_code' is not a valid ISO 639-1
        language code for whisperx to transcribe in

        Parameters
        ----------
        iso6391_lang_code: str
            The language code to check

        Raises
        ------
        WhisperXTranscriberConfigError: if 'iso6391_lang_code' is not a valid
        ISO 639-1 language code for whisperx to transcribe in
        """
        msg = self.check_valid_language(iso6391_lang_code)
        if msg is not None:
            raise TranscriberConfigError(msg)

    def get_valid_precisions(self) -> list[str]:
        """
        Returns the valid precisions to transcribe with whisperx

        Parameters
        ----------
        None

        Returns
        -------
        list[str]:
            list of compute types that can be used to transcribe
        """
        valid_precisions = [
            "float32",
            "float16",
            "int8",
        ]
        return valid_precisions

    def check_valid_precision(self, precision: str) -> str or None:
        """
        Checks if 'precision' is valid to transcribe with whisperx

        Parameters
        ----------
        precision: str
            The precision to check

        Returns
        -------
        str or None
            None if 'precision' is valid. A descriptive error message if invalid
        """
        if precision not in self.get_valid_precisions():
            msg = "Invalid compute type '{}'. Must be one of: {}." "".format(
                precision, self.get_valid_precisions()
            )
            return msg

        return None

    def is_valid_precision(self, precision: str) -> bool:
        """
        Returns True if 'precision' is valid to transcribe with whisperx, False if not

        Parameters
        ----------
        precision: str
            The precision to check

        Returns
        -------
        bool
            True if 'precision' is valid to transcribe with whisperx, False if not
        """
        msg = self.check_valid_precision(precision)
        if msg is None:
            return True
        else:
            return False

    def assert_valid_precision(self, precision: str) -> None:
        """
        Raises TranscriptionError if 'precision' is invalid to transcribe with whisperx

        Parameters
        ----------
        precision: str
            The precision to check

        Returns
        -------
        None

        Raises
        ------
        WhisperXTranscriberConfigError: if 'precision' is invalid to transcribe with
        whisperx
        """
        msg = self.check_valid_precision(precision)
        if msg is not None:
            raise TranscriberConfigError(msg)
