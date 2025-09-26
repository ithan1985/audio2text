#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import subprocess
import shutil
import shlex
from datetime import timedelta
from pathlib import Path
import sys
from faster_whisper import WhisperModel
import torch

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


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
    if not shutil.which("ffmpeg"):
        raise SystemExit(
            "[ERROR] ffmpeg no está instalado o no se encuentra en el PATH. "
            "Es necesario para la conversión de audio."
        )
    tmp = src.parent / (src.stem + "_fw16k.wav")
    cmd = f'ffmpeg -y -i "{src}" -vn -ac 1 -ar 16000 -acodec pcm_s16le "{tmp}"'
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


def translate_segments(segments, src_lang: str, dest_lang: str = "es"):
    """Traduce el texto de los segmentos a un idioma de destino usando un modelo Helsinki-NLP."""
    if not TRANSFORMERS_AVAILABLE:
        print("[ERROR] La librería 'transformers' no está instalada. No se puede traducir.", file=sys.stderr)  # fmt: skip
        print("        Instálala con: pip install torch sentencepiece 'transformers[sentencepiece]'", file=sys.stderr)
        return segments, False

    if src_lang == "es":
        print("[INFO] El idioma de origen ya es español, no se requiere traducción.")
        return segments, False

    model_name = f"Helsinki-NLP/opus-mt-{src_lang}-{dest_lang}"
    print(f"[INFO] Cargando modelo de traducción: {model_name}...")
    try:
        translator = pipeline("translation", model=model_name, device=-1)  # device=-1 for CPU
    except Exception as e:
        print(f"[ERROR] No se pudo cargar el modelo de traducción para '{src_lang}->{dest_lang}'. Razón: {e}", file=sys.stderr)
        print(f"         Asegúrate de que el modelo '{model_name}' existe en Hugging Face.", file=sys.stderr)
        return segments, False

    # Crear una copia profunda para no modificar los segmentos originales
    segments_copy = [s.copy() for s in segments]
    texts_to_translate = [s['text'] for s in segments]
    # Traducir en lotes para mayor eficiencia
    translated_texts = translator(texts_to_translate, batch_size=16)

    for seg, trans in zip(segments_copy, translated_texts):
        seg['text'] = trans['translation_text']
    return segments_copy, True


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
    p.add_argument("-l", "--language", default="es", help="Idioma (ej: es, en). Vacío para autodetección.")
    p.add_argument("--compute-type", default="int8", help="CPU: int8 recomendado (rápido y suficiente)")
    p.add_argument("--beam-size", type=int, default=1, help="Beam search size (1 = greedy, más rápido)")
    p.add_argument("--vad", action="store_true", help="VAD interno (mejor segmentación en audio ruidoso)")
    p.add_argument("--progress", type=int, default=10, help="Imprimir progreso cada N segmentos (default: 10)")
    p.add_argument("--translate-to", help="Traducir el texto a un idioma (ej: 'en' para inglés, 'es' para español). Requiere modelos de traducción.")
    p.add_argument("--cleanup", action="store_true", help="Eliminar el archivo WAV temporal después de usarlo.")
    args = p.parse_args()

    in_path = Path(args.input).expanduser().resolve()
    if not in_path.exists():
        raise SystemExit(f"No existe el archivo: {in_path}")

    # Crear un subdirectorio de salida con el nombre del archivo de audio
    base_outdir = Path(args.outdir).resolve() if args.outdir else in_path.parent
    outdir = base_outdir / in_path.stem
    outdir.mkdir(parents=True, exist_ok=True)    

    # Convierte a WAV mono 16kHz siempre
    audio_path = None
    try:
        audio_path = preconvert_to_wav(in_path)

        model = WhisperModel(args.model, device="cpu", compute_type=args.compute_type)

        segments_iter, info = model.transcribe(
            str(audio_path),
            language=None if args.language.strip() == "" else args.language,
            beam_size=args.beam_size,
            vad_filter=args.vad,
            vad_parameters=dict(min_silence_duration_ms=500) if args.vad else None,
            task="transcribe", # Siempre transcribir primero para obtener el idioma original
        )

        segments = []
        for idx, seg in enumerate(segments_iter, 1):
            segments.append({
                "id": seg.id,
                "start": seg.start,
                "end": seg.end,
                "text": (seg.text or "").strip(),
            })
            if idx % args.progress == 0:
                print(f"[INFO] Segmentos procesados: {idx}, tiempo actual: {ts(seg.end)}")

        # --- 1. Guardar la transcripción original ---
        action_text = "Transcrito"
        output_lang = info.language
        stem = f"{in_path.stem}_{output_lang}" # Ej: audio_en, audio_es, audio_de

        txt_path  = outdir / (stem + ".txt")
        srt_path  = outdir / (stem + ".srt")
        json_path = outdir / (stem + ".json")

        write_txt(segments, txt_path)
        write_srt(segments, srt_path)
        write_json(segments, json_path, lang=output_lang, duration=info.duration)

        print(f"\n✅ {action_text} -> {output_lang.upper()}")
        print(f"   - {txt_path.name}")

        # --- 2. Si se pide, traducir y guardar archivos adicionales ---
        if args.translate_to:
            dest_lang = args.translate_to
            print(f"\n[INFO] Iniciando traducción de '{info.language}' a '{dest_lang}'...")
            translated_segments, success = translate_segments(segments, src_lang=info.language, dest_lang=dest_lang)
            if success:
                translated_stem = f"{in_path.stem}_{info.language}-{dest_lang}" # Ej: audio_en-es.txt
                write_txt(translated_segments, outdir / (translated_stem + ".txt"))
                write_srt(translated_segments, outdir / (translated_stem + ".srt"))
                write_json(translated_segments, outdir / (translated_stem + ".json"), lang=dest_lang, duration=info.duration)
                print(f"✅ Traducido a {dest_lang.upper()} (desde {info.language.upper()})")
                print(f"   - {translated_stem}.txt")

    finally:
        if audio_path and audio_path.exists() and args.cleanup:
            print(f"[INFO] Limpiando archivo temporal: {audio_path.name}")
            audio_path.unlink()


if __name__ == "__main__":
    main()
