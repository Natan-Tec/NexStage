# NexStage 0.4.5

## Agora também para Linux e macOS

- **macOS:** `NexStage-macOS-AppleSilicon.dmg` (chip M1 ou mais novo) e
  `NexStage-macOS-Intel.dmg`. Arraste para Aplicativos. O NexStage fica no ícone da
  barra de menus, sem janela de terminal.
- **Linux (64 bits):** `NexStage-Linux-x64.tar.gz`. Extraia e rode `sh instalar.sh`
  para criar o atalho no menu de aplicativos, ou execute `./NexStage` direto.
- Sem janela de terminal, uma instância por vez (abrir de novo só reabre o controlador)
  e menu com controlador, telão, endereço do OBS, pasta dos dados e **Encerrar**.
- Sem ícone de bandeja no ambiente, o NexStage segue funcionando em segundo plano e
  pode ser encerrado com `NexStage --stop`.
- Os dados ficam fora da pasta do programa (`~/Library/Application Support/NexStage` no
  macOS e `~/.local/share/NexStage` no Linux), então atualizar não apaga nada.
- As fontes cujo nome começa com **CMG** também são importadas do sistema nesses sistemas.
- No macOS o app ainda não tem assinatura paga da Apple: na primeira vez, clique com o
  botão direito > **Abrir** (detalhes no README).

## Release

- Uma única release com os quatro arquivos; cada programa é aberto e testado antes de
  publicar, e nada é publicado se algum deles falhar.
- O atualizador interno continua só para o Windows (procura `NexStage-Setup.exe`).
