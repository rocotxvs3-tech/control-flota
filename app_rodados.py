import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA Y CONEXIÓN
# ---------------------------------------------------------
st.set_page_config(page_title="Control de Rodados y Neumáticos - XIMA SRL", layout="wide", page_icon="🛞")

conn = st.connection("gsheets", type=GSheetsConnection)

st.title("🛞 Control de Rodados y Gestión de Neumáticos - XIMA SRL")
st.markdown("Sistema sincronizado en tiempo real con Google Drive (Actualiza la unidad y el historial automáticamente).")

# Lista exacta de solapas (vehículos) en tu Google Sheet
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
    "📊 Historial de Cambios en Google Drive"
])

# ---------------------------------------------------------
# OPCIÓN 1: MODIFICAR Y GESTIONAR NEUMÁTICOS POR UNIDAD
# ---------------------------------------------------------
if menu == "🛠️ Ver / Modificar Neumáticos por Unidad":
    st.subheader("📋 Planilla de Rodados por Unidad")
    
    unidad_seleccionada = st.selectbox("Seleccione Unidad / Vehículo:", hojas_vehiculos)
    
    try:
        # Leer la solapa del vehículo seleccionado desde Google Sheets
        df_unidad = conn.read(worksheet=unidad_seleccionada, ttl=0)
        
        st.markdown(f"### 🚛 Unidad: **{unidad_seleccionada}**")
        st.dataframe(df_unidad, use_container_width=True)

    except Exception as e:
        st.error(f"⚠️ No se pudo leer la solapa '{unidad_seleccionada}': {e}")
        st.info("💡 Asegúrate de que la pestaña en tu Google Sheet se llame exactamente igual.")
        st.stop()

    st.markdown("---")
    st.markdown("### ✍️ Registrar Cambio o Recambio de Cubierta")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Posiciones basadas en el esquema de tus planillas
        posicion = st.selectbox("Posición del Neumático a Modificar:", [
            "Auxilio",
            "Eje Delantero - Lado Izquierdo",
            "Eje Delantero - Lado Derecho",
            "Eje Tracción - Izq. Exterior",
            "Eje Tracción - Izq. Interior",
            "Eje Tracción - Der. Interior",
            "Eje Tracción - Der. Exterior",
            "Balancín / Eje Neumático"
        ], key="rod_pos")
        
        cod_anterior = st.text_input("Código Interno Anterior (ej: INT 166):", key="rod_cod_ant")
        cod_nuevo = st.text_input("Código Interno Nuevo / A Colocar (ej: INT 180):", key="rod_cod_nuevo")
        
    with col2:
        marca_modelo = st.text_input("Marca y Modelo:", placeholder="ej: FATE 1425 / Recauchutada", key="rod_marca")
        kilometraje = st.number_input("Kilometraje actual de la cubierta/unidad:", min_value=0, value=100000, step=500, key="rod_km")
        
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
    btn_guardar_cambio = st.button("💾 ACTUALIZAR PLANILLA Y GUARDAR EN GOOGLE DRIVE", type="primary", use_container_width=True)

    if btn_guardar_cambio:
        if not cod_nuevo or cod_nuevo.strip() == "":
            st.warning("⚠️ Debe ingresar el código interno del nuevo neumático.")
        else:
            with st.spinner("Actualizando planilla del camión y registrando historial en Google Drive..."):
                try:
                    # 1. ACTUALIZAR LAS CELDAS EN LA PLANILLA DEL VEHÍCULO
                    # Mapeo de filas/columnas según la estructura fija de tus planillas de rodados:
                    # - Auxilio: Fila 1 (Marca), Fila 3 (Cód), Fila 4 (Kilom) en col 2
                    # - Eje Delantero Izq: Fila 6 (Marca), Fila 8 (Cód), Fila 9 (Kilom) en col 2
                    # - Eje Delantero Der: Fila 6 (Marca), Fila 8 (Cód), Fila 9 (Kilom) en col 7
                    # - Eje Tracción Izq Ext: Fila 11 (Marca), Fila 13 (Cód), Fila 14 (Kilom) en col 2
                    # - Eje Tracción Izq Int: Fila 11 (Marca), Fila 13 (Cód), Fila 14 (Kilom) en col 4
                    # - Eje Tracción Der Int: Fila 11 (Marca), Fila 13 (Cód), Fila 14 (Kilom) en col 5
                    # - Eje Tracción Der Ext: Fila 11 (Marca), Fila 13 (Cód), Fila 14 (Kilom) en col 7
                    
                    r_marca, r_cod, r_km, col_idx = 1, 3, 4, 2 # Por defecto Auxilio
                    
                    if "Delantero - Lado Izquierdo" in posicion:
                        r_marca, r_cod, r_km, col_idx = 6, 8, 9, 2
                    elif "Delantero - Lado Derecho" in posicion:
                        r_marca, r_cod, r_km, col_idx = 6, 8, 9, 7
                    elif "Tracción - Izq. Exterior" in posicion:
                        r_marca, r_cod, r_km, col_idx = 11, 13, 14, 2
                    elif "Tracción - Izq. Interior" in posicion:
                        r_marca, r_cod, r_km, col_idx = 11, 13, 14, 4
                    elif "Tracción - Der. Interior" in posicion:
                        r_marca, r_cod, r_km, col_idx = 11, 13, 14, 5
                    elif "Tracción - Der. Exterior" in posicion:
                        r_marca, r_cod, r_km, col_idx = 11, 13, 14, 7
                    elif "Balancín" in posicion:
                        r_marca, r_cod, r_km, col_idx = 16, 18, 19, 2

                    # Aplicar la modificación en el DataFrame del vehículo si las dimensiones lo permiten
                    if df_unidad.shape[0] > r_km and df_unidad.shape[1] > col_idx:
                        df_unidad.iat[r_marca, col_idx] = f"Marca: {marca_modelo}"
                        df_unidad.iat[r_cod, col_idx] = f"Cód.: {cod_nuevo}"
                        df_unidad.iat[r_km, col_idx] = f"Kilom.: {kilometraje}"
                        
                        # Actualizar observaciones generales en la parte baja si se ingresó algo
                        if obs_cambio and df_unidad.shape[0] > 24:
                            df_unidad.iat[24, 1] = f"OBSERVACIONES: {obs_cambio} (Ref: {posicion} - {datetime.now().strftime('%d/%m/%Y')})"

                        # Enviar la planilla del camión actualizada a Google Drive
                        conn.update(worksheet=unidad_seleccionada, data=df_unidad)

                    # 2. REGISTRAR EN LA SOLAPA DE HISTORIAL_CAMBIOS
                    try:
                        df_hist = conn.read(worksheet="Historial_Cambios", ttl=0)
                    except Exception:
                        df_hist = pd.DataFrame(columns=[
                            "Fecha", "Unidad", "Posición", "Código Anterior", 
                            "Código Nuevo", "Marca / Modelo", "Kilometraje", 
                            "Motivo", "Responsable", "Observaciones"
                        ])

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

                    df_actualizado = pd.concat([df_hist, nueva_fila], ignore_index=True)
                    conn.update(worksheet="Historial_Cambios", data=df_actualizado)

                    st.success(f"✅ ¡Modificación aplicada en la planilla de **{unidad_seleccionada}** y registrada en el historial de Google Drive!")
                    st.cache_data.clear()

                except Exception as e:
                    st.error(f"❌ Error al actualizar Google Drive: {e}")

# ---------------------------------------------------------
# OPCIÓN 2: VER HISTORIAL DESDE GOOGLE DRIVE
# ---------------------------------------------------------
else:
    st.subheader("📊 Historial General de Cambios (Google Drive)")
    
    if st.button("🔄 Actualizar Registros"):
        st.cache_data.clear()
        st.rerun()

    try:
        df_historial = conn.read(worksheet="Historial_Cambios", ttl=0)
        
        if df_historial.empty:
            st.info("Aún no hay registros en el historial de cambios.")
        else:
            unidades_hist = ["Todas"] + list(df_historial["Unidad"].unique())
            filtro_h = st.selectbox("Filtrar historial por Unidad:", unidades_hist)
            
            df_filtrado = df_historial if filtro_h == "Todas" else df_historial[df_historial["Unidad"] == filtro_h]
            
            st.markdown(f"Mostrando **{len(df_filtrado)}** registros guardados en Drive:")
            st.dataframe(df_filtrado.iloc[::-1], use_container_width=True)

    except Exception:
        st.info("Aún no se ha creado la pestaña 'Historial_Cambios' en tu Google Sheet. Realiza tu primer registro en la pestaña anterior para generarla automáticamente en Drive.")
