"""
Error codes, log levels, and error-related definitions for nexa-sdk.
This module contains C-level definitions (error codes, log levels, callbacks).
"""

import ctypes
from typing import Optional

from ._lib import _lib

# Error codes from ml.h
ML_SUCCESS = 0
ML_ERROR_COMMON_UNKNOWN = -100000
ML_ERROR_COMMON_INVALID_INPUT = -100001
ML_ERROR_COMMON_MEMORY_ALLOCATION = -100003
ML_ERROR_COMMON_FILE_NOT_FOUND = -100004
ML_ERROR_COMMON_NOT_INITIALIZED = -100007
ML_ERROR_COMMON_NOT_SUPPORTED = -100013
ML_ERROR_COMMON_MODEL_LOAD = -100201
ML_ERROR_COMMON_MODEL_INVALID = -100203
ML_ERROR_COMMON_LICENSE_INVALID = -100601
ML_ERROR_COMMON_LICENSE_EXPIRED = -100602

# LLM ERRORS (200xxx)
ML_ERROR_LLM_TOKENIZATION_FAILED = -200001
ML_ERROR_LLM_TOKENIZATION_CONTEXT_LENGTH = -200004
ML_ERROR_LLM_GENERATION_FAILED = -200101
ML_ERROR_LLM_GENERATION_PROMPT_TOO_LONG = -200103

# VLM ERRORS (201xxx)
ML_ERROR_VLM_IMAGE_LOAD = -201001
ML_ERROR_VLM_IMAGE_FORMAT = -201002
ML_ERROR_VLM_AUDIO_LOAD = -201101
ML_ERROR_VLM_AUDIO_FORMAT = -201102
ML_ERROR_VLM_GENERATION_FAILED = -201201

# Embedding ERRORS (202xxx)
ML_ERROR_EMBEDDING_GENERATION = -202301
ML_ERROR_EMBEDDING_DIMENSION = -202302

# Reranking ERRORS (203xxx)
ML_ERROR_RERANK_FAILED = -203401
ML_ERROR_RERANK_INPUT = -203402

# Image Generation ERRORS (204xxx)
ML_ERROR_IMAGEGEN_GENERATION = -204501
ML_ERROR_IMAGEGEN_PROMPT = -204502
ML_ERROR_IMAGEGEN_DIMENSION = -204503

# ASR ERRORS (205xxx)
ML_ERROR_ASR_TRANSCRIPTION = -205001
ML_ERROR_ASR_AUDIO_FORMAT = -205002
ML_ERROR_ASR_LANGUAGE = -205003
ML_ERROR_ASR_STREAM_NOT_STARTED = -205010
ML_ERROR_ASR_STREAM_ALREADY_ACTIVE = -205011
ML_ERROR_ASR_STREAM_INVALID_AUDIO = -205012
ML_ERROR_ASR_STREAM_BUFFER_FULL = -205013
ML_ERROR_ASR_STREAM_CALLBACK_ERROR = -205014

# TTS ERRORS (206xxx)
ML_ERROR_TTS_SYNTHESIS = -206001
ML_ERROR_TTS_VOICE = -206002
ML_ERROR_TTS_AUDIO_FORMAT = -206003

# CV ERRORS (207xxx)
ML_ERROR_CV_OCR_DETECTION = -207001
ML_ERROR_CV_OCR_RECOGNITION = -207002
ML_ERROR_CV_OCR_FAILED = -207003

# Diarization ERRORS (208xxx)
ML_ERROR_DIARIZE_AUDIO_LOAD = -208001
ML_ERROR_DIARIZE_SEGMENTATION = -208101
ML_ERROR_DIARIZE_EMBEDDING = -208102
ML_ERROR_DIARIZE_CLUSTERING = -208103

# Log levels
ML_LOG_LEVEL_TRACE = 0
ML_LOG_LEVEL_DEBUG = 1
ML_LOG_LEVEL_INFO = 2
ML_LOG_LEVEL_WARN = 3
ML_LOG_LEVEL_ERROR = 4

# Callback types
ml_log_callback = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p)

# Function signatures
_lib.ml_get_error_message.argtypes = [ctypes.c_int32]
_lib.ml_get_error_message.restype = ctypes.c_char_p


# ============================================================================
# Python Exception Classes
# ============================================================================

# ============================================================================
# Error Handling Functions
# ============================================================================


def ml_get_error_message(error_code: int) -> str:
    """
    Get error message string for error code.

    Args:
        error_code: The error code.

    Returns:
        Error message string.
    """
    result = _lib.ml_get_error_message(error_code)
    if result:
        return result.decode('utf-8')
    return f'Unknown error code: {error_code}'


def check_error(error_code: int) -> None:
    """
    Check error code and raise appropriate exception if not success.

    Args:
        error_code: The error code returned from a C function.

    Raises:
        NexaError: Appropriate exception based on error code.
    """
    if error_code == ML_SUCCESS:
        return

    # Get the exception class from the map, or use base NexaError
    exception_class = _ERROR_MAP.get(error_code, NexaError)
    raise exception_class(error_code)


# ============================================================================
# Python Exception Classes
# ============================================================================


class NexaError(Exception):
    """Base exception for all nexa-sdk errors."""

    def __init__(self, error_code: int, message: Optional[str] = None):
        self.error_code = error_code
        if message is None:
            message = ml_get_error_message(error_code)
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return f'[{self.error_code}] {self.message}'


class NexaCommonError(NexaError):
    """Base class for common errors."""

    pass


class NexaUnknownError(NexaCommonError):
    """Unknown error."""

    pass


class NexaInvalidInputError(NexaCommonError):
    """Invalid input parameters or handle."""

    pass


class NexaMemoryAllocationError(NexaCommonError):
    """Memory allocation failed."""

    pass


class NexaFileNotFoundError(NexaCommonError):
    """File not found or inaccessible."""

    pass


class NexaNotInitializedError(NexaCommonError):
    """Library not initialized."""

    pass


class NexaNotSupportedError(NexaCommonError):
    """Operation not supported."""

    pass


class NexaModelLoadError(NexaCommonError):
    """Model loading failed."""

    pass


class NexaModelInvalidError(NexaCommonError):
    """Invalid model format."""

    pass


class NexaLicenseInvalidError(NexaCommonError):
    """Invalid license."""

    pass


class NexaLicenseExpiredError(NexaCommonError):
    """License expired."""

    pass


class NexaLLMError(NexaError):
    """Base class for LLM errors."""

    pass


class NexaLLMTokenizationError(NexaLLMError):
    """Tokenization failed."""

    pass


class NexaLLMTokenizationContextLengthError(NexaLLMError):
    """Context length exceeded."""

    pass


class NexaLLMGenerationError(NexaLLMError):
    """Text generation failed."""

    pass


class NexaLLMGenerationPromptTooLongError(NexaLLMError):
    """Input prompt too long."""

    pass


class NexaVLMError(NexaError):
    """Base class for VLM errors."""

    pass


class NexaVLMImageLoadError(NexaVLMError):
    """Image loading failed."""

    pass


class NexaVLMImageFormatError(NexaVLMError):
    """Unsupported image format."""

    pass


class NexaVLMAudioLoadError(NexaVLMError):
    """Audio loading failed."""

    pass


class NexaVLMAudioFormatError(NexaVLMError):
    """Unsupported audio format."""

    pass


class NexaVLMGenerationError(NexaVLMError):
    """Multimodal generation failed."""

    pass


class NexaEmbeddingError(NexaError):
    """Base class for Embedding errors."""

    pass


class NexaEmbeddingGenerationError(NexaEmbeddingError):
    """Embedding generation failed."""

    pass


class NexaEmbeddingDimensionError(NexaEmbeddingError):
    """Invalid embedding dimension."""

    pass


class NexaRerankError(NexaError):
    """Base class for Reranking errors."""

    pass


class NexaRerankFailedError(NexaRerankError):
    """Reranking failed."""

    pass


class NexaRerankInputError(NexaRerankError):
    """Invalid reranking input."""

    pass


class NexaImageGenError(NexaError):
    """Base class for Image Generation errors."""

    pass


class NexaImageGenGenerationError(NexaImageGenError):
    """Image generation failed."""

    pass


class NexaImageGenPromptError(NexaImageGenError):
    """Invalid image prompt."""

    pass


class NexaImageGenDimensionError(NexaImageGenError):
    """Invalid image dimensions."""

    pass


class NexaASRError(NexaError):
    """Base class for ASR errors."""

    pass


class NexaASRTranscriptionError(NexaASRError):
    """ASR transcription failed."""

    pass


class NexaASRAudioFormatError(NexaASRError):
    """Unsupported ASR audio format."""

    pass


class NexaASRLanguageError(NexaASRError):
    """Unsupported ASR language."""

    pass


class NexaASRStreamNotStartedError(NexaASRError):
    """Streaming not started."""

    pass


class NexaASRStreamAlreadyActiveError(NexaASRError):
    """Streaming already active."""

    pass


class NexaASRStreamInvalidAudioError(NexaASRError):
    """Invalid audio data."""

    pass


class NexaASRStreamBufferFullError(NexaASRError):
    """Audio buffer full."""

    pass


class NexaASRStreamCallbackError(NexaASRError):
    """Callback execution error."""

    pass


class NexaTTSError(NexaError):
    """Base class for TTS errors."""

    pass


class NexaTTSSynthesisError(NexaTTSError):
    """TTS synthesis failed."""

    pass


class NexaTTSVoiceError(NexaTTSError):
    """TTS voice not found."""

    pass


class NexaTTSAudioFormatError(NexaTTSError):
    """TTS audio format error."""

    pass


class NexaCVError(NexaError):
    """Base class for CV errors."""

    pass


class NexaCVOCRDetectionError(NexaCVError):
    """OCR text detection failed."""

    pass


class NexaCVOCRRecognitionError(NexaCVError):
    """OCR text recognition failed."""

    pass


class NexaCVOCRFailedError(NexaCVError):
    """OCR failed."""

    pass


class NexaDiarizeError(NexaError):
    """Base class for Diarization errors."""

    pass


class NexaDiarizeAudioLoadError(NexaDiarizeError):
    """Audio loading failed."""

    pass


class NexaDiarizeSegmentationError(NexaDiarizeError):
    """Segmentation model execution failed."""

    pass


class NexaDiarizeEmbeddingError(NexaDiarizeError):
    """Embedding extraction failed."""

    pass


class NexaDiarizeClusteringError(NexaDiarizeError):
    """Speaker clustering failed (PLDA/VBx)."""

    pass


# Error code to exception class mapping
_ERROR_MAP = {
    ML_ERROR_COMMON_UNKNOWN: NexaUnknownError,
    ML_ERROR_COMMON_INVALID_INPUT: NexaInvalidInputError,
    ML_ERROR_COMMON_MEMORY_ALLOCATION: NexaMemoryAllocationError,
    ML_ERROR_COMMON_FILE_NOT_FOUND: NexaFileNotFoundError,
    ML_ERROR_COMMON_NOT_INITIALIZED: NexaNotInitializedError,
    ML_ERROR_COMMON_NOT_SUPPORTED: NexaNotSupportedError,
    ML_ERROR_COMMON_MODEL_LOAD: NexaModelLoadError,
    ML_ERROR_COMMON_MODEL_INVALID: NexaModelInvalidError,
    ML_ERROR_COMMON_LICENSE_INVALID: NexaLicenseInvalidError,
    ML_ERROR_COMMON_LICENSE_EXPIRED: NexaLicenseExpiredError,
    ML_ERROR_LLM_TOKENIZATION_FAILED: NexaLLMTokenizationError,
    ML_ERROR_LLM_TOKENIZATION_CONTEXT_LENGTH: NexaLLMTokenizationContextLengthError,
    ML_ERROR_LLM_GENERATION_FAILED: NexaLLMGenerationError,
    ML_ERROR_LLM_GENERATION_PROMPT_TOO_LONG: NexaLLMGenerationPromptTooLongError,
    ML_ERROR_VLM_IMAGE_LOAD: NexaVLMImageLoadError,
    ML_ERROR_VLM_IMAGE_FORMAT: NexaVLMImageFormatError,
    ML_ERROR_VLM_AUDIO_LOAD: NexaVLMAudioLoadError,
    ML_ERROR_VLM_AUDIO_FORMAT: NexaVLMAudioFormatError,
    ML_ERROR_VLM_GENERATION_FAILED: NexaVLMGenerationError,
    ML_ERROR_EMBEDDING_GENERATION: NexaEmbeddingGenerationError,
    ML_ERROR_EMBEDDING_DIMENSION: NexaEmbeddingDimensionError,
    ML_ERROR_RERANK_FAILED: NexaRerankFailedError,
    ML_ERROR_RERANK_INPUT: NexaRerankInputError,
    ML_ERROR_IMAGEGEN_GENERATION: NexaImageGenGenerationError,
    ML_ERROR_IMAGEGEN_PROMPT: NexaImageGenPromptError,
    ML_ERROR_IMAGEGEN_DIMENSION: NexaImageGenDimensionError,
    ML_ERROR_ASR_TRANSCRIPTION: NexaASRTranscriptionError,
    ML_ERROR_ASR_AUDIO_FORMAT: NexaASRAudioFormatError,
    ML_ERROR_ASR_LANGUAGE: NexaASRLanguageError,
    ML_ERROR_ASR_STREAM_NOT_STARTED: NexaASRStreamNotStartedError,
    ML_ERROR_ASR_STREAM_ALREADY_ACTIVE: NexaASRStreamAlreadyActiveError,
    ML_ERROR_ASR_STREAM_INVALID_AUDIO: NexaASRStreamInvalidAudioError,
    ML_ERROR_ASR_STREAM_BUFFER_FULL: NexaASRStreamBufferFullError,
    ML_ERROR_ASR_STREAM_CALLBACK_ERROR: NexaASRStreamCallbackError,
    ML_ERROR_TTS_SYNTHESIS: NexaTTSSynthesisError,
    ML_ERROR_TTS_VOICE: NexaTTSVoiceError,
    ML_ERROR_TTS_AUDIO_FORMAT: NexaTTSAudioFormatError,
    ML_ERROR_CV_OCR_DETECTION: NexaCVOCRDetectionError,
    ML_ERROR_CV_OCR_RECOGNITION: NexaCVOCRRecognitionError,
    ML_ERROR_CV_OCR_FAILED: NexaCVOCRFailedError,
    ML_ERROR_DIARIZE_AUDIO_LOAD: NexaDiarizeAudioLoadError,
    ML_ERROR_DIARIZE_SEGMENTATION: NexaDiarizeSegmentationError,
    ML_ERROR_DIARIZE_EMBEDDING: NexaDiarizeEmbeddingError,
    ML_ERROR_DIARIZE_CLUSTERING: NexaDiarizeClusteringError,
}
