#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import subprocess
import shlex
from datetime import timedelta
from pathlib import Path
from faster_whisper import WhisperModel


def ts(seconds: float) -> str:
    if seconds is None:
        return "00:00:00,000"
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def preconvert_to_wav(src: Path) -> Path:
    """Convierte cualquier audio/video a WAV mono 16kHz con ffmpeg."""
    tmp = src.parent / (src.stem + "_fw16k.wav")
    cmd = f'ffmpeg -y -i "{src}" -ac 1 -ar 16000 "{tmp}"'
    subprocess.run(shlex.split(cmd), check=True)
    return tmp


def write_txt(segments, out_path: Path):
    out_path.write_text("\n".join(s["text"].strip() for s in segments), encoding="utf-8")


def write_srt(segments, out_path: Path):
    with out_path.open("w", encoding="utf-8") as f:
        for i, s in enumerate(segments, 1):
            f.write(f"{i}\n{ts(s['start'])} --> {ts(s['end'])}\n{s['text'].strip()}\n\n")


def write_json(segments, out_path: Path, lang: str, duration: float):
    payload = {"language": lang, "duration_sec": duration, "segments": segments}
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description="Transcribir audio/video a TXT, SRT y JSON (CPU con faster-whisper).")
    p.add_argument("input", help="Ruta del archivo (m4a, mp3, wav, mp4, etc.)")
    p.add_argument("-o", "--outdir", default=None, help="Directorio de salida (default: mismo del input)")
    p.add_argument(
        "-m", "--model",
        default="small",
        choices=["tiny", "base", "small", "medium", "large-v3"],
        help="Modelo a usar (default: small)"
    )
    p.add_argument("--language", default="es", help="Idioma (ej: es, en). Vacío para autodetección.")
    p.add_argument("--compute-type", default="int8", help="CPU: int8 recomendado (rápido y suficiente)")
    p.add_argument("--beam-size", type=int, default=1, help="Beam search size (1 = greedy, más rápido)")
    p.add_argument("--vad", action="store_true", help="VAD interno (mejor segmentación en audio ruidoso)")
    p.add_argument("--progress", type=int, default=10, help="Imprimir progreso cada N segmentos (default: 10)")
    args = p.parse_args()

    in_path = Path(args.input).expanduser().resolve()
    if not in_path.exists():
        raise SystemExit(f"No existe el archivo: {in_path}")

    outdir = Path(args.outdir).resolve() if args.outdir else in_path.parent
    outdir.mkdir(parents=True, exist_ok=True)

    # Convierte a WAV mono 16kHz siempre
    audio_path = preconvert_to_wav(in_path)

    model = WhisperModel(args.model, device="cpu", compute_type=args.compute_type)

    segments_iter, info = model.transcribe(
        str(audio_path),
        language=None if args.language.strip() == "" else args.language,
        beam_size=args.beam_size,
        vad_filter=args.vad,
        vad_parameters=dict(min_silence_duration_ms=500) if args.vad else None,
    )

    segments = []
    for idx, seg in enumerate(segments_iter, 1):
        segments.append({
            "id": seg.id,
            "start": seg.start,
            "end": seg.end,
            "text": (seg.text or "").strip(),
            "avg_logprob": seg.avg_logprob,
            "no_speech_prob": seg.no_speech_prob,
            "temperature": seg.temperature,
            "compression_ratio": seg.compression_ratio,
        })
        if idx % args.progress == 0:
            print(f"[INFO] Segmentos procesados: {idx}, tiempo actual: {ts(seg.end)}")

    stem = in_path.stem
    txt_path  = outdir / (stem + ".txt")
    srt_path  = outdir / (stem + ".srt")
    json_path = outdir / (stem + ".json")

    write_txt(segments, txt_path)
    write_srt(segments, srt_path)
    write_json(segments, json_path, lang=info.language, duration=info.duration)

    print(f"✅ Listo. Idioma: {info.language}  Duración: {info.duration:.1f}s")
    print(f"TXT : {txt_path}")
    print(f"SRT : {srt_path}")
    print(f"JSON: {json_path}")


if __name__ == "__main__":
    main()
