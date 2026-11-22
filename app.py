"""Vivienda Esperanza | Streamlit + Supabase. Ejecutar: python -m streamlit run app.py"""
import hashlib
import hmac
import json
import secrets
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client

st.set_page_config(page_title="Valorización RCD | Vivienda Esperanza", page_icon="♻️", layout="wide")
BASE = Path(__file__).resolve().parent


def setting(section, key, default=""):
    try:
        return str(st.secrets[section][key])
    except (KeyError, FileNotFoundError):
        return default


@st.cache_resource(show_spinner=False)
def db_client(url, key):
    return create_client(url, key)


def verify_password(candidate, encoded):
    """Formato: pbkdf2_sha256$iteraciones$salt_hex$hash_hex."""
    try:
        method, rounds, salt, expected = encoded.split("$")
        if method != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac("sha256", candidate.encode(), bytes.fromhex(salt), int(rounds))
        return hmac.compare_digest(actual, bytes.fromhex(expected))
    except (ValueError, TypeError):
        return False


def clp(value):
    return "$" + f"{float(value or 0):,.0f}".replace(",", ".")


def load(table, order="id"):
    # Consultas del servidor, nunca del navegador; no exponer credenciales.
    result = db.table(table).select("*").order(order, desc=True).limit(2000).execute()
    return pd.DataFrame(result.data or [])


st.markdown("""<style>
.block-container{max-width:1450px;padding-top:1.1rem}
.hero{background:linear-gradient(110deg,#102e43,#146f80);padding:22px 26px;border-radius:18px;color:white;margin-bottom:15px}
.hero h1{color:white;margin:0;font-size:2.05rem}.hero p{margin:6px 0 0;color:#e5f2f4}
[data-testid="stMetric"]{border:1px solid #58798450;border-radius:14px;padding:12px;background:#748e9511}
</style>""", unsafe_allow_html=True)
logo = BASE / "logo_duoc_uc.png"
if logo.exists():
    left, right = st.columns([1, 7], vertical_alignment="center")
    with left:
        st.image(str(logo), use_container_width=True)
    with right:
        st.markdown('<div class="hero"><h1>♻️ Valorización de residuos</h1><p>Vivienda Esperanza · Control físico, económico y trazabilidad RCD · Duoc UC</p></div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="hero"><h1>♻️ Valorización de residuos</h1><p>Vivienda Esperanza · Control físico, económico y trazabilidad RCD · Duoc UC</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.subheader("🕒 Centro de control")
    components.html('''<div style="font-family:Arial;background:#102e43;color:white;border-radius:12px;text-align:center;padding:12px"><div id="clock" style="font-size:27px;font-weight:bold"></div><div id="day" style="font-size:12px"></div></div><script>function tick(){const d=new Date();document.getElementById('clock').textContent=d.toLocaleTimeString('es-CL');document.getElementById('day').textContent=d.toLocaleDateString('es-CL',{dateStyle:'full'});}tick();setInterval(tick,1000)</script>''', height=90)
    st.caption("Hora local del navegador")
    st.link_button("📂 Antecedentes técnicos", "https://drive.google.com/drive/folders/1VJqQTbifp-w4MRRxEkLwQInxMbYieSzE")
    st.divider()
    if st.session_state.get("admin", False):
        st.success("Sesión: administrador")
        if st.button("Cerrar sesión"):
            st.session_state.admin = False
            st.rerun()
    else:
        with st.form("login"):
            username = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            login = st.form_submit_button("Ingresar como administrador")
        if login:
            correct_user = setting("auth", "username", "admin")
            correct_hash = setting("auth", "password_hash")
            user_ok = hmac.compare_digest(username, correct_user)
            pass_ok = verify_password(password, correct_hash)
            if user_ok and pass_ok:
                st.session_state.admin = True
                st.rerun()
            else:
                st.error("Credenciales incorrectas o autenticación no configurada.")
    st.caption("Consulta pública · edición restringida a administradores")

url = st.secrets.get("supabase", {}).get("url", "")
server_key = st.secrets.get("supabase", {}).get("service_role_key", "")
if not url or not server_key:
    st.error("Falta configurar [supabase] url y service_role_key en Streamlit Secrets. La clave publishable no sirve para escritura con las políticas RLS actuales.")
    st.stop()
try:
    db = db_client(url, server_key)
    reportes = load("reportes")
    residuos = load("residuos")
    paneles = load("paneles")
except Exception as exc:
    st.error("No se pudo consultar Supabase. Comprueba la clave de servidor, la URL y las tablas.")
    st.code(str(exc))
    st.stop()

st.info("**Datos iniciales:** 54 paneles OSB de 1,22 × 2,44 m y 12,5 mm; seis vanos de ventana de 1 × 1 m. Los 5 m³ retirados y $27.000/m³ corresponden a antecedentes informados, aún pendientes de respaldo. No sumar el OSB al retiro global sin comprobar si ya está incluido.")

with st.expander("📐 Cubicación de paneles y recortes", expanded=True):
    c1, c2, c3, c4 = st.columns(4)
    n = c1.number_input("Paneles", min_value=0, value=54, step=1)
    width = c2.number_input("Ancho panel (m)", min_value=0.01, value=1.22)
    height = c3.number_input("Alto panel (m)", min_value=0.01, value=2.44)
    thickness = c4.number_input("Espesor OSB (mm)", min_value=0.1, value=12.5)
    c5, c6, c7, c8 = st.columns(4)
    windows = c5.number_input("Vanos cortados", min_value=0, value=6, step=1)
    win_w = c6.number_input("Ancho vano (m)", min_value=0.0, value=1.0)
    win_h = c7.number_input("Alto vano (m)", min_value=0.0, value=1.0)
    faces = c8.selectbox("Caras OSB cortadas", [1, 2])
    area = n * width * height
    cut_area = windows * win_w * win_h * faces
    cut_volume = cut_area * thickness / 1000
    a, b, c, d = st.columns(4)
    a.metric("Área nominal paneles", f"{area:.2f} m²")
    b.metric("Área recortes OSB", f"{cut_area:.2f} m²")
    c.metric("Volumen recortes OSB", f"{cut_volume:.4f} m³")
    d.metric("Recorte / área nominal", f"{100 * cut_area / area if area else 0:.2f} %")
    st.caption("Estimación geométrica: no incluye recortes del pino 2×3, ni otros cortes; verificar dimensiones reales y número de caras.")

r1, r2, r3, r4 = st.columns(4)
r1.metric("Reportes guardados", len(reportes))
r2.metric("Registros de residuos", len(residuos))
r3.metric("Costo de retiros registrado", clp(residuos["costo_retiro_clp"].fillna(0).sum()) if not residuos.empty else clp(0))
r4.metric("Volumen registrado (m³)", f"{residuos.loc[residuos['unidad'].eq('m³'), 'cantidad'].fillna(0).sum():.2f}" if not residuos.empty else "0.00")

tab1, tab2, tab3 = st.tabs(["📊 Visor público", "📝 Administración", "🗂️ Historial"])
with tab1:
    if residuos.empty:
        st.warning("Todavía no existen residuos guardados. Las cifras geométricas superiores son supuestos editables, no reportes almacenados.")
    else:
        st.subheader("Residuos registrados por etapa")
        tmp = residuos.copy()
        tmp["cantidad"] = pd.to_numeric(tmp["cantidad"], errors="coerce").fillna(0)
        st.dataframe(tmp[["id", "reporte_id", "etapa", "material", "cantidad", "unidad", "destino", "estado_verificacion", "costo_retiro_clp"]], hide_index=True, use_container_width=True)
        st.caption("No se agregan cantidades de unidades distintas.")
        cubic = tmp[tmp["unidad"] == "m³"].groupby("etapa", as_index=False)["cantidad"].sum()
        if not cubic.empty:
            st.bar_chart(cubic.set_index("etapa"))
        st.download_button("Descargar residuos CSV", tmp.to_csv(index=False).encode("utf-8-sig"), "residuos_vivienda_esperanza.csv", "text/csv")

with tab2:
    if not st.session_state.get("admin", False):
        st.warning("Para registrar o modificar datos, ingresa con el usuario administrador en el menú lateral.")
    else:
        st.subheader("Nuevo reporte y registro de residuos")
        with st.form("new_report"):
            fecha = st.date_input("Fecha del reporte", value=date.today())
            responsable = st.text_input("Responsable", value="Equipo Vivienda Esperanza")
            observaciones = st.text_area("Observaciones", value="Registro preliminar, pendiente de verificación documental")
            st.markdown("**Residuo asociado al reporte**")
            etapa = st.selectbox("Etapa", ["Demolición inicial", "Montaje de paneles / vanos", "Terminaciones", "Otros"])
            material = st.text_input("Material / descripción", value="Retiro global de residuos de demolición")
            origen = st.text_input("Origen", value="Demolición inicial")
            a, b, c = st.columns(3)
            cantidad = a.number_input("Cantidad", min_value=0.0, value=5.0, step=0.1)
            unidad = b.selectbox("Unidad", ["m³", "m²", "kg", "un", "ml"])
            costo = c.number_input("Costo retiro (CLP)", min_value=0.0, value=135000.0, step=1000.0)
            destino = st.text_input("Destino", value="Retiro externo, destino por confirmar")
            estado = st.selectbox("Verificación", ["Informado, pendiente de respaldo", "Estimación geométrica", "Medido en terreno", "Verificado documentalmente"])
            evidencia = st.text_area("Evidencia / respaldo", value="5 m³ aproximados × $27.000/m³; verificar comprobante")
            save = st.form_submit_button("💾 Guardar reporte y residuo", type="primary")
        if save:
            if not material.strip():
                st.error("Indica un material o descripción.")
            else:
                try:
                    created = db.table("reportes").insert({"fecha_reporte": fecha.isoformat(), "responsable": responsable, "observaciones": observaciones}).execute()
                    rid = created.data[0]["id"]
                    try:
                        db.table("residuos").insert({"reporte_id": rid, "etapa": etapa, "material": material, "origen": origen, "cantidad": cantidad, "unidad": unidad, "destino": destino, "estado_verificacion": estado, "costo_retiro_clp": costo, "observaciones": evidencia}).execute()
                        db.table("paneles").insert({"reporte_id": rid, "cantidad_paneles": n, "ancho_m": width, "alto_m": height, "espesor_osb_m": thickness / 1000, "cantidad_ventanas": windows, "ancho_ventana_m": win_w, "alto_ventana_m": win_h, "observaciones": f"Caras cortadas: {faces}. Área estimada: {cut_area:.4f} m²; volumen: {cut_volume:.4f} m³."}).execute()
                    except Exception:
                        db.table("reportes").delete().eq("id", rid).execute()
                        raise
                    st.success(f"Reporte #{rid} guardado en Supabase.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Error al guardar: {exc}")
        st.divider()
        st.subheader("Agregar residuo a un reporte existente")
        if not reportes.empty:
            with st.form("add_waste"):
                rid = st.selectbox("Reporte", reportes["id"].astype(int).tolist(), format_func=lambda x: f"Reporte #{x}")
                etapa2 = st.selectbox("Etapa", ["Demolición inicial", "Montaje de paneles / vanos", "Terminaciones", "Otros"], key="e2")
                mat2 = st.text_input("Material", value="Recortes OSB de ventanas")
                col1, col2, col3 = st.columns(3)
                qty2 = col1.number_input("Cantidad", min_value=0.0, value=float(cut_area), key="q2")
                unit2 = col2.selectbox("Unidad", ["m²", "m³", "kg", "un", "ml"], key="u2")
                cost2 = col3.number_input("Costo retiro CLP", min_value=0.0, value=0.0, key="c2")
                dest2 = st.text_input("Destino", value="Desecho retirado, destino por confirmar", key="d2")
                status2 = st.selectbox("Verificación", ["Estimación geométrica", "Informado, pendiente de respaldo", "Medido en terreno", "Verificado documentalmente"], key="s2")
                notes2 = st.text_area("Observaciones", value=f"{windows} ventanas, {faces} cara(s), OSB {thickness} mm; no sumar al retiro global sin conciliación.", key="n2")
                add = st.form_submit_button("Agregar residuo")
            if add:
                try:
                    db.table("residuos").insert({"reporte_id": int(rid), "etapa": etapa2, "material": mat2, "origen": "Montaje / corte en obra", "cantidad": qty2, "unidad": unit2, "destino": dest2, "estado_verificacion": status2, "costo_retiro_clp": cost2, "observaciones": notes2}).execute()
                    st.success("Residuo agregado.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Error: {exc}")
        st.divider()
        st.subheader("Modificar un registro existente")
        if not residuos.empty:
            with st.form("edit_waste"):
                selected = st.selectbox("ID del registro", residuos["id"].astype(int).tolist())
                current = residuos.loc[residuos["id"] == selected].iloc[0]
                material_edit = st.text_input("Descripción", value=str(current["material"]))
                q_edit = st.number_input("Cantidad actualizada", min_value=0.0, value=float(current["cantidad"]), key=f"editq{selected}")
                cost_edit = st.number_input("Costo retiro actualizado CLP", min_value=0.0, value=float(current["costo_retiro_clp"] or 0), key=f"editc{selected}")
                evidence_edit = st.text_area("Respaldo de modificación", value=str(current.get("observaciones") or ""))
                update = st.form_submit_button("Guardar modificación")
            if update:
                try:
                    db.table("residuos").update({"material": material_edit, "cantidad": q_edit, "costo_retiro_clp": cost_edit, "observaciones": evidence_edit}).eq("id", int(selected)).execute()
                    st.success("Registro actualizado.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Error: {exc}")

with tab3:
    if reportes.empty:
        st.info("Sin reportes registrados.")
    else:
        st.dataframe(reportes[["id", "fecha_reporte", "responsable", "observaciones", "creado_en"]], use_container_width=True, hide_index=True)
        st.download_button("Descargar historial CSV", reportes.to_csv(index=False).encode("utf-8-sig"), "reportes_vivienda_esperanza.csv", "text/csv")
    if not paneles.empty:
        with st.expander("Registros de geometría de paneles"):
            st.dataframe(paneles, use_container_width=True, hide_index=True)

st.caption("Proyecto Vivienda Esperanza · Registro de datos y estimaciones diferenciados · Los costos de retiro no son ahorros ni valorización económica verificada.")
