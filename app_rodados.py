import streamlit as st
import pandas as pd
from datetime import datetime
from openpyxl import load_workbook
import os

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# ---------------------------------------------------------
st.set_page_config(page_title="Control de Rodados y Neumáticos - XIMA SRL", layout="wide", page_icon="🛞")

EXCEL_PATH = "CONTROL DE RODADOS XIMA SRL 2026.xlsx"

st.title("🛞 Control de Rodados y Gestión de Neumáticos - XIMA SRL")
st.markdown("Gestión de cubiertas y bitácora histórica basada en archivos Excel (`.xlsx`).")

# Verificar si el archivo Excel existe
if not os.path.exists(EXCEL_PATH):
    st.error(f"⚠️ No se encuentra el archivo '{EXCEL_PATH}' en el repositorio. Asegúrate de subirlo junto con app_rodados.py.")
    st.stop()

# Cargar las solapas del archivo Excel
try:
    xls = pd.ExcelFile(EXCEL_PATH)
    hojas_vehiculos = [h for h in xls.sheet_names if h not in ["Hoja1", "Historial_Cambios"]]
except Exception as e:
    st.error(f"❌ Error al leer el archivo Excel: {e}")
    st.stop()

menu = st.sidebar.radio("Navegación:", [
    "🛠️ Ver / Modificar Neumáticos por Unidad", 
    "📊 Historial de Cambios y Descarga"
])

# ---------------------------------------------------------
# OPCIÓN 1: MODIFICAR Y GESTIONAR NEUMÁTICOS POR UNIDAD
# ---------------------------------------------------------
if menu == "🛠️ Ver / Modificar Neumáticos por Unidad":
    st.subheader("📋 Planilla de Rodados por Unidad")
    
    unidad_seleccionada = st.selectbox("Seleccione Unidad / Vehículo:", hojas_vehiculos)
    
    try:
        # Leer la solapa del vehículo seleccionado
        df_unidad = pd.read_excel(EXCEL_PATH, sheet_name=unidad_seleccionada, header=None)
        
        st.markdown(f"### 🚛 Unidad: **{unidad_seleccionada}**")
        st.dataframe(df_unidad, use_container_width=True)

    except Exception as e:
        st.error(f"⚠️ Error al leer la solapa '{unidad_seleccionada}': {e}")

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
    btn_guardar_cambio = st.button("💾 GUARDAR CAMBIO EN EL EXCEL", type="primary", use_container_width=True)

    if btn_guardar_cambio:
        if not cod_nuevo or cod_nuevo.strip() == "":
            st.warning("⚠️ Debe ingresar el código interno del nuevo neumático.")
        else:
            with st.spinner("Actualizando archivo Excel..."):
                try:
                    # Abrir el libro con openpyxl para conservar todas las solapas y formato original
                    wb = load_workbook(EXCEL_PATH)
                    
                    # 1. Verificar o crear la hoja de Historial
                    if "Historial_Cambios" not in wb.sheetnames:
                        ws_hist = wb.create_sheet("Historial_Cambios")
                        ws_hist.append([
                            "Fecha", "Unidad", "Posición", "Código Anterior", 
                            "Código Nuevo", "Marca / Modelo", "Kilometraje", 
                            "Motivo", "Responsable", "Observaciones"
                        ])
                    else:
                        ws_hist = wb["Historial_Cambios"]
                    
                    # 2. Agregar la nueva fila al historial
                    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
                    ws_hist.append([
                        fecha_actual,
                        unidad_seleccionada,
                        posicion,
                        cod_anterior if cod_anterior else "N/D",
                        cod_nuevo,
                        marca_modelo if marca_modelo else "N/D",
                        kilometraje,
                        motivo,
                        responsable,
                        obs_cambio
                    ])
                    
                    # 3. Guardar cambios en el archivo físico
                    wb.save(EXCEL_PATH)
                    
                    st.success(f"✅ ¡Cambio registrado con éxito para **{unidad_seleccionada}** y guardado en el archivo Excel!")
                    st.cache_data.clear()

                except Exception as e:
                    st.error(f"❌ Error al modificar el archivo Excel: {e}")

# ---------------------------------------------------------
# OPCIÓN 2: VER HISTORIAL Y DESCARGAR EXCEL ACTUALIZADO
# ---------------------------------------------------------
else:
    st.subheader("📊 Historial de Cambios y Descarga de Planilla")
    
    if st.button("🔄 Actualizar Registros"):
        st.cache_data.clear()
        st.rerun()

    try:
        # Leer la solapa de historial directamente del archivo Excel
        df_historial = pd.read_excel(EXCEL_PATH, sheet_name="Historial_Cambios")
        
        if df_historial.empty:
            st.info("Aún no hay registros en el historial de cambios.")
        else:
            unidades_hist = ["Todas"] + list(df_historial["Unidad"].unique())
            filtro_h = st.selectbox("Filtrar historial por Unidad:", unidades_hist)
            
            df_filtrado = df_historial if filtro_h == "Todas" else df_historial[df_historial["Unidad"] == filtro_h]
            
            st.markdown(f"Mostrando **{len(df_filtrado)}** registros de cambios:")
            st.dataframe(df_filtrado.iloc[::-1], use_container_width=True)

    except Exception:
        st.info("Aún no se ha generado la solapa 'Historial_Cambios'. Realiza tu primer registro en la pestaña anterior para generarla automáticamente.")

    st.markdown("---")
    st.markdown("### 📥 Descargar Planilla Completa Actualizada")
    st.markdown("Puedes descargar el archivo `.xlsx` con todas las modificaciones y el historial integrado en cualquier momento:")
    
    if os.path.exists(EXCEL_PATH):
        with open(EXCEL_PATH, "rb") as f:
            st.download_button(
                label="📥 DESCARGAR EXCEL ACTUALIZADO",
                data=f,
                file_name="CONTROL_DE_RODADOS_XIMA_ACTUALIZADO.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
