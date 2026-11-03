# Uso de IA — registro de prompts

Conforme o Plano de Ensino, documento aqui o uso de IA generativa nesta atividade.

**Ferramenta:** Claude Code (Anthropic), modelo Claude Opus 5.5
**Data:** 03/11/2026

## Prompt 1

> Enviei os PDFs das aulas 21, 22 e 23 (Streamlit partes 1 a 3), o enunciado da atividade e o link do dataset
> (https://www.kaggle.com/datasets/fatismajli/ufc-data), além do notebook da EDA que fiz anteriormente.
>
> Enunciado colado: "Com base na sua EDA, crie uma aplicação no Streamlit com dois dashboards.
> Dashboard 1: um 'laboratório' de análise de distribuição e correlação. Dashboard 2: KPIs e métricas
> voltadas a um público alvo determinado individualmente." (seguido dos visuais mínimos, do checklist
> de teste do app publicado e dos entregáveis finais).

**O que a IA produziu:**

- `app.py` com as duas abas, reaproveitando os tratamentos da EDA (conversão de altura, envergadura e peso; preenchimento de `Stance`; variável `perfil_carreira`).
- Variáveis derivadas novas: `Total_lutas`, `Taxa_vitoria`, `Ape_index` e categorias oficiais de peso do UFC.
- Escolha do público-alvo do Dashboard 2 (olheiros e treinadores) e das 5 métricas.
- Rascunhos (wireframes) em `entregas/`, `README.md`, `requirements.txt` e `.gitignore`.

**O que revisei / decidi:**

- <!-- Preencha: o que você conferiu, alterou ou discordou no código gerado. -->
