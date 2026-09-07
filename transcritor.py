#!/usr/bin/env python
"""transcritor — CLI para baixar vídeos (via yt-dlp) ou usar áudio local e
transcrever com faster-whisper, salvando o resultado em .txt.

Exemplos:
    python transcritor.py transcrever https://www.youtube.com/watch?v=xxxx
    python transcritor.py transcrever https://vm.tiktok.com/xxxx -o ./output --modelo small --idioma pt
    python transcritor.py transcrever ./audios/entrevista.mp3 --manter-audio
    python transcritor.py transcrever <url> --cookies cookies.txt
    python transcritor.py modelos
"""

import argparse
import os
import sys
from urllib.parse import urlparse

from transcritor.download import baixar_audio
from transcritor.transcrever import MODELOS_DISPONIVEIS, transcrever_audio
from transcritor.utils import (
    DownloadFailedError,
    EntradaInvalidaError,
    TranscricaoFailedError,
    criar_diretorio_temp,
    gerar_caminho_saida,
    limpar_temp,
    verificar_ffmpeg_disponivel,
)


def eh_url(entrada: str) -> bool:
    return urlparse(entrada).scheme in ("http", "https")


def cmd_transcrever(args: argparse.Namespace) -> None:
    entrada = args.entrada
    origem_url = eh_url(entrada)

    if origem_url:
        caminho_audio_entrada = None
    elif os.path.isfile(entrada):
        caminho_audio_entrada = os.path.abspath(entrada)
    else:
        raise EntradaInvalidaError(
            "entrada inválida — não é uma URL HTTP(S) válida nem um arquivo existente."
        )

    diretorio_temp = None
    try:
        if origem_url:
            if not verificar_ffmpeg_disponivel():
                raise DownloadFailedError(
                    "FFmpeg não encontrado no PATH. Instale o FFmpeg e adicione ao PATH."
                )
            diretorio_temp = criar_diretorio_temp()
            caminho_audio, titulo = baixar_audio(entrada, diretorio_temp, cookies=args.cookies)
        else:
            caminho_audio = caminho_audio_entrada
            titulo = os.path.splitext(os.path.basename(caminho_audio))[0]

        texto, idioma = transcrever_audio(
            caminho_audio,
            model_size=args.model,
            device=args.device,
            compute_type=args.compute_type,
            lang=args.lang,
            verbose=args.verbose,
        )

        caminho_saida = gerar_caminho_saida(titulo, args.output)
        with open(caminho_saida, "w", encoding="utf-8") as f:
            f.write(f"Idioma detectado: {idioma}\n\n")
            f.write(texto)
            f.write("\n")

        print(f"Transcrição salva em: {caminho_saida}")
    finally:
        if diretorio_temp:
            limpar_temp(diretorio_temp, manter=args.keep_audio)


def cmd_modelos(args: argparse.Namespace) -> None:
    print("Modelos disponíveis (faster-whisper):\n")
    for nome, tamanho, descricao in MODELOS_DISPONIVEIS:
        print(f"  {nome:<10} {tamanho:<10} {descricao}")
    print(
        "\nObs: o primeiro uso de cada modelo baixa os pesos do Hugging Face Hub "
        "(é necessária conexão com a internet na primeira vez)."
    )


def montar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Baixa vídeos (via yt-dlp) ou usa áudio local e transcreve com faster-whisper.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="comando", required=True)

    p_transcrever = subparsers.add_parser(
        "transcrever", help="Baixa (se URL) ou usa arquivo local e transcreve para .txt."
    )
    p_transcrever.add_argument(
        "entrada", help="URL do vídeo (qualquer site suportado pelo yt-dlp) ou caminho de arquivo de áudio local."
    )
    p_transcrever.add_argument(
        "-o", "--saida", dest="output", default="./output",
        help="Diretório de saída ou caminho de arquivo .txt (padrão: ./output).",
    )
    p_transcrever.add_argument(
        "-m", "--modelo", dest="model", default="base",
        choices=["tiny", "base", "small", "medium", "large-v2", "large-v3"],
        help="Tamanho do modelo faster-whisper (padrão: base).",
    )
    p_transcrever.add_argument(
        "--idioma", dest="lang", default=None,
        help="Força o idioma da transcrição (ex: pt, en). Padrão: detecção automática.",
    )
    p_transcrever.add_argument(
        "--dispositivo", dest="device", default="cpu", choices=["cpu", "cuda", "auto"],
        help="Dispositivo de inferência (padrão: cpu).",
    )
    p_transcrever.add_argument(
        "--tipo-computo", dest="compute_type", default="int8",
        help="Compute type do CTranslate2 (padrão: int8 para CPU; use float16 em GPU).",
    )
    p_transcrever.add_argument(
        "--cookies", dest="cookies", default=None,
        help="Caminho de um cookies.txt (formato Netscape) para sites que exigem sessão.",
    )
    p_transcrever.add_argument(
        "--manter-audio", dest="keep_audio", action="store_true",
        help="Não apaga o áudio baixado após a transcrição (ignorado para entrada de arquivo local).",
    )
    p_transcrever.add_argument(
        "-v", "--verbose", dest="verbose", action="store_true",
        help="Mostra o progresso da transcrição segmento a segmento.",
    )
    p_transcrever.set_defaults(func=cmd_transcrever)

    p_modelos = subparsers.add_parser("modelos", help="Lista os tamanhos de modelo disponíveis.")
    p_modelos.set_defaults(func=cmd_modelos)

    return parser


def main() -> None:
    # Evita UnicodeEncodeError ao imprimir títulos/textos com emoji ou acentos
    # em consoles Windows que usam codepage legada (cp1252) em vez de UTF-8.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = montar_parser()
    args = parser.parse_args()

    try:
        args.func(args)
    except EntradaInvalidaError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        sys.exit(1)
    except DownloadFailedError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        sys.exit(1)
    except TranscricaoFailedError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        sys.exit(1)
    except (OSError, PermissionError) as exc:
        print(f"Erro de arquivo: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"Erro inesperado: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
