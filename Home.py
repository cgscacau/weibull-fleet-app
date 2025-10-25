"""
Página principal do Weibull Fleet Analytics - VERSÃO FINAL SEGURA
Landing page visual sem dependências complexas
"""
import streamlit as st
from pathlib import Path

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
    /* Header principal */
    .main-header {
        font-size: 3.5rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin: 2rem 0;
    }
    
    /* Subtítulo */
    .subtitle {
        text-align: center;
        font-size: 1.3rem;
        color: #64748b;
        margin-bottom: 3rem;
    }
    
    /* Cards de features */
    .feature-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
    }
    
    .feature-card h3 {
        margin-top: 0;
        font-size: 1.5rem;
    }
    
    .feature-card ul {
        margin: 1rem 0;
        padding-left: 1.5rem;
    }
    
    .feature-card li {
        margin: 0.5rem 0;
        font-size: 1.05rem;
    }
    
    /* Step cards */
    .step-card {
        background: #f8fafc;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #3b82f6;
        margin: 1rem 0;
    }
    
    .step-number {
        display: inline-block;
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 50%;
        text-align: center;
        line-height: 40px;
        font-weight: bold;
        font-size: 1.2rem;
        margin-right: 1rem;
    }
    
    /* Benefit cards */
    .benefit-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #e2e8f0;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
    .benefit-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    
    .benefit-title {
        font-size: 1.2rem;
        font-weight: bold;
        color: #1e293b;
        margin-bottom: 0.5rem;
    }
    
    .benefit-desc {
        color: #64748b;
        font-size: 0.95rem;
    }
    
    /* Call to action button */
    .cta-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 2rem;
        border-radius: 50px;
        text-align: center;
        font-size: 1.2rem;
        font-weight: bold;
        margin: 2rem auto;
        display: block;
        width: fit-content;
        text-decoration: none;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    
    /* Stats */
    .stats-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }
    
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    
    .stat-label {
        font-size: 1rem;
        opacity: 0.9;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header principal
    st.markdown('<h1 class="main-header">⚙️ Weibull Fleet Analytics</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="subtitle">
        Sistema Inteligente de Análise de Confiabilidade com IA para Gestão de Frotas Industriais
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar com quick start
    with st.sidebar:
        st.markdown("## 🚀 Quick Start")
        st.markdown("""
        ### Fluxo Recomendado:
        
        **1. 📊 Dados UNIFIED**
        Upload CSV/Excel com seus dados
        
        **2. 🧼 Qualidade dos Dados**  
        Verificação e limpeza automática
        
        **3. 📈 Ajuste Weibull UNIFIED**
        Análise de confiabilidade completa
        
        **4. 🛠️ Planejamento PM Estoque**
        Otimização de manutenção
        """)
        
        st.markdown("---")
        st.markdown("## 💡 Dica")
        st.info("Use o menu lateral acima para navegar entre as páginas do sistema!")
        
        st.markdown("---")
        st.markdown("## 📋 Formatos Aceitos")
        st.success("""
        **Colunas do CSV:**
        - `asset_id` ou `component_id`
        - `component` ou `component_type`
        - `operating_hours` ou `failure_time`
        - `censored` (opcional)
        """)
    
    # Seção de benefícios
    st.markdown("## 🎯 Por Que Usar Este Sistema?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="benefit-card">
            <div class="benefit-icon">📊</div>
            <div class="benefit-title">Análise Precisa</div>
            <div class="benefit-desc">
                Ajuste Weibull com MLE e tratamento de censura para análise estatística rigorosa
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="benefit-card">
            <div class="benefit-icon">🤖</div>
            <div class="benefit-title">IA Assistiva</div>
            <div class="benefit-desc">
                Limpeza automática de dados e explicações em linguagem simples
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="benefit-card">
            <div class="benefit-icon">⚡</div>
            <div class="benefit-title">Resultados Rápidos</div>
            <div class="benefit-desc">
                Interface intuitiva para análises complexas em minutos, não dias
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Seção de funcionalidades principais
    st.markdown("---")
    st.markdown("## 🚀 Funcionalidades Principais")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>📈 Análise Weibull</h3>
            <ul>
                <li>Ajuste por MLE com censura</li>
                <li>Gráficos de probabilidade</li>
                <li>Intervalos de confiança</li>
                <li>Comparação de modelos</li>
                <li>Interpretação automática</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>🧼 Qualidade de Dados</h3>
            <ul>
                <li>Validação automática</li>
                <li>Detecção de outliers</li>
                <li>Normalização de nomes</li>
                <li>Tratamento de faltantes</li>
                <li>Relatórios de qualidade</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>🛠️ Planejamento PM</h3>
            <ul>
                <li>Intervalos ótimos de PM</li>
                <li>Gestão de estoque</li>
                <li>Análise de cenários</li>
                <li>Otimização de custos</li>
                <li>Relatórios executivos</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Seção de como começar
    st.markdown("---")
    st.markdown("## 🎓 Como Começar")
    
    st.markdown("""
    <div class="step-card">
        <span class="step-number">1</span>
        <strong>Prepare seus dados</strong><br>
        Organize um CSV/Excel com colunas: asset_id, component, operating_hours
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="step-card">
        <span class="step-number">2</span>
        <strong>Faça upload na página "Dados UNIFIED"</strong><br>
        O sistema detecta automaticamente o formato e padroniza os dados
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="step-card">
        <span class="step-number">3</span>
        <strong>Navegue para "Ajuste Weibull UNIFIED"</strong><br>
        Selecione o componente e execute a análise de confiabilidade
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="step-card">
        <span class="step-number">4</span>
        <strong>Obtenha insights e recomendações</strong><br>
        Visualize gráficos, parâmetros e recomendações de manutenção
    </div>
    """, unsafe_allow_html=True)
    
    # Call to action
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; margin: 3rem 0;">
        <h2>Pronto para começar?</h2>
        <p style="font-size: 1.1rem; color: #64748b; margin-bottom: 2rem;">
            Comece sua análise agora usando o menu lateral →
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Estatísticas (exemplo)
    st.markdown("## 📊 Capacidades do Sistema")
    
    st.markdown("""
    <div class="stats-container">
        <div class="stat-card">
            <div class="stat-number">∞</div>
            <div class="stat-label">Registros Suportados</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">10+</div>
            <div class="stat-label">Formatos de Colunas</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">100%</div>
            <div class="stat-label">Automático</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">⚡</div>
            <div class="stat-label">Análise Rápida</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Seção de suporte
    st.markdown("---")
    st.markdown("## ❓ Precisa de Ajuda?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.expander("📥 Formatos de Dados Aceitos"):
            st.markdown("""
            **O sistema aceita múltiplos nomes para cada coluna:**
            
            **ID do Equipamento:**
            - `asset_id`, `component_id`, `equipment_id`, `id`
            
            **Tipo de Componente:**
            - `component`, `component_type`, `tipo`, `equipment_type`
            
            **Tempo de Operação:**
            - `operating_hours`, `failure_time`, `hours`, `horas`
            
            **Censura (opcional):**
            - `censored`, `censurado`, `suspended`
            - Se não fornecido, será inferido automaticamente
            
            **Formatos de Arquivo:**
            - CSV (.csv)
            - Excel (.xlsx, .xls)
            """)
    
    with col2:
        with st.expander("🔍 Sobre Análise Weibull"):
            st.markdown("""
            **O que é Análise Weibull?**
            
            Método estatístico para analisar confiabilidade de componentes.
            
            **Parâmetros Principais:**
            - **β (Beta/Forma):** Indica tipo de falha
              - β < 1: Falhas infantis
              - β ≈ 1: Falhas aleatórias
              - β > 1: Falhas por desgaste
            
            - **η (Eta/Escala):** Vida característica
              - 63.2% dos componentes falham até esse tempo
            
            **Benefícios:**
            - Planejamento preciso de manutenção
            - Otimização de estoque de peças
            - Redução de custos operacionais
            """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #64748b; padding: 2rem 0;">
        <p style="font-size: 1.1rem; margin-bottom: 0.5rem;">
            <strong>Weibull Fleet Analytics</strong>
        </p>
        <p style="font-size: 0.9rem;">
            Sistema de análise de confiabilidade com IA para gestão inteligente de manutenção industrial
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
