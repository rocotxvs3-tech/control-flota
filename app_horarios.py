import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import io

# Configuración de página
st.set_page_config(page_title="Control de Horarios y Personal", layout="wide", page_icon="⏱️")

# Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Listas oficiales del personal
albaniles_list = [
    "Nicolás (Albañil)",
    "Axel (Albañil)",
    "Gabriel (Albañil)",
    "Misky (Albañil)",
    "Otro Albañil"
]

mecanicos_list = [
    "Rocho (Mecánico)",
    "Daniel (Mecánico)",
    "Otro Mecánico"
]

st.title("⏱️ Sistema de Control de Personal y Horarios")
st.markdown("Gestión diferenciada para **Albañilería (Por hora L-V)** y **Mecánicos (Roster 20/10)**.")

menu = st.sidebar.radio("Navegación:", ["📲 Fichaje Diario", "📊 Reportes y Liquidación"])

# ---------------------------------------------------------
# OPCIÓN 1: FICHAJE DIARIO
# ---------------------------------------------------------
if menu == "📲 Fichaje Diario":
    st.subheader("📝 Fichaje e Ingreso de Horas")
    
    rubro = st.radio("Selecciona la categoría de trabajador:", ["🧱 Albañilería (Por Hora / L-V)", "🔧 Mecánicos (Roster 20x10)"], horizontal=True)
    
    st.divider()

    # ----------------------------------------
    # FORMULARIO PARA ALBAÑILES (PAGO POR HORA)
    # ----------------------------------------
    if "Albañilería" in rubro:
        st.markdown("### 🧱 Fichaje de Albañiles (Control de Horas)")
        
        with st.form("form_albanil", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                emp_sel = st.selectbox("Trabajador", albaniles_list)
                nombre_emp = st.text_input("Especifique Nombre") if emp_sel == "Otro Albañil" else emp_sel
                fecha = st.date_input("Fecha de Trabajo", value=datetime.now().date())
                
            with col2:
                hora_ingreso = st.time_input("Hora de Entrada", value=datetime.strptime("08:00", "%H:%M").time())
                hora_egreso = st.time_input("Hora de Salida", value=datetime.strptime("17:00", "%H:%M").time())
                descuento_almuerzo = st.number_input("Descuento Almuerzo/Descanso (Horas)", min_value=0.0, max_value=3.0, value=1.0, step=0.5)

            # Cálculo de horas netas
            t_ingreso = datetime.combine(fecha, hora_ingreso)
            t_egreso = datetime.combine(fecha, hora_egreso)
            if t_egreso > t_ingreso:
                horas_brutas = (t_egreso - t_ingreso).total_seconds() / 3600
                horas_netas = max(0.0, horas_brutas - descuento_almuerzo)
            else:
                horas_netas = 0.0

            st.info(f"⏱️ **Horas Netas a Liquidar:** `{horas_netas:.1f} hs` (Total jornada: {horas_brutas:.1f} hs - {descuento_almuerzo} hs descanso)")
            
            obs = st.text_input("Observaciones / Tareas realizadas", placeholder="ej: Encofrado, levantamiento de mampostería, etc.")
            btn_guardar_alb = st.form_submit_button("💾 GUARDAR JORNADA Y HORAS", use_container_width=True)
            
            if btn_guardar_alb:
                if nombre_emp.strip() == "":
                    st.error("⚠️ Debe seleccionar o ingresar el nombre del trabajador.")
                else:
                    try:
                        df_existente = conn.read(worksheet="Control_Horarios", ttl=0)
                    except Exception:
                        df_existente = pd.DataFrame()

                    nueva_fila = pd.DataFrame([{
                        "Fecha": fecha.strftime("%d/%m/%Y"),
                        "Empleado": nombre_emp,
                        "Rubro": "Albañil (Por Hora)",
                        "Tipo Registro": "Jornada Completa",
                        "Hora Entrada": hora_ingreso.strftime("%H:%M"),
                        "Hora Salida": hora_egreso.strftime("%H:%M"),
                        "Horas Trabajadas": round(horas_netas, 2),
                        "Estado Roster": "N/A (L-V)",
                        "Observaciones": obs
                    }])
                    
                    df_actualizado = pd.concat([df_existente, nueva_fila], ignore_index=True)
                    conn.update(worksheet="Control_Horarios", data=df_actualizado)
                    st.success(f"✅ ¡Jornada de {nombre_emp} ({horas_netas:.1f} hs) registrada con éxito!")

    # ----------------------------------------
    # FORMULARIO PARA MECÁNICOS (ROSTER 20/10)
    # ----------------------------------------
    else:
        st.markdown("### 🔧 Fichaje de Mecánicos (Turno 20/10)")
        
        with st.form("form_mecanico", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                emp_sel = st.selectbox("Mecánico", mecanicos_list)
                nombre_emp = st.text_input("Especifique Nombre") if emp_sel == "Otro Mecánico" else emp_sel
                fecha = st.date_input("Fecha", value=datetime.now().date())
                estado_roster = st.selectbox("Estado en Roster 20/10", [
                    "🟢 En Turno de Trabajo (Día 1 al 20)",
                    "🔴 En Franco / Descanso (Día 1 al 10)",
                    "🚌 En Viaje de Subida / Bajada"
                ])
                
            with col2:
                dia_consecutivo = st.number_input("Nº de Día del Ciclo (ej: Día 5 de 20)", min_value=1, max_value=20, value=1, step=1)
                tipo_fichaje = st.radio("Acción:", ["Entrada Turno Taller", "Salida Turno Taller", "Registro de Franco / Ausencia"])
                hora_marca = st.time_input("Hora del Fichaje", value=datetime.now().time())

            obs = st.text_input("Observaciones / Novedades de Taller", placeholder="ej: Mantenimiento preventivo camión, reparación de frenos, etc.")
            btn_guardar_mec = st.form_submit_button("💾 GUARDAR FICHAJE DE MECÁNICO", use_container_width=True)
            
            if btn_guardar_mec:
                if nombre_emp.strip() == "":
                    st.error("⚠️ Debe seleccionar o ingresar el nombre del mecánico.")
                else:
                    try:
                        df_existente = conn.read(worksheet="Control_Horarios", ttl=0)
                    except Exception:
                        df_existente = pd.DataFrame()

                    roster_str = f"{estado_roster} - Día {dia_consecutivo}"

                    nueva_fila = pd.DataFrame([{
                        "Fecha": fecha.strftime("%d/%m/%Y"),
                        "Empleado": nombre_emp,
                        "Rubro": "Mecánico (Roster 20x10)",
                        "Tipo Registro": tipo_fichaje,
                        "Hora Entrada": hora_marca.strftime("%H:%M") if "Entrada" in tipo_fichaje else "",
                        "Hora Salida": hora_marca.strftime("%H:%M") if "Salida" in tipo_fichaje else "",
                        "Horas Trabajadas": 0.0,
                        "Estado Roster": roster_str,
                        "Observaciones": obs
                    }])
                    
                    df_actualizado = pd.concat([df_existente, nueva_fila], ignore_index=True)
                    conn.update(worksheet="Control_Horarios", data=df_actualizado)
                    st.success(f"✅ ¡Fichaje de {nombre_emp} ({roster_str}) guardado con éxito!")

# ---------------------------------------------------------
# OPCIÓN 2: REPORTES Y LIQUIDACIÓN EN EXCEL
# ---------------------------------------------------------
else:
    st.subheader("📊 Reporte de Horarios y Horas Acumuladas")
    
    if st.button("🔄 Actualizar Registros"):
        st.cache_data.clear()
        st.rerun()

    try:
        df_horarios = conn.read(worksheet="Control_Horarios", ttl=0)
        
        # Filtro rápido por rubro
        filtro_rubro = st.selectbox("Filtrar por categoría:", ["Todos", "Albañil (Por Hora)", "Mecánico (Roster 20x10)"])
        if filtro_rubro != "Todos":
            df_mostrar = df_horarios[df_horarios["Rubro"] == filtro_rubro]
        else:
            df_mostrar = df_horarios

        st.dataframe(df_mostrar, use_container_width=True)

        # Resumen de horas para albañilería (para liquidar sueldos fácilmente)
        if not df_horarios.empty and "Horas Trabajadas" in df_horarios.columns:
            st.markdown("### 💰 Total de Horas Trabajadas (Albañilería)")
            df_alb = df_horarios[df_horarios["Rubro"] == "Albañil (Por Hora)"]
            if not df_alb.empty:
                df_alb["Horas Trabajadas"] = pd.to_numeric(df_alb["Horas Trabajadas"], errors='coerce').fillna(0)
                resumen_horas = df_alb.groupby("Empleado")["Horas Trabajadas"].sum().reset_index()
                st.table(resumen_horas)

        # Descarga a Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_horarios.to_excel(writer, index=False, sheet_name='Control_Horarios')
        
        st.download_button(
            label="📥 Descargar Reporte Completo de Personal en Excel (.xlsx)",
            data=buffer.getvalue(),
            file_name=f"Reporte_Personal_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception:
        st.info("Aún no hay registros en la pestaña 'Control_Horarios'.")
