import streamlit as st
import pandas as pd
from io import BytesIO
import requests
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Validador", page_icon="🔍", layout="wide")

st.markdown("""
<h1 style="text-align: center; color: #667eea;">
    🔍 Validador de Materiales
</h1>
<p style="text-align: center; color: #666;">
    Compara SolidWorks vs BBDD (Proyecto + Estática fusionadas)
</p>
""", unsafe_allow_html=True)

st.divider()

# ============= 1. SOLIDWORKS =============
st.markdown("## 📊 1. SolidWorks")
sw_file = st.file_uploader("Carga SolidWorks (2601.xls)", type=["xlsx", "xls", "csv"], key="sw")
sw_data = None

if sw_file:
    try:
        sw_data = pd.read_excel(sw_file) if not sw_file.name.endswith('.csv') else pd.read_csv(sw_file)
        st.success(f"✅ {len(sw_data)} filas cargadas")
    except Exception as e:
        st.error(f"Error: {e}")

# ============= 2. BBDD PROYECTO =============
st.divider()
st.markdown("## 📁 2. BBDD Proyecto (cargar)")
bbdd_proyecto_file = st.file_uploader("Carga BBDD Proyecto actual", type=["xlsx", "xls", "csv"], key="bbdd_proj")
bbdd_proyecto = None

if bbdd_proyecto_file:
    try:
        bbdd_proyecto = pd.read_excel(bbdd_proyecto_file) if not bbdd_proyecto_file.name.endswith('.csv') else pd.read_csv(bbdd_proyecto_file)
        st.success(f"✅ {len(bbdd_proyecto)} filas cargadas")
    except Exception as e:
        st.error(f"Error: {e}")

# ============= 3. BBDD ESTÁTICA (desde GitHub) =============
st.divider()
st.markdown("## 🗄️ 3. BBDD Estática (desde GitHub)")

bbdd_estatica = None
try:
    GITHUB_USER = "sebasmapura"  # ⚠️ CAMBIAR POR TU USUARIO
    REPO_NAME = "validador-materiales"
    
    url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/main/20260630ElementosTodos.xls"
    
    response = requests.get(url)
    if response.status_code == 200:
        bbdd_estatica = pd.read_excel(BytesIO(response.content))
        st.success(f"✅ BBDD Estática descargada ({len(bbdd_estatica)} filas)")
    else:
        st.warning(f"⚠️ No se pudo descargar BBDD Estática")
        
except Exception as e:
    st.warning(f"⚠️ Error descargando BBDD Estática: {e}")

# ============= VALIDAR =============
if sw_data is not None and (bbdd_proyecto is not None or bbdd_estatica is not None):
    st.divider()
    st.markdown("## 🚀 Validación")
    
    sw_cols = list(sw_data.columns)
    
    if len(sw_cols) < 2:
        st.error("❌ SolidWorks necesita al menos 2 columnas")
    else:
        col_numero_sw = sw_cols[1]
        
        bbdd_info = ""
        if bbdd_proyecto is not None:
            bbdd_info += f"✓ BBDD Proyecto ({len(bbdd_proyecto)} filas)\n"
        if bbdd_estatica is not None:
            bbdd_info += f"✓ BBDD Estática ({len(bbdd_estatica)} filas)"
        
        st.info(f"""
        📊 **SolidWorks:** {len(sw_data)} filas, referencias de columna 2 → **{col_numero_sw}**
        
        🗄️  **BBDD Fusionada:**
        {bbdd_info}
        
        ⚡ Búsqueda: Se compararán todas las referencias contra BBDD fusionada
        """)
        
        st.divider()
        
        if st.button("🔍 VALIDAR", use_container_width=True, type="primary"):
            with st.spinner("Validando..."):
                
                # PASO 1: Extraer referencias de SolidWorks
                referencias_sw = set()
                for idx, row in sw_data.iterrows():
                    try:
                        ref = row[col_numero_sw]
                        if pd.notna(ref):
                            try:
                                ref_num = int(float(str(ref).strip()))
                                referencias_sw.add(ref_num)
                            except:
                                pass
                    except:
                        pass
                
                st.info(f"✅ Leídas {len(referencias_sw)} referencias únicas de SolidWorks")
                
                # PASO 2: Extraer referencias de BBDD (fusionadas)
                referencias_bbdd = set()
                
                # De BBDD Proyecto
                if bbdd_proyecto is not None:
                    # Buscar en todas las columnas ref_empresa
                    for col in bbdd_proyecto.columns:
                        if 'ref' in str(col).lower():
                            for val in bbdd_proyecto[col]:
                                try:
                                    if pd.notna(val):
                                        ref_num = int(float(str(val).strip()))
                                        referencias_bbdd.add(ref_num)
                                except:
                                    pass
                
                # De BBDD Estática
                if bbdd_estatica is not None:
                    # Buscar en RefEmpresa
                    if 'RefEmpresa' in bbdd_estatica.columns:
                        for val in bbdd_estatica['RefEmpresa']:
                            try:
                                if pd.notna(val):
                                    ref_num = int(float(str(val).strip()))
                                    referencias_bbdd.add(ref_num)
                            except:
                                pass
                
                st.info(f"✅ Encontradas {len(referencias_bbdd)} referencias únicas en BBDD fusionada")
                
                # PASO 3: Comparar
                resultado = []
                hay_count = 0
                no_hay_count = 0
                
                for ref_sw in sorted(referencias_sw):
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
        
        # ============= MOSTRAR RESULTADOS =============
        if 'validado' in st.session_state:
            st.divider()
            st.markdown("## 📊 RESULTADOS")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("📊 Total Referencias", len(st.session_state.resultado))
            col2.metric("✓ HAY en BBDD", st.session_state.hay_count)
            col3.metric("✗ NO HAY en BBDD", st.session_state.no_hay_count)
            
            if len(st.session_state.resultado) > 0:
                pct = (st.session_state.hay_count / len(st.session_state.resultado) * 100)
                st.markdown(f"### {pct:.1f}% de elementos están en BBDD")
            
            st.divider()
            
            df = pd.DataFrame(st.session_state.resultado)
            
            tab1, tab2, tab3 = st.tabs(["📋 TODAS", "✓ HAY EN BBDD", "✗ NO HAY EN BBDD"])
            
            with tab1:
                st.markdown("### Validación Completa")
                
                for idx, row in df.iterrows():
                    if '✓' in row['Estado']:
                        st.success(f"✓ **{row['Referencia']}** → HAY")
                    else:
                        st.error(f"✗ **{row['Referencia']}** → NO HAY")
                
                st.divider()
                
                col1, col2 = st.columns(2)
                with col1:
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, sheet_name='Validacion', index=False)
                    st.download_button(
                        "📥 Descargar Excel",
                        output.getvalue(),
                        "Validacion_Completa.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                with col2:
                    st.download_button(
                        "📥 Descargar CSV",
                        df.to_csv(index=False),
                        "Validacion_Completa.csv",
                        "text/csv",
                        use_container_width=True
                    )
            
            with tab2:
                df_hay = df[df['Estado'] == "✓ HAY"]
                if len(df_hay) > 0:
                    st.markdown(f"### ✓ {len(df_hay)} Referencias en BBDD")
                    for idx, row in df_hay.iterrows():
                        st.success(f"✓ **{row['Referencia']}**")
                else:
                    st.info("No hay referencias")
            
            with tab3:
                df_no_hay = df[df['Estado'] == "✗ NO HAY"]
                if len(df_no_hay) > 0:
                    st.markdown(f"### ✗ {len(df_no_hay)} Referencias NO en BBDD")
                    st.error("**FALTA CARGAR EN BBDD:**")
                    
                    for idx, row in df_no_hay.iterrows():
                        st.error(f"✗ **{row['Referencia']}**")
                    
                    csv_faltantes = df_no_hay[['Referencia']].to_csv(index=False)
                    st.download_button(
                        "📥 Descargar Faltantes (CSV)",
                        csv_faltantes,
                        "Referencias_Faltantes.csv",
                        "text/csv",
                        use_container_width=True
                    )
                else:
                    st.success("✅ ¡Todos los elementos están en BBDD!")

else:
    st.warning("⏳ Carga: SolidWorks + al menos una BBDD (Proyecto o Estática)")

st.divider()
st.markdown("<p style='text-align: center; color: #999;'>🔍 Validador FINAL | SolidWorks vs BBDD Fusionada</p>", unsafe_allow_html=True)
