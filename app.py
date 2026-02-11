import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Addiuva · Asignaciones",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* KPI cards */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 16px 20px;
    color: #f8fafc;
}
[data-testid="stMetric"] label {
    color: #94a3b8 !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
}
[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #f1f5f9 !important;
    font-weight: 700 !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    padding: 10px 20px;
    font-weight: 600;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
}
section[data-testid="stSidebar"] .stMarkdown, 
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stCaption {
    color: #cbd5e1 !important;
}

/* Charts container */
[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] {
    gap: 12px;
}
</style>
""", unsafe_allow_html=True)

# ─── Color Palette ────────────────────────────────────────────────────────────
COLORS = {
    'primary': '#3b82f6',
    'secondary': '#8b5cf6',
    'accent': '#06b6d4',
    'success': '#10b981',
    'warning': '#f59e0b',
    'danger': '#ef4444',
    'muted': '#64748b',
}
PALETTE = ['#3b82f6', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444',
           '#ec4899', '#14b8a6', '#f97316', '#6366f1', '#84cc16', '#a855f7']
CHART_TEMPLATE = 'plotly_dark'

# ─── Data Loading ─────────────────────────────────────────────────────────────
@st.cache_data
def load_asignaciones():
    path = Path(__file__).parent / "data" / "asignaciones_v2.csv"
    if not path.exists():
        # Fallback to old format
        path = Path(__file__).parent / "data" / "asignaciones.csv"
        df = pd.read_csv(path)
        df['estado'] = 'DESCONOCIDO'
        return df
    df = pd.read_csv(path)
    df['fecha'] = pd.to_datetime(df['mes'] + '-01')
    df['año'] = df['fecha'].dt.year
    df['mes_nombre'] = df['fecha'].dt.strftime('%b %Y')
    return df

@st.cache_data
def load_nodos():
    path = Path(__file__).parent / "data" / "nodos_detalle.csv"
    if path.exists():
        df = pd.read_csv(path)
        df['fecha'] = pd.to_datetime(df['mes'] + '-01')
        df['año'] = df['fecha'].dt.year
        return df
    return None

df = load_asignaciones()
df_nodos = load_nodos()

# ─── Helper Functions ─────────────────────────────────────────────────────────
def fmt(n):
    """Format number with K/M suffix."""
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n/1_000:.1f}K"
    return f"{n:,.0f}"

def chart_layout(fig, height=380, **kwargs):
    """Apply consistent dark styling to charts."""
    fig.update_layout(
        template=CHART_TEMPLATE,
        height=height,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(15,23,42,0.6)',
        font=dict(family='Inter', color='#94a3b8'),
        legend=dict(
            bgcolor='rgba(0,0,0,0)',
            font=dict(color='#94a3b8', size=11),
        ),
        **kwargs,
    )
    fig.update_xaxes(gridcolor='rgba(51,65,85,0.4)', tickfont=dict(size=10))
    fig.update_yaxes(gridcolor='rgba(51,65,85,0.4)', tickfont=dict(size=10))
    return fig

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown("## 📊 Dashboard de Asignaciones")
st.caption("Análisis de servicios, expedientes y estado por país y nodo")

# ─── Sidebar Filters ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔍 Filtros")

    # Solo Concluidos Toggle
    solo_concluidos = st.toggle("✅ Solo Concluidos", value=False)

    # 1. Year Filter
    años = sorted(df['año'].unique(), reverse=True)
    años_opts = ["Todos"] + list(años)
    año_sel = st.selectbox("📅 Año", años_opts, index=1 if len(años) > 0 else 0) # Default to latest year if possible

    # 2. Month Filter
    meses_map = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
                 7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
    df['mes_num'] = df['fecha'].dt.month
    df['mes_txt'] = df['mes_num'].map(meses_map)
    
    meses_disponibles = sorted(df['mes_num'].unique())
    meses_opciones = ["Todos"] + [meses_map[m] for m in meses_disponibles]
    
    mes_sel = st.selectbox("🗓 Mes", meses_opciones, index=0)

    # 3. Country Filter
    paises_list = sorted(df['pais'].unique())
    paises_opts = ["Todos"] + paises_list
    pais_sel = st.selectbox("🌎 País", paises_opts, index=0)

    # 4. Type Filter
    tipos = sorted(df['tipo_asignacion'].unique())
    tipos_opts = ["Todos"] + tipos
    tipo_sel = st.selectbox("⚙️ Tipo de Asignación", tipos_opts, index=0)

    st.markdown("---")
    st.caption("💡 *Concluidos* = servicios con estado CONCLUIDA. Selecciona filtros para refinar la vista.")

# ─── Apply Filters ────────────────────────────────────────────────────────────
mask = pd.Series(True, index=df.index)

if año_sel != "Todos":
    mask = mask & (df['año'] == año_sel)

if mes_sel != "Todos":
    mask = mask & (df['mes_txt'] == mes_sel)

if pais_sel != "Todos":
    mask = mask & (df['pais'] == pais_sel)

if tipo_sel != "Todos":
    mask = mask & (df['tipo_asignacion'] == tipo_sel)

if solo_concluidos:
    mask = mask & (df['estado'] == 'CONCLUIDA')

dff = df[mask].copy()

# Pre-compute key aggregates
total_servicios = int(dff['servicios'].sum())
total_expedientes = int(dff['expedientes'].sum())
concluidos = int(dff[dff['estado'] == 'CONCLUIDA']['servicios'].sum())
cancelados = int(dff[dff['estado'] == 'CANCELADA']['servicios'].sum())
pct_concl = (concluidos / total_servicios * 100) if total_servicios else 0
paises_activos = dff['pais'].nunique()

# ─── KPI Row ──────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("📋 Total Servicios", fmt(total_servicios))
k2.metric("✅ Concluidos", fmt(concluidos))
k3.metric("❌ Cancelados", fmt(cancelados))
k4.metric("📁 Expedientes", fmt(total_expedientes))
k5.metric("🏳️ % Conclusión", f"{pct_concl:.1f}%")

st.markdown("")

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab_asig, tab_nodos = st.tabs(["📊 Asignaciones por País", "🏢 Nodos (Call Centers)"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: ASIGNACIONES
# ═══════════════════════════════════════════════════════════════════════════════
with tab_asig:

    # ── Row 1: Monthly Trends (3 charts side by side) ─────────────────────────
    st.markdown("#### 📈 Tendencias Mensuales")
    c1, c2, c3 = st.columns(3)

    # Servicios totales por mes
    df_mes = dff.groupby('mes', as_index=False)['servicios'].sum().sort_values('mes')
    with c1:
        fig = px.area(df_mes, x='mes', y='servicios', markers=True,
                      color_discrete_sequence=[COLORS['primary']])
        fig.update_traces(fill='tozeroy', fillcolor='rgba(59,130,246,0.15)',
                          line=dict(width=2.5))
        chart_layout(fig, title='Servicios Totales')
        fig.update_xaxes(tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    # Concluidos por mes
    df_concl_mes = dff[dff['estado'] == 'CONCLUIDA'].groupby('mes', as_index=False)['servicios'].sum().sort_values('mes')
    with c2:
        fig = px.area(df_concl_mes, x='mes', y='servicios', markers=True,
                      color_discrete_sequence=[COLORS['success']])
        fig.update_traces(fill='tozeroy', fillcolor='rgba(16,185,129,0.15)',
                          line=dict(width=2.5))
        chart_layout(fig, title='Servicios Concluidos')
        fig.update_xaxes(tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    # Expedientes por mes
    df_exp_mes = dff.groupby('mes', as_index=False)['expedientes'].sum().sort_values('mes')
    with c3:
        fig = px.area(df_exp_mes, x='mes', y='expedientes', markers=True,
                      color_discrete_sequence=[COLORS['secondary']])
        fig.update_traces(fill='tozeroy', fillcolor='rgba(139,92,246,0.15)',
                          line=dict(width=2.5))
        chart_layout(fig, title='Expedientes')
        fig.update_xaxes(tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    # ── Row 2: By Country (3 bar charts) ──────────────────────────────────────
    st.markdown("#### 🌎 Por País")
    c4, c5, c6 = st.columns(3)

    # Servicios por país
    df_pais_serv = dff.groupby('pais', as_index=False)['servicios'].sum() \
                      .sort_values('servicios', ascending=True)
    with c4:
        fig = px.bar(df_pais_serv, x='servicios', y='pais', orientation='h',
                     color_discrete_sequence=[COLORS['primary']])
        h = max(350, len(df_pais_serv) * 28)
        chart_layout(fig, height=h, title='Servicios Totales')
        st.plotly_chart(fig, use_container_width=True)

    # Concluidos por país
    df_pais_concl = dff[dff['estado'] == 'CONCLUIDA'] \
        .groupby('pais', as_index=False)['servicios'].sum() \
        .sort_values('servicios', ascending=True)
    with c5:
        fig = px.bar(df_pais_concl, x='servicios', y='pais', orientation='h',
                     color_discrete_sequence=[COLORS['success']])
        chart_layout(fig, height=h, title='Concluidos')
        st.plotly_chart(fig, use_container_width=True)

    # Expedientes por país
    df_pais_exp = dff.groupby('pais', as_index=False)['expedientes'].sum() \
                     .sort_values('expedientes', ascending=True)
    with c6:
        fig = px.bar(df_pais_exp, x='expedientes', y='pais', orientation='h',
                     color_discrete_sequence=[COLORS['secondary']])
        chart_layout(fig, height=h, title='Expedientes')
        st.plotly_chart(fig, use_container_width=True)

    # ── Row 3: Distributions ──────────────────────────────────────────────────
    st.markdown("#### 📊 Distribuciones")
    c7, c8, c9 = st.columns(3)

    # Estado distribution (pie)
    with c7:
        df_estado = dff.groupby('estado', as_index=False)['servicios'].sum()
        color_map = {'CONCLUIDA': COLORS['success'], 'CANCELADA': COLORS['danger'],
                     'PROCESO': COLORS['warning'], 'OTRO': COLORS['muted'],
                     'SIN_ESTADO': '#475569', 'DESCONOCIDO': '#475569'}
        fig = px.pie(df_estado, values='servicios', names='estado', hole=0.45,
                     color='estado', color_discrete_map=color_map)
        fig.update_traces(textinfo='percent+label', textfont_size=11)
        chart_layout(fig, title='Estado de Servicios')
        st.plotly_chart(fig, use_container_width=True)

    # Tipo asignación (pie) — group small segments to avoid label overlap
    with c8:
        df_tipo = dff.groupby('tipo_asignacion', as_index=False)['servicios'].sum() \
                     .sort_values('servicios', ascending=False)
        top_n = 5
        if len(df_tipo) > top_n:
            top = df_tipo.head(top_n)
            otros = pd.DataFrame([{
                'tipo_asignacion': 'OTROS',
                'servicios': df_tipo.iloc[top_n:]['servicios'].sum()
            }])
            df_tipo = pd.concat([top, otros], ignore_index=True)
        fig = px.pie(df_tipo, values='servicios', names='tipo_asignacion', hole=0.45,
                     color_discrete_sequence=PALETTE)
        fig.update_traces(textinfo='percent', textfont_size=11,
                          textposition='inside')
        chart_layout(fig, title='Tipo de Asignación')
        fig.update_layout(legend=dict(font=dict(size=10), orientation='v',
                                       y=0.5, x=1.02))
        st.plotly_chart(fig, use_container_width=True)

    # App vs Manual (bar)
    with c9:
        app_types = ['APP', 'ANCLAJE APP SOA', 'ANCLAJE APP', 'ANCLAJE']
        manual_types = ['MANUAL', 'ANCLAJE BASE', 'BASE AUTOMATICO']
        def classify(t):
            if t in app_types: return 'App / Automatizado'
            elif t in manual_types: return 'Manual'
            else: return 'Otro'
        df_cat = dff.copy()
        df_cat['categoria'] = df_cat['tipo_asignacion'].apply(classify)
        df_cat_agg = df_cat.groupby('categoria', as_index=False)['servicios'].sum()
        cmap = {'App / Automatizado': COLORS['accent'], 'Manual': COLORS['warning'], 'Otro': COLORS['muted']}
        fig = px.bar(df_cat_agg, x='categoria', y='servicios', color='categoria',
                     color_discrete_map=cmap)
        chart_layout(fig, title='App vs Manual', showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    # ── Row 4: % Conclusión por País ──────────────────────────────────────────
    st.markdown("#### 🎯 Tasa de Conclusión por País")
    df_pais_all = dff.groupby('pais', as_index=False).agg(
        servicios=('servicios', 'sum'),
        expedientes=('expedientes', 'sum'),
    )
    df_pais_c = dff[dff['estado'] == 'CONCLUIDA'].groupby('pais', as_index=False)['servicios'].sum()
    df_pais_c.columns = ['pais', 'concluidos']
    df_rate = df_pais_all.merge(df_pais_c, on='pais', how='left').fillna(0)
    df_rate['pct_conclusion'] = (df_rate['concluidos'] / df_rate['servicios'] * 100).round(1)
    df_rate = df_rate.sort_values('pct_conclusion', ascending=True)

    fig = px.bar(df_rate, x='pct_conclusion', y='pais', orientation='h',
                 color='pct_conclusion',
                 color_continuous_scale=['#ef4444', '#f59e0b', '#10b981'],
                 range_color=[30, 85])
    chart_layout(fig, height=max(350, len(df_rate) * 28),
                 title='% Servicios Concluidos por País',
                 coloraxis_colorbar=dict(title='%'))
    fig.update_traces(texttemplate='%{x:.1f}%', textposition='outside', textfont_size=10)
    st.plotly_chart(fig, use_container_width=True)

    # ── Row 5: Data Table ─────────────────────────────────────────────────────
    st.markdown("#### 📋 Tabla Resumen por País")
    df_table = df_rate[['pais', 'servicios', 'concluidos', 'expedientes', 'pct_conclusion']].copy()
    df_table = df_table.sort_values('servicios', ascending=False)
    df_table['cancelados'] = df_table['servicios'] - df_table['concluidos']
    df_table = df_table[['pais', 'servicios', 'concluidos', 'cancelados', 'expedientes', 'pct_conclusion']]
    df_table.columns = ['País', 'Total Servicios', 'Concluidos', 'Cancelados', 'Expedientes', '% Conclusión']

    # Add totals row
    totals = pd.DataFrame([{
        'País': '🟰 TOTAL',
        'Total Servicios': df_table['Total Servicios'].sum(),
        'Concluidos': df_table['Concluidos'].sum(),
        'Cancelados': df_table['Cancelados'].sum(),
        'Expedientes': df_table['Expedientes'].sum(),
        '% Conclusión': round(df_table['Concluidos'].sum() / df_table['Total Servicios'].sum() * 100, 1) if df_table['Total Servicios'].sum() else 0,
    }])
    df_display = pd.concat([df_table, totals], ignore_index=True)

    st.dataframe(
        df_display.style.format({
            'Total Servicios': '{:,.0f}',
            'Concluidos': '{:,.0f}',
            'Cancelados': '{:,.0f}',
            'Expedientes': '{:,.0f}',
            '% Conclusión': '{:.1f}%',
        }),
        use_container_width=True,
        hide_index=True,
        height=min(600, 40 * len(df_display) + 40),
    )

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: NODOS
# ═══════════════════════════════════════════════════════════════════════════════
with tab_nodos:
    if df_nodos is not None:
        # Apply year filter to nodos too
        dfn = df_nodos[df_nodos['año'].isin(año_sel)].copy()

        # ── KPI Row ───────────────────────────────────────────────────────────
        # Use asignaciones data (dff) for totals to match main KPIs exactly.
        # Nodo data groups differently (no tipo_asignacion), so expediente
        # deduplication is tighter, causing a mismatch if summed from nodos.
        nodos_activos = dfn[dfn['nodo'] != 'Sin Nodo']['nodo'].nunique()
        n_total_serv = int(dff['servicios'].sum())
        n_total_exp = int(dff['expedientes'].sum())
        n_concl = int(dff[dff['estado'] == 'CONCLUIDA']['servicios'].sum())

        nk1, nk2, nk3, nk4 = st.columns(4)
        nk1.metric("🏢 Nodos Activos", nodos_activos)
        nk2.metric("📋 Servicios", fmt(n_total_serv))
        nk3.metric("✅ Concluidos", fmt(n_concl))
        nk4.metric("📁 Expedientes", fmt(n_total_exp))

        st.markdown("")

        # ── Row 1: Nodo overview (bar + pie) ──────────────────────────────────
        st.markdown("#### 🏢 Distribución por Nodo")
        nc1, nc2 = st.columns([3, 2])

        # Filter out "Sin Nodo" for cleaner display, but show as info
        sin_nodo_serv = int(dfn[dfn['nodo'] == 'Sin Nodo']['servicios'].sum())
        dfn_clean = dfn[dfn['nodo'] != 'Sin Nodo']

        nodo_agg = dfn_clean.groupby('nodo', as_index=False).agg(
            servicios=('servicios', 'sum'),
            expedientes=('expedientes', 'sum'),
        ).sort_values('servicios', ascending=True)

        with nc1:
            # Stacked bar: concluidos vs cancelados per nodo
            nodo_estado = dfn_clean.groupby(['nodo', 'estado'], as_index=False)['servicios'].sum()
            estado_colors = {'CONCLUIDA': COLORS['success'], 'CANCELADA': COLORS['danger'],
                            'PROCESO': COLORS['warning'], 'OTRO': COLORS['muted'], 'SIN_ESTADO': '#475569'}
            fig = px.bar(nodo_estado, x='servicios', y='nodo', color='estado', orientation='h',
                         color_discrete_map=estado_colors,
                         category_orders={'nodo': nodo_agg['nodo'].tolist()})
            chart_layout(fig, height=max(350, len(nodo_agg) * 50),
                         title='Servicios por Nodo (por Estado)',
                         barmode='stack')
            st.plotly_chart(fig, use_container_width=True)

        with nc2:
            fig = px.pie(nodo_agg, values='servicios', names='nodo', hole=0.45,
                         color_discrete_sequence=PALETTE)
            fig.update_traces(textinfo='percent+label', textfont_size=11)
            chart_layout(fig, title='Distribución %')
            st.plotly_chart(fig, use_container_width=True)

        if sin_nodo_serv > 0:
            st.info(f"ℹ️ Hay **{sin_nodo_serv:,}** servicios sin nodo asignado ({sin_nodo_serv/n_total_serv*100:.1f}% del total). Estos expedientes no tienen cruce en el archivo SOA.")

        # ── Row 2: Monthly trend per nodo ─────────────────────────────────────
        st.markdown("#### 📈 Tendencia Mensual por Nodo")
        nodo_mensual = dfn_clean.groupby(['nodo', 'mes'], as_index=False)['servicios'].sum().sort_values('mes')
        fig = px.line(nodo_mensual, x='mes', y='servicios', color='nodo',
                      markers=True, color_discrete_sequence=PALETTE)
        chart_layout(fig, height=420, title='Servicios Totales por Nodo')
        fig.update_xaxes(tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

        # ── Row 3: Countries per Nodo ─────────────────────────────────────────
        st.markdown("#### 🌎 Países atendidos por cada Nodo")

        nodo_pais = dfn_clean.groupby(['nodo', 'pais_asistencia'], as_index=False).agg(
            servicios=('servicios', 'sum'),
            expedientes=('expedientes', 'sum'),
        )

        # Show top nodos in expandable sections
        top_nodos = nodo_agg.sort_values('servicios', ascending=False)['nodo'].tolist()
        for nodo in top_nodos:
            nodo_detail = nodo_pais[nodo_pais['nodo'] == nodo].sort_values('servicios', ascending=False)
            total_nodo = nodo_detail['servicios'].sum()
            with st.expander(f"🏢 **{nodo}** — {fmt(total_nodo)} servicios, {len(nodo_detail)} países"):
                ec1, ec2 = st.columns([3, 2])
                with ec1:
                    fig = px.bar(nodo_detail.sort_values('servicios', ascending=True),
                                 x='servicios', y='pais_asistencia', orientation='h',
                                 color_discrete_sequence=[COLORS['accent']])
                    chart_layout(fig, height=max(200, len(nodo_detail) * 25), title=f'Servicios')
                    st.plotly_chart(fig, use_container_width=True)
                with ec2:
                    tbl = nodo_detail[['pais_asistencia', 'servicios', 'expedientes']].copy()
                    tbl.columns = ['País', 'Servicios', 'Expedientes']
                    tbl['%'] = (tbl['Servicios'] / total_nodo * 100).round(1)
                    st.dataframe(
                        tbl.style.format({'Servicios': '{:,.0f}', 'Expedientes': '{:,.0f}', '%': '{:.1f}%'}),
                        use_container_width=True, hide_index=True,
                    )

        # ── Row 4: Nodo summary table ─────────────────────────────────────────
        st.markdown("#### 📋 Tabla Resumen por Nodo")
        nodo_summary = dfn_clean.groupby('nodo', as_index=False).agg(
            servicios=('servicios', 'sum'),
            expedientes=('expedientes', 'sum'),
        )
        nodo_concl = dfn_clean[dfn_clean['estado'] == 'CONCLUIDA'].groupby('nodo', as_index=False)['servicios'].sum()
        nodo_concl.columns = ['nodo', 'concluidos']
        nodo_summary = nodo_summary.merge(nodo_concl, on='nodo', how='left').fillna(0)
        nodo_summary['pct_conclusion'] = (nodo_summary['concluidos'] / nodo_summary['servicios'] * 100).round(1)
        nodo_summary['paises'] = nodo_summary['nodo'].apply(
            lambda n: len(nodo_pais[nodo_pais['nodo'] == n]['pais_asistencia'].unique())
        )
        nodo_summary = nodo_summary.sort_values('servicios', ascending=False)
        nodo_summary.columns = ['Nodo', 'Servicios', 'Expedientes', 'Concluidos', '% Conclusión', 'Países']
        nodo_summary = nodo_summary[['Nodo', 'Servicios', 'Concluidos', 'Expedientes', '% Conclusión', 'Países']]

        st.dataframe(
            nodo_summary.style.format({
                'Servicios': '{:,.0f}',
                'Concluidos': '{:,.0f}',
                'Expedientes': '{:,.0f}',
                '% Conclusión': '{:.1f}%',
            }),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.warning("⚠️ No hay datos de nodos disponibles. Ejecuta `generate_data.py` primero.")

# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("📊 Dashboard Addiuva · Datos procesados desde archivos Client · Concluidos = estado_asistencia == CONCLUIDA")
