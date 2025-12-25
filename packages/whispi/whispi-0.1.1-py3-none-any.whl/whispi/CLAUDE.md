[根目录](../CLAUDE.md) > **whispi**

# whispi（核心包）

> 包含所有转录、说话人分离和导出逻辑的 Python 包。

## 模块职责

这是包含所有核心功能的主 Python 包：

| 文件 | 行数 | 用途 |
|------|------|------|
| `cli.py` | 256 | Typer CLI 入口，包含 `run`、`list` 命令 |
| `transcription.py` | 799 | 核心 `TranscriptionHandler` 类，包含所有转录逻辑 |
| `models.py` | 76 | Whisper 模型注册表，映射名称到实现 |
| `output_utils.py` | 352 | `OutputWriter` 多格式导出（JSON、TXT、SRT、WEBVTT） |
| `little_helper.py` | 466 | 设备检测、文件格式转换、进度辅助 |
| `diarize_utils.py` | 213 | 通过 pyannote.audio 进行说话人分离 |

## 入口点

### CLI 入口 (`cli.py:250-255`)
```python
def run():
    cli_app()

if __name__ == "__main__":
    run()
```

在 `pyproject.toml` 中注册：
```toml
[project.scripts]
whispi = "whispi.cli:run"
```

## 核心类：TranscriptionHandler

位置：`transcription.py:24-799`

### 初始化参数
```python
TranscriptionHandler(
    base_dir='./transcriptions',  # 输出目录
    model='large-v3-turbo',       # Whisper 模型
    device='cpu',                 # cpu, cuda:0, mlx
    file_language=None,           # None 时自动检测
    annotate=False,               # 说话人分离
    num_speakers=None,            # 说话人数量提示
    hf_token=None,                # HuggingFace token
    subtitle=False,               # 生成字幕
    verbose=False,                # 打印进度
    export_formats='all',         # 输出格式
)
```

### 关键方法

| 方法 | 用途 |
|------|------|
| `process_files()` | 批量文件处理的主入口 |
| `transcribe_with_mlx_whisper()` | MLX Whisper（Apple Silicon） |
| `transcribe_with_faster_whisper()` | Faster-whisper（CPU/GPU，支持说话人标注和字幕） |
| `detect_language()` | 通过 faster-whisper 检测语言 |
| `adjust_word_chunk_length()` | 转换 segments 为 chunks 格式（pass-through） |
| `to_transcription_dict()` | 转换为标准转录字典格式 |
| `to_whisperx()` | 标准化为 whisperX 格式 |
| `to_mlx_chunks()` | 转换 MLX 结果为块格式 |
| `create_text_with_speakers()` | 创建带说话人标注的文本 |
| `_faster_whisper_to_whisperx()` | 将 faster-whisper 结果转换为 whisperX 格式 |

### 转录实现选择逻辑 (`transcription.py:751-772`)

```python
if self.device == 'mlx':
    # Apple Silicon：使用 mlx-whisper
    self.model = models.set_supported_model(
        self.model_provided,
        implementation='mlx-whisper'
    )
    result_data = self.transcribe_with_mlx_whisper(filepath)

elif self.device in ['cpu', 'cuda:0']:
    # CPU/CUDA：统一使用 faster-whisper
    self.model = models.set_supported_model(
        self.model_provided,
        implementation='faster-whisper'
    )
    result_data = self.transcribe_with_faster_whisper(filepath)
```

## 模型注册表

位置：`models.py:3-23`

```python
WHISPER_MODELS = {
    # OpenAI Whisper 原版（多语言通用）
    'large-v3': {
        'faster-whisper': 'large-v3',
        'mlx-whisper': 'mlx-community/whisper-large-v3-mlx'
    },
    'large-v3-turbo': {
        'faster-whisper': 'deepdml/faster-whisper-large-v3-turbo-ct2',
        'mlx-whisper': 'mlx-community/whisper-large-v3-turbo'
    },
    # Belle-whisper 中文优化版 (性能提升 24-65%)
    'belle-large-v3-zh': {
        'faster-whisper': 'XA9/Belle-faster-whisper-large-v3-zh-punct',
        'mlx-whisper': None  # 不支持 MLX，自动回退到 large-v3
    },
}
```

### 模型选择函数 (`models.py:59-67`)
```python
def set_supported_model(model: str, implementation: str) -> str:
    """
    返回实现特定的模型标识符。
    如果请求的模型不支持，则自动回退到默认模型（large-v3-turbo）。
    """
```

## 设备检测

位置：`little_helper.py:33-74`

```python
class DeviceChoice(str, Enum):
    AUTO = "auto"
    CPU = "cpu"
    GPU = "gpu"
    MLX = "mlx"

def get_device(device: DeviceChoice = DeviceChoice.AUTO) -> str:
    """
    AUTO：CUDA > MLX > CPU
    返回：'cuda:0'、'mlx' 或 'cpu'
    """
```

### 设备优先级
1. CUDA (NVIDIA GPU)
2. MLX (Apple Silicon M1-M5)
3. CPU（通用回退）

## 输出格式

位置：`output_utils.py:17-73`

### 导出格式枚举
```python
class ExportFormats(str, Enum):
    ALL = "all"
    JSON = "json"
    TXT = "txt"
    WEBVTT = "webvtt"
    SRT = "srt"

class TxtFormat(str, Enum):
    PLAIN = "plain"           # 纯文本
    TIMESTAMPED = "timestamped"  # 带时间戳的文本
```

### OutputWriter 类 (`output_utils.py:66-311`)

| 方法 | 用途 |
|------|------|
| `save_json()` | 保存 JSON 格式 |
| `save_txt()` | 保存 TXT 格式（支持 plain 和 timestamped） |
| `save_txt_with_speaker_annotation()` | 保存带说话人标注的 TXT |
| `save_subtitles()` | 保存 SRT 或 WEBVTT 字幕 |
| `save_results()` | 主入口，根据 export_formats 保存所有格式 |

### 格式验证 (`output_utils.py:25-63`)

```python
def determine_export_formats(
    export_format: ExportFormats,
    annotate: bool,
    subtitle: bool
) -> List[str]:
    """
    验证导出格式与功能开关的兼容性：
    - SRT/WEBVTT 需要 subtitle=True
    """
```

## 文件处理流程

### 1. 输入处理 (`little_helper.py:128-274`)

`FilePathProcessor` 类支持三种输入类型：
- 单个文件：验证文件格式后添加
- 文件夹：递归搜索所有支持的格式
- `.list` 文件：每行一个路径（文件、文件夹、URL 混合）

```python
def get_filepaths(self, filepath: str):
    # 支持 .list、单文件、文件夹
    # 自动规范化文件名（移除特殊字符）
    # 自动过滤已转换的文件
```

### 2. 格式转换 (`little_helper.py:320-409`)

```python
def check_file_format(filepath: Path) -> tuple[Path, np.ndarray]:
    """
    检查并转换音频文件为 16kHz 单声道 WAV。
    要求：codec='pcm_s16le', sample_rate=16000, channels=1
    原始输入文件始终保留。
    返回：(文件路径, 音频数组)
    """
```

### 3. 语言检测 (`transcription.py:656-696`)

```python
def detect_language(self, filepath, audio_array) -> str:
    """
    使用 faster-whisper 的 WhisperModel 检测音频语言。
    返回 ISO 639-1 语言代码（如 'zh', 'en'）。
    """
```

### 4. 转录实现

#### MLX 实现 (`transcription.py:361-464`)
- 使用 `mlx_whisper.transcribe()`
- 不支持 `word_timestamps` 参数（某些版本）
- 说话人标注通过 `diarize_utils.diarize()` 实现

#### Faster-Whisper 实现 (`transcription.py:466-620`)
- 使用 `BatchedInferencePipeline` 和 `WhisperModel`
- 始终启用 `word_timestamps=True`（支持说话人标注和字幕）
- 说话人标注通过 `diarize_utils.diarize()` 实现

### 5. 说话人分离 (`diarize_utils.py:185-212`)

```python
def diarize(outputs, **kwargs):
    """
    使用 pyannote.audio 的 Pipeline.from_pretrained()
    模型：pyannote/speaker-diarization-community-1
    设备自动检测：CUDA > CPU
    返回：带说话人标签的词级片段
    """
```

### 6. 输出保存 (`output_utils.py:250-340`)

```python
def save_results(self, result: dict, export_formats: List[str]) -> List[Path]:
    """
    根据 export_formats 列表保存所有输出文件。
    返回已写入文件的路径列表。
    """
```

## 相关文件清单

| 路径 | 用途 |
|------|------|
| `cli.py` | Typer CLI 入口 |
| `transcription.py` | 核心转录处理类 |
| `models.py` | Whisper 模型注册表 |
| `output_utils.py` | 多格式导出工具 |
| `little_helper.py` | 设备检测、文件处理、进度显示 |
| `diarize_utils.py` | pyannote.audio 说话人分离 |
| `__init__.py` | 包初始化（空文件） |

## 关键常量和配置

| 配置 | 值/位置 |
|------|---------|
| 支持的音频格式 | `.mp3`, `.wav`, `.m4a`, `.aac`, `.flac`, `.ogg`, `.mkv`, `.mov`, `.mp4`, `.avi`, `.mpeg`, `.vob` |
| 目标音频格式 | 16kHz 单声道 WAV (pcm_s16le) |
| 日志目录 | `./logs/` |
| 默认输出目录 | `./transcriptions/` |
| 默认模型 | `large-v3-turbo` |
| 批处理大小 | `batch_size=16` (faster-whisper) |

## 常见问题 (FAQ)

### Q: 为什么 Belle-whisper 模型不支持 MLX？
A: Belle-whisper 模型只有 CTranslate2 格式，没有 MLX 兼容版本。在 MLX 设备上会自动回退到 `large-v3`。

### Q: 说话人标注支持哪些语言？
A: pyannote.audio 模型本身是语言无关的，但转录需要支持词级时间戳的语言。默认支持：`en, fr, de, es, it, ja, zh, nl, uk, pt`。

## 变更记录

| 日期 | 变更 |
|------|------|
| 2025-12-22 | 更新代码扫描结果，修正行数统计（cli.py: 256, transcription.py: 799, models.py: 76, output_utils.py: 437, little_helper.py: 466, diarize_utils.py: 213） |
| 2025-12-22 | 移除 whisperX 依赖，统一使用 faster-whisper + pyannote.audio 架构，代码减少约 650 行（transcription.py: 1297→798, models.py: 202→75），支持所有 3 个模型（包括 large-v3-turbo） |
| 2025-12-22 | 移除 MPS 设备支持和 insanely-fast-whisper 实现，简化为 MLX (Apple Silicon) + faster-whisper (CUDA/CPU) 架构 |
| 2025-12-22 | 移除翻译为英文功能 |
| 2025-12-22 | 移除 post_correction 和 output_templates 模块，不再输出 HTML 格式 |
| 2025-12-22 | 移除 Gradio Web 应用功能（app.py、app_helpers.py） |
| 2025-12-22 | 移除 URL/YouTube 下载功能（download_utils.py） |
| 2025-12-22 | 生成初始模块 CLAUDE.md |
