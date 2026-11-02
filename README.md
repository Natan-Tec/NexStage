# NexStage 0.5.1

Apresentador local para igrejas, criado para letras, Bíblia em XML ou Louvor JA, vídeos de
fundo e integração simples com OBS. A interface é HTML/CSS/JavaScript, mas o
aplicativo roda por um servidor Python local e não precisa de Node.js, Docker,
npm, servidor de banco de dados ou internet para apresentar.

> O nome **NexStage** é provisório e pode ser trocado depois sem alterar a base
> técnica.

## Vídeos do YouTube

Na aba **YouTube**, cole um link (ou o código de 11 letras do vídeo). O NexStage baixa o
vídeo em H.264 em segundo plano e, se você projetar antes de acabar, transmite direto e troca
para o arquivo local depois. O vídeo toca só na projeção; o controlador mostra apenas os
botões (play, linha do tempo, volume, resolução). Os componentes yt-dlp e deno são baixados
na primeira vez; o ffmpeg vai dentro do instalador. Detalhes em `CHANGELOG-0.5.1.md`.

## Instalar e abrir

### Windows

Para o público, baixe `NexStage-Setup.exe` na página de releases, abra-o e siga o
assistente. O Windows pode pedir permissão de administrador porque o aplicativo
é instalado em `C:\NexStage`.

O instalador cria atalhos na Área de Trabalho, no menu Iniciar e em Documentos.
O NexStage abre sem terminal preto e permanece no ícone da bandeja do Windows.
Fechar a guia do navegador não encerra o aplicativo. Para encerrar de verdade,
clique com o botão direito no ícone da bandeja e escolha **Encerrar NexStage**.

O menu da bandeja também permite abrir o controlador, abrir o telão, copiar o
endereço do OBS e abrir a pasta dos dados. Se o NexStage já estiver executando,
um segundo clique no atalho apenas reabre o controlador atual.

### macOS

Baixe o arquivo `.dmg` na página de releases: **NexStage-macOS-AppleSilicon.dmg**
para Macs com chip M1/M2/M3/M4 ou **NexStage-macOS-Intel.dmg** para Macs com
processador Intel. Arraste o NexStage para a pasta Aplicativos.

Na primeira vez, clique com o botão direito no NexStage e escolha **Abrir**, pois o
app ainda não tem assinatura paga da Apple. Se o macOS disser que o app está
danificado, rode uma única vez no Terminal:

```bash
xattr -dr com.apple.quarantine /Applications/NexStage.app
```

O NexStage abre sem terminal e fica no ícone da barra de menus, com as mesmas opções
do Windows (controlador, telão, endereço do OBS, pasta dos dados e **Encerrar**).
Os dados ficam em `~/Library/Application Support/NexStage`.

### Linux

Baixe `NexStage-Linux-x64.tar.gz` na página de releases, extraia e, dentro da pasta
`NexStage`, rode `sh instalar.sh`. Ele instala na sua conta (sem sudo) e cria o
atalho no menu de aplicativos. Também dá para rodar `./NexStage` direto da pasta.

Sem terminal: o NexStage fica no ícone da bandeja quando o ambiente tem bandeja. Se
não tiver, ele continua em segundo plano; encerre com `nexstage --stop`. Os dados
ficam em `~/.local/share/NexStage`.

### Executar pelo código-fonte (qualquer sistema)

Em macOS e Linux, com Python 3 instalado, dá para rodar sem compilar:

```bash
chmod +x start.sh
./start.sh        # ou: python3 run.py   (no macOS: start.command)
```

Por padrão o controlador abre em `http://127.0.0.1:4310`.

### Executar diretamente pelo código-fonte (Windows)

No Windows, o desenvolvedor também pode usar `start.bat`, desde que tenha Python
3. Esse modo serve para desenvolvimento; a distribuição normal deve usar o
instalador compilado.

## Atualizar versões anteriores

Ao instalar uma nova versão por cima da 0.4.2 ou posterior, o instalador substitui
somente os arquivos do aplicativo. As pastas `data` e `media` são preservadas.

Para migrar de um ZIP antigo, feche o NexStage, instale a versão nova e copie as
pastas `data` e `media` da instalação anterior para `C:\NexStage`. Isso preserva
músicas, Bíblias, configurações, vídeos, imagens, logos e fontes.

Em **Ajustes › Sobre e atualizações**, o NexStage instalado pode consultar a
release mais recente no GitHub. O download nunca é obrigatório: o instalador só
é baixado e aberto depois da confirmação do usuário. Sem internet, a apresentação
local continua funcionando normalmente.

## Fluxo mais rápido

1. Em **Músicas**, importe um `.txt`. Linhas em branco separam os slides e
   cabeçalhos como `[Verso 1]`, `[Refrão]` e `[Ponte]` viram rótulos.
2. Em **Mídia**, importe um vídeo ou imagem e clique nele para defini-lo como
   fundo.
3. Clique em um slide. Ele vai para o ar imediatamente. Use o lápis ou dê dois
   cliques para corrigir a letra, dividir, duplicar ou excluir o slide.
4. Use as setas do teclado para avançar e voltar, `B` para preto e `Esc` para
   limpar a letra.
5. Em **Ajustes › Monitor do telão**, detecte as telas e escolha o monitor
   padrão. Depois, **Abrir telão** posiciona a janela diretamente nele quando o
   navegador oferece esse recurso.

## Previews do controlador

- A área grande é dedicada à letra ou ao versículo selecionado. Ela continua
  disponível enquanto outro conteúdo, como o relógio, está no telão.
- A mini-preview **Telão do público** tem dois modos: **Saída** espelha o estado
  enviado ao público; **Preparado** mostra um relógio ou visual configurado antes
  de colocá-lo no ar.
- O relógio da mini-preview respeita o texto auxiliar, o formato, os segundos,
  a fonte, o tamanho, a cor e o alinhamento escolhidos.
- A logo/sobreposição importada aparece tanto na preview da letra quanto na
  mini-preview.
- Os estados **No ar**, **Fora do ar** e **Preto** são identificados na própria
  mini-preview.

## Editor visual

Música, Bíblia e relógio têm estilos independentes. Escolha o elemento no painel
**Visual da saída** e ajuste fonte, peso, tamanho, cor, alinhamento, posição X/Y,
largura, altura de linha, espaço entre letras, sombra, itálico, maiúsculas,
contorno e fundo semitransparente. Na prévia grande, também é possível arrastar o
elemento para posicioná-lo.

A barra de tamanho cobre a faixa mais usada, mas o número ao lado aceita
qualquer valor positivo em pixels. Assim é possível digitar diretamente 180,
300, 1000 px ou outro tamanho sem um limite máximo artificial.

- **Música:** letra, rótulo de seção e créditos.
- **Bíblia:** texto, nome da versão e referência `Livro capítulo:verso`.
- **Relógio:** hora, texto auxiliar e data.

Cada elemento pode ser restaurado separadamente. Os ajustes ficam salvos para a
próxima abertura.

## Bíblia — XML e Louvor JA

A importação aceita a estrutura Zefania XML:

```xml
<XMLBIBLE biblename="Nome da tradução">
  <BIBLEBOOK bnumber="1" bname="Gênesis">
    <CHAPTER cnumber="1">
      <VERS vnumber="1">Texto do versículo.</VERS>
    </CHAPTER>
  </BIBLEBOOK>
</XMLBIBLE>
```

O NexStage não baixa nem distribui traduções bíblicas. Importe apenas arquivos
que você tem autorização para usar.

É possível ocultar o nome da versão, usar referência completa ou compacta e
editar separadamente tamanho, fonte, cor e localização da versão, do versículo e
da referência.

Quando o `database.db` do Louvor JA está disponível, as versões locais aparecem
automaticamente no mesmo seletor, em um grupo separado. A versão, o livro e o
capítulo são escolhidos normalmente. O NexStage abre o banco em modo somente
leitura e consulta apenas o capítulo escolhido; os textos não são copiados para
o pacote nem carregados todos na memória.

## Louvor JA — catálogo local e offline

Em **Músicas**, clique em **Importar do Louvor JA**. O NexStage procura
automaticamente:

```text
C:\Program Files (x86)\Louvor JA\config\database.db
```

Se a instalação estiver em outro local, informe o caminho completo em
**Ajustes › Louvor JA**. A busca lê título, álbum e letra diretamente no banco
local e funciona sem internet. O banco é aberto como SQLite em modo somente
leitura; fundos, imagens e MP3 não são copiados. A música escolhida é copiada
para a biblioteca do NexStage e pode ser revisada antes de ir ao ar.

O arquivo usado é `database.db`, não o `BD.mdb` do Microsoft Access. Portanto, a
senha solicitada pelo Access para o MDB não é necessária nessa integração.

O mesmo banco também pode fornecer as traduções da Bíblia instaladas no Louvor
JA. A disponibilidade exata depende da versão local do programa. No banco
validado para esta versão foram encontradas ACRF, ARA, ARIB, NTLH, NVI, KJA,
NVT, NAA, ARC e ACF.

## OBS Studio

1. Inicie o NexStage.
2. No OBS, adicione uma **Fonte de navegador**.
3. Use `http://127.0.0.1:4310/obs` com resolução 1920 × 1080.
4. A saída é transparente e mostra somente letra, referência e logo.

O CSS personalizado do OBS pode alterar qualquer parte. Exemplo de lower third:

```css
#lyrics {
  font-family: Arial, sans-serif !important;
  font-size: 64px !important;
  left: 50% !important;
  top: 72% !important;
  width: 88% !important;
}

#reference {
  color: #66b7ff !important;
}
```

Para incluir também o fundo no OBS, use
`http://127.0.0.1:4310/obs?background=1`.

## Vídeos e desempenho

- Use preferencialmente **MP4, H.264, 1920 × 1080, 30 fps, 8–16 Mb/s**.
- O telão usa dois players: o próximo fundo é preparado fora da tela e entra
  por crossfade.
- O painel de operação não mantém outra cópia do vídeo tocando. Ele decodifica
  um único quadro de 640 × 360, guarda esse quadro em cache e libera o player;
  a reprodução contínua permanece somente na saída principal.
- O servidor oferece HTTP Range, necessário para o navegador buscar trechos do
  vídeo sem reler o arquivo inteiro.
- Telão e OBS usam long polling. Quando nada muda, não ficam fazendo centenas
  de requisições por minuto.
- O upload é gravado em blocos e não ocupa na RAM o tamanho total do vídeo.

Se um `.mov` não tocar no Chrome/Edge, converta-o para H.264 MP4. O contêiner
MOV é aceito, mas os codecs internos variam.

## Letras online

A busca usa a API pública do LRCLIB e só funciona com internet. Sempre confira
a letra e as permissões de uso antes de apresentá-la. As letras importadas ficam
locais em `data/library.json`.

Essa busca é independente da integração com o Louvor JA. Se a internet estiver
fora, o catálogo Louvor JA, os TXT já importados, as Bíblias, as mídias, o telão
e o OBS continuam funcionando normalmente.

## Fontes personalizadas

Em **Ajustes › Fontes**, importe TTF, OTF, WOFF ou WOFF2. A fonte fica instalada
somente no NexStage e passa a aparecer no seletor de todos os elementos de
música, Bíblia e relógio. Não é necessário instalar a fonte no Windows, macOS ou
Linux.

## Ajustes úteis

- Cor de destaque e escala da interface.
- Densidade compacta, confortável ou grande.
- Confirmação opcional para excluir músicas e limpar a saída.
- Duração do crossfade entre vídeos.
- Frame congelado do vídeo na preview ou preview de vídeo desligada.
- Cache de frames com botão para limpeza.
- Monitor padrão e abertura usando toda a área disponível.
- Formato da hora, segundos, data e texto auxiliar do relógio.
- Rótulos e créditos opcionais nas músicas.

## Exportar e importar configurações

Em **Ajustes › Configurações**, use **Exportar** para baixar um arquivo
`.nxsconfig`. Ele guarda estilos de música, Bíblia e relógio, cores, interface,
opções de vídeo e demais preferências. **Importar** restaura esses ajustes.

Por segurança e portabilidade, o arquivo não contém letras, Bíblias XML,
vídeos, imagens, arquivos de fontes, caminho do Louvor JA nem o identificador do
monitor. Esses dois últimos permanecem configurados no computador atual durante
a importação.

## Pastas importantes

- `C:\NexStage\media\`: vídeos, imagens e logos importados.
- `C:\NexStage\data\library.json`: músicas e índice das Bíblias.
- `C:\NexStage\data\bibles\`: cópia dos XMLs importados.
- `C:\NexStage\data\fonts\`: fontes importadas para uso no NexStage.
- `C:\NexStage\data\settings.json`: aparência e mídia padrão.

Faça backup das pastas `data` e `media` antes de formatar o computador.

O desinstalador fica em `C:\NexStage` e não apaga automaticamente essas pastas
pessoais. Se quiser removê-las também, faça isso manualmente depois do backup.

## Limites atuais

- Não transcodifica vídeos; apenas reproduz o arquivo original.
- A busca online depende da disponibilidade do LRCLIB.
- A escolha automática do monitor depende da API de gerenciamento de janelas do
  navegador. Chrome e Edge atuais pedem permissão na primeira detecção; em outros
  navegadores, a janela abre normalmente e pode ser movida manualmente.
- Ainda não há NDI nem controle remoto pela rede.
- macOS e Linux continuam no modo Python; esta versão não cria DMG, AppImage nem
  outros pacotes nativos para esses sistemas.

## Desenvolvimento e testes

O servidor e a interface em modo Python não possuem dependências externas. Rode:

```bash
python3 -m unittest discover -s tests -v
```

### Gerar `NexStage-Setup.exe` no Windows

É necessário usar Windows 64 bits com Python 3 e Inno Setup 6 instalados. Abra
`build-windows.bat`; ele cria um ambiente de compilação isolado, instala
PyInstaller, pystray e Pillow, executa os testes e gera:

```text
release\NexStage-Setup.exe
```

Esse é o único arquivo que deve ser anexado à release para os usuários do
Windows, sempre com o nome exato `NexStage-Setup.exe`. Os scripts de build ficam
no repositório de código-fonte e não entram no programa instalado.

O passo a passo completo está em `COMPILAR-NO-WINDOWS.md`.

O executável e o instalador recebem o ícone oficial, produto **NexStage** e autor
**Natan Gabriel** nos metadados. O código-fonte continua disponível e
modificável conforme a licença do projeto.

Projeto original, sem reaproveitamento de código do FreeShow.
