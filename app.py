"""Vivienda Esperanza · dashboard Streamlit/Supabase. Ejecutar: python -m streamlit run app.py"""
from __future__ import annotations
import hashlib
import hmac
from datetime import date, datetime
from io import BytesIO
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Vivienda Esperanza | Valorización RCD", page_icon="♻️", layout="wide", initial_sidebar_state="expanded")
ROOT = Path(__file__).resolve().parent
FAMILIAS = ["Madera", "Vidrio", "Plásticos", "Pinturas y químicos", "Áridos y escombros", "Metales", "Yeso-cartón", "Papel y cartón", "Mixtos", "Otros"]
DESTINOS = ["Pendiente", "Solo gasto", "Reutilización en obra", "Reciclaje externo", "Venta"]
ESTADOS = ["Sin medir", "Estimado", "Informado", "Medido en terreno", "Verificado documentalmente"]
UNIDADES = ["m²", "m³", "kg", "un", "m lineal", "L"]
ETAPAS = ["Demolición inicial", "Montaje de paneles", "Terminaciones", "Otros"]


def setting(section, key):
    try:
        return str(st.secrets[section][key]).strip()
    except (KeyError, FileNotFoundError, TypeError):
        return ""


def money(v):
    return "$" + f"{float(v or 0):,.0f}".replace(",", ".")


def number(v):
    try:
        return float(v) if pd.notna(v) else 0.0
    except (ValueError, TypeError):
        return 0.0


def verify_password(password, encoded):
    try:
        algorithm, rounds, salt, expected = encoded.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(rounds))
        return hmac.compare_digest(actual, bytes.fromhex(expected))
    except (ValueError, TypeError, OverflowError):
        return False


@st.cache_resource(show_spinner=False)
def client(url, secret):
    return create_client(url, secret)


def fetch(table):
    return pd.DataFrame(db.table(table).select("*").order("id", desc=True).limit(10000).execute().data or [])


def safe_fetch(table):
    try:
        return fetch(table), True
    except Exception:
        return pd.DataFrame(), False


def numeric_frame(df, columns):
    if not df.empty:
        for col in columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def excel_download(df, name, label):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Vivienda Esperanza")
    st.download_button(label, output.getvalue(), file_name=name, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


st.markdown("""<style>
/* Colores legibles: texto azul oscuro sobre superficies blancas. */
.stApp, [data-testid="stAppViewContainer"] {background:#f3f6fa;color:#15283c}
[data-testid="stSidebar"] {background:#102e47}
[data-testid="stSidebar"] p, [data-testid="stSidebar"] label,
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3, [data-testid="stSidebar"] span {color:#f4f8fc}
.block-container {max-width:1500px;padding-top:1.1rem;padding-bottom:2.5rem}
h1,h2,h3,h4,h5,h6, p, label, [data-testid="stMarkdownContainer"] {color:#15283c}
.hero {background:linear-gradient(105deg,#10334e,#0d6781);border-radius:19px;padding:24px 30px;color:#fff;margin-bottom:17px;box-shadow:0 8px 22px #15364a22}
.hero h1,.hero p {color:#fff !important}
.hero h1 {font-size:2.2rem;margin:0 0 6px}
.hero p {margin:0;color:#e3f3fa !important;overflow-wrap:anywhere}
[data-testid="stMetric"] {background:#fff;border:1px solid #dbe5ed;border-radius:15px;padding:15px 18px;box-shadow:0 4px 12px #21364b0a}
[data-testid="stMetricLabel"] *, [data-testid="stMetricLabel"] {color:#41566a !important}
[data-testid="stMetricValue"] *, [data-testid="stMetricValue"] {color:#123c59 !important}
[data-testid="stDataFrame"] {background:#fff;border-radius:12px}
[data-testid="stAlert"] {border-radius:10px}
/* Evitar que advertencias y campos hereden fondos amarillos del tema anterior. */
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input, [data-testid="stTextArea"] textarea,
[data-baseweb="select"] > div {background:#fff !important;color:#15283c !important}
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input, [data-testid="stTextArea"] textarea {color:#15283c !important}
[data-testid="stSidebar"] input {color:#15283c !important;background:#fff !important}
div.stButton>button[kind="primary"],div.stDownloadButton>button[kind="primary"] {background:#087b83;border-color:#087b83;color:#fff}
</style>""", unsafe_allow_html=True)

logo = ROOT / "OR_Logotipo_DuocUC.jpg"
if logo.is_file():
    st.markdown('<div style="background:white;padding:12px 20px;border-radius:14px;margin-bottom:12px;border:1px solid #e2e9f1">', unsafe_allow_html=True)
    st.image(str(logo), width=360)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div class="hero"><h1>♻️ Valorización de residuos</h1><p>Vivienda Esperanza · Duoc UC · Escuela de Construcción · Escuela de Administración y Negocios</p></div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="hero"><h1>♻️ Valorización de residuos</h1><p>Vivienda Esperanza · Duoc UC · Escuela de Construcción · Escuela de Administración y Negocios</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🏗️ Centro de control")
    st.caption("Proyecto Vivienda Esperanza · Chile")
    @st.fragment(run_every="60s")
    def clock():
        st.markdown("🕒 **" + datetime.now(ZoneInfo("America/Santiago")).strftime("%d-%m-%Y · %H:%M") + "**")
    clock()
    st.link_button("📁 Antecedentes del proyecto", "https://drive.google.com/drive/folders/1VJqQTbifp-w4MRRxEkLwQInxMbYieSzE")
    st.divider()
    if st.session_state.get("admin", False):
        st.success("🔓 Sesión de administrador")
        if st.button("Cerrar sesión"):
            st.session_state.admin = False
            st.rerun()
    else:
        st.markdown("#### Acceso para edición")
        with st.form("admin_login"):
            username = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            login = st.form_submit_button("Ingresar")
        if login:
            correct_user = hmac.compare_digest(username, setting("auth", "username"))
            correct_password = verify_password(password, setting("auth", "password_hash"))
            if correct_user and correct_password:
                st.session_state.admin = True
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")
    st.caption("Consulta pública · modificación exclusiva del administrador")

url = setting("supabase", "url")
secret = setting("supabase", "service_role_key")
if not url or not secret:
    st.error("Faltan los Secrets [supabase]: url y service_role_key. En PyCharm usa .streamlit/secrets.toml; en Streamlit Cloud, App settings → Secrets.")
    st.stop()
try:
    db = client(url, secret)
    reportes, ok_reportes = safe_fetch("reportes")
    residuos, ok_residuos = safe_fetch("residuos")
    paneles, ok_paneles = safe_fetch("paneles")
    if not (ok_reportes and ok_residuos and ok_paneles):
        raise RuntimeError("No se pudieron consultar las tablas originales reportes, residuos y paneles")
except Exception as exc:
    st.error("No fue posible conectarse a las tablas originales de Supabase.")
    st.code(str(exc))
    st.stop()

movimientos, ok_movimientos = safe_fetch("movimientos_valorizacion")
inventario, ok_inventario = safe_fetch("inventario_reuso")
if not ok_movimientos:
    st.warning("Falta ejecutar migracion_supabase.sql para habilitar movimientos_valorizacion.")
if not ok_inventario:
    st.warning("Falta ejecutar migracion_planilla_reuso.sql para habilitar inventario_reuso.")

# La vista de escenarios no tiene columna id: se consulta directamente.
try:
    escenario_rows = db.table("vw_escenario_paneles").select("*").eq("codigo", "VE-OSB-BASE-2026").limit(1).execute().data or []
    escenario = escenario_rows[0] if escenario_rows else None
    error_escenario = None
except Exception as exc:
    escenario = None
    error_escenario = str(exc)

inventario = numeric_frame(inventario, ["cantidad", "cantidad_reutilizada", "precio_reuso_clp"])
movimientos = numeric_frame(movimientos, ["kg_generados", "kg_recuperados", "costo_retiro_clp", "costo_recuperacion_clp", "compra_evitada_clp", "disposicion_evitada_clp", "ingreso_venta_clp", "costo_material_clp"])

potencial = 0.0
valor_reuso_referencial = 0.0
if not inventario.empty:
    inventario["valor_potencial_clp"] = inventario["cantidad"] * inventario["precio_reuso_clp"]
    inventario["valor_reuso_referencial_clp"] = inventario.apply(lambda r: number(r["cantidad_reutilizada"]) * number(r["precio_reuso_clp"]) if r["estado"] == "Verificado documentalmente" and str(r.get("evidencia") or "").strip() else 0.0, axis=1)
    potencial = float(inventario["valor_potencial_clp"].sum())
    valor_reuso_referencial = float(inventario["valor_reuso_referencial_clp"].sum())

beneficios = costos = recuperacion = 0.0
porcentaje = ratio = None
if not movimientos.empty:
    movimientos["beneficios_clp"] = movimientos[["compra_evitada_clp", "disposicion_evitada_clp", "ingreso_venta_clp"]].sum(axis=1)
    movimientos["costos_clp"] = movimientos[["costo_retiro_clp", "costo_recuperacion_clp"]].sum(axis=1)
    validos = movimientos[(movimientos["estado"] == "Verificado documentalmente") & (movimientos["evidencia"].fillna("").astype(str).str.strip() != "")]
    beneficios = float(validos["beneficios_clp"].sum())
    costos = float(movimientos["costos_clp"].sum())
    masa = float(validos["kg_generados"].sum())
    recuperacion = float(validos["kg_recuperados"].sum())
    porcentaje = recuperacion / masa * 100 if masa > 0 else None
    costo_validado = float(validos["costos_clp"].sum())
    ratio = beneficios / costo_validado if costo_validado > 0 else None

st.markdown("### 📊 Indicadores de gestión y valorización")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Valor recuperado acreditado", money(beneficios), help="Compras evitadas + disposición evitada + ventas documentadas en movimientos. No incluye precios potenciales de inventario.")
k2.metric("Recuperación física verificada", f"{porcentaje:.1f} %" if porcentaje is not None else "Sin base", help="Masa recuperada / masa generada en movimientos verificados con evidencia.")
k3.metric("Costos de gestión registrados", money(costos), help="Costos de retiro y recuperación ingresados en movimientos; no suma antecedentes históricos para evitar duplicar.")
k4.metric("Beneficio / costo", f"{ratio:.2f}" if ratio is not None else "Sin base", help="Beneficios verificados / costos asociados a los mismos movimientos.")
p1, p2, p3 = st.columns(3)
p1.metric("Valor potencial de reuso", money(potencial), help="Cantidad disponible por precio referencial. No es ingreso realizado.")
p2.metric("Reuso documentado a precio referencial", money(valor_reuso_referencial), help="Indicador informativo separado; no se suma a los beneficios de movimientos.")
p3.metric("Retiro histórico informado", money(135000), help="Antecedente de 5 m³ × $27.000/m³, pendiente de respaldo; no se suma automáticamente.")

# Indicadores adicionales de la línea base, independientes de las ventas realizadas.
st.markdown("#### 🏗️ Línea base de paneles y escenario de recuperación")
if escenario:
    base1, base2, base3, base4 = st.columns(4)
    base1.metric("Valor OSB nuevo comparable", money(escenario.get("valor_osb_nuevo_comparable_clp")), help="Precio de referencia de tableros nuevos comparables; NO es el costo real de adquisición ni el valor de los paneles armados.")
    base2.metric("Superficie OSB inicial", f"{number(escenario.get('area_osb_inicial_m2')):.2f} m²")
    base3.metric("Superficie neta teórica", f"{number(escenario.get('area_neta_teorica_m2')):.2f} m²")
    base4.metric("Ocupación geométrica teórica", f"{number(escenario.get('ocupacion_geometrica_pct')):.2f} %", help="Superficie nominal menos vanos / superficie nominal. NO representa recuperación de residuos.")
    st.caption("Referencia comercial, no ingreso: " + str(escenario.get("estado_comercial") or "Sin transacción") + ". Comprador potencial: " + str(escenario.get("comprador_potencial") or "Sin identificar"))
else:
    st.info("La línea base OSB todavía no está disponible. Verifica que la vista vw_escenario_paneles y el registro VE-OSB-BASE-2026 existan en Supabase.")
    if error_escenario and st.session_state.get("admin", False):
        with st.expander("Detalle técnico de consulta (administrador)"):
            st.code(error_escenario)

t_resumen, t_inventario, t_movimientos, t_osb, t_reportes = st.tabs(["📈 Resumen", "📋 Planilla tipo Excel", "💰 Costos y beneficios", "📐 Paneles OSB", "🗂️ Historial"])

with t_resumen:
    st.subheader("Balance general de la obra")
    st.caption("Los costos corresponden a movimientos registrados. Los valores de reuso son potenciales, no ventas realizadas.")
    b1, b2, b3 = st.columns(3)
    b1.metric("Gastos registrados", money(costos))
    b2.metric("Reuso potencial", money(potencial))
    b3.metric("Ventas acreditadas", money(float(validos["ingreso_venta_clp"].sum())) if not movimientos.empty else money(0))
    if not movimientos.empty:
        st.markdown("#### Detalle de gastos por movimiento")
        gastos_detalle = movimientos.loc[movimientos["costos_clp"] > 0].copy()
        if not gastos_detalle.empty:
            columnas_gasto = ["fecha", "etapa", "familia", "material", "costo_retiro_clp", "costo_recuperacion_clp", "costos_clp", "estado", "responsable"]
            st.dataframe(gastos_detalle[[c for c in columnas_gasto if c in gastos_detalle.columns]], use_container_width=True, hide_index=True)
            excel_download(gastos_detalle, "gastos_vivienda_esperanza.xlsx", "⬇️ Exportar gastos a Excel")
        else:
            st.info("No hay gastos registrados en movimientos.")
    if not inventario.empty:
        st.markdown("#### Materiales con potencial de valorización")
        materiales_detalle = inventario.loc[inventario["valor_potencial_clp"] > 0].copy()
        cols_mat = ["fecha_medicion", "familia", "material", "cantidad", "unidad", "precio_reuso_clp", "valor_potencial_clp", "destino", "estado", "fuente_precio"]
        st.dataframe(materiales_detalle[[c for c in cols_mat if c in materiales_detalle.columns]], use_container_width=True, hide_index=True)
    if escenario:
        with st.expander("📐 Detalle de la línea base OSB y posible comprador"):
            st.write("**Código:**", escenario.get("codigo", ""))
            st.write("**Paneles:**", escenario.get("paneles", ""))
            st.write("**Área de vanos nominal:**", f"{number(escenario.get('area_vanos_nominal_m2')):.2f} m²")
            st.write("**Corte geométrico:**", f"{number(escenario.get('corte_geometrico_pct')):.2f} %")
            st.write("**Comprador potencial (no confirmado):**", escenario.get("comprador_potencial") or "Pendiente")
            st.write("**Estado comercial:**", escenario.get("estado_comercial") or "Sin transacción")
            st.write("**Observaciones:**", escenario.get("observaciones") or "")
    st.divider()
    st.subheader("Distribución económica por familia")
    if movimientos.empty:
        st.info("Aún no hay movimientos de valorización. Los indicadores se completarán con datos medidos y documentados.")
    else:
        grouped = movimientos.groupby("familia", as_index=False)[["costos_clp", "beneficios_clp"]].sum()
        st.bar_chart(grouped.set_index("familia"))
        st.caption("Comparación en CLP. No se suman kg, m² y m³ como si fueran unidades equivalentes.")
    st.markdown("#### Antecedentes geométricos del proyecto")
    a, b, c = st.columns(3)
    a.metric("Paneles prefabricados", "54")
    b.metric("Superficie OSB nominal por cara", "160,75 m²")
    c.metric("Recorte nominal de 6 ventanas", "6,00 m²")
    st.info("Los recortes de ventanas informados fueron enviados a desecho. No se registran como recuperados. Los precios de reuso requieren cotización y evidencia.")
    if not inventario.empty:
        st.markdown("#### Inventario por familia")
        st.bar_chart(inventario.groupby("familia")["valor_potencial_clp"].sum())

with t_inventario:
    st.subheader("📋 Planilla de materiales valorizables")
    st.caption("Edición en cuadrícula similar a Excel. Una fila corresponde a un material en una fecha de medición. El precio es referencial y no implica beneficio realizado.")
    if not ok_inventario:
        st.error("Falta la tabla inventario_reuso. Ejecuta migracion_planilla_reuso.sql en Supabase.")
    else:
        f1, f2 = st.columns(2)
        familia_filtro = f1.selectbox("Filtrar por familia", ["Todas"] + FAMILIAS)
        estado_filtro = f2.selectbox("Filtrar por estado", ["Todos"] + ESTADOS)
        view = inventario.copy()
        if not view.empty:
            if familia_filtro != "Todas":
                view = view[view["familia"] == familia_filtro]
            if estado_filtro != "Todos":
                view = view[view["estado"] == estado_filtro]
            view = view.copy()
            view["valor_potencial_clp"] = view["cantidad"] * view["precio_reuso_clp"]
            display_cols = ["id", "fecha_medicion", "familia", "material", "descripcion", "cantidad", "unidad", "cantidad_reutilizada", "precio_reuso_clp", "valor_potencial_clp", "fuente_precio", "fecha_precio", "destino", "estado", "responsable", "evidencia"]
            st.dataframe(view[[c for c in display_cols if c in view.columns]], use_container_width=True, hide_index=True)
            excel_download(view, "inventario_reuso_vivienda_esperanza.xlsx", "⬇️ Descargar inventario Excel")
        else:
            st.info("El inventario está vacío. Ingresa como administrador para crear las primeras filas.")
        if not st.session_state.get("admin", False):
            st.info("🔒 Para ingresar o modificar materiales, inicia sesión en el panel lateral izquierdo.")
        else:
            st.markdown("#### Nueva carga: planilla tipo Excel")
            st.caption("Agrega tantas filas como necesites con el botón + de la cuadrícula. Las cantidades y precios deben corresponder a la misma unidad.")
            plantilla = pd.DataFrame([
                {"fecha_medicion": date.today(), "familia": "Madera", "material": "", "descripcion": "", "cantidad": 0.0, "unidad": "m²", "cantidad_reutilizada": 0.0, "precio_reuso_clp": 0.0, "fuente_precio": "", "fecha_precio": date.today(), "destino": "Pendiente", "estado": "Sin medir", "responsable": "", "evidencia": ""}
            ])
            grid = st.data_editor(
                plantilla, num_rows="dynamic", use_container_width=True, hide_index=True,
                key="planilla_carga",
                column_config={
                    "fecha_medicion": st.column_config.DateColumn("Fecha medición", format="DD/MM/YYYY", required=True),
                    "familia": st.column_config.SelectboxColumn("Familia", options=FAMILIAS, required=True),
                    "material": st.column_config.TextColumn("Material", required=True),
                    "descripcion": st.column_config.TextColumn("Descripción / medidas"),
                    "cantidad": st.column_config.NumberColumn("Cantidad disponible", min_value=0.0, format="%.3f"),
                    "unidad": st.column_config.SelectboxColumn("Unidad", options=UNIDADES, required=True),
                    "cantidad_reutilizada": st.column_config.NumberColumn("Reutilizada", min_value=0.0, format="%.3f"),
                    "precio_reuso_clp": st.column_config.NumberColumn("Precio reuso CLP/unidad", min_value=0.0, format="%.0f"),
                    "fuente_precio": st.column_config.TextColumn("Fuente precio"),
                    "fecha_precio": st.column_config.DateColumn("Fecha cotización", format="DD/MM/YYYY"),
                    "destino": st.column_config.SelectboxColumn("Destino", options=DESTINOS, required=True),
                    "estado": st.column_config.SelectboxColumn("Estado", options=ESTADOS, required=True),
                    "responsable": st.column_config.TextColumn("Responsable"),
                    "evidencia": st.column_config.TextColumn("Evidencia / respaldo"),
                },
            )
            st.metric("Valor potencial de esta carga", money(sum(number(r.get("cantidad")) * number(r.get("precio_reuso_clp")) for r in grid.to_dict("records"))))
            if st.button("💾 Guardar filas en Supabase", type="primary"):
                payloads = []
                problems = []
                for i, r in enumerate(grid.to_dict("records"), 1):
                    material = str(r.get("material") or "").strip()
                    if not material:
                        if any(number(r.get(k)) > 0 for k in ("cantidad", "cantidad_reutilizada", "precio_reuso_clp")):
                            problems.append(f"Fila {i}: falta nombre del material.")
                        continue
                    qty, reused, price = (number(r.get(k)) for k in ("cantidad", "cantidad_reutilizada", "precio_reuso_clp"))
                    if min(qty, reused, price) < 0 or reused > qty:
                        problems.append(f"Fila {i}: cantidades o precios inválidos.")
                    if r.get("estado") == "Verificado documentalmente" and not str(r.get("evidencia") or "").strip():
                        problems.append(f"Fila {i}: la verificación requiere evidencia.")
                    if r.get("destino") in ("Pendiente", "Solo gasto") and reused > 0:
                        problems.append(f"Fila {i}: no puede existir cantidad reutilizada con destino {r.get('destino')}.")
                    def iso(v):
                        return v.isoformat() if isinstance(v, (date, datetime)) else str(v)[:10] if pd.notna(v) else None
                    payloads.append({
                        "fecha_medicion": iso(r.get("fecha_medicion")) or date.today().isoformat(),
                        "familia": r.get("familia") or "Otros", "material": material,
                        "descripcion": str(r.get("descripcion") or ""),
                        "cantidad": qty, "unidad": r.get("unidad") or "un",
                        "cantidad_reutilizada": reused, "precio_reuso_clp": price,
                        "fuente_precio": str(r.get("fuente_precio") or ""),
                        "fecha_precio": iso(r.get("fecha_precio")),
                        "destino": r.get("destino") or "Pendiente",
                        "estado": r.get("estado") or "Sin medir",
                        "responsable": str(r.get("responsable") or ""),
                        "evidencia": str(r.get("evidencia") or ""),
                    })
                if problems:
                    for problem in problems:
                        st.error(problem)
                elif not payloads:
                    st.warning("Escribe al menos un material para guardar.")
                else:
                    try:
                        db.table("inventario_reuso").insert(payloads).execute()
                        st.success(f"Se guardaron {len(payloads)} materiales.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"No se pudieron guardar los materiales: {exc}")
            if not inventario.empty:
                st.markdown("#### Corregir registro guardado")
                selected = st.selectbox("Registro a modificar", inventario["id"].astype(int).tolist(), format_func=lambda x: f"#{x} · {inventario.loc[inventario['id']==x, 'material'].iloc[0]}")
                old = inventario.loc[inventario["id"] == selected].iloc[0]
                with st.form("editar_inventario"):
                    e1, e2, e3 = st.columns(3)
                    new_date = e1.date_input("Fecha de medición", value=date.fromisoformat(str(old["fecha_medicion"])[:10]))
                    new_family = e2.selectbox("Familia", FAMILIAS, index=FAMILIAS.index(old["familia"]) if old["familia"] in FAMILIAS else 0)
                    new_material = e3.text_input("Material", value=str(old["material"]))
                    e1, e2, e3 = st.columns(3)
                    new_qty = e1.number_input("Cantidad disponible", min_value=0.0, value=number(old["cantidad"]), step=0.1)
                    new_reused = e2.number_input("Cantidad reutilizada", min_value=0.0, value=number(old["cantidad_reutilizada"]), step=0.1)
                    new_price = e3.number_input("Precio reuso CLP/unidad", min_value=0.0, value=number(old["precio_reuso_clp"]), step=100.0)
                    e1, e2, e3 = st.columns(3)
                    new_source = e1.text_input("Fuente del precio", value=str(old.get("fuente_precio") or ""))
                    new_unit = e2.selectbox("Unidad", UNIDADES, index=UNIDADES.index(old["unidad"]) if old["unidad"] in UNIDADES else 0)
                    new_dest = e3.selectbox("Destino", DESTINOS, index=DESTINOS.index(old["destino"]) if old["destino"] in DESTINOS else 0)
                    new_state = st.selectbox("Estado", ESTADOS, index=ESTADOS.index(old["estado"]) if old["estado"] in ESTADOS else 0)
                    new_evidence = st.text_area("Evidencia", value=str(old.get("evidencia") or ""))
                    update = st.form_submit_button("Guardar cambios")
                if update:
                    if not new_material.strip() or new_reused > new_qty:
                        st.error("Revisa el material y las cantidades.")
                    elif new_state == "Verificado documentalmente" and not new_evidence.strip():
                        st.error("Para verificar documentalmente, registra evidencia.")
                    elif new_dest in ("Pendiente", "Solo gasto") and new_reused > 0:
                        st.error("No corresponde cantidad reutilizada con ese destino.")
                    else:
                        try:
                            db.table("inventario_reuso").update({"fecha_medicion": new_date.isoformat(), "familia": new_family, "material": new_material.strip(), "cantidad": new_qty, "unidad": new_unit, "cantidad_reutilizada": new_reused, "precio_reuso_clp": new_price, "fuente_precio": new_source, "destino": new_dest, "estado": new_state, "evidencia": new_evidence, "actualizado_en": datetime.now(ZoneInfo("America/Santiago")).isoformat()}).eq("id", int(selected)).execute()
                            st.success("Registro actualizado.")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Error al actualizar: {exc}")

with t_movimientos:
    st.subheader("Movimientos, costos y beneficios")
    if not ok_movimientos:
        st.warning("Ejecuta migracion_supabase.sql para crear movimientos_valorizacion.")
    else:
        if not movimientos.empty:
            st.dataframe(movimientos, hide_index=True, use_container_width=True)
            excel_download(movimientos, "movimientos_valorizacion.xlsx", "⬇️ Exportar movimientos")
        if st.session_state.get("admin", False):
            with st.form("nuevo_movimiento", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                fecha_m = c1.date_input("Fecha del movimiento", date.today())
                etapa = c2.selectbox("Etapa", ETAPAS)
                familia_m = c3.selectbox("Familia", FAMILIAS)
                material_m = st.text_input("Material / descripción")
                c1, c2, c3 = st.columns(3)
                tipo = c1.selectbox("Tratamiento", DESTINOS)
                qty = c2.number_input("Cantidad", min_value=0.0, step=0.1)
                unidad_m = c3.selectbox("Unidad", UNIDADES)
                c1, c2 = st.columns(2)
                masa_gen = c1.number_input("Masa generada (kg)", min_value=0.0, step=1.0)
                masa_rec = c2.number_input("Masa recuperada (kg)", min_value=0.0, step=1.0)
                c1, c2, c3 = st.columns(3)
                costo_material = c1.number_input("Costo original material CLP", min_value=0.0, step=1000.0)
                retiro = c2.number_input("Costo retiro CLP", min_value=0.0, step=1000.0)
                costo_rec = c3.number_input("Costo recuperación CLP", min_value=0.0, step=1000.0)
                c1, c2, c3 = st.columns(3)
                compra = c1.number_input("Compra evitada acreditada CLP", min_value=0.0, step=1000.0)
                disposicion = c2.number_input("Disposición evitada acreditada CLP", min_value=0.0, step=1000.0)
                venta = c3.number_input("Ingreso venta acreditado CLP", min_value=0.0, step=1000.0)
                c1, c2 = st.columns(2)
                estado_m = c1.selectbox("Estado", ESTADOS)
                destino_m = c2.text_input("Destino físico")
                responsable_m = st.text_input("Responsable del movimiento")
                evidencia_m = st.text_area("Evidencia")
                save_m = st.form_submit_button("💾 Guardar movimiento", type="primary")
            if save_m:
                if not material_m.strip():
                    st.error("Indica el material")
                elif masa_rec > masa_gen:
                    st.error("La masa recuperada no puede superar la generada")
                elif tipo in ("Solo gasto", "Pendiente") and any(x > 0 for x in (compra, disposicion, venta)):
                    st.error("Un movimiento 'Solo gasto' o 'Pendiente' no puede registrar beneficios")
                elif estado_m == "Verificado documentalmente" and not evidencia_m.strip():
                    st.error("Un registro verificado requiere evidencia")
                else:
                    payload = {"fecha": fecha_m.isoformat(), "etapa": etapa, "familia": familia_m, "material": material_m.strip(), "tipo": tipo, "cantidad": qty, "unidad": unidad_m, "kg_generados": masa_gen if masa_gen > 0 else None, "kg_recuperados": masa_rec if masa_gen > 0 else None, "costo_material_clp": costo_material, "costo_retiro_clp": retiro, "costo_recuperacion_clp": costo_rec, "compra_evitada_clp": compra, "disposicion_evitada_clp": disposicion, "ingreso_venta_clp": venta, "estado": estado_m, "destino": destino_m, "responsable": responsable_m, "evidencia": evidencia_m}
                    try:
                        db.table("movimientos_valorizacion").insert(payload).execute()
                        st.success("Movimiento guardado")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Error al guardar: {exc}")
        else:
            st.info("Para registrar gastos y beneficios debes iniciar sesión como administrador.")

with t_osb:
    st.subheader("Conversor de paneles prefabricados OSB")
    c1, c2, c3, c4 = st.columns(4)
    panels = c1.number_input("Paneles", min_value=0, value=54, step=1)
    width = c2.number_input("Ancho panel (m)", min_value=0.01, value=1.22, step=0.01)
    height = c3.number_input("Alto panel (m)", min_value=0.01, value=2.44, step=0.01)
    thickness = c4.number_input("Espesor OSB (mm)", min_value=0.1, value=12.5, step=0.5)
    c1, c2, c3, c4 = st.columns(4)
    openings = c1.number_input("Vanos", min_value=0, value=6, step=1)
    open_width = c2.number_input("Ancho vano (m)", min_value=0.0, value=1.0, step=0.05)
    open_height = c3.number_input("Alto vano (m)", min_value=0.0, value=1.0, step=0.05)
    faces = c4.selectbox("Caras OSB", [1, 2])
    area = panels * width * height * faces
    cut = openings * open_width * open_height * faces
    if cut > area:
        st.error("Los recortes exceden el área disponible. Revisa los datos.")
    a, b, c, d = st.columns(4)
    a.metric("Área OSB nominal", f"{area:,.2f} m²")
    b.metric("Recorte nominal", f"{cut:,.2f} m²")
    c.metric("Volumen OSB recortado", f"{cut*thickness/1000:,.4f} m³")
    d.metric("Fracción recortada", f"{cut/area*100:.2f} %" if area else "—")
    st.progress(min(cut/area, 1.0) if area else 0.0)
    rec = st.number_input("Superficie de recortes realmente reutilizada (m²)", min_value=0.0, max_value=max(cut, 0.01), value=0.0, step=0.1)
    st.metric("Reutilización de recortes", f"{rec/cut*100:.2f} %" if cut else "—")
    st.info("Cálculo geométrico ilustrativo. No equivale a masa medida ni a valorización efectiva. Los recortes de ventanas informados fueron retirados como desecho. El pino 2×3 debe cubicarse por separado.")

with t_reportes:
    st.subheader("Historial y trazabilidad")
    for label, data in [("Reportes originales", reportes), ("Residuos originales", residuos), ("Paneles originales", paneles)]:
        with st.expander(label):
            if data.empty:
                st.info("Sin registros")
            else:
                st.dataframe(data, hide_index=True, use_container_width=True)
                excel_download(data, label.lower().replace(" ", "_") + ".xlsx", "Exportar Excel")
    st.caption("El historial actual conserva registros, pero la edición de una fila no crea aún una auditoría individual de versiones.")

st.divider()
st.caption("Vivienda Esperanza · Tablero de trabajo. Las cifras referenciales y simulaciones no sustituyen mediciones ni respaldos documentales. Identidad institucional sujeta a autorización.")
