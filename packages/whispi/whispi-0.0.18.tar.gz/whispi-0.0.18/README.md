# whispi

*使用 OpenAI [Whisper](https://github.com/openai/whisper) 快速转录、标注和生成音视频字幕！*

`whispi` 整合了 [faster-whisper](https://github.com/SYSTRAN/faster-whisper) 和 [mlx-whisper](https://github.com/ml-explore/mlx)，为 Windows、Linux 和 Mac 平台提供易用的批量文件处理方案。同时集成 [pyannote.audio](https://github.com/pyannote/pyannote-audio) 实现词级别的说话人标注。

---

## 快速开始

最快 30 秒上手 whispi：

```bash
# 1. 安装 whispi
pip install whispi

# 2. 转录单个音视频文件（自动选择最优设备和模型）
whispi run -f your_audio.mp3

# 3. 查看转录结果
cat transcriptions/your_audio.json
```

**就这么简单！** whispi 会自动：
- 检测你的硬件（CUDA GPU / Apple Silicon / CPU）
- 选择最快的 Whisper 实现
- 使用默认模型 `large-v3-turbo` 进行转录
- 输出 JSON 和 TXT 格式的转录结果

**需要更多功能？** 继续阅读下面的[使用场景](#常见使用场景)。

---

## 目录

- [核心特性](#核心特性)
- [系统要求](#系统要求)
- [安装指南](#安装指南)
- [常见使用场景](#常见使用场景)
- [CLI 参数速查](#cli-参数速查)
- [技术说明（高级）](#技术说明高级)
- [批量处理](#批量处理)
- [引用](#引用)

---

## 核心特性

### 🚀 智能设备选择
whispi 自动检测硬件并选择最快的 Whisper 实现：
- **NVIDIA GPU (CUDA)**：使用 `faster-whisper`
- **Apple Silicon (M1-M5)**：使用 `mlx-whisper`
- **CPU**：使用 `faster-whisper`

### 🎯 精选模型策略
保留 3 个经过优化的模型，覆盖多语言和中文场景：

| 模型 | 特点 | 适用场景 | 中文性能提升 |
|------|------|---------|------------|
| `large-v3-turbo` | 速度快，精度高（默认） | 多语言通用 | - |
| `large-v3` | 最高精度 | 需要极致准确度 | - |
| `belle-large-v3-zh` | 中文最高精度 | 中文极致准确度 | +24-65% |

### ⚡ 统一架构
whispi 采用简洁的统一实现架构：
- **CPU/CUDA 设备**：统一使用 `faster-whisper`（支持所有模型和功能）
- **MLX 设备**：使用 `mlx-whisper`（Apple Silicon 优化）
- **说话人标注**：通过 `pyannote.audio` 实现（设备无关）

### ✨ 其他特性
- **词级别标注**：集成 pyannote.audio 实现精确的说话人分离和标注
- **自定义字幕**：可指定每个字幕块的词数，生成 `.srt` 和 `.webvtt` 文件
- **批量处理**：支持单个文件、文件夹或 `.list` 文件批量处理
- **多种导出格式**：`.json`、`.txt`、`.srt`、`.webvtt`
- **带时间戳的文本**：支持导出带时间戳的 TXT 格式

---

## 系统要求

- **FFmpeg**：音视频格式转换必需
- **Python**：3.10 - 3.13
- **GPU 加速**（可选）：
  - NVIDIA GPU（需要 CUDA + cuBLAS + cuDNN）
  - Apple Silicon（Mac M1-M5）
- **说话人标注**：需要 [HuggingFace 访问令牌](https://huggingface.co/docs/hub/security-tokens)

---

## 安装指南

### 第一步：安装 FFmpeg

<details>
<summary><b>macOS</b></summary>

```bash
brew install ffmpeg
```
</details>

<details>
<summary><b>Linux</b></summary>

```bash
sudo apt-get update
sudo apt-get install ffmpeg
```
</details>

<details>
<summary><b>Windows</b></summary>

```bash
winget install Gyan.FFmpeg
```
</details>

更多信息请访问 [FFmpeg 官网](https://ffmpeg.org/download.html)。

### 第二步：安装 whispi

**用户安装（推荐）**

```bash
# 基础安装
pip install whispi

# Apple Silicon 用户需要安装 MLX 扩展
pip install "whispi[mlx]"
```

<details>
<summary><b>开发者安装（从源码）</b></summary>

本项目使用 [uv](https://github.com/astral-sh/uv) 进行包管理。

```bash
# 1. 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 克隆仓库
git clone https://github.com/tsmdt/whispi.git
cd whispi

# 3. 同步依赖
uv sync              # 基础依赖
uv sync --extra mlx  # 或安装 MLX 扩展（Apple Silicon）

# 4. 运行
uv run whispi run -f audio.mp3
```
</details>

### 第三步：配置 HuggingFace 认证（可选）

如果需要使用**说话人标注功能**，需要配置 HuggingFace 访问令牌：

```bash
# 安装 HuggingFace CLI（如果尚未安装）
pip install huggingface-hub

# 一次性登录（token 会被保存）
hf auth login

# 之后可直接使用标注功能，无需传递 --hf_token 参数
whispi run -f audio.mp3 --annotate
```

**重要提示**：
1. 获取 [HuggingFace 访问令牌](https://huggingface.co/docs/hub/security-tokens)
2. 同意 [pyannote 模型条款](https://huggingface.co/pyannote/speaker-diarization-community-1#requirements)

**或者**，你也可以通过以下方式传递 token：
- 使用 `--hf_token` 参数：`whispi run -f audio.mp3 --annotate --hf_token YOUR_TOKEN`
- 设置环境变量：`export HF_TOKEN=YOUR_TOKEN`

---

## 常见使用场景

### 场景 1：基础转录（纯文本）

**用途**：将音视频转录为纯文本，不需要时间戳或字幕

```bash
whispi run -f audio.mp3
```

**使用的实现和模型**：
- CPU/CUDA：`faster-whisper` + `large-v3-turbo`
- Apple Silicon：`mlx-whisper` + `large-v3-turbo`

**输出格式**：`audio.json` + `audio.txt`

---

### 场景 2：中文音频转录

**用途**：使用中文优化模型提升中文转录质量（性能提升 24-65%）

```bash
# 使用 Belle-whisper 中文优化模型
whispi run -f audio.mp3 -m belle-large-v3-zh
```

**使用的实现和模型**：
- CPU/CUDA：`faster-whisper` + `belle-large-v3-zh`
- Apple Silicon：自动回退到 `mlx-whisper` + `large-v3`（Belle 模型不支持 MLX）

> ⚠️ **注意**：Belle-whisper 模型不支持 MLX 设备，在 Apple Silicon 上会自动回退到原版 Whisper

**输出格式**：`audio.json` + `audio.txt`

---

### 场景 3：生成字幕文件

**用途**：生成带时间戳的字幕文件（`.srt` 或 `.webvtt`）

```bash
# 生成 SRT 字幕
whispi run -f video.mp4 --subtitle --export srt

# 同时导出 SRT 和 WEBVTT 格式
whispi run -f video.mp4 --subtitle --export all
```

**使用的实现和模型**：
- CPU/CUDA：`faster-whisper` + `large-v3-turbo`
- Apple Silicon：`mlx-whisper` + `large-v3-turbo`

**输出格式**：`video.json` + `video.txt` + `video.srt` + `video.webvtt`

> 📘 **重要**：`--subtitle` 是功能开关（启用字幕功能），`--export` 是格式选择器（选择导出格式）。要导出字幕文件，必须先启用 `--subtitle`。详见[参数说明](#subtitle-与-export-的区别)。

---

### 场景 4：说话人标注

**用途**：识别和标注不同说话人，输出词级别的说话人信息

```bash
# 自动检测说话人数量（需先运行 hf auth login 认证）
whispi run -f meeting.mp3 --annotate

# 指定说话人数量（2人对话）
whispi run -f interview.mp3 --annotate --num_speakers 2

# 同时生成标注和所有支持的导出格式
whispi run -f meeting.mp3 --annotate --export all

# 或者使用 --hf_token 参数直接传递 token
whispi run -f meeting.mp3 --annotate --hf_token your_hf_token_here
```

**使用的实现和模型**：
- CPU/CUDA：`faster-whisper` + `large-v3-turbo` + `pyannote.audio`
- Apple Silicon：`mlx-whisper` + `large-v3-turbo` + `pyannote.audio`

**输出格式**：`meeting.json`（含说话人标注）+ `meeting_zh_annotated.txt`（含说话人标注）

**前置要求**：
1. 获取 [HuggingFace 访问令牌](https://huggingface.co/docs/hub/security-tokens)
2. 同意 [pyannote 模型条款](https://huggingface.co/pyannote/speaker-diarization-community-1#requirements)

> 💡 **提示**：使用 `hf auth login` 登录后，可以省略 `--hf_token` 参数

---

### 场景 5：批量处理多个文件

**用途**：一次性处理多个音视频文件

```bash
# 处理整个文件夹
whispi run -f ./audio_folder/

# 使用 .list 文件批量处理（支持混合文件、文件夹）
whispi run -f my_files.list

# 使用配置文件批量处理
whispi run --config batch_config.json
```

**`.list` 文件示例**：
```text
video_01.mp4
video_02.mp4
./my_files/
```

**配置文件示例**：
```json
{
    "files": "./files/my_files.list",
    "output_dir": "./transcriptions",
    "device": "auto",
    "model": "large-v3-turbo",
    "lang": null,
    "annotate": false,
    "num_speakers": null,
    "hf_token": "your_hf_token_here",
    "subtitle": false,
    "export": "all",
    "verbose": false
}
```

---

### 场景 6：手动指定设备

**用途**：在多 GPU 环境或特定场景下手动指定计算设备

```bash
# 强制使用 CPU
whispi run -f audio.mp3 --device cpu

# 强制使用 NVIDIA GPU
whispi run -f audio.mp3 --device gpu

# 强制使用 Apple Silicon MLX
whispi run -f audio.mp3 --device mlx
```

> 💡 **提示**：大多数情况下使用默认的 `--device=auto` 即可，whispi 会自动选择最优设备

---

## CLI 参数速查

### 常用参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--files` | `-f` | 文件、文件夹或 .list 文件路径 | - |
| `--model` | `-m` | Whisper 模型（运行 `whispi list` 查看） | `large-v3-turbo` |
| `--lang` | `-l` | 文件语言（如 "en", "zh"，默认自动检测） | `null` |
| `--device` | `-d` | 计算设备（auto/cpu/gpu/mlx） | `auto` |
| `--subtitle` | `-s` | 启用字幕生成 | `False` |
| `--annotate` | `-a` | 启用说话人标注 | `False` |
| `--export` | `-e` | 导出格式（all/json/txt/srt/webvtt） | `all` |

### 完整参数列表

<details>
<summary><b>点击展开所有参数</b></summary>

```text
whispi run [OPTIONS]

选项：
  --files            -f         TEXT                要处理的文件、文件夹或 .list 文件路径
  --output_dir       -o         DIRECTORY           转录结果保存目录 [默认: transcriptions]
  --device           -d         [auto|cpu|gpu|mlx]  CPU、GPU (NVIDIA) 或 MLX (Mac M1-M5) [默认: auto]
  --model            -m         TEXT                使用的 Whisper 模型 [默认: large-v3-turbo]
  --lang             -l         TEXT                文件语言（如 "en", "de"，默认自动检测）
  --annotate         -a                             启用说话人标注 [默认: False]
  --num_speakers     -num       INTEGER             标注的说话人数量（默认：自动检测）
  --hf_token         -hf        TEXT                说话人标注所需的 HuggingFace 访问令牌
  --subtitle         -s                             创建字幕（保存 .srt 和 .webvtt）[默认: False]
  --export           -e         [all|json|txt|webvtt|srt]  选择导出格式 [默认: all]
  --verbose          -v                             转录时打印文本块 [默认: False]
  --config                      PATH                配置文件路径
  --help                                            显示帮助信息并退出
```
</details>

### `--subtitle` 与 `--export` 的区别

这两个参数有不同的作用，需要配合使用：

| 参数 | 类型 | 作用 |
|------|------|------|
| `--subtitle` / `-s` | 布尔标志 | **功能开关**：启用字幕生成功能 |
| `--export` / `-e` | 枚举值 | **格式选择器**：决定导出哪些文件格式 |

**重要规则**：
- ✅ 要导出字幕文件（`.srt` 或 `.webvtt`），必须先用 `--subtitle` 启用字幕功能
- ❌ 如果只设置 `--export=srt` 而不设置 `--subtitle`，程序会报错退出

**`--export=all` 的行为**：
- 总是导出：`json` + `txt`
- 如果 `--annotate`：额外导出 `txt_annotated`（带说话人标注的文本）
- 如果 `--subtitle`：额外导出 `srt` + `webvtt`（字幕文件）

**示例**：

```bash
# ✅ 正确：生成字幕并导出 SRT 格式
whispi run -f audio.mp3 --subtitle --export srt

# ✅ 正确：生成字幕并导出所有格式（包括 srt + webvtt）
whispi run -f audio.mp3 --subtitle --export all

# ✅ 正确：只导出基础格式（json + txt），不生成字幕
whispi run -f audio.mp3 --export txt

# ❌ 错误：没有启用 subtitle 却想导出 SRT
whispi run -f audio.mp3 --export srt  # 报错："SRT export format requires subtitle option to be True."
```

### 查看可用模型

```bash
whispi list
```

这将显示当前设备支持的所有 Whisper 模型。

---

## 技术说明（高级）

本部分面向需要深入了解 whispi 工作原理的开发者和高级用户。

### 设备自动选择逻辑

使用 `--device=auto`（默认）时，whispi 按以下优先级自动选择计算设备：

```
CUDA (NVIDIA GPU) > MLX (Apple Silicon) > CPU
```

- 如果检测到 NVIDIA GPU 且 CUDA 可用 → 使用 **CUDA**
- 如果在 macOS 且检测到 Apple Silicon → 使用 **MLX**
- 其他情况 → 回退到 **CPU**

### 硬件设备与 Whisper 实现的对应关系

| 硬件设备 | 自动选择的实现 | 优势 | 备注 |
|---------|--------------|------|------|
| **NVIDIA GPU (CUDA)** | `faster-whisper` | 高速推理，支持大批量处理 | 统一实现，支持所有功能 |
| **Apple Silicon (M1-M5)** | `mlx-whisper` | 针对 Apple 芯片优化，统一内存架构 | Belle-whisper 模型不支持 |
| **CPU** | `faster-whisper` | 无硬件依赖，通用兼容性 | 统一实现，支持所有功能 |

### 模型支持矩阵

| 模型 | faster-whisper | mlx-whisper | 不支持时的自动回退 |
|-----|----------------|-------------|------------------|
| `large-v3` | ✅ | ✅ | - |
| `large-v3-turbo` | ✅ | ✅ | - |
| `belle-large-v3-zh` | ✅ | ❌ | 回退到 `large-v3` |

**自动回退机制**：

当请求的模型不支持当前实现时，whispi 会：
1. 自动回退到该实现支持的默认模型
2. 在终端显示蓝色提示信息，告知已切换模型
3. 继续正常执行转录任务，无需手动干预

**示例**：在 Apple Silicon (MLX) 上指定 `belle-large-v3-zh`，会自动回退到 `large-v3`。

### 说话人标注技术细节

whispi 使用 [pyannote.audio](https://github.com/pyannote/pyannote-audio) 的说话人分离模型（版本 3.1）实现词级别的说话人标注。

**工作原理**：
1. faster-whisper/mlx-whisper 完成转录并生成词级时间戳
2. pyannote.audio 对音频进行说话人分离分析
3. 通过时间戳对齐将说话人标签分配给每个词

**已知限制**：
- **多人同时说话**：多人同时说话时说话人分离可能不准确
- **语言支持**：pyannote.audio 模型本身是语言无关的，但转录需要支持词级时间戳的语言

---

## 批量处理

除了通过 `--files` 参数提供文件或文件夹，您还可以传递一个 `.list` 文件，其中混合包含文件和文件夹路径。

**示例**：

```bash
# 创建 .list 文件
cat > my_files.list << EOF
video_01.mp4
video_02.mp4
./my_files/
EOF

# 批量处理
whispi run -f my_files.list
```

### 使用配置文件进行批量处理

您可以通过 `--config` 参数提供 `.json` 配置文件，简化批量处理。

**配置文件示例**：

```json
{
    "files": "./files/my_files.list",
    "output_dir": "./transcriptions",
    "device": "auto",
    "model": "large-v3-turbo",
    "lang": null,
    "annotate": false,
    "num_speakers": null,
    "hf_token": "your_hf_token_here",
    "subtitle": false,
    "export": "all",
    "verbose": false
}
```

**使用方法**：

```bash
whispi run --config batch_config.json
```
