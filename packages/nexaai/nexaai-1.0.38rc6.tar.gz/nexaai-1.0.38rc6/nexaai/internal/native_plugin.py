import os
import sys
from pathlib import Path
from typing import Optional

# Plugin IDs that support native Python calls
_NATIVE_PLUGIN_IDS = {'metal', 'mlx'}


def is_native_plugin(plugin_id: Optional[str]) -> bool:
    if not plugin_id:
        return False
    return plugin_id.lower() in _NATIVE_PLUGIN_IDS


def find_mlx_py_lib() -> Optional[Path]:
    import logging

    logger = logging.getLogger(__name__)

    lib_paths = [
        Path(__file__).parent.parent / 'nexa_sdk' / 'lib' / 'metal' / 'py-lib',
        Path(os.getenv('NEXA_PLUGIN_PATH', Path(__file__).parent / 'lib')) / 'metal' / 'py-lib',
    ]

    logger.debug('Searching for py-lib in: ')
    for lib_path in lib_paths:
        logger.debug(f' - {lib_path}')
        if lib_path.exists() and lib_path.is_dir():
            logger.debug(f' - found py-lib at: {lib_path}')
            return lib_path
    return None


def setup_mlx_imports() -> bool:
    import logging

    logger = logging.getLogger(__name__)

    mlx_path = find_mlx_py_lib()
    if not mlx_path or not mlx_path.exists():
        logger.debug(f'MLX py-lib not found at {mlx_path}')
        return False

    mlx_path_str = str(mlx_path)
    logger.debug(f'Found MLX py-lib at: {mlx_path_str}')

    if mlx_path_str not in sys.path:
        sys.path.insert(0, mlx_path_str)
        logger.debug(f'Added {mlx_path_str} to sys.path')

    try:
        import ml  # noqa: F401

        return True
    except ImportError as e:
        logger.debug(f'Failed to import MLX modules: {e}')
        if mlx_path_str in sys.path:
            sys.path.remove(mlx_path_str)
        return False


def get_mlx_llm_class():
    from llm.interface import LLM

    return LLM


def get_mlx_vlm_class():
    from vlm.interface import VLM

    return VLM


def get_mlx_embedder_class():
    from embedding.interface import Embedder

    return Embedder


def get_mlx_asr_class():
    from asr.interface import MlxAsr

    return MlxAsr


def get_mlx_cv_class():
    from cv.interface import CVModel

    return CVModel


def get_mlx_tts_class():
    from tts.interface import MlxTts

    return MlxTts


def get_mlx_reranker_class():
    from rerank.interface import Reranker

    return Reranker


def get_mlx_imagegen_class():
    from image_gen.interface import ImageGen

    return ImageGen


def convert_to_mlx_model_config(config):
    import ml

    return ml.ModelConfig(
        n_ctx=config.n_ctx,
        n_threads=config.n_threads,
        n_threads_batch=config.n_threads_batch,
        n_batch=config.n_batch,
        n_ubatch=config.n_ubatch,
        n_seq_max=config.n_seq_max,
        chat_template_path=config.chat_template_path,
        chat_template_content=config.chat_template_content,
    )


def convert_to_mlx_generation_config(config):
    import ml

    sampler_config = None
    if config.sampler_config:
        sampler_config = ml.SamplerConfig(
            temperature=config.sampler_config.temperature,
            top_p=config.sampler_config.top_p,
            top_k=config.sampler_config.top_k,
            min_p=config.sampler_config.min_p,
            repetition_penalty=config.sampler_config.repetition_penalty,
            presence_penalty=config.sampler_config.presence_penalty,
            frequency_penalty=config.sampler_config.frequency_penalty,
            seed=config.sampler_config.seed,
            grammar_path=config.sampler_config.grammar_path,
            grammar_string=config.sampler_config.grammar_string,
        )

    image_paths = None
    if config.image_paths:
        image_paths = tuple(config.image_paths)

    audio_paths = None
    if config.audio_paths:
        audio_paths = tuple(config.audio_paths)

    return ml.GenerationConfig(
        max_tokens=config.max_tokens,
        stop=tuple(config.stop) if config.stop else tuple(),
        n_past=config.n_past,
        sampler_config=sampler_config,
        image_paths=image_paths,
        audio_paths=audio_paths,
    )


def convert_to_mlx_chat_message(message):
    import ml

    return ml.ChatMessage(
        role=message.role,
        content=message.content,
    )


def convert_to_mlx_asr_config(
    timestamps: Optional[str] = None,
    beam_size: int = 5,
    stream: bool = False,
):
    import ml

    return ml.ASRConfig(
        timestamps=timestamps or 'none',
        beam_size=beam_size,
        stream=stream,
    )


def convert_from_mlx_profile_data(profiling_data):
    from ..nexa_sdk.types import ProfileData

    return ProfileData(
        ttft=profiling_data.ttft if hasattr(profiling_data, 'ttft') else 0,
        prompt_time=profiling_data.prompt_time if hasattr(profiling_data, 'prompt_time') else 0,
        decode_time=profiling_data.decode_time if hasattr(profiling_data, 'decode_time') else 0,
        prompt_tokens=profiling_data.prompt_tokens if hasattr(profiling_data, 'prompt_tokens') else 0,
        generated_tokens=profiling_data.generated_tokens if hasattr(profiling_data, 'generated_tokens') else 0,
        audio_duration=profiling_data.audio_duration if hasattr(profiling_data, 'audio_duration') else 0,
        prefill_speed=profiling_data.prefill_speed if hasattr(profiling_data, 'prefill_speed') else 0.0,
        decoding_speed=profiling_data.decoding_speed if hasattr(profiling_data, 'decoding_speed') else 0.0,
        real_time_factor=profiling_data.real_time_factor if hasattr(profiling_data, 'real_time_factor') else 0.0,
        stop_reason=profiling_data.stop_reason if hasattr(profiling_data, 'stop_reason') else None,
    )
