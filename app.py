"""Dashboard local Vivienda Esperanza. Ejecutar: python -m streamlit run app.py"""
import sqlite3
from datetime import date, datetime
from pathlib import Path
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

BASE = Path(__file__).resolve().parent
DB = BASE / 'vivienda_esperanza.sqlite3'
st.set_page_config(page_title='Valorización de residuos | Vivienda Esperanza', page_icon='♻️', layout='wide')

@st.cache_resource
def conexion():
    c = sqlite3.connect(str(DB), check_same_thread=False, timeout=20)
    c.execute('PRAGMA journal_mode=WAL')
    c.execute('''CREATE TABLE IF NOT EXISTS reportes (id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT NOT NULL, responsable TEXT NOT NULL, nota TEXT NOT NULL,
        creado TEXT NOT NULL, actualizado TEXT NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS partidas (id INTEGER PRIMARY KEY AUTOINCREMENT,
        reporte_id INTEGER NOT NULL, etapa TEXT NOT NULL, material TEXT NOT NULL,
        cantidad REAL NOT NULL, unidad TEXT NOT NULL, destino TEXT NOT NULL,
        calidad TEXT NOT NULL, costo_clp REAL NOT NULL DEFAULT 0,
        ahorro_clp REAL NOT NULL DEFAULT 0, costo_valorizacion_clp REAL NOT NULL DEFAULT 0,
        evidencia TEXT NOT NULL DEFAULT '', FOREIGN KEY(reporte_id) REFERENCES reportes(id))''')
    c.commit()
    return c

c = conexion()
def consulta(sql, args=()):
    return pd.read_sql_query(sql, c, params=args)
def clp(x):
    return '$' + f'{x:,.0f}'.replace(',', '.')

st.markdown('''<style>
.block-container{padding-top:1.1rem;max-width:1500px}
.hero{background:linear-gradient(110deg,#092d45,#116c82);border-radius:18px;padding:24px 28px;color:white;margin-bottom:18px}
.hero h1{color:white;margin:0;font-size:2.1rem}.hero p{color:#e5f4f6;margin:7px 0 0}
[data-testid="stMetric"]{border:1px solid #cbdde1;border-radius:14px;padding:14px;background:rgba(120,170,180,.06)}
</style>''', unsafe_allow_html=True)
logo = BASE / 'logo_duoc_uc.png'
if logo.exists():
    a,b=st.columns([1,7],vertical_alignment='center')
    with a: st.image(str(logo),use_container_width=True)
    with b: st.markdown('<div class="hero"><h1>♻️ Valorización de residuos</h1><p>Duoc UC · Vivienda Esperanza · Control físico y económico de RCD</p></div>',unsafe_allow_html=True)
else:
    st.markdown('<div class="hero"><h1>♻️ Valorización de residuos</h1><p>Duoc UC · Vivienda Esperanza · Control físico y económico de RCD</p></div>',unsafe_allow_html=True)

with st.sidebar:
    st.header('🕒 Centro de control')
    components.html('''<div style="font-family:Arial;background:#0b3449;color:white;padding:13px;border-radius:12px;text-align:center"><div id="reloj" style="font-size:28px;font-weight:700"></div><div id="fecha" style="font-size:13px"></div></div><script>function tic(){let d=new Date();document.getElementById('reloj').textContent=d.toLocaleTimeString('es-CL');document.getElementById('fecha').textContent=d.toLocaleDateString('es-CL',{weekday:'long',day:'numeric',month:'long',year:'numeric'});}tic();setInterval(tic,1000);</script>''',height=92)
    st.caption('Reloj local del navegador')
    st.link_button('📂 Carpeta técnica Drive','https://drive.google.com/drive/folders/1VJqQTbifp-w4MRRxEkLwQInxMbYieSzE')
    st.caption('Almacenamiento local SQLite. Para publicar con edición multiusuario se necesitará una base de datos persistente externa.')

st.info('**Criterio de cálculo:** 54 paneles prefabricados de 1,22 × 2,44 m, OSB de 12,5 mm y entramado de pino 2×3. Los 54 paneles son material de obra, **no residuos**. El recorte estimado se calcula exclusivamente por vanos; no se presume que todo el panel sea desecho.')

# Valores de referencia editables; nunca se escriben automáticamente como observaciones verificadas.
with st.expander('📐 Geometría de paneles y recortes de ventanas',expanded=True):
    a,b,d,e=st.columns(4)
    n=a.number_input('Paneles instalados / previstos',min_value=0,value=54,step=1)
    largo=b.number_input('Largo del panel (m)',min_value=0.01,value=2.44,step=.01)
    ancho=d.number_input('Ancho del panel (m)',min_value=0.01,value=1.22,step=.01)
    espesor=e.number_input('Espesor OSB (mm)',min_value=.1,value=12.5,step=.5)
    f,g,h=st.columns(3)
    vanos=f.number_input('Ventanas cortadas (un)',min_value=0,value=6,step=1)
    vano_ancho=g.number_input('Ancho del vano (m)',min_value=0.,value=1.,step=.05)
    vano_alto=h.number_input('Alto del vano (m)',min_value=0.,value=1.,step=.05)
    caras=st.selectbox('Caras de OSB efectivamente cortadas por vano',[1,2],index=0,help='No asumir doble cara: confirmar configuración del panel.')
    area_panel=n*largo*ancho
    area_recorte=vanos*vano_ancho*vano_alto*caras
    volumen_recorte=area_recorte*espesor/1000
    porcentaje=100*area_recorte/area_panel if area_panel else 0
    m1,m2,m3,m4=st.columns(4)
    m1.metric('Área nominal de 54 paneles',f'{area_panel:.2f} m²')
    m2.metric('OSB recortado (estimado)',f'{area_recorte:.2f} m²')
    m3.metric('Volumen OSB recortado',f'{volumen_recorte:.4f} m³')
    m4.metric('Recorte / área nominal',f'{porcentaje:.2f} %')
    st.caption('Cálculo geométrico bruto: supone vanos completos cortados en obra. No incluye pino 2×3, cortes adicionales, espesor de marcos ni otras pérdidas. El área nominal de paneles no equivale necesariamente al área neta instalada.')

st.subheader('📊 Reportes de obra')
tab1,tab2,tab3=st.tabs(['📝 Crear reporte','📈 Visor y edición','🗂️ Historial'])

COLUMNAS=['etapa','material','cantidad','unidad','destino','calidad','costo_clp','ahorro_clp','costo_valorizacion_clp','evidencia']
ETAPAS=['Demolición inicial','Montaje de paneles / vanos','Terminaciones','Otros']
CALIDADES=['Informado, pendiente de respaldo','Estimación geométrica','Medido en terreno','Verificado documentalmente']

with tab1:
    st.caption('**Primera etapa: demolición inicial.** El retiro global informado de 5 m³ se registra una sola vez; los recortes OSB pueden formar parte de ese volumen y no deben sumarse automáticamente.')
    with st.form('nuevo_reporte'):
        q1,q2=st.columns(2)
        fecha=q1.date_input('Fecha del reporte',date.today())
        responsable=q2.text_input('Responsable del registro','Equipo Vivienda Esperanza')
        nota=st.text_area('Observaciones / origen de los antecedentes','Datos iniciales informados; validar con guías, fotografías y cubicación.')
        partida_inicial=pd.DataFrame([
            ['Demolición inicial','Retiro global de residuos de demolición (composición por confirmar)',5.0,'m³','Retiro externo','Informado, pendiente de respaldo',135000.,0.,0.,'5 m³ aproximados × $27.000/m³; costo estimado, solicitar comprobante.'],
            ['Montaje de paneles / vanos','Recortes de OSB de ventanas',round(area_recorte,4),'m²','Desecho retirado','Estimación geométrica',0.,0.,0.,f'{vanos} vanos de {vano_ancho} × {vano_alto} m; {caras} cara(s), OSB {espesor} mm; volumen {volumen_recorte:.4f} m³. No sumar al retiro global sin conciliación.'],
            ['Montaje de paneles / vanos','Recortes de pino 2×3 de vanos',0.,'ml','Pendiente de verificar','Informado, pendiente de respaldo',0.,0.,0.,'Cantidad cero es marcador pendiente de medición, no constatación de ausencia.'],
        ],columns=COLUMNAS)
        datos=st.data_editor(partida_inicial,num_rows='dynamic',hide_index=True,use_container_width=True,key='editor_nuevo',column_config={
            'etapa':st.column_config.SelectboxColumn('Etapa',options=ETAPAS,required=True),
            'cantidad':st.column_config.NumberColumn('Cantidad',min_value=0.,format='%.4f',required=True),
            'unidad':st.column_config.SelectboxColumn('Unidad',options=['m³','m²','kg','un','ml'],required=True),
            'calidad':st.column_config.SelectboxColumn('Respaldo',options=CALIDADES,required=True),
            'costo_clp':st.column_config.NumberColumn('Costo efectivo/estimado CLP',min_value=0.),
            'ahorro_clp':st.column_config.NumberColumn('Ahorro verificado CLP',min_value=0.),
            'costo_valorizacion_clp':st.column_config.NumberColumn('Costo valorización CLP',min_value=0.)})
        guardar=st.form_submit_button('💾 Guardar nuevo reporte',type='primary')
    if guardar:
        numeros=['cantidad','costo_clp','ahorro_clp','costo_valorizacion_clp']
        validos=all(datos[col].notna().all() for col in ['etapa','material','cantidad','unidad','destino','calidad']) and not datos.empty
        validos=validos and all((pd.to_numeric(datos[col],errors='coerce').fillna(-1)>=0).all() for col in numeros)
        if not responsable.strip() or not validos: st.error('Complete los campos obligatorios; cantidades y costos deben ser números no negativos.')
        else:
            ahora=datetime.now().isoformat(timespec='seconds')
            with c:
                cursor=c.execute('INSERT INTO reportes(fecha,responsable,nota,creado,actualizado) VALUES (?,?,?,?,?)',(fecha.isoformat(),responsable.strip(),nota,ahora,ahora))
                rid=cursor.lastrowid
                for _,r in datos.iterrows():
                    valores=[float(r[k]) if k in numeros and pd.notna(r[k]) else (0. if k in numeros else str(r[k] if pd.notna(r[k]) else '')) for k in COLUMNAS]
                    c.execute('INSERT INTO partidas(reporte_id,'+','.join(COLUMNAS)+') VALUES ('+','.join(['?']*11)+')',[rid]+valores)
            st.success(f'Reporte #{rid} guardado. Puede editarlo en la pestaña Visor y edición.')

with tab2:
    reportes=consulta('SELECT * FROM reportes ORDER BY fecha DESC,id DESC')
    if reportes.empty: st.warning('Guarde primero un reporte en la pestaña Crear reporte.')
    else:
        opciones={f"#{int(r.id)} · {r.fecha} · {r.responsable}":int(r.id) for r in reportes.itertuples()}
        rid=st.selectbox('Seleccione un reporte',list(opciones),format_func=str,key='sel_reporte')
        rid=opciones[rid]
        actual=consulta('SELECT * FROM partidas WHERE reporte_id=? ORDER BY id',(rid,))
        st.markdown('**Indicadores del reporte seleccionado**')
        retiro=actual[(actual.etapa=='Demolición inicial') & (actual.unidad=='m³')]['cantidad'].sum()
        costo=actual.costo_clp.sum()
        ahorro=actual.ahorro_clp.sum()
        val_cost=actual.costo_valorizacion_clp.sum()
        k1,k2,k3,k4=st.columns(4)
        k1.metric('Demolición / retiro declarado',f'{retiro:.2f} m³')
        k2.metric('Costos registrados',clp(costo))
        k3.metric('Ahorros acreditados',clp(ahorro))
        k4.metric('Beneficio neto valorización',clp(ahorro-val_cost))
        st.caption('Los costos de retiro no son ahorros. Beneficio neto = ahorro verificado − costo incremental de valorización. El retiro de demolición y los recortes de ventanas se mantienen separados para evitar doble conteo.')
        l,r=st.columns(2)
        with l:
            st.markdown('**Costos por etapa (CLP)**')
            st.bar_chart(actual.groupby('etapa')['costo_clp'].sum())
        with r:
            st.markdown('**Registros por estado de evidencia**')
            st.bar_chart(actual['calidad'].value_counts())
        st.markdown('**Editar cantidades, costos, destino y evidencia del reporte**')
        with st.form(f'editar_{rid}'):
            edit=st.data_editor(actual[COLUMNAS],num_rows='dynamic',hide_index=True,use_container_width=True,key=f'tabla_{rid}',column_config={
                'etapa':st.column_config.SelectboxColumn('Etapa',options=ETAPAS),
                'cantidad':st.column_config.NumberColumn('Cantidad',min_value=0.,format='%.4f'),
                'unidad':st.column_config.SelectboxColumn('Unidad',options=['m³','m²','kg','un','ml']),
                'calidad':st.column_config.SelectboxColumn('Respaldo',options=CALIDADES)})
            guardar_cambios=st.form_submit_button('💾 Actualizar reporte seleccionado')
        if guardar_cambios:
            numericos=['cantidad','costo_clp','ahorro_clp','costo_valorizacion_clp']
            ok=not edit.empty and all(edit[col].notna().all() for col in ['etapa','material','cantidad','unidad','destino','calidad'])
            ok=ok and all((pd.to_numeric(edit[col],errors='coerce').fillna(-1)>=0).all() for col in numericos)
            if not ok: st.error('Revise campos obligatorios y valores numéricos no negativos.')
            else:
                with c:
                    c.execute('DELETE FROM partidas WHERE reporte_id=?',(rid,))
                    for _,r in edit.iterrows():
                        valores=[float(r[k]) if k in numericos and pd.notna(r[k]) else (0. if k in numericos else str(r[k] if pd.notna(r[k]) else '')) for k in COLUMNAS]
                        c.execute('INSERT INTO partidas(reporte_id,'+','.join(COLUMNAS)+') VALUES ('+','.join(['?']*11)+')',[rid]+valores)
                    c.execute('UPDATE reportes SET actualizado=? WHERE id=?',(datetime.now().isoformat(timespec='seconds'),rid))
                st.success('Cambios almacenados en SQLite. Actualice la página para ver los indicadores recalculados.')
        st.download_button('⬇️ Descargar detalle CSV',actual.to_csv(index=False).encode('utf-8-sig'),f'reporte_{rid}.csv',mime='text/csv')

with tab3:
    historial=consulta('''SELECT r.id,r.fecha,r.responsable,r.actualizado,
        COUNT(p.id) registros,
        COALESCE(SUM(CASE WHEN p.etapa='Demolición inicial' AND p.unidad='m³' THEN p.cantidad ELSE 0 END),0) retiro_demolicion_m3,
        COALESCE(SUM(p.costo_clp),0) costos_clp,
        COALESCE(SUM(p.ahorro_clp-p.costo_valorizacion_clp),0) beneficio_neto_clp
        FROM reportes r LEFT JOIN partidas p ON p.reporte_id=r.id
        GROUP BY r.id ORDER BY r.fecha,r.id''')
    if historial.empty: st.warning('Aún no existen reportes guardados.')
    else:
        st.dataframe(historial,hide_index=True,use_container_width=True)
        st.line_chart(historial.set_index('fecha')[['costos_clp','beneficio_neto_clp']])
        st.download_button('⬇️ Descargar historial CSV',historial.to_csv(index=False).encode('utf-8-sig'),'historial_vivienda_esperanza.csv',mime='text/csv')
        st.caption('Cada fila es una fotografía de un reporte. No sumar los volúmenes entre fechas si los reportes registran valores acumulados.')

st.divider()
st.caption('Modelo piloto · Valores iniciales declarados o estimados, pendientes de respaldo técnico. Fuente: antecedentes del proyecto Vivienda Esperanza y registro del equipo de obra. Base local: vivienda_esperanza.sqlite3.')
