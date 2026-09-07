"""Download de áudio de qualquer site suportado pelo yt-dlp."""

import os

import yt_dlp

from transcritor.utils import DownloadFailedError

DICA_AUTENTICACAO = (
    " Dica: se o conteúdo for privado ou exigir login, tente usar --cookies "
    "com um arquivo cookies.txt (formato Netscape)."
)
TERMOS_AUTENTICACAO = ("private", "login", "members-only", "sign in")


def baixar_audio(url: str, dest_dir: str, cookies: str | None = None) -> tuple[str, str]:
    """Baixa o áudio de `url` para `dest_dir` usando yt-dlp.

    Retorna (caminho_audio, titulo). Levanta DownloadFailedError em caso de falha.
    """
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(dest_dir, "%(id)s.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
            }
        ],
        "quiet": True,
        "noprogress": True,
        "cookiefile": cookies,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
    except (yt_dlp.utils.DownloadError, yt_dlp.utils.ExtractorError) as exc:
        mensagem = str(exc)
        dica = DICA_AUTENTICACAO if any(t in mensagem.lower() for t in TERMOS_AUTENTICACAO) else ""
        raise DownloadFailedError(f"falha ao baixar áudio: {mensagem}{dica}") from exc

    if info is None:
        raise DownloadFailedError("falha ao baixar áudio: yt-dlp não retornou informações do vídeo.")

    # info pode ser um dict "playlist" com "entries"; nesse caso pega o primeiro item.
    if "entries" in info:
        entradas = [e for e in info["entries"] if e]
        if not entradas:
            raise DownloadFailedError("falha ao baixar áudio: nenhuma entrada válida encontrada.")
        info = entradas[0]

    titulo = info.get("title") or info.get("id", "audio")

    caminho_audio = _resolver_caminho_audio(info, dest_dir)
    if not caminho_audio or not os.path.isfile(caminho_audio):
        raise DownloadFailedError(
            "falha ao baixar áudio: arquivo de áudio não foi encontrado após o download."
        )

    return caminho_audio, titulo


def _resolver_caminho_audio(info: dict, dest_dir: str) -> str | None:
    """Resolve o caminho final do áudio (pós-postprocessor) a partir do info dict do yt-dlp."""
    requested = info.get("requested_downloads")
    if requested:
        caminho = requested[0].get("filepath")
        if caminho and os.path.isfile(caminho):
            return caminho

    # Fallback: o postprocessor sempre gera .wav a partir do id do vídeo.
    video_id = info.get("id")
    if video_id:
        candidato = os.path.join(dest_dir, f"{video_id}.wav")
        if os.path.isfile(candidato):
            return candidato

    return None
