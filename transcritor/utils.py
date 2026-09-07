"""Funções auxiliares: sanitização de nomes, resolução de caminho de saída,
diretório temporário e exceções customizadas do transcritor."""

import os
import re
import shutil
import subprocess
import tempfile

CARACTERES_INVALIDOS = r'[<>:"/\\|?*\x00-\x1f]'
TAMANHO_MAXIMO_NOME = 150


class DownloadFailedError(Exception):
    """Levantada quando o yt-dlp falha ao baixar/extrair o áudio de uma URL."""


class TranscricaoFailedError(Exception):
    """Levantada quando o faster-whisper falha ao carregar o modelo ou transcrever."""


class EntradaInvalidaError(Exception):
    """Levantada quando a entrada não é nem uma URL http(s) válida nem um arquivo existente."""


def sanitizar_nome_arquivo(nome: str) -> str:
    """Remove caracteres inválidos em nomes de arquivo no Windows/Unix e limita o tamanho."""
    nome = (nome or "").strip()
    nome = re.sub(CARACTERES_INVALIDOS, "_", nome)
    nome = re.sub(r"\s+", " ", nome).strip(" .")
    if not nome:
        nome = "transcricao"
    return nome[:TAMANHO_MAXIMO_NOME]


def gerar_caminho_saida(nome_base: str, output_arg: str) -> str:
    """Resolve o caminho final do .txt a partir de --output.

    Se `output_arg` termina em .txt, é usado como caminho explícito (cria o
    diretório pai se necessário). Caso contrário, é tratado como diretório e
    o nome do arquivo é derivado de `nome_base`. Em caso de colisão, adiciona
    sufixo _1, _2, ... para nunca sobrescrever um arquivo existente.
    """
    if output_arg.lower().endswith(".txt"):
        diretorio_pai = os.path.dirname(os.path.abspath(output_arg))
        if diretorio_pai:
            os.makedirs(diretorio_pai, exist_ok=True)
        caminho = output_arg
    else:
        os.makedirs(output_arg, exist_ok=True)
        nome_arquivo = sanitizar_nome_arquivo(nome_base) + ".txt"
        caminho = os.path.join(output_arg, nome_arquivo)

    if not os.path.exists(caminho):
        return caminho

    raiz, ext = os.path.splitext(caminho)
    contador = 1
    while True:
        candidato = f"{raiz}_{contador}{ext}"
        if not os.path.exists(candidato):
            return candidato
        contador += 1


def criar_diretorio_temp() -> str:
    """Cria um diretório temporário único para esta execução."""
    return tempfile.mkdtemp(prefix="transcritor_")


def limpar_temp(diretorio: str, manter: bool = False) -> None:
    """Remove o diretório temporário, a menos que `manter` seja True."""
    if manter:
        print(f"Áudio mantido em: {diretorio}")
        return
    shutil.rmtree(diretorio, ignore_errors=True)


def verificar_ffmpeg_disponivel() -> bool:
    """Verifica se o executável ffmpeg está disponível no PATH."""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            check=False,
        )
        return True
    except FileNotFoundError:
        return False
