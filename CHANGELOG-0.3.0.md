# NexStage 0.3.0 — recursos entregues

## Conteúdo e integrações

- Catálogo Louvor JA local e offline, usando `database.db` em modo somente leitura.
- Detecção do caminho padrão do Louvor JA e configuração de caminho alternativo.
- Busca por título e álbum sem diferenciar acentos ou maiúsculas.
- Importação somente de metadados e letra, preservando a ordem dos slides.
- Identificação de músicas já importadas e prevenção de duplicatas.
- Edição persistente de título, artista, álbum e conteúdo dos slides.
- Divisão no cursor, duplicação e exclusão de slides.

## Aparência

- Estilos separados para música, Bíblia e relógio.
- Elementos independentes: letra/rótulo/créditos, versículo/versão/referência e hora/texto/data.
- Fonte, peso, tamanho, cor, alinhamento, X/Y, largura, altura de linha, espaçamento, sombra, itálico, maiúsculas, contorno e fundo.
- Arraste direto dos elementos na prévia grande e restauração individual ao padrão.
- Referência bíblica completa ou compacta e versão opcional.
- Relógio 12/24 horas, segundos, data opcional, três formatos e texto auxiliar.
- Rótulos e créditos opcionais nas músicas.

## Sistema

- Importação de fontes TTF, OTF, WOFF e WOFF2 para uso local no NexStage e no OBS.
- Detecção de monitores e abertura do telão no monitor preferido quando o navegador suporta a API.
- Cor, escala e densidade da interface.
- Confirmações opcionais para exclusão e limpeza da saída.
- Crossfade configurável e controle/cache do frame congelado das previews.
- Favicon igual à marca da interface no controlador, telão e OBS.
- Migração automática das configurações visuais da versão 0.2.0.

## Validação

- 15 testes automatizados aprovados.
- Teste HTTP das páginas e APIs principais aprovado.
- Teste do Louvor JA confirma que o `database.db` permanece idêntico após busca e importação.
