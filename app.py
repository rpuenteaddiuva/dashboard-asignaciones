import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# Configuración de página
st.set_page_config(
    page_title="Dashboard de Asignaciones",
    page_icon="📊",
    layout="wide"
)

# Cargar datos
@st.cache_data
def load_data():
    data_path = Path(__file__).parent / "data" / "asignaciones.csv"
    df = pd.read_csv(data_path)
    df['fecha'] = pd.to_datetime(df['mes'] + '-01')
    df['año'] = df['fecha'].dt.year
    return df

@st.cache_data
def load_nodos():
    nodos_path = Path(__file__).parent / "data" / "nodos_resumen.csv"
    if nodos_path.exists():
        return pd.read_csv(nodos_path)
    return None

df = load_data()
df_nodos = load_nodos()

# Título
st.title("📊 Dashboard de Asignaciones por País")
st.markdown("---")

# Sidebar - Filtros mejorados con UX
with st.sidebar:
    st.image("https://img.icons8.com/color/96/analytics.png", width=60)
    st.header("🔍 Filtros")
    st.caption("Selecciona los filtros y presiona Aplicar")
    
    with st.form("filtros_form"):
        # Filtro de año (primero, más importante)
        años = sorted(df['año'].unique(), reverse=True)
        año_seleccionado = st.multiselect(
            "📅 Año",
            options=años,
            default=[max(años)],
            help="Selecciona uno o más años"
        )
        
        # Filtro de país con selectbox "Todos" o específicos
        paises = sorted(df['pais'].unique())
        todos_paises = st.checkbox("🌎 Todos los países", value=True)
        
        if not todos_paises:
            pais_seleccionado = st.multiselect(
                "País",
                options=paises,
                default=paises[:5],
                help="Selecciona países específicos"
            )
        else:
            pais_seleccionado = paises
        
        # Filtros avanzados en expander
        with st.expander("⚙️ Filtros Avanzados"):
            tipos = sorted(df['tipo_asignacion'].unique())
            tipo_seleccionado = st.multiselect(
                "Tipo de Asignación",
                options=tipos,
                default=tipos
            )
        
        # Botón de aplicar
        submitted = st.form_submit_button("✅ Aplicar Filtros", use_container_width=True, type="primary")
    
    # Métricas rápidas en sidebar
    st.markdown("---")
    st.caption("📊 Resumen rápido")

# Aplicar filtros
df_filtrado = df[
    (df['pais'].isin(pais_seleccionado)) &
    (df['año'].isin(año_seleccionado)) &
    (df['tipo_asignacion'].isin(tipo_seleccionado))
]

# KPIs principales
with st.container(horizontal=True):
    total_servicios = df_filtrado['servicios'].sum()
    total_expedientes = df_filtrado['expedientes'].sum()
    paises_activos = df_filtrado['pais'].nunique()
    
    st.metric("📋 Total Servicios", f"{total_servicios:,.0f}", border=True)
    st.metric("📁 Total Expedientes", f"{total_expedientes:,.0f}", border=True)
    st.metric("🌎 Países", paises_activos, border=True)

st.markdown("---")

# Gráficos en dos columnas - Tendencias
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.subheader("📈 Servicios por Mes")
        df_mensual = df_filtrado.groupby('mes')['servicios'].sum().reset_index()
        fig = px.line(df_mensual, x='mes', y='servicios', markers=True)
        fig.update_layout(xaxis_tickangle=-45, height=350)
        st.plotly_chart(fig, use_container_width=True)

with col2:
    with st.container(border=True):
        st.subheader("📁 Expedientes por Mes")
        df_exp_mensual = df_filtrado.groupby('mes')['expedientes'].sum().reset_index()
        fig = px.line(df_exp_mensual, x='mes', y='expedientes', markers=True, color_discrete_sequence=['#E94F37'])
        fig.update_layout(xaxis_tickangle=-45, height=350)
        st.plotly_chart(fig, use_container_width=True)

# Gráficos por país
col3, col4 = st.columns(2)

with col3:
    with st.container(border=True):
        st.subheader("🌎 Servicios por País")
        df_pais = df_filtrado.groupby('pais')['servicios'].sum().reset_index()
        df_pais = df_pais.sort_values('servicios', ascending=True)
        chart_height = max(350, len(df_pais) * 30)
        fig = px.bar(df_pais, x='servicios', y='pais', orientation='h')
        fig.update_layout(height=chart_height)
        st.plotly_chart(fig, use_container_width=True)

with col4:
    with st.container(border=True):
        st.subheader("📁 Expedientes por País")
        df_pais_exp = df_filtrado.groupby('pais')['expedientes'].sum().reset_index()
        df_pais_exp = df_pais_exp.sort_values('expedientes', ascending=True)
        chart_height = max(350, len(df_pais_exp) * 30)
        fig = px.bar(df_pais_exp, x='expedientes', y='pais', orientation='h', color_discrete_sequence=['#E94F37'])
        fig.update_layout(height=chart_height)
        st.plotly_chart(fig, use_container_width=True)

# Tercera fila de gráficos
col5, col6 = st.columns(2)

with col5:
    with st.container(border=True):
        st.subheader("🔧 Distribución por Tipo de Asignación")
        df_tipo = df_filtrado.groupby('tipo_asignacion')['servicios'].sum().reset_index()
        fig = px.pie(df_tipo, values='servicios', names='tipo_asignacion', hole=0.4)
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

with col6:
    with st.container(border=True):
        st.subheader("📊 App vs Manual (Servicios)")
        
        # Clasificación
        app_types = ['APP', 'ANCLAJE APP SOA', 'ANCLAJE APP', 'ANCLAJE']
        manual_types = ['MANUAL', 'ANCLAJE BASE', 'BASE AUTOMATICO']
        
        df_clasificado = df_filtrado.copy()
        def clasificar(tipo):
            if tipo in app_types:
                return 'APP'
            elif tipo in manual_types:
                return 'MANUAL'
            else:
                return 'OTRO'
        
        df_clasificado['categoria'] = df_clasificado['tipo_asignacion'].apply(clasificar)
        df_cat = df_clasificado.groupby('categoria')['servicios'].sum().reset_index()
        
        fig = px.bar(df_cat, x='categoria', y='servicios', color='categoria',
                     color_discrete_map={'APP': '#2E86AB', 'MANUAL': '#E94F37', 'OTRO': '#999999'})
        fig.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Tabla de datos
with st.container(border=True):
    st.subheader("📋 Datos Detallados")
    
    # Pivot por mes y tipo
    df_pivot = df_filtrado.pivot_table(
        index=['pais', 'mes'],
        columns='tipo_asignacion',
        values='servicios',
        aggfunc='sum',
        fill_value=0
    ).reset_index()
    
    st.dataframe(df_pivot, use_container_width=True, hide_index=True)

st.markdown("---")

# Sección de Nodos (Call Centers)
if df_nodos is not None:
    st.header("📞 Distribución por Nodos (Call Centers)")
    st.caption("Los nodos son los call centers que atienden a los diferentes países")
    
    col_n1, col_n2 = st.columns(2)
    
    with col_n1:
        with st.container(border=True):
            st.subheader("🏢 Expedientes por Nodo")
            fig = px.bar(
                df_nodos.sort_values('expedientes', ascending=True), 
                x='expedientes', 
                y='nodo', 
                orientation='h',
                color='nodo',
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    
    with col_n2:
        with st.container(border=True):
            st.subheader("📊 Distribución Porcentual")
            fig = px.pie(
                df_nodos, 
                values='expedientes', 
                names='nodo', 
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    # KPIs de nodos
    with st.container(border=True):
        st.subheader("📈 Resumen por Nodo")
        st.dataframe(
            df_nodos.sort_values('expedientes', ascending=False),
            use_container_width=True,
            hide_index=True
        )
    
    st.markdown("---")

# Footer
st.caption("Dashboard generado automáticamente | Datos sin registros de prueba")

