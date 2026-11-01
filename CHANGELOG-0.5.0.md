# NexStage 0.5.0

## Vídeos do YouTube

Nova aba **YouTube** no controlador. Cole o link do vídeo (ou só o código de 11 letras que
aparece na URL) e use o NexStage como controle remoto: o vídeo toca **só na projeção**, e o
operador não renderiza nada na própria tela.

- **Sempre H.264 + AAC**, no máximo 1080p e de preferência 30 fps, para rodar leve em placas
  simples como a GT 730. Só se o vídeo não tiver nenhuma versão H.264 ele é convertido.
- **Download em segundo plano ao adicionar** (720p por padrão, configurável). Se o operador
  projetar antes de terminar, o vídeo passa em **transmissão direta** (cópia do fluxo, sem
  re-codificar) e troca sozinho para o arquivo local assim que o download acaba.
- Controles no controlador: Reproduzir/Pausar, linha do tempo, ±10 s, volume, mudo,
  resolução (troca sem perder a posição) e parar. Atalhos: Espaço, ←/→ (5 s, Shift 30 s),
  ↑/↓ volume, M mudo.
- Vídeos já baixados funcionam sem internet.
- Na saída OBS o vídeo toca sem som, a menos que a URL tenha `?audio=1`.
- Na primeira vez o NexStage baixa o yt-dlp e um runtime JavaScript (cerca de 60 MB). O ffmpeg
  já vai dentro do instalador.

Aviso: usar o yt-dlp pode conflitar com os termos de uso do YouTube. Use por sua conta.

## Correções internas

- Instaladores incluem o ffmpeg (imageio-ffmpeg).
