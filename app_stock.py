import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import cloudinary
import cloudinary.uploader

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# ---------------------------------------------------------
st.set_page_config(page_title="Control de Stock con Fotos - Taller", layout="wide", page_icon="📦")

conn = st.connection("gsheets", type=GSheetsConnection)

# Configuración de Cloudinary para fotos de repuestos y herramientas
try:
    cloudinary.config(
        cloud_name=st.secrets["CLOUDINARY_CLOUD_NAME"],
        api_key=st.secrets["CLOUDINARY_API_KEY"],
        api_secret=st.secrets["CLOUDINARY_API_SECRET"],
        secure=True
    )
except Exception:
    pass

st.title("📦 Control de Stock y Herramientas con Fotos")
st.markdown("Sistema de inventario para el taller y campamento minero.")

menu = st.sidebar.radio("Navegación:", [
    "➕ Registrar / Ingresar Objeto", 
    "📊 Consultar Inventario y Stock"
])

def subir_foto(file_buffer):
    if file_buffer:
        try:
            res = cloudinary.uploader.upload(file_buffer, folder="stock_taller", quality="auto:good")
            return res.get("secure_url", "")
        except Exception:
            return ""
    return ""

# ---------------------------------------------------------
# OPCIÓN 1: REGISTRAR NUEVO OBJETO
# ---------------------------------------------------------
if menu == "➕ Registrar / Ingresar Objeto":
    st.subheader("📋 Cargar Nuevo Elemento al Inventario")
    
    col1, col2 = st.columns(2)
    
    with col1:
        nombre_objeto = st.text_input("Nombre del Objeto o Repuesto:", placeholder="ej: Juego de llaves combinadas / Filtro de aceite")
        
        categoria = st.selectbox("Categoría:", [
            "🛠️ Herramientas de Mano",
            "⚙️ Repuestos de Maquinaria / Vehículos",
            "🛢️ Lubricantes e Insumos",
            "🥾 EPP y Seguridad",
            "⚡ Material Eléctrico / Electrónica",
            "📦 Varios / General"
        ])
        
        cantidad = st.number_input("Cantidad:", min_value=1, value=1, step=1)
        ubicacion = st.text_input("Ubicación / Estante / Contenedor:", placeholder="ej: Estante 3 - Taller Base")

    with col2:
        codigo = st.text_input("Código o Nro. Interno (Opcional):", placeholder="ej: INT-166 o SKU")
        responsable = st.text_input("Responsable del ingreso:", value="Franco Luna")
        obs = st.text_area("Observaciones o estado:", placeholder="ej: Nuevo sin usar / Usado en buen estado", height=100)

    st.markdown("### 📷 Adjuntar Foto del Objeto")
    foto_file = st.file_uploader("Seleccionar imagen:", type=["jpg", "png", "jpeg"], key="stock_foto")

    st.divider()
    btn_guardar = st.button("💾 GUARDAR EN EL INVENTARIO DE GOOGLE DRIVE", type="primary", use_container_width=True)

    if btn_guardar:
        if not nombre_objeto or nombre_objeto.strip() == "":
            st.warning("⚠️ Debe ingresar el nombre del objeto.")
        else:
            with st.spinner("Subiendo foto y guardando en Google Drive..."):
                url_foto = subir_foto(foto_file) if foto_file else "Sin foto"
                
                try:
                    df_exist = conn.read(worksheet="Inventario_Stock", ttl=0)
                except Exception:
                    df_exist = pd.DataFrame()

                nueva_fila = pd.DataFrame([{
                    "Fecha Registro": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Nombre / Objeto": nombre_objeto,
                    "Categoría": categoria,
                    "Cantidad": cantidad,
                    "Ubicación / Estante": ubicacion,
                    "Código / Interno": codigo if codigo else "S/C",
                    "Foto Evidencia": url_foto,
                    "Observaciones": obs,
                    "Responsable": responsable
                }])

                df_actualizado = pd.concat([df_exist, nueva_fila], ignore_index=True)
                conn.update(worksheet="Inventario_Stock", data=df_actualizado)

                st.success("✅ ¡Objeto registrado con éxito en el stock!")

# ---------------------------------------------------------
# OPCIÓN 2: CONSULTAR INVENTARIO
# ---------------------------------------------------------
else:
    st.subheader("📊 Inventario Actual de Objetos y Repuestos")

    if st.button("🔄 Actualizar Tabla"):
        st.cache_data.clear()
        st.rerun()

    try:
        df_stock = conn.read(worksheet="Inventario_Stock", ttl=0)

        if df_stock.empty:
            st.info("No hay objetos registrados en el inventario todavía.")
        else:
            # Filtro por categoría
            categorias_disponibles = ["Todas"] + list(df_stock["Categoría"].unique())
            cat_filtro = st.selectbox("Filtrar por Categoría:", categorias_disponibles)
            
            df_mostrar = df_stock if cat_filtro == "Todas" else df_stock[df_stock["Categoría"] == cat_filtro]

            st.markdown(f"Mostrando **{len(df_mostrar)}** elementos en stock:")
            
            st.markdown("---")
            for idx, row in df_mostrar.iloc[::-1].iterrows():
                with st.expander(f"📦 {row['Nombre / Objeto']} (Cant: {row['Cantidad']}) - Ubicación: {row['Ubicación / Estante']}"):
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.markdown(f"**Categoría:** {row['Categoría']}")
                        st.markdown(f"**Código / Interno:** `{row['Código / Interno']}`")
                        st.markdown(f"**Cantidad disponible:** `{row['Cantidad']}`")
                        st.markdown(f"**Ubicación:** {row['Ubicación / Estante']}")
                        st.markdown(f"**Observaciones:** {row['Observaciones']}")
                        st.markdown(f"**Registrado por:** {row['Responsable']} ({row['Fecha Registro']})")
                    with c2:
                        foto_url = str(row.get("Foto Evidencia", "")).strip()
                        if foto_url.startswith("http"):
                            st.image(foto_url, caption=row['Nombre / Objeto'], use_container_width=True)
                            st.link_button("🔎 Ampliar Foto", foto_url, use_container_width=True)
                        else:
                            st.info("Sin foto adjunta")

    except Exception as e:
        st.info("Asegúrate de haber creado la pestaña 'Inventario_Stock' en tu Google Sheet.")
