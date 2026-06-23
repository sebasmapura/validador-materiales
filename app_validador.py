import streamlit as st
import pandas as pd
from io import BytesIO
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Validador", page_icon="🔍", layout="wide")

st.markdown("""
<h1 style="text-align: center; color: #667eea;">
    🔍 Validador de Listas de Materiales
</h1>
<p style="text-align: center; color: #666;">
    SolidWorks Col2 vs BBDD (Proyectos.ref_empresa + Elementos.ref_empresa)
</p>
""", unsafe_allow_html=True)

st.divider()

# CARGAR ARCHIVOS
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📊 SolidWorks")
    sw_file = st.file_uploader("Carga tu SolidWorks", type=["xlsx", "xls", "csv"])
    sw_data = None
    if sw_file:
        try:
            sw_data = pd.read_excel(sw_file) if not sw_file.name.endswith('.csv') else pd.read_csv(sw_file)
            st.success(f"✅ {sw_file.name}")
            st.caption(f"Filas: {len(sw_data)}")
        except Exception as e:
            st.error(f"Error: {e}")

with col2:
    st.markdown("### 🗄️ Base de Datos")
    bbdd_file = st.file_uploader("Carga tu BBDD", type=["xlsx", "xls", "csv"])
    bbdd_data = None
    if bbdd_file:
        try:
            bbdd_data = pd.read_excel(bbdd_file) if not bbdd_file.name.endswith('.csv') else pd.read_csv(bbdd_file)
            st.success(f"✅ {bbdd_file.name}")
            st.caption(f"Filas: {len(bbdd_data)}")
        except Exception as e:
            st.error(f"Error: {e}")

# VALIDAR
if sw_data is not None and bbdd_data is not None:
    st.divider()
    st.markdown("## 🚀 Validación")
    
    # Verificar columnas
    sw_cols = list(sw_data.columns)
    bbdd_cols = list(bbdd_data.columns)
    
    col1, col2 = st.columns(2)
    with col1:
        if len(sw_cols) >= 2:
            sw_col = sw_cols[1]
            st.info(f"📊 Columna 2 SolidWorks: **{sw_col}**")
        else:
            st.error("SolidWorks necesita al menos 2 columnas")
            sw_data = None
    
    with col2:
        proyectos_col = None
        elementos_col = None
        for col in bbdd_cols:
            if 'proyectos' in str(col).lower() and 'ref' in str(col).lower():
                proyectos_col = col
            if 'elementos' in str(col).lower() and 'ref' in str(col).lower():
                elementos_col = col
        
        info_msg = "🗄️ BBDD: Buscará en\n"
        if proyectos_col:
            info_msg += f"  • {proyectos_col}\n"
        if elementos_col:
            info_msg += f"  • {elementos_col}"
        st.info(info_msg)
    
    st.divider()
    
    if st.button("🚀 VALIDAR", use_container_width=True, type="primary"):
        with st.spinner("Validando..."):
            
            # PROCESAR SOLIDWORKS
            sw_elements = []
            for idx, row in sw_data.iterrows():
                try:
                    ref = str(row[sw_col]).strip() if pd.notna(row[sw_col]) else ""
                    cols = list(row.index)
                    col1 = str(row[cols[0]]).strip() if pd.notna(row[cols[0]]) else ""
                    col3 = str(row[cols[2]]).strip() if len(cols) > 2 and pd.notna(row[cols[2]]) else ""
                    qty = int(row[cols[3]]) if len(cols) > 3 and pd.notna(row[cols[3]]) else 1
                    
                    if ref:
                        sw_elements.append({
                            'col1': col1,
                            'ref': ref.lower(),
                            'ref_orig': ref,
                            'desc': col3,
                            'qty': qty
                        })
                except:
                    pass
            
            # PROCESAR BBDD
            bbdd_elements = []
            for idx, row in bbdd_data.iterrows():
                try:
                    refs = []
                    if proyectos_col and pd.notna(row[proyectos_col]):
                        refs.append(str(row[proyectos_col]).strip().lower())
                    if elementos_col and pd.notna(row[elementos_col]):
                        refs.append(str(row[elementos_col]).strip().lower())
                    
                    if not refs:
                        continue
                    
                    qty = 0
                    for col in bbdd_data.columns:
                        if 'cant' in str(col).lower():
                            qty = int(row[col]) if pd.notna(row[col]) else 0
                            break
                    
                    desc = ""
                    for col in bbdd_data.columns:
                        if 'descripcion' in str(col).lower():
                            desc = str(row[col]).strip() if pd.notna(row[col]) else ""
                            break
                    
                    for ref in refs:
                        bbdd_elements.append({
                            'ref': ref,
                            'desc': desc,
                            'qty': qty
                        })
                except:
                    pass
            
            st.info(f"Procesados: {len(sw_elements)} SolidWorks, {len(bbdd_elements)} BBDD")
            
            # COMPARAR
            consolidado = []
            discrepancias = []
            
            for sw in sw_elements:
                match = None
                for bb in bbdd_elements:
                    if sw['ref'] == bb['ref']:
                        match = bb
                        break
                
                if not match:
                    estado = "✗ FALTA"
                    accion = "Crear en BBDD"
                    discrepancias.append({'ref': sw['ref_orig'], 'tipo': 'FALTA', 'qty_sw': sw['qty']})
                elif sw['qty'] != match['qty']:
                    estado = "⚠ QTY"
                    accion = f"BBDD: {match['qty']} → SW: {sw['qty']}"
                    discrepancias.append({'ref': sw['ref_orig'], 'tipo': 'QTY', 'qty_sw': sw['qty'], 'qty_bb': match['qty']})
                else:
                    estado = "✓ OK"
                    accion = "Correcto"
                
                consolidado.append({
                    'Ref': sw['ref_orig'],
                    'Descripción': sw['desc'],
                    'Qty SW': sw['qty'],
                    'Qty BBDD': match['qty'] if match else 'FALTA',
                    'Estado': estado,
                    'Acción': accion
                })
            
            st.session_state.consolidado = consolidado
            st.session_state.discrepancias = discrepancias
            st.session_state.validado = True
    
    # MOSTRAR RESULTADOS
    if 'validado' in st.session_state:
        st.divider()
        st.markdown("## 📊 Resultados")
        
        df = pd.DataFrame(st.session_state.consolidado)
        ok = len([x for x in st.session_state.consolidado if '✓' in x['Estado']])
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total", len(st.session_state.consolidado))
        col2.metric("✓ OK", ok)
        col3.metric("⚠ Qty", len([x for x in st.session_state.consolidado if '⚠' in x['Estado']]))
        col4.metric("✗ Falta", len([x for x in st.session_state.consolidado if '✗' in x['Estado']]))
        
        st.divider()
        
        tab1, tab2, tab3 = st.tabs(["Consolidado", "Problemas", "OK"])
        
        with tab1:
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            col1, col2 = st.columns(2)
            with col1:
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Consolidado', index=False)
                st.download_button(
                    "📥 Descargar Excel",
                    output.getvalue(),
                    "Consolidado.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            with col2:
                st.download_button(
                    "📥 Descargar CSV",
                    df.to_csv(index=False),
                    "Consolidado.csv",
                    "text/csv",
                    use_container_width=True
                )
        
        with tab2:
            if st.session_state.discrepancias:
                for d in st.session_state.discrepancias:
                    if d['tipo'] == 'FALTA':
                        st.error(f"❌ **{d['ref']}** - Falta en BBDD (Qty: {d['qty_sw']})")
                    else:
                        st.warning(f"⚠️ **{d['ref']}** - SW: {d['qty_sw']}, BBDD: {d['qty_bb']}")
            else:
                st.success("✅ Sin problemas")
        
        with tab3:
            ok_items = [x for x in st.session_state.consolidado if '✓' in x['Estado']]
            if ok_items:
                st.dataframe(pd.DataFrame(ok_items)[['Ref', 'Descripción', 'Qty SW']], use_container_width=True, hide_index=True)

st.divider()
st.markdown("<p style='text-align: center; color: #999;'>🔍 v4.0 - Validador de Materiales</p>", unsafe_allow_html=True)
