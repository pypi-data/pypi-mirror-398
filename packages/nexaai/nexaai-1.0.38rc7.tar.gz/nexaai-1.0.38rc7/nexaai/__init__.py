"""
NexaAI - Python SDK for Nexa AI ML library.

This package provides a Pythonic interface to the nexa-sdk machine learning library,
including support for LLMs, embeddings, and other ML operations.
"""

import atexit

# IMPORTANT: Preload CUDA libraries BEFORE importing _lib
# This ensures CUDA symbols are available when plugins are loaded
from .nexa_sdk._cuda import _find_cuda

_find_cuda()

from ._version import __version__
from .asr import ASR, TranscribeResult
from .core import _init_logging, get_device_list, get_plugin_list, setup_logging
from .cv import CV, BoundingBox, CVResult, CVResultItem
from .diarize import Diarize, DiarizeResult, SpeechSegment
from .embedding import Embedder, EmbedResult
from .image_gen import ImageGen, ImageGenResult
from .internal.types import DownloadProgressInfo, ModelInfo
from .llm import LLM, GenerateResult
from .models import download_model, list_models, remove_model
from .nexa_sdk._lib import _lib
from .nexa_sdk.error import (
    NexaASRAudioFormatError,
    NexaASRError,
    NexaASRLanguageError,
    NexaASRStreamAlreadyActiveError,
    NexaASRStreamBufferFullError,
    NexaASRStreamCallbackError,
    NexaASRStreamInvalidAudioError,
    NexaASRStreamNotStartedError,
    NexaASRTranscriptionError,
    NexaCommonError,
    NexaCVError,
    NexaCVOCRDetectionError,
    NexaCVOCRFailedError,
    NexaCVOCRRecognitionError,
    NexaDiarizeAudioLoadError,
    NexaDiarizeClusteringError,
    NexaDiarizeEmbeddingError,
    NexaDiarizeError,
    NexaDiarizeSegmentationError,
    NexaEmbeddingDimensionError,
    NexaEmbeddingError,
    NexaEmbeddingGenerationError,
    NexaError,
    NexaFileNotFoundError,
    NexaImageGenDimensionError,
    NexaImageGenError,
    NexaImageGenGenerationError,
    NexaImageGenPromptError,
    NexaInvalidInputError,
    NexaLicenseExpiredError,
    NexaLicenseInvalidError,
    NexaLLMError,
    NexaLLMGenerationError,
    NexaLLMGenerationPromptTooLongError,
    NexaLLMTokenizationContextLengthError,
    NexaLLMTokenizationError,
    NexaMemoryAllocationError,
    NexaModelInvalidError,
    NexaModelLoadError,
    NexaNotInitializedError,
    NexaNotSupportedError,
    NexaRerankError,
    NexaRerankFailedError,
    NexaRerankInputError,
    NexaTTSAudioFormatError,
    NexaTTSError,
    NexaTTSSynthesisError,
    NexaTTSVoiceError,
    NexaUnknownError,
    NexaVLMAudioFormatError,
    NexaVLMAudioLoadError,
    NexaVLMError,
    NexaVLMGenerationError,
    NexaVLMImageFormatError,
    NexaVLMImageLoadError,
    check_error,
    ml_get_error_message,
)
from .nexa_sdk.types import (
    GenerationConfig,
    KvCacheLoadInput,
    KvCacheSaveInput,
    LlmChatMessage,
    ModelConfig,
    ProfileData,
    SamplerConfig,
    VlmChatMessage,
    VlmContent,
)
from .rerank import Reranker, RerankResult
from .tts import TTS, SynthesizeResult
from .vlm import VLM


def version() -> str:
    """Get Python package version."""
    return __version__


def nexa_version() -> str:
    """Get Nexa SDK (C library) version."""
    return _lib.ml_version().decode('utf-8')


_init_logging()

check_error(_lib.ml_init())
atexit.register(lambda: check_error(_lib.ml_deinit()))

__all__ = [
    # Core functions
    'version',
    'nexa_version',
    'get_plugin_list',
    'get_device_list',
    # Logging
    'setup_logging',
    # Model management
    'download_model',
    'list_models',
    'remove_model',
    'ModelInfo',
    'DownloadProgressInfo',
    'FileProgressInfo',
    # LLM
    'LLM',
    'GenerateResult',
    # VLM
    'VLM',
    # ASR
    'ASR',
    'TranscribeResult',
    # TTS
    'TTS',
    'SynthesizeResult',
    # Embedding
    'Embedder',
    'EmbedResult',
    # Rerank
    'Reranker',
    'RerankResult',
    # Diarize
    'Diarize',
    'DiarizeResult',
    'SpeechSegment',
    # CV
    'CV',
    'CVResult',
    'CVResultItem',
    'BoundingBox',
    # ImageGen
    'ImageGen',
    'ImageGenResult',
    # Types
    'SamplerConfig',
    'GenerationConfig',
    'ModelConfig',
    'LlmChatMessage',
    'VlmChatMessage',
    'VlmContent',
    'ProfileData',
    'KvCacheSaveInput',
    'KvCacheLoadInput',
    # Errors
    'NexaError',
    'NexaCommonError',
    'NexaUnknownError',
    'NexaInvalidInputError',
    'NexaMemoryAllocationError',
    'NexaFileNotFoundError',
    'NexaNotInitializedError',
    'NexaNotSupportedError',
    'NexaModelLoadError',
    'NexaModelInvalidError',
    'NexaLicenseInvalidError',
    'NexaLicenseExpiredError',
    'NexaLLMError',
    'NexaLLMTokenizationError',
    'NexaLLMTokenizationContextLengthError',
    'NexaLLMGenerationError',
    'NexaLLMGenerationPromptTooLongError',
    'NexaVLMError',
    'NexaVLMImageLoadError',
    'NexaVLMImageFormatError',
    'NexaVLMAudioLoadError',
    'NexaVLMAudioFormatError',
    'NexaVLMGenerationError',
    'NexaEmbeddingError',
    'NexaEmbeddingGenerationError',
    'NexaEmbeddingDimensionError',
    'NexaRerankError',
    'NexaRerankFailedError',
    'NexaRerankInputError',
    'NexaImageGenError',
    'NexaImageGenGenerationError',
    'NexaImageGenPromptError',
    'NexaImageGenDimensionError',
    'NexaASRError',
    'NexaASRTranscriptionError',
    'NexaASRAudioFormatError',
    'NexaASRLanguageError',
    'NexaASRStreamNotStartedError',
    'NexaASRStreamAlreadyActiveError',
    'NexaASRStreamInvalidAudioError',
    'NexaASRStreamBufferFullError',
    'NexaASRStreamCallbackError',
    'NexaTTSError',
    'NexaTTSSynthesisError',
    'NexaTTSVoiceError',
    'NexaTTSAudioFormatError',
    'NexaCVError',
    'NexaCVOCRDetectionError',
    'NexaCVOCRRecognitionError',
    'NexaCVOCRFailedError',
    'NexaDiarizeError',
    'NexaDiarizeAudioLoadError',
    'NexaDiarizeSegmentationError',
    'NexaDiarizeEmbeddingError',
    'NexaDiarizeClusteringError',
    'check_error',
    'ml_get_error_message',
]
