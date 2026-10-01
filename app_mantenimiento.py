import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import base64
from PIL import Image
import io

# Configuración de página
st.set_page_config(page_title="Mantenimiento y Fotos de Cambios", layout="wide", page_icon="🛠️")

# Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Lista de Unidades
unidades_list = [
    "Camión 01 - Mercedes Benz",
    "Camión 02 - Scania",
    "Camión 03 - Volvo",
    "Pala Cargadora",
    "Excavadora",
    "Otra Unidad"
]

st.title("🛠️ Registro de Mantenimientos, Cambios y Fotos")
st.markdown("Carga de servicios realizados con **evidencia fotográfica** (Cámara o Galería).")

menu = st.sidebar.radio("Navegación:", ["📸 Registrar Mantenimiento / Foto", "📊 Historial y Comprobantes"])

# Función para convertir imagen a Base64 (para guardar en la celda del Sheet)
def convertir_imagen_a_base64(uploaded_file):
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        # Redimensionar si es muy grande para optimizar espacio
        image.thumbnail((800, 800))
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG", quality=70)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/jpeg;base64,{img_str}"
    return ""

# ---------------------------------------------------------
# OPCIÓN 1: REGISTRAR MANTENIMIENTO CON FOTO
# ---------------------------------------------------------
if menu == "📸 Registrar Mantenimiento / Foto":
    st.subheader("📝 Nuevo Registro de Mantenimiento o Cambio de Repuesto")
    
    with st.form("form_mantenimiento", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            fecha = st.date_input("Fecha del Trabajo", value=datetime.now().date())
            unidad_sel = st.selectbox("Unidad / Camión / Máquina", unidades_list)
            unidad = st.text_input("Especifique Unidad") if unidad_sel == "Otra Unidad" else unidad_sel
            
            tipo_trabajo = st.selectbox("Tipo de Mantenimiento / Cambio", [
                "🛢️ Cambio de Aceite y Filtros",
                "🔩 Cambio de Repuesto / Pieza Rota",
                "🛞 Servicio de Neumáticos / Alineación",
                "⚡ Reparación Eléctrica",
                "🔨 Mantenimiento General / Taller",
                "🧾 Comprobante / Factura de Compra"
            ])
            
            km_horas = st.number_input("Kilometraje actual u Horas de Motor", min_value=0, value=100000, step=500)
            
        with col2:
            mecanico = st.selectbox("Mecánico / Responsable", [
                "Rocho (Mecánico)",
                "Daniel (Mecánico)",
                "Taller Externo",
                "Otro"
            ])
            repuestos_usados = st.text_input("Repuestos o Insumos Utilizados", placeholder="ej: Filtro Mann W950, Aceite 15W40 20L, etc.")
            costo = st.number_input("Costo Aproximado / Factura ($)", min_value=0.0, value=0.0, step=100.0)
            obs = st.text_area("Detalle / Observaciones del trabajo realizado", placeholder="Describa el estado de la pieza reemplazada o el motivo del cambio...")

        st.divider()
        st.markdown("### 📷 Adjuntar Foto / Evidencia Fotográfica")
        
        opcion_foto = st.radio("Método para cargar la foto:", ["📷 Sacar foto ahora (Cámara Celular/Webcam)", "📁 Cargar desde la Galería/Archivos"], horizontal=True)
        
        foto_capturada = None
        if "Cámara" in opcion_foto:
            foto_capturada = st.camera_input("Toma la foto del repuesto cambiado o factura:")
        else:
            foto_capturada = st.file_uploader("Selecciona la imagen desde tu dispositivo:", type=["jpg", "png", "jpeg"])

        btn_guardar = st.form_submit_button("💾 GUARDAR MANTENIMIENTO Y FOTO", use_container_width=True)
        
        if btn_guardar:
            if unidad.strip() == "":
                st.error("⚠️ Debe especificar la unidad o camión.")
            else:
                str_foto_base64 = convertir_imagen_a_base64(foto_capturada) if foto_capturada else ""
                
                try:
                    df_existente = conn.read(worksheet="Mantenimientos_Fotos", ttl=0)
                except Exception:
                    df_existente = pd.DataFrame()

                nueva_fila = pd.DataFrame([{
                    "Fecha": fecha.strftime("%d/%m/%Y"),
                    "Unidad": unidad,
                    "Tipo Trabajo": tipo_trabajo,
                    "Kilometraje/Horas": km_horas,
                    "Repuestos Utilizados": repuestos_usados,
                    "Mecánico/Responsable": mecanico,
                    "Foto Evidencia": str_foto_base64,
                    "Costo Aprox": costo,
                    "Observaciones": obs
                }])
                
                df_actualizado = pd.concat([df_existente, nueva_fila], ignore_index=True)
                conn.update(worksheet="Mantenimientos_Fotos", data=df_actualizado)
                
                st.success(f"✅ ¡Mantenimiento de **{unidad}** guardado con éxito con su foto adjunta!")

# ---------------------------------------------------------
# OPCIÓN 2: HISTORIAL Y VISUALIZADOR DE FOTOS
# ---------------------------------------------------------
else:
    st.subheader("📊 Historial de Mantenimientos y Fotos")
    
    if st.button("🔄 Actualizar Registros"):
        st.cache_data.clear()
        st.rerun()

    try:
        df_mant = conn.read(worksheet="Mantenimientos_Fotos", ttl=0)
        
        if df_mant.empty:
            st.info("Aún no hay mantenimientos ni fotos registradas.")
        else:
            # Filtro por unidad
            unidades_disponibles = ["Todas"] + list(df_mant["Unidad"].unique())
            filtro_u = st.selectbox("Filtrar por Unidad:", unidades_disponibles)
            
            if filtro_u != "Todas":
                df_filtrado = df_mant[df_mant["Unidad"] == filtro_u]
            else:
                df_filtrado = df_mant

            # Vista en fichas/tarjetas con fotos
            st.markdown("---")
            for idx, row in df_filtrado.iloc[::-1].iterrows(): # Mostrar los más recientes primero
                with st.expander(f"🛠️ {row['Fecha']} - {row['Unidad']} ({row['Tipo Trabajo']})"):
                    c1, c2 = st.columns([2, 1])
                    
                    with c1:
                        st.markdown(f"**Mecánico/Responsable:** {row['Mecánico/Responsable']}")
                        st.markdown(f"**Kilometraje / Horas:** {row['Kilometraje/Horas']} km/hs")
                        st.markdown(f"**Repuestos Usados:** {row['Repuestos Utilizados']}")
                        st.markdown(f"**Costo Aprox:** ${row['Costo Aprox']}")
                        st.markdown(f"**Observaciones:** {row['Observaciones']}")
                        
                    with c2:
                        foto_data = row.get("Foto Evidencia", "")
                        if pd.notna(foto_data) and str(foto_data).startswith("data:image"):
                            st.image(foto_data, caption=f"Foto Evidencia ({row['Unidad']})", use_container_width=True)
                        else:
                            st.info("Sin foto adjunta")

    except Exception as e:
        st.error(f"Error al cargar la pestaña 'Mantenimientos_Fotos': {e}")
