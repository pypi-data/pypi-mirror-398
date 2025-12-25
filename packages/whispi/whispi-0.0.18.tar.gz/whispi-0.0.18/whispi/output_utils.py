import json
import logging
from enum import Enum
from pathlib import Path
from typing import List

import typer
from rich import print

from whispi import little_helper

# Set logging configuration
logger = logging.getLogger("little_helper")
logger.setLevel(logging.INFO)


class ExportFormats(str, Enum):
    ALL = "all"
    JSON = "json"
    TXT = "txt"
    WEBVTT = "webvtt"
    SRT = "srt"


def determine_export_formats(
    export_format: str, annotate: bool
) -> List[str]:
    """
    Determine the export formats based on user options.

    Supports comma-separated format list (e.g., "txt,srt,json").
    Valid formats: txt, srt, webvtt, json, all

    Args:
        export_format: Comma-separated export format string
        annotate: Whether speaker annotation is enabled

    Returns:
        List of export format strings
    """
    valid_formats = {"txt", "srt", "webvtt", "json", "all"}
    available_formats = set()

    # Parse comma-separated formats
    requested_formats = [f.strip().lower() for f in export_format.split(",")]

    for fmt in requested_formats:
        if fmt not in valid_formats:
            print(f"→ Unknown export format: {fmt}")
            print(f"  Valid formats: {', '.join(sorted(valid_formats))}")
            raise typer.Exit()

        if fmt == "all":
            # ALL includes everything available
            available_formats.add("json")
            available_formats.add("txt")
            available_formats.add("srt")
            available_formats.add("webvtt")
        else:
            # Individual format
            available_formats.add(fmt)

    return list(available_formats)


class OutputWriter:
    """
    Class for writing various output formats to disk.
    """

    def __init__(self):
        self.cwd = Path.cwd()

    def _save_file(
        self, content: str, filepath: Path, description: str, log_message: str
    ) -> None:
        """
        Generic method to save content to a file.
        """
        with open(filepath, "w", encoding="utf-8") as file:
            file.write(content)
        print(f"[blue1]→ Saved {description}: [bold]{filepath.relative_to(self.cwd)}")
        logger.info(f"{log_message} {filepath}")

    def save_json(self, result: dict, filepath: Path) -> None:
        with open(filepath, "w", encoding="utf-8") as fout:
            json.dump(result, fout, indent=4, ensure_ascii=False)
        print(f"[blue1]→ Saved .json: [bold]{filepath.relative_to(self.cwd)}")
        logger.info(f"Saved .json to {filepath}")

    def save_txt(self, transcription: dict, filepath: Path) -> None:
        """
        Save the transcription as a TXT file with timestamps.

        Args:
            transcription: Dict with 'text' and 'chunks' keys
            filepath: Output file path
        """
        text = self._format_timestamped_txt(transcription)

        self._save_file(
            content=text,
            filepath=filepath,
            description=".txt (timestamped)",
            log_message="Saved .txt transcript to",
        )

    def _format_timestamped_txt(self, transcription: dict) -> str:
        """
        Format transcription chunks with simple timestamps.

        Format: [MM:SS] Text content

        Args:
            transcription: Dict with 'chunks' key containing list of chunks

        Returns:
            Formatted string with one chunk per line
        """
        from whispi import little_helper

        chunks = transcription.get("chunks", [])
        if not chunks:
            return transcription.get("text", "").strip()

        lines = []
        for chunk in chunks:
            timestamp = chunk.get("timestamp")
            text = chunk.get("text", "").strip()

            if not timestamp or len(timestamp) < 2:
                lines.append(text)
                continue

            start_time = timestamp[0]

            if start_time is None:
                lines.append(text)
                continue

            # Use simple MM:SS format for readability
            start_str = little_helper.format_time_simple(start_time)

            line = f"[{start_str}] {text}"
            lines.append(line)

        return "\n".join(lines)

    def _format_timestamped_txt_with_speakers(self, transcription: dict) -> str:
        """
        Format transcription chunks with simple timestamps AND speaker labels.

        Format: [MM:SS] [SPEAKER_00] Text content

        Args:
            transcription: Dict with 'chunks' key containing list of chunks with speaker info

        Returns:
            Formatted string with timestamps and speaker labels
        """
        from whispi import little_helper

        chunks = transcription.get("chunks", [])
        if not chunks:
            return transcription.get("text_with_speaker_annotation", "").strip()

        lines = []
        for chunk in chunks:
            timestamp = chunk.get("timestamp")
            text = chunk.get("text", "").strip()

            if not timestamp or len(timestamp) < 2:
                lines.append(text)
                continue

            start_time = timestamp[0]

            if start_time is None:
                lines.append(text)
                continue

            # Use simple MM:SS format for readability
            start_str = little_helper.format_time_simple(start_time)

            # Get speaker from chunk level (preferred) or from first word
            speaker = chunk.get("speaker")
            if not speaker:
                words = chunk.get("words", [])
                if words and len(words) > 0:
                    speaker = words[0].get("speaker")

            if speaker:
                line = f"[{start_str}] [{speaker}] {text}"
            else:
                line = f"[{start_str}] {text}"

            lines.append(line)

        return "\n".join(lines)

    def save_txt_with_speaker_annotation(
        self, annotated_text: str, filepath: Path
    ) -> None:
        """
        Save the annotated transcription as a TXT file.
        """
        self._save_file(
            content=annotated_text,
            filepath=filepath,
            description=".txt with speaker annotation",
            log_message="Saved .txt transcription with speaker annotation →",
        )

    def save_subtitles(self, text: str, type: str, filepath: Path) -> None:
        """
        Save subtitles in the specified format.
        """
        description = f".{type} subtitles"
        log_message = f"Saved .{type} subtitles →"
        self._save_file(
            content=text,
            filepath=filepath,
            description=description,
            log_message=log_message,
        )

    def save_results(
        self, result: dict, export_formats: List[str], speaker_only: bool = False
    ) -> List[Path]:
        """
        Write various output formats to disk based on the specified
        export formats.

        Args:
            result: Transcription result dictionary
            export_formats: List of formats to export
            speaker_only: If True, only export speaker-annotated formats.
                          If False, export non-speaker formats only.
                          Used for progressive export when annotate=True.
        """
        output_filepath = Path(result["output_filepath"])
        written_filepaths = []

        transcription_items = result.get("transcription", {}).items()

        # Check if speaker annotation is available
        has_speaker_annotation = any(
            "text_with_speaker_annotation" in transcription
            for transcription in result["transcription"].values()
        )

        # Write .txt (non-speaker or speaker-annotated)
        if "txt" in export_formats:
            if speaker_only:
                # Only write annotated TXT (speaker-only mode)
                if has_speaker_annotation:
                    for language, transcription in transcription_items:
                        if "text_with_speaker_annotation" in transcription:
                            fout = (
                                output_filepath.parent
                                / f"{output_filepath.name}_{language}_annotated.txt"
                            )

                            # Use the pre-formatted text_with_speaker_annotation if available
                            annotated_text = transcription.get("text_with_speaker_annotation")

                            self.save_txt_with_speaker_annotation(
                                annotated_text=annotated_text,
                                filepath=fout,
                            )
                            written_filepaths.append(str(fout))
            else:
                # Write regular TXT (non-speaker mode)
                for language, transcription in transcription_items:
                    fout = (
                        output_filepath.parent / f"{output_filepath.name}_{language}.txt"
                    )

                    # Skip if already written during streaming
                    streamed_txt = result.get("streamed_txt_file")
                    if streamed_txt and Path(streamed_txt) == fout:
                        print(
                            f"[blue1]→ TXT already streamed during transcription: [bold]{fout.relative_to(self.cwd)}"
                        )
                        written_filepaths.append(str(fout))
                        continue

                    self.save_txt(transcription, filepath=fout)
                    written_filepaths.append(str(fout))

        # Write subtitles (.srt and .webvtt) - non-speaker only
        if not speaker_only:
            subtitle_formats = {"srt", "webvtt"}
            if subtitle_formats.intersection(export_formats):
                for language, transcription in transcription_items:
                    # .srt subtitles
                    if "srt" in export_formats:
                        fout = (
                            output_filepath.parent
                            / f"{output_filepath.name}_{language}.srt"
                        )
                        srt_text = create_subtitles(transcription, type="srt")
                        self.save_subtitles(srt_text, type="srt", filepath=fout)
                        written_filepaths.append(str(fout))

                    # .webvtt subtitles
                    if "webvtt" in export_formats:
                        fout = (
                            output_filepath.parent
                            / f"{output_filepath.name}_{language}.webvtt"
                        )
                        webvtt_text = create_subtitles(
                            transcription, type="webvtt", result=result
                        )
                        self.save_subtitles(webvtt_text, type="webvtt", filepath=fout)
                        written_filepaths.append(str(fout))

        # Write .json - always write in non-speaker mode, or write final in speaker-only mode
        if "json" in export_formats:
            if not speaker_only:
                # In non-speaker mode, write JSON without final speaker annotation
                fout = output_filepath.with_suffix(".json")
                written_filepaths.append(str(fout))
                result["written_files"] = written_filepaths
                self.save_json(result, filepath=fout)
            elif has_speaker_annotation:
                # In speaker-only mode, update JSON with final speaker annotation
                fout = output_filepath.with_suffix(".json")
                written_filepaths.append(str(fout))
                result["written_files"] = written_filepaths
                self.save_json(result, filepath=fout)

        return written_filepaths


def create_subtitles(
    transcription_dict: dict, type: str = "srt", result: dict = None
) -> str:
    """
    Converts a transcription dictionary into subtitle format (.srt or .webvtt).
    """
    subtitle_text = ""
    seg_id = 0

    for chunk in transcription_dict["chunks"]:
        start_time = chunk["timestamp"][0]
        end_time = chunk["timestamp"][1]
        text = chunk["text"].replace("'", "'")

        if type == "srt":
            start_time_str = little_helper.format_time(start_time, delimiter=",")
            end_time_str = little_helper.format_time(end_time, delimiter=",")
            seg_id += 1
            subtitle_text += (
                f"{seg_id}\n{start_time_str} --> {end_time_str}\n{text.strip()}\n\n"
            )
        elif type == "webvtt":
            start_time_str = little_helper.format_time(start_time, delimiter=".")
            end_time_str = little_helper.format_time(end_time, delimiter=".")

            if seg_id == 0:
                subtitle_text += f"WEBVTT {Path(result['output_filepath']).stem}\n\n"
                subtitle_text += "NOTE transcribed with whispi\n\n"
                subtitle_text += (
                    f"NOTE media: {Path(result['input_filepath']).absolute()}\n\n"
                )

            seg_id += 1
            subtitle_text += (
                f"{seg_id}\n{start_time_str} --> {end_time_str}\n{text.strip()}\n\n"
            )

    return subtitle_text

