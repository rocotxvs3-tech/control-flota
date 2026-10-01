import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import io

# Configuración de página
st.set_page_config(page_title="Control de Repuestos y Stock", layout="wide", page_icon="📦")

# Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Categorías de Repuestos
categorias_repuestos = [
    "Filtros (Aceite, Aire, Combustible)",
    "Frenos y Suspensión",
    "Motor y Correas",
    "Transmisión y Caja",
    "Sistema Eléctrico y Luces",
    "Accesorios de Acoplados / Bateas",
    "Aceites, Fluidos y Engrase",
    "Ferretería y Taller General"
]

# Flota para asociar repuestos o egresos
unidades_flota = [
    "General / Taller Base",
    "AG506KW - MB Actros",
    "AB020RG - MB 1735",
    "AB032RM - MB 1735",
    "AG096CP - Iveco",
    "AC737ZZ - Iveco Tector",
    "AF720XG - RANDON SemiTolva 1",
    "AC738FC - RANDON SemiTolva 2",
    "LBZ158 - RANDON SemiTolva 3",
    "AC738HC - RANDON Batea",
    "AC116DF - Sola y Brusa Semi"
]

st.title("📦 Control de Repuestos, Códigos y Stock")
st.markdown("Gestión de inventario de taller, alerta de stock mínimo e historial de repuestos por vehículo.")

# Menú lateral
menu = st.sidebar.radio("Navegación:", [
    "📋 Inventario y Stock",
    "➕ Carga de Nuevo Repuesto",
    "🔄 Movimientos (Entrada / Salida)",
    "📊 Historial de Movimientos"
])

# ---------------------------------------------------------
# OPCIÓN 1: VER INVENTARIO Y ALERTAS DE STOCK
# ---------------------------------------------------------
if menu == "📋 Inventario y Stock":
    st.subheader("📦 Estado de Stock e Inventario")
    
    if st.button("🔄 Actualizar Datos"):
        st.cache_data.clear()
        st.rerun()

    try:
        df_stock = conn.read(worksheet="Inventario_Repuestos", ttl=0)
        
        if df_stock.empty:
            st.info("Aún no hay repuestos cargados en el inventario.")
        else:
            # Asegurar tipos de datos numéricos
            df_stock["Stock Actual"] = pd.to_numeric(df_stock["Stock Actual"], errors='coerce').fillna(0)
            df_stock["Stock Mínimo"] = pd.to_numeric(df_stock["Stock Mínimo"], errors='coerce').fillna(0)

            # Detectar repuestos con bajo stock
            bajo_stock = df_stock[df_stock["Stock Actual"] <= df_stock["Stock Mínimo"]]
            
            if not bajo_stock.empty:
                st.error(f"⚠️ **ALERTA DE REPOSICIÓN:** Hay {len(bajo_stock)} repuesto(s) con stock igual o inferior al mínimo permitido.")
                st.dataframe(bajo_stock[["Código", "Descripción", "Categoría", "Stock Actual", "Stock Mínimo", "Ubicación Base"]], use_container_width=True)
                st.divider()

            # Buscador y Filtros
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                busqueda = st.text_input("🔍 Buscar por Código o Nombre del Repuesto")
            with col_f2:
                cat_filtro = st.selectbox("Filtrar por Categoría", ["Todas"] + categorias_repuestos)

            df_filtrado = df_stock.copy()
            if busqueda:
                df_filtrado = df_filtrado[
                    df_filtrado["Código"].astype(str).str.contains(busqueda, case=False, na=False) |
                    df_filtrado["Descripción"].astype(str).str.contains(busqueda, case=False, na=False)
                ]
            if cat_filtro != "Todas":
                df_filtrado = df_filtrado[df_filtrado["Categoría"] == cat_filtro]

            st.markdown("### Listado Completo de Repuestos")
            st.dataframe(df_filtrado, use_container_width=True)

    except Exception:
        st.info("No se encontró la pestaña 'Inventario_Repuestos' o aún está vacía.")

# ---------------------------------------------------------
# OPCIÓN 2: CARGAR UN NUEVO REPUESTO AL CATÁLOGO
# ---------------------------------------------------------
elif menu == "➕ Carga de Nuevo Repuesto":
    st.subheader("🆕 Registrar Nuevo Repuesto en Ficha Técnica")
    
    with st.form("form_nuevo_repuesto", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            codigo = st.text_input("Código de Repuesto / Parte (ej: FIL-010, BRK-201)", placeholder="Código único").upper()
            descripcion = st.text_input("Descripción / Nombre del Repuesto", placeholder="ej: Filtro de Aceite MB Actros")
            categoria = st.selectbox("Categoría", categorias_repuestos)
            marca_proveedor = st.text_input("Marca / Marca del Repuesto", placeholder="ej: Mann Filter, Beral, Varga, etc.")

        with col2:
            aplicacion_unidad = st.selectbox("Aplica para Unidad / Modelo", unidades_flota)
            stock_inicial = st.number_input("Cantidad Inicial en Stock", min_value=0, value=1, step=1)
            stock_minimo = st.number_input("Stock Mínimo de Alerta", min_value=1, value=2, step=1)
            ubicacion = st.text_input("Ubicación en Taller / Estante", placeholder="ej: Estante A-2, Cajón 3")

        obs = st.text_input("Observaciones adicionales", placeholder="ej: Compatible también con Iveco Tector")
        
        btn_guardar_repuesto = st.form_submit_button("💾 REGISTRAR REPUESTO EN INVENTARIO", use_container_width=True)
        
        if btn_guardar_repuesto:
            if codigo.strip() == "" or descripcion.strip() == "":
                st.error("⚠️️ El código y la descripción son obligatorios.")
            else:
                try:
                    df_inv = conn.read(worksheet="Inventario_Repuestos", ttl=0)
                except Exception:
                    df_inv = pd.DataFrame()

                # Verificar código duplicado
                if not df_inv.empty and "Código" in df_inv.columns and codigo in df_inv["Código"].astype(str).values:
                    st.error(f"⚠️ El código '{codigo}' ya existe en el inventario. Utiliza otro o realiza un movimiento de entrada.")
                else:
                    nueva_fila = pd.DataFrame([{
                        "Código": codigo,
                        "Descripción": descripcion,
                        "Categoría": categoria,
                        "Marca": marca_proveedor,
                        "Unidad Compatible": aplicacion_unidad,
                        "Stock Actual": stock_inicial,
                        "Stock Mínimo": stock_minimo,
                        "Ubicación Base": ubicacion,
                        "Observaciones": obs
                    }])

                    df_actualizado = pd.concat([df_inv, nueva_fila], ignore_index=True)
                    conn.update(worksheet="Inventario_Repuestos", data=df_actualizado)
                    st.success(f"✅ Repuesto '{descripcion}' ({codigo}) guardado con éxito en el catálogo.")

# ---------------------------------------------------------
# OPCIÓN 3: REGISTRO DE MOVIMIENTOS (ENTRADA / SALIDA)
# ---------------------------------------------------------
elif menu == "🔄 Movimientos (Entrada / Salida)":
    st.subheader("🔄 Registrar Entrada o Egreso de Stock")

    try:
        df_inv = conn.read(worksheet="Inventario_Repuestos", ttl=0)
        
        if df_inv.empty or "Código" not in df_inv.columns:
            st.warning("⚠️ Primero debes registrar repuestos en la opción '➕ Carga de Nuevo Repuesto'.")
        else:
            # Crear lista desplegable de repuestos registrados
            opciones_repuestos = df_inv["Código"].astype(str) + " - " + df_inv["Descripción"].astype(str)
            
            with st.form("form_movimiento", clear_on_submit=True):
                col_m1, col_m2 = st.columns(2)
                
                with col_m1:
                    repuesto_sel = st.selectbox("Seleccionar Repuesto", opciones_repuestos)
                    tipo_movimiento = st.radio("Tipo de Operación:", ["🔴 SALIDA (Uso en Vehículo / Taller)", "🟢 ENTRADA (Compra / Reposición)"], horizontal=True)
                    cantidad = st.number_input("Cantidad", min_value=1, value=1, step=1)
                    
                with col_m2:
                    fecha_mov = st.date_input("Fecha", value=datetime.now().date())
                    destino_unidad = st.selectbox("Destino / Asignado a Vehículo", unidades_flota)
                    mecanico_responsable = st.text_input("Mecánico / Encargado del Taller")

                detalle_trabajo = st.text_input("Motivo / Orden de Trabajo", placeholder="ej: Cambio por mantenimiento preventivo, Rotura en viaje, etc.")
                btn_movimiento = st.form_submit_button("🚀 CONFIRMAR MOVIMIENTO DE STOCK", use_container_width=True)

                if btn_movimiento:
                    if mecanico_responsable.strip() == "":
                        st.error("⚠️ Debe ingresar el nombre del responsable/mecanico.")
                    else:
                        codigo_codigo = repuesto_sel.split(" - ")[0]
                        
                        # Actualizar cantidad en Inventario
                        idx = df_inv[df_inv["Código"].astype(str) == codigo_codigo].index
                        if len(idx) > 0:
                            stock_actual = float(df_inv.loc[idx[0], "Stock Actual"])
                            
                            if "SALIDA" in tipo_movimiento:
                                if stock_actual < cantidad:
                                    st.error(f"⚠️ Stock insuficiente. El stock actual de {codigo_codigo} es de {stock_actual} unidades.")
                                else:
                                    nuevo_stock = stock_actual - cantidad
                                    df_inv.loc[idx[0], "Stock Actual"] = nuevo_stock
                                    conn.update(worksheet="Inventario_Repuestos", data=df_inv)
                                    
                                    # Registrar en Movimientos
                                    try:
                                        df_movs = conn.read(worksheet="Movimientos_Repuestos", ttl=0)
                                    except Exception:
                                        df_movs = pd.DataFrame()

                                    nueva_salida = pd.DataFrame([{
                                        "Fecha": fecha_mov.strftime("%d/%m/%Y"),
                                        "Código": codigo_codigo,
                                        "Descripción": repuesto_sel.split(" - ")[1],
                                        "Tipo": "EGRESO / SALIDA",
                                        "Cantidad": cantidad,
                                        "Destino/Unidad": destino_unidad,
                                        "Responsable": mecanico_responsable,
                                        "Motivo": detalle_trabajo
                                    }])
                                    df_movs_act = pd.concat([df_movs, nueva_salida], ignore_index=True)
                                    conn.update(worksheet="Movimientos_Repuestos", data=df_movs_act)
                                    st.success(f"✅ Salida de {cantidad} unidad(es) registrada. Quedan {nuevo_stock} en stock.")
                            else:
                                nuevo_stock = stock_actual + cantidad
                                df_inv.loc[idx[0], "Stock Actual"] = nuevo_stock
                                conn.update(worksheet="Inventario_Repuestos", data=df_inv)

                                # Registrar en Movimientos
                                try:
                                    df_movs = conn.read(worksheet="Movimientos_Repuestos", ttl=0)
                                except Exception:
                                    df_movs = pd.DataFrame()

                                nueva_entrada = pd.DataFrame([{
                                    "Fecha": fecha_mov.strftime("%d/%m/%Y"),
                                    "Código": codigo_codigo,
                                    "Descripción": repuesto_sel.split(" - ")[1],
                                    "Tipo": "INGRESO / COMPRA",
                                    "Cantidad": cantidad,
                                    "Destino/Unidad": destino_unidad,
                                    "Responsable": mecanico_responsable,
                                    "Motivo": detalle_trabajo
                                }])
                                df_movs_act = pd.concat([df_movs, nueva_entrada], ignore_index=True)
                                conn.update(worksheet="Movimientos_Repuestos", data=df_movs_act)
                                st.success(f"✅ Ingreso de {cantidad} unidad(es) registrado. Nuevo stock: {nuevo_stock}.")
    except Exception as e:
        st.info("Asegúrate de tener repuestos cargados para poder realizar movimientos.")

# ---------------------------------------------------------
# OPCIÓN 4: HISTORIAL Y REPORTE EN EXCEL
# ---------------------------------------------------------
else:
    st.subheader("📊 Historial de Entradas y Salidas de Repuestos")

    if st.button("🔄 Actualizar Historial"):
        st.cache_data.clear()
        st.rerun()

    try:
        df_historial = conn.read(worksheet="Movimientos_Repuestos", ttl=0)
        st.dataframe(df_historial, use_container_width=True)

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_historial.to_excel(writer, index=False, sheet_name='Movimientos_Repuestos')

        st.download_button(
            label="📥 Descargar Reporte de Movimientos en Excel (.xlsx)",
            data=buffer.getvalue(),
            file_name=f"Reporte_Movimientos_Repuestos_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception:
        st.info("Aún no hay movimientos de repuestos registrados.")
