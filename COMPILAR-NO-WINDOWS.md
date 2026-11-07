# Como gerar o instalador do NexStage 0.6.0

Você só precisa fazer isso no computador usado para criar a release. Quem
instalar o NexStage não precisará de Python, PyInstaller ou Inno Setup.

## Jeito automático: o GitHub compila e publica

Não precisa instalar nada no computador. O arquivo `.github/workflows/release.yml`
faz tudo nos computadores do próprio GitHub: roda os testes, gera os programas para
Windows, Linux e macOS, **testa cada um** (abre, responde e encerra) e publica a release
com estes arquivos:

- `NexStage-Setup.exe` (Windows)
- `NexStage-Linux-x64.tar.gz` (Linux 64 bits)
- `NexStage-macOS-AppleSilicon.dmg` (Macs com chip M1 ou mais novo)
- `NexStage-macOS-Intel.dmg` (Macs com processador Intel)

Para publicar uma versão nova:

1. Confira se `APP_VERSION` em `server.py` e em `windows_launcher.py` está na versão
   desejada e se existe o arquivo `CHANGELOG-<versão>.md` (ele vira o texto da release).
2. No GitHub, abra **Actions > Compilar e publicar o instalador > Run workflow**,
   marque **Publicar a release no GitHub** e clique em **Run workflow**.
   O fluxo cria sozinho a tag `v<versão>` (por exemplo `v0.6.0`) e a release.
3. Em uns 10 a 15 minutos a release aparece em **Releases** com os quatro arquivos
   anexados. Se um deles falhar, nada é publicado pela metade. Se der erro, o motivo aparece na própria execução em **Actions**.

Alternativa: enviar a tag pelo Git (`git tag v0.6.0` e `git push origin v0.6.0`) faz o
mesmo. Se a tag não bater com a versão do código, o fluxo para antes de compilar.

Rodar **sem** marcar a opção apenas testa a compilação: o instalador fica em
*Artifacts*, na página da execução, e nenhuma release é criada.

---

## Jeito manual: compilar no seu computador

## 1. Instale as duas ferramentas

1. Instale o **Python 3 de 64 bits**. Durante a instalação, marque a opção
   **Add Python to PATH**.
2. Instale o **Inno Setup 6** pelo site oficial:
   <https://jrsoftware.org/isdl.php>.

Não é necessário instalar Node.js, npm ou Docker.

## 2. Gere o arquivo

1. Extraia todo o código-fonte do NexStage para uma pasta comum.
2. Mantenha a internet conectada na primeira compilação, pois o script precisa
   baixar PyInstaller, pystray e Pillow.
3. Dê dois cliques em `build-windows.bat`.
4. Aguarde a mensagem **BUILD CONCLUIDO**.

O resultado estará em:

```text
release\NexStage-Setup.exe
```

O script executa os testes antes de compilar. Se algum teste falhar, o
instalador não é gerado.

## 3. Teste antes de publicar

1. Abra `NexStage-Setup.exe`.
2. Confirme que o atalho da Área de Trabalho abre o controlador sem terminal.
3. Confira o ícone do NexStage próximo ao relógio do Windows.
4. Feche a guia do navegador e abra o controlador novamente pelo menu da
   bandeja.
5. Importe um TXT pequeno, feche pelo menu **Encerrar NexStage** e abra outra
   vez para confirmar que os dados foram salvos.

Como o projeto ainda não usa um certificado pago de assinatura de código, o
Windows SmartScreen pode mostrar **Editor desconhecido**. Os metadados internos
continuam identificando o produto como NexStage e o autor como Natan Gabriel,
mas isso não substitui uma assinatura digital.

## 4. Publique no GitHub

Crie a release com a tag `v0.6.0` e anexe o instalador usando exatamente este
nome:

```text
NexStage-Setup.exe
```

O atualizador interno procura esse nome exato na release mais recente. Não
publique as pastas `build`, `dist`, `.venv-build` ou `release` como código-fonte;
elas são resultados locais de compilação.
