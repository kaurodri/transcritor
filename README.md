# transcritor

CLI em Python para baixar vídeos de qualquer site suportado pelo [yt-dlp](https://github.com/yt-dlp/yt-dlp)
(ou usar um arquivo de áudio já existente) e transcrever com
[faster-whisper](https://github.com/SYSTRAN/faster-whisper), salvando o resultado em um arquivo `.txt`.
Também baixa os comentários de vídeos do YouTube para `.txt`.

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

# Baixar comentários de um vídeo do YouTube
python transcritor.py comentarios "https://www.youtube.com/watch?v=xxxx"

# Limitando quantidade, ordenando por mais recentes e incluindo respostas
python transcritor.py comentarios "https://www.youtube.com/watch?v=xxxx" --limite 50 --ordenar new --respostas
```

Por padrão a transcrição/comentários são salvos em `./output/<título>.txt`. Se o arquivo já
existir, um sufixo `_1`, `_2`, ... é adicionado automaticamente para não sobrescrever.

### Comentários

- Funciona apenas para **YouTube** — via `yt-dlp`, sem precisar de API key nem depender de
  nenhuma lib extra.
- Comentários do **TikTok não são suportados**: o yt-dlp não implementa extração de
  comentários para TikTok, e as alternativas disponíveis (`pyktok`, `TikTokApi`) exigem
  Playwright e um token de sessão de navegador (`ms_token`) frágil, que expira e quebra com
  frequência — não é algo que dá pra prometer como confiável numa CLI.
- Por padrão só baixa comentários de topo (mais rápido); use `--respostas` para incluir
  também as respostas de cada comentário, indentadas com `↳`.

## Observações

- O primeiro uso de cada tamanho de modelo (`--modelo`) baixa os pesos do Hugging Face Hub —
  é necessária conexão com a internet na primeira vez; depois fica em cache local.
- `cookies.txt` deve estar no formato Netscape (ex: exportado com a extensão de navegador
  "Get cookies.txt LOCALLY").
- Em GPU, use `--dispositivo cuda --tipo-computo float16`.
