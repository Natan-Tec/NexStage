# NexStage 0.4.4

## Fontes CMG do Windows

- Ao abrir, o NexStage procura as fontes instaladas no sistema cujo nome começa com
  **CMG** (pelo nome do arquivo e pelo nome da fonte no Windows) e importa sozinho.
- As fontes importadas à mão que têm equivalente no sistema (mesmo nome ou mesmo
  conteúdo) são apagadas. Fontes manuais **sem** equivalente no sistema são mantidas.
- Textos que já usavam uma fonte apagada passam a usar a fonte do sistema; nenhum
  estilo fica sem fonte.
- Se a fonte do sistema mudar, a cópia no NexStage é atualizada na próxima abertura.
- Em **Ajustes > Fontes** há o botão **Procurar agora** e a opção **Importar
  automaticamente ao abrir** (ligada por padrão).
- Nada é instalado ou alterado no Windows: o NexStage só lê as fontes e guarda uma cópia
  na própria pasta de dados.
