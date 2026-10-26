import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA Y CONEXIÓN
# ---------------------------------------------------------
st.set_page_config(page_title="Control de Rodados y Neumáticos - XIMA SRL", layout="wide", page_icon="🛞")

# Conexión central con Google Sheets (usa la misma configuración de tus secrets)
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("🛞 Control de Rodados y Gestión de Neumáticos - XIMA SRL")
st.markdown("Sistema vinculado a Google Sheets para actualización de cubiertas y bitácora histórica.")

# Lista de solapas correspondientes a cada unidad en tu Google Sheet
hojas_vehiculos = [
    "ATEGO AH395LS",
    "ACTROS AG506KW",
    "1735 AB032RM",
    "1735 AB020RG",
    "IVECO AG096CP",
    "IVECO AC737ZZ",
    "TOLVA AC738FC",
    "TOLVA AF720XG",
    "BATEA AC738HC",
    "SEMI AC116DF"
]

menu = st.sidebar.radio("Navegación:", [
    "🛠️ Ver / Modificar Neumáticos por Unidad", 
    "📊 Historial de Cambios"
])

# ---------------------------------------------------------
# OPCIÓN 1: MODIFICAR Y GESTIONAR NEUMÁTICOS POR UNIDAD
# ---------------------------------------------------------
if menu == "🛠️ Ver / Modificar Neumáticos por Unidad":
    st.subheader("📋 Planilla de Rodados por Unidad")
    
    unidad_seleccionada = st.selectbox("Seleccione Unidad / Vehículo:", hojas_vehiculos)
    
    try:
        # Leer la solapa correspondiente desde Google Sheets
        df_unidad = conn.read(worksheet=unidad_seleccionada, ttl=0)
        
        st.markdown(f"### 🚛 Unidad: **{unidad_seleccionada}**")
        
        # Mostrar la planilla actual de la unidad
        st.dataframe(df_unidad, use_container_width=True)

    except Exception as e:
        st.warning(f"⚠️ No se pudo leer la solapa '{unidad_seleccionada}'. Verifica que exista exactamente con ese nombre en tu Google Sheet.")

    st.markdown("---")
    st.markdown("### ✍️ Registrar Cambio o Recambio de Cubierta")
    
    col1, col2 = st.columns(2)
    
    with col1:
        posicion = st.selectbox("Posición del Neumático:", [
            "Eje Delantero - Izquierdo",
            "Eje Delantero - Derecho",
            "Eje Tracción - Izquierdo Ext.",
            "Eje Tracción - Izquierdo Int.",
            "Eje Tracción - Derecho Int.",
            "Eje Tracción - Derecho Ext.",
            "Balancín / Eje Neumático",
            "Auxilio"
        ], key="rod_pos")
        
        cod_anterior = st.text_input("Código Interno Anterior (ej: INT 166):", key="rod_cod_ant")
        cod_nuevo = st.text_input("Código Interno Nuevo (ej: INT 180):", key="rod_cod_nuevo")
        
    with col2:
        marca_modelo = st.text_input("Marca y Modelo:", placeholder="ej: FATE 1425 / Recauchutada", key="rod_marca")
        kilometraje = st.number_input("Kilometraje actual de la unidad:", min_value=0, value=100000, step=500, key="rod_km")
        motivo = st.selectbox("Motivo del cambio:", [
            "Desgaste normal",
            "Pinchadura / Rotura",
            "Rotación entre ejes",
            "Recauche",
            "Auxilio utilizado",
            "Otro"
        ], key="rod_motivo")
        
        responsable = st.text_input("Responsable del registro:", value="Franco Luna", key="rod_resp")
        obs_cambio = st.text_input("Observaciones breves:", placeholder="ej: Se alinea el tren delantero", key="rod_obs")

    st.divider()
    btn_guardar_cambio = st.button("💾 GUARDAR CAMBIO Y ACTUALIZAR HISTORIAL", type="primary", use_container_width=True)

    if btn_guardar_cambio:
        if not cod_nuevo or cod_nuevo.strip() == "":
            st.warning("⚠️ Debe ingresar el código interno del nuevo neumático.")
        else:
            with st.spinner("Registrando cambio en Google Sheets..."):
                try:
                    # 1. Leer o inicializar la solapa de Historial_Cambios
                    try:
                        df_hist = conn.read(worksheet="Historial_Cambios", ttl=0)
                    except Exception:
                        df_hist = pd.DataFrame(columns=[
                            "Fecha", "Unidad", "Posición", "Código Anterior", 
                            "Código Nuevo", "Marca / Modelo", "Kilometraje", 
                            "Motivo", "Responsable", "Observaciones"
                        ])

                    # 2. Crear la nueva fila de historial
                    nueva_fila = pd.DataFrame([{
                        "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "Unidad": unidad_seleccionada,
                        "Posición": posicion,
                        "Código Anterior": cod_anterior if cod_anterior else "N/D",
                        "Código Nuevo": cod_nuevo,
                        "Marca / Modelo": marca_modelo if marca_modelo else "N/D",
                        "Kilometraje": kilometraje,
                        "Motivo": motivo,
                        "Responsable": responsable,
                        "Observaciones": obs_cambio
                    }])

                    # 3. Actualizar la solapa 'Historial_Cambios' en Google Sheets
                    df_actualizado = pd.concat([df_hist, nueva_fila], ignore_index=True)
                    conn.update(worksheet="Historial_Cambios", data=df_actualizado)

                    st.success(f"✅ ¡Cambio registrado con éxito para **{unidad_seleccionada}** ({posicion}) y guardado en Google Sheets!")
                    st.cache_data.clear()

                except Exception as e:
                    st.error(f"❌ Error al actualizar Google Sheets: {e}")

# ---------------------------------------------------------
# OPCIÓN 2: VER HISTORIAL DE CAMBIOS
# ---------------------------------------------------------
else:
    st.subheader("📊 Historial General de Cambios de Neumáticos")
    
    if st.button("🔄 Actualizar Registros"):
        st.cache_data.clear()
        st.rerun()

    try:
        # Leer el historial desde Google Sheets
        df_historial = conn.read(worksheet="Historial_Cambios", ttl=0)
        
        if df_historial.empty:
            st.info("Aún no hay registros en el historial de cambios.")
        else:
            unidades_hist = ["Todas"] + list(df_historial["Unidad"].unique())
            filtro_h = st.selectbox("Filtrar historial por Unidad:", unidades_hist)
            
            df_filtrado = df_historial if filtro_h == "Todas" else df_historial[df_historial["Unidad"] == filtro_h]
            
            st.markdown(f"Mostrando **{len(df_filtrado)}** registros de cambios:")
            st.dataframe(df_filtrado.iloc[::-1], use_container_width=True)

    except Exception:
        st.info("Aún no se ha creado la pestaña 'Historial_Cambios' en tu Google Sheet. Realiza tu primer registro de cambio para generarla automáticamente.")
