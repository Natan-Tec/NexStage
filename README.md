# NexStage 0.4.1

Apresentador local para igrejas, criado para letras, Bíblia em XML ou Louvor JA, vídeos de
fundo e integração simples com OBS. A interface é HTML/CSS/JavaScript, mas o
aplicativo roda por um servidor Python local e não precisa de Node.js, Docker,
npm, servidor de banco de dados ou internet para apresentar.

> O nome **NexStage** é provisório e pode ser trocado depois sem alterar a base
> técnica.

## Abrir

### Windows

1. Extraia a pasta completa.
2. Coloque-a em um local definitivo, como `Documentos\NexStage`.
3. Dê dois cliques em `instalar.bat` para criar o atalho **NexStage** na Área de
   Trabalho com o ícone oficial.
4. Abra pelo novo atalho. O navegador abrirá automaticamente.

O instalador não exige permissão de administrador e não altera o Registro do
Windows. Ele apenas cria um atalho para o `start.bat`; se a pasta for movida
depois, execute `instalar.bat` novamente. Também é possível abrir diretamente
por `start.bat`, sem instalar o atalho.

### macOS

1. Tenha o Python 3 instalado.
2. Clique com o botão direito em `start.command` e escolha **Abrir**.
3. Se necessário, no Terminal execute `chmod +x start.command` uma única vez.

### Linux

Execute:

```bash
chmod +x start.sh
./start.sh
```

Também funciona em qualquer sistema com:

```bash
python3 run.py
```

Por padrão o controlador abre em `http://127.0.0.1:4310`.

## Atualizar das versões 0.2.0, 0.3.0 ou 0.4.0

Feche o NexStage, extraia a 0.4.1 em uma pasta nova e copie da pasta antiga para
a nova as pastas `data` e `media`. Músicas, Bíblias, configurações, vídeos e
logos serão preservados. Na primeira abertura, o formato antigo de aparência é
migrado automaticamente para os novos estilos independentes.

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

- `media/`: vídeos, imagens e logos importados.
- `data/library.json`: músicas e índice das Bíblias.
- `data/bibles/`: cópia dos XMLs importados.
- `data/fonts/`: fontes importadas para uso no NexStage.
- `data/settings.json`: aparência e mídia padrão.

Faça backup das pastas `data` e `media` antes de formatar o computador.

## Limites atuais

- Não transcodifica vídeos; apenas reproduz o arquivo original.
- A busca online depende da disponibilidade do LRCLIB.
- A escolha automática do monitor depende da API de gerenciamento de janelas do
  navegador. Chrome e Edge atuais pedem permissão na primeira detecção; em outros
  navegadores, a janela abre normalmente e pode ser movida manualmente.
- Ainda não há instalador `.exe`, assinatura de macOS, NDI nem controle remoto
  pela rede.

## Desenvolvimento e testes

Não há dependências externas. Rode:

```bash
python3 -m unittest discover -s tests -v
```

Projeto original, sem reaproveitamento de código do FreeShow.
