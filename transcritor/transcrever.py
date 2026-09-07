"""Transcrição de áudio usando faster-whisper."""

from transcritor.utils import TranscricaoFailedError

MODELOS_DISPONIVEIS = [
    ("tiny", "~75 MB", "mais rápido, menos preciso"),
    ("base", "~140 MB", "bom equilíbrio (padrão)"),
    ("small", "~460 MB", "mais preciso, mais lento"),
    ("medium", "~1.5 GB", "alta precisão, lento em CPU"),
    ("large-v2", "~3 GB", "muito preciso, requer bastante recurso"),
    ("large-v3", "~3 GB", "estado da arte, mais lento"),
]


def transcrever_audio(
    caminho: str,
    model_size: str = "base",
    device: str = "cpu",
    compute_type: str = "int8",
    lang: str | None = None,
    verbose: bool = False,
) -> tuple[str, str]:
    """Transcreve o arquivo de áudio em `caminho`.

    Retorna (texto, idioma_detectado). Levanta TranscricaoFailedError em caso de falha.
    """
    try:
        from faster_whisper import WhisperModel

        modelo = WhisperModel(model_size, device=device, compute_type=compute_type)
        segments, info = modelo.transcribe(caminho, language=lang, vad_filter=True)

        partes = []
        for seg in segments:
            if verbose:
                print(f"[{seg.start:.1f}s -> {seg.end:.1f}s] {seg.text}")
            partes.append(seg.text.strip())

        texto = " ".join(partes).strip()
        idioma = info.language if info and info.language else (lang or "desconhecido")
        return texto, idioma
    except TranscricaoFailedError:
        raise
    except Exception as exc:
        raise TranscricaoFailedError(f"falha ao transcrever o áudio: {exc}") from exc
