import streamlit as st

# === CONFIGURAÇÃO - PRIMEIRA LINHA ===
st.set_page_config(
    page_title="Planejamento PM & Estoque",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === IMPORTS ===
import sys
from pathlib import Path

root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from utils.state_manager import initialize_session_state, display_pipeline_status
from utils.navigation import (
    handle_navigation, 
    create_navigation_button, 
    create_page_navigation_links,
    check_streamlit_version
)

# === PROCESSA NAVEGAÇÃO PENDENTE ===
handle_navigation()

# === INICIALIZAÇÃO ===
initialize_session_state()

# === HEADER ===
st.title("🔧 Planejamento PM & Estoque")
st.markdown("**Sistema integrado de otimização de manutenção preventiva e gestão de peças de reposição**")

# === VERIFICAÇÃO DE COMPATIBILIDADE ===
with st.expander("🔧 **Verificar Compatibilidade do Sistema**"):
    check_streamlit_version()

# === DESCRIÇÃO ===
st.markdown("""
Este sistema utiliza análise de confiabilidade baseada na distribuição Weibull para otimizar:

- 📊 **Intervalos de manutenção preventiva** - Determine quando realizar manutenções
- 📦 **Gestão de inventário de peças** - Calcule estoques de segurança e pontos de reposição
- 💰 **Custos de manutenção** - Minimize custos totais (preventiva + corretiva)
- ⚠️ **Análise de riscos** - Avalie probabilidades de falha e níveis de risco
""")

# === STATUS DO PIPELINE ===
st.markdown("---")
st.subheader("📊 Status do Sistema")
display_pipeline_status()

# === GUIA DE USO ===
st.markdown("---")
st.subheader("🚀 Guia de Uso do Sistema")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 1️⃣ **Carregar Dados**
    
    📤 **Carregue seus dados de falha**
    
    **Formato CSV esperado:**
    - `component_type`: Tipo do componente
    - `failure_time`: Tempo até falha (horas)
    - `censored`: Dados censurados (0 ou 1)
    - `fleet`: Frota (opcional)
    
    **Requisitos:**
    - Mínimo 3 observações por componente
    - Tempos de falha > 0
    - Formato de dados limpo
    """)

with col2:
    st.markdown("""
    ### 2️⃣ **Análise Weibull**
    
    📈 **Execute a análise de confiabilidade**
    
    **O sistema irá:**
    - Validar qualidade dos dados
    - Ajustar parâmetros Weibull (λ, ρ)
    - Calcular MTBF por componente
    - Gerar relatórios detalhados
    - Classificar padrões de falha
    
    **Resultado:**
    - Parâmetros de confiabilidade
    - Estatísticas de ajuste
    """)

with col3:
    st.markdown("""
    ### 3️⃣ **Otimização**
    
    🎯 **Otimize suas estratégias**
    
    **Funcionalidades:**
    - Cálculo de intervalos ótimos
    - Análise de cenários alternativos
    - Gestão de estoque inteligente
    - Avaliação de custos e riscos
    
    **Entregáveis:**
    - Plano de manutenção otimizado
    - Política de estoque recomendada
    - Relatórios exportáveis
    """)

# === NAVEGAÇÃO RÁPIDA ===
st.markdown("---")
st.subheader("🧭 Acesso Rápido às Páginas")

st.info("💡 **Dica:** Clique nos botões abaixo ou use a **barra lateral** (☰) para navegar entre as páginas.")

col1, col2, col3 = st.columns(3)

with col1:
    create_navigation_button(
        "pages/1_Dados_UNIFIED.py",
        "📤 **Carregar Dados**",
        button_type="secondary",
        key="home_nav_dados"
    )
    st.caption("Carregue e valide seus dados de falha")

with col2:
    create_navigation_button(
        "pages/2_Ajuste_Weibull_UNIFIED.py", 
        "📈 **Análise Weibull**",
        button_type="secondary",
        key="home_nav_weibull"
    )
    st.caption("Execute a análise de confiabilidade")

with col3:
    create_navigation_button(
        "pages/3_Planejamento_PM_Estoque.py",
        "🔧 **Planejamento PM**", 
        button_type="secondary",
        key="home_nav_planning"
    )
    st.caption("Otimize manutenção e estoque")

# === FALLBACK DE NAVEGAÇÃO ===
create_page_navigation_links()

# === INFORMAÇÕES TÉCNICAS ===
st.markdown("---")
with st.expander("🔧 **Informações Técnicas Detalhadas**"):
    st.markdown("""
    ### 📚 **Fundamentos Teóricos**
    
    #### **Distribuição Weibull**
    A distribuição Weibull é amplamente utilizada em análise de confiabilidade devido à sua flexibilidade 
    em modelar diferentes padrões de falha através de seus dois parâmetros:
    
    - **λ (lambda)** - Parâmetro de escala: Representa a vida característica do componente
    - **ρ (rho)** - Parâmetro de forma: Caracteriza o tipo de falha
      - ρ < 1: Mortalidade infantil (falhas precoces)
      - ρ = 1: Taxa de falha constante (falhas aleatórias)
      - ρ > 1: Desgaste (falhas por envelhecimento)
    
    #### **Metodologia de Otimização**
    
    **Política de Substituição por Idade:**
    - Minimiza o custo total por unidade de tempo
    - Considera custos de manutenção preventiva e corretiva
    - Incorpora custos de parada (downtime)
    - Utiliza busca ternária para encontrar o intervalo ótimo
    
    **Gestão de Estoque:**
    - Modelo (s, S) com estoque de segurança
    - Cálculo de ponto de reposição baseado em nível de serviço
    - Lote econômico (EOQ) para otimizar custos de pedido
    - Considera lead time e variabilidade da demanda
    
    ### 🛠️ **Bibliotecas Utilizadas**
    
    - **streamlit** >= 1.29.0: Interface web interativa
    - **pandas**: Manipulação e análise de dados
    - **numpy**: Computação numérica
    - **lifelines**: Análise de sobrevivência e ajuste Weibull
    
    ### 📊 **Requisitos de Dados**
    
    **Qualidade Mínima:**
    - Pelo menos 3 observações por componente
    - Tempos de falha estritamente positivos
    - Indicadores de censura válidos (0 ou 1)
    - Dados sem valores nulos nas colunas críticas
    
    **Formato Recomendado:**
    ```
    component_type,failure_time,censored,fleet
    Motor A,1200,1,Frota 1
    Motor A,1450,1,Frota 1
    Motor A,1100,0,Frota 1
    ```
    
    ### 🔬 **Validação e Testes**
    
    O sistema realiza múltiplas validações:
    - Verificação de formato e tipos de dados
    - Análise de qualidade estatística
    - Validação de parâmetros Weibull
    - Testes de convergência na otimização
    
    ### 📖 **Referências Bibliográficas**
    
    - Barlow & Proschan (1965) - *Mathematical Theory of Reliability*
    - Nakagawa (2005) - *Maintenance Theory of Reliability*  
    - Abernethy (2006) - *The New Weibull Handbook*
    - Silver, Pyke & Peterson (1998) - *Inventory Management and Production Planning*
    """)

# === EXEMPLOS E CASOS DE USO ===
st.markdown("---")
with st.expander("💡 **Exemplos de Aplicação**"):
    st.markdown("""
    ### 🏭 **Casos de Uso Típicos**
    
    #### **1. Manutenção de Frotas**
    - **Cenário:** Empresa com 50 caminhões
    - **Objetivo:** Otimizar substituição de componentes críticos
    - **Benefícios:** Redução de 30% em custos de manutenção corretiva
    
    #### **2. Indústria de Manufatura**
    - **Cenário:** Linha de produção com múltiplas máquinas
    - **Objetivo:** Minimizar paradas não planejadas
    - **Benefícios:** Aumento de 15% na disponibilidade operacional
    
    #### **3. Gestão de Peças de Reposição**
    - **Cenário:** Almoxarifado com 200+ SKUs
    - **Objetivo:** Otimizar níveis de estoque
    - **Benefícios:** Redução de 40% em capital imobilizado
    
    ### 📊 **Exemplo Numérico**
    
    **Dados de Entrada:**
    - Componente: Rolamento de motor
    - MTBF: 8.000 horas
    - Custo MP: $500
    - Custo MC: $3.000
    
    **Resultados Típicos:**
    - Intervalo ótimo: 6.400 horas (~9 meses)
    - Confiabilidade: 85%
    - Economia anual: $12.000 por equipamento
    - Estoque de segurança: 3 peças
    """)

# === SUPORTE E AJUDA ===
st.markdown("---")
with st.expander("❓ **Perguntas Frequentes (FAQ)**"):
    st.markdown("""
    ### ❓ **Dúvidas Comuns**
    
    **P: Quantos dados preciso para análise?**  
    R: Mínimo de 3 observações por componente, mas recomendamos 10+ para resultados robustos.
    
    **P: O que fazer se a análise Weibull falhar?**  
    R: Verifique a qualidade dos dados, remova outliers e garanta que há eventos observados (não censurados).
    
    **P: Como interpretar o parâmetro ρ (rho)?**  
    R: 
    - ρ < 1: Componente tem falhas precoces (defeitos de fabricação)
    - ρ ≈ 1: Falhas aleatórias (componente maduro)
    - ρ > 1: Falhas por desgaste (envelhecimento)
    
    **P: Posso usar dados censurados?**  
    R: Sim! O método Weibull suporta censura à direita (observações que não falharam).
    
    **P: Como exportar os resultados?**  
    R: Na página de Planejamento PM, use os botões de exportação para CSV ou JSON.
    
    **P: O sistema funciona offline?**  
    R: Sim, após instalação local com `pip install -r requirements.txt`.
    """)

# === FOOTER ===
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p style='font-size: 14px;'><em>Sistema de Otimização de Manutenção Preventiva e Gestão de Estoque</em></p>
    <p style='font-size: 12px;'>Baseado em análise de confiabilidade Weibull e teoria de gestão de operações</p>
    <p style='font-size: 11px; margin-top: 10px;'>
        Desenvolvido para suporte à decisão em manutenção industrial | 
        Versão 2.0 | 
        © 2024
    </p>
</div>
""", unsafe_allow_html=True)

# === DEBUG INFO (OPCIONAL) ===
if st.sidebar.checkbox("🐛 Modo Debug", value=False):
    st.markdown("---")
    st.subheader("🔍 Informações de Debug")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Session State:**")
        st.json({
            "dataset_loaded": st.session_state.get("dataset") is not None,
            "weibull_results": len(st.session_state.get("weibull_results", {})),
            "pipeline_status": st.session_state.get("pipeline_status", {}),
            "navigation_state": {
                "navigate_to": st.session_state.get("navigate_to"),
                "triggered": st.session_state.get("navigation_triggered", False)
            }
        })
    
    with col2:
        st.write("**System Info:**")
        st.write(f"- Streamlit: {st.__version__}")
        st.write(f"- Python: {sys.version.split()[0]}")
        st.write(f"- Root dir: {root_dir}")
