"""
VOC Pipeline — Motor de Análisis de Datos (NLP + Pandas)

Este módulo es el núcleo del procesamiento del sistema Voice of Customer (VOC).
Se encarga de:
1. Conectar con las fuentes de datos (Google Sheets/Master Sheet).
2. Limpiar y normalizar los datos crudos.
3. Calcular KPIs estratégicos (NPS, Sentimiento, Urgencia).
4. Generar análisis de tendencias temporales y por categoría.
5. Exportar los resultados a un formato JSON optimizado para el dashboard y reportes.

Output: voc_analysis_output.json
"""

import json
import os
import warnings
from datetime import datetime, timedelta
from pathlib import Path

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

warnings.filterwarnings("ignore")

# ============================================================
# CONFIGURACIÓN GLOBAL
# ============================================================
MASTER_SHEET_ID  = os.environ.get("MASTER_SHEET_ID", "TU_MASTER_SHEET_ID")
CREDENTIALS_FILE = os.environ.get("GOOGLE_CREDENTIALS_FILE", "credentials.json")
OUTPUT_FILE      = Path(__file__).parent / "voc_analysis_output.json"
PLATAFORMA       = "VOC Intelligence System"

# Categorías de análisis para segmentación del feedback
CATEGORIAS_VALIDAS = [
    "experiencia_cliente",
    "calidad_producto",
    "soporte_tecnico",
    "logistica_entrega",
    "valor_precio",
    "usabilidad",
    "atencion_cliente",
    "otro"
]

CATEGORIAS_LABELS = {
    "experiencia_cliente": "Experiencia General",
    "calidad_producto":    "Calidad de Producto/Servicio",
    "soporte_tecnico":     "Soporte Técnico",
    "logistica_entrega":   "Logística y Entrega",
    "valor_precio":        "Valor Percibido",
    "usabilidad":          "Interfaz y Usabilidad",
    "atencion_cliente":    "Atención al Cliente",
    "otro":                "Otros Temas"
}


# ============================================================
# 1. CARGA DE DATOS
# ============================================================
def cargar_master_sheet():
    """Conecta a Google Sheets y retorna DataFrame del Master."""
    print(f"[VOC] Conectando a Master Sheet: {MASTER_SHEET_ID}")

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds  = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scope)
    client = gspread.authorize(creds)
    sheet  = client.open_by_key(MASTER_SHEET_ID).worksheet("Master")
    data   = sheet.get_all_records()
    df     = pd.DataFrame(data)

    print(f"[VOC] Filas cargadas: {len(df)}")
    return df


def limpiar_df(df):
    """Normaliza tipos y filtra solo reseñas procesadas."""
    if df.empty:
        return df

    # Solo filas procesadas (con análisis IA completo)
    df = df[df["estado_procesado"] == "procesado"].copy()

    # Tipos
    df["fecha_resena"]          = pd.to_datetime(df["fecha_resena"],          errors="coerce")
    df["fecha_ingesta"]         = pd.to_datetime(df["fecha_ingesta"],          errors="coerce")
    df["calificacion_estrella"] = pd.to_numeric(df["calificacion_estrella"],   errors="coerce")
    df["score_urgencia"]        = pd.to_numeric(df["score_urgencia"],           errors="coerce")

    # Normalizar categorías
    df["categoria"] = df["categoria"].str.strip().str.lower()
    df.loc[~df["categoria"].isin(CATEGORIAS_VALIDAS), "categoria"] = "otro"

    # Semana de ingesta (para tendencias)
    df["semana"] = df["fecha_ingesta"].dt.to_period("W").astype(str)

    print(f"[VOC] Filas procesadas válidas: {len(df)}")
    return df


# ============================================================
# 2. KPIs GLOBALES
# ============================================================
def calcular_kpis(df):
    """Calcula los KPIs del resumen ejecutivo."""
    if df.empty:
        return {}

    total = len(df)

    # Distribución de sentimiento
    sentiment_counts = df["sentimiento"].value_counts().to_dict()
    positivos  = sentiment_counts.get("positivo", 0)
    negativos  = sentiment_counts.get("negativo", 0)
    neutrales  = sentiment_counts.get("neutral",  0)

    # NPS estimado (escala 1-5 → NPS aproximado)
    # Promotores: 5 estrellas, Detractores: 1-2, Pasivos: 3-4
    df_con_rating = df[df["calificacion_estrella"].notna()]
    if len(df_con_rating) > 0:
        promotores  = len(df_con_rating[df_con_rating["calificacion_estrella"] == 5])
        detractores = len(df_con_rating[df_con_rating["calificacion_estrella"] <= 2])
        n_rating    = len(df_con_rating)
        nps_estimado = round(((promotores - detractores) / n_rating) * 100, 1)
        avg_rating   = round(df_con_rating["calificacion_estrella"].mean(), 2)
    else:
        nps_estimado = None
        avg_rating   = None

    # Alertas activas (urgencia >= 4)
    alertas_activas = len(df[df["score_urgencia"] >= 4])
    criticas        = len(df[df["score_urgencia"] == 5])

    # Tasa de respuesta positiva
    tasa_positiva = round((positivos / total) * 100, 1) if total > 0 else 0

    return {
        "total_resenas":      total,
        "positivos":          positivos,
        "negativos":          negativos,
        "neutrales":          neutrales,
        "tasa_positiva_pct":  tasa_positiva,
        "nps_estimado":       nps_estimado,
        "avg_rating":         avg_rating,
        "alertas_activas":    alertas_activas,
        "alertas_criticas":   criticas,
        "fecha_analisis":     datetime.now().isoformat()
    }


# ============================================================
# 3. ANÁLISIS POR CATEGORÍA
# ============================================================
def analisis_por_categoria(df):
    """Desglose de sentimiento y urgencia por categoría."""
    if df.empty:
        return []

    resultado = []
    for cat in CATEGORIAS_VALIDAS:
        subset = df[df["categoria"] == cat]
        if len(subset) == 0:
            continue

        sentiment_dist = subset["sentimiento"].value_counts().to_dict()
        avg_urgencia   = round(subset["score_urgencia"].mean(), 2) if len(subset) > 0 else 0

        resultado.append({
            "categoria":       cat,
            "label":           CATEGORIAS_LABELS.get(cat, cat),
            "total":           len(subset),
            "positivos":       sentiment_dist.get("positivo", 0),
            "neutrales":       sentiment_dist.get("neutral",  0),
            "negativos":       sentiment_dist.get("negativo", 0),
            "avg_urgencia":    avg_urgencia,
            "pct_del_total":   round((len(subset) / len(df)) * 100, 1)
        })

    # Ordenar por total descendente
    resultado.sort(key=lambda x: x["total"], reverse=True)
    return resultado


# ============================================================
# 4. TENDENCIAS SEMANALES
# ============================================================
def calcular_tendencias(df):
    """
    Detecta tendencias por categoría semana a semana.
    Marca como 'escalando' si los negativos crecen > 20% vs semana anterior.
    """
    if df.empty or "semana" not in df.columns:
        return {"por_semana": [], "categorias_escalando": []}

    # Últimas 8 semanas
    semanas = sorted(df["semana"].dropna().unique())[-8:]
    df_rec  = df[df["semana"].isin(semanas)]

    # Pivot: semana x categoría x sentimiento
    por_semana = []
    for semana in semanas:
        subset = df_rec[df_rec["semana"] == semana]
        fila   = {"semana": semana, "total": len(subset)}
        sent   = subset["sentimiento"].value_counts().to_dict()
        fila.update({
            "positivos": sent.get("positivo", 0),
            "neutrales": sent.get("neutral",  0),
            "negativos": sent.get("negativo", 0),
        })
        por_semana.append(fila)

    # Detectar categorías escalando (negativos +20% vs semana anterior)
    categorias_escalando = []
    if len(semanas) >= 2:
        sem_actual   = semanas[-1]
        sem_anterior = semanas[-2]

        for cat in CATEGORIAS_VALIDAS:
            neg_actual   = len(df[(df["semana"] == sem_actual)   & (df["categoria"] == cat) & (df["sentimiento"] == "negativo")])
            neg_anterior = len(df[(df["semana"] == sem_anterior) & (df["categoria"] == cat) & (df["sentimiento"] == "negativo")])

            if neg_anterior > 0:
                variacion = ((neg_actual - neg_anterior) / neg_anterior) * 100
                if variacion >= 20:
                    categorias_escalando.append({
                        "categoria":    cat,
                        "label":        CATEGORIAS_LABELS.get(cat, cat),
                        "neg_actual":   neg_actual,
                        "neg_anterior": neg_anterior,
                        "variacion_pct": round(variacion, 1)
                    })

    return {
        "por_semana":             por_semana,
        "categorias_escalando":   categorias_escalando
    }


# ============================================================
# 5. ALERTAS CRÍTICAS (para el reporte ejecutivo)
# ============================================================
def extraer_alertas(df):
    """Extrae reseñas con urgencia >= 4 para el panel de problemas críticos."""
    if df.empty:
        return []

    alertas = df[df["score_urgencia"] >= 4].copy()
    alertas = alertas.sort_values("score_urgencia", ascending=False)

    resultado = []
    for _, row in alertas.iterrows():
        resultado.append({
            "id":              row.get("id", ""),
            "texto_original":  str(row.get("texto_original", ""))[:500],
            "fuente":          row.get("fuente", ""),
            "categoria":       row.get("categoria", ""),
            "label":           CATEGORIAS_LABELS.get(row.get("categoria", ""), ""),
            "sentimiento":     row.get("sentimiento", ""),
            "score_urgencia":  int(row.get("score_urgencia", 0)),
            "resumen_ia":      row.get("resumen_ia", ""),
            "accion_sugerida": row.get("accion_sugerida", ""),
            "entidades_clave": row.get("entidades_clave", ""),
            "fecha_resena":    str(row.get("fecha_resena", ""))[:10],
            "autor":           row.get("autor", "Anónimo")
        })

    return resultado


# ============================================================
# 6. TOP ENTIDADES MENCIONADAS
# ============================================================
def top_entidades(df, top_n=15):
    """Extrae las entidades más mencionadas en todo el corpus."""
    if df.empty:
        return []

    from collections import Counter
    todas = []
    for entidades in df["entidades_clave"].dropna():
        items = [e.strip() for e in str(entidades).split(",") if e.strip() and e.strip() != ""]
        todas.extend(items)

    counter = Counter(todas)
    return [{"entidad": k, "menciones": v} for k, v in counter.most_common(top_n)]


# ============================================================
# 7. COMPARATIVA SEMANA ACTUAL VS ANTERIOR
# ============================================================
def comparativa_semanal(df):
    """KPIs de la semana actual vs la semana anterior."""
    if df.empty:
        return {}

    semanas = sorted(df["semana"].dropna().unique())
    if len(semanas) < 2:
        return {}

    sem_actual   = semanas[-1]
    sem_anterior = semanas[-2]

    def kpis_semana(semana):
        sub   = df[df["semana"] == semana]
        total = len(sub)
        if total == 0:
            return {"total": 0, "nps": None, "positivos_pct": 0}
        pos = len(sub[sub["sentimiento"] == "positivo"])
        neg = len(sub[sub["sentimiento"] == "negativo"])
        rat = sub["calificacion_estrella"].dropna()
        prom = len(rat[rat == 5])
        detr = len(rat[rat <= 2])
        nps  = round(((prom - detr) / len(rat)) * 100, 1) if len(rat) > 0 else None
        return {
            "total":          total,
            "positivos":      pos,
            "negativos":      neg,
            "positivos_pct":  round((pos / total) * 100, 1),
            "negativos_pct":  round((neg / total) * 100, 1),
            "nps":            nps,
            "alertas":        len(sub[sub["score_urgencia"] >= 4])
        }

    actual   = kpis_semana(sem_actual)
    anterior = kpis_semana(sem_anterior)

    # Variaciones
    def variacion(a, b, key):
        va, vb = a.get(key), b.get(key)
        if va is None or vb is None or vb == 0:
            return None
        return round(((va - vb) / abs(vb)) * 100, 1)

    return {
        "semana_actual":    sem_actual,
        "semana_anterior":  sem_anterior,
        "actual":           actual,
        "anterior":         anterior,
        "variaciones": {
            "total":         variacion(actual, anterior, "total"),
            "positivos_pct": variacion(actual, anterior, "positivos_pct"),
            "negativos_pct": variacion(actual, anterior, "negativos_pct"),
            "nps":           variacion(actual, anterior, "nps"),
            "alertas":       variacion(actual, anterior, "alertas")
        }
    }


# ============================================================
# 8. MUESTRA DE RESEÑAS RECIENTES (para el dashboard)
# ============================================================
def resenas_recientes(df, n=20):
    """Últimas N reseñas procesadas para mostrar en el dashboard."""
    if df.empty:
        return []

    recientes = df.sort_values("fecha_ingesta", ascending=False).head(n)
    resultado = []
    for _, row in recientes.iterrows():
        resultado.append({
            "id":              row.get("id", ""),
            "texto_original":  str(row.get("texto_original", ""))[:300],
            "fuente":          row.get("fuente", ""),
            "categoria":       row.get("categoria", ""),
            "label":           CATEGORIAS_LABELS.get(row.get("categoria", ""), ""),
            "sentimiento":     row.get("sentimiento", ""),
            "score_urgencia":  int(row.get("score_urgencia", 0) or 0),
            "resumen_ia":      row.get("resumen_ia", ""),
            "calificacion":    row.get("calificacion_estrella", ""),
            "fecha_resena":    str(row.get("fecha_resena", ""))[:10],
            "autor":           row.get("autor", "Anónimo")
        })
    return resultado


# ============================================================
# MAIN
# ============================================================
def main():
    print(f"\n{'='*50}")
    print(f"VOC Pipeline — Motor de Inteligencia")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}\n")

    # Cargar y limpiar datos
    df_raw = cargar_master_sheet()
    df     = limpiar_df(df_raw)

    if df.empty:
        print("[VOC] No hay reseñas procesadas. Saliendo.")
        return

    # Calcular todo
    output = {
        "metadata": {
            "plataforma":      PLATAFORMA,
            "fecha_analisis":  datetime.now().isoformat(),
            "total_procesadas": len(df)
        },
        "kpis_globales":       calcular_kpis(df),
        "por_categoria":       analisis_por_categoria(df),
        "tendencias":          calcular_tendencias(df),
        "alertas_criticas":    extraer_alertas(df),
        "top_entidades":       top_entidades(df),
        "comparativa_semanal": comparativa_semanal(df),
        "resenas_recientes":   resenas_recientes(df)
    }

    # Guardar JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n[VOC] ✓ Análisis completado")
    print(f"[VOC] ✓ KPIs: {output['kpis_globales']['total_resenas']} reseñas | NPS: {output['kpis_globales']['nps_estimado']} | Alertas: {output['kpis_globales']['alertas_activas']}")
    print(f"[VOC] ✓ Output guardado en: {OUTPUT_FILE}")
    print(f"[VOC] ✓ Categorías escalando: {len(output['tendencias']['categorias_escalando'])}")


if __name__ == "__main__":
    main()
