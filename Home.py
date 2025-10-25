import streamlit as st
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
root_path = Path(__file__).parent
sys.path.insert(0, str(root_path))

# Configuração da página
st.set_page_config(
    page_title="Weibull Fleet Analytics",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    /* Estilo geral */
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    .subtitle {
        font-size: 1.3rem;
        color: #666;
        text-align: center;
        margin-bottom: 3rem;
    }
    
    /* Cards de funcionalidades */
    .feature-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        border-left: 5px solid;
        margin-bottom: 1.5rem;
        height: 100%;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 12px rgba(0,0,0,0.15);
    }
    
    .feature-card.blue {
        border-left-color: #667eea;
    }
    
    .feature-card.purple {
        border-left-color: #764ba2;
    }
    
    .feature-card.orange {
        border-left-color: #f093fb;
    }
    
    .feature-card.red {
        border-left-color: #f5576c;
    }
    
    .feature-card.green {
        border-left-color: #4facfe;
    }
    
    .feature-card.yellow {
        border-left-color: #43e97b;
    }
    
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        display: block;
    }
    
    .feature-title {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
        color: #333;
    }
    
    .feature-description {
        color: #666;
        line-height: 1.6;
        margin-bottom: 1rem;
    }
    
    .feature-list {
        list-style: none;
        padding: 0;
    }
    
    .feature-list li {
        padding: 0.3rem 0;
        color: #555;
    }
    
    .feature-list li:before {
        content: "✓ ";
        color: #43e97b;
        font-weight: bold;
        margin-right: 0.5rem;
    }
    
    /* Seção de benefícios */
    .benefit-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2.5rem;
        border-radius: 15px;
        margin: 2rem 0;
        text-align: center;
    }
    
    .benefit-title {
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    
    .benefit-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1.5rem;
        margin-top: 2rem;
    }
    
    .benefit-item {
        background: rgba(255,255,255,0.2);
        padding: 1.5rem;
        border-radius: 10px;
        backdrop-filter: blur(10px);
    }
    
    .benefit-number {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    
    .benefit-text {
        font-size: 1rem;
        opacity: 0.95;
    }
    
    /* Seção CTA */
    .cta-box {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 3rem;
        border-radius: 15px;
        text-align: center;
        margin: 3rem 0;
    }
    
    .cta-title {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    
    .cta-subtitle {
        font-size: 1.3rem;
        opacity: 0.95;
        margin-bottom: 2rem;
    }
    
    /* Botões */
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.8rem 2rem;
        font-size: 1.1rem;
        font-weight: bold;
        border-radius: 10px;
        cursor: pointer;
        transition: transform 0.2s ease;
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
    }
    
    /* Remover padding extra */
    .block-container {
        padding-top: 3rem;
        padding-bottom: 3rem;
    }
    
    /* Esconder menu e footer padrão */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Responsividade */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2rem;
        }
        .subtitle {
            font-size: 1rem;
        }
        .benefit-grid {
            grid-template-columns: 1fr;
        }
    }
</style>
""", unsafe_allow_html=True)

# Header principal
st.markdown('<div class="main-header">⚙️ Weibull Fleet Analytics</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Sistema Avançado de Análise de Confiabilidade com IA Assistida para Gestão de Frotas Industriais</div>', unsafe_allow_html=True)

# Seção de benefícios
st.markdown("""
<div class="benefit-box">
    <div class="benefit-title">🎯 Resultados Comprovados</div>
    <div class="benefit-grid">
        <div class="benefit-item">
            <div class="benefit-number">30-50%</div>
            <div class="benefit-text">Redução em paradas não planejadas</div>
        </div>
        <div class="benefit-item">
            <div class="benefit-number">20-40%</div>
            <div class="benefit-text">Economia em custos de manutenção</div>
        </div>
        <div class="benefit-item">
            <div class="benefit-number">25-35%</div>
            <div class="benefit-text">Otimização de estoque de peças</div>
        </div>
        <div class="benefit-item">
            <div class="benefit-number">15-25%</div>
            <div class="benefit-text">Aumento de disponibilidade</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Funcionalidades principais
st.markdown("## 🚀 Funcionalidades Principais")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-card blue">
        <span class="feature-icon">📊</span>
        <div class="feature-title">Análise Weibull Avançada</div>
        <div class="feature-description">
        Modelagem estatística de ponta para análise de confiabilidade
        </div>
        <ul class="feature-list">
            <li>Estimação MLE com censura</li>
            <li>8 tipos de gráficos interativos</li>
            <li>Intervalos de confiança 95%</li>
            <li>Testes de aderência</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card purple">
        <span class="feature-icon">🤖</span>
        <div class="feature-title">IA Assistiva</div>
        <div class="feature-description">
        Inteligência artificial para otimização e insights
        </div>
        <ul class="feature-list">
            <li>Limpeza automática de dados</li>
            <li>Explicações em linguagem natural</li>
            <li>Sugestões de melhorias</li>
            <li>Relatórios executivos automáticos</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card orange">
        <span class="feature-icon">🛠️</span>
        <div class="feature-title">Planejamento PM</div>
        <div class="feature-description">
        Otimização de manutenção preventiva baseada em dados
        </div>
        <ul class="feature-list">
            <li>3 políticas de manutenção</li>
            <li>Análise de custo-benefício</li>
            <li>Intervalos ótimos de PM</li>
            <li>Simulações de cenários</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

col4, col5, col6 = st.columns(3)

with col4:
    st.markdown("""
    <div class="feature-card red">
        <span class="feature-icon">📦</span>
        <div class="feature-title">Gestão de Estoque</div>
        <div class="feature-description">
        Dimensionamento inteligente de peças sobressalentes
        </div>
        <ul class="feature-list">
            <li>Cálculo de EOQ otimizado</li>
            <li>Safety stock dinâmico</li>
            <li>Ponto de reposição automático</li>
            <li>Análise de custos de estoque</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown("""
    <div class="feature-card green">
        <span class="feature-icon">📈</span>
        <div class="feature-title">Comparativos</div>
        <div class="feature-description">
        Benchmarking e análise comparativa de componentes
        </div>
        <ul class="feature-list">
            <li>Comparação entre equipamentos</li>
            <li>Análise de frota completa</li>
            <li>Identificação de outliers</li>
            <li>Tendências de confiabilidade</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col6:
    st.markdown("""
    <div class="feature-card yellow">
        <span class="feature-icon">📑</span>
        <div class="feature-title">Relatórios IA</div>
        <div class="feature-description">
        Relatórios executivos gerados automaticamente
        </div>
        <ul class="feature-list">
            <li>Sumário executivo automático</li>
            <li>Insights acionáveis</li>
            <li>Recomendações personalizadas</li>
            <li>Exportação para Excel/PDF</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# Seção "Como Funciona"
st.markdown("---")
st.markdown("## 🔄 Como Funciona")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <div style="font-size: 3rem; margin-bottom: 1rem;">📁</div>
        <div style="font-size: 1.3rem; font-weight: bold; margin-bottom: 0.5rem;">1. Upload de Dados</div>
        <div style="color: #666;">
            Carregue seu histórico de falhas em CSV ou Excel. Suporte para múltiplas fontes de dados.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
        <div style="font-size: 1.3rem; font-weight: bold; margin-bottom: 0.5rem;">2. Análise Automática</div>
        <div style="color: #666;">
            Sistema calcula parâmetros Weibull, gera gráficos e valida resultados estatisticamente.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <div style="font-size: 3rem; margin-bottom: 1rem;">🎯</div>
        <div style="font-size: 1.3rem; font-weight: bold; margin-bottom: 0.5rem;">3. Decisões Ótimas</div>
        <div style="color: #666;">
            Receba recomendações de intervalos PM, dimensionamento de estoque e ROI esperado.
        </div>
    </div>
    """, unsafe_allow_html=True)

# CTA - Call to Action
st.markdown("""
<div class="cta-box">
    <div class="cta-title">🚀 Pronto para Começar?</div>
    <div class="cta-subtitle">
        Siga o fluxo recomendado abaixo ou acesse qualquer página diretamente pelo menu lateral
    </div>
</div>
""", unsafe_allow_html=True)

# Fluxo recomendado com botões
st.markdown("### 📍 Fluxo Recomendado")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📚 1. Como Usar", use_container_width=True):
        st.switch_page("pages/0_Como_Usar.py")
    st.caption("📖 Tutorial completo + templates para download")

with col2:
    if st.button("📁 2. Carregar Dados", use_container_width=True):
        st.switch_page("pages/1_Dados.py")
    st.caption("📥 Upload CSV/Excel ou use dados de exemplo")

with col3:
    if st.button("🧼 3. Qualidade", use_container_width=True):
        st.switch_page("pages/2_Qualidade.py")
    st.caption("🔍 Limpeza e validação assistida por IA")

col4, col5, col6 = st.columns(3)

with col4:
    if st.button("📈 4. Análise Weibull", use_container_width=True):
        st.switch_page("pages/3_Weibull.py")
    st.caption("📊 Ajuste de parâmetros e gráficos")

with col5:
    if st.button("🛠️ 5. Planejamento PM", use_container_width=True):
        st.switch_page("pages/4_Planejamento.py")
    st.caption("⚙️ Intervalos ótimos e gestão de estoque")

with col6:
    if st.button("📊 6. Relatórios", use_container_width=True):
        st.switch_page("pages/6_Relatorio_IA.py")
    st.caption("📑 Relatórios executivos automáticos")

# Seção de aplicações
st.markdown("---")
st.markdown("## 🏭 Aplicações Industriais")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **🚗 Frotas de Veículos**
    - Caminhões e ônibus comerciais
    - Tratores agrícolas
    - Equipamentos de construção
    - Veículos de logística
    
    **⚙️ Manufatura**
    - Linhas de produção
    - Robôs industriais
    - Prensas e injetoras
    - Sistemas de movimentação
    
    **⛏️ Mineração**
    - Equipamentos pesados
    - Correias transportadoras
    - Britadores e peneiras
    - Sistemas hidráulicos
    """)

with col2:
    st.markdown("""
    **🛢️ Oil & Gas**
    - Compressores
    - Turbinas a gás
    - Bombas de processo
    - Trocadores de calor
    
    **⚡ Energia**
    - Geradores elétricos
    - Transformadores
    - Turbinas eólicas
    - Sistemas HVAC
    
    **🏗️ Infraestrutura**
    - Elevadores e escadas rolantes
    - Sistemas de ar condicionado
    - Motores e acionamentos
    - Equipamentos de segurança
    """)

# Tecnologias utilizadas
st.markdown("---")
st.markdown("## 🔧 Tecnologias e Metodologias")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    **📊 Estatística**
    - Distribuição Weibull
    - Maximum Likelihood Estimation
    - Análise de censura
    - Testes de aderência
    """)

with col2:
    st.markdown("""
    **🤖 IA / ML**
    - Processamento de linguagem natural
    - Detecção de anomalias
    - Sistemas de recomendação
    - AutoML para otimização
    """)

with col3:
    st.markdown("""
    **💻 Desenvolvimento**
    - Python / Streamlit
    - Pandas / NumPy
    - SciPy / Plotly
    - Pydantic validation
    """)

with col4:
    st.markdown("""
    **📚 Referências**
    - ISO 14224 (Petroleum)
    - MIL-HDBK-217 (Military)
    - RCM (Reliability-Centered)
    - SAE International
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p style='font-size: 1.2rem; margin-bottom: 1rem;'>
        <strong>Weibull Fleet Analytics</strong> | Sistema Profissional de Análise de Confiabilidade
    </p>
    <p style='font-size: 0.9rem; color: #999;'>
        Desenvolvido com ❤️ usando Python + Streamlit + IA | Versão 1.0.0
    </p>
    <p style='font-size: 0.85rem; color: #aaa; margin-top: 1rem;'>
        © 2024 | Otimização de Manutenção Industrial Baseada em Dados
    </p>
</div>
""", unsafe_allow_html=True)
