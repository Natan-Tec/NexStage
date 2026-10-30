# Como gerar o instalador do NexStage 0.4.3

Você só precisa fazer isso no computador usado para criar a release. Quem
instalar o NexStage não precisará de Python, PyInstaller ou Inno Setup.

## Jeito automático: o GitHub compila e publica

Não precisa instalar nada no computador. O arquivo `.github/workflows/release.yml`
faz tudo no Windows do próprio GitHub: roda os testes, gera o `NexStage.exe`,
cria o `NexStage-Setup.exe` e publica a release com esse nome exato.

Para publicar uma versão nova:

1. Confira se `APP_VERSION` em `server.py` e em `windows_launcher.py` está na versão
   desejada e se existe o arquivo `CHANGELOG-<versão>.md` (ele vira o texto da release).
2. Crie a tag da versão e envie para o GitHub, por exemplo:

```text
git tag v0.4.3
git push origin v0.4.3
```

   (ou, no site do GitHub: **Releases > Draft a new release**, crie a tag `v0.4.3` e publique).
3. Acompanhe em **Actions**. Em uns 5 a 10 minutos a release aparece em **Releases**
   com `NexStage-Setup.exe` anexado.

Se a tag não bater com a versão do código (por exemplo `v0.4.4` com `APP_VERSION` 0.4.3),
o fluxo para antes de compilar. Para só testar a compilação sem criar release, use
**Actions > Compilar e publicar o instalador > Run workflow**: o instalador fica em
*Artifacts*, na página da execução.

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

Crie a release com a tag `v0.4.3` e anexe o instalador usando exatamente este
nome:

```text
NexStage-Setup.exe
```

O atualizador interno procura esse nome exato na release mais recente. Não
publique as pastas `build`, `dist`, `.venv-build` ou `release` como código-fonte;
elas são resultados locais de compilação.
