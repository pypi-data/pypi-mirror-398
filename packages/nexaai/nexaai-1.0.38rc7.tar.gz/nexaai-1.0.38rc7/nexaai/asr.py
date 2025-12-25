"""
ASR (Automatic Speech Recognition) wrapper for nexaai.
Provides high-level Python API for ASR operations.
"""

import ctypes
import logging
from typing import Callable, List, Optional

from .internal.model_loader import ModelLoaderMixin
from .internal.native_plugin import (
    convert_from_mlx_profile_data,
    convert_to_mlx_asr_config,
    get_mlx_asr_class,
    is_native_plugin,
    setup_mlx_imports,
)
from .nexa_sdk._lib import _lib
from .nexa_sdk.asr import (
    ml_ASR,
    ml_asr_transcription_callback,
    ml_ASRConfig,
    ml_AsrCreateInput,
    ml_AsrListSupportedLanguagesInput,
    ml_AsrListSupportedLanguagesOutput,
    ml_AsrStreamBeginInput,
    ml_AsrStreamBeginOutput,
    ml_ASRStreamConfig,
    ml_AsrStreamPushAudioInput,
    ml_AsrStreamStopInput,
    ml_AsrTranscribeInput,
    ml_AsrTranscribeOutput,
)
from .nexa_sdk.error import check_error
from .nexa_sdk.types import ModelConfig, ProfileData

logger = logging.getLogger(__name__)


class ASR(ModelLoaderMixin):
    """Automatic Speech Recognition wrapper."""

    def __init__(
        self,
        model_path: str,
        tokenizer_path: Optional[str] = None,
        model_name: Optional[str] = None,
        config: Optional[ModelConfig] = None,
        language: Optional[str] = None,
        plugin_id: Optional[str] = None,
        device_id: Optional[str] = None,
        license_id: Optional[str] = None,
        license_key: Optional[str] = None,
    ):
        """
        Create and initialize an ASR instance.

        Args:
            model_path: Path to the model file.
            tokenizer_path: Path to the tokenizer file. If None, uses model_path.
            model_name: Name of the model. If None, uses model_path.
            config: Model configuration. If None, uses default config.
            language: Language code for ASR. If None, uses default.
            plugin_id: Plugin to use for the model. If None, uses default.
            device_id: Device to use for the model. If None, uses default device.
            license_id: License ID for loading NPU models.
            license_key: License key for loading NPU models.
        """
        if config is None:
            config = ModelConfig()

        if tokenizer_path is None:
            tokenizer_path = model_path

        if model_name is None:
            model_name = model_path

        if not model_name:
            model_name = model_path

        # Check if we should use native Python calls (for MLX plugin)
        self._is_native = False
        if is_native_plugin(plugin_id):
            if not setup_mlx_imports():
                raise RuntimeError(
                    f'Failed to setup MLX imports for native plugin {plugin_id}. '
                    f'Cannot fallback to C interface as it would cause GIL conflicts.'
                )
            try:
                self._init_mlx_native(
                    model_path=model_path,
                    tokenizer_path=tokenizer_path,
                    model_name=model_name,
                    config=config,
                    language=language,
                    device_id=device_id,
                )
                return  # Native initialization successful, skip C interface
            except Exception as e:
                raise RuntimeError(
                    f'Failed to initialize MLX native for plugin {plugin_id}: {e}. '
                    f'Cannot fallback to C interface as it would cause GIL conflicts.'
                ) from e

        # C interface initialization (default or fallback)
        c_config = config.to_c_struct()

        model_name_bytes = model_name.encode('utf-8')
        model_path_bytes = model_path.encode('utf-8')
        tokenizer_path_bytes = tokenizer_path.encode('utf-8') if tokenizer_path else b''
        language_bytes = language.encode('utf-8') if language else None
        plugin_id_str = plugin_id if plugin_id else ''
        plugin_id_buf = ctypes.create_string_buffer(plugin_id_str.encode('utf-8'))
        device_id_buf = ctypes.create_string_buffer(device_id.encode('utf-8')) if device_id else None
        license_id_buf = ctypes.create_string_buffer(license_id.encode('utf-8')) if license_id else None
        license_key_buf = ctypes.create_string_buffer(license_key.encode('utf-8')) if license_key else None

        model_name_buf = ctypes.create_string_buffer(model_name_bytes)
        model_path_buf = ctypes.create_string_buffer(model_path_bytes)
        tokenizer_path_buf = ctypes.create_string_buffer(tokenizer_path_bytes) if tokenizer_path_bytes else None
        language_buf = ctypes.create_string_buffer(language_bytes) if language_bytes else None

        c_input = ml_AsrCreateInput(
            model_name=ctypes.cast(model_name_buf, ctypes.c_char_p),
            model_path=ctypes.cast(model_path_buf, ctypes.c_char_p),
            tokenizer_path=ctypes.cast(tokenizer_path_buf, ctypes.c_char_p) if tokenizer_path_buf else None,
            config=c_config,
            language=ctypes.cast(language_buf, ctypes.c_char_p) if language_buf else None,
            plugin_id=ctypes.cast(plugin_id_buf, ctypes.c_char_p) if plugin_id_buf else None,
            device_id=ctypes.cast(device_id_buf, ctypes.c_char_p) if device_id_buf else None,
            license_id=ctypes.cast(license_id_buf, ctypes.c_char_p) if license_id_buf else None,
            license_key=ctypes.cast(license_key_buf, ctypes.c_char_p) if license_key_buf else None,
        )

        self._string_refs = [
            model_name_buf,
            model_path_buf,
            tokenizer_path_buf,
            language_buf,
            plugin_id_buf,
            device_id_buf,
            license_id_buf,
            license_key_buf,
        ]

        handle_ptr = ctypes.POINTER(ml_ASR)()
        error_code = _lib.ml_asr_create(ctypes.pointer(c_input), ctypes.byref(handle_ptr))
        check_error(error_code)

        if not handle_ptr:
            raise RuntimeError('Failed to create ASR instance')

        self._handle = handle_ptr
        self._config = config

    def _init_mlx_native(
        self,
        model_path: str,
        tokenizer_path: str,
        model_name: str,
        config: ModelConfig,
        language: Optional[str],
        device_id: Optional[str],
    ):
        """
        Initialize ASR using MLX native Python implementation.

        Args:
            model_path: Path to the model file
            tokenizer_path: Path to the tokenizer file
            model_name: Name of the model
            config: Model configuration
            language: Language code
            device_id: Device ID (e.g., 'cpu', 'gpu')
        """
        MLXASR = get_mlx_asr_class()

        # Create MLX ASR instance
        self._mlx_asr = MLXASR(
            model_path=model_path,
            tokenizer_path=tokenizer_path if tokenizer_path else None,
            language=language,
        )

        self._is_native = True
        self._config = config
        self._handle = None  # No C handle for native implementation

    def __del__(self):
        """Destroy ASR instance and free associated resources."""
        if hasattr(self, '_is_native') and self._is_native:
            # Native implementation cleanup
            if hasattr(self, '_mlx_asr') and self._mlx_asr:
                try:
                    self._mlx_asr.destroy()
                except Exception as e:
                    logger.warning(f'Error during MLX native ASR cleanup: {e}')
                self._mlx_asr = None
        elif hasattr(self, '_handle') and self._handle:
            # C interface cleanup
            try:
                _lib.ml_asr_destroy(self._handle)
            except Exception as e:
                logger.warning(f'Error during ASR cleanup: {e}')
            self._handle = None

    @classmethod
    def _get_model_type(cls) -> str:
        return 'asr'

    @classmethod
    def _extract_model_params_from_manifest(
        cls,
        manifest,
        model_path: str,
        repo_id: str,
        store,
        **kwargs,
    ) -> dict:
        """Extract ASR-specific parameters from manifest."""
        tokenizer_path = None
        if manifest.tokenizer_file.name:
            tokenizer_path_obj = store.modelfile_path(repo_id, manifest.tokenizer_file.name)
            if tokenizer_path_obj.exists():
                tokenizer_path = str(tokenizer_path_obj)

        model_name = manifest.model_name or repo_id
        if not model_name:
            model_name = repo_id

        plugin_id = manifest.plugin_id.strip() if manifest.plugin_id else None
        if not plugin_id:
            plugin_id = kwargs.pop('plugin_id', None)
        else:
            # Remove plugin_id from kwargs if manifest has it (to avoid passing it twice)
            kwargs.pop('plugin_id', None)
        if plugin_id:
            plugin_id = plugin_id.strip() if isinstance(plugin_id, str) else plugin_id
            if not plugin_id:
                plugin_id = None

        if not plugin_id:
            plugin_id = cls._get_default_plugin_id()

        device_id = manifest.device_id.strip() if manifest.device_id else None
        if not device_id:
            device_id = kwargs.pop('device_id', None)
        if device_id:
            device_id = device_id.strip() if isinstance(device_id, str) else device_id
            if not device_id:
                device_id = None

        return {
            'model_path': str(model_path),
            'tokenizer_path': tokenizer_path,
            'model_name': model_name,
            'plugin_id': plugin_id,
            'device_id': device_id,
            **kwargs,
        }

    @classmethod
    def _create_instance(cls, **params) -> 'ASR':
        """Create ASR instance with given parameters."""
        return cls(**params)

    @classmethod
    def _get_default_plugin_id(cls) -> str:
        """Get default plugin ID for ASR."""
        return 'metal'

    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        timestamps: Optional[str] = None,
        beam_size: int = 5,
    ) -> 'TranscribeResult':
        """
        Transcribe audio file to text.

        Args:
            audio_path: Path to the audio file.
            language: Language code. If None, uses default.
            timestamps: Timestamp format. If None, no timestamps.
            beam_size: Beam size for decoding.

        Returns:
            TranscribeResult containing transcript and metadata.

        Raises:
            NexaError: If transcription fails.
        """
        if self._is_native:
            return self._mlx_transcribe(audio_path, language, timestamps, beam_size)

        asr_config = ml_ASRConfig(
            timestamps=timestamps.encode('utf-8') if timestamps else None,
            beam_size=ctypes.c_int32(beam_size),
            stream=ctypes.c_bool(False),
        )

        audio_path_bytes = audio_path.encode('utf-8')
        audio_path_buf = ctypes.create_string_buffer(audio_path_bytes)
        language_bytes = language.encode('utf-8') if language else None
        language_buf = ctypes.create_string_buffer(language_bytes) if language_bytes else None

        c_input = ml_AsrTranscribeInput(
            audio_path=ctypes.cast(audio_path_buf, ctypes.c_char_p),
            language=ctypes.cast(language_buf, ctypes.c_char_p) if language_buf else None,
            config=ctypes.pointer(asr_config),
        )

        c_output = ml_AsrTranscribeOutput()
        error_code = _lib.ml_asr_transcribe(self._handle, ctypes.pointer(c_input), ctypes.pointer(c_output))
        check_error(error_code)

        return self._extract_result(c_output)

    def _mlx_transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        timestamps: Optional[str] = None,
        beam_size: int = 5,
    ) -> 'TranscribeResult':
        """Transcribe using MLX native implementation."""
        # Convert config
        mlx_config = convert_to_mlx_asr_config(
            timestamps=timestamps,
            beam_size=beam_size,
            stream=False,
        )

        # Call MLX transcribe
        result = self._mlx_asr.transcribe(
            audio_path=audio_path,
            language=language,
            config=mlx_config,
        )

        # Extract profiling data if available
        profiling_data = None
        if hasattr(self._mlx_asr, 'get_profiling_data'):
            profiling_data = self._mlx_asr.get_profiling_data()

        profile_data = convert_from_mlx_profile_data(profiling_data) if profiling_data else ProfileData()

        return TranscribeResult(
            transcript=result.transcript,
            confidence_scores=list(result.confidence_scores),
            timestamps=[(ts[0], ts[1]) for ts in result.timestamps],
            profile_data=profile_data,
        )

    def _extract_result(self, c_output: ml_AsrTranscribeOutput) -> 'TranscribeResult':
        """Extract TranscribeResult from C output structure."""
        result = c_output.result
        transcript = ''
        if result.transcript:
            transcript = result.transcript.decode('utf-8')

        confidence_scores = []
        if result.confidence_scores and result.confidence_count > 0:
            confidence_scores = [result.confidence_scores[i] for i in range(result.confidence_count)]

        timestamps = []
        if result.timestamps and result.timestamp_count > 0:
            timestamps = [result.timestamps[i] for i in range(result.timestamp_count)]

        profile_data = ProfileData.from_c_struct(c_output.profile_data)
        return TranscribeResult(
            transcript=transcript,
            confidence_scores=confidence_scores,
            timestamps=timestamps,
            profile_data=profile_data,
        )

    def list_supported_languages(self) -> List[str]:
        """
        List supported languages.

        Returns:
            List of language codes.

        Raises:
            NexaError: If query fails.
        """
        if self._is_native:
            return self._mlx_asr.list_supported_languages()

        c_input = ml_AsrListSupportedLanguagesInput(reserved=None)
        c_output = ml_AsrListSupportedLanguagesOutput()

        error_code = _lib.ml_asr_list_supported_languages(
            self._handle,
            ctypes.pointer(c_input),
            ctypes.pointer(c_output),
        )
        check_error(error_code)

        languages = []
        if c_output.language_codes and c_output.language_count > 0:
            for i in range(c_output.language_count):
                lang_ptr = c_output.language_codes[i]
                if lang_ptr:
                    languages.append(lang_ptr.decode('utf-8'))
            _lib.ml_free(c_output.language_codes)

        return languages

    def stream_begin(
        self,
        language: Optional[str] = None,
        on_transcription: Optional[Callable[[str], None]] = None,
        chunk_duration: float = 0.5,
        overlap_duration: float = 0.1,
        sample_rate: int = 16000,
        max_queue_size: int = 10,
        buffer_size: int = 4096,
        timestamps: Optional[str] = None,
        beam_size: int = 5,
    ) -> None:
        """
        Begin streaming ASR transcription.

        Args:
            language: Language code. If None, uses default.
            on_transcription: Callback function for transcription results.
            chunk_duration: Audio chunk duration in seconds.
            overlap_duration: Overlap duration in seconds.
            sample_rate: Audio sample rate.
            max_queue_size: Maximum queue size.
            buffer_size: Buffer size.
            timestamps: Timestamp format. If None, no timestamps.
            beam_size: Beam size for decoding.

        Raises:
            NexaError: If stream begin fails.
        """
        stream_config = ml_ASRStreamConfig(
            chunk_duration=ctypes.c_float(chunk_duration),
            overlap_duration=ctypes.c_float(overlap_duration),
            sample_rate=ctypes.c_int32(sample_rate),
            max_queue_size=ctypes.c_int32(max_queue_size),
            buffer_size=ctypes.c_int32(buffer_size),
            timestamps=timestamps.encode('utf-8') if timestamps else None,
            beam_size=ctypes.c_int32(beam_size),
        )

        transcription_callback = None
        if on_transcription:

            def _transcription_callback(transcript_ptr: ctypes.c_char_p, user_data_ptr: ctypes.c_void_p) -> None:
                if transcript_ptr:
                    transcript = transcript_ptr.decode('utf-8')
                    on_transcription(transcript)

            transcription_callback = ml_asr_transcription_callback(_transcription_callback)

        language_bytes = language.encode('utf-8') if language else None
        language_buf = ctypes.create_string_buffer(language_bytes) if language_bytes else None

        c_input = ml_AsrStreamBeginInput(
            stream_config=ctypes.pointer(stream_config),
            language=ctypes.cast(language_buf, ctypes.c_char_p) if language_buf else None,
            on_transcription=transcription_callback,
            user_data=None,
        )

        c_output = ml_AsrStreamBeginOutput()
        error_code = _lib.ml_asr_stream_begin(self._handle, ctypes.pointer(c_input), ctypes.pointer(c_output))
        check_error(error_code)

        self._transcription_callback_ref = transcription_callback

    def stream_push_audio(self, audio_data: List[float]) -> None:
        """
        Push audio data for streaming transcription.

        Args:
            audio_data: List of audio samples (float values).

        Raises:
            NexaError: If push fails.
        """
        length = len(audio_data)
        audio_array = (ctypes.c_float * length)(*audio_data)

        c_input = ml_AsrStreamPushAudioInput(
            audio_data=ctypes.cast(audio_array, ctypes.POINTER(ctypes.c_float)),
            length=ctypes.c_int32(length),
        )

        error_code = _lib.ml_asr_stream_push_audio(self._handle, ctypes.pointer(c_input))
        check_error(error_code)

    def stream_stop(self, graceful: bool = True) -> None:
        """
        Stop streaming transcription.

        Args:
            graceful: If True, wait for current processing to complete.

        Raises:
            NexaError: If stop fails.
        """
        c_input = ml_AsrStreamStopInput(graceful=ctypes.c_bool(graceful))
        error_code = _lib.ml_asr_stream_stop(self._handle, ctypes.pointer(c_input))
        check_error(error_code)


class TranscribeResult:
    """Result of ASR transcription."""

    def __init__(
        self,
        transcript: str,
        confidence_scores: List[float],
        timestamps: List[float],
        profile_data: ProfileData,
    ):
        self.transcript = transcript
        self.confidence_scores = confidence_scores
        self.timestamps = timestamps
        self.profile_data = profile_data

    def __str__(self) -> str:
        return self.transcript

    def __repr__(self) -> str:
        transcript_preview = self.transcript[:50] + '...' if len(self.transcript) > 50 else self.transcript
        return (
            f'TranscribeResult(transcript={transcript_preview}, '
            f'confidence_scores={len(self.confidence_scores)}, '
            f'timestamps={len(self.timestamps)})'
        )
