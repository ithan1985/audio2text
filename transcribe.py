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
    from ctranslate2 import Translator as CT2Translator
    from huggingface_hub import snapshot_download
    import sentencepiece as spm
    NLLB_AVAILABLE = True
except ImportError:
    NLLB_AVAILABLE = False


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


# Mapeo de códigos ISO 639-1 a códigos NLLB (flores_200)
_NLLB_CODES = {
    "en": "eng_Latn",
    "es": "spa_Latn",
    "fr": "fra_Latn",
    "de": "deu_Latn",
    "it": "ita_Latn",
    "pt": "por_Latn",
    "zh": "zho_Hans",
    "ja": "jpn_Jpan",
    "ko": "kor_Hang",
    "ru": "rus_Cyrl",
    "ar": "arb_Arab",
}

_NLLB_MODEL = "facebook/nllb-200-distilled-600M"
_nllb_translator = None
_nllb_sp = None


def _load_nllb():
    global _nllb_translator, _nllb_sp
    if _nllb_translator is not None:
        return
    print(f"[INFO] Cargando modelo NLLB (primera vez descarga ~600 MB)...")
    model_path = snapshot_download(_NLLB_MODEL)
    _nllb_translator = CT2Translator(model_path, device="cpu", inter_threads=2)
    sp_model = Path(model_path) / "sentencepiece.bpe.model"
    _nllb_sp = spm.SentencePieceProcessor()
    _nllb_sp.Load(str(sp_model))


def _nllb_translate(text: str, src_nllb: str, tgt_nllb: str) -> str:
    tokens = _nllb_sp.Encode(text, out_type=str)
    tokens = [src_nllb] + tokens
    result = _nllb_translator.translate_batch(
        [tokens],
        target_prefix=[[tgt_nllb]],
        max_decoding_length=512,
        beam_size=4,
    )
    out_tokens = result[0].hypotheses[0][1:]  # quitar el token de idioma
    return _nllb_sp.Decode(out_tokens)


def translate_segments(segments, src_lang: str, dest_lang: str = "es"):
    """Traduce segmentos usando NLLB-200 vía ctranslate2 (sin torch)."""
    if not NLLB_AVAILABLE:
        print("[ERROR] Faltan dependencias para NLLB. Instala con:", file=sys.stderr)
        print("        pip install huggingface_hub sentencepiece", file=sys.stderr)
        print("        (ctranslate2 ya viene con faster-whisper)", file=sys.stderr)
        return segments, False

    if src_lang == dest_lang:
        print(f"[INFO] Idioma origen ('{src_lang}') == destino ('{dest_lang}'). Sin traducción.")
        return segments, False

    src_nllb = _NLLB_CODES.get(src_lang)
    tgt_nllb = _NLLB_CODES.get(dest_lang)
    if not src_nllb or not tgt_nllb:
        print(f"[ERROR] Código de idioma no soportado: '{src_lang}' o '{dest_lang}'.", file=sys.stderr)
        print(f"        Idiomas soportados: {', '.join(_NLLB_CODES.keys())}", file=sys.stderr)
        return segments, False

    try:
        _load_nllb()
    except Exception as e:
        print(f"[ERROR] No se pudo cargar el modelo NLLB: {e}", file=sys.stderr)
        return segments, False

    segments_copy = [s.copy() for s in segments]
    for seg in segments_copy:
        seg['text'] = _nllb_translate(seg['text'], src_nllb, tgt_nllb)
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
    p.add_argument("--start", type=float, default=0.0, help="Segundo de inicio del recorte (default: 0)")
    p.add_argument("--duration", type=float, default=None, help="Duración en segundos a procesar (default: todo el archivo)")
    args = p.parse_args()

    in_path = Path(args.input).expanduser().resolve()
    if not in_path.exists():
        raise SystemExit(f"No existe el archivo: {in_path}")

    # Crear un subdirectorio de salida con el nombre del archivo de audio
    base_outdir = Path(args.outdir).resolve() if args.outdir else Path("/app/outputs").resolve()
    outdir = base_outdir / in_path.stem
    outdir.mkdir(parents=True, exist_ok=True)    

    temp_audio_path = None
    info = None

    try:
        # --- 1. Pre-conversión a WAV ---
        recorte = f" (desde {args.start}s, duración {args.duration}s)" if args.duration else ""
        print(f"[INFO] Convirtiendo '{in_path.name}' a formato WAV{recorte}...")
        temp_audio_path = preconvert_to_wav(in_path, start=args.start, duration=args.duration)
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

    shutil.rmtree(temp_audio_path.parent, ignore_errors=True)
    print(f"\n✅ Audio procesado -> idioma detectado: {output_lang.upper()}")

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
            
            write_txt(translated_segments, outdir / (translated_stem + ".txt"))
            write_srt(translated_segments, outdir / (translated_stem + ".srt"))
            write_json(translated_segments, outdir / (translated_stem + ".json"), lang=dest_lang, duration=info.duration)
            print(f"✅ Traducido a {dest_lang.upper()} (desde {output_lang.upper()})")
            print(f"   - {(outdir / (translated_stem + '.txt')).relative_to(base_outdir)}")
            print(f"   - {(outdir / (translated_stem + '.srt')).relative_to(base_outdir)}")
            print(f"   - {(outdir / (translated_stem + '.json')).relative_to(base_outdir)}")


if __name__ == "__main__":
    main()
