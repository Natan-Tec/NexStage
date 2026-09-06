# NexStage 0.4.0

## Bíblia do Louvor JA

- Detecção automática das versões bíblicas existentes no `database.db` local.
- Traduções do Louvor JA e Bíblias XML agrupadas no mesmo seletor.
- Seleção normal de versão, livro e capítulo, inteiramente offline.
- Leitura sob demanda: somente o capítulo escolhido é consultado.
- Banco aberto por URI SQLite em modo somente leitura e com `query_only` ativo.
- Linhas sem texto são ignoradas com segurança.
- O banco e suas traduções não são incluídos nem redistribuídos pelo NexStage.

## Tamanho livre do texto

- A barra mantém a faixa prática de 12 a 160 px.
- Nova caixa numérica aceita qualquer valor positivo, sem máximo artificial.
- O valor personalizado é preservado ao alterar cor, fonte, posição ou outro ajuste.
- Funciona em letras, rótulos, créditos, versículos, referências, versão bíblica,
  hora, texto auxiliar e data.

## Configurações portáteis

- Exportação para arquivo `.nxsconfig`.
- Importação validada de configurações e estilos.
- Compatibilidade com o formato direto do `settings.json` das versões anteriores.
- Caminho local do Louvor JA e monitor preferido não são substituídos ao importar.
- Biblioteca, mídias e arquivos de fontes continuam separados do arquivo de ajustes.

## Compatibilidade

- Migração das configurações 0.2.0 e 0.3.0 mantida.
- Integração de músicas do Louvor JA, fontes locais, seleção de monitor, favicon,
  previews duplas, OBS e reprodução otimizada de vídeo preservadas.
- Nenhuma dependência nova: continua usando somente Python 3 e o navegador.
