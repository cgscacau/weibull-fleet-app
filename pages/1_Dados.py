import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
root_path = Path(__file__).parent.parent
sys.path.insert(0, str(root_path))

# Configuração da página
st.set_page_config(
    page_title="Carregar Dados",
    page_icon="📁",
    layout="wide"
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .upload-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .info-box {
        background: #e7f3ff;
        border-left: 4px solid #2196f3;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .success-box {
        background: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .warning-box {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">📁 Carregar Dados</div>', unsafe_allow_html=True)
st.markdown("**Upload de dados históricos de falhas para análise de confiabilidade**")
st.markdown("---")

# Inicializar session_state
if 'df' not in st.session_state:
    st.session_state.df = None

# Seção de upload
st.markdown("""
<div class="upload-section">
    <h3 style="color: white; margin-bottom: 1rem;">📤 Upload de Arquivo</h3>
    <p style="color: white; opacity: 0.9;">
    Carregue seu arquivo com dados históricos de falhas.<br>
    <strong>Formatos aceitos:</strong> CSV (.csv) ou Excel (.xlsx, .xls)
    </p>
</div>
""", unsafe_allow_html=True)

# Informações sobre formato
with st.expander("📋 Formato do Arquivo Requerido", expanded=True):
    st.markdown("""
    ### Colunas Obrigatórias:
    
    | Coluna | Descrição | Exemplo | Tipo |
    |--------|-----------|---------|------|
    | `component_id` | Identificador único do equipamento | "MOTOR_001" | Texto |
    | `component_type` | Tipo/modelo do componente | "Motor Elétrico" | Texto |
    | `failure_time` | Tempo até falha (horas) | 5420 | Número |
    | `censored` | 0=falhou, 1=ainda funcionando | 0 ou 1 | Número |
    
    ### Colunas Opcionais:
    
    - `installation_date` - Data de instalação (YYYY-MM-DD)
    - `failure_date` - Data da falha (YYYY-MM-DD)
    - `location` - Localização do equipamento
    - `severity` - Gravidade da falha (1-5)
    - `operating_hours_per_day` - Horas de operação por dia
    
    ### Exemplo de Dados:
    
    ```csv
    component_id,component_type,failure_time,censored
    MOTOR_001,Motor Elétrico,5420,0
    MOTOR_002,Motor Elétrico,3890,0
    BOMBA_001,Bomba Hidráulica,6100,1
    ```
    """)

# Seção de templates
st.markdown("### 📥 Não Tem Dados Ainda?")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="info-box">
    <h4>📋 Baixe um Template</h4>
    <p>Use os templates prontos da página <strong>"📚 Como Usar"</strong> → Tab "Templates"</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("📚 Ir para Templates", use_container_width=True):
        st.switch_page("pages/0_Como_Usar.py")

with col2:
    st.markdown("""
    <div class="info-box">
    <h4>🧪 Use Dados de Exemplo</h4>
    <p>Teste o sistema com dados sintéticos prontos</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🧪 Carregar Dados de Exemplo", use_container_width=True):
        # Gera dados de exemplo
        import numpy as np
        np.random.seed(42)
        
        n_samples = 100
        tipos = ['Motor Elétrico', 'Bomba Hidráulica', 'Válvula']
        
        example_df = pd.DataFrame({
            'component_id': [f'EQUIP_{i:03d}' for i in range(1, n_samples + 1)],
            'component_type': np.random.choice(tipos, n_samples),
            'failure_time': np.random.weibull(2, n_samples) * 5000 + 1000,
            'censored': np.random.choice([0, 1], n_samples, p=[0.7, 0.3])
        })
        
        st.session_state.df = example_df
        st.success("✅ Dados de exemplo carregados com sucesso!")
        st.rerun()

st.markdown("---")

# Upload de arquivo
st.markdown("### 📤 Carregar Seu Arquivo")

uploaded_file = st.file_uploader(
    "Escolha um arquivo CSV ou Excel",
    type=['csv', 'xlsx', 'xls'],
    help="Arraste e solte ou clique para selecionar"
)

if uploaded_file is not None:
    try:
        # Detecta o tipo de arquivo e lê apropriadamente
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension == 'csv':
            # Tenta diferentes encodings para CSV
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8')
            except UnicodeDecodeError:
                uploaded_file.seek(0)  # Reset file pointer
                try:
                    df = pd.read_csv(uploaded_file, encoding='latin1')
                except:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding='iso-8859-1')
        
        elif file_extension in ['xlsx', 'xls']:
            # Lê Excel
            df = pd.read_excel(uploaded_file)
        
        else:
            st.error(f"❌ Formato de arquivo não suportado: .{file_extension}")
            st.stop()
        
        # Valida colunas obrigatórias
        required_columns = ['component_id', 'component_type', 'failure_time', 'censored']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.markdown("""
            <div class="warning-box">
            <h4>⚠️ Colunas Obrigatórias Faltando</h4>
            <p>Seu arquivo não contém as seguintes colunas obrigatórias:</p>
            </div>
            """, unsafe_allow_html=True)
            
            for col in missing_columns:
                st.error(f"❌ Faltando: `{col}`")
            
            st.markdown("""
            **Como corrigir:**
            1. Abra seu arquivo no Excel
            2. Renomeie as colunas para corresponder exatamente aos nomes acima
            3. Salve e faça upload novamente
            
            **Ou baixe um template na página "📚 Como Usar"**
            """)
            
            st.stop()
        
        # Validações básicas
        errors = []
        
        # Valida tipos de dados
        if not pd.api.types.is_numeric_dtype(df['failure_time']):
            errors.append("❌ Coluna 'failure_time' deve conter apenas números")
        
        if not pd.api.types.is_numeric_dtype(df['censored']):
            errors.append("❌ Coluna 'censored' deve conter apenas números (0 ou 1)")
        
        # Valida valores de censored
        if df['censored'].isin([0, 1]).sum() != len(df):
            errors.append("❌ Coluna 'censored' deve conter apenas valores 0 ou 1")
        
        # Valida valores negativos
        if (df['failure_time'] <= 0).any():
            errors.append("❌ Coluna 'failure_time' não pode ter valores negativos ou zero")
        
        # Valida dados faltando
        for col in required_columns:
            if df[col].isna().any():
                errors.append(f"❌ Coluna '{col}' tem valores faltando (células vazias)")
        
        if errors:
            st.markdown("""
            <div class="warning-box">
            <h4>⚠️ Problemas Encontrados nos Dados</h4>
            </div>
            """, unsafe_allow_html=True)
            
            for error in errors:
                st.error(error)
            
            st.markdown("""
            **Como corrigir:**
            - Verifique os dados no Excel
            - Corrija os problemas listados acima
            - Faça upload novamente
            
            **Ou use a página "🧼 Qualidade dos Dados" para limpeza assistida por IA**
            """)
            
            # Permite visualizar mesmo com erros
            if st.checkbox("🔍 Visualizar dados mesmo com erros (para diagnóstico)"):
                st.dataframe(df.head(20), use_container_width=True)
            
            st.stop()
        
        # Dados válidos!
        st.session_state.df = df
        
        st.markdown("""
        <div class="success-box">
        <h4>✅ Arquivo Carregado com Sucesso!</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # Estatísticas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Total de Registros", len(df))
        
        with col2:
            n_types = df['component_type'].nunique()
            st.metric("🔧 Tipos de Componentes", n_types)
        
        with col3:
            n_failures = (df['censored'] == 0).sum()
            st.metric("❌ Falhas Observadas", n_failures)
        
        with col4:
            n_censored = (df['censored'] == 1).sum()
            st.metric("⏱️ Dados Censurados", n_censored)
        
        # Preview dos dados
        st.markdown("### 🔍 Preview dos Dados")
        st.dataframe(df.head(20), use_container_width=True)
        
        # Informações por tipo de componente
        st.markdown("### 📊 Resumo por Componente")
        
        summary = df.groupby('component_type').agg({
            'component_id': 'count',
            'failure_time': ['mean', 'min', 'max'],
            'censored': lambda x: (x == 1).sum()
        }).round(0)
        
        summary.columns = ['Qtd', 'Tempo Médio (h)', 'Mín (h)', 'Máx (h)', 'Censurados']
        st.dataframe(summary, use_container_width=True)
        
        # Próximos passos
        st.markdown("---")
        st.markdown("### 🚀 Próximos Passos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🧼 Verificar Qualidade dos Dados", use_container_width=True):
                st.switch_page("pages/2_Qualidade_dos_Dados.py")
        
        with col2:
            if st.button("📈 Ir Direto para Análise Weibull", use_container_width=True):
                st.switch_page("pages/3_Weibull.py")
        
    except Exception as e:
        st.error(f"❌ Erro ao processar arquivo: {str(e)}")
        
        st.markdown("""
        **Dicas:**
        - Verifique se o arquivo não está corrompido
        - Tente salvar novamente no Excel
        - Use o formato CSV (mais confiável)
        - Baixe um template da página "📚 Como Usar"
        """)

# Se já tem dados carregados
elif st.session_state.df is not None:
    st.markdown("""
    <div class="success-box">
    <h4>✅ Dados já Carregados na Sessão</h4>
    </div>
    """, unsafe_allow_html=True)
    
    df = st.session_state.df
    
    # Estatísticas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total de Registros", len(df))
    
    with col2:
        n_types = df['component_type'].nunique()
        st.metric("🔧 Tipos de Componentes", n_types)
    
    with col3:
        n_failures = (df['censored'] == 0).sum()
        st.metric("❌ Falhas Observadas", n_failures)
    
    with col4:
        n_censored = (df['censored'] == 1).sum()
        st.metric("⏱️ Dados Censurados", n_censored)
    
    # Preview dos dados
    st.markdown("### 🔍 Dados Atuais")
    st.dataframe(df.head(20), use_container_width=True)
    
    # Opção de limpar dados
    if st.button("🗑️ Limpar Dados e Carregar Novos", use_container_width=True):
        st.session_state.df = None
        st.rerun()
    
    # Próximos passos
    st.markdown("---")
    st.markdown("### 🚀 Próximos Passos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🧼 Verificar Qualidade dos Dados", use_container_width=True):
            st.switch_page("pages/2_Qualidade_dos_Dados.py")
    
    with col2:
        if st.button("📈 Ir Direto para Análise Weibull", use_container_width=True):
            st.switch_page("pages/3_Weibull.py")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p><strong>💡 Dica:</strong> Use a página "📚 Como Usar" para baixar templates prontos!</p>
    <p style='font-size: 0.9rem; color: #999;'>Formatos suportados: CSV, Excel (.xlsx, .xls)</p>
</div>
""", unsafe_allow_html=True)
