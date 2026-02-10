# Dashboard de Asignaciones — Contexto del Proyecto

## Descripción General

Dashboard interactivo en **Streamlit** que visualiza la distribución de asignaciones de servicios de asistencia (roadside assistance / travel assistance) por país, tipo de asignación, estado de servicio y nodo (call center). Forma parte del ecosistema de análisis de **Global Solutions Center SAS**.

---

## Stack Tecnológico

| Componente | Tecnología | Versión mínima |
|------------|-----------|----------------|
| Framework web | Streamlit | ≥ 1.30.0 |
| Manipulación de datos | Pandas | ≥ 2.0.0 |
| Visualización | Plotly Express | ≥ 5.18.0 |
| Lenguaje | Python 3 | — |
| Hosting | Streamlit Cloud (potencial) | — |
| Control de versiones | Git | — |

---

## Estructura del Proyecto

```
dashboard_asignaciones/
├── app.py                  # Aplicación principal Streamlit (dark premium theme)
├── generate_data.py        # Script para regenerar CSVs desde archivos Client
├── requirements.txt        # Dependencias
├── .gitignore              # __pycache__, *.pyc, .streamlit/, .env, archivos grandes
├── data/
│   ├── asignaciones_v2.csv # Datos principales con estado (CONCLUIDA/CANCELADA/PROCESO)
│   ├── nodos_detalle.csv   # Desglose mensual por nodo/país/estado
│   ├── asignaciones.csv    # (legacy) Datos sin columna estado
│   ├── nodos_resumen.csv   # (legacy) Resumen simple por nodo
│   ├── soa_nodos.csv       # Cruce SOA: Id_Expediente → Nodo (~31 MB, en .gitignore)
│   └── expediente_nodo.csv # Cruce: Id_Expediente → Pais → Nodo (~19 MB, en .gitignore)
└── claude.md               # Este archivo
```

---

## Archivos de Datos

### `asignaciones_v2.csv` (archivo principal)
Datos agregados mensuales con estado de servicio. 2,959 filas.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `pais` | string | País: Argentina, Bolivia, Chile, Colombia, Costa Rica, Dominicana, Ecuador, Egipto, El Salvador, Estados Unidos, Guatemala, Honduras, Mexico, Nicaragua, Paraguay, Peru, Puerto Rico, Uruguay |
| `mes` | string | Mes en formato `YYYY-MM` |
| `tipo_asignacion` | string | APP, MANUAL, ANCLAJE, ANCLAJE APP, ANCLAJE APP SOA, ANCLAJE BASE, BASE AUTOMATICO, SIN_TIPO, etc. |
| `estado` | string | **CONCLUIDA**, **CANCELADA**, **PROCESO**, OTRO |
| `servicios` | int | Cantidad de servicios (id_asistencia) |
| `expedientes` | int | Cantidad de expedientes únicos (id_expediente) |

**Nota importante:** `estado == 'CONCLUIDA'` equivale a **"Servicios Concluidos (C)"** del Reporte Acumulado de Índices de Johana. Este es el filtro clave para validación cruzada con los índices oficiales.

### `nodos_detalle.csv`
Desglose mensual por nodo (call center), país de asistencia y estado.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `nodo` | string | Call center: Puerto Rico, Guatemala, Costa Rica, Argentina, Colombia, Mexico, Sin Nodo |
| `pais_asistencia` | string | País del servicio |
| `mes` | string | `YYYY-MM` |
| `estado` | string | CONCLUIDA, CANCELADA, PROCESO, OTRO |
| `servicios` | int | Cantidad de servicios |
| `expedientes` | int | Expedientes únicos |

**Consistencia:** El total de servicios en `nodos_detalle.csv` es idéntico al total en `asignaciones_v2.csv` (2,180,036 servicios). Esto es porque ambos se generan del mismo pipeline (`generate_data.py`).

### `generate_data.py`
Script que procesa los 18 archivos Client CSV para producir `asignaciones_v2.csv` y `nodos_detalle.csv`. Usa el mapeo `soa_nodos.csv` (980K expedientes) para asignar nodo a cada servicio.

---

## Arquitectura del Dashboard (`app.py`)

### Theme y Estética
- **Dark premium theme** con fondo `#0f172a` / `#1e293b`
- **Fuente Inter** (Google Fonts)
- **Plotly dark template** con paleta consistente:
  - Azul `#3b82f6` (servicios), Verde `#10b981` (concluidos), Morado `#8b5cf6` (expedientes)
  - Rojo `#ef4444` (cancelados), Ámbar `#f59e0b` (proceso), Cyan `#06b6d4` (app)

### KPIs (5 tarjetas)
1. 📋 Total Servicios
2. ✅ Concluidos (estado == CONCLUIDA)
3. ❌ Cancelados (estado == CANCELADA)
4. 📁 Expedientes
5. 🏳️ % Conclusión

### Pestaña 1: Asignaciones por País
- **3 gráficos de tendencia mensual**: Servicios, Concluidos, Expedientes (area charts)
- **3 barras horizontales por país**: Servicios, Concluidos, Expedientes
- **3 distribuciones**: Estado (pie), Tipo asignación (pie), App vs Manual (bar)
- **Tasa de conclusión por país** (bar horizontal con escala de color semáforo)
- **Tabla resumen** con totales formateados

### Pestaña 2: Nodos (Call Centers)
- 4 KPIs: Nodos activos, Servicios, Concluidos, Expedientes
- **Barras apiladas** servicios por nodo desglosados por estado
- **Pie** distribución porcentual
- **Tendencia mensual** por nodo (líneas)
- **Expandibles** por nodo con detalle de países atendidos
- **Tabla resumen** por nodo

### Clasificación App vs Manual
```python
app_types = ['APP', 'ANCLAJE APP SOA', 'ANCLAJE APP', 'ANCLAJE']
manual_types = ['MANUAL', 'ANCLAJE BASE', 'BASE AUTOMATICO']
```

---

## Descubrimientos Clave

### 1. Estado de Asistencia y Validación con Índices
- El campo `estado_asistencia` en los Client CSVs tiene 3 valores principales: **CONCLUIDA**, **CANCELADA**, **PROCESO**
- `CONCLUIDA` coincide con "Servicios Concluidos (C)" del Reporte de Índices dentro de 1-2% para la mayoría de países (AR +0.5%, DO +1.0%, EC +1.3%, UY +1.2%, PE -0.1%)
- **Outliers**: Guatemala +45.5%, Bolivia +75.6%, México -26.7%
- **Chile** tiene 65% de servicios cancelados (tasa más alta)

### 2. Servicios vs Expedientes
- Un **expediente** = un caso/siniestro único
- Un expediente puede generar **múltiples servicios** (grúa + taxi + hotel)
- Siempre: `servicios ≥ expedientes`

### 3. Nodos = Call Centers
| Nodo | Servicios | % del Total |
|------|-----------|-------------|
| Puerto Rico | 1,030,157 | 47.3% |
| Sin Nodo | 502,377 | 23.0% |
| Guatemala | 281,032 | 12.9% |
| Argentina | 277,702 | 12.7% |
| Costa Rica | 77,228 | 3.5% |
| Colombia | 9,444 | 0.4% |
| Mexico | 2,096 | 0.1% |

### 4. 18 Países Procesados
Argentina, Bolivia, Chile, Colombia, Costa Rica, Dominicana, Ecuador, Egipto, El Salvador, Estados Unidos, Guatemala, Honduras, Mexico, Nicaragua, Paraguay, Peru, Puerto Rico, Uruguay

---

## Convenciones

- **Fechas**: `YYYY-MM` en datos, datetime (`YYYY-MM-01`) en dashboard
- **Cache**: `@st.cache_data` para performance
- **Archivos grandes**: `soa_nodos.csv` (31MB) y `expediente_nodo.csv` (19MB) están en `.gitignore`
- **Git**: `rpuenteaddiuva/dashboard-asignaciones` en GitHub

---

## Proyectos Relacionados

1. **Dashboard de Calidad (ads-calidad)** — Streamlit Cloud (`ads-calidad.streamlit.app`)
2. **Visuales Power BI** — `costosGastosVisual`, `comparativoAnualVisual`, `coverVisual`
3. **Addiuva CLI** — Framework D3 para Power BI Custom Visuals
4. **Plan Estratégico BI 2026-2030** — Documento LaTeX
