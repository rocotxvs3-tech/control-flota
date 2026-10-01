import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# Configuración de página
st.set_page_config(page_title="Control de Neumáticos - Flota", layout="wide", page_icon="🛞")

# Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Definición de la Flota (Tractores y Tolvas)
tractores = {
    "AG506KW": "MB Actros",
    "AB020RG": "MB 1735",
    "AB032RM": "MB 1735"
}

tolvas = {
    "AF720XG": "RANDON SemiTolva 1",
    "AC738FC": "RANDON SemiTolva 2",
    "LBZ158": "RANDON SemiTolva 3"
}

# Posiciones según el tipo de unidad
posiciones_tractor = [
    "Eje 1 - Dirección Izquierda", "Eje 1 - Dirección Derecha",
    "Eje 2 - Tracción Izquierda Externa", "Eje 2 - Tracción Izquierda Interna",
    "Eje 2 - Tracción Derecha Externa", "Eje 2 - Tracción Derecha Interna",
    "Auxilio / Repuesto Tractor"
]

posiciones_tolva = [
    "Eje 1 - Izquierda Externa", "Eje 1 - Izquierda Interna",
    "Eje 1 - Derecha Externa", "Eje 1 - Derecha Interna",
    "Eje 2 - Izquierda Externa", "Eje 2 - Izquierda Interna",
    "Eje 2 - Derecha Externa", "Eje 2 - Derecha Interna",
    "Eje 3 - Izquierda Externa", "Eje 3 - Izquierda Interna",
    "Eje 3 - Derecha Externa", "Eje 3 - Derecha Interna",
    "Auxilio / Repuesto Tolva"
]

st.title("🛞 Sistema de Control e Inspección de Neumáticos")
st.markdown("Registro de presión (PSI), profundidad de dibujo (mm) e historial de mantenimiento por unidad.")

# Menú de navegación interno
menu = st.sidebar.radio("Navegación:", ["📝 Inspección / Carga", "📊 Historial y Reportes"])

# ---------------------------------------------------------
# OPCIÓN 1: INSPECCIÓN Y CARGA DE DATOS
# ---------------------------------------------------------
if menu == "📝 Inspección / Carga":
    st.subheader("📋 Registro de Medición de Neumático")
    
    tipo_vehiculo = st.radio("Selecciona el tipo de unidad:", ["Tractocamión (Mercedes Benz)", "SemiTolva (RANDON)"], horizontal=True)
    
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        if tipo_vehiculo == "Tractocamión (Mercedes Benz)":
            patente_sel = st.selectbox("Patente del Tractor", list(tractores.keys()))
            vehiculo_str = f"{tractores[patente_sel]} ({patente_sel})"
            posiciones_disponibles = posiciones_tractor
        else:
            patente_sel = st.selectbox("Patente de la SemiTolva", list(tolvas.keys()))
            vehiculo_str = f"{tolvas[patente_sel]} ({patente_sel})"
            posiciones_disponibles = posiciones_tolva

    with col_sel2:
        posicion_sel = st.selectbox("Posición / Ubicación de la Goma", posiciones_disponibles)

    st.divider()

    with st.form("form_gomas", clear_on_submit=True):
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            num_serie = st.text_input("Nº de Serie / Ficha de la Goma", value="MIC-101")
            marca_goma = st.selectbox("Marca del Neumático", ["Michelin", "Bridgestone", "Pirelli", "Fate", "Continental", "Goodyear", "Otra"])
            presion_psi = st.number_input("Presión Medida (PSI)", min_value=0, max_value=160, value=110, step=1)
            
        with col_g2:
            profundidad_mm = st.number_input("Profundidad de Dibujo (mm)", min_value=0.0, max_value=25.0, value=12.0, step=0.5)
            estado_goma = st.selectbox("Diagnóstico / Estado Operativo", [
                "OK / En Buen Estado",
                "Alerta: Requiere Aire (Baja Presión)",
                "Alerta: Para Rotación / Mover de Eje",
                "Crítico: Mandar a Recapado / Recauchutado",
                "Fuera de Servicio / Para Cambio Urgente"
            ])
            inspector = st.text_input("Nombre del Inspector / Mecánico")

        # Alertas preventivas en pantalla
        if profundidad_mm < 4.0:
            st.warning("⚠️ ALERTA: Profundidad menor a 4.0 mm. Se sugiere enviar a recapado o rotar.")
        if presion_psi < 90:
            st.error("🚨 ALERTA CRÍTICA: Presión por debajo de 90 PSI.")

        btn_guardar = st.form_submit_button("💾 GUARDAR REGISTRO DE NEUMÁTICO", use_container_width=True)
        
        if btn_guardar:
            if inspector.strip() == "":
                st.error("⚠️ Debes ingresar el nombre del inspector.")
            else:
                try:
                    df_existente = conn.read(worksheet="Control_Gomas", ttl=0)
                except Exception:
                    df_existente = pd.DataFrame()

                nueva_fila = pd.DataFrame([{
                    "Fecha/Hora": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Vehículo": vehiculo_str,
                    "Patente": patente_sel,
                    "Posición Eje": posicion_sel,
                    "Nº Serie": num_serie,
                    "Marca": marca_goma,
                    "Presión (PSI)": presion_psi,
                    "Profundidad (mm)": profundidad_mm,
                    "Estado": estado_goma,
                    "Inspector": inspector
                }])
                
                df_actualizado = pd.concat([df_existente, nueva_fila], ignore_index=True)
                conn.update(worksheet="Control_Gomas", data=df_actualizado)
                st.success(f"✅ ¡Registro de neumático ({num_serie}) guardado exitosamente!")

# ---------------------------------------------------------
# OPCIÓN 2: HISTORIAL Y DESCARGA DE EXCEL
# ---------------------------------------------------------
else:
    st.subheader("📊 Historial de Inspecciones de Neumáticos")
    
    if st.button("🔄 Actualizar Registros"):
        st.cache_data.clear()
        st.rerun()

    try:
        df_datos = conn.read(worksheet="Control_Gomas", ttl=0)
        st.dataframe(df_datos, use_container_width=True)

        # Botón para descargar Excel
        import io
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_datos.to_excel(writer, index=False, sheet_name='Control_Gomas')
        
        st.download_button(
            label="📥 Descargar Reporte de Neumáticos en Excel (.xlsx)",
            data=buffer.getvalue(),
            file_name=f"Reporte_Neumaticos_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        st.info("Aún no hay mediciones registradas en la hoja 'Control_Gomas'.")
