"""
UFC Fighters — Dashboards em Streamlit
Autor: Luca Albuquerque

Aplicação construída a partir da EDA do dataset "UFC Data" (Kaggle, fatismajli/ufc-data).
- Dashboard 1: laboratório de distribuição e correlação
- Dashboard 2: KPIs para olheiros e treinadores de MMA

Para rodar localmente:  streamlit run app.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from scipy import stats

# ---------------------------------------------------------------------------
# Configuração da página e paleta (a mesma convenção de cores da EDA)
# ---------------------------------------------------------------------------
st.set_page_config(page_title="UFC Fighters — Dashboards", page_icon="🥊", layout="wide")

COR_NEUTRA = "#b8b8b8"      # pano de fundo genérico
COR_CONTEXTO = "#d9a8a0"    # classe de referência ("Não Vencedor"); mais escuro que na EDA para contrastar com o fundo branco
COR_DESTAQUE = "#2d223a"    # classe de interesse ("Vencedor")
COR_ALERTA = "#d62728"      # pontos de atenção
PALETA_PERFIL = {"Vencedor": COR_DESTAQUE, "Não Vencedor": COR_CONTEXTO}

CAMINHO_DADOS = Path(__file__).parent / "data" / "ufc_fighters.csv"

# Nomes amigáveis para as variáveis quantitativas
ROTULOS = {
    "Wins": "Vitórias",
    "Losses": "Derrotas",
    "Draws": "Empates",
    "Total_lutas": "Total de lutas",
    "Taxa_vitoria": "Taxa de vitória (%)",
    "Height_in": "Altura (pol.)",
    "Reach_in": "Envergadura (pol.)",
    "Weight_lbs": "Peso (lbs)",
    "Ape_index": "Ape index (envergadura − altura, pol.)",
}
VARS_QUANT = list(ROTULOS.keys())

CATEGORIAS_PESO = {
    "Palha (≤115)": 115,
    "Mosca (≤125)": 125,
    "Galo (≤135)": 135,
    "Pena (≤145)": 145,
    "Leve (≤155)": 155,
    "Meio-médio (≤170)": 170,
    "Médio (≤185)": 185,
    "Meio-pesado (≤205)": 205,
    "Pesado (≤265)": 265,
    "Acima de 265": np.inf,
}


def rotulo(col: str) -> str:
    return ROTULOS.get(col, col)


# ---------------------------------------------------------------------------
# Carga e tratamento (replica as decisões tomadas no notebook de EDA)
# ---------------------------------------------------------------------------
def altura_para_polegadas(h):
    if pd.isna(h) or h == "--":
        return np.nan
    h = str(h).replace('"', "").strip()
    try:
        pes, pol = h.split("' ")
        return int(pes) * 12 + int(pol)
    except ValueError:
        return np.nan


@st.cache_data
def carregar_dados() -> pd.DataFrame:
    df = pd.read_csv(CAMINHO_DADOS)

    # Privacidade: nomes e apelidos não são necessários para nenhuma análise,
    # então saem logo na carga e nunca chegam à interface.
    df = df.drop(columns=["First Name", "Last Name", "Nickname"])

    df["Stance"] = df["Stance"].fillna("Desconhecida")

    df["Height_in"] = df["Height"].apply(altura_para_polegadas)
    df["Reach_in"] = pd.to_numeric(
        df["Reach"].replace("--", np.nan).astype(str).str.replace('"', "", regex=False),
        errors="coerce",
    )
    df["Weight_lbs"] = pd.to_numeric(
        df["Weight"].astype(str).str.replace(" lbs.", "", regex=False), errors="coerce"
    )
    df = df.drop(columns=["Height", "Reach", "Weight"])

    for col in ["Wins", "Losses", "Draws"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["Total_lutas"] = df["Wins"] + df["Losses"] + df["Draws"]
    df["Taxa_vitoria"] = np.where(df["Total_lutas"] > 0, df["Wins"] / df["Total_lutas"] * 100, np.nan)
    df["Ape_index"] = df["Reach_in"] - df["Height_in"]
    df["perfil_carreira"] = np.where(df["Wins"] > df["Losses"], "Vencedor", "Não Vencedor")

    limites = [0] + list(CATEGORIAS_PESO.values())
    df["categoria_peso"] = pd.cut(df["Weight_lbs"], bins=limites, labels=list(CATEGORIAS_PESO.keys()))

    df["faixa_ape"] = pd.cut(
        df["Ape_index"],
        bins=[-np.inf, -1, 1, 3, np.inf],
        labels=["Negativo (< −1)", "Neutro (−1 a 1)", "Positivo (1 a 3)", "Muito positivo (> 3)"],
    )
    return df


def remover_outliers_iqr(df: pd.DataFrame, colunas: list[str]) -> pd.DataFrame:
    mascara = pd.Series(True, index=df.index)
    for col in colunas:
        q1, q3 = df[col].quantile([0.25, 0.75])
        iqr = q3 - q1
        fora = (df[col] < q1 - 1.5 * iqr) | (df[col] > q3 + 1.5 * iqr)
        mascara &= ~fora  # valores ausentes não são tratados como outliers
    return df[mascara]


df_completo = carregar_dados()

# ---------------------------------------------------------------------------
# Painel lateral — filtros globais (valem para os dois dashboards)
# ---------------------------------------------------------------------------
st.sidebar.title("🥊 Filtros")

vars_selecionadas = st.sidebar.multiselect(
    "Variáveis quantitativas avaliadas",
    options=VARS_QUANT,
    default=["Height_in", "Reach_in", "Weight_lbs", "Ape_index", "Taxa_vitoria", "Total_lutas"],
    format_func=rotulo,
    help="Controlam o mapa de calor, os histogramas e a tabela descritiva do Dashboard 1.",
)

st.sidebar.markdown("---")
var_intervalo = st.sidebar.selectbox(
    "Variável do filtro de intervalo",
    options=VARS_QUANT,
    index=VARS_QUANT.index("Weight_lbs"),
    format_func=rotulo,
)
minimo = float(np.floor(df_completo[var_intervalo].min()))
maximo = float(np.ceil(df_completo[var_intervalo].max()))
intervalo = st.sidebar.slider(
    f"Intervalo de {rotulo(var_intervalo)}",
    min_value=minimo,
    max_value=maximo,
    value=(minimo, maximo),
    step=1.0,
    help="Registros fora do intervalo são excluídos da avaliação. Registros sem valor nessa variável também saem quando o intervalo é reduzido.",
)

min_lutas = st.sidebar.slider(
    "Mínimo de lutas no cartel",
    min_value=0,
    max_value=30,
    value=0,
    help="Lutadores com poucas lutas têm taxas de vitória instáveis (ex.: 1-0 = 100%).",
)

bases = sorted(df_completo["Stance"].unique())
bases_selecionadas = st.sidebar.multiselect("Base de luta (Stance)", options=bases, default=bases)

tirar_outliers = st.sidebar.checkbox(
    "Remover outliers (regra do IQR) das variáveis avaliadas",
    value=False,
)

# Aplicação dos filtros
df = df_completo[df_completo["Stance"].isin(bases_selecionadas)]
df = df[df["Total_lutas"] >= min_lutas]
if intervalo != (minimo, maximo):
    df = df[df[var_intervalo].between(*intervalo)]
if tirar_outliers and vars_selecionadas:
    df = remover_outliers_iqr(df, vars_selecionadas)

st.sidebar.markdown("---")
st.sidebar.caption(
    f"**{len(df):,}** de {len(df_completo):,} lutadores no recorte atual.".replace(",", ".")
)

# ---------------------------------------------------------------------------
# Cabeçalho
# ---------------------------------------------------------------------------
st.title("UFC Fighters — Dashboards")
st.caption(
    "Fonte: [UFC Data — Kaggle](https://www.kaggle.com/datasets/fatismajli/ufc-data). "
    "Cada registro é um lutador; nomes e apelidos foram removidos da aplicação."
)

if df.empty:
    st.warning("Nenhum lutador atende aos filtros escolhidos. Ajuste o painel lateral.")
    st.stop()

aba_lab, aba_kpi = st.tabs(["🔬 Dashboard 1 — Laboratório", "🎯 Dashboard 2 — KPIs para olheiros"])

# ---------------------------------------------------------------------------
# Dashboard 1 — laboratório de distribuição e correlação
# ---------------------------------------------------------------------------
with aba_lab:
    st.subheader("Laboratório de distribuição e correlação")
    st.write(
        "Escolha as variáveis no painel lateral e explore como elas se distribuem e se relacionam. "
        "Tudo aqui reflete o recorte atual dos filtros."
    )

    if not vars_selecionadas:
        st.info("Selecione ao menos uma variável quantitativa no painel lateral.")
    else:
        # --- Mapa de calor de correlação
        st.markdown("#### Mapa de calor de correlação")
        col_metodo, col_info = st.columns([1, 3])
        metodo = col_metodo.radio(
            "Método",
            options=["spearman", "pearson", "kendall"],
            format_func=str.capitalize,
            help="Spearman foi o método adotado na EDA, já que as variáveis não seguem distribuição normal.",
        )
        col_info.info(
            "**Pearson** mede relação linear; **Spearman** e **Kendall** medem relação monotônica "
            "e são mais robustos a outliers e assimetria."
        )

        if len(vars_selecionadas) < 2:
            st.info("Selecione pelo menos duas variáveis para calcular correlações.")
        else:
            corr = df[vars_selecionadas].corr(method=metodo)
            corr.index = corr.columns = [rotulo(c) for c in vars_selecionadas]
            fig_corr = px.imshow(
                corr,
                text_auto=".2f",
                color_continuous_scale="RdBu_r",
                zmin=-1,
                zmax=1,
                aspect="auto",
            )
            fig_corr.update_layout(height=520, margin=dict(t=20, b=20), coloraxis_colorbar_title="r")
            st.plotly_chart(fig_corr, width="stretch")

        # --- Histogramas
        st.markdown("#### Distribuição de cada variável")
        col_a, col_b = st.columns(2)
        n_bins = col_a.slider("Número de bins", min_value=5, max_value=80, value=30)
        separar = col_b.toggle("Separar por perfil de carreira (Vencedor × Não Vencedor)", value=False)

        grade = st.columns(2)
        for i, col in enumerate(vars_selecionadas):
            fig_hist = px.histogram(
                df.dropna(subset=[col]),
                x=col,
                nbins=n_bins,
                color="perfil_carreira" if separar else None,
                color_discrete_map=PALETA_PERFIL,
                color_discrete_sequence=[COR_NEUTRA],
                marginal="box",
                barmode="overlay",
                opacity=0.75 if separar else 1,
                labels={col: rotulo(col), "perfil_carreira": "Perfil"},
            )
            media, mediana = df[col].mean(), df[col].median()
            fig_hist.add_vline(x=media, line_dash="dash", line_color=COR_ALERTA)
            fig_hist.add_vline(x=mediana, line_color="black")
            fig_hist.update_layout(
                title=f"{rotulo(col)}  ·  média {media:.1f} (tracejado) · mediana {mediana:.1f}",
                title_font_size=14,
                height=360,
                margin=dict(t=50, b=10),
                yaxis_title="Lutadores",
                legend_title_text="",
            )
            grade[i % 2].plotly_chart(fig_hist, width="stretch")

        # --- Estatística descritiva
        st.markdown("#### Estatística descritiva")
        desc = df[vars_selecionadas].describe().T
        desc["assimetria"] = df[vars_selecionadas].skew()
        desc["curtose"] = df[vars_selecionadas].kurtosis()
        p_valores = []
        for col in vars_selecionadas:
            amostra = df[col].dropna()
            if len(amostra) >= 3:
                amostra = amostra.sample(min(len(amostra), 5000), random_state=42)
                p_valores.append(stats.shapiro(amostra).pvalue)
            else:
                p_valores.append(np.nan)
        desc["p-valor Shapiro"] = p_valores
        desc = desc.rename(
            columns={"count": "n", "mean": "média", "std": "desvio", "min": "mín", "50%": "mediana", "max": "máx"}
        )[["n", "média", "mediana", "desvio", "mín", "máx", "assimetria", "curtose", "p-valor Shapiro"]]
        desc.index = [rotulo(c) for c in desc.index]
        st.dataframe(
            desc.style.format("{:.2f}").format("{:.0f}", subset=["n"]).format("{:.2g}", subset=["p-valor Shapiro"]),
            width="stretch",
        )
        st.caption("p-valor de Shapiro-Wilk < 0,05 indica que a variável não segue distribuição normal.")

        # --- Dispersão livre
        st.markdown("#### Dispersão entre duas variáveis")
        c1, c2 = st.columns(2)
        eixo_x = c1.selectbox("Eixo X", options=VARS_QUANT, index=VARS_QUANT.index("Height_in"), format_func=rotulo)
        eixo_y = c2.selectbox("Eixo Y", options=VARS_QUANT, index=VARS_QUANT.index("Reach_in"), format_func=rotulo)
        pares = df[[eixo_x, eixo_y, "perfil_carreira"]].dropna()
        if len(pares) > 2 and eixo_x != eixo_y:
            r_s = stats.spearmanr(pares[eixo_x], pares[eixo_y]).statistic
            titulo = f"Spearman r = {r_s:.2f}  (n = {len(pares)})"
        else:
            titulo = f"n = {len(pares)}"
        fig_disp = px.scatter(
            pares,
            x=eixo_x,
            y=eixo_y,
            color="perfil_carreira",
            color_discrete_map=PALETA_PERFIL,
            opacity=0.7,
            labels={eixo_x: rotulo(eixo_x), eixo_y: rotulo(eixo_y), "perfil_carreira": "Perfil"},
            title=titulo,
        )
        fig_disp.update_layout(height=450, legend_title_text="")
        st.plotly_chart(fig_disp, width="stretch")

# ---------------------------------------------------------------------------
# Dashboard 2 — KPIs para olheiros e treinadores de MMA
# ---------------------------------------------------------------------------
with aba_kpi:
    st.subheader("Painel do olheiro: que perfil físico e de luta vence mais?")
    st.write(
        "**Público-alvo:** olheiros (scouts) e treinadores de academias de MMA que avaliam atletas "
        "e precisam saber quais características físicas e de base estão associadas a um cartel vencedor. "
        "As setas comparam o recorte filtrado com a base completa."
    )

    def kpis(d: pd.DataFrame) -> dict:
        return {
            "n": len(d),
            "taxa": d["Taxa_vitoria"].mean(),
            "pct_venc": (d["perfil_carreira"] == "Vencedor").mean() * 100,
            "ape": d["Ape_index"].mean(),
            "lutas": d["Total_lutas"].median(),
        }

    atual, base = kpis(df), kpis(df_completo)
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric(
        "Lutadores no recorte",
        f"{atual['n']:,}".replace(",", "."),
        f"{atual['n'] / base['n'] * 100:.0f}% da base",
        delta_color="off",
    )
    m2.metric(
        "Taxa média de vitória",
        f"{atual['taxa']:.1f}%",
        f"{atual['taxa'] - base['taxa']:+.1f} p.p.",
        help="Vitórias ÷ total de lutas, média entre os lutadores.",
    )
    m3.metric(
        "Cartel positivo",
        f"{atual['pct_venc']:.1f}%",
        f"{atual['pct_venc'] - base['pct_venc']:+.1f} p.p.",
        help="Percentual de lutadores com mais vitórias do que derrotas.",
    )
    m4.metric(
        "Vantagem de envergadura",
        f"{atual['ape']:+.2f} pol." if pd.notna(atual["ape"]) else "—",
        f"{atual['ape'] - base['ape']:+.2f} pol." if pd.notna(atual["ape"]) else None,
        help="Ape index médio: envergadura menos altura. Positivo = braços mais longos que a altura.",
    )
    m5.metric(
        "Experiência mediana",
        f"{atual['lutas']:.0f} lutas",
        f"{atual['lutas'] - base['lutas']:+.0f} lutas",
        help="Mediana do total de lutas profissionais (vitórias + derrotas + empates).",
    )

    st.markdown("---")
    min_grupo = st.slider(
        "Tamanho mínimo de grupo para aparecer nos gráficos",
        min_value=1,
        max_value=100,
        value=20,
        help="Grupos muito pequenos geram porcentagens enganosas (ex.: a base 'Sideways' tem 3 lutadores).",
    )

    def resumo_por(coluna: str) -> pd.DataFrame:
        r = (
            df.dropna(subset=[coluna])
            .groupby(coluna, observed=True)
            .agg(
                lutadores=("Taxa_vitoria", "size"),
                taxa_vitoria=("Taxa_vitoria", "mean"),
                pct_vencedores=("perfil_carreira", lambda s: (s == "Vencedor").mean() * 100),
            )
            .reset_index()
        )
        return r[r["lutadores"] >= min_grupo]

    v1, v2 = st.columns(2)

    # Visual 1 — taxa de vitória por categoria de peso
    por_peso = resumo_por("categoria_peso")
    with v1:
        st.markdown("##### Taxa de vitória por categoria de peso")
        if por_peso.empty:
            st.info("Nenhuma categoria com lutadores suficientes no recorte.")
        else:
            fig_peso = px.bar(
                por_peso,
                x="categoria_peso",
                y="taxa_vitoria",
                text=por_peso["taxa_vitoria"].map("{:.0f}%".format),
                hover_data={"lutadores": True, "taxa_vitoria": ":.1f"},
                color_discrete_sequence=[COR_DESTAQUE],
                labels={"categoria_peso": "Categoria", "taxa_vitoria": "Taxa média de vitória (%)"},
            )
            fig_peso.add_hline(y=base["taxa"], line_dash="dash", line_color=COR_ALERTA)
            fig_peso.update_traces(textposition="outside")
            fig_peso.update_layout(height=400, yaxis_range=[0, 100], xaxis_tickangle=-35)
            st.caption("Linha tracejada vermelha = média geral da base completa.")
            st.plotly_chart(fig_peso, width="stretch")

    # Visual 2 — % de cartel positivo por base
    por_base = resumo_por("Stance").sort_values("pct_vencedores")
    with v2:
        st.markdown("##### Cartel positivo por base de luta")
        if por_base.empty:
            st.info("Nenhuma base com lutadores suficientes no recorte.")
        else:
            fig_base = px.bar(
                por_base,
                x="pct_vencedores",
                y="Stance",
                orientation="h",
                text=por_base["pct_vencedores"].map("{:.0f}%".format),
                hover_data={"lutadores": True, "pct_vencedores": ":.1f"},
                color_discrete_sequence=[COR_DESTAQUE],
                labels={"pct_vencedores": "% com cartel positivo", "Stance": "Base"},
            )
            fig_base.add_vline(x=base["pct_venc"], line_dash="dash", line_color=COR_ALERTA)
            fig_base.update_traces(textposition="inside")
            fig_base.update_layout(height=400, xaxis_range=[0, 100])
            st.caption("Linha tracejada vermelha = média geral da base completa.")
            st.plotly_chart(fig_base, width="stretch")

    # Visual 3 — envergadura relativa x desempenho
    st.markdown("##### Braços longos ajudam? Ape index × taxa de vitória")
    v3, v4 = st.columns([3, 2])
    com_ape = df.dropna(subset=["Ape_index", "faixa_ape", "Taxa_vitoria"])
    with v3:
        if com_ape.empty:
            st.info("Sem lutadores com altura e envergadura registradas no recorte.")
        else:
            fig_box = px.box(
                com_ape,
                x="faixa_ape",
                y="Taxa_vitoria",
                color_discrete_sequence=[COR_DESTAQUE],
                category_orders={"faixa_ape": list(com_ape["faixa_ape"].cat.categories)},
                points=False,
                labels={"faixa_ape": "Ape index (envergadura − altura)", "Taxa_vitoria": "Taxa de vitória (%)"},
            )
            fig_box.update_layout(height=400)
            st.plotly_chart(fig_box, width="stretch")
    with v4:
        por_ape = resumo_por("faixa_ape")
        if not por_ape.empty:
            st.dataframe(
                por_ape.rename(
                    columns={
                        "faixa_ape": "Ape index",
                        "lutadores": "n",
                        "taxa_vitoria": "Vitória (%)",
                        "pct_vencedores": "Positivo (%)",
                    }
                ).style.format({"Vitória (%)": "{:.1f}", "Positivo (%)": "{:.1f}"}),
                hide_index=True,
                width="stretch",
            )
        st.caption(
            "Apenas lutadores com altura **e** envergadura registradas entram nesta análise. "
            "Associação não implica causalidade: a envergadura também varia com a categoria de peso."
        )
