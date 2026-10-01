import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import urllib.parse
import cloudinary
import cloudinary.uploader

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# ---------------------------------------------------------
st.set_page_config(page_title="Pedidos Franco Luna ➔ Carlos Vega", layout="wide", page_icon="📦")

conn = st.connection("gsheets", type=GSheetsConnection)

# Configuración de Cloudinary
try:
    cloudinary.config(
        cloud_name=st.secrets["CLOUDINARY_CLOUD_NAME"],
        api_key=st.secrets["CLOUDINARY_API_KEY"],
        api_secret=st.secrets["CLOUDINARY_API_SECRET"],
        secure=True
    )
except Exception:
    pass

# Teléfono directo de Carlos Vega
TEL_CARLOS_VEGA = "5493886509152"

unidades_list = [
    "General / Campamento Base",
    "Taller / Mantenimiento",
    "MB Actros - AG506KW",
    "MB Actros - AB020RG",
    "MB Actros - AB032RM",
    "Iveco - AG096CP",
    "Iveco - AC737ZZ",
    "Tolva Randon - AF720XG",
    "Tolva Randon - AC738FC",
    "Tolva Randon - LBZ158",
    "Batea Randon - AC738HC",
    "Sola y Brusa - AC116DF",
    "Pala Cargadora",
    "Excavadora",
    "Otro Destino"
]

st.title("📦 Envío de Pedidos: Franco Luna ➔ Carlos Vega")
st.markdown("Plataforma de emisión, envío por WhatsApp y confirmación de recepción de insumos.")

menu = st.sidebar.radio("Navegación:", [
    "📝 Enviar Nuevo Pedido a Carlos Vega", 
    "📊 Historial y Confirmaciones de Recepción"
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
# OPCIÓN 1: ENVIAR NUEVO PEDIDO A CARLOS VEGA
# ---------------------------------------------------------
if menu == "📝 Enviar Nuevo Pedido a Carlos Vega":
    st.subheader("📋 Detalle del Pedido de Insumos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        emisor = st.text_input("Emisor del Pedido:", value="Franco Luna", disabled=True)
        destinatario = st.text_input("Destinatario:", value="Carlos Vega (3886509152)", disabled=True)
        
        destino = st.selectbox("Equipo / Área de Destino:", unidades_list, key="camp_destino")
        destino_real = st.text_input("Especifique Destino:", key="camp_dest_otro") if destino == "Otro Destino" else destino

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
            placeholder="Escriba un elemento por línea:\n- 2 Filtros de aceite\n- 1 Juego de llaves combinadas\n- 20 Lts de Refrigerante",
            height=160,
            key="camp_elementos"
        )
        
        obs = st.text_input("Observaciones o aclaración corta:", placeholder="ej: Necesario para la subida del viernes", key="camp_obs")

    st.markdown("### 📷 Adjuntar foto de pieza, lista manuscrita o muestra (Opcional)")
    foto_file = st.file_uploader("Seleccionar imagen:", type=["jpg", "png", "jpeg"], key="camp_foto")

    st.divider()
    btn_guardar = st.button("💾 REGISTRAR PEDIDO Y ENVIAR A CARLOS VEGA", type="primary", use_container_width=True)

    if btn_guardar:
        if not elementos or elementos.strip() == "":
            st.warning("⚠️ Debe ingresar al menos un elemento en la lista.")
        else:
            with st.spinner("Guardando pedido en planilla y armando mensaje..."):
                url_foto = subir_foto(foto_file) if foto_file else ""
                
                try:
                    df_exist = conn.read(worksheet="Pedidos_Campamento", ttl=0)
                except Exception:
                    df_exist = pd.DataFrame()

                nueva_fila = pd.DataFrame([{
                    "Fecha Registro": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Emisor": "Franco Luna",
                    "Destinatario": "Carlos Vega",
                    "Unidad / Destino": destino_real,
                    "Categoría": categoria,
                    "Lista de Elementos Requeridos": elementos,
                    "Prioridad": prioridad,
                    "Estado Confirmación": "⏳ Pendiente de Confirmación",
                    "Foto Evidencia": url_foto if url_foto else "Sin foto",
                    "Observaciones": obs
                }])

                df_actualizado = pd.concat([df_exist, nueva_fila], ignore_index=True)
                conn.update(worksheet="Pedidos_Campamento", data=df_actualizado)

                st.success("✅ Pedido registrado con éxito en la base de datos.")

                # Mensaje con solicitud explicita de confirmación para Carlos Vega
                texto_wa = (
                    f"📦 *NUEVO PEDIDO DE INSUMOS*\n"
                    f"👤 *De:* Franco Luna\n"
                    f"👤 *Para:* Carlos Vega\n\n"
                    f"📍 *Destino/Equipo:* {destino_real}\n"
                    f"🏷️ *Categoría:* {categoria}\n"
                    f"⚠️ *Prioridad:* {prioridad}\n\n"
                    f"📋 *LISTA DE ELEMENTOS:*\n{elementos}\n\n"
                    f"📝 *Obs:* {obs if obs else 'Sin observaciones'}\n"
                )
                if url_foto:
                    texto_wa += f"📷 *Foto Muestra:* {url_foto}\n\n"
                
                texto_wa += "📲 *Por favor responde este mensaje confirmando la recepción.*"

                texto_encoded = urllib.parse.quote(texto_wa)
                wa_url = f"https://api.whatsapp.com/send?phone={TEL_CARLOS_VEGA}&text={texto_encoded}"

                st.markdown("---")
                st.subheader("📲 Enviar a Carlos Vega por WhatsApp")
                st.link_button("📲 ENVIAR PEDIDO A CARLOS VEGA (3886509152)", wa_url, use_container_width=True, type="primary")

# ---------------------------------------------------------
# OPCIÓN 2: HISTORIAL Y ESTADO DE CONFIRMACIONES
# ---------------------------------------------------------
else:
    st.subheader("📊 Control de Pedidos y Confirmaciones (Franco Luna ➔ Carlos Vega)")

    if st.button("🔄 Actualizar Registro"):
        st.cache_data.clear()
        st.rerun()

    try:
        df_pedidos = conn.read(worksheet="Pedidos_Campamento", ttl=0)

        if df_pedidos.empty:
            st.info("No hay pedidos registrados aún.")
        else:
            # Filtro por estado de confirmación
            estados_posibles = [
                "Todos", 
                "⏳ Pendiente de Confirmación", 
                "👍 Confirmado por Carlos Vega", 
                "📦 En Preparación / Armado", 
                "✅ Entregado / Recibido"
            ]
            
            estado_filtro = st.selectbox("Filtrar por Estado de Confirmación:", estados_posibles)
            
            col_est = "Estado Confirmación" if "Estado Confirmación" in df_pedidos.columns else "Estado"
            df_mostrar = df_pedidos if estado_filtro == "Todos" else df_pedidos[df_pedidos[col_est] == estado_filtro]

            st.markdown("---")
            for idx, row in df_mostrar.iloc[::-1].iterrows():
                emisor_val = row.get("Emisor", "Franco Luna")
                dest_val = row.get("Destinatario", "Carlos Vega")
                estado_actual = str(row.get(col_est, "⏳ Pendiente de Confirmación"))

                with st.expander(f"📦 {row['Fecha Registro']} | {emisor_val} ➔ {dest_val} | Destino: {row['Unidad / Destino']} [{estado_actual}]"):
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.markdown(f"**Categoría:** {row['Categoría']} | **Prioridad:** {row['Prioridad']}")
                        st.markdown(f"**Elementos Requeridos:**\n{row['Lista de Elementos Requeridos']}")
                        st.markdown(f"**Observaciones:** {row['Observaciones']}")
                        
                        st.markdown("---")
                        st.markdown("##### ⚙️ Actualizar Confirmación de Recepción/Entrega")
                        
                        lista_confirmaciones = [
                            "⏳ Pendiente de Confirmación", 
                            "👍 Confirmado por Carlos Vega", 
                            "📦 En Preparación / Armado", 
                            "✅ Entregado / Recibido"
                        ]
                        
                        idx_def = lista_confirmaciones.index(estado_actual) if estado_actual in lista_confirmaciones else 0
                        
                        nuevo_estado = st.selectbox(
                            "Estado de confirmación:", 
                            lista_confirmaciones, 
                            index=idx_def, 
                            key=f"sel_conf_{idx}"
                        )
                        
                        if st.button("💾 Actualizar Estado de Confirmación", key=f"btn_conf_{idx}"):
                            df_pedidos.at[idx, col_est] = nuevo_estado
                            conn.update(worksheet="Pedidos_Campamento", data=df_pedidos)
                            st.success(f"✅ Estado actualizado a: {nuevo_estado}")
                            st.cache_data.clear()
                            st.rerun()

                    with c2:
                        foto_url = str(row.get("Foto Evidencia", "")).strip()
                        if foto_url.startswith("http"):
                            st.image(foto_url, caption="Foto muestra/lista", use_container_width=True)
                            st.link_button("🔎 Ampliar Foto", foto_url, use_container_width=True)
                        else:
                            st.info("Sin foto adjunta")

    except Exception as e:
        st.info("Asegúrate de haber creado la pestaña 'Pedidos_Campamento' en tu planilla de Google Sheets.")
