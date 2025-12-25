"""
Embedding wrapper for nexaai.
Provides high-level Python API for embedding operations.
"""

import ctypes
import logging
from typing import List, Optional

from .internal.model_loader import ModelLoaderMixin
from .internal.native_plugin import (
    convert_from_mlx_profile_data,
    convert_to_mlx_model_config,
    get_mlx_embedder_class,
    is_native_plugin,
    setup_mlx_imports,
)
from .nexa_sdk._lib import _lib
from .nexa_sdk.embedding import (
    ml_Embedder,
    ml_EmbedderCreateInput,
    ml_EmbedderDimOutput,
    ml_EmbedderEmbedInput,
    ml_EmbedderEmbedOutput,
    ml_EmbeddingConfig,
)
from .nexa_sdk.error import check_error
from .nexa_sdk.types import ModelConfig, ProfileData

logger = logging.getLogger(__name__)


class Embedder(ModelLoaderMixin):
    """Embedding model wrapper."""

    def __init__(
        self,
        model_path: str,
        tokenizer_path: Optional[str] = None,
        model_name: Optional[str] = None,
        config: Optional[ModelConfig] = None,
        plugin_id: Optional[str] = None,
        device_id: Optional[str] = None,
    ):
        """
        Create and initialize an Embedder instance.

        Args:
            model_path: Path to the model file.
            tokenizer_path: Path to the tokenizer file. If None, uses model_path.
            model_name: Name of the model. If None, uses model_path.
            config: Model configuration. If None, uses default config.
            plugin_id: Plugin to use for the model. If None, uses default.
            device_id: Device to use for the model. If None, uses default device.
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
        plugin_id_str = plugin_id if plugin_id else ''
        plugin_id_buf = ctypes.create_string_buffer(plugin_id_str.encode('utf-8'))
        device_id_buf = ctypes.create_string_buffer(device_id.encode('utf-8')) if device_id else None

        model_name_buf = ctypes.create_string_buffer(model_name_bytes)
        model_path_buf = ctypes.create_string_buffer(model_path_bytes)
        tokenizer_path_buf = ctypes.create_string_buffer(tokenizer_path_bytes) if tokenizer_path_bytes else None

        c_input = ml_EmbedderCreateInput(
            model_name=ctypes.cast(model_name_buf, ctypes.c_char_p),
            model_path=ctypes.cast(model_path_buf, ctypes.c_char_p),
            tokenizer_path=ctypes.cast(tokenizer_path_buf, ctypes.c_char_p) if tokenizer_path_buf else None,
            config=c_config,
            plugin_id=ctypes.cast(plugin_id_buf, ctypes.c_char_p) if plugin_id_buf else None,
            device_id=ctypes.cast(device_id_buf, ctypes.c_char_p) if device_id_buf else None,
        )

        self._string_refs = [
            model_name_buf,
            model_path_buf,
            tokenizer_path_buf,
            plugin_id_buf,
            device_id_buf,
        ]

        handle_ptr = ctypes.POINTER(ml_Embedder)()
        error_code = _lib.ml_embedder_create(ctypes.pointer(c_input), ctypes.byref(handle_ptr))
        check_error(error_code)

        if not handle_ptr:
            raise RuntimeError('Failed to create Embedder instance')

        self._handle = handle_ptr
        self._config = config

    def _init_mlx_native(
        self,
        model_path: str,
        tokenizer_path: str,
        model_name: str,
        config: ModelConfig,
        device_id: Optional[str],
    ):
        """
        Initialize Embedder using MLX native Python implementation.

        Args:
            model_path: Path to the model file
            tokenizer_path: Path to the tokenizer file
            model_name: Name of the model
            config: Model configuration
            device_id: Device ID (e.g., 'cpu', 'gpu')
        """
        MLXEmbedder = get_mlx_embedder_class()

        # Convert config to MLX format
        mlx_config = convert_to_mlx_model_config(config)

        # Create MLX Embedder instance
        self._mlx_embedder = MLXEmbedder(
            model_path=model_path,
            tokenizer_path=tokenizer_path,
            device=device_id if device_id else 'cpu',
        )

        if not self._mlx_embedder.load_model(model_path):
            raise RuntimeError(f'Failed to load MLX embedder model from {model_path}')

        self._is_native = True
        self._config = config
        self._handle = None  # No C handle for native implementation

    def __del__(self):
        """Destroy Embedder instance and free associated resources."""
        if hasattr(self, '_is_native') and self._is_native:
            # Native implementation cleanup
            if hasattr(self, '_mlx_embedder') and self._mlx_embedder:
                try:
                    self._mlx_embedder.destroy()
                except Exception as e:
                    logger.warning(f'Error during MLX native Embedder cleanup: {e}')
                self._mlx_embedder = None
        elif hasattr(self, '_handle') and self._handle:
            # C interface cleanup
            try:
                _lib.ml_embedder_destroy(self._handle)
            except Exception as e:
                logger.warning(f'Error during Embedder cleanup: {e}')
            self._handle = None

    @classmethod
    def _get_model_type(cls) -> str:
        return 'embedder'

    @classmethod
    def _extract_model_params_from_manifest(
        cls,
        manifest,
        model_path: str,
        repo_id: str,
        store,
        **kwargs,
    ) -> dict:
        """Extract Embedder-specific parameters from manifest."""
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
    def _create_instance(cls, **params) -> 'Embedder':
        """Create Embedder instance with given parameters."""
        return cls(**params)

    def embed(
        self,
        texts: Optional[List[str]] = None,
        input_ids: Optional[List[List[int]]] = None,
        image_paths: Optional[List[str]] = None,
        task_type: Optional[str] = None,
        batch_size: int = 32,
        normalize: bool = False,
        normalize_method: Optional[str] = None,
    ) -> 'EmbedResult':
        """
        Generate embeddings for texts, tokens, or images.

        Args:
            texts: List of text strings to embed.
            input_ids: List of token ID sequences (alternative to texts).
            image_paths: List of image file paths to embed.
            task_type: Task type for embedding (e.g., "classification", "retrieval").
            batch_size: Batch size for processing.
            normalize: Whether to normalize embeddings.
            normalize_method: Normalization method (e.g., "l2").

        Returns:
            EmbedResult containing embeddings and metadata.

        Raises:
            NexaError: If embedding generation fails.
        """
        if self._is_native:
            return self._mlx_embed(texts, input_ids, image_paths, task_type, batch_size, normalize, normalize_method)

        if texts and input_ids:
            raise ValueError('Cannot provide both texts and input_ids')
        if not texts and not input_ids and not image_paths:
            raise ValueError('Must provide texts, input_ids, or image_paths')

        embedding_config = ml_EmbeddingConfig(
            batch_size=ctypes.c_int32(batch_size),
            normalize=ctypes.c_bool(normalize),
            normalize_method=normalize_method.encode('utf-8') if normalize_method else None,
        )

        texts_ptr = None
        text_count = 0
        if texts:
            text_count = len(texts)
            text_array = (ctypes.c_char_p * text_count)()
            text_bufs = []
            for i, text in enumerate(texts):
                text_bytes = text.encode('utf-8')
                text_buf = ctypes.create_string_buffer(text_bytes)
                text_bufs.append(text_buf)
                text_array[i] = ctypes.cast(text_buf, ctypes.c_char_p)
            texts_ptr = ctypes.cast(text_array, ctypes.POINTER(ctypes.c_char_p))
            self._text_bufs = text_bufs

        input_ids_2d = None
        input_ids_row_lengths = None
        input_ids_row_count = 0
        if input_ids:
            input_ids_row_count = len(input_ids)
            row_lengths = [len(row) for row in input_ids]
            max_length = max(row_lengths) if row_lengths else 0

            input_ids_array = (ctypes.POINTER(ctypes.c_int32) * input_ids_row_count)()
            row_lengths_array = (ctypes.c_int32 * input_ids_row_count)()

            for i, row in enumerate(input_ids):
                row_array = (ctypes.c_int32 * len(row))(*row)
                input_ids_array[i] = ctypes.cast(row_array, ctypes.POINTER(ctypes.c_int32))
                row_lengths_array[i] = ctypes.c_int32(len(row))

            input_ids_2d = ctypes.cast(input_ids_array, ctypes.POINTER(ctypes.POINTER(ctypes.c_int32)))
            input_ids_row_lengths = ctypes.cast(row_lengths_array, ctypes.POINTER(ctypes.c_int32))

        image_paths_ptr = None
        image_count = 0
        if image_paths:
            image_count = len(image_paths)
            image_array = (ctypes.c_char_p * image_count)()
            image_bufs = []
            for i, path in enumerate(image_paths):
                path_bytes = path.encode('utf-8')
                path_buf = ctypes.create_string_buffer(path_bytes)
                image_bufs.append(path_buf)
                image_array[i] = ctypes.cast(path_buf, ctypes.c_char_p)
            image_paths_ptr = ctypes.cast(image_array, ctypes.POINTER(ctypes.c_char_p))
            self._image_bufs = image_bufs

        task_type_bytes = task_type.encode('utf-8') if task_type else None
        task_type_buf = ctypes.create_string_buffer(task_type_bytes) if task_type_bytes else None

        c_input = ml_EmbedderEmbedInput(
            texts=texts_ptr,
            text_count=ctypes.c_int32(text_count),
            config=ctypes.pointer(embedding_config),
            input_ids_2d=input_ids_2d,
            input_ids_row_lengths=input_ids_row_lengths,
            input_ids_row_count=ctypes.c_int32(input_ids_row_count),
            task_type=ctypes.cast(task_type_buf, ctypes.c_char_p) if task_type_buf else None,
            image_paths=image_paths_ptr,
            image_count=ctypes.c_int32(image_count),
        )

        c_output = ml_EmbedderEmbedOutput()
        error_code = _lib.ml_embedder_embed(self._handle, ctypes.pointer(c_input), ctypes.pointer(c_output))
        check_error(error_code)

        return self._extract_result(c_output)

    def _mlx_embed(
        self,
        texts: Optional[List[str]] = None,
        input_ids: Optional[List[List[int]]] = None,
        image_paths: Optional[List[str]] = None,
        task_type: Optional[str] = None,
        batch_size: int = 32,
        normalize: bool = False,
        normalize_method: Optional[str] = None,
    ) -> 'EmbedResult':
        """Generate embeddings using MLX native implementation."""
        import ml

        # Create embedding config
        embedding_config = ml.EmbeddingConfig(
            batch_size=batch_size,
            normalize=normalize,
            normalize_method=normalize_method or 'l2',
        )

        # Call MLX embed method
        embeddings = self._mlx_embedder.embed(
            texts=texts if texts else [],
            config=embedding_config,
        )

        # Extract profiling data if available
        profiling_data = None
        if hasattr(self._mlx_embedder, 'get_profiling_data'):
            profiling_data = self._mlx_embedder.get_profiling_data()

        profile_data = convert_from_mlx_profile_data(profiling_data) if profiling_data else ProfileData()

        return EmbedResult(embeddings=embeddings, profile_data=profile_data)

    def _extract_result(self, c_output: ml_EmbedderEmbedOutput) -> 'EmbedResult':
        """Extract EmbedResult from C output structure."""
        embeddings = []
        if c_output.embeddings and c_output.embedding_count > 0:
            dim = self.embedding_dim()
            count = c_output.embedding_count
            for i in range(count):
                start_idx = i * dim
                end_idx = start_idx + dim
                embedding = [c_output.embeddings[j] for j in range(start_idx, end_idx)]
                embeddings.append(embedding)

        profile_data = ProfileData.from_c_struct(c_output.profile_data)
        return EmbedResult(
            embeddings=embeddings,
            profile_data=profile_data,
        )

    def embedding_dim(self) -> int:
        """
        Get embedding dimension.

        Returns:
            Embedding dimension.

        Raises:
            NexaError: If query fails.
        """
        if self._is_native:
            return self._mlx_embedder.embedding_dim()

        c_output = ml_EmbedderDimOutput()
        error_code = _lib.ml_embedder_embedding_dim(self._handle, ctypes.pointer(c_output))
        check_error(error_code)
        return c_output.dimension


class EmbedResult:
    """Result of embedding generation."""

    def __init__(
        self,
        embeddings: List[List[float]],
        profile_data: ProfileData,
    ):
        self.embeddings = embeddings
        self.profile_data = profile_data

    def __repr__(self) -> str:
        return (
            f'EmbedResult(embeddings={len(self.embeddings)}, dim={len(self.embeddings[0]) if self.embeddings else 0})'
        )
