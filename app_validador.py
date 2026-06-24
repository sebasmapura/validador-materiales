import streamlit as st
import pandas as pd
from io import BytesIO
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Validador", page_icon="🔍", layout="wide")

st.markdown("""
<h1 style="text-align: center; color: #667eea;">
    🔍 Validador de Materiales
</h1>
<p style="text-align: center; color: #666;">
    ¿Cargué esto en la BBDD después de diseñar?
</p>
""", unsafe_allow_html=True)

st.divider()

# CARGAR ARCHIVOS
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📊 SolidWorks (2601.xls)")
    st.caption("Columna 2 = Referencias a buscar")
    sw_file = st.file_uploader("Carga SolidWorks", type=["xlsx", "xls", "csv"], key="sw")
    sw_data = None
    if sw_file:
        try:
            sw_data = pd.read_excel(sw_file) if not sw_file.name.endswith('.csv') else pd.read_csv(sw_file)
            st.success(f"✅ {len(sw_data)} filas")
        except Exception as e:
            st.error(f"Error: {e}")

with col2:
    st.markdown("### 🗄️ BBDD (ProyectosXConjArt.xlsx)")
    st.caption("Buscará en: Elementos.ref_empresa + Proyectos.ref_empresa")
    bbdd_file = st.file_uploader("Carga BBDD", type=["xlsx", "xls", "csv"], key="bbdd")
    bbdd_data = None
    if bbdd_file:
        try:
            bbdd_data = pd.read_excel(bbdd_file) if not bbdd_file.name.endswith('.csv') else pd.read_csv(bbdd_file)
            st.success(f"✅ {len(bbdd_data)} filas")
        except Exception as e:
            st.error(f"Error: {e}")

# VALIDAR
if sw_data is not None and bbdd_data is not None:
    st.divider()
    st.markdown("## 🚀 Validación")
    
    # Verificar columnas
    sw_cols = list(sw_data.columns)
    
    if len(sw_cols) < 2:
        st.error("❌ SolidWorks necesita al menos 2 columnas")
    else:
        col_numero_sw = sw_cols[1]  # Columna 2
        
        st.info(f"""
        📊 **SolidWorks:** Buscando referencias de la columna 2 → **{col_numero_sw}**
        
        🗄️  **BBDD:** Buscará SOLO en:
        - Elementos.ref_empresa
        - Proyectos.ref_empresa
        
        ⚠️ NO se consideran: id_elemento_mps (son códigos internos BBDD)
        """)
        
        st.divider()
        
        if st.button("🔍 VALIDAR", use_container_width=True, type="primary"):
            with st.spinner("Validando... buscando en ref_empresa"):
                
                # PASO 1: Extraer referencias de SolidWorks
                referencias_sw = {}
                for idx, row in sw_data.iterrows():
                    try:
                        ref = row[col_numero_sw]
                        if pd.notna(ref):
                            # Intentar convertir a número
                            try:
                                ref_num = int(float(str(ref).strip()))
                                if ref_num not in referencias_sw:
                                    referencias_sw[ref_num] = True
                            except:
                                pass
                    except:
                        pass
                
                st.info(f"✅ Leídas {len(referencias_sw)} referencias únicas de SolidWorks")
                
                # PASO 2: Extraer referencias de BBDD (SOLO ref_empresa)
                referencias_bbdd = set()
                
                # Elementos.ref_empresa
                if 'Elementos.ref_empresa' in bbdd_data.columns:
                    for val in bbdd_data['Elementos.ref_empresa']:
                        try:
                            if pd.notna(val):
                                ref_num = int(float(str(val).strip()))
                                referencias_bbdd.add(ref_num)
                        except:
                            pass
                
                # Proyectos.ref_empresa
                if 'Proyectos.ref_empresa' in bbdd_data.columns:
                    for val in bbdd_data['Proyectos.ref_empresa']:
                        try:
                            if pd.notna(val):
                                ref_num = int(float(str(val).strip()))
                                referencias_bbdd.add(ref_num)
                        except:
                            pass
                
                st.info(f"✅ Encontradas {len(referencias_bbdd)} referencias únicas en BBDD (ref_empresa)")
                
                # PASO 3: Comparar
                resultado = []
                hay_count = 0
                no_hay_count = 0
                
                for ref_sw in sorted(referencias_sw.keys()):
                    if ref_sw in referencias_bbdd:
                        estado = "✓ HAY"
                        hay_count += 1
                    else:
                        estado = "✗ NO HAY"
                        no_hay_count += 1
                    
                    resultado.append({
                        'Referencia': ref_sw,
                        'Estado': estado
                    })
                
                st.session_state.resultado = resultado
                st.session_state.hay_count = hay_count
                st.session_state.no_hay_count = no_hay_count
                st.session_state.validado = True
        
        # MOSTRAR RESULTADOS
        if 'validado' in st.session_state:
            st.divider()
            st.markdown("## 📊 RESULTADOS")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("📊 Total Referencias", len(st.session_state.resultado))
            col2.metric("✓ HAY en BBDD", st.session_state.hay_count)
            col3.metric("✗ NO HAY en BBDD", st.session_state.no_hay_count)
            
            if len(st.session_state.resultado) > 0:
                pct = (st.session_state.hay_count / len(st.session_state.resultado) * 100)
                st.markdown(f"### {pct:.1f}% de los elementos están cargados en BBDD")
            
            st.divider()
            
            df = pd.DataFrame(st.session_state.resultado)
            
            tab1, tab2, tab3 = st.tabs(["📋 TODAS", "✓ HAY EN BBDD", "✗ NO HAY EN BBDD"])
            
            with tab1:
                st.markdown("### Validación Completa")
                
                # Mostrar con colores
                for idx, row in df.iterrows():
                    if '✓' in row['Estado']:
                        st.success(f"✓ **{row['Referencia']}**")
                    else:
                        st.error(f"✗ **{row['Referencia']}**")
                
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
                        "Validacion_BBDD.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                with col2:
                    st.download_button(
                        "📥 Descargar CSV",
                        df.to_csv(index=False),
                        "Validacion_BBDD.csv",
                        "text/csv",
                        use_container_width=True
                    )
            
            with tab2:
                df_hay = df[df['Estado'] == "✓ HAY"]
                if len(df_hay) > 0:
                    st.markdown(f"### ✓ {len(df_hay)} Referencias encontradas en BBDD")
                    for idx, row in df_hay.iterrows():
                        st.success(f"✓ **{row['Referencia']}**")
                else:
                    st.info("No hay referencias encontradas")
            
            with tab3:
                df_no_hay = df[df['Estado'] == "✗ NO HAY"]
                if len(df_no_hay) > 0:
                    st.markdown(f"### ✗ {len(df_no_hay)} Referencias NO encontradas en BBDD")
                    st.error("**DEBES CARGAR ESTAS REFERENCIAS EN LA BBDD:**")
                    
                    # Mostrar en grupos de 10
                    for idx, row in df_no_hay.iterrows():
                        st.error(f"✗ **{row['Referencia']}**")
                    
                    # Descargar lista de faltantes
                    csv_faltantes = df_no_hay.to_csv(index=False)
                    st.download_button(
                        "📥 Descargar Referencias Faltantes (CSV)",
                        csv_faltantes,
                        "Referencias_Faltantes.csv",
                        "text/csv",
                        use_container_width=True
                    )
                else:
                    st.success("✅ ¡Todas las referencias están en la BBDD!")

st.divider()
st.markdown("<p style='text-align: center; color: #999;'>🔍 Validador Final - CORRECTO</p>", 
            unsafe_allow_html=True)
