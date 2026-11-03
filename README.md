# 🥊 UFC Fighters — Dashboards em Streamlit

Aplicação Streamlit construída a partir da minha EDA do dataset **UFC Data**, com dois dashboards em abas.

**🔗 App publicado:** https://ufc-dashboards-avd.streamlit.app/

**Dataset:** [UFC Data — Kaggle (fatismajli)](https://www.kaggle.com/datasets/fatismajli/ufc-data) · 3.951 lutadores · altura, peso, envergadura, base e cartel (vitórias, derrotas, empates).

## Dashboards

| Aba | Objetivo | Conteúdo |
|---|---|---|
| 🔬 **Dashboard 1 — Laboratório** | Explorar distribuição e correlação | Mapa de calor de correlação (Spearman/Pearson/Kendall), histograma por variável quantitativa, tabela descritiva com Shapiro-Wilk, dispersão X × Y |
| 🎯 **Dashboard 2 — KPIs** | Público-alvo: **olheiros e treinadores de MMA** | 5 métricas (lutadores, taxa de vitória, % cartel positivo, vantagem de envergadura, experiência mediana) + 3 visuais (vitória por categoria de peso, cartel positivo por base, ape index × vitória) |

**Painel lateral:** seletor de variáveis quantitativas, filtro de intervalo (slider) sobre qualquer variável, mínimo de lutas, base de luta e remoção de outliers (IQR). Os filtros valem para as duas abas.

## Estrutura do repositório

```
├── app.py                  # aplicação Streamlit
├── requirements.txt        # dependências para o deploy
├── .streamlit/config.toml  # tema
├── data/ufc_fighters.csv   # dataset (público, Kaggle)
├── notebooks/              # notebook da EDA
├── entregas/               # rascunhos dos dois dashboards
└── prompts/                # registro do uso de IA
```

## Como rodar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Privacidade e dados sensíveis

- O dataset é público e não exige credenciais: o CSV está versionado em `data/`, então o app não usa API do Kaggle nem chaves.
- Nomes e apelidos dos lutadores são removidos logo na carga e nunca aparecem na interface.
- `.streamlit/secrets.toml`, `.env` e `kaggle.json` estão no `.gitignore`.

## Autor

Luca Albuquerque
