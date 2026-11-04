# NexStage 0.5.5

## Versículos soltos com Ctrl+clique

Na aba Bíblia, segure **Ctrl** (ou ⌘ no Mac) e clique nos versículos para marcar vários, mesmo separados. Os marcados vão juntos para a tela, com a referência agrupada (ex.: "João 3:2,4-5"), e cada novo Ctrl+clique atualiza ao vivo. Clique normal, setas, trocar capítulo ou versículo voltam ao modo comum.

## Visual desatualizado após atualizar

O navegador guardava por 1 hora o CSS/JS antigo, então logo depois de atualizar a aba YouTube aparecia sem estilo e o tema laranja não aparecia. Agora os arquivos da interface são sempre revalidados.

Para ver o tema laranja sem esperar uma atualização real: abra `http://127.0.0.1:4310/?testar-atualizacao` (ajuste a porta se for outra).

## Barra rápida da Bíblia

- "jo 3:16" agora abre **João** (e não Jó) em Bíblias sem abreviações; "jó" com acento continua sendo Jó.
- Abreviações de livros numerados funcionam também quando a Bíblia usa algarismos romanos ("1sm", "1rs" → I Samuel, I Reis).

(Inclui o tema laranja de atualização da 0.5.1 e a aba YouTube da 0.5.0.)

## Aviso de atualização em laranja

Quando existe uma versão nova, **todo o controlador** troca do azul para o laranja (nada de misturar as duas cores), o botão "Atualização disponível" aparece no topo e o ícone de Ajustes ganha um ponto pulsante. Sem atualização, o visual azul normal continua igual.

(Esta versão inclui a aba YouTube da 0.5.0.)

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
