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
import tempfile
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
    temp_dir = Path(tempfile.mkdtemp())
    tmp = temp_dir / (src.stem + "_fw16k.wav")
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

    if src_lang == dest_lang:
        print(f"[INFO] El idioma de origen ('{src_lang}') y el de destino ('{dest_lang}') son el mismo. No se requiere traducción.")
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
    args = p.parse_args()

    in_path = Path(args.input).expanduser().resolve()
    if not in_path.exists():
        raise SystemExit(f"No existe el archivo: {in_path}")

    # Crear un subdirectorio de salida con el nombre del archivo de audio
    base_outdir = Path(args.outdir).resolve() if args.outdir else Path("/app/outputs").resolve()
    outdir = base_outdir / in_path.stem
    outdir.mkdir(parents=True, exist_ok=True)    

    temp_audio_path = None
    segments = []
    info = None

    try:
        # --- 1. Pre-conversión a WAV ---
        print(f"[INFO] Convirtiendo '{in_path.name}' a formato WAV para análisis...")
        temp_audio_path = preconvert_to_wav(in_path) # Archivo temporal
    except Exception as e:
        print(f"\n[ERROR] Falló la conversión de audio con ffmpeg: {e}", file=sys.stderr)
        sys.exit(1)

    # --- 2. Transcripción ---
    segments = []
    try:
        model = WhisperModel(args.model, device="cpu", compute_type=args.compute_type)
        segments_iter, info = model.transcribe(
            str(temp_audio_path),
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
    except Exception as e:
        print(f"\n[ERROR] Ocurrió un error durante la transcripción: {e}", file=sys.stderr)
        if temp_audio_path and temp_audio_path.exists():
            shutil.rmtree(temp_audio_path.parent, ignore_errors=True) # Limpiar el directorio temporal
        sys.exit(1)


    # --- 3. Procesamiento y guardado ---
    output_lang = info.language
    
    # Mover el archivo WAV temporal a la carpeta de salida y renombrarlo
    final_wav_path = outdir / f"{in_path.stem}_{output_lang}_fw16k.wav"
    shutil.move(str(temp_audio_path), str(final_wav_path))
    shutil.rmtree(temp_audio_path.parent) # Limpiar directorio temporal
    print(f"\n✅ Audio convertido -> {output_lang.upper()}")
    print(f"   - {final_wav_path.relative_to(base_outdir)}")

    if not segments:
        print("\n[INFO] No se detectaron segmentos de audio. No se crearán archivos de transcripción.")
        # El archivo WAV se conserva, ya que puede ser útil.
        return

    # Guardar la transcripción original
    stem = f"{in_path.stem}_{output_lang}"

    txt_path = outdir / (stem + ".txt")
    srt_path = outdir / (stem + ".srt")
    json_path = outdir / (stem + ".json")
    
    write_txt(segments, txt_path)
    write_srt(segments, srt_path)
    write_json(segments, json_path, lang=output_lang, duration=info.duration)

    print(f"\n✅ Transcrito -> {output_lang.upper()}")
    print(f"   - {txt_path.relative_to(base_outdir)}")
    print(f"   - {srt_path.relative_to(base_outdir)}")
    print(f"   - {json_path.relative_to(base_outdir)}")

    # --- 4. Si se pide, traducir y guardar archivos adicionales ---
    if args.translate_to:
        dest_lang = args.translate_to
        print(f"\n[INFO] Iniciando traducción de '{output_lang}' a '{dest_lang}'...")
        translated_segments, success = translate_segments(segments, src_lang=output_lang, dest_lang=dest_lang)
        if success:
            translated_stem = f"{in_path.stem}_{output_lang}-{dest_lang}"
            
            # Copiar el archivo WAV para que coincida con los nombres de los archivos traducidos
            translated_wav_path = outdir / f"{translated_stem}_fw16k.wav"
            shutil.copy(final_wav_path, translated_wav_path)

            write_txt(translated_segments, outdir / (translated_stem + ".txt"))
            write_srt(translated_segments, outdir / (translated_stem + ".srt"))
            write_json(translated_segments, outdir / (translated_stem + ".json"), lang=dest_lang, duration=info.duration)
            print(f"✅ Traducido a {dest_lang.upper()} (desde {output_lang.upper()})")
            print(f"   - {translated_wav_path.relative_to(base_outdir)}")
            print(f"   - {(outdir / (translated_stem + '.txt')).relative_to(base_outdir)}")
            print(f"   - {(outdir / (translated_stem + '.srt')).relative_to(base_outdir)}")
            print(f"   - {(outdir / (translated_stem + '.json')).relative_to(base_outdir)}")


if __name__ == "__main__":
    main()
