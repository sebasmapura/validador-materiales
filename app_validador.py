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
    Busca en TODAS las columnas de BBDD y suma cantidades
</p>
""", unsafe_allow_html=True)

st.divider()

# CARGAR ARCHIVOS
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📊 SolidWorks")
    st.caption("Columna 2 = Ref a buscar")
    sw_file = st.file_uploader("Carga tu SolidWorks", type=["xlsx", "xls", "csv"], key="sw")
    sw_data = None
    if sw_file:
        try:
            sw_data = pd.read_excel(sw_file) if not sw_file.name.endswith('.csv') else pd.read_csv(sw_file)
            st.success(f"✅ {sw_file.name}")
            st.caption(f"Filas: {len(sw_data)} | Cols: {len(sw_data.columns)}")
        except Exception as e:
            st.error(f"Error: {e}")

with col2:
    st.markdown("### 🗄️ Base de Datos")
    st.caption("Buscará en TODAS las columnas")
    bbdd_file = st.file_uploader("Carga tu BBDD", type=["xlsx", "xls", "csv"], key="bbdd")
    bbdd_data = None
    if bbdd_file:
        try:
            bbdd_data = pd.read_excel(bbdd_file) if not bbdd_file.name.endswith('.csv') else pd.read_csv(bbdd_file)
            st.success(f"✅ {bbdd_file.name}")
            st.caption(f"Filas: {len(bbdd_data)} | Cols: {len(bbdd_data.columns)}")
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
            st.info(f"📊 SolidWorks Columna 2: **{sw_col}**")
        else:
            st.error("SolidWorks necesita al menos 2 columnas")
            sw_data = None
    
    with col2:
        # Buscar columna de cantidad en BBDD
        cant_col = None
        for col in bbdd_cols:
            if 'cant' in str(col).lower():
                cant_col = col
                break
        
        if cant_col:
            st.info(f"🗄️ BBDD Columna de Cantidad: **{cant_col}**\n\nBuscará la referencia en TODAS las columnas")
        else:
            st.warning("⚠️ No encontré columna de cantidad en BBDD")
    
    st.divider()
    
    if st.button("🚀 VALIDAR", use_container_width=True, type="primary"):
        with st.spinner("Validando... buscando en todas las columnas y sumando cantidades"):
            
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
                            'ref': ref.strip(),
                            'ref_lower': ref.lower().strip(),
                            'desc': col3,
                            'qty': qty
                        })
                except:
                    pass
            
            st.info(f"✅ SolidWorks: {len(sw_elements)} elementos leídos")
            
            # PROCESAR BBDD - BUSCAR EN TODAS LAS COLUMNAS
            bbdd_encontrados = {}  # {ref: {'qty_total': X, 'filas': Y}}
            
            for idx, row in bbdd_data.iterrows():
                try:
                    # Obtener cantidad
                    qty = 0
                    if cant_col and pd.notna(row[cant_col]):
                        qty = int(row[cant_col])
                    
                    # BUSCAR LA REFERENCIA EN TODAS LAS COLUMNAS
                    for col in bbdd_cols:
                        celda = str(row[col]).strip().lower() if pd.notna(row[col]) else ""
                        
                        # Buscar si esta celda coincide con alguna ref de SolidWorks
                        for sw in sw_elements:
                            sw_ref_lower = sw['ref_lower']
                            
                            # Búsqueda exacta o parcial
                            if (celda == sw_ref_lower or 
                                sw_ref_lower in celda or 
                                celda in sw_ref_lower):
                                
                                # Registrar este hallazgo
                                if sw['ref'] not in bbdd_encontrados:
                                    bbdd_encontrados[sw['ref']] = {
                                        'qty_total': 0,
                                        'filas': []
                                    }
                                
                                bbdd_encontrados[sw['ref']]['qty_total'] += qty
                                bbdd_encontrados[sw['ref']]['filas'].append({
                                    'fila': idx + 2,
                                    'columna': col,
                                    'qty': qty
                                })
                                break
                
                except:
                    pass
            
            st.info(f"✅ BBDD: Elementos encontrados y cantidades sumadas")
            
            # COMPARAR
            consolidado = []
            discrepancias = []
            
            for sw in sw_elements:
                ref = sw['ref']
                sw_qty = sw['qty']
                
                if ref not in bbdd_encontrados:
                    # NO ENCONTRADO
                    estado = "✗ FALTA"
                    accion = "NO existe en BBDD"
                    bbdd_qty = "NO ENCONTRADO"
                    discrepancias.append({
                        'ref': ref,
                        'tipo': 'FALTA',
                        'qty_sw': sw_qty,
                        'qty_bbdd': None
                    })
                else:
                    # ENCONTRADO - COMPARAR CANTIDAD TOTAL
                    bbdd_qty = bbdd_encontrados[ref]['qty_total']
                    
                    if sw_qty == bbdd_qty:
                        estado = "✓ OK"
                        accion = f"Encontrado (Qty: {bbdd_qty})"
                    else:
                        estado = "⚠ QTY"
                        accion = f"BBDD tiene {bbdd_qty}, SW tiene {sw_qty}"
                        discrepancias.append({
                            'ref': ref,
                            'tipo': 'QTY',
                            'qty_sw': sw_qty,
                            'qty_bbdd': bbdd_qty
                        })
                
                consolidado.append({
                    'Ref': ref,
                    'Descripción': sw['desc'],
                    'Qty SolidWorks': sw_qty,
                    'Qty BBDD (Total)': bbdd_qty if ref in bbdd_encontrados else 'NO ENCONTRADO',
                    'Estado': estado,
                    'Acción': accion
                })
            
            st.session_state.consolidado = consolidado
            st.session_state.discrepancias = discrepancias
            st.session_state.bbdd_encontrados = bbdd_encontrados
            st.session_state.validado = True
    
    # MOSTRAR RESULTADOS
    if 'validado' in st.session_state:
        st.divider()
        st.markdown("## 📊 Resultados")
        
        df = pd.DataFrame(st.session_state.consolidado)
        ok = len([x for x in st.session_state.consolidado if '✓' in x['Estado']])
        qty_diff = len([x for x in st.session_state.consolidado if '⚠' in x['Estado']])
        falta = len([x for x in st.session_state.consolidado if '✗' in x['Estado']])
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📊 Total", len(st.session_state.consolidado))
        col2.metric("✓ OK", ok)
        col3.metric("⚠ Qty Diferente", qty_diff)
        col4.metric("✗ No Encontrado", falta)
        
        if len(st.session_state.consolidado) > 0:
            pct = (ok / len(st.session_state.consolidado) * 100)
            st.markdown(f"### {pct:.1f}% de los elementos están correctos")
        
        st.divider()
        
        tab1, tab2, tab3 = st.tabs(["📋 Consolidado Completo", "🔴 Problemas", "✓ OK"])
        
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
                    "Consolidado_Validacion.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            with col2:
                st.download_button(
                    "📥 Descargar CSV",
                    df.to_csv(index=False),
                    "Consolidado_Validacion.csv",
                    "text/csv",
                    use_container_width=True
                )
        
        with tab2:
            if st.session_state.discrepancias:
                st.markdown(f"### {len(st.session_state.discrepancias)} Problemas Encontrados")
                
                for d in st.session_state.discrepancias:
                    if d['tipo'] == 'FALTA':
                        st.error(f"❌ **{d['ref']}** - NO EXISTE en BBDD (SolidWorks requiere {d['qty_sw']} unidades)")
                    else:
                        st.warning(f"⚠️ **{d['ref']}** - Cantidad incorrecta:\n  • SolidWorks: {d['qty_sw']}\n  • BBDD (Total): {d['qty_bbdd']}")
                    st.divider()
            else:
                st.success("✅ TODOS LOS ELEMENTOS TIENEN CANTIDAD CORRECTA")
        
        with tab3:
            ok_items = [x for x in st.session_state.consolidado if '✓' in x['Estado']]
            if ok_items:
                st.markdown(f"### {len(ok_items)} Elementos Correctos ✓")
                st.dataframe(pd.DataFrame(ok_items)[['Ref', 'Descripción', 'Qty SolidWorks', 'Qty BBDD (Total)']], 
                           use_container_width=True, hide_index=True)
            else:
                st.info("No hay elementos perfectamente correctos")

st.divider()
st.markdown("<p style='text-align: center; color: #999;'>🔍 v5.0 - Busca en todas las columnas y suma cantidades</p>", 
            unsafe_allow_html=True)
