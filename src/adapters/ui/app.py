import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import os
import base64

from src.composer import get_obtener_datos_diabetes_use_case, get_obtener_logs_auditoria_use_case
from src.domain.exceptions import DomainError


def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return ""

# Configuración de página
st.set_page_config(
    page_title="Dashboard Salud Pública - Diabetes (Arquitectura Hexagonal)",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS básicos
bg_base64 = get_base64_of_bin_file("bg_image.png")
bg_css = f"""
    .stApp {{
        background-image: url("data:image/png;base64,{bg_base64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-color: #f4f6f9;
        color: #212529;
    }}
""" if bg_base64 else """
    .stApp {
        background-color: #f4f6f9;
        color: #212529;
    }
"""

st.markdown(f"""
<style>
{bg_css}
    .metric-card {{
        background-color: rgba(255, 255, 255, 0.85);
        border-radius: 10px;
        padding: 20px;
        color: #333333;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        backdrop-filter: blur(5px);
    }}
    .metric-value {{
        font-size: 2.5rem;
        font-weight: bold;
        color: #d32f2f;
    }}
    .metric-label {{
        font-size: 1.1rem;
        color: #546e7a;
    }}
</style>
""", unsafe_allow_html=True)

@st.cache_data(show_spinner="Sincronizando con la API del Banco Mundial...")
def load_data(db_path="diabetes.db"):
    try:
        # Obtener el caso de uso compuesto (el composer asegura que las migraciones corran)
        use_case = get_obtener_datos_diabetes_use_case(db_path)
        registros, paises, status = use_case.execute()

        # Mapeamos los datos de las entidades de dominio a un pandas DataFrame
        paises_dict = {p.id: (p.nombre, p.codigo.value) for p in paises}
        data = []
        for r in registros:
            pais_nombre, pais_codigo = paises_dict.get(r.pais_id, (None, None))
            if pais_nombre is None:
                continue
            data.append({
                "registro_id": r.id,
                "pais": pais_nombre,
                "codigo_pais": pais_codigo,
                "ano": r.ano.value,
                "prevalencia": r.prevalencia.value,
                "poblacion": r.poblacion.value,
                "gasto_salud_pib": r.gasto_salud_pib.value,
                "casos_estimados": r.casos_estimados
            })

        df = pd.DataFrame(data)
        if not df.empty:
            df = df.sort_values(by=['pais', 'ano'])
        return df, status
    except DomainError as e:
        st.error(f"Error en el dominio: {e}")
        return pd.DataFrame(), "ERROR"
    except Exception as e:
        st.error(f"Error inesperado al cargar datos: {e}")
        return pd.DataFrame(), "ERROR"

def compute_annual_growth(df):
    """Calcula la diferencia de prevalencia respecto al año anterior registrado"""
    df_sorted = df.sort_values(by='ano')
    if len(df_sorted) < 2:
        return 0
        
    latest = df_sorted['prevalencia'].iloc[-1]
    previous = df_sorted['prevalencia'].iloc[-2]
    
    return latest - previous

def main():
    st.title("Dashboard de Salud Pública: Diabetes en Centroamérica ")
    st.markdown("Monitorización de la **Prevalencia Anual** de diabetes (% de la población de 20 a 79 años), enfocado en **Nicaragua** y países vecinos. Los datos son obtenidos de la **API del Banco Mundial** y persistidos en una base de datos local SQLite.")

    # Cargar datos desde el caso de uso
    df, status = load_data()
    
    if df.empty:
        st.error("No se pudieron cargar datos desde la API ni desde la base de datos local SQLite.")
        return

    st.sidebar.header("Configuración del Panel")
    
    # Mostrar el estado de la conexión de forma amigable y profesional
    if status == "ONLINE":
        st.sidebar.success("🟢 Conexión: En Línea (API Banco Mundial)")
    elif status == "OFFLINE_FALLBACK":
        st.sidebar.warning("⚠️ Conexión: Modo Fallback Local (Offline)")
    else:
        st.sidebar.error("🔴 Conexión: Error en sincronización")
        

    st.sidebar.markdown("---")
    
    available_countries = df['pais'].unique().tolist()
    
    selected_countries = st.sidebar.multiselect(
        "Seleccionar Países a Comparar:",
        options=available_countries,
        default=["Nicaragua", "Costa Rica", "Honduras"] if "Nicaragua" in available_countries else available_countries[:3]
    )
    
    # Filtro de rango de años
    min_year = int(df['ano'].min())
    max_year = int(df['ano'].max())
    
    date_range = st.sidebar.slider(
        "Rango de Años:",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year)
    )
    
    start_year, end_year = date_range
 
    if not selected_countries:
        st.warning("Seleccione al menos un país de la lista.")
        return

    # DataFrame filtrado
    mask = (df['pais'].isin(selected_countries)) & (df['ano'] >= start_year) & (df['ano'] <= end_year)
    df_filtered = df.loc[mask]

    # KPIs Principales
    primary_country = "Nicaragua" if "Nicaragua" in selected_countries else selected_countries[0]
    st.subheader(f"Resumen Epidemiológico: {primary_country}")
    
    df_primary = df_filtered[df_filtered['pais'] == primary_country].copy()
    
    df_primary_sorted = df_primary.sort_values(by='ano')
    if not df_primary_sorted.empty:
        latest_year = int(df_primary_sorted['ano'].iloc[-1])
        latest_prevalencia = df_primary_sorted['prevalencia'].iloc[-1]
        tasa_crecimiento = compute_annual_growth(df_primary_sorted)
        latest_casos = int(df_primary_sorted['casos_estimados'].iloc[-1])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label=f"Prevalencia Actual ({latest_year})", 
                value=f"{latest_prevalencia:.1f}%",
            )
            
        with col2:
            st.metric(
                label="Cambio Interanual", 
                value=f"{tasa_crecimiento:+.1f}%",
                delta=f"{tasa_crecimiento:+.1f}%",
                delta_color="inverse"
            )
            
        with col3:
            st.metric(
                label="Total Casos (Aprox.)",
                value=f"{latest_casos:,}"
            )
            
    st.markdown("---")
    
    # Gráficas Interactivas
    st.subheader("Evolución y Análisis Comparativo")
    
    tab1, tab2, tab3 = st.tabs(["Evolución Prevalencia (%)", "Comparativa Porcentaje", "Casos Estimados Totales"])
    
    with tab1:
        fig_line = px.line(
            df_filtered, 
            x='ano', 
            y='prevalencia', 
            color='pais',
            title='Evolución de Prevalencia de Diabetes (%) a lo largo del tiempo',
            labels={'prevalencia': 'Prevalencia (%)', 'ano': 'Año', 'pais': 'País'},
            markers=True,
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig_line.update_layout(hovermode="x unified", legend_title_text='')
        fig_line.update_xaxes(dtick=1) # Mostrar años de 1 en 1
        st.plotly_chart(fig_line, use_container_width=True)
        
    with tab2:
        df_latest = df_filtered.sort_values('ano').groupby('pais').last().reset_index()
        fig_bar = px.bar(
            df_latest, 
            x='pais', 
            y='prevalencia',
            color='pais',
            title='Prevalencia de Diabetes (%) por País en el Último Año',
            text_auto='.1f',
            labels={'prevalencia': 'Prevalencia (%)', 'pais': 'País'},
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_bar.update_layout(showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)
 
    with tab3:
        if 'casos_estimados' in df_latest.columns:
            fig_bar_cases = px.bar(
                df_latest, 
                x='pais', 
                y='casos_estimados',
                color='pais',
                title='Número Estimado de Personas con Diabetes por País (Último Año)',
                text_auto='.2s',
                labels={'casos_estimados': 'Casos Físicos Estimados', 'pais': 'País'},
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            fig_bar_cases.update_layout(showlegend=False)
            st.plotly_chart(fig_bar_cases, use_container_width=True)
        
    # Tabla de Datos y Descarga
    st.markdown("---")
    st.subheader("Explorador de Datos")
    
    with st.expander("Ver y Descargar Datos en Crudo (Desde Base de Datos)"):
        df_display = df_filtered.sort_values(by=['ano', 'pais'], ascending=[False, True]).copy()
            
        # Formatear visualmente para la tabla de renderizado
        def format_for_table(num):
            if pd.isnull(num): return "0"
            if num >= 1_000_000: return f"{num/1_000_000:.2f} M"
            elif num >= 1_000: return f"{num/1_000:.1f} K"
            return str(int(num))
            
        df_display_table = df_display.copy()
        df_display_table['poblacion'] = df_display_table['poblacion'].apply(format_for_table)
        df_display_table['casos_estimados'] = df_display_table['casos_estimados'].apply(format_for_table)
        df_display_table['gasto_salud_pib'] = df_display_table['gasto_salud_pib'].apply(lambda x: f"{x:.2f}%" if x > 0 else "Sin Datos")
        df_display_table['prevalencia'] = df_display_table['prevalencia'].apply(lambda x: f"{x:.2f}%")
        
        st.dataframe(df_display_table, use_container_width=True)
        
        # Permitir descarga del CSV, dándoles la versión formateada y limpia
        csv_data = df_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Descargar datos en CSV",
            data=csv_data,
            file_name="datos_diabetes_filtrados.csv",
            mime="text/csv",
        )

    # Administrador SQLite Local
    st.markdown("---")
    st.subheader("Administración del Motor de Datos (Offline)")
    
    with st.expander(" Ver Diagnóstico e Historial de Auditoría SQLite (Triggers)"):
        st.markdown("Esta sección interactúa a través del caso de uso de auditoría del dominio para comprobar los logs del sistema de base de datos.")
        
        try:
            logs_use_case = get_obtener_logs_auditoria_use_case()
            logs, stats = logs_use_case.execute(limit=10)
            
            # Mostrar métricas del motor
            col_met1, col_met2, col_met3 = st.columns(3)
            with col_met1:
                st.metric(label="Países Registrados", value=stats["total_paises"])
            with col_met2:
                st.metric(label="Registros Totales", value=stats["total_registros"])
            with col_met3:
                st.metric(label="Eventos en Auditoría", value=stats["total_logs"])
                
            st.markdown("#### Últimos 10 Logs de Auditoría")
            st.markdown("Los registros de auditoría de abajo son creados automáticamente por disparadores (triggers) en la base de datos SQLite.")
            
            if logs:
                df_logs = pd.DataFrame(logs)
                st.dataframe(df_logs, use_container_width=True)
            else:
                st.info("No hay logs en la tabla de auditoría.")
                
        except Exception as ex:
            st.error(f"Error al cargar información de administración de base de datos: {ex}")

if __name__ == "__main__":
    main()
