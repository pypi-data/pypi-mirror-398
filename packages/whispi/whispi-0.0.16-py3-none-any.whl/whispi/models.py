from rich import print

WHISPER_MODELS = {
    # Models for faster-whisper: https://huggingface.co/Systran
    # Models for mlx-whisper: https://huggingface.co/mlx-community

    # OpenAI Whisper 原版（多语言通用）
    'large-v3': {
        'faster-whisper': 'large-v3',
        'mlx-whisper': 'mlx-community/whisper-large-v3-mlx'
        },
    'large-v3-turbo': {
        'faster-whisper': 'deepdml/faster-whisper-large-v3-turbo-ct2',
        'mlx-whisper': 'mlx-community/whisper-large-v3-turbo'
        },

    # Belle-whisper 中文优化版 (https://huggingface.co/BELLE-2)
    # 在中文 ASR 基准测试上比原版提升 24-65%
    'belle-large-v3-zh': {
        'faster-whisper': 'XA9/Belle-faster-whisper-large-v3-zh-punct',  # CTranslate2 格式
        'mlx-whisper': None  # 不支持 MLX，自动回退到 large-v3
        },
}


def ensure_model(model: str) -> bool:
    return model in WHISPER_MODELS


def _get_default_model_for_impl(implementation: str) -> str:
    """
    Pick a sensible default model for the requested implementation.
    Falls back to any model that supports the implementation if the
    preferred choice is not available.
    """
    preferred = 'large-v3-turbo'

    if is_model_supported(preferred, implementation):
        return preferred

    for name in WHISPER_MODELS:
        if is_model_supported(name, implementation):
            return name

    raise ValueError(
        f'No model available for implementation "{implementation}".'
        )


def is_model_supported(model: str, implementation: str) -> bool:
    model_info = WHISPER_MODELS.get(model)
    if not model_info:
        return False
    if model_info.get(implementation) is None:
        return False
    return True


def set_supported_model(model: str, implementation: str) -> str:
    if not is_model_supported(model, implementation):
        default_model = _get_default_model_for_impl(implementation)
        print(
            f'[blue1]→ Model "{model}" is not available for this '
            f'implementation → Using default model "{default_model}".'
        )
        return WHISPER_MODELS.get(default_model)[implementation]
    return WHISPER_MODELS.get(model)[implementation]


def set_mlx_model(model: str) -> str:
    """
    Selects a supported mlx-whisper model, falling back to a default one
    if the requested model is unavailable.
    """
    return set_supported_model(model=model, implementation='mlx-whisper')
