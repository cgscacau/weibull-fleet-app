"""
Página de upload e gestão de dados
"""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Adicionar raiz ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

st.set_page_config(
    page_title="Dados - Weibull Fleet Analytics",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Gestão de Dados")

# Inicializar session state
if 'dataset' not in st.session_state:
    st.session_state.dataset = None

# Carregar dados de exemplo
def load_sample_data():
    sample_file = project_root / "storage" / "sample_fleet_data.csv"
    if sample_file.exists():
        return pd.read_csv(sample_file)
    return None

# Upload ou carregar exemplo
tab1, tab2 = st.tabs(["📥 Upload", "🔍 Visualizar"])

with tab1:
    st.markdown("## Carregar Dados")
    
    col1, col2 = st.columns(2)
    
    with col1:
        uploaded_file = st.file_uploader("Escolha um arquivo CSV", type=['csv'])
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.session_state.dataset = df
                st.success(f"✅ Arquivo carregado: {len(df)} registros")
            except Exception as e:
                st.error(f"❌ Erro ao carregar: {e}")
    
    with col2:
        if st.button("🔄 Carregar Dados de Exemplo", type="primary"):
            sample_data = load_sample_data()
            if sample_data is not None:
                st.session_state.dataset = sample_data
                st.success(f"✅ Dados de exemplo carregados: {len(sample_data)} registros")
            else:
                st.error("❌ Dados de exemplo não encontrados")

with tab2:
    if st.session_state.dataset is not None:
        df = st.session_state.dataset
        
        st.markdown("## 📋 Visualização dos Dados")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Registros", f"{len(df):,}")
        
        with col2:
            n_components = df['component'].nunique() if 'component' in df.columns else 0
            st.metric("Componentes Únicos", n_components)
        
        with col3:
            n_assets = df['asset_id'].nunique() if 'asset_id' in df.columns else 0
            st.metric("Ativos Únicos", n_assets)
        
        with col4:
            if 'censored' in df.columns:
                censoring_rate = df['censored'].mean() * 100
                st.metric("Taxa de Censura", f"{censoring_rate:.1f}%")
        
        st.markdown("---")
        
        # Mostrar dados
        n_rows = st.slider("Linhas para exibir", 5, 50, 10)
        st.dataframe(df.head(n_rows), use_container_width=True)
        
        # Informações das colunas
        st.markdown("### 📊 Informações das Colunas")
        col_info = pd.DataFrame({
            'Tipo': df.dtypes.astype(str),
            'Não Nulos': df.count(),
            'Valores Únicos': df.nunique()
        })
        st.dataframe(col_info)
    
    else:
        st.info("📥 Carregue os dados primeiro na aba 'Upload'")
