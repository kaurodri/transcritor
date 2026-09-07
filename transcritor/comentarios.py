"""Download de comentários de vídeos do YouTube via yt-dlp (sem API key)."""

import yt_dlp

from transcritor.utils import ComentariosFailedError


def baixar_comentarios_youtube(
    url: str,
    limite: int | None = None,
    ordenar: str = "top",
    incluir_respostas: bool = False,
) -> tuple[list[dict], str]:
    """Baixa os comentários de um vídeo do YouTube via yt-dlp.

    Retorna (comentarios, titulo). `comentarios` é uma lista vazia se o vídeo
    não tiver comentários (não é considerado erro). Levanta ComentariosFailedError
    em caso de falha na extração (vídeo removido, privado, etc.).
    """
    # O "total" do yt-dlp conta comentários de topo e respostas juntos, então não dá pra
    # usar `limite` diretamente ali quando respostas são incluídas (senão respostas
    # consomem a cota de comentários de topo, e vídeos populares têm milhares de
    # respostas — pedir "all" pode travar por minutos). Em vez disso pedimos ao yt-dlp
    # um teto generoso (respostas limitadas por thread) e aplicamos o limite real de
    # comentários de topo nós mesmos, em Python.
    if incluir_respostas:
        max_replies, max_replies_por_thread = "all", "20"
        total = str(max(limite, 1) * 25) if limite else "1000"
    else:
        max_replies, max_replies_por_thread = "0", "0"
        total = str(limite) if limite else "all"

    ydl_opts = {
        "skip_download": True,
        "getcomments": True,
        "quiet": True,
        "noprogress": True,
        "extractor_args": {
            "youtube": {
                "comment_sort": [ordenar],
                "max_comments": [total, "all", max_replies, max_replies_por_thread],
            }
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except (yt_dlp.utils.DownloadError, yt_dlp.utils.ExtractorError) as exc:
        raise ComentariosFailedError(f"falha ao extrair comentários: {exc}") from exc

    if info is None:
        raise ComentariosFailedError("falha ao extrair comentários: yt-dlp não retornou informações do vídeo.")

    titulo = info.get("title") or info.get("id", "comentarios")
    comentarios = info.get("comments") or []

    if not incluir_respostas:
        raizes = [c for c in comentarios if c.get("parent", "root") == "root"]
        return (raizes[:limite] if limite else raizes), titulo

    if limite:
        raizes = [c for c in comentarios if c.get("parent", "root") == "root"][:limite]
        ids_mantidos = {c.get("id") for c in raizes}
        respostas = [c for c in comentarios if c.get("parent") in ids_mantidos]
        comentarios = raizes + respostas

    return comentarios, titulo
