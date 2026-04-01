"""
VOC Pipeline — Dashboard Interactivo (Streamlit)

Este módulo implementa la interfaz de usuario para la visualización de datos
de la "Voz del Cliente" (VOC). Proporciona una vista analítica y operativa
de los sentimientos, categorías y alertas críticas procesadas.

Ejecutar: streamlit run dashboard.py
"""

import json
import os
import textwrap
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

COLORS = {
    "primary": "#247BA0",
    "primary_dark": "#19586F",
    "primary_soft": "#E8F4F8",
    "accent": "#70C1B3",
    "accent_dark": "#2E8D7E",
    "support": "#B2DBBF",
    "cream": "#F3FFBD",
    "highlight": "#FF1654",
    "highlight_dark": "#C11243",
    "surface": "#FFFFFF",
    "surface_alt": "#F7FCFA",
    "background": "#F4FBF8",
    "border": "#D1E5E4",
    "ink": "#173241",
    "muted": "#557280",
    "positive": "#2E8D7E",
    "neutral": "#6F9488",
    "negative": "#FF1654",
    "warning": "#8A7B1F",
    "warning_bg": "#FFF9DA",
    "danger_bg": "#FFE6EE",
}

PIE_COLORS = ["#247BA0", "#70C1B3", "#B2DBBF", "#F3FFBD", "#FF1654", "#19586F", "#2E8D7E"]
PURPLE_SCALE = ["#EAF6F3", "#D6EDE7", "#B2DBBF", "#70C1B3", "#247BA0", "#19586F"]
URGENCY_SCALE = ["#EAF7F2", "#BFE5DA", "#F3FFBD", "#FFC48F", "#FF1654"]


def wrap_axis_labels(values, width=14):
    return ["<br>".join(textwrap.wrap(str(value), width=width)) for value in values]


def render_page_header(title, description, eyebrow):
    st.markdown(
        f"""
        <div class="hero-panel">
            <div class="hero-eyebrow">{eyebrow}</div>
            <div class="hero-title">{title}</div>
            <div class="hero-description">{description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def style_figure(fig, height, title=None, legend_orientation="h", legend_y=-0.18):
    layout_kwargs = dict(
        height=height,
        margin=dict(l=0, r=0, t=82 if title else 18, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["ink"], family="Inter, Segoe UI, sans-serif"),
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            bordercolor=COLORS["border"],
            font=dict(color=COLORS["ink"])
        ),
        legend=dict(
            orientation=legend_orientation,
            y=legend_y,
            x=0,
            title_text="",
            bgcolor="rgba(255,255,255,0.78)"
        ),
        uniformtext_minsize=10,
        uniformtext_mode="hide",
    )
    if title:
        layout_kwargs["title"] = dict(
            text=title,
            x=0.02,
            xanchor="left",
            y=0.98,
            yanchor="top",
            font=dict(size=18, color=COLORS["ink"])
        )
    fig.update_layout(**layout_kwargs)
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        linecolor=COLORS["border"],
        automargin=True,
        tickfont=dict(color=COLORS["muted"]),
        title_font=dict(color=COLORS["muted"]),
    )
    fig.update_yaxes(
        gridcolor="rgba(36, 123, 160, 0.10)",
        zeroline=False,
        linecolor=COLORS["border"],
        automargin=True,
        tickfont=dict(color=COLORS["muted"]),
        title_font=dict(color=COLORS["muted"]),
    )
    return fig

# ============================================================
# CONFIGURACIÓN DE PÁGINA
# ============================================================
st.set_page_config(
    page_title="VOC Intelligence Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# ESTILOS
# ============================================================
st.markdown("""
<style>
    :root {
        --primary: #247BA0;
        --primary-dark: #19586F;
        --primary-soft: #E8F4F8;
        --accent: #70C1B3;
        --accent-dark: #2E8D7E;
        --support: #B2DBBF;
        --cream: #F3FFBD;
        --highlight: #FF1654;
        --surface: #FFFFFF;
        --surface-alt: #F7FCFA;
        --background: #F4FBF8;
        --border: #D1E5E4;
        --ink: #173241;
        --muted: #557280;
        --positive: #2E8D7E;
        --neutral: #6F9488;
        --negative: #FF1654;
        --warning: #8A7B1F;
        --warning-bg: #FFF9DA;
        --danger-bg: #FFE6EE;
        --shadow: 0 18px 45px rgba(17, 24, 39, 0.08);
    }
    .stApp {
        background:
            radial-gradient(circle at top right, rgba(36, 123, 160, 0.12), transparent 28%),
            linear-gradient(180deg, #FBFFF9 0%, var(--background) 100%);
        color: var(--ink);
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 1.5rem;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #19586F 0%, #247BA0 100%);
        border-right: 1px solid rgba(255,255,255,0.08);
    }
    [data-testid="stSidebar"] * {
        color: #F8FAFC;
    }
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] .stCaption,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span {
        color: #E8ECF8 !important;
    }
    .sidebar-brand {
        background: linear-gradient(145deg, rgba(255,255,255,0.14), rgba(255,255,255,0.06));
        border: 1px solid rgba(255,255,255,0.16);
        border-radius: 22px;
        padding: 18px;
        margin-bottom: 1rem;
        box-shadow: 0 18px 40px rgba(6, 14, 30, 0.28);
        backdrop-filter: blur(6px);
    }
    .sidebar-brand img {
        width: 148px;
        display: block;
        margin-bottom: 16px;
        filter: brightness(0) invert(1);
    }
    .sidebar-kicker {
        font-size: 0.78rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: #B8C2DB;
        margin-bottom: 6px;
        font-weight: 700;
    }
    .sidebar-title {
        font-size: 1.35rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 6px;
    }
    .sidebar-copy {
        font-size: 0.92rem;
        line-height: 1.5;
        color: #D7DFF3;
    }
    .hero-panel {
        background:
            linear-gradient(135deg, rgba(36, 123, 160, 0.96), rgba(112, 193, 179, 0.95)),
            linear-gradient(135deg, #FFFFFF, #E9F8F4);
        border-radius: 24px;
        padding: 24px 28px;
        margin-bottom: 1.4rem;
        box-shadow: 0 20px 55px rgba(36, 123, 160, 0.20);
        position: relative;
        overflow: hidden;
    }
    .hero-panel::after {
        content: "";
        position: absolute;
        right: -38px;
        top: -38px;
        width: 170px;
        height: 170px;
        border-radius: 50%;
        background: rgba(255,255,255,0.12);
    }
    .hero-eyebrow {
        position: relative;
        z-index: 1;
        font-size: 0.78rem;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: rgba(255,255,255,0.78);
        margin-bottom: 10px;
        font-weight: 700;
    }
    .hero-title {
        position: relative;
        z-index: 1;
        font-size: 2rem;
        line-height: 1.1;
        font-weight: 800;
        color: #FFFFFF;
        margin-bottom: 8px;
    }
    .hero-description {
        position: relative;
        z-index: 1;
        font-size: 1rem;
        line-height: 1.65;
        color: rgba(255,255,255,0.88);
        max-width: 760px;
    }
    [data-testid="stMetric"] {
        background: linear-gradient(180deg, rgba(255,255,255,0.96) 0%, rgba(248,250,252,0.96) 100%);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 18px 18px 14px 18px;
        box-shadow: var(--shadow);
        min-height: 142px;
    }
    [data-testid="stMetricLabel"] p {
        color: var(--muted);
        font-weight: 600;
        letter-spacing: 0.01em;
    }
    [data-testid="stMetricValue"] {
        color: var(--ink);
        font-weight: 800;
    }
    [data-testid="stMetricDelta"] {
        font-size: 0.84rem;
        font-weight: 700;
    }
    .metric-delta-pos { color: var(--positive); font-size: 0.85rem; }
    .metric-delta-neg { color: var(--negative); font-size: 0.85rem; }
    .alerta-critica {
        background: linear-gradient(180deg, #FFF4F7 0%, #FFE8EF 100%);
        border: 1px solid rgba(255, 22, 84, 0.20);
        box-shadow: 0 18px 34px rgba(255, 22, 84, 0.10);
    }
    .alerta-alta {
        background: linear-gradient(180deg, #FFFCED 0%, #FFF8D3 100%);
        border: 1px solid rgba(138, 123, 31, 0.22);
        box-shadow: 0 18px 34px rgba(138, 123, 31, 0.10);
    }
    .alerta-critica, .alerta-alta, .resena-card {
        border-radius: 20px;
        padding: 18px;
        margin-bottom: 14px;
    }
    .alerta-header, .resena-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 16px;
        margin-bottom: 12px;
    }
    .alerta-title, .resena-title {
        color: var(--ink);
        font-weight: 700;
        font-size: 1rem;
    }
    .meta-text {
        font-size: 0.82rem;
        color: var(--muted);
        line-height: 1.5;
    }
    .alerta-body, .review-text {
        color: var(--ink);
        font-size: 0.97rem;
        line-height: 1.65;
        margin-bottom: 12px;
    }
    .alerta-summary, .review-summary {
        color: var(--muted);
        font-size: 0.86rem;
        line-height: 1.6;
    }
    .alerta-summary strong {
        color: var(--ink);
    }
    .alerta-action {
        background: var(--warning-bg);
        color: #6D430B;
        border: 1px solid rgba(183, 121, 31, 0.18);
        border-radius: 14px;
        padding: 12px 14px;
        margin-top: 12px;
        line-height: 1.55;
    }
    .alerta-footer {
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px solid rgba(91, 101, 122, 0.14);
    }
    .badge-positivo, .badge-negativo, .badge-neutral {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 5px 11px;
        border-radius: 999px;
        font-size: 0.74rem;
        font-weight: 700;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }
    .badge-positivo { background:#2E8D7E; color:#FFFFFF; }
    .badge-negativo { background:#FF1654; color:#FFFFFF; }
    .badge-neutral  { background:#247BA0; color:#FFFFFF; }
    .resena-card {
        background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(249,250,252,0.98) 100%);
        border: 1px solid var(--border);
        box-shadow: var(--shadow);
    }
    .section-title {
        font-size: 1.02rem;
        font-weight: 700;
        color: var(--ink);
        margin: 0 0 16px 0;
        padding: 0 0 10px 0;
        border-bottom: 1px solid rgba(36, 123, 160, 0.18);
    }
    .urgency-pill {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 6px 12px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 700;
    }
    .urgency-low {
        background: #E6F5F1;
        color: #256E63;
    }
    .urgency-medium {
        background: #FFF9DA;
        color: #80721B;
    }
    .urgency-high {
        background: #FFE8EF;
        color: #C11243;
    }
    .stButton > button, [data-testid="baseButton-secondary"] {
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
        color: #FFFFFF !important;
        border: none;
        border-radius: 14px;
        font-weight: 700;
        padding: 0.7rem 1rem;
        box-shadow: 0 12px 24px rgba(36, 123, 160, 0.24);
    }
    .stButton > button:hover {
        filter: brightness(1.03);
        transform: translateY(-1px);
    }
    div[data-baseweb="select"] > div,
    [data-baseweb="input"] > div,
    .stDateInput > div > div,
    .stTextInput > div > div {
        background: rgba(255,255,255,0.92);
        border: 1px solid var(--border);
        border-radius: 14px;
    }
    .stSlider [data-baseweb="slider"] {
        padding-top: 8px;
    }
    .stSlider [role="slider"] {
        background: var(--primary);
        border-color: var(--primary);
    }
    [data-testid="stDataFrame"] {
        border: 1px solid var(--border);
        border-radius: 18px;
        overflow: hidden;
        box-shadow: var(--shadow);
    }
    [data-testid="stAlert"] {
        border-radius: 16px;
        border: 1px solid var(--border);
        box-shadow: var(--shadow);
    }
    @media (max-width: 900px) {
        .hero-title {
            font-size: 1.65rem;
        }
        .alerta-header, .resena-header {
            flex-direction: column;
        }
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# CARGA DE DATOS
# ============================================================
OUTPUT_FILE = Path(__file__).parent / "voc_analysis_output.json"

@st.cache_data(ttl=300)  # cache 5 minutos
def cargar_datos():
    if not OUTPUT_FILE.exists():
        return None
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def delta_str(val):
    """Formatea variación con signo."""
    if val is None:
        return ""
    return f"+{val}%" if val >= 0 else f"{val}%"

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="sidebar-kicker">Intelligence Center</div>
        <div class="sidebar-title">VOC Analytics</div>
        <div class="sidebar-copy">Transformando el feedback disperso en insights estratégicos y señales accionables.</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    vista = st.radio(
        "Sección",
        ["Resumen ejecutivo", "Tendencias", "Alertas críticas",
         "Por categoría", "Explorador de reseñas"],
        label_visibility="collapsed"
    )
    st.divider()

    if st.button("🔄 Actualizar datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    datos = cargar_datos()
    if datos:
        fecha = datos.get("metadata", {}).get("fecha_analisis", "")[:16].replace("T", " ")
        st.caption(f"Último análisis: {fecha}")

# ============================================================
# VERIFICAR DATOS
# ============================================================
if not datos:
    st.error("⚠️ No se encontró `voc_analysis_output.json`.")
    st.info("Ejecuta primero `python voc_analysis.py` para generar el archivo de análisis.")
    st.stop()

kpis        = datos.get("kpis_globales", {})
categorias  = datos.get("por_categoria", [])
tendencias  = datos.get("tendencias", {})
alertas     = datos.get("alertas_criticas", [])
entidades   = datos.get("top_entidades", [])
comparativa = datos.get("comparativa_semanal", {})
recientes   = datos.get("resenas_recientes", [])

# ============================================================
# VISTA 1: RESUMEN EJECUTIVO
# ============================================================
if vista == "Resumen ejecutivo":
    render_page_header(
        "📊 Resumen ejecutivo",
        f"Visión consolidada de desempeño, sentimiento y volumen sobre {kpis.get('total_resenas', 0)} reseñas analizadas.",
        "Panel principal"
    )
    st.divider()

    # KPIs principales
    col1, col2, col3, col4, col5 = st.columns(5)

    comp_var = comparativa.get("variaciones", {})

    with col1:
        st.metric(
            "Total reseñas",
            kpis.get("total_resenas", 0),
            delta=delta_str(comp_var.get("total")),
            help="Total de reseñas procesadas con IA"
        )
    with col2:
        nps = kpis.get("nps_estimado")
        st.metric(
            "NPS estimado",
            f"{nps}" if nps is not None else "N/A",
            delta=delta_str(comp_var.get("nps")),
            help="Net Promoter Score estimado (escala -100 a 100)"
        )
    with col3:
        st.metric(
            "Tasa positiva",
            f"{kpis.get('tasa_positiva_pct', 0)}%",
            delta=delta_str(comp_var.get("positivos_pct")),
            help="% de reseñas con sentimiento positivo"
        )
    with col4:
        avg = kpis.get("avg_rating")
        st.metric(
            "Rating promedio",
            f"{avg} ⭐" if avg else "N/A",
            help="Calificación promedio (1-5 estrellas)"
        )
    with col5:
        alertas_n = kpis.get("alertas_activas", 0)
        st.metric(
            "Alertas activas",
            alertas_n,
            delta=delta_str(comp_var.get("alertas")),
            delta_color="inverse",
            help="Reseñas con urgencia ≥ 4 que requieren acción"
        )

    st.divider()
    col_l, col_r = st.columns([3, 2])

    with col_l:
        st.markdown('<div class="section-title">Distribución de sentimiento</div>',
                    unsafe_allow_html=True)
        if categorias:
            df_cat = pd.DataFrame(categorias)
            labels_wrapped = wrap_axis_labels(df_cat["label"], width=12)
            fig = go.Figure()
            fig.add_trace(go.Bar(
                name="Positivo", x=labels_wrapped,
                y=df_cat["positivos"], marker_color=COLORS["positive"]
            ))
            fig.add_trace(go.Bar(
                name="Neutral", x=labels_wrapped,
                y=df_cat["neutrales"], marker_color=COLORS["neutral"]
            ))
            fig.add_trace(go.Bar(
                name="Negativo", x=labels_wrapped,
                y=df_cat["negativos"], marker_color=COLORS["negative"]
            ))
            fig.update_layout(barmode="stack")
            style_figure(fig, height=360, legend_y=-0.2)
            fig.update_xaxes(tickangle=0, tickfont=dict(size=11, color=COLORS["muted"]))
            st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown('<div class="section-title">Categorías más frecuentes</div>',
                    unsafe_allow_html=True)
        if categorias:
            df_cat = pd.DataFrame(categorias)
            fig2 = px.pie(
                df_cat, values="total", names="label",
                color_discrete_sequence=PIE_COLORS,
                hole=0.4
            )
            fig2.update_traces(
                textposition="inside",
                textinfo="percent",
                marker=dict(line=dict(color="#FFFFFF", width=2))
            )
            style_figure(fig2, height=360, legend_orientation="v", legend_y=1)
            fig2.update_layout(showlegend=True, legend=dict(x=1.02, y=1))
            st.plotly_chart(fig2, use_container_width=True)

    # Categorías escalando
    escalando = tendencias.get("categorias_escalando", [])
    if escalando:
        st.divider()
        st.markdown("### ⚠️ Categorías con tendencia negativa creciente")
        for e in escalando:
            st.warning(
                f"**{e['label']}** — negativos esta semana: {e['neg_actual']} "
                f"(+{e['variacion_pct']}% vs semana anterior)"
            )

    # Top entidades
    if entidades:
        st.divider()
        st.markdown('<div class="section-title">Entidades más mencionadas</div>',
                    unsafe_allow_html=True)
        df_ent = pd.DataFrame(entidades[:10])
        fig3 = px.bar(
            df_ent, x="menciones", y="entidad",
            orientation="h",
            color="menciones",
            color_continuous_scale=PURPLE_SCALE
        )
        style_figure(fig3, height=320)
        fig3.update_layout(coloraxis_showscale=False, yaxis_title="", xaxis_title="menciones")
        st.plotly_chart(fig3, use_container_width=True)


# ============================================================
# VISTA 2: TENDENCIAS
# ============================================================
elif vista == "Tendencias":
    render_page_header(
        "📈 Tendencias semanales",
        "Compara la evolución del sentimiento y detecta señales tempranas de deterioro por periodo.",
        "Análisis temporal"
    )
    st.divider()

    por_semana = tendencias.get("por_semana", [])
    if not por_semana:
        st.info("Necesitas al menos 2 semanas de datos para ver tendencias.")
    else:
        df_sem = pd.DataFrame(por_semana)
        st.markdown('<div class="section-title">Evolución de sentimiento por semana</div>',
                    unsafe_allow_html=True)

        # Línea de tendencia
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_sem["semana"], y=df_sem["positivos"],
            name="Positivos", line=dict(color=COLORS["positive"], width=3),
            mode="lines+markers"
        ))
        fig.add_trace(go.Scatter(
            x=df_sem["semana"], y=df_sem["negativos"],
            name="Negativos", line=dict(color=COLORS["negative"], width=3),
            mode="lines+markers"
        ))
        fig.add_trace(go.Scatter(
            x=df_sem["semana"], y=df_sem["neutrales"],
            name="Neutrales", line=dict(color=COLORS["neutral"], width=2.2, dash="dot"),
            mode="lines+markers"
        ))
        style_figure(fig, height=380, legend_y=-0.15)
        fig.update_xaxes(tickangle=0)
        st.plotly_chart(fig, use_container_width=True)

        # Comparativa semana actual vs anterior
        if comparativa:
            st.divider()
            st.markdown("### Semana actual vs semana anterior")
            col1, col2 = st.columns(2)
            actual   = comparativa.get("actual", {})
            anterior = comparativa.get("anterior", {})
            var      = comparativa.get("variaciones", {})

            with col1:
                st.markdown(f"**Semana actual** ({comparativa.get('semana_actual', '')})")
                st.metric("Reseñas", actual.get("total", 0),
                          delta=delta_str(var.get("total")))
                st.metric("Positivas", f"{actual.get('positivos_pct', 0)}%",
                          delta=delta_str(var.get("positivos_pct")))
                st.metric("Negativas", f"{actual.get('negativos_pct', 0)}%",
                          delta=delta_str(var.get("negativos_pct")),
                          delta_color="inverse")

            with col2:
                st.markdown(f"**Semana anterior** ({comparativa.get('semana_anterior', '')})")
                st.metric("Reseñas", anterior.get("total", 0))
                st.metric("Positivas", f"{anterior.get('positivos_pct', 0)}%")
                st.metric("Negativas", f"{anterior.get('negativos_pct', 0)}%")

    # Categorías escalando
    escalando = tendencias.get("categorias_escalando", [])
    if escalando:
        st.divider()
        st.markdown("### 🚨 Categorías escalando — requieren atención")
        for e in escalando:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.error(f"**{e['label']}**")
            with col2:
                st.metric("Esta semana", e["neg_actual"])
            with col3:
                st.metric("Semana anterior", e["neg_anterior"],
                          delta=f"+{e['variacion_pct']}%", delta_color="inverse")


# ============================================================
# VISTA 3: ALERTAS CRÍTICAS
# ============================================================
elif vista == "Alertas críticas":
    render_page_header(
        "🚨 Alertas críticas",
        f"Prioriza reseñas con urgencia alta y acelera la respuesta sobre los {len(alertas)} casos activos detectados por IA.",
        "Respuesta inmediata"
    )
    st.divider()

    if not alertas:
        st.success("✅ Sin alertas críticas activas. ¡Buenas noticias!")
    else:
        for a in alertas:
            clase = "alerta-critica" if a["score_urgencia"] == 5 else "alerta-alta"
            icono = "🚨" if a["score_urgencia"] == 5 else "⚠️"
            st.markdown(f"""
            <div class="{clase}">
                <div class="alerta-header">
                    <div class="alerta-title">{icono} {a.get('label','')}</div>
                    <div class="meta-text">{a.get('fuente','')} · {a.get('fecha_resena','')[:10]}</div>
                </div>
                <div class="alerta-body">
                    "{a.get('texto_original','')[:280]}..."
                </div>
                <div class="alerta-summary">
                    <strong>Resumen IA:</strong> {a.get('resumen_ia','')}
                </div>
                <div class="alerta-action">
                    <strong>👉 Acción sugerida:</strong> {a.get('accion_sugerida','')}
                </div>
                <div class="alerta-footer meta-text">
                    Urgencia: {a.get('score_urgencia','')}/5 · Autor: {a.get('autor','')}
                    {' · Entidades: ' + a.get('entidades_clave','') if a.get('entidades_clave') else ''}
                </div>
            </div>
            """, unsafe_allow_html=True)


# ============================================================
# VISTA 4: POR CATEGORÍA
# ============================================================
elif vista == "Por categoría":
    render_page_header(
        "🏷️ Análisis por categoría",
        "Identifica dónde se concentra el volumen, la urgencia y los principales focos de fricción del journey.",
        "Segmentación"
    )
    st.divider()

    if not categorias:
        st.info("Sin datos por categoría aún.")
    else:
        df_cat = pd.DataFrame(categorias)

        # Tabla resumen
        st.markdown('<div class="section-title">Resumen por categoría</div>',
                    unsafe_allow_html=True)
        df_display = df_cat[["label","total","positivos","neutrales","negativos",
                              "avg_urgencia","pct_del_total"]].copy()
        df_display.columns = ["Categoría","Total","Positivos","Neutrales",
                               "Negativos","Urgencia prom.","% del total"]
        st.dataframe(df_display, use_container_width=True, hide_index=True)

        st.divider()
        col1, col2 = st.columns(2)

        with col1:
            st.markdown('<div class="section-title">Urgencia promedio por categoría</div>',
                        unsafe_allow_html=True)
            fig = px.bar(
                df_cat.sort_values("avg_urgencia", ascending=True),
                x="avg_urgencia", y="label", orientation="h",
                color="avg_urgencia",
                color_continuous_scale=URGENCY_SCALE,
                range_color=[1, 5]
            )
            style_figure(fig, height=330)
            fig.update_layout(coloraxis_showscale=False, yaxis_title="", xaxis_title="urgencia promedio")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown('<div class="section-title">Volumen por categoría</div>',
                        unsafe_allow_html=True)
            fig2 = px.bar(
                df_cat.sort_values("total", ascending=True),
                x="total", y="label", orientation="h",
                color="total", color_continuous_scale=PURPLE_SCALE
            )
            style_figure(fig2, height=330)
            fig2.update_layout(coloraxis_showscale=False, yaxis_title="", xaxis_title="total reseñas")
            st.plotly_chart(fig2, use_container_width=True)


# ============================================================
# VISTA 5: EXPLORADOR DE RESEÑAS
# ============================================================
elif vista == "Explorador de reseñas":
    render_page_header(
        "🔍 Explorador de reseñas",
        "Filtra conversaciones recientes y revisa el contexto exacto detrás de cada señal de experiencia.",
        "Detalle operativo"
    )
    st.divider()

    # Filtros
    col1, col2, col3 = st.columns(3)
    with col1:
        filtro_sentimiento = st.multiselect(
            "Sentimiento",
            ["positivo", "neutral", "negativo"],
            default=["positivo", "neutral", "negativo"]
        )
    with col2:
        todas_cats = list(set([r["categoria"] for r in recientes]))
        filtro_cat = st.multiselect(
            "Categoría",
            todas_cats,
            default=todas_cats
        )
    with col3:
        filtro_urgencia = st.slider("Urgencia mínima", 1, 5, 1)

    # Filtrar
    filtradas = [
        r for r in recientes
        if r.get("sentimiento") in filtro_sentimiento
        and r.get("categoria") in filtro_cat
        and (r.get("score_urgencia") or 0) >= filtro_urgencia
    ]

    st.markdown(f"**{len(filtradas)} reseñas** coinciden con los filtros")
    st.divider()

    for r in filtradas:
        sent = r.get("sentimiento", "neutral")
        badge_class = f"badge-{sent}"
        urgencia = r.get("score_urgencia", 0)
        urgency_class = "urgency-high" if urgencia >= 4 else ("urgency-medium" if urgencia == 3 else "urgency-low")

        st.markdown(f"""
        <div class="resena-card">
            <div class="resena-header">
                <div>
                    <span class="{badge_class}">{sent}</span>
                    <span class="meta-text" style="margin-left:10px">{r.get('label','')}</span>
                </div>
                <div class="meta-text">
                    {r.get('fuente','')} · {r.get('fecha_resena','')[:10]}
                    <span class="urgency-pill {urgency_class}" style="margin-left:10px">
                        Urgencia {urgencia}/5
                    </span>
                </div>
            </div>
            <div class="review-text">
                {r.get('texto_original','')[:300]}{'...' if len(r.get('texto_original','')) > 300 else ''}
            </div>
            <div class="review-summary">
                <em>{r.get('resumen_ia','')}</em>
                {' · ' + r.get('autor','') if r.get('autor') != 'Anónimo' else ''}
            </div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# FOOTER
# ============================================================
st.divider()
st.caption("VOC Intelligence System · Análisis de Datos con IA · Generado por el Motor de Análisis NLP")
