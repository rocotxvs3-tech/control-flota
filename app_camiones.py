import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Control de Flota en Ruta", layout="wide", page_icon="🚛")

# Conexión con la planilla de Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Estructura base de los camiones
tractores = {
    "AG506KW": {"modelo": "MB Actros", "tolva": "AF720XG"},
    "AB020RG": {"modelo": "MB 1735", "tolva": "AC738FC"},
    "AB032RM": {"modelo": "MB 1735", "tolva": "LBZ158"}
}

# Menú lateral para elegir el rol
st.sidebar.title("📌 Menú de Acceso")
rol = st.sidebar.radio("Selecciona tu perfil:", ["📱 Modo Chofer", "🖥️ Modo Administración"])

# ---------------------------------------------------------
# MODO CHOFER (Carga desde celular)
# ---------------------------------------------------------
if rol == "📱 Modo Chofer":
    st.title("📲 Carga de Reporte Diario")
    
    patente = st.selectbox("Selecciona la patente de tu Camión", list(tractores.keys()))
    camion = tractores[patente]
    
    st.info(f"Vehículo: **{camion['modelo']} ({patente})** | Tolva: **{camion['tolva']}**")
    
    with st.form("form_chofer", clear_on_submit=True):
        nombre_chofer = st.text_input("Nombre y Apellido del Chofer")
        
        estado = st.selectbox("Estado del viaje", [
            "En Ruta (Ida)",
            "Cargando en Origen",
            "Descargando en Destino",
            "En Ruta (Retorno)",
            "Mantenimiento / Parado"
        ])
        
        col1, col2 = st.columns(2)
        with col1:
            km = st.number_input("Kilometraje Actual (Odómetro)", min_value=0, step=10, value=150000)
            gasoil = st.slider("Nivel de Gasoil (%)", 0, 100, 80)
        with col2:
            urea = st.slider("Nivel de Urea (%)", 0, 100, 80)
            toneladas = st.number_input("Toneladas de la Carga", min_value=0.0, max_value=60.0, value=30.0, step=0.5)
            
        duracion_min = st.number_input("Duración del tramo (Minutos)", min_value=0, max_value=1440, value=45, step=5)
        
        btn_enviar = st.form_submit_button("🚀 ENVIAR REPORTE A ADMINISTRACIÓN", use_container_width=True)
        
        if btn_enviar:
            if nombre_chofer.strip() == "":
                st.error("⚠️ Debes ingresar tu nombre antes de enviar.")
            else:
                # Leer datos existentes de Google Sheets
                df_existente = conn.read(ttl=0)
                
                # Nueva fila
                nueva_fila = pd.DataFrame([{
                    "Fecha/Hora": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Tractor": f"{camion['modelo']} ({patente})",
                    "Tolva": camion['tolva'],
                    "Chofer": nombre_chofer,
                    "Estado": estado,
                    "Km": km,
                    "Gasoil": f"{gasoil}%",
                    "Urea": f"{urea}%",
                    "Toneladas": toneladas,
                    "Tiempo": f"{duracion_min} min"
                }])
                
                # Concatenar y actualizar la hoja
                df_actualizado = pd.concat([df_existente, nueva_fila], ignore_index=True)
                conn.update(data=df_actualizado)
                
                st.success("✅ ¡Reporte enviado y guardado con éxito en la planilla general!")

# ---------------------------------------------------------
# MODO ADMINISTRACIÓN (Visualización y Descarga de Excel)
# ---------------------------------------------------------
else:
    st.title("🖥️ Administración de Flota y Descarga de Registros")
    
    if st.button("🔄 Actualizar Datos"):
        st.cache_data.clear()
        st.rerun()
        
    try:
        df_datos = conn.read(ttl=0)
        st.subheader("📋 Planilla General de Viajes e Insumos")
        st.dataframe(df_datos, use_container_width=True)
        
        # Botón para descargar directo en Excel
        @st.cache_data
        def convertir_a_excel(df):
            import io
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Registro_Flota')
            return buffer.getvalue()

        excel_data = convertir_a_excel(df_datos)
        st.download_button(
            label="📥 Descargar Reporte Completo en Excel (.xlsx)",
            data=excel_data,
            file_name=f"Reporte_Flota_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        st.warning("Aún no hay registros cargados o falta conectar la planilla de Google Sheets.")