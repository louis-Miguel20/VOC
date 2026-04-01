"""
VOC Pipeline — Generador de Reportes Ejecutivos (PDF)

Este módulo automatiza la creación de informes profesionales en formato PDF
utilizando los datos procesados por el motor de análisis. El reporte incluye:
1. Resumen de KPIs globales (NPS, Sentimiento, Volumen).
2. Análisis de tendencias semanales.
3. Panel de problemas críticos (Alertas).
4. Desglose detallado por categoría.
5. Entidades clave y muestra de feedback.

Dependencias: reportlab
"""

import json
import os
import argparse
from pathlib import Path
from datetime import datetime, timedelta

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics import renderPDF

# ============================================================
# PALETA DE COLORES PROFESIONAL
# ============================================================
PRIMARY      = HexColor('#247BA0')
PRIMARY_DARK = HexColor('#19586F')
PRIMARY_LIGHT= HexColor('#E8F4F8')
RED          = HexColor('#FF1654')
GREEN        = HexColor('#2E8D7E')
AMBER        = HexColor('#EF9F27')
GRAY_DARK    = HexColor('#173241')
GRAY_MID     = HexColor('#557280')
GRAY_LIGHT   = HexColor('#F4FBF8')
BORDER       = HexColor('#D1E5E4')

# ============================================================
# ESTILOS
# ============================================================
def crear_estilos():
    styles = getSampleStyleSheet()

    estilos = {
        'titulo_portada': ParagraphStyle(
            'titulo_portada',
            fontName='Helvetica-Bold',
            fontSize=28,
            textColor=white,
            alignment=TA_LEFT,
            leading=34
        ),
        'subtitulo_portada': ParagraphStyle(
            'subtitulo_portada',
            fontName='Helvetica',
            fontSize=14,
            textColor=HexColor('#DDD6FE'),
            alignment=TA_LEFT,
            leading=20
        ),
        'kpi_valor': ParagraphStyle(
            'kpi_valor',
            fontName='Helvetica-Bold',
            fontSize=32,
            textColor=PRIMARY_DARK,
            alignment=TA_CENTER,
            leading=38
        ),
        'kpi_label': ParagraphStyle(
            'kpi_label',
            fontName='Helvetica',
            fontSize=9,
            textColor=GRAY_MID,
            alignment=TA_CENTER,
            leading=12
        ),
        'section_header': ParagraphStyle(
            'section_header',
            fontName='Helvetica-Bold',
            fontSize=14,
            textColor=PRIMARY_DARK,
            leading=18,
            spaceBefore=16,
            spaceAfter=8
        ),
        'body': ParagraphStyle(
            'body',
            fontName='Helvetica',
            fontSize=10,
            textColor=GRAY_DARK,
            leading=15,
            spaceAfter=6
        ),
        'body_small': ParagraphStyle(
            'body_small',
            fontName='Helvetica',
            fontSize=9,
            textColor=GRAY_MID,
            leading=13
        ),
        'alerta_titulo': ParagraphStyle(
            'alerta_titulo',
            fontName='Helvetica-Bold',
            fontSize=10,
            textColor=RED,
            leading=14
        ),
        'alerta_texto': ParagraphStyle(
            'alerta_texto',
            fontName='Helvetica',
            fontSize=9,
            textColor=GRAY_DARK,
            leading=13
        ),
        'accion': ParagraphStyle(
            'accion',
            fontName='Helvetica-Bold',
            fontSize=9,
            textColor=PRIMARY_DARK,
            leading=13
        ),
        'footer': ParagraphStyle(
            'footer',
            fontName='Helvetica',
            fontSize=8,
            textColor=GRAY_MID,
            alignment=TA_CENTER
        ),
        'table_header': ParagraphStyle(
            'table_header',
            fontName='Helvetica-Bold',
            fontSize=9,
            textColor=white,
            alignment=TA_CENTER
        ),
        'table_cell': ParagraphStyle(
            'table_cell',
            fontName='Helvetica',
            fontSize=9,
            textColor=GRAY_DARK,
            leading=12
        ),
    }
    return estilos


# ============================================================
# HELPERS
# ============================================================
def barra_horizontal(positivos, neutrales, negativos, ancho=380):
    """Dibuja una barra de sentimiento proporcional."""
    total = positivos + neutrales + negativos
    if total == 0:
        return Spacer(1, 20)

    altura = 18
    d = Drawing(ancho, altura)

    w_pos  = int((positivos  / total) * ancho)
    w_neu  = int((neutrales  / total) * ancho)
    w_neg  = ancho - w_pos - w_neu

    x = 0
    if w_pos > 0:
        d.add(Rect(x, 0, w_pos, altura, fillColor=GREEN, strokeColor=None))
        if w_pos > 30:
            d.add(String(x + w_pos/2, 5, f'{positivos}', fontSize=8, fillColor=white, textAnchor='middle'))
    x += w_pos
    if w_neu > 0:
        d.add(Rect(x, 0, w_neu, altura, fillColor=HexColor('#B2BEC3'), strokeColor=None))
        if w_neu > 30:
            d.add(String(x + w_neu/2, 5, f'{neutrales}', fontSize=8, fillColor=white, textAnchor='middle'))
    x += w_neu
    if w_neg > 0:
        d.add(Rect(x, 0, w_neg, altura, fillColor=RED, strokeColor=None))
        if w_neg > 30:
            d.add(String(x + w_neg/2, 5, f'{negativos}', fontSize=8, fillColor=white, textAnchor='middle'))

    return d


def barra_menciones(valor, maximo, ancho=200, altura=14):
    if maximo <= 0:
        maximo = 1

    pct = int((valor / maximo) * ancho)
    d = Drawing(ancho, altura)
    d.add(Rect(0, 2, ancho, 10, fillColor=GRAY_LIGHT, strokeColor=None))
    if pct > 0:
        d.add(Rect(0, 2, pct, 10, fillColor=PRIMARY, strokeColor=None))
    return d


def color_urgencia(score):
    if score >= 5: return RED
    if score >= 4: return HexColor('#E17055')
    if score >= 3: return AMBER
    return GREEN


def flecha_variacion(val):
    if val is None: return ''
    if val > 0:  return f'+{val}% ▲'
    if val < 0:  return f'{val}% ▼'
    return '0%'


def semana_actual():
    hoy = datetime.now()
    lunes = hoy - timedelta(days=hoy.weekday())
    domingo = lunes + timedelta(days=6)
    return f"{lunes.strftime('%d/%m')} – {domingo.strftime('%d/%m/%Y')}"


# ============================================================
# SECCIONES DEL PDF
# ============================================================

def portada(datos, estilos, story, ancho_pagina, alto_pagina):
    """Portada con fondo corporativo y KPIs clave."""
    kpis = datos.get('kpis_globales', {})
    meta = datos.get('metadata', {})
    comp = datos.get('comparativa_semanal', {})
    var  = comp.get('variaciones', {})

    fecha = datetime.fromisoformat(meta.get('fecha_analisis', datetime.now().isoformat()))

    # Tabla de portada
    portada_data = [[
        Paragraph('VOC Intelligence Report', estilos['titulo_portada']),
    ]]
    portada_tabla = Table(portada_data, colWidths=[ancho_pagina - 4*cm])
    portada_tabla.setStyle(TableStyle([
        ('BACKGROUND',  (0,0), (-1,-1), PRIMARY),
        ('TOPPADDING',  (0,0), (-1,-1), 40),
        ('BOTTOMPADDING',(0,0),(-1,-1), 20),
        ('LEFTPADDING', (0,0), (-1,-1), 30),
        ('RIGHTPADDING',(0,0), (-1,-1), 30),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [PRIMARY]),
    ]))
    story.append(portada_tabla)

    # Subtítulo
    info_data = [[
        Paragraph('Insights & Analytics Center', estilos['subtitulo_portada']),
        Paragraph(f"Semana {semana_actual()}", estilos['subtitulo_portada']),
    ]]
    info_tabla = Table(info_data, colWidths=[(ancho_pagina - 4*cm)/2]*2)
    info_tabla.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,-1), PRIMARY_DARK),
        ('TOPPADDING',   (0,0), (-1,-1), 12),
        ('BOTTOMPADDING',(0,0), (-1,-1), 16),
        ('LEFTPADDING',  (0,0), (-1,-1), 30),
        ('RIGHTPADDING', (0,0), (-1,-1), 30),
    ]))
    story.append(info_tabla)
    story.append(Spacer(1, 30))

    # KPIs principales — fila de tarjetas
    nps   = kpis.get('nps_estimado')
    rating= kpis.get('avg_rating')

    kpi_items = [
        (str(kpis.get('total_resenas', 0)),  'Total reseñas',     flecha_variacion(var.get('total'))),
        (f"{nps}" if nps is not None else 'N/A', 'NPS estimado', flecha_variacion(var.get('nps'))),
        (f"{kpis.get('tasa_positiva_pct', 0)}%", 'Tasa positiva', flecha_variacion(var.get('positivos_pct'))),
        (f"{rating}★" if rating else 'N/A',  'Rating promedio',   ''),
        (str(kpis.get('alertas_activas', 0)), 'Alertas activas',  flecha_variacion(var.get('alertas'))),
    ]

    col_w = (ancho_pagina - 4*cm) / 5
    kpi_row_vals = [[Paragraph(v, estilos['kpi_valor'])    for v, l, d in kpi_items]]
    kpi_row_labs = [[Paragraph(l, estilos['kpi_label'])    for v, l, d in kpi_items]]
    kpi_row_del  = [[Paragraph(d, estilos['body_small'])   for v, l, d in kpi_items]]

    kpi_tabla = Table(
        kpi_row_vals + kpi_row_labs + kpi_row_del,
        colWidths=[col_w]*5
    )
    kpi_tabla.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,-1), GRAY_LIGHT),
        ('BOX',          (0,0), (-1,-1), 0.5, BORDER),
        ('INNERGRID',    (0,0), (-1,-1), 0.5, BORDER),
        ('TOPPADDING',   (0,0), (-1,0), 16),
        ('BOTTOMPADDING',(0,-1),(-1,-1), 12),
        ('TOPPADDING',   (0,1), (-1,-1), 4),
        ('ALIGN',        (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(kpi_tabla)
    story.append(Spacer(1, 20))

    # Barra de sentimiento global
    story.append(Paragraph('Distribución de sentimiento global', estilos['section_header']))
    story.append(barra_horizontal(
        kpis.get('positivos', 0),
        kpis.get('neutrales', 0),
        kpis.get('negativos', 0),
        ancho=int(ancho_pagina - 4*cm)
    ))
    story.append(Spacer(1, 6))

    leyenda_data = [[
        Paragraph('■ Positivo', ParagraphStyle('l', fontName='Helvetica', fontSize=9, textColor=GREEN)),
        Paragraph('■ Neutral',  ParagraphStyle('l', fontName='Helvetica', fontSize=9, textColor=GRAY_MID)),
        Paragraph('■ Negativo', ParagraphStyle('l', fontName='Helvetica', fontSize=9, textColor=RED)),
    ]]
    leyenda = Table(leyenda_data, colWidths=[(ancho_pagina-4*cm)/3]*3)
    leyenda.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER')]))
    story.append(leyenda)


def seccion_tendencias(datos, estilos, story):
    """Sección 2 — Tendencias para Estrategia."""
    story.append(PageBreak())
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY, spaceAfter=8))
    story.append(Paragraph('2. Tendencias y evolución semanal', estilos['section_header']))
    story.append(Paragraph(
        'Análisis de evolución del sentimiento semana a semana. '
        'Las categorías marcadas en rojo presentan crecimiento de menciones negativas superior al 20%.',
        estilos['body']
    ))
    story.append(Spacer(1, 12))

    tendencias = datos.get('tendencias', {})
    por_semana = tendencias.get('por_semana', [])

    if por_semana:
        headers = ['Semana', 'Total', 'Positivos', 'Neutrales', 'Negativos']
        tabla_data = [[Paragraph(h, estilos['table_header']) for h in headers]]
        for sem in por_semana[-6:]:  # últimas 6 semanas
            total = sem.get('total', 0)
            pos   = sem.get('positivos', 0)
            neg   = sem.get('negativos', 0)
            neu   = sem.get('neutrales', 0)
            tasa  = f"{round((pos/total)*100)}%" if total > 0 else '0%'
            tabla_data.append([
                Paragraph(str(sem.get('semana', '')), estilos['table_cell']),
                Paragraph(str(total), estilos['table_cell']),
                Paragraph(f"{pos} ({tasa})", estilos['table_cell']),
                Paragraph(str(neu), estilos['table_cell']),
                Paragraph(str(neg), estilos['table_cell']),
            ])

        tabla = Table(tabla_data, colWidths=[120, 60, 80, 70, 70])
        tabla.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,0), PRIMARY),
            ('ROWBACKGROUNDS',(0,1), (-1,-1), [white, GRAY_LIGHT]),
            ('BOX',           (0,0), (-1,-1), 0.5, BORDER),
            ('INNERGRID',     (0,0), (-1,-1), 0.5, BORDER),
            ('ALIGN',         (1,0), (-1,-1), 'CENTER'),
            ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING',    (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(tabla)

    # Categorías escalando
    escalando = tendencias.get('categorias_escalando', [])
    if escalando:
        story.append(Spacer(1, 16))
        story.append(Paragraph('⚠ Categorías con tendencia negativa creciente', estilos['alerta_titulo']))
        for e in escalando:
            story.append(Spacer(1, 6))
            esc_data = [[
                Paragraph(f"<b>{e['label']}</b>", estilos['body']),
                Paragraph(f"Esta semana: <b>{e['neg_actual']}</b> negativos", estilos['body']),
                Paragraph(f"Semana anterior: {e['neg_anterior']}", estilos['body']),
                Paragraph(f"<font color='red'>+{e['variacion_pct']}%</font>", estilos['body']),
            ]]
            esc_tabla = Table(esc_data, colWidths=[140, 110, 110, 60])
            esc_tabla.setStyle(TableStyle([
                ('BACKGROUND',   (0,0), (-1,-1), HexColor('#FFF5F5')),
                ('BOX',          (0,0), (-1,-1), 1, RED),
                ('LEFTPADDING',  (0,0), (0,-1), 10),
                ('TOPPADDING',   (0,0), (-1,-1), 8),
                ('BOTTOMPADDING',(0,0), (-1,-1), 8),
                ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
            ]))
            story.append(esc_tabla)
    else:
        story.append(Spacer(1, 12))
        story.append(Paragraph('✓ Sin categorías con tendencia negativa creciente esta semana.', estilos['body']))


def seccion_alertas(datos, estilos, story):
    """Sección 3 — Alertas críticas para Producto y Atención al Cliente."""
    story.append(PageBreak())
    story.append(HRFlowable(width="100%", thickness=2, color=RED, spaceAfter=8))
    story.append(Paragraph('3. Panel de problemas críticos', estilos['section_header']))

    alertas = datos.get('alertas_criticas', [])

    if not alertas:
        story.append(Paragraph(
            '✓ Sin alertas críticas esta semana. Todas las reseñas tienen urgencia menor a 4.',
            estilos['body']
        ))
        return

    story.append(Paragraph(
        f'{len(alertas)} reseña(s) con urgencia ≥ 4 requieren acción inmediata.',
        estilos['body']
    ))
    story.append(Spacer(1, 12))

    for i, a in enumerate(alertas):
        score = int(a.get('score_urgencia', 0))
        color_fondo = HexColor('#FFF5F5') if score >= 5 else HexColor('#FFFBF0')
        color_borde = RED if score >= 5 else HexColor('#E17055')

        icono = '🚨' if score >= 5 else '⚠'
        items = [
            [
                Paragraph(f"{icono}  {a.get('label','').upper()}  |  Urgencia: {score}/5  |  {a.get('fuente','')}  |  {str(a.get('fecha_resena',''))[:10]}", estilos['alerta_titulo']),
            ],
            [
                Paragraph(f'"{str(a.get("texto_original",""))[:350]}..."', estilos['alerta_texto']),
            ],
            [
                Paragraph(f"<b>Resumen IA:</b> {a.get('resumen_ia','')}", estilos['body_small']),
            ],
            [
                Paragraph(f"👉 <b>Acción sugerida:</b> {a.get('accion_sugerida','')}", estilos['accion']),
            ],
        ]
        if a.get('entidades_clave'):
            items.append([Paragraph(f"Entidades: {a.get('entidades_clave','')}", estilos['body_small'])])

        alerta_tabla = Table(items, colWidths=[420])
        alerta_tabla.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),  (-1,-1), color_fondo),
            ('BACKGROUND',    (0,0),  (-1,0),  HexColor('#FFE8E8') if score >= 5 else HexColor('#FFF3E0')),
            ('BOX',           (0,0),  (-1,-1), 1, color_borde),
            ('LEFTPADDING',   (0,0),  (-1,-1), 12),
            ('RIGHTPADDING',  (0,0),  (-1,-1), 12),
            ('TOPPADDING',    (0,0),  (-1,-1), 8),
            ('BOTTOMPADDING', (0,0),  (-1,-1), 8),
        ]))
        story.append(KeepTogether([alerta_tabla, Spacer(1, 10)]))


def seccion_categorias(datos, estilos, story):
    """Sección 4 — Detalle por categoría."""
    story.append(PageBreak())
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY, spaceAfter=8))
    story.append(Paragraph('4. Análisis por categoría', estilos['section_header']))

    categorias = datos.get('por_categoria', [])
    if not categorias:
        story.append(Paragraph('Sin datos por categoría disponibles.', estilos['body']))
        return

    headers = ['Categoría', 'Total', 'Positivos', 'Neutrales', 'Negativos', 'Urgencia prom.', '% del total']
    tabla_data = [[Paragraph(h, estilos['table_header']) for h in headers]]

    for cat in categorias:
        urg_color = color_urgencia(cat.get('avg_urgencia', 0))
        tabla_data.append([
            Paragraph(cat.get('label',''), estilos['table_cell']),
            Paragraph(str(cat.get('total',0)), estilos['table_cell']),
            Paragraph(str(cat.get('positivos',0)), ParagraphStyle('g', fontName='Helvetica', fontSize=9, textColor=GREEN)),
            Paragraph(str(cat.get('neutrales',0)), estilos['table_cell']),
            Paragraph(str(cat.get('negativos',0)), ParagraphStyle('r', fontName='Helvetica', fontSize=9, textColor=RED)),
            Paragraph(str(cat.get('avg_urgencia',0)), ParagraphStyle('u', fontName='Helvetica-Bold', fontSize=9, textColor=urg_color)),
            Paragraph(f"{cat.get('pct_del_total',0)}%", estilos['table_cell']),
        ])

    col_widths = [110, 40, 60, 60, 60, 70, 60]
    tabla = Table(tabla_data, colWidths=col_widths)
    tabla.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),  (-1,0),  PRIMARY),
        ('ROWBACKGROUNDS',(0,1),  (-1,-1), [white, GRAY_LIGHT]),
        ('BOX',           (0,0),  (-1,-1), 0.5, BORDER),
        ('INNERGRID',     (0,0),  (-1,-1), 0.5, BORDER),
        ('ALIGN',         (1,0),  (-1,-1), 'CENTER'),
        ('VALIGN',        (0,0),  (-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0),  (-1,-1), 7),
        ('BOTTOMPADDING', (0,0),  (-1,-1), 7),
    ]))
    story.append(tabla)

    # Barras por categoría
    story.append(Spacer(1, 20))
    story.append(Paragraph('Distribución de sentimiento por categoría', estilos['section_header']))

    for cat in categorias:
        story.append(Spacer(1, 4))
        story.append(Paragraph(cat.get('label',''), estilos['body_small']))
        story.append(barra_horizontal(
            cat.get('positivos',0),
            cat.get('neutrales',0),
            cat.get('negativos',0),
            ancho=380
        ))


def seccion_entidades(datos, estilos, story):
    """Sección 5 — Entidades clave y muestra de reseñas."""
    story.append(PageBreak())
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY, spaceAfter=8))
    story.append(Paragraph('5. Entidades clave y reseñas recientes', estilos['section_header']))

    entidades = datos.get('top_entidades', [])
    if entidades:
        story.append(Paragraph('Personas, áreas y demos más mencionados:', estilos['body']))
        story.append(Spacer(1, 8))

        max_menciones = max(e['menciones'] for e in entidades) if entidades else 1
        ent_data = []
        for e in entidades[:10]:
            ent_data.append([
                Paragraph(e['entidad'], estilos['body']),
                Paragraph(str(e['menciones']), estilos['body']),
                barra_menciones(e['menciones'], max_menciones),
            ])

        ent_tabla = Table(ent_data, colWidths=[150, 50, 210])
        ent_tabla.setStyle(TableStyle([
            ('ROWBACKGROUNDS',(0,0), (-1,-1), [white, GRAY_LIGHT]),
            ('BOX',          (0,0), (-1,-1), 0.5, BORDER),
            ('INNERGRID',    (0,0), (-1,-1), 0.5, BORDER),
            ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING',   (0,0), (-1,-1), 5),
            ('BOTTOMPADDING',(0,0), (-1,-1), 5),
            ('LEFTPADDING',  (0,0), (0,-1),  10),
        ]))
        story.append(ent_tabla)

    # Muestra de reseñas recientes
    recientes = datos.get('resenas_recientes', [])
    if recientes:
        story.append(Spacer(1, 20))
        story.append(Paragraph('Reseñas recientes (muestra)', estilos['section_header']))
        for r in recientes[:5]:
            sent_color = GREEN if r.get('sentimiento') == 'positivo' else (RED if r.get('sentimiento') == 'negativo' else GRAY_MID)
            items = [
                [Paragraph(
                    f"<b>{r.get('sentimiento','').upper()}</b>  |  {r.get('label','')}  |  {r.get('fuente','')}  |  {str(r.get('fecha_resena',''))[:10]}",
                    ParagraphStyle('rh', fontName='Helvetica-Bold', fontSize=9, textColor=sent_color)
                )],
                [Paragraph(str(r.get('texto_original',''))[:280], estilos['alerta_texto'])],
                [Paragraph(f"<i>{r.get('resumen_ia','')}</i>", estilos['body_small'])],
            ]
            r_tabla = Table(items, colWidths=[420])
            r_tabla.setStyle(TableStyle([
                ('BACKGROUND',   (0,0), (-1,-1), GRAY_LIGHT),
                ('BOX',          (0,0), (-1,-1), 0.5, BORDER),
                ('LEFTPADDING',  (0,0), (-1,-1), 10),
                ('TOPPADDING',   (0,0), (-1,-1), 6),
                ('BOTTOMPADDING',(0,0), (-1,-1), 6),
            ]))
            story.append(KeepTogether([r_tabla, Spacer(1, 6)]))


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================
def generar_pdf(input_file='voc_analysis_output.json', output_file=None):
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"[PDF] Error: no se encontró {input_file}")
        print("[PDF] Ejecuta primero: python voc_analysis.py")
        return None

    with open(input_path, 'r', encoding='utf-8') as f:
        datos = json.load(f)

    if output_file is None:
        fecha = datetime.now().strftime('%Y_W%V')
        output_file = f"VOC_Intelligence_Report_{fecha}.pdf"

    output_path = Path(input_path.parent) / output_file

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
        title=f"VOC Intelligence Report",
        author="VOC Intelligence Pipeline",
        subject="Reporte ejecutivo de Voice of Customer"
    )

    ancho, alto = A4
    estilos = crear_estilos()
    story   = []

    portada(datos, estilos, story, ancho, alto)
    seccion_tendencias(datos, estilos, story)
    seccion_alertas(datos, estilos, story)
    seccion_categorias(datos, estilos, story)
    seccion_entidades(datos, estilos, story)

    # Footer en cada página
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(GRAY_MID)
        canvas.drawCentredString(
            ancho / 2, 1.2*cm,
            f"VOC Intelligence Pipeline · Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')} · Página {doc.page}"
        )
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)

    print(f"[PDF] Reporte generado: {output_path}")
    return str(output_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generar reporte PDF VOC Intelligence')
    parser.add_argument('--input',  default='voc_analysis_output.json')
    parser.add_argument('--output', default=None)
    args = parser.parse_args()
    generar_pdf(args.input, args.output)
