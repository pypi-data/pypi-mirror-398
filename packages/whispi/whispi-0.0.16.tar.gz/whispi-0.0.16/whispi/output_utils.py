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
    RTTM = "rttm"
    WEBVTT = "webvtt"
    SRT = "srt"


def determine_export_formats(
    export_format: str, annotate: bool
) -> List[str]:
    """
    Determine the export formats based on user options.

    Supports comma-separated format list (e.g., "txt,srt,json").
    Valid formats: txt, srt, webvtt, json, rttm, all

    Args:
        export_format: Comma-separated export format string
        annotate: Whether speaker annotation is enabled

    Returns:
        List of export format strings
    """
    valid_formats = {"txt", "srt", "webvtt", "json", "rttm", "all"}
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
            if annotate:
                available_formats.add("rttm")
        elif fmt == "rttm":
            # RTTM requires annotation
            if not annotate:
                print("→ RTTM export format requires --annotate option.")
                raise typer.Exit()
            available_formats.add(fmt)
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
            words = chunk.get("words", [])

            if not timestamp or len(timestamp) < 2:
                lines.append(text)
                continue

            start_time = timestamp[0]

            if start_time is None:
                lines.append(text)
                continue

            # Use simple MM:SS format for readability
            start_str = little_helper.format_time_simple(start_time)

            # Get speaker from first word in chunk
            speaker = None
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

    def save_rttm_annotations(self, rttm: str, filepath: Path) -> None:
        self._save_file(
            content=rttm,
            filepath=filepath,
            description=".rttm annotations",
            log_message="Saved .rttm annotations →",
        )

    def save_results(self, result: dict, export_formats: List[str]) -> List[Path]:
        """
        Write various output formats to disk based on the specified
        export formats.

        Args:
            result: Transcription result dictionary
            export_formats: List of formats to export
        """
        output_filepath = Path(result["output_filepath"])
        written_filepaths = []

        transcription_items = result.get("transcription", {}).items()

        # Write .txt
        if "txt" in export_formats:
            for language, transcription in transcription_items:
                fout = output_filepath.parent / f"{output_filepath.name}_{language}.txt"

                # Skip if already written during streaming
                streamed_txt = result.get('streamed_txt_file')
                if streamed_txt and Path(streamed_txt) == fout:
                    print(f"[blue1]→ TXT already streamed during transcription: [bold]{fout.relative_to(self.cwd)}")
                    written_filepaths.append(str(fout))
                    continue

                self.save_txt(transcription, filepath=fout)
                written_filepaths.append(str(fout))

        # Write subtitles (.srt and .webvtt)
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

        # Write annotated .txt with speaker annotations
        has_speaker_annotation = any(
            "text_with_speaker_annotation" in transcription
            for transcription in result["transcription"].values()
        )

        if "txt" in export_formats and has_speaker_annotation:
            for language, transcription in transcription_items:
                if "text_with_speaker_annotation" in transcription:
                    fout = (
                        output_filepath.parent
                        / f"{output_filepath.name}_{language}_annotated.txt"
                    )

                    annotated_text = self._format_timestamped_txt_with_speakers(transcription)

                    self.save_txt_with_speaker_annotation(
                        annotated_text=annotated_text,
                        filepath=fout,
                    )
                    written_filepaths.append(str(fout))

        # Write .rttm
        if "rttm" in export_formats:
            rttm_dict = dict_to_rttm(result)
            for language, rttm_annotation in rttm_dict.items():
                fout = (
                    output_filepath.parent / f"{output_filepath.name}_{language}.rttm"
                )
                self.save_rttm_annotations(rttm=rttm_annotation, filepath=fout)
                written_filepaths.append(str(fout))

        # Write .json
        if "json" in export_formats:
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


def dict_to_rttm(result: dict) -> dict:
    """
    Converts a transcription dictionary to RTTM file format.
    """
    file_id = result.get("input_filepath", "unknown_file")
    file_id = Path(file_id).stem
    rttm_dict = {}

    for lang, transcription in result.get("transcription", {}).items():
        lines = []
        current_speaker = None
        speaker_start_time = None
        speaker_end_time = None

        chunks = transcription.get("chunks", [])
        all_words = []
        for chunk in chunks:
            words = chunk.get("words", [])
            all_words.extend(words)

        all_words.sort(key=lambda w: w.get("start", 0.0))

        for word_info in all_words:
            speaker = word_info.get("speaker", "SPEAKER_00")
            word_start = word_info.get("start", 0.0)
            word_end = word_info.get("end", word_start)

            if speaker != current_speaker:
                if current_speaker is not None:
                    duration = speaker_end_time - speaker_start_time
                    rttm_line = (
                        f"SPEAKER {file_id} 1 {speaker_start_time:.3f} "
                        f"{duration:.3f} <NA> <NA> {current_speaker} <NA>"
                    )
                    lines.append(rttm_line)

                current_speaker = speaker
                speaker_start_time = word_start
                speaker_end_time = word_end
            else:
                speaker_end_time = max(speaker_end_time, word_end)

        if current_speaker is not None:
            duration = speaker_end_time - speaker_start_time
            rttm_line = (
                f"SPEAKER {file_id} 1 {speaker_start_time:.3f} {duration:.3f} "
                f"<NA> <NA> {current_speaker} <NA>"
            )
            lines.append(rttm_line)

        rttm_content = "\n".join(lines)
        rttm_dict[lang] = rttm_content

    return rttm_dict
