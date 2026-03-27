"""
VOC Pipeline — Etapa 5: Dashboard Streamlit
LOGYCA / LAB

Ejecutar: streamlit run dashboard.py
Deploy gratis: streamlit.io/cloud
"""

import json
import os
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ============================================================
# CONFIGURACIÓN DE PÁGINA
# ============================================================
st.set_page_config(
    page_title="VOC Dashboard — LOGYCA/LAB",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# ESTILOS
# ============================================================
st.markdown("""
<style>
    .metric-card {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 20px;
        border-left: 4px solid #6C5CE7;
        margin-bottom: 10px;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #2d3436;
        line-height: 1;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #636e72;
        margin-top: 4px;
    }
    .metric-delta-pos { color: #00b894; font-size: 0.85rem; }
    .metric-delta-neg { color: #d63031; font-size: 0.85rem; }
    .alerta-critica {
        background: #fff5f5;
        border-left: 4px solid #d63031;
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 10px;
    }
    .alerta-alta {
        background: #fffbf0;
        border-left: 4px solid #e17055;
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 10px;
    }
    .badge-positivo { background:#00b894; color:white; padding:2px 8px; border-radius:12px; font-size:0.75rem; }
    .badge-negativo { background:#d63031; color:white; padding:2px 8px; border-radius:12px; font-size:0.75rem; }
    .badge-neutral  { background:#636e72; color:white; padding:2px 8px; border-radius:12px; font-size:0.75rem; }
    .resena-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 14px;
        margin-bottom: 8px;
    }
    .section-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #2d3436;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 2px solid #6C5CE7;
    }
    [data-testid="stMetricDelta"] { font-size: 0.8rem; }
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
    st.image("https://logyca.org/sites/default/files/inline-images/logo-logyca-lab.png",
             width=160)
    st.markdown("## VOC Dashboard")
    st.markdown("**LOGYCA / LAB**")
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
    st.markdown("# 📊 Resumen ejecutivo")
    st.markdown(f"**LOGYCA / LAB** · {kpis.get('total_resenas', 0)} reseñas analizadas")
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
            fig = go.Figure()
            fig.add_trace(go.Bar(
                name="Positivo", x=df_cat["label"],
                y=df_cat["positivos"], marker_color="#00b894"
            ))
            fig.add_trace(go.Bar(
                name="Neutral", x=df_cat["label"],
                y=df_cat["neutrales"], marker_color="#b2bec3"
            ))
            fig.add_trace(go.Bar(
                name="Negativo", x=df_cat["label"],
                y=df_cat["negativos"], marker_color="#d63031"
            ))
            fig.update_layout(
                barmode="stack", height=320,
                margin=dict(l=0, r=0, t=10, b=0),
                legend=dict(orientation="h", y=-0.2),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
            )
            fig.update_xaxes(tickangle=-30)
            st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown('<div class="section-title">Categorías más frecuentes</div>',
                    unsafe_allow_html=True)
        if categorias:
            df_cat = pd.DataFrame(categorias)
            fig2 = px.pie(
                df_cat, values="total", names="label",
                color_discrete_sequence=px.colors.qualitative.Set3,
                hole=0.4
            )
            fig2.update_layout(
                height=320, margin=dict(l=0, r=0, t=10, b=0),
                showlegend=True,
                legend=dict(orientation="v", x=1.0),
                paper_bgcolor="rgba(0,0,0,0)"
            )
            fig2.update_traces(textposition="inside", textinfo="percent")
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
            color_continuous_scale="Purples"
        )
        fig3.update_layout(
            height=300, margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            coloraxis_showscale=False, yaxis_title="", xaxis_title="menciones"
        )
        st.plotly_chart(fig3, use_container_width=True)


# ============================================================
# VISTA 2: TENDENCIAS
# ============================================================
elif vista == "Tendencias":
    st.markdown("# 📈 Tendencias semanales")
    st.divider()

    por_semana = tendencias.get("por_semana", [])
    if not por_semana:
        st.info("Necesitas al menos 2 semanas de datos para ver tendencias.")
    else:
        df_sem = pd.DataFrame(por_semana)

        # Línea de tendencia
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_sem["semana"], y=df_sem["positivos"],
            name="Positivos", line=dict(color="#00b894", width=2.5),
            mode="lines+markers"
        ))
        fig.add_trace(go.Scatter(
            x=df_sem["semana"], y=df_sem["negativos"],
            name="Negativos", line=dict(color="#d63031", width=2.5),
            mode="lines+markers"
        ))
        fig.add_trace(go.Scatter(
            x=df_sem["semana"], y=df_sem["neutrales"],
            name="Neutrales", line=dict(color="#b2bec3", width=1.5, dash="dot"),
            mode="lines+markers"
        ))
        fig.update_layout(
            title="Evolución de sentimiento por semana",
            height=380, margin=dict(l=0, r=0, t=40, b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", y=-0.15),
            xaxis=dict(tickangle=-30)
        )
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
    st.markdown("# 🚨 Alertas críticas")
    st.markdown(f"Reseñas con urgencia ≥ 4 que requieren acción inmediata — **{len(alertas)} activas**")
    st.divider()

    if not alertas:
        st.success("✅ Sin alertas críticas activas. ¡Buenas noticias!")
    else:
        for a in alertas:
            clase = "alerta-critica" if a["score_urgencia"] == 5 else "alerta-alta"
            icono = "🚨" if a["score_urgencia"] == 5 else "⚠️"
            st.markdown(f"""
            <div class="{clase}">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                    <strong>{icono} {a.get('label','')}</strong>
                    <span style="font-size:0.8rem;color:#636e72">{a.get('fuente','')} · {a.get('fecha_resena','')[:10]}</span>
                </div>
                <div style="font-size:0.95rem;margin-bottom:8px;color:#2d3436">
                    "{a.get('texto_original','')[:280]}..."
                </div>
                <div style="margin-bottom:6px">
                    <strong>Resumen IA:</strong> {a.get('resumen_ia','')}
                </div>
                <div style="background:#fff3cd;border-radius:6px;padding:8px;margin-top:8px">
                    <strong>👉 Acción sugerida:</strong> {a.get('accion_sugerida','')}
                </div>
                <div style="margin-top:8px;font-size:0.8rem;color:#636e72">
                    Urgencia: {a.get('score_urgencia','')}/5 · Autor: {a.get('autor','')}
                    {' · Entidades: ' + a.get('entidades_clave','') if a.get('entidades_clave') else ''}
                </div>
            </div>
            """, unsafe_allow_html=True)


# ============================================================
# VISTA 4: POR CATEGORÍA
# ============================================================
elif vista == "Por categoría":
    st.markdown("# 🏷️ Análisis por categoría")
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
                color_continuous_scale=["#00b894","#fdcb6e","#d63031"],
                range_color=[1, 5]
            )
            fig.update_layout(
                height=320, margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                coloraxis_showscale=False, yaxis_title="", xaxis_title="urgencia promedio"
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown('<div class="section-title">Volumen por categoría</div>',
                        unsafe_allow_html=True)
            fig2 = px.bar(
                df_cat.sort_values("total", ascending=True),
                x="total", y="label", orientation="h",
                color="total", color_continuous_scale="Purples"
            )
            fig2.update_layout(
                height=320, margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                coloraxis_showscale=False, yaxis_title="", xaxis_title="total reseñas"
            )
            st.plotly_chart(fig2, use_container_width=True)


# ============================================================
# VISTA 5: EXPLORADOR DE RESEÑAS
# ============================================================
elif vista == "Explorador de reseñas":
    st.markdown("# 🔍 Explorador de reseñas")
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
        urgencia_color = "#d63031" if urgencia >= 4 else ("#e17055" if urgencia == 3 else "#00b894")

        st.markdown(f"""
        <div class="resena-card">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                <div>
                    <span class="{badge_class}">{sent}</span>
                    <span style="margin-left:8px;font-size:0.8rem;color:#636e72">{r.get('label','')}</span>
                </div>
                <div style="font-size:0.8rem;color:#636e72">
                    {r.get('fuente','')} · {r.get('fecha_resena','')[:10]}
                    <span style="margin-left:8px;color:{urgencia_color};font-weight:600">
                        urgencia {urgencia}/5
                    </span>
                </div>
            </div>
            <div style="font-size:0.95rem;color:#2d3436;margin-bottom:8px">
                {r.get('texto_original','')[:300]}{'...' if len(r.get('texto_original','')) > 300 else ''}
            </div>
            <div style="font-size:0.82rem;color:#636e72">
                <em>{r.get('resumen_ia','')}</em>
                {' · ' + r.get('autor','') if r.get('autor') != 'Anónimo' else ''}
            </div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# FOOTER
# ============================================================
st.divider()
st.caption("VOC Pipeline · LOGYCA/LAB · Análisis automático con IA · Datos actualizados diariamente")
