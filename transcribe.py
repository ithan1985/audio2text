#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import subprocess
import shutil
import shlex
from pathlib import Path
import sys
import tempfile
from faster_whisper import WhisperModel

try:
    from transformers import MarianMTModel, MarianTokenizer
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


def preconvert_to_wav(src: Path, start: float = 0.0, duration: float = None) -> Path:
    """Convierte cualquier audio/video a WAV mono 16kHz con ffmpeg."""
    if not shutil.which("ffmpeg"):
        raise SystemExit(
            "[ERROR] ffmpeg no está instalado o no se encuentra en el PATH. "
            "Es necesario para la conversión de audio."
        )
    temp_dir = Path(tempfile.mkdtemp())
    tmp = temp_dir / (src.stem + "_fw16k.wav")
    seek = f"-ss {start} " if start > 0 else ""
    trim = f"-t {duration} " if duration is not None else ""
    cmd = f'ffmpeg -y -loglevel error {seek}-i "{src}" {trim}-vn -ac 1 -ar 16000 -acodec pcm_s16le "{tmp}"'
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
    """Traduce el texto de los segmentos usando Helsinki-NLP/opus-mt."""
    if not TRANSFORMERS_AVAILABLE:
        print("[ERROR] La librería 'transformers' no está instalada. No se puede traducir.", file=sys.stderr)
        print("        Instálala con: pip install sentencepiece 'transformers[sentencepiece]'", file=sys.stderr)
        return segments, False

    if src_lang == dest_lang:
        print(f"[INFO] Idioma origen ('{src_lang}') == destino ('{dest_lang}'). Sin traducción.")
        return segments, False

    model_name = f"Helsinki-NLP/opus-mt-{src_lang}-{dest_lang}"
    print(f"[INFO] Cargando modelo de traducción: {model_name}...")
    try:
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        model = MarianMTModel.from_pretrained(model_name)
    except Exception as e:
        print(f"[ERROR] No se pudo cargar el modelo '{model_name}': {e}", file=sys.stderr)
        print(f"        Verifica que el par de idiomas '{src_lang}->{dest_lang}' exista en Hugging Face.", file=sys.stderr)
        return segments, False

    segments_copy = [s.copy() for s in segments]
    texts = [s['text'] for s in segments]

    batch_size = 16
    translated_texts = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        inputs = tokenizer(batch, return_tensors="pt", padding=True, truncation=True, max_length=512)
        outputs = model.generate(**inputs)
        translated_texts.extend(tokenizer.batch_decode(outputs, skip_special_tokens=True))

    for seg, translated in zip(segments_copy, translated_texts):
        seg['text'] = translated
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
    p.add_argument("--cpu-threads", type=int, default=2, help="Hilos de CPU para el modelo (default: 2)")
    p.add_argument("--num-workers", type=int, default=2, help="Workers paralelos para transcripción (default: 2)")
    p.add_argument("--translate-to", help="Traducir el texto a un idioma (ej: 'en' para inglés, 'es' para español).")
    p.add_argument("--start", type=float, default=0.0, help="Segundo de inicio del recorte (default: 0)")
    p.add_argument("--duration", type=float, default=None, help="Duración en segundos a procesar (default: todo el archivo)")
    args = p.parse_args()

    in_path = Path(args.input).expanduser().resolve()
    if not in_path.exists():
        raise SystemExit(f"No existe el archivo: {in_path}")

    base_outdir = Path(args.outdir).resolve() if args.outdir else Path("/app/outputs").resolve()
    outdir = base_outdir / in_path.stem
    outdir.mkdir(parents=True, exist_ok=True)

    temp_audio_path = None
    info = None

    try:
        recorte = f" (desde {args.start}s, duración {args.duration}s)" if args.duration else ""
        print(f"[INFO] Convirtiendo '{in_path.name}' a formato WAV{recorte}...")
        temp_audio_path = preconvert_to_wav(in_path, start=args.start, duration=args.duration)
    except Exception as e:
        print(f"\n[ERROR] Falló la conversión de audio con ffmpeg: {e}", file=sys.stderr)
        sys.exit(1)

    segments = []
    try:
        model = WhisperModel(args.model, device="cpu", compute_type=args.compute_type, cpu_threads=args.cpu_threads, num_workers=args.num_workers)
        segments_iter, info = model.transcribe(
            str(temp_audio_path),
            language=None if args.language.strip() == "" else args.language,
            beam_size=args.beam_size,
            vad_filter=args.vad,
            vad_parameters=dict(min_silence_duration_ms=500) if args.vad else None,
            task="transcribe",
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
            shutil.rmtree(temp_audio_path.parent, ignore_errors=True)
        sys.exit(1)

    output_lang = info.language
    shutil.rmtree(temp_audio_path.parent, ignore_errors=True)
    print(f"\n✅ Audio procesado -> idioma detectado: {output_lang.upper()}")

    if not segments:
        print("\n[INFO] No se detectaron segmentos de audio. No se crearán archivos de transcripción.")
        return

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

    if args.translate_to:
        dest_lang = args.translate_to
        print(f"\n[INFO] Iniciando traducción de '{output_lang}' a '{dest_lang}'...")
        translated_segments, success = translate_segments(segments, src_lang=output_lang, dest_lang=dest_lang)
        if success:
            translated_stem = f"{in_path.stem}_{output_lang}-{dest_lang}"

            write_txt(translated_segments, outdir / (translated_stem + ".txt"))
            write_srt(translated_segments, outdir / (translated_stem + ".srt"))
            write_json(translated_segments, outdir / (translated_stem + ".json"), lang=dest_lang, duration=info.duration)
            print(f"✅ Traducido a {dest_lang.upper()} (desde {output_lang.upper()})")
            print(f"   - {(outdir / (translated_stem + '.txt')).relative_to(base_outdir)}")
            print(f"   - {(outdir / (translated_stem + '.srt')).relative_to(base_outdir)}")
            print(f"   - {(outdir / (translated_stem + '.json')).relative_to(base_outdir)}")


if __name__ == "__main__":
    main()
