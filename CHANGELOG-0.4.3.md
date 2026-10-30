# NexStage 0.4.3

## Bíblia mais rápida de usar

- **Referência rápida:** digite `jo 3:16`, `sl 23` ou `1co 13:4-7` e aperte Enter.
  Entende abreviações, nomes sem acento e “1 co”, “i coríntios”, “primeira coríntios”.
  A tecla `/` leva direto ao campo, de qualquer lugar do controlador.
- **Versículo e intervalo:** novas caixas **Versículo** e **Até**. O capítulo continua
  inteiro na sequência, já posicionado no versículo escolhido; com “Até” a sequência
  passa a ter só o intervalo.
- **Juntar o intervalo num slide só** (opcional), com a referência “João 3:16-18”.
- **Navegação:** `←` e `→` trocam de versículo e, no fim do capítulo, seguem para o
  próximo (ou voltam ao anterior). `Shift + ←/→` e os botões **‹ Capítulo / Capítulo ›**
  trocam de capítulo, passando para o livro vizinho nas pontas.
- **Última passagem lembrada:** ao abrir a aba Bíblia, a tradução, o livro, o capítulo e
  o versículo da última vez voltam sozinhos (sem mexer no telão).
- **Trocar de tradução mantém o versículo:** o livro, o capítulo e o versículo continuam
  os mesmos; se uma Bíblia já está no ar, o telão é atualizado com a nova tradução.

Escolher um versículo pelas caixas ou pelo campo rápido só muda o que está no ar se já
houver uma passagem bíblica no telão. Uma música no ar nunca é trocada por engano.

## Instalador pelo GitHub

- Novo fluxo automático (`.github/workflows/release.yml`): ao enviar uma tag `vX.Y.Z`,
  o GitHub compila no Windows, roda os testes, gera `NexStage-Setup.exe` e publica a release.
- `build-windows.bat` continua funcionando para compilar no próprio computador.
