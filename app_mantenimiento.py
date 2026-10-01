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

# Función para convertir imagen a Base64
def convertir_imagen_a_base64(uploaded_file):
    if uploaded_file is not None:
        try:
            image = Image.open(uploaded_file)
            image.thumbnail((800, 800))  # Redimensionar para optimizar peso
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG", quality=70)
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return f"data:image/jpeg;base64,{img_str}"
        except Exception as e:
            st.error(f"Error al procesar la imagen: {e}")
            return ""
    return ""

# Función para limpiar campos al terminar
def limpiar_formulario():
    keys_a_limpiar = [
        "mant_unidad_otra", "mant_repuestos", "mant_costo", 
        "mant_obs", "mant_foto_cam", "mant_foto_file"
    ]
    for key in keys_a_limpiar:
        if key in st.session_state:
            del st.session_state[key]

# ---------------------------------------------------------
# OPCIÓN 1: REGISTRAR MANTENIMIENTO CON FOTO (MEMORIA ACTIVA)
# ---------------------------------------------------------
if menu == "📸 Registrar Mantenimiento / Foto":
    st.subheader("📝 Nuevo Registro de Mantenimiento o Cambio de Repuesto")
    st.caption("💡 Nota: Puedes escribir los datos y sacar la foto en el orden que quieras, **no se borrará nada**.")

    col1, col2 = st.columns(2)
    
    with col1:
        fecha = st.date_input("Fecha del Trabajo", value=datetime.now().date(), key="mant_fecha")
        unidad_sel = st.selectbox("Unidad / Camión / Máquina", unidades_list, key="mant_unidad_sel")
        
        if unidad_sel == "Otra Unidad":
            unidad = st.text_input("Especifique Unidad", key="mant_unidad_otra")
        else:
            unidad = unidad_sel
        
        tipo_trabajo = st.selectbox("Tipo de Mantenimiento / Cambio", [
            "🛢️ Cambio de Aceite y Filtros",
            "🔩 Cambio de Repuesto / Pieza Rota",
            "🛞 Servicio de Neumáticos / Alineación",
            "⚡ Reparación Eléctrica",
            "🔨 Mantenimiento General / Taller",
            "🧾 Comprobante / Factura de Compra"
        ], key="mant_tipo")
        
        km_horas = st.number_input("Kilometraje actual u Horas de Motor", min_value=0, value=100000, step=500, key="mant_km")
        
    with col2:
        mecanico = st.selectbox("Mecánico / Responsable", [
            "Rocho (Mecánico)",
            "Daniel (Mecánico)",
            "Taller Externo",
            "Otro"
        ], key="mant_mecanico")
        
        repuestos_usados = st.text_input("Repuestos o Insumos Utilizados", placeholder="ej: Filtro Mann W950, Aceite 15W40 20L, etc.", key="mant_repuestos")
        costo = st.number_input("Costo Aproximado / Factura ($)", min_value=0.0, value=0.0, step=100.0, key="mant_costo")
        obs = st.text_area("Detalle / Observaciones del trabajo realizado", placeholder="Describa el estado de la pieza reemplazada o el motivo del cambio...", key="mant_obs")

    st.divider()
    st.markdown("### 📷 Adjuntar Foto / Evidencia Fotográfica")
    
    opcion_foto = st.radio("Método para cargar la foto:", ["📷 Sacar foto ahora (Cámara Celular/Webcam)", "📁 Cargar desde la Galería/Archivos"], horizontal=True, key="mant_metodo_foto")
    
    foto_capturada = None
    if "Cámara" in opcion_foto:
        foto_capturada = st.camera_input("Toma la foto del repuesto cambiado o factura:", key="mant_foto_cam")
    else:
        foto_capturada = st.file_uploader("Selecciona la imagen desde tu dispositivo:", type=["jpg", "png", "jpeg"], key="mant_foto_file")

    st.markdown("---")
    btn_guardar = st.button("💾 GUARDAR MANTENIMIENTO Y FOTO", use_container_width=True, type="primary")
    
    if btn_guardar:
        if not unidad or unidad.strip() == "":
            st.error("⚠️ Debe especificar la unidad o camión.")
        else:
            with st.spinner("Guardando registro y procesando imagen..."):
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
        st.info("Aún no hay registros en la pestaña 'Mantenimientos_Fotos' o no se ha creado.")
