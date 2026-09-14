# NexStage 0.4.2

## Correção de build no Windows

- Conexões SQLite do Louvor JA e dos testes são fechadas explicitamente;
  arquivos temporários não ficam bloqueados durante os testes no Windows.
- O script de build encontra o Inno Setup 6 instalado apenas para o usuário,
  em `%LOCALAPPDATA%\Programs\Inno Setup 6`.

## Aplicativo instalado no Windows

- Executável sem janela preta de terminal.
- Ícone na bandeja com atalhos para controlador, telão, OBS e dados.
- Instância única: abrir novamente apenas traz o controlador de volta.
- Fechar a guia do navegador não encerra o NexStage.
- Encerramento explícito pelo menu da bandeja.
- Ícone oficial no executável, nos atalhos, na interface e no favicon.

## Instalador e dados

- Instalador tradicional `NexStage-Setup.exe` para `C:\NexStage`.
- Atalhos na Área de Trabalho, menu Iniciar e Documentos.
- Desinstalador dentro da pasta do NexStage.
- Atualizações e desinstalações preservam músicas, Bíblias, fontes, mídias,
  logos e configurações.
- Metadados do Windows com produto **NexStage** e autor **Natan Gabriel**.

## Atualizações

- Nova área **Sobre e atualizações** nos Ajustes.
- Exibe versão, sistema, URLs do controlador/OBS e pasta dos dados.
- Consulta opcional à release mais recente no GitHub.
- Download iniciado somente após confirmação do usuário.
- O funcionamento offline da apresentação permanece inalterado.

## Código-fonte

- `build-windows.bat` reproduz os testes, o executável e o instalador no Windows.
- O pacote compilado não inclui o ambiente nem os scripts de compilação.
- macOS e Linux continuam disponíveis pelo modo Python, sem novo empacotamento.
