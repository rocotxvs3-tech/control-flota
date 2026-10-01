import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import cloudinary
import cloudinary.uploader

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA Y CONEXIONES
# ---------------------------------------------------------
st.set_page_config(page_title="Mantenimiento y Fotos HD", layout="wide", page_icon="🛠️")

# Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Configuración de Cloudinary para almacenamiento HD
try:
    cloudinary.config(
        cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
        api_key = st.secrets["CLOUDINARY_API_KEY"],
        api_secret = st.secrets["CLOUDINARY_API_SECRET"],
        secure = True
    )
except Exception:
    st.warning("⚠️️ Asegúrate de agregar las credenciales de Cloudinary en los Secrets de Streamlit.")

# ---------------------------------------------------------
# LISTA OFICIAL DE VEHÍCULOS Y EQUIPOS DE LA FLOTA
# ---------------------------------------------------------
unidades_list = [
    # Tractocamiones
    "MB Actros - AG506KW",
    "MB 1735 - AB020RG",
    "MB 1735 - AB032RM",
    "Iveco - AG096CP",
    "Iveco - AC737ZZ",
    # Semirremolques, Tolvas y Bateas
    "Tolva Randon - AF720XG",
    "Tolva Randon - AC738FC",
    "Tolva Randon - LBZ158",
    "Batea Randon - AC738HC",
    "Sola y Brusa - AC116DF",
    # Maquinarias y Taller
    "Pala Cargadora",
    "Excavadora",
    "General / Taller Base",
    "Otra Unidad"
]

st.title("🛠️ Registro de Mantenimientos y Fotos HD")

menu = st.sidebar.radio("Navegación:", ["📸 Registrar Mantenimiento / Foto HD", "📊 Historial y Comprobantes"])

# ---------------------------------------------------------
# FUNCIÓN PARA SUBIR IMAGEN EN ALTA CALIDAD A CLOUDINARY
# ---------------------------------------------------------
def subir_foto_alta_resolucion(file_buffer):
    if file_buffer is not None:
        try:
            respuesta = cloudinary.uploader.upload(
                file_buffer,
                folder="mantenimientos_flota",
                quality="auto:good"
            )
            return respuesta.get("secure_url", "")
        except Exception as e:
            st.error(f"❌ Error al subir imagen a Cloudinary: {e}")
            return ""
    return ""

# ---------------------------------------------------------
# OPCIÓN 1: REGISTRAR MANTENIMIENTO CON FOTO HD
# ---------------------------------------------------------
if menu == "📸 Registrar Mantenimiento / Foto HD":
    st.subheader("📝 Nuevo Registro con Foto HD")

    col1, col2 = st.columns(2)
    
    with col1:
        fecha = st.date_input("Fecha del Trabajo", value=datetime.now().date(), key="mant_fecha")
        unidad_sel = st.selectbox("Unidad / Camión / Equipo", unidades_list, key="mant_unidad_sel")
        unidad = st.text_input("Especifique Unidad", key="mant_unidad_otra") if unidad_sel == "Otra Unidad" else unidad_sel
        
        tipo_trabajo = st.selectbox("Tipo de Mantenimiento", [
            "🛢️ Cambio de Aceite y Filtros",
            "🔩 Cambio de Repuesto / Pieza Rota",
            "🛞 Servicio de Neumáticos / Alineación",
            "⚡ Reparación Eléctrica",
            "🔨 Mantenimiento General / Taller",
            "🧾 Comprobante / Factura de Compra"
        ], key="mant_tipo")
        
        km_horas = st.number_input("Kilometraje / Horas", min_value=0, value=100000, step=500, key="mant_km")
        
    with col2:
        mecanico = st.selectbox("Mecánico / Responsable", [
            "Rocho (Mecánico)", 
            "Daniel (Mecánico)", 
            "Taller Externo", 
            "Otro"
        ], key="mant_mecanico")
        
        repuestos_usados = st.text_input("Repuestos Utilizados", placeholder="ej: Filtro Mann, Aceite 15W40, etc.", key="mant_repuestos")
        costo = st.number_input("Costo Aproximado ($)", min_value=0.0, value=0.0, step=100.0, key="mant_costo")
        obs = st.text_area("Observaciones del trabajo", placeholder="Detalle del trabajo o causa de reemplazo...", key="mant_obs")

    st.divider()
    st.markdown("### 📷 Captura / Carga de Foto Evidencia HD")
    
    opcion_foto = st.radio("Cargar foto desde:", ["📷 Cámara del Celular", "📁 Archivos / Galería"], horizontal=True, key="mant_metodo")
    
    foto_capturada = None
    if "Cámara" in opcion_foto:
        foto_capturada = st.camera_input("Toma la foto:", key="mant_foto_cam")
    else:
        foto_capturada = st.file_uploader("Selecciona imagen en Alta Calidad:", type=["jpg", "png", "jpeg"], key="mant_foto_file")

    st.markdown("---")
    btn_guardar = st.button("💾 GUARDAR REGISTRO Y FOTO HD", use_container_width=True, type="primary")
    
    if btn_guardar:
        if not unidad or unidad.strip() == "":
            st.error("⚠️ Debe especificar la unidad o equipo.")
        else:
            with st.spinner("Subiendo foto en alta resolución y guardando en planilla..."):
                url_foto_hd = subir_foto_alta_resolucion(foto_capturada) if foto_capturada else ""

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
                    "Foto Evidencia": url_foto_hd,  # URL directa y limpia
                    "Costo Aprox": costo,
                    "Observaciones": obs
                }])
                
                df_actualizado = pd.concat([df_existente, nueva_fila], ignore_index=True)
                conn.update(worksheet="Mantenimientos_Fotos", data=df_actualizado)
                
                st.success(f"✅ ¡Mantenimiento de **{unidad}** guardado con éxito con su foto en alta resolución!")

# ---------------------------------------------------------
# OPCIÓN 2: HISTORIAL Y VISUALIZADOR DE FOTOS
# ---------------------------------------------------------
else:
    st.subheader("📊 Historial de Mantenimientos y Fotos HD")
    
    if st.button("🔄 Actualizar Registros"):
        st.cache_data.clear()
        st.rerun()

    try:
        df_mant = conn.read(worksheet="Mantenimientos_Fotos", ttl=0)
        
        if df_mant.empty:
            st.info("Aún no hay mantenimientos ni fotos registradas.")
        else:
            unidades_disponibles = ["Todas"] + list(df_mant["Unidad"].unique())
            filtro_u = st.selectbox("Filtrar por Unidad:", unidades_disponibles)
            
            df_filtrado = df_mant if filtro_u == "Todas" else df_mant[df_mant["Unidad"] == filtro_u]

            st.markdown("---")
            for idx, row in df_filtrado.iloc[::-1].iterrows():
                with st.expander(f"🛠️ {row['Fecha']} - {row['Unidad']} ({row['Tipo Trabajo']})"):
                    c1, c2 = st.columns([2, 1])
                    
                    with c1:
                        st.markdown(f"**Mecánico/Responsable:** {row['Mecánico/Responsable']}")
                        st.markdown(f"**Kilometraje / Horas:** {row['Kilometraje/Horas']} km/hs")
                        st.markdown(f"**Repuestos Usados:** {row['Repuestos Utilizados']}")
                        st.markdown(f"**Costo Aprox:** ${row['Costo Aprox']}")
                        st.markdown(f"**Observaciones:** {row['Observaciones']}")
                        
                    with c2:
                        url_foto = str(row.get("Foto Evidencia", "")).strip()

                        if pd.notna(url_foto) and url_foto.startswith("http"):
                            st.image(url_foto, caption=f"Foto HD ({row['Unidad']})", use_container_width=True)
                            st.link_button("🔎 Ampliar / Abrir Foto HD", url_foto, use_container_width=True)
                        else:
                            st.info("📷 Sin foto adjunta")

    except Exception as e:
        st.info("Asegúrate de haber creado la pestaña 'Mantenimientos_Fotos' en tu archivo de Google Sheets.")
