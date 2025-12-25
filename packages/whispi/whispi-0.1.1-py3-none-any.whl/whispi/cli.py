import os
import warnings
from pathlib import Path
from typing import List, Optional

import typer
from rich import print

from whispi import output_utils
from whispi.little_helper import DeviceChoice

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

cli_app = typer.Typer(no_args_is_help=True)


@cli_app.command("run", no_args_is_help=True)
def run_cmd(
    files: Optional[List[str]] = typer.Option(
        None,
        "--files",
        "-f",
        help="Path to file, folder or .list to process.",
    ),
    output_dir: Path = typer.Option(
        Path("./transcriptions"),
        "--output_dir",
        "-o",
        file_okay=False,
        dir_okay=True,
        writable=True,
        readable=True,
        resolve_path=True,
        help="Folder where transcripts should be saved.",
    ),
    device: DeviceChoice = typer.Option(
        DeviceChoice.AUTO,
        "--device",
        "-d",
        help=("CPU, GPU (NVIDIA), or MLX (Mac M1-M5)"),
    ),
    model: str = typer.Option(
        "large-v3-turbo",
        "--model",
        "-m",
        help='Whisper model to use (run "whispi list" to see options)',
    ),
    lang: Optional[str] = typer.Option(
        None,
        "--lang",
        "-l",
        help='Language of your file(s) ("en", "de") (Default: auto-detection)',
    ),
    annotate: bool = typer.Option(
        False,
        "--annotate",
        "-a",
        help="Enable speaker annotation (Default: False)",
    ),
    num_speakers: Optional[int] = typer.Option(
        None,
        "--num_speakers",
        "-num",
        help="Number of speakers to annotate (Default: auto-detection)",
    ),
    hf_token: Optional[str] = typer.Option(
        None,
        "--hf_token",
        "-hf",
        help="HuggingFace Access token required for speaker annotation",
    ),
    export_format: str = typer.Option(
        "txt",
        "--export",
        "-e",
        help="Export formats (comma-separated): txt, srt, webvtt, json, all",
    ),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        help="Path to configuration file",
    ),
):
    """
    Transcribe files with whispi
    """
    from whispi import little_helper, models

    # Load configuration from config.json if provided
    if config:
        config_data = little_helper.load_config(config)
        files = (
            files or Path(config_data.get("files"))
            if config_data.get("files")
            else files
        )
        output_dir = (
            Path(config_data.get("output_dir"))
            if config_data.get("output_dir")
            else output_dir
        )
        device = DeviceChoice(config_data.get("device", device.value))
        model = config_data.get("model", model)
        lang = config_data.get("lang", lang)
        annotate = config_data.get("annotate", annotate)
        num_speakers = config_data.get("num_speakers", num_speakers)
        hf_token = config_data.get("hf_token", hf_token)

    # Check if provided model is available
    if not models.ensure_model(model):
        msg = f"""→ Model "{model}" not available.\n→ Available models:\n..."""
        msg += "\n... ".join(models.WHISPER_MODELS.keys())
        print(f"{msg}")
        raise typer.Exit()

    # Check for HuggingFace Access Token if speaker annotation is enabled
    if annotate and not hf_token:
        # Try to get token from huggingface-cli login (recommended method)
        try:
            from huggingface_hub import HfFolder

            hf_token = HfFolder.get_token()
        except ImportError:
            pass

        # Fallback to environment variable
        if not hf_token:
            hf_token = os.getenv("HF_TOKEN")

        if not hf_token:
            print("→ Please provide a HuggingFace access token for speaker annotation.")
            print("  Recommended: Run `hf auth login` to authenticate")
            print(
                "  Alternative: Use --hf_token option or set HF_TOKEN environment variable"
            )
            raise typer.Exit()

    # Determine the computation device
    device_str = little_helper.get_device(device=device)

    deps_ok, deps_message = little_helper.check_dependencies_for_device(
        device=device_str, requested_device=device
    )
    if not deps_ok:
        print(f"[blue1]→ {deps_message}")
        raise typer.Exit(code=1)

    # Determine the export formats
    export_formats = output_utils.determine_export_formats(export_format, annotate)

    # Transcription
    if files:
        from whispi.transcription import TranscriptionHandler

        # Instantiate TranscriptionHandler
        try:
            service = TranscriptionHandler(
                base_dir=output_dir,
                device=device_str,
                model=model,
                file_language=lang,
                annotate=annotate,
                num_speakers=num_speakers,
                hf_token=hf_token,
                export_formats=export_formats,
            )
        except RuntimeError as exc:
            print(f"[blue1]→ {exc}")
            raise typer.Exit(code=1)
        # Process files
        service.process_files(files)
    else:
        print("[bold]→ Please provide a path to a file, folder or")
        print("  .list to start the transcription.")
        raise typer.Exit()


@cli_app.command("list")
def list_cmd():
    """
    List available models
    """
    from whispi.models import WHISPER_MODELS

    impl_device_map = {
        "faster-whisper": ["cpu", "gpu"],
        "mlx-whisper": ["mlx"],
    }
    device_order = ["cpu", "gpu", "mlx"]

    print("[bold]Available models for each device:[/bold]")
    for model_key, info in WHISPER_MODELS.items():
        device_support = {device: False for device in device_order}
        for impl, devices in impl_device_map.items():
            if info.get(impl):
                for device in devices:
                    device_support[device] = True

        supported_devices = [d for d in device_order if device_support[d]]
        devices_str = ", ".join(supported_devices)

        print(f"[blue bold]{model_key:<18}[/][gold3]→ [deep_pink4]{devices_str}")


def run():
    cli_app()


if __name__ == "__main__":
    run()
