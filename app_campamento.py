import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import urllib.parse
import cloudinary
import cloudinary.uploader

# ---------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------
st.set_page_config(page_title="Insumos y Requerimientos de Campamento", layout="wide", page_icon="📦")

conn = st.connection("gsheets", type=GSheetsConnection)

# Configuración de Cloudinary para fotos de remitos, repuestos o listas
try:
    cloudinary.config(
        cloud_name=st.secrets["CLOUDINARY_CLOUD_NAME"],
        api_key=st.secrets["CLOUDINARY_API_KEY"],
        api_secret=st.secrets["CLOUDINARY_API_SECRET"],
        secure=True
    )
except Exception:
    pass

# Unidades / Áreas de la mina
unidades_list = [
    "General / Campamento Base",
    "Taller / Mantenimiento",
    "Otro Destino"
]

st.title("📦 Requerimientos de Materiales e Insumos - Campamento Mina")
st.markdown("Lista directa de elementos solicitados para enviar al encargado.")

menu = st.sidebar.radio("Navegación:", [
    "📝 Crear Lista de Elementos", 
    "📊 Historial y Estado de Pedidos"
])

def subir_foto(file_buffer):
    if file_buffer:
        try:
            res = cloudinary.uploader.upload(file_buffer, folder="pedidos_campamento", quality="auto:good")
            return res.get("secure_url", "")
        except Exception:
            return ""
    return ""

# ---------------------------------------------------------
# OPCIÓN 1: CREAR LISTA DE ELEMENTOS
# ---------------------------------------------------------
if menu == "📝 Crear Lista de Elementos":
    st.subheader("📋 Cargar Lista de Elementos Necesarios")
    
    col1, col2 = st.columns(2)
    
    with col1:
        destino = st.selectbox("Equipo / Área de Destino:", unidades_list, key="camp_destino")
        if destino == "Otro Destino":
            destino_real = st.text_input("Especifique Destino:", key="camp_dest_otro")
        else:
            destino_real = destino

        categoria = st.selectbox("Categoría de Insumos:", [
            "🛠️ Herramientas y Repuestos",
            "🛢️ Aceites, Insumos y Lubricantes",
            "🥾 EPP y Seguridad",
            "📦 Víveres y General Campamento",
            "🧾 Varios / Comprobantes"
        ], key="camp_cat")

        prioridad = st.selectbox("Prioridad:", ["🟢 Normal", "🟡 Alta", "🔴 URGENTE"], key="camp_prio")

    with col2:
        elementos = st.text_area(
            "Lista detallada de elementos requeridos:",
            placeholder="Escriba un elemento por línea. Ej:\n- 2 Filtros de aceite\n- 1 Juego de llaves combinadas\n- 5 Cajas de electrodos\n- 20 Lts de Refrigerante",
            height=160,
            key="camp_elementos"
        )
        
        obs = st.text_input("Observaciones o aclaración corta:", placeholder="ej: Entregar antes del viernes", key="camp_obs")
        telefono_encargado = st.text_input("Teléfono WhatsApp Encargado (con código de país/área):", placeholder="ej: 5492641234567", key="camp_tel")

    st.markdown("### 📷 Adjuntar foto de pieza, muestra o lista manuscrita (Opcional)")
    foto_file = st.file_uploader("Seleccionar imagen:", type=["jpg", "png", "jpeg"], key="camp_foto")

    st.divider()
    btn_guardar = st.button("💾 GUARDAR LISTA Y ARMAR MENSAJE", type="primary", use_container_width=True)

    if btn_guardar:
        if not elementos or elementos.strip() == "":
            st.warning("⚠️ Debe ingresar al menos un elemento en la lista.")
        else:
            with st.spinner("Guardando registro de materiales..."):
                url_foto = subir_foto(foto_file) if foto_file else ""
                
                try:
                    df_exist = conn.read(worksheet="Pedidos_Campamento", ttl=0)
                except Exception:
                    df_exist = pd.DataFrame()

                nueva_fila = pd.DataFrame([{
                    "Fecha Registro": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Unidad / Destino": destino_real,
                    "Categoría": categoria,
                    "Lista de Elementos Requeridos": elementos,
                    "Prioridad": prioridad,
                    "Estado": "⏳ Pendiente",
                    "Foto Evidencia": url_foto if url_foto else "Sin foto",
                    "Observaciones": obs
                }])

                df_actualizado = pd.concat([df_exist, nueva_fila], ignore_index=True)
                conn.update(worksheet="Pedidos_Campamento", data=df_actualizado)

                st.success("✅ Lista de elementos registrada con éxito.")

                # Armar mensaje para enviar al encargado
                texto_wa = (
                    f"📦 *REQUERIMIENTO DE ELEMENTOS - CAMPAMENTO*\n\n"
                    f"📍 *Destino/Equipo:* {destino_real}\n"
                    f"🏷️ *Categoría:* {categoria}\n"
                    f"⚠️ *Prioridad:* {prioridad}\n\n"
                    f"📋 *LISTA DE ELEMENTOS:*\n{elementos}\n\n"
                    f"📝 *Obs:* {obs if obs else 'Sin observaciones'}\n"
                )
                if url_foto:
                    texto_wa += f"📷 *Foto muestra/lista:* {url_foto}"

                texto_encoded = urllib.parse.quote(texto_wa)
                num_tel = telefono_encargado.replace("+", "").replace(" ", "").strip()
                
                wa_url = f"https://wa.me/{num_tel}?text={texto_encoded}" if num_tel else f"https://wa.me/?text={texto_encoded}"

                st.markdown("---")
                st.subheader("📲 Enviar Lista por WhatsApp")
                st.link_button("📲 ENVIAR LISTA AL ENCARGADO POR WHATSAPP", wa_url, use_container_width=True, type="primary")

# ---------------------------------------------------------
# OPCIÓN 2: HISTORIAL Y ESTADO DE PEDIDOS
# ---------------------------------------------------------
else:
    st.subheader("📊 Historial de Materiales e Insumos Pedidos")

    if st.button("🔄 Actualizar Registro"):
        st.cache_data.clear()
        st.rerun()

    try:
        df_pedidos = conn.read(worksheet="Pedidos_Campamento", ttl=0)

        if df_pedidos.empty:
            st.info("No hay listas de elementos registradas aún.")
        else:
            estado_filtro = st.selectbox("Filtrar por Estado:", ["Todos", "⏳ Pendiente", "📦 En Preparación", "✅ Listo / Entregado"])
            
            df_mostrar = df_pedidos if estado_filtro == "Todos" else df_pedidos[df_pedidos["Estado"] == estado_filtro]

            st.markdown("---")
            for idx, row in df_mostrar.iloc[::-1].iterrows():
                with st.expander(f"📦 {row['Fecha Registro']} - {row['Unidad / Destino']} ({row['Prioridad']})"):
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.markdown(f"**Categoría:** {row['Categoría']}")
                        st.markdown(f"**Elementos Requeridos:**\n{row['Lista de Elementos Requeridos']}")
                        st.markdown(f"**Estado:** `{row['Estado']}`")
                        st.markdown(f"**Observaciones:** {row['Observaciones']}")
                    with c2:
                        foto_url = str(row.get("Foto Evidencia", "")).strip()
                        if foto_url.startswith("http"):
                            st.image(foto_url, caption="Foto muestra/lista", use_container_width=True)
                            st.link_button("🔎 Ampliar Foto", foto_url, use_container_width=True)
                        else:
                            st.info("Sin foto adjunta")

    except Exception as e:
        st.info("Asegúrate de haber creado la pestaña 'Pedidos_Campamento' en tu planilla de Google Sheets.")
