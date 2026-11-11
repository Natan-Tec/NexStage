# NexStage 0.8.1

## Prévia dos fundos em vídeo

Na aba **Fundos**, cada vídeo agora mostra um quadro dele (em vez de só o ícone de play), para reconhecer o fundo pela imagem. As miniaturas são geradas uma vez, guardadas e não pesam na reprodução.

## Vídeos do computador, em tela cheia e com áudio

- A aba **YouTube** virou **Vídeos**, com dois jeitos de adicionar: **Do computador** (escolha ou solte arquivos) e **YouTube**. Os controles são os mesmos: reproduzir/pausar, linha do tempo, ±10 s, volume, mudo e parar, tudo no controlador (o vídeo toca só na projeção, em tela cheia, com som).
- Ao adicionar, o NexStage copia o arquivo e deixa em **H.264 + AAC (até 1080p)**: se já estiver assim, usa direto; se só o contêiner for diferente (MOV…), reempacota sem perder qualidade; senão converte, com barra de progresso. Isso mantém a reprodução leve em placas simples como a GT 730.
- Formatos aceitos: MP4, MOV, MKV, WebM, AVI, WMV, MPG, TS e outros.
- A aba **Mídia** agora se chama **Fundos** (é onde ficam os fundos em vídeo/imagem e logos).

## Melhorias nas letras

- **Nova música:** botão (lápis) na aba Músicas para colar a letra, com título, artista e linhas por slide. Estrofes separadas por linha em branco; `[Refrão]`, `[Ponte]`… dão nome às seções.
- **Busca por trecho da letra:** digite qualquer parte (sem se preocupar com acentos); a linha encontrada aparece sob o título.
- **Favoritas:** estrela em cada música; as favoritas ficam no topo.
- **Linhas por slide:** agora é configurável (antes fixo em 4) em Opções das músicas, e há um botão para reorganizar a música aberta (só divide, nunca junta).
- **Atalhos de seção:** botões e teclas **1–9** para pular direto a Verso 1, Refrão, Ponte… Repetir a tecla do Refrão vai para o próximo Refrão da música.

## Cronômetro de culto (nova aba)

Hora atual em cima e, embaixo, o **tempo restante** até a hora de término ou por **duração fixa** (que começa em "Ligar contagem"). Hora, regressiva e texto auxiliar têm **fonte, cor, tamanho e posição independentes** no menu da direita. Opções: segundos e 24 h na hora, esconder a regressiva ao zerar. Mudanças feitas com o cronômetro no ar atualizam ao vivo, e as configurações ficam salvas.

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
