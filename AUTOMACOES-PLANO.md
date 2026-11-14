# Automações do NexStage — plano por partes

Cada parte é **independente, testada e publicada sozinha**. Se o uso do Claude acabar no meio, o
NexStage continua funcionando na última parte publicada (nada fica pela metade na `main`).

Ideia geral (a partir do plano da IA anterior): regras **QUANDO** (gatilho) → **SE** (condições) →
**ENTÃO** (passos em sequência). Rodam no servidor Python, então funcionam mesmo com o controlador
fechado (desde que o NexStage esteja aberto). Só dados, nunca código livre.

Arquitetura (importante para as próximas partes): `automation.py` tem um **catálogo** (gatilhos,
condições e ações, cada um com seus parâmetros). A tela de edição é gerada a partir do catálogo;
para criar um bloco novo basta registrar no catálogo + escrever a função da ação.

| Parte | Conteúdo | Estado |
|---|---|---|
| 1 | Motor, armazenamento, histórico, pausar tudo, executar agora. Gatilhos: horário, a cada N min, ao abrir o NexStage, manual. Condições: dia da semana, entre horários, está no ar. Ações: fundo, logo, relógio, cronômetro, mensagem, preto, limpar, esperar, parar. Aba **Automações** com editor em cartões. Controlador passa a acompanhar mudanças feitas pelo servidor. | em andamento (0.9.0) |
| 2 | Ações de conteúdo: exibir música/seção, passagem bíblica, próximo/anterior slide, fundo aleatório. | |
| 3 | Vídeo: iniciar/pausar/parar vídeo (computador e YouTube); gatilhos "quando o vídeo terminar", "quando o cronômetro zerar / faltar X min". | |
| 4 | Controle de fluxo: SENÃO, E/OU/NÃO, REPETIR. | |
| 5 | Rotinas encadeadas ("Culto de Sábado"), chamar outra automação, prioridade do operador (ação manual cancela a automação), prevenção de conflitos. | |
| 6 (futuro) | Variáveis, sorteio, salvar/restaurar estado, exportar/importar automações. | |

Regras desde o começo: executar manualmente para testar; histórico (quando rodou, se deu erro);
agendamento só funciona com o NexStage aberto (não "recupera" horários perdidos); uma automação
não roda duas vezes ao mesmo tempo.
