import streamlit as st
from utils.state_manager import initialize_session_state, display_pipeline_status

# === INICIALIZAÇÃO OBRIGATÓRIA ===
initialize_session_state()

st.set_page_config(
    page_title="Planejamento PM & Estoque",
    page_icon="🔧",
    layout="wide"
)

# === HEADER ===
st.title("🔧 Planejamento PM & Estoque")
st.markdown("**Sistema integrado de otimização de manutenção preventiva e gestão de peças de reposição**")

# === DESCRIÇÃO DO SISTEMA ===
st.markdown("""
Este sistema utiliza análise de confiabilidade baseada na distribuição Weibull para otimizar:
- 📊 **Intervalos de manutenção preventiva**
- 📦 **Gestão de inventário de peças**
- 💰 **Custos de manutenção**
- ⚠️ **Análise de riscos**
""")

# === STATUS DO PIPELINE ===
st.markdown("---")
st.subheader("📊 Status do Sistema")
display_pipeline_status()

# === GUIA DE USO ===
st.markdown("---")
st.subheader("🚀 Como Usar")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 1️⃣ **Dados UNIFIED**
    
    📤 **Carregue seus dados** de falha
    
    **Formato esperado:**
    - `component_type`: Tipo do componente
    - `failure_time`: Tempo até falha
    - `censored`: Dados censurados (0/1)
    - `fleet`: Frota (opcional)
    """)

with col2:
    st.markdown("""
    ### 2️⃣ **Ajuste Weibull**
    
    📈 **Execute a análise** de confiabilidade
    
    **O sistema irá:**
    - Validar qualidade dos dados
    - Ajustar parâmetros Weibull
    - Calcular MTBF por componente
    - Gerar relatórios de qualidade
    """)

with col3:
    st.markdown("""
    ### 3️⃣ **Planejamento**
    
    🎯 **Otimize suas estratégias**
    
    **Funcionalidades:**
    - Intervalos ótimos de manutenção
    - Análise de custos
    - Gestão de estoque
    - Cenários de risco
    """)

# === INFORMAÇÕES TÉCNICAS ===
st.markdown("---")

with st.expander("🔧 **Informações Técnicas**"):
    st.markdown("""
    **Bibliotecas utilizadas:**
    - `lifelines`: Análise de sobrevivência e Weibull
    - `streamlit`: Interface web interativa
    - `pandas`: Manipulação de dados
    - `plotly`: Visualizações interativas
    
    **Requisitos de dados:**
    - Mínimo de 3 observações por componente
    - Tempos de falha > 0
    - Dados de censura válidos (0 ou 1)
    
    **Parâmetros Weibull:**
    - **λ (lambda)**: Parâmetro de escala
    - **ρ (rho)**: Parâmetro de forma
    - **MTBF**: Tempo médio entre falhas
    """)

# === NAVEGAÇÃO RÁPIDA ===
st.markdown("---")
st.subheader("🧭 Navegação Rápida")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📤 **Carregar Dados**", use_container_width=True, type="secondary"):
        st.switch_page("pages/1_Dados_UNIFIED.py")

with col2:
    if st.button("📈 **Análise Weibull**", use_container_width=True, type="secondary"):
        st.switch_page("pages/2_Ajuste_Weibull_UNIFIED.py")

with col3:
    if st.button("🔧 **Planejamento PM**", use_container_width=True, type="secondary"):
        st.switch_page("pages/3_Planejamento_PM_Estoque.py")

# === FOOTER ===
st.markdown("---")
st.markdown("*Desenvolvido para otimização de manutenção industrial baseada em análise de confiabilidade*")
