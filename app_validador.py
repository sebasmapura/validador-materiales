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
    SolidWorks vs BBDD Fusionada (Proyecto + Estática) | ELEMENTO/ARTÍCULO/AMBOS
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
st.markdown("## 📁 2. BBDD Proyecto")
bbdd_proyecto_file = st.file_uploader("Carga BBDD Proyecto actual", type=["xlsx", "xls", "csv"], key="bbdd_proj")
bbdd_proyecto = None

if bbdd_proyecto_file:
    try:
        bbdd_proyecto = pd.read_excel(bbdd_proyecto_file) if not bbdd_proyecto_file.name.endswith('.csv') else pd.read_csv(bbdd_proyecto_file)
        st.success(f"✅ {len(bbdd_proyecto)} filas cargadas")
    except Exception as e:
        st.error(f"Error: {e}")

# ============= 3. BBDD ESTÁTICA (GitHub) =============
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
        
        ⚡ Clasificación:
        - Elementos.ref_empresa (Proyecto) → 📦 ELEMENTO
        - Proyectos.ref_empresa (Proyecto) → 🏷️ ARTÍCULO
        - RefEmpresa (Estática) → 📦 ELEMENTO
        """)
        
        st.divider()
        
        if st.button("🔍 VALIDAR", use_container_width=True, type="primary"):
            with st.spinner("Validando y clasificando..."):
                
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
                
                # PASO 2: Crear BBDD fusionada clasificada por tipo
                referencias_clasificadas = {}
                
                # De BBDD Proyecto - ELEMENTOS
                if bbdd_proyecto is not None and 'Elementos.ref_empresa' in bbdd_proyecto.columns:
                    for val in bbdd_proyecto['Elementos.ref_empresa']:
                        try:
                            if pd.notna(val):
                                ref_num = int(float(str(val).strip()))
                                if ref_num not in referencias_clasificadas:
                                    referencias_clasificadas[ref_num] = {'es_elemento': False, 'es_articulo': False}
                                referencias_clasificadas[ref_num]['es_elemento'] = True
                        except:
                            pass
                
                # De BBDD Proyecto - ARTÍCULOS
                if bbdd_proyecto is not None and 'Proyectos.ref_empresa' in bbdd_proyecto.columns:
                    for val in bbdd_proyecto['Proyectos.ref_empresa']:
                        try:
                            if pd.notna(val):
                                ref_num = int(float(str(val).strip()))
                                if ref_num not in referencias_clasificadas:
                                    referencias_clasificadas[ref_num] = {'es_elemento': False, 'es_articulo': False}
                                referencias_clasificadas[ref_num]['es_articulo'] = True
                        except:
                            pass
                
                # De BBDD Estática - ELEMENTOS (RefEmpresa)
                if bbdd_estatica is not None and 'RefEmpresa' in bbdd_estatica.columns:
                    for val in bbdd_estatica['RefEmpresa']:
                        try:
                            if pd.notna(val):
                                ref_num = int(float(str(val).strip()))
                                if ref_num not in referencias_clasificadas:
                                    referencias_clasificadas[ref_num] = {'es_elemento': False, 'es_articulo': False}
                                referencias_clasificadas[ref_num]['es_elemento'] = True
                        except:
                            pass
                
                st.info(f"✅ BBDD fusionada: {len(referencias_clasificadas)} referencias únicas clasificadas")
                
                # PASO 3: Comparar SolidWorks con BBDD fusionada
                resultado = []
                hay_count = 0
                no_hay_count = 0
                elemento_count = 0
                articulo_count = 0
                ambos_count = 0
                
                for ref_sw in sorted(referencias_sw):
                    if ref_sw in referencias_clasificadas:
                        data = referencias_clasificadas[ref_sw]
                        
                        # Determinar tipo
                        if data['es_elemento'] and data['es_articulo']:
                            tipo = "AMBOS"
                            ambos_count += 1
                        elif data['es_elemento']:
                            tipo = "ELEMENTO"
                            elemento_count += 1
                        else:  # solo artículo
                            tipo = "ARTÍCULO"
                            articulo_count += 1
                        
                        estado = "✓ HAY"
                        hay_count += 1
                    else:
                        estado = "✗ NO HAY"
                        tipo = "NO EXISTE"
                        no_hay_count += 1
                    
                    resultado.append({
                        'Referencia': ref_sw,
                        'Estado': estado,
                        'Tipo': tipo
                    })
                
                st.session_state.resultado = resultado
                st.session_state.hay_count = hay_count
                st.session_state.no_hay_count = no_hay_count
                st.session_state.elemento_count = elemento_count
                st.session_state.articulo_count = articulo_count
                st.session_state.ambos_count = ambos_count
                st.session_state.validado = True
        
        # ============= MOSTRAR RESULTADOS =============
        if 'validado' in st.session_state:
            st.divider()
            st.markdown("## 📊 RESULTADOS")
            
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            col1.metric("📊 Total", len(st.session_state.resultado))
            col2.metric("✓ HAY", st.session_state.hay_count)
            col3.metric("📦 Elementos", st.session_state.elemento_count)
            col4.metric("🏷️ Artículos", st.session_state.articulo_count)
            col5.metric("🔗 Ambos", st.session_state.ambos_count)
            col6.metric("✗ NO HAY", st.session_state.no_hay_count)
            
            if len(st.session_state.resultado) > 0:
                pct = (st.session_state.hay_count / len(st.session_state.resultado) * 100)
                st.markdown(f"### {pct:.1f}% de elementos están en BBDD")
            
            st.divider()
            
            df = pd.DataFrame(st.session_state.resultado)
            
            # MOSTRAR TABLA COMPLETA
            st.markdown("### 📋 Validación Completa")
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.divider()
            
            # DESCARGAR
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
            
            st.divider()
            
            # FILTROS POR TIPO
            tab1, tab2, tab3, tab4, tab5 = st.tabs(
                ["✓ HAY", "📦 ELEMENTOS", "🏷️ ARTÍCULOS", "🔗 AMBOS", "✗ NO HAY"]
            )
            
            with tab1:
                df_hay = df[df['Estado'] == "✓ HAY"]
                if len(df_hay) > 0:
                    st.markdown(f"### ✓ {len(df_hay)} Referencias en BBDD")
                    st.dataframe(df_hay, use_container_width=True, hide_index=True)
                else:
                    st.info("No hay referencias")
            
            with tab2:
                df_elementos = df[df['Tipo'] == "ELEMENTO"]
                if len(df_elementos) > 0:
                    st.markdown(f"### 📦 {len(df_elementos)} Elementos en BBDD")
                    st.dataframe(df_elementos, use_container_width=True, hide_index=True)
                else:
                    st.info("No hay elementos")
            
            with tab3:
                df_articulos = df[df['Tipo'] == "ARTÍCULO"]
                if len(df_articulos) > 0:
                    st.markdown(f"### 🏷️ {len(df_articulos)} Artículos en BBDD")
                    st.dataframe(df_articulos, use_container_width=True, hide_index=True)
                else:
                    st.info("No hay artículos")
            
            with tab4:
                df_ambos = df[df['Tipo'] == "AMBOS"]
                if len(df_ambos) > 0:
                    st.markdown(f"### 🔗 {len(df_ambos)} Referencias en AMBOS")
                    st.dataframe(df_ambos, use_container_width=True, hide_index=True)
                else:
                    st.info("No hay referencias en ambos")
            
            with tab5:
                df_no_hay = df[df['Estado'] == "✗ NO HAY"]
                if len(df_no_hay) > 0:
                    st.markdown(f"### ✗ {len(df_no_hay)} Referencias NO en BBDD")
                    st.dataframe(df_no_hay, use_container_width=True, hide_index=True)
                    
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
st.markdown("<p style='text-align: center; color: #999;'>🔍 Validador FINAL PRECISO | ELEMENTO/ARTÍCULO/AMBOS</p>", unsafe_allow_html=True)
