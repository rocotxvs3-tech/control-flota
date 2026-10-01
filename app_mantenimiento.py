import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

# ---------------------------------------------------------
# CONFIGURACIÓN E ID DE CARPETA DE GOOGLE DRIVE
# ---------------------------------------------------------
# ⚠️ Reemplaza este valor con el ID real de tu carpeta de Google Drive
FOLDER_ID_DRIVE = "COLOCA_AQUI_EL_ID_DE_TU_CARPETA_DE_DRIVE"

st.set_page_config(page_title="Mantenimiento y Fotos HD (Drive)", layout="wide", page_icon="🛠️")

# Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

unidades_list = [
    "Camión 01 - Mercedes Benz",
    "Camión 02 - Scania",
    "Camión 03 - Volvo",
    "Pala Cargadora",
    "Excavadora",
    "Otra Unidad"
]

st.title("🛠️ Registro de Mantenimientos y Fotos en Google Drive")

menu = st.sidebar.radio("Navegación:", ["📸 Registrar Mantenimiento / Foto HD", "📊 Historial y Comprobantes"])

# ---------------------------------------------------------
# FUNCIÓN PARA SUBIR FOTO EN ALTA RESOLUCIÓN A GOOGLE DRIVE
# ---------------------------------------------------------
def subir_foto_a_google_drive(file_buffer, nombre_archivo):
    try:
        # Obtener las credenciales de la Service Account desde st.secrets
        # Funciona con la estructura estándar de [connections.gsheets] de Streamlit
        creds_dict = dict(st.secrets["connections"]["gsheets"])
        
        scopes = ['https://www.googleapis.com/auth/drive']
        creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=scopes)
        
        service = build('drive', 'v3', credentials=creds)
        
        # Metadatos del archivo a subir
        file_metadata = {
            'name': nombre_archivo,
            'parents': [FOLDER_ID_DRIVE]
        }
        
        # Preparar el archivo en memoria
        media = MediaIoBaseUpload(io.BytesIO(file_buffer.getvalue()), mimetype='image/jpeg', resumable=True)
        
        # 1. Subir archivo
        archivo_creado = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        file_id = archivo_creado.get('id')
        
        # 2. Hacer que el archivo sea accesible por enlace público
        permiso_publico = {
            'type': 'anyone',
            'role': 'reader',
        }
        service.permissions().create(
            fileId=file_id,
            body=permiso_publico,
            fields='id',
        ).execute()
        
        # 3. Retornar el link de visualización directa de imagen para la app
        link_directo_imagen = f"https://lh3.googleusercontent.com/d/{file_id}"
        return link_directo_imagen

    except Exception as e:
        st.error(f"❌ Error al subir la imagen a Google Drive: {e}")
        return ""

# ---------------------------------------------------------
# OPCIÓN 1: REGISTRAR MANTENIMIENTO CON FOTO HD
# ---------------------------------------------------------
if menu == "📸 Registrar Mantenimiento / Foto HD":
    st.subheader("📝 Nuevo Registro con Foto HD Guardada en Drive")

    col1, col2 = st.columns(2)
    
    with col1:
        fecha = st.date_input("Fecha del Trabajo", value=datetime.now().date(), key="mant_fecha")
        unidad_sel = st.selectbox("Unidad / Camión / Máquina", unidades_list, key="mant_unidad_sel")
        unidad = st.text_input("Especifique Unidad", key="mant_unidad_otra") if unidad_sel == "Otra Unidad" else unidad_sel
        
        tipo_trabajo = st.selectbox("Tipo de Mantenimiento", [
            "🛢️️ Cambio de Aceite y Filtros",
            "🔩 Cambio de Repuesto / Pieza Rota",
            "🛞 Servicio de Neumáticos / Alineación",
            "⚡ Reparación Eléctrica",
            "🔨 Mantenimiento General / Taller",
            "🧾 Comprobante / Factura de Compra"
        ], key="mant_tipo")
        
        km_horas = st.number_input("Kilometraje / Horas", min_value=0, value=100000, step=500, key="mant_km")
        
    with col2:
        mecanico = st.selectbox("Mecánico / Responsable", ["Rocho (Mecánico)", "Daniel (Mecánico)", "Taller Externo", "Otro"], key="mant_mecanico")
        repuestos_usados = st.text_input("Repuestos Utilizados", key="mant_repuestos")
        costo = st.number_input("Costo ($)", min_value=0.0, value=0.0, step=100.0, key="mant_costo")
        obs = st.text_area("Observaciones", key="mant_obs")

    st.divider()
    st.markdown("### 📷 Captura / Carga de Foto HD")
    
    opcion_foto = st.radio("Cargar foto desde:", ["📷 Cámara del Celular", "📁 Archivos / Galería"], horizontal=True, key="mant_metodo")
    
    foto_capturada = None
    if "Cámara" in opcion_foto:
        foto_capturada = st.camera_input("Toma la foto:", key="mant_foto_cam")
    else:
        foto_capturada = st.file_uploader("Selecciona imagen en Alta Calidad:", type=["jpg", "png", "jpeg"], key="mant_foto_file")

    st.markdown("---")
    btn_guardar = st.button("💾 GUARDAR MANTENIMIENTO Y FOTO EN DRIVE", use_container_width=True, type="primary")
    
    if btn_guardar:
        if not unidad or unidad.strip() == "":
            st.error("⚠️ Debe especificar la unidad o camión.")
        elif FOLDER_ID_DRIVE == "COLOCA_AQUI_EL_ID_DE_TU_CARPETA_DE_DRIVE":
            st.error("⚠️ Recuerda reemplazar 'FOLDER_ID_DRIVE' en el código con el ID real de tu carpeta de Google Drive.")
        else:
            with st.spinner("Subiendo foto en alta resolución a tu Google Drive..."):
                url_foto_drive = ""
                if foto_capturada:
                    nombre_archivo = f"{unidad.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                    url_foto_drive = subir_foto_a_google_drive(foto_capturada, nombre_archivo)
                
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
                    "Foto Evidencia": url_foto_drive, # Se guarda el enlace directo a Google Drive
                    "Costo Aprox": costo,
                    "Observaciones": obs
                }])
                
                df_actualizado = pd.concat([df_existente, nueva_fila], ignore_index=True)
                conn.update(worksheet="Mantenimientos_Fotos", data=df_actualizado)
                
                st.success(f"✅ ¡Registro guardado con éxito! La foto se almacenó en tu carpeta de Google Drive.")

# ---------------------------------------------------------
# OPCIÓN 2: HISTORIAL Y VISUALIZADOR DE FOTOS
# ---------------------------------------------------------
else:
    st.subheader("📊 Historial de Mantenimientos y Fotos (Drive)")
    
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
                        url_foto = row.get("Foto Evidencia", "")
                        if pd.notna(url_foto) and str(url_foto).startswith("http"):
                            st.image(url_foto, caption=f"Evidencia HD Drive ({row['Unidad']})", use_container_width=True)
                        else:
                            st.info("Sin foto adjunta")

    except Exception as e:
        st.info("Asegúrate de tener creada la pestaña 'Mantenimientos_Fotos' en tu Google Sheets.")
