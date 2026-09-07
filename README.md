# transcritor

CLI em Python para baixar vídeos de qualquer site suportado pelo [yt-dlp](https://github.com/yt-dlp/yt-dlp)
(ou usar um arquivo de áudio já existente) e transcrever com
[faster-whisper](https://github.com/SYSTRAN/faster-whisper), salvando o resultado em um arquivo `.txt`.

## Requisitos

- Python 3.10+
- FFmpeg instalado e disponível no `PATH` (necessário para o yt-dlp extrair áudio e para o
  faster-whisper decodificar arquivos que não sejam WAV puro).
  - Windows: `choco install ffmpeg` ou baixe em https://ffmpeg.org e adicione ao PATH.

## Instalação

```bash
python -m venv .venv
source .venv/Scripts/activate   # Git Bash no Windows
pip install -r requirements.txt
```

## Uso

```bash
# A partir de um link (qualquer site suportado pelo yt-dlp)
python transcritor.py transcrever "https://www.youtube.com/watch?v=xxxx"

# Escolhendo modelo e idioma
python transcritor.py transcrever "<url>" --modelo small --idioma pt -o ./minhas_transcricoes

# A partir de um arquivo de áudio local (pula o download)
python transcritor.py transcrever ./audios/entrevista.mp3

# Sites que exigem sessão/login (ex: conteúdo privado)
python transcritor.py transcrever "<url>" --cookies cookies.txt

# Mantendo o áudio baixado (não apaga o temporário)
python transcritor.py transcrever "<url>" --manter-audio

# Listar modelos disponíveis
python transcritor.py modelos
```

Por padrão a transcrição é salva em `./output/<título>.txt`. Se o arquivo já existir, um
sufixo `_1`, `_2`, ... é adicionado automaticamente para não sobrescrever.

## Observações

- O primeiro uso de cada tamanho de modelo (`--modelo`) baixa os pesos do Hugging Face Hub —
  é necessária conexão com a internet na primeira vez; depois fica em cache local.
- `cookies.txt` deve estar no formato Netscape (ex: exportado com a extensão de navegador
  "Get cookies.txt LOCALLY").
- Em GPU, use `--dispositivo cuda --tipo-computo float16`.
