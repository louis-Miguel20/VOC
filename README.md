# 🎙️ VOC Pipeline: Voice of Customer Intelligence System

### *Transformando el feedback de los clientes en decisiones estratégicas mediante Inteligencia Artificial*

**VOC Pipeline** es una solución integral de análisis de datos de nivel empresarial diseñada para capturar, procesar y visualizar la "Voz del Cliente" de manera automatizada. Este sistema centraliza el feedback proveniente de múltiples canales y utiliza modelos avanzados de procesamiento de lenguaje natural (NLP) para extraer insights accionables en tiempo real, permitiendo a las organizaciones reaccionar rápidamente a las necesidades de sus clientes.

---

## 🚩 El Problema

En un entorno altamente competitivo, las empresas recolectan miles de comentarios a través de múltiples plataformas (encuestas, redes sociales, reseñas de mapas, etc.). Sin embargo, enfrentan tres desafíos críticos:
1. **Silos de Información**: El feedback está disperso en diferentes herramientas, lo que dificulta una visión unificada.
2. **Análisis Manual Ineficiente**: Procesar y categorizar manualmente el sentimiento y la urgencia de cientos de reseñas consume tiempo valioso y es propenso a errores humanos.
3. **Falta de Acción Inmediata**: Sin una detección automatizada de casos críticos, los problemas de los clientes suelen ser atendidos demasiado tarde, afectando la reputación y la retención.

---

## 🛠️ Desarrollo y Arquitectura

El sistema se diseñó bajo una arquitectura robusta y escalable que sigue el ciclo de vida de los datos:

### 1. Ingesta y Orquestación
Se implementaron conectores para fuentes de datos heterogéneas (Google Sheets, Forms, y scrapers de Google Maps). La orquestación permite que el flujo de datos sea continuo y confiable, asegurando que la información esté siempre actualizada.

### 2. Procesamiento Inteligente (NLP)
Utilizando **OpenAI GPT-4**, el motor de análisis realiza una extracción de características multicapa:
- **Análisis de Sentimiento**: Clasifica la polaridad del feedback con alta precisión.
- **Categorización Automática**: Mapea el texto a dimensiones específicas del servicio (Logística, Calidad, Atención, etc.).
- **Scoring de Urgencia**: Un algoritmo que prioriza comentarios negativos o críticos para una respuesta inmediata.

### 3. Visualización y BI
Se desarrolló un dashboard interactivo en **Streamlit** que permite a los stakeholders:
- Visualizar KPIs clave como NPS (Net Promoter Score) y satisfacción general.
- Explorar tendencias temporales para medir el impacto de cambios estratégicos.
- Identificar puntos de dolor específicos mediante mapas de calor y nubes de categorías.

### 4. Reporting Ejecutivo
Un módulo especializado en **Python** genera reportes PDF profesionales listos para ser presentados en juntas directivas, resumiendo los hallazgos más importantes de la semana.

---

## 🚀 Características Principales

- **📥 Ingesta Multi-canal**: Integración con hojas de cálculo, formularios y reseñas web.
- **🧠 IA Avanzada**: Procesamiento de lenguaje natural para insights profundos.
- **📊 Dashboard Interactivo**: BI ágil para la toma de decisiones basada en datos.
- **📅 Reportes Automatizados**: Generación de informes profesionales en PDF.
- **📈 Análisis de Tendencias**: Seguimiento histórico del sentimiento del cliente.

---

## 🛠️ Stack Tecnológico

| Componente | Tecnologías |
| :--- | :--- |
| **Frontend / BI** | [Streamlit](https://streamlit.io/), [Plotly](https://plotly.com/) |
| **Backend / Análisis** | [Python](https://www.python.org/), [Pandas](https://pandas.pydata.org/) |
| **IA / NLP** | [OpenAI GPT-4](https://openai.com/) |
| **Fuentes de Datos** | Google Sheets API, Google Forms, Scrapers Web |
| **Reporting** | [ReportLab](https://www.reportlab.com/) (PDF Generation) |

---

## 📂 Estructura del Proyecto

- `dashboard.py`: Aplicación principal de visualización de datos.
- `voc_analysis.py`: Motor de procesamiento, limpieza de datos y cálculo de KPIs.
- `generate_report.py`: Generador de reportes semanales en formato PDF.
- `voc_analysis_output.json`: Almacén de datos procesados para consumo del dashboard.
- `requirements.txt`: Dependencias necesarias para el entorno de ejecución.

---

## 🔧 Instalación y Uso

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/voc-intelligence-pipeline.git
cd voc-intelligence-pipeline
```

### 2. Configurar el entorno
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Ejecutar el Dashboard
```bash
streamlit run dashboard.py
```

---

## 💡 Beneficios y Valor Agregado

1. **Eficiencia Operativa**: Automatización del 95% del flujo de trabajo de análisis de encuestas.
2. **Respuesta Proactiva**: Detección de urgencia en tiempo real que mejora el Customer Lifetime Value (CLV).
3. **Decisiones Data-Driven**: Sustitución de la intuición por métricas objetivas y visualizaciones claras.
4. **Escalabilidad**: El sistema puede adaptarse a nuevas fuentes de datos y categorías con cambios mínimos.

---
*Este proyecto demuestra la capacidad de integrar soluciones de IA en flujos de trabajo empresariales para generar valor real y medible.*
