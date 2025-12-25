import logging
import time
from pathlib import Path
from datetime import datetime
from functools import partial
from rich import print

from whispi import output_utils, models
from whispi import little_helper as help
from whispi.little_helper import FilePathProcessor

# Set logging configuration
log_dir = help.ensure_dir(Path('./logs'))
log_filename = f"log_whispi_{datetime.now().strftime('%Y-%m-%d')}.log"
log_file = f"{log_dir}/{log_filename}"

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(funcName)s]: %(message)s",
)


class TranscriptionHandler:
    """
    Handles transcription and diarization of audio/video files using various
    Whisper-based models.

    This class leverages different implementations of OpenAI's Whisper models
    (faster-whisper, mlx-whisper) to transcribe audio and
    video files. It supports features like language detection, speaker
    diarization, and exporting transcriptions in multiple formats.
    It is capable of processing single files, directories,
    and lists of files, providing flexibility for diverse transcription
    needs.

    Args:
        base_dir (str, optional): Directory to store transcription outputs.
            Defaults to './transcriptions'.
        model (str, optional): Whisper model variant to use (e.g., 'large-v3-turbo' or 'large-v3').
            Defaults to 'large-v3-turbo'.
        device (str, optional): Compute device ('cpu', 'cuda', 'mlx').
            Defaults to 'cpu'.
        file_language (str, optional): Language of the input audio.
            If not provided, language detection is performed.
        annotate (bool, optional): Enable speaker diarization.
            Defaults to False.
        hf_token (str, optional): Hugging Face token for accessing restricted
            models or features.
        export_formats (str or list, optional): Formats to export
            transcriptions (e.g., 'txt', 'srt', 'json', 'all').
            Comma-separated for multiple formats. Defaults to 'all'.

    Attributes:
        base_dir (Path): Directory for storing transcriptions.
        device (str): Compute device in use.
        file_language (str or None): Detected or specified language of the
            audio.
        annotate (bool): Indicates if speaker diarization is enabled.
        export_formats (str or list): Selected formats for exporting
            transcriptions.
        processed_files (list): List of processed file information and results.

    Methods:
        get_filepaths(filepath: str):
            Retrieves and validates file paths from various input types.

        detect_language(file: Path, audio_array) -> str:
            Detects the language of the given audio file.

        process_files(files: list):
            Processes a list of audio files for transcription and diarization.

        transcribe_with_whisperx(filepath: Path) -> dict:
            Transcribes an audio file using the whisperX implementation.

        transcribe_with_mlx_whisper(filepath: Path) -> dict:
            Transcribes an audio file using the mlx-whisper implementation.

        transcribe_with_faster_whisper(filepath: Path, num_workers: int = 1)
            -> dict:
            Transcribes an audio file using the faster-whisper implementation.

        adjust_word_chunk_length(result: dict) -> dict:
            Splits transcription text into chunks based on a maximum word
            count.

        to_transcription_dict(insanely_annotation: list[dict]) -> dict:
            Converts speaker-annotated results into a standardized dictionary.

        to_whisperx(transcription_result: dict) -> dict:
            Normalizes transcription results to the whisperX format.

        create_text_with_speakers(transcription_dict: dict,
            delimiter: str = '.') -> dict:
            Inserts speaker labels into the transcription text upon speaker
            changes.
    """
    def __init__(
        self,
        base_dir='./transcriptions',
        model='large-v3-turbo',
        device='cpu',
        file_language=None,
        annotate=False,
        num_speakers=None,
        hf_token=None,
        export_formats='all',
    ):
        self.base_dir = help.ensure_dir(Path(base_dir))
        self.file_formats = help.return_valid_fileformats()
        self.device = device
        self.file_language = file_language
        self.file_language_provided = file_language is not None
        self.model = None
        self.model_provided = model
        self.annotate = annotate
        self.num_speakers = num_speakers
        self.hf_token = hf_token
        self.export_formats = export_formats
        self.metadata = self._collect_metadata()
        self.filepaths = []
        self.output_dir = None
        self.processed_files = []

    def _collect_metadata(self):
        return {
            'output_dir': str(self.base_dir),
            'file_language': self.file_language,
            'model': self.model_provided,
            'device': self.device,
            'annotate': self.annotate,
            'num_speakers': self.num_speakers,
            }

    def _close_streaming_file(self, handle, path: Path) -> None:
        """安全关闭流式 TXT 文件"""
        if handle:
            try:
                handle.close()
                logging.info(f"Closed streaming TXT file: {path}")
            except Exception as e:
                logging.error(f"Failed to close streaming TXT file: {e}")

    def _export_intermediate_results(
        self,
        filepath: Path,
        output_filepath: Path,
        transcription_result: dict,
        streaming_txt_path: Path = None
    ) -> None:
        """在说话人分离前导出非说话人格式文件（SRT, WEBVTT, TXT, JSON）"""
        intermediate_result = {
            'id': 'intermediate',
            'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'input_filepath': str(filepath.absolute()),
            'output_filepath': str(output_filepath.absolute()),
            'written_files': None,
            'device': self.device,
            'model': self.model,
            'transcription': {self.file_language: transcription_result},
        }
        if streaming_txt_path:
            intermediate_result['streamed_txt_file'] = str(streaming_txt_path)

        logging.info("Exporting non-speaker files (SRT, WEBVTT, JSON)...")
        output_utils.OutputWriter().save_results(
            result=intermediate_result,
            export_formats=self.export_formats,
            speaker_only=False,
        )

    def _run_diarization(self, filepath: Path, transcript_chunks: list) -> list:
        """运行 pyannote.audio 说话人分离并合并结果"""
        from whispi import diarize_utils

        logging.info("Starting diarization...")
        progress = help.create_dual_progress()
        diarize_task_id = None

        def progress_hook(step_name, step_artifact, file=None, total=None, completed=None, **kwargs):
            if diarize_task_id is not None and total is not None and completed is not None:
                if total > 0:
                    progress.update(diarize_task_id, completed=completed, total=total)

        with progress:
            diarize_task_id = progress.add_task(
                f"[purple]→ Diarizing [bold]{filepath.name}",
                total=None  # 由 pyannote hook 动态设置
            )
            diarization_segments = diarize_utils.diarize_audio_only(
                file_name=str(filepath),
                diarization_model='pyannote/speaker-diarization-community-1',
                hf_token=self.hf_token,
                num_speakers=self.num_speakers,
                min_speakers=None,
                max_speakers=None,
                progress_hook=progress_hook,
            )

        return diarize_utils.merge_diarization_with_transcript(
            diarization_segments, transcript_chunks, group_by_speaker=False
        )

    def _finalize_transcription_result(
        self,
        transcription_result: dict,
        streaming_txt_path: Path = None
    ) -> dict:
        """构建最终转录结果字典"""
        result = {'transcriptions': {}}
        result['transcriptions'][self.file_language] = transcription_result

        if self.annotate:
            result = self.create_text_with_speakers(result)

        result_dict = {'transcription': result}
        if streaming_txt_path:
            result_dict['streamed_txt_file'] = str(streaming_txt_path)

        return result_dict

    def adjust_word_chunk_length(self, result: dict) -> dict:
        """
        Pass-through method: returns segments as-is without any processing.
        Each original Whisper segment becomes one subtitle chunk.

        Parameters:
            result (dict): The nested dictionary containing segments.

        Returns:
            dict: A dictionary containing 'text' and 'chunks' list.
        """
        segments = result.get('segments', [])

        # Handle empty result
        if not segments:
            return {'text': '', 'chunks': []}

        # Convert segments to chunks format with 'timestamp' key
        chunks = []
        for segment in segments:
            chunk = {
                'text': segment.get('text', ''),
                'timestamp': (segment.get('start', 0.0), segment.get('end', 0.0))
            }
            # Include words if present
            if 'words' in segment:
                chunk['words'] = segment['words']
            # Include speaker if present
            if 'speaker' in segment:
                chunk['speaker'] = segment['speaker']
            chunks.append(chunk)

        # Build final result text
        result_text = ' '.join(
            segment.get('text', '').strip() for segment in segments
        )

        return {
            'text': result_text,
            'chunks': chunks
        }

    def to_transcription_dict(self, insanely_annotation: list[dict]) -> dict:
        """
        Transform insanely-fast-whisper speaker annotation result to dict.
        """
        chunks = []
        for s in insanely_annotation:
            chunk = {
                'text': s['text'],
                'timestamp': (s['timestamp'][0], s['timestamp'][1]),
                'speaker': s['speaker']
            }
            chunks.append(chunk)

        result = {
            'text': ''.join([s['text'] for s in insanely_annotation]),
            'chunks': chunks
        }
        return result

    def to_whisperx(self, transcription_result: dict) -> dict:
        """
        Normalize insanely-fast-whisper transcription result to whisperX dict.
        """
        words = []
        for c in transcription_result['chunks']:
            if 'speaker' in c:
                word = {
                    'word': c['text'].strip(),
                    'start': c['timestamp'][0],
                    'end': c['timestamp'][1],
                    'speaker': c['speaker']
                }
            else:
                word = {
                    'word': c['text'].strip(),
                    'start': c['timestamp'][0],
                    'end': c['timestamp'][1]
                }
            words.append(word)

        result = {
            'segments': [
                {
                    'start': transcription_result['chunks'][0]['timestamp'][0],
                    'end': transcription_result['chunks'][-1]['timestamp'][1],
                    'text': transcription_result['text'].strip(),
                    'words': words
                }
            ]
        }
        return result

    def create_text_with_speakers(
        self,
        transcription_dict: dict,
        delimiter: str = '.'
    ) -> dict:
        """
        Iterates through all chunks of each language and creates the complete
        text with speaker labels inserted when there is a speaker change.

        Supports two data structures:
        1. whisperX format: chunks[].words[] with word/start/speaker
        2. diarization format: flat chunks[] with text/timestamp/speaker

        Args:
            transcription_dict (dict): The dictionary containing transcription
            data.

        Returns:
            dict: A dictionary mapping each language to its formatted text with
            speaker labels.
        """
        transcriptions = transcription_dict.get('transcriptions', {})

        for lang, lang_data in transcriptions.items():
            text = ""
            current_speaker = None
            chunks = lang_data.get('chunks', [])

            for chunk in chunks:
                words = chunk.get('words', [])

                if words:
                    # whisperX format: chunks[].words[]
                    for word_info in words:
                        speaker = word_info.get('speaker')
                        word = word_info.get('word', '')
                        start_timestamp = help.format_time(
                            word_info.get('start'),
                            delimiter
                            )

                        # Insert speaker label if a speaker change is detected
                        if speaker != current_speaker:
                            text += f"\n[{start_timestamp}] [{speaker}] "
                            current_speaker = speaker

                        # Append the word with a space
                        text += word + " "
                else:
                    # Diarization format: flat chunks with text/timestamp/speaker
                    speaker = chunk.get('speaker')
                    chunk_text = chunk.get('text', '')
                    timestamp = chunk.get('timestamp', (None, None))
                    start_time = timestamp[0] if timestamp else None
                    start_timestamp = help.format_time(start_time, delimiter)

                    # Each chunk gets its own timestamp and speaker label
                    text += f"\n[{start_timestamp}] [{speaker}] {chunk_text.strip()}"

            transcription_dict['transcriptions'][lang][
                'text_with_speaker_annotation'
            ] = text.strip()

        return transcription_dict

    def to_mlx_chunks(self, mlx_result: dict) -> dict:
        """
        Normalize mlx-whisper results to a chunk-based structure that mirrors
        the insanely-fast-whisper output.
        """
        def _to_float(value, default=0.0) -> float:
            try:
                return float(value)
            except (TypeError, ValueError):
                return default

        chunks = []
        segments = mlx_result.get('segments') or []

        for segment in segments:
            seg_start = round(_to_float(segment.get('start'), 0.0), 2)
            seg_end = round(
                _to_float(segment.get('end'), seg_start),
                2
            )
            words = segment.get('words') or []

            if words:
                for word in words:
                    word_text = (
                        word.get('word')
                        or word.get('text')
                        or str(word.get('token', '')).strip()
                    )
                    if not word_text:
                        continue

                    w_start = round(
                        _to_float(word.get('start'), seg_start),
                        2
                    )
                    w_end = round(
                        _to_float(word.get('end'), w_start),
                        2
                    )

                    chunks.append({
                        'text': word_text.strip(),
                        'timestamp': (w_start, w_end)
                    })
            else:
                seg_text = segment.get('text', '').strip()
                if seg_text:
                    chunks.append({
                        'text': seg_text,
                        'timestamp': (seg_start, seg_end)
                    })

        if not chunks and mlx_result.get('text'):
            chunks.append({
                'text': mlx_result['text'].strip(),
                'timestamp': (0.0, 0.0)
            })

        text = ' '.join([c['text'].strip() for c in chunks])
        return {'text': text, 'chunks': chunks}

    def transcribe_with_mlx_whisper(
        self, filepath: Path, output_filepath: Path = None
    ) -> dict:
        """
        Transcribes a file using the 'mlx-whisper' implementation:
        https://huggingface.co/mlx-community

        This method utilizes the MLX implementation of OpenAI Whisper for
        Apple Silicon devices.

        Parameters:
        - filepath (Path): The path to the audio file for transcription.
        - output_filepath (Path): The path to use for output files.

        Returns:
        - dict: A dictionary containing the transcription result and, if
                speaker detection is enabled, the speaker diarization result.
        """
        try:
            import mlx_whisper
        except ImportError as exc:
            raise ImportError(
                "mlx-whisper is required to run transcriptions on MLX. "
                "Install it with `pip install mlx-whisper` (macOS only)."
            ) from exc

        logging.info(
            f"👨‍💻 Transcription started with 🍎 mlx-whisper "
            f"for {filepath.name}"
        )
        t_start = time.time()

        try:
            def transcription_task(task: str = 'transcribe', language=None):
                try:
                    return mlx_whisper.transcribe(
                        str(filepath),
                        path_or_hf_repo=self.model,
                        task=task,
                        language=language,
                        word_timestamps=False,  # Segment-level timestamps are sufficient
                    )
                except TypeError:
                    logging.info(
                        "mlx-whisper does not support `word_timestamps` in "
                        "this version. Falling back to default call."
                    )
                    return mlx_whisper.transcribe(
                        str(filepath),
                        path_or_hf_repo=self.model,
                        task=task,
                        language=language,
                    )

            # SEQUENTIAL EXECUTION: Run transcription first, then diarization
            if self.annotate:
                logging.info("Starting transcription and diarization (MLX)")

                # Step 1: Transcription
                raw_result = help.run_with_progress(
                    description=(
                        f"[cyan]→ Transcribing ({self.device.upper()}) "
                        f"[bold]{filepath.name}"
                    ),
                    task=partial(
                        transcription_task,
                        task='transcribe',
                        language=self.file_language
                    )
                )

                # Convert MLX result to chunks format
                transcription_result = self.to_mlx_chunks(raw_result)

                # Step 1.5: Export non-speaker files before diarization
                if output_filepath:
                    self._export_intermediate_results(
                        filepath, output_filepath, transcription_result
                    )

                # Step 2: Diarization
                annotated_chunks = self._run_diarization(
                    filepath, transcription_result['chunks']
                )

                # Convert to transcription format
                transcription_result = self.to_transcription_dict(annotated_chunks)

                logging.info("Transcription and diarization completed (MLX)")

            else:
                # Only transcription, no diarization
                raw_result = help.run_with_progress(
                    description=(
                        f"[cyan]→ Transcribing ({self.device.upper()}) "
                        f"[bold]{filepath.name}"
                    ),
                    task=partial(
                        transcription_task,
                        task='transcribe',
                        language=self.file_language
                    )
                )
                transcription_result = self.to_mlx_chunks(raw_result)

            return self._finalize_transcription_result(transcription_result)
        except Exception:
            logging.exception("Transcription failed with mlx-whisper")
            raise
        finally:
            logging.info(
                f"👨‍💻 Transcription ended in {time.time() - t_start:.2f} sec."
            )

    def transcribe_with_faster_whisper(
        self,
        filepath: Path,
        num_workers: int = 1,
        output_filepath: Path = None
    ) -> dict:
        """
        Transcribes an audio file using the 'faster-whisper' implementation:
        https://github.com/SYSTRAN/faster-whisper

        Parameters:
        - filepath (Path): The path to the audio file for transcription.
        - num_workers (int): The number of workers to use for transcription.

        Returns:
        - dict: A dictionary containing the transcription result and, if
                speaker detection is enabled, the speaker diarization result.
        """
        from faster_whisper import WhisperModel, BatchedInferencePipeline

        # Start and time transcription
        logging.info(
            f"👨‍💻 Transcription started with 🏃‍♀️‍➡️ faster-whisper "
            f"for {filepath.name}"
        )
        t_start = time.time()

        # Load model and set parameters
        model = BatchedInferencePipeline(
            model=WhisperModel(
                self.model,
                device='cpu' if self.device in ['mps', 'cpu'] else 'cuda',
                num_workers=num_workers,
                compute_type=(
                    'int8' if self.device in ['mps', 'cpu'] else 'float16'
                )
            )
        )

        # Initialize streaming TXT file if needed (only when not annotating)
        streaming_txt_handle = None
        streaming_txt_path = None
        if output_filepath and 'txt' in self.export_formats and not self.annotate:
            streaming_txt_path = output_filepath.parent / f"{output_filepath.name}_{self.file_language}.txt"
            try:
                streaming_txt_handle = open(streaming_txt_path, 'w', encoding='utf-8')
                logging.info(f"Opened streaming TXT file: {streaming_txt_path}")
            except Exception as e:
                logging.error(f"Failed to open streaming TXT file: {e}")
                streaming_txt_handle = None
                streaming_txt_path = None

        # Define the transcription task
        def transcription_task():
            segments, _ = model.transcribe(
                str(filepath),
                beam_size=5,
                language=self.file_language,
                word_timestamps=True,  # Enable word timestamps for annotate/subtitle
                batch_size=16
            )

            chunks = []
            for segment in segments:
                seg = {
                    'timestamp': (
                        float(f"{segment.start:.2f}"),
                        float(f"{segment.end:.2f}")
                    ),
                    'text': segment.text.strip(),
                    'words': [{
                        'word': i.word.strip(),
                        'start': float(f"{i.start:.2f}"),
                        'end': float(f"{i.end:.2f}"),
                        'score': float(f"{i.probability:.2f}")
                    } for i in segment.words]
                }
                chunks.append(seg)

                # Stream write to TXT file if handle is open (simple format: [MM:SS] text)
                nonlocal streaming_txt_handle
                if streaming_txt_handle:
                    try:
                        start_seconds = seg['timestamp'][0]
                        minutes = int(start_seconds // 60)
                        seconds = int(start_seconds % 60)
                        time_str = f"{minutes:02d}:{seconds:02d}"
                        line = f"[{time_str}] {seg['text']}\n"
                        streaming_txt_handle.write(line)
                        streaming_txt_handle.flush()  # Immediately write to disk
                    except Exception as e:
                        logging.error(f"Failed to write segment to streaming TXT: {e}")

            return chunks

        # SEQUENTIAL EXECUTION: Run transcription first, then diarization
        if self.annotate:
            logging.info("Starting transcription and diarization")

            # Get audio duration for progress calculation
            audio_duration = help.get_audio_duration(filepath)

            # Step 1: Transcription with progress
            progress = help.create_dual_progress()
            transcribe_task_id = None

            chunks = []
            with progress:
                transcribe_task_id = progress.add_task(
                    f"[cyan]→ Transcribing ({self.device.upper()}) [bold]{filepath.name}",
                    total=100
                )
                segments, _ = model.transcribe(
                    str(filepath),
                    beam_size=5,
                    language=self.file_language,
                    word_timestamps=True,
                    batch_size=16
                )

                for segment in segments:
                    seg = {
                        'timestamp': (
                            float(f"{segment.start:.2f}"),
                            float(f"{segment.end:.2f}")
                        ),
                        'text': segment.text.strip(),
                        'words': [{
                            'word': i.word.strip(),
                            'start': float(f"{i.start:.2f}"),
                            'end': float(f"{i.end:.2f}"),
                            'score': float(f"{i.probability:.2f}")
                        } for i in segment.words]
                    }
                    chunks.append(seg)

                    # Update transcription progress
                    if audio_duration > 0:
                        pct = min(100, (segment.end / audio_duration) * 100)
                        progress.update(transcribe_task_id, completed=pct)

            # Close streaming TXT file if open
            self._close_streaming_file(streaming_txt_handle, streaming_txt_path)

            # Step 1.5: Export non-speaker files before diarization
            if output_filepath:
                transcription_result_for_export = self._chunks_to_result_format(chunks)
                self._export_intermediate_results(
                    filepath, output_filepath, transcription_result_for_export, streaming_txt_path
                )

            # Step 2: Diarization - convert chunks to word-level for diarization
            transcript_chunks = [
                {'text': w['word'], 'timestamp': (w['start'], w['end'])}
                for chunk in chunks
                for w in chunk['words']
            ]
            annotated_chunks = self._run_diarization(filepath, transcript_chunks)

            # Convert to transcription format
            trans_dict = self.to_transcription_dict(annotated_chunks)
            transcription_result = self.to_whisperx(trans_dict)

            logging.info("Transcription and diarization completed")

        else:
            # SEQUENTIAL: Only transcription, no diarization
            chunks = help.run_with_progress(
                description=(
                    f"[cyan]→ Transcribing ({self.device.upper()}) "
                    f"[bold]{filepath.name}"
                ),
                task=transcription_task
            )

            # Close streaming TXT file if open
            self._close_streaming_file(streaming_txt_handle, streaming_txt_path)

            # Convert to standard format
            transcription_result = self._chunks_to_result_format(chunks)

        # Stop timing transcription
        logging.info(
            f"👨‍💻 Transcription completed in {time.time() - t_start:.2f} sec."
        )

        return self._finalize_transcription_result(transcription_result, streaming_txt_path)

    def _faster_whisper_to_whisperx(self, chunks: list) -> dict:
        """
        Convert faster-whisper chunks to whisperX-compatible format.

        Parameters:
        - chunks (list): List of chunks from faster-whisper

        Returns:
        - dict: Dictionary in whisperX format with 'segments' and 'text'
        """
        if not chunks:
            return {'segments': [], 'text': ''}

        # Flatten all words from chunks
        all_words = []
        for chunk in chunks:
            all_words.extend(chunk.get('words', []))

        if not all_words:
            return {'segments': [], 'text': ''}

        # Create a single segment with all words (whisperX format)
        segment = {
            'start': all_words[0]['start'],
            'end': all_words[-1]['end'],
            'text': ' '.join(w['word'] for w in all_words),
            'words': all_words
        }

        return {
            'segments': [segment],
            'text': segment['text']
        }

    def _chunks_to_result_format(self, chunks: list) -> dict:
        """
        将 faster-whisper 的 chunks 转换为标准输出格式，保持原始分段。

        不同于 _faster_whisper_to_whisperx()，此方法不合并 segments。

        Args:
            chunks: List of segment dictionaries from faster-whisper

        Returns:
            Dict with 'text', 'chunks', and 'segments' keys
        """
        if not chunks:
            return {'text': '', 'chunks': [], 'segments': []}

        # 提取全文
        text = ' '.join(c['text'].strip() for c in chunks)

        # 转换为标准 chunks 格式
        output_chunks = []
        for chunk in chunks:
            output_chunk = {
                'text': chunk['text'].strip(),
                'timestamp': chunk['timestamp']
            }
            # 保留 words（如果有）
            if 'words' in chunk:
                output_chunk['words'] = chunk['words']
            # 保留 speaker（如果有）
            if 'speaker' in chunk:
                output_chunk['speaker'] = chunk['speaker']
            output_chunks.append(output_chunk)

        # 同时生成 segments 格式（向后兼容）
        segments = []
        for chunk in chunks:
            segment = {
                'start': chunk['timestamp'][0],
                'end': chunk['timestamp'][1],
                'text': chunk['text'].strip()
            }
            if 'words' in chunk:
                segment['words'] = chunk['words']
            if 'speaker' in chunk:
                segment['speaker'] = chunk['speaker']
            segments.append(segment)

        return {
            'text': text,
            'chunks': output_chunks,
            'segments': segments
        }

    def detect_language(self, filepath, audio_array) -> str:
        """
        Detects the language of the input file.
        """
        from faster_whisper import WhisperModel

        logging.info(f"Detecting language of file: {filepath.name}")

        def run_language_detection():
            device_for_detection = (
                'cpu' if self.device in ['mps', 'cpu', 'mlx'] else 'cuda'
            )
            lang_detection_model = WhisperModel(
                models.set_supported_model(
                    model=self.model_provided,
                    implementation='faster-whisper'
                    ),
                device=device_for_detection,
                compute_type=(
                    'int8'
                    if device_for_detection == 'cpu'
                    else 'float16'
                    )
                )
            lang, score, _ = lang_detection_model.detect_language(audio_array)
            return lang, score

        lang, score = help.run_with_progress(
            description=(
                f"[dark_goldenrod]→ Detecting language for "
                f"[bold]{filepath.name}"
            ),
            task=run_language_detection
        )

        self.file_language = lang

        msg = f"Detected language '{lang}' with probability {score:.2f}"
        print(f'[blue1]→ {msg}')
        logging.info(msg)

    def process_files(self, files) -> None:
        """
        Processes a list of audio files for transcription and/or diarization.

        This method logs the processing parameters, extracts filepaths from the
        input list, and initializes an empty list for storing results. Each
        file is processed based on the compute device specified ('mps',
        'cuda:0', or 'cpu'). Appropriate transcription method is chosen based
        on the device. Results, including file ids, paths, transcriptions, and
        diarizations, are stored in a dictionary and saved to a designated
        output directory. Each result is also appended to
        `self.processed_files`.

        Parameters:
        files (list of str): A list of file paths or file-like objects
        representing the audio files to be processed.
        """
        logging.info(f"Provided parameters for processing: {self.metadata}")

        # Check if dependencies for chosen device are installed
        deps_ok, deps_message = help.check_dependencies_for_device(
            device=self.device
        )
        if not deps_ok:
            raise RuntimeError(deps_message)

        # Get filepaths
        filepath_handler = FilePathProcessor(self.file_formats)
        [filepath_handler.get_filepaths(f) for f in files]
        self.filepaths = filepath_handler.filepaths

        # Process filepaths
        logging.info(f"Processing files: {self.filepaths}")

        self.processed_files = []
        for idx, filepath in enumerate(self.filepaths):

            # Create and set output_dir and output_filepath
            self.output_dir = help.set_output_dir(filepath, self.base_dir)
            output_filepath = self.output_dir / Path(filepath).stem

            # Convert file format
            filepath, audio_array = help.check_file_format(filepath=filepath)

            # Detect file language
            if not self.file_language:
                self.detect_language(filepath, audio_array)

            logging.info(f"Transcribing file: {filepath.name}")

            # Transcription and speaker annotation
            if self.device == 'mlx':
                self.model = models.set_supported_model(
                    self.model_provided,
                    implementation='mlx-whisper'
                )
                print(
                    f'[blue1]→ Using {self.device.upper()} and 🍎 MLX-Whisper '
                    f'with model "{self.model}"'
                )
                result_data = self.transcribe_with_mlx_whisper(
                    filepath, output_filepath=output_filepath
                )

            elif self.device in ['cpu', 'cuda:0']:
                # Unified path: always use faster-whisper
                self.model = models.set_supported_model(
                    self.model_provided,
                    implementation='faster-whisper'
                )
                print(
                    f'[blue1]→ Using {self.device.upper()} and '
                    f'🏃‍♀️‍➡️ Faster-Whisper with model "{self.model}"'
                )
                result_data = self.transcribe_with_faster_whisper(
                    filepath,
                    output_filepath=output_filepath
                )

            result = {
                'id': f'file_00{idx + 1}',
                'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'input_filepath': str(filepath.absolute()),
                'output_filepath': str(Path(output_filepath).absolute()),
                'written_files': None,
                'device': self.device,
                'model': self.model,
                'transcription': (
                    result_data['transcription']['transcriptions']
                    ),
            }

            # Save results
            # When annotate=True, non-speaker files (SRT, WEBVTT) are already exported
            # during transcription, so we only export speaker-annotated files here.
            result['written_files'] = output_utils.OutputWriter().save_results(
                result=result,
                export_formats=self.export_formats,
                speaker_only=self.annotate,  # Only export speaker files when annotate=True
            )

            self.processed_files.append(result)

            if not self.file_language_provided:
                self.file_language = None
