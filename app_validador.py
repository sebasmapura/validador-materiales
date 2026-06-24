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
    MVP: Validar QUÉ HAY y QUÉ NO HAY en BBDD
</p>
""", unsafe_allow_html=True)

st.divider()

# CARGAR ARCHIVOS
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📊 SolidWorks")
    st.caption("Col 2 = Referencia (a buscar)\nCol 3 = Cantidad")
    sw_file = st.file_uploader("Carga SolidWorks", type=["xlsx", "xls", "csv"], key="sw")
    sw_data = None
    if sw_file:
        try:
            sw_data = pd.read_excel(sw_file) if not sw_file.name.endswith('.csv') else pd.read_csv(sw_file)
            st.success(f"✅ {sw_file.name}")
            st.caption(f"Filas: {len(sw_data)}")
            with st.expander("Ver datos"):
                st.dataframe(sw_data.head(5), use_container_width=True)
        except Exception as e:
            st.error(f"Error: {e}")

with col2:
    st.markdown("### 🗄️ Base de Datos")
    st.caption("Buscará en TODAS las columnas")
    bbdd_file = st.file_uploader("Carga BBDD", type=["xlsx", "xls", "csv"], key="bbdd")
    bbdd_data = None
    if bbdd_file:
        try:
            bbdd_data = pd.read_excel(bbdd_file) if not bbdd_file.name.endswith('.csv') else pd.read_csv(bbdd_file)
            st.success(f"✅ {bbdd_file.name}")
            st.caption(f"Filas: {len(bbdd_data)}")
            with st.expander("Ver datos"):
                st.dataframe(bbdd_data.head(5), use_container_width=True)
        except Exception as e:
            st.error(f"Error: {e}")

# VALIDAR
if sw_data is not None and bbdd_data is not None:
    st.divider()
    
    # Verificar columnas
    sw_cols = list(sw_data.columns)
    
    if len(sw_cols) < 3:
        st.error("❌ SolidWorks necesita al menos 3 columnas")
    else:
        col_ref = sw_cols[1]  # Columna 2
        col_qty = sw_cols[2]  # Columna 3
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"📊 SolidWorks:\n  Col 2 (Ref): **{col_ref}**\n  Col 3 (Qty): **{col_qty}**")
        with col2:
            st.info(f"🗄️ BBDD:\n  Buscará **{col_ref}**\n  en TODAS las columnas")
        
        st.divider()
        
        if st.button("🚀 VALIDAR", use_container_width=True, type="primary"):
            with st.spinner("Validando..."):
                
                # LEER SOLIDWORKS
                referencias_sw = []
                for idx, row in sw_data.iterrows():
                    try:
                        ref = str(row[col_ref]).strip() if pd.notna(row[col_ref]) else ""
                        qty = int(row[col_qty]) if pd.notna(row[col_qty]) else 1
                        
                        if ref:
                            referencias_sw.append({
                                'referencia': ref,
                                'cantidad_sw': qty,
                                'encontrado': False
                            })
                    except:
                        pass
                
                # BUSCAR EN BBDD
                bbdd_referencias = set()
                for idx, row in bbdd_data.iterrows():
                    for col in bbdd_data.columns:
                        celda = str(row[col]).strip().lower() if pd.notna(row[col]) else ""
                        for ref_obj in referencias_sw:
                            if celda == ref_obj['referencia'].lower():
                                ref_obj['encontrado'] = True
                                bbdd_referencias.add(ref_obj['referencia'].lower())
                                break
                
                # CREAR RESULTADO
                resultado = []
                hay_count = 0
                no_hay_count = 0
                
                for ref_obj in referencias_sw:
                    if ref_obj['encontrado']:
                        estado = "✓ HAY"
                        severidad = "success"
                        hay_count += 1
                    else:
                        estado = "✗ NO HAY"
                        severidad = "error"
                        no_hay_count += 1
                    
                    resultado.append({
                        'Referencia': ref_obj['referencia'],
                        'Cantidad SolidWorks': ref_obj['cantidad_sw'],
                        'Estado': estado,
                        'Severidad': severidad
                    })
                
                st.session_state.resultado = resultado
                st.session_state.hay_count = hay_count
                st.session_state.no_hay_count = no_hay_count
                st.session_state.validado = True
        
        # MOSTRAR RESULTADOS
        if 'validado' in st.session_state:
            st.divider()
            st.markdown("## 📊 Resultados")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("📊 Total Referencias", len(st.session_state.resultado))
            col2.metric("✓ HAY en BBDD", st.session_state.hay_count)
            col3.metric("✗ NO HAY en BBDD", st.session_state.no_hay_count)
            
            st.divider()
            
            # Crear DataFrame
            df = pd.DataFrame(st.session_state.resultado)
            
            tab1, tab2, tab3 = st.tabs(["📋 Todas", "✓ HAY", "✗ NO HAY"])
            
            with tab1:
                st.markdown("### Validación Completa")
                
                # Mostrar con colores
                for idx, row in df.iterrows():
                    if '✓' in row['Estado']:
                        st.success(f"✓ **{row['Referencia']}** - Cantidad: {row['Cantidad SolidWorks']}")
                    else:
                        st.error(f"✗ **{row['Referencia']}** - Cantidad: {row['Cantidad SolidWorks']}")
                
                st.divider()
                
                # Descargar
                col1, col2 = st.columns(2)
                with col1:
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, sheet_name='Validacion', index=False)
                    st.download_button(
                        "📥 Descargar Excel",
                        output.getvalue(),
                        "Validacion_MVP.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                with col2:
                    st.download_button(
                        "📥 Descargar CSV",
                        df.to_csv(index=False),
                        "Validacion_MVP.csv",
                        "text/csv",
                        use_container_width=True
                    )
            
            with tab2:
                df_hay = df[df['Estado'] == "✓ HAY"]
                if len(df_hay) > 0:
                    st.markdown(f"### {len(df_hay)} Referencias encontradas en BBDD ✓")
                    for idx, row in df_hay.iterrows():
                        st.success(f"✓ **{row['Referencia']}** - Qty: {row['Cantidad SolidWorks']}")
                else:
                    st.info("No hay referencias encontradas")
            
            with tab3:
                df_no_hay = df[df['Estado'] == "✗ NO HAY"]
                if len(df_no_hay) > 0:
                    st.markdown(f"### {len(df_no_hay)} Referencias NO encontradas en BBDD ✗")
                    st.warning("Estas referencias FALTA cargarlas en la BBDD:")
                    for idx, row in df_no_hay.iterrows():
                        st.error(f"✗ **{row['Referencia']}** - Qty: {row['Cantidad SolidWorks']}")
                else:
                    st.success("¡Todas las referencias están en la BBDD!")

st.divider()
st.markdown("<p style='text-align: center; color: #999;'>🔍 MVP v1 - QUÉ HAY y QUÉ NO HAY</p>", 
            unsafe_allow_html=True)
