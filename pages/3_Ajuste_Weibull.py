"""
Página de planejamento de manutenção
"""
import streamlit as st
import numpy as np
import sys
from pathlib import Path

# Adicionar raiz ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from core.planner import MaintenancePlanner
except ImportError:
    st.error("❌ Erro ao importar módulo de planejamento")
    st.stop()

st.set_page_config(
    page_title="Planejamento PM",
    page_icon="🛠️",
    layout="wide"
)

st.title("🛠️ Planejamento de Manutenção")

# Verificar se há resultados Weibull
if 'weibull_results' not in st.session_state or not st.session_state.weibull_results:
    st.warning("📈 Execute a análise Weibull primeiro na página 'Analise Weibull'")
    st.stop()

# Selecionar componente
components = list(st.session_state.weibull_results.keys())
selected_component = st.sidebar.selectbox("Componente", components)

results = st.session_state.weibull_results[selected_component]['results']

st.markdown(f"""
### 🔧 Componente Selecionado: {selected_component}

**Parâmetros Weibull:**
- β (forma): {results['beta']:.2f}
- η (escala): {results['eta']:.0f}h
- MTBF: {results['mtbf']:.0f}h
""")

# Configurações
st.sidebar.markdown("## ⚙️ Configurações")

# Política de manutenção
policy = st.sidebar.selectbox(
    "Política de Manutenção",
    ["reliability_target", "fraction_of_eta"],
    format_func=lambda x: {
        "reliability_target": "Meta de Confiabilidade",
        "fraction_of_eta": "Fração da Vida Característica"
    }[x]
)

if policy == "reliability_target":
    target_reliability = st.sidebar.slider("Confiabilidade Alvo", 0.5, 0.95, 0.8, 0.05)
else:
    fraction_of_eta = st.sidebar.slider("Fração de η", 0.3, 0.9, 0.75, 0.05)

# Custos
st.sidebar.markdown("### 💰 Custos")
cost_failure = st.sidebar.number_input("Custo de Falha (R$)", 1000, 100000, 10000, 1000)
cost_pm = st.sidebar.number_input("Custo de PM (R$)", 100, 10000, 1000, 100)

# Calcular estratégia
if st.button("🎯 Calcular Estratégia Ótima", type="primary"):
    with st.spinner("Calculando..."):
        try:
            planner = MaintenancePlanner(results['beta'], results['eta'], selected_component)
            
            if policy == "reliability_target":
                strategy = planner.optimal_pm_interval(
                    policy="reliability_target",
                    target_reliability=target_reliability,
                    cost_failure=cost_failure,
                    cost_pm=cost_pm
                )
            else:
                strategy = planner.optimal_pm_interval(
                    policy="fraction_of_eta",
                    fraction_of_eta=fraction_of_eta,
                    cost_failure=cost_failure,
                    cost_pm=cost_pm
                )
            
            # Salvar estratégia
            if 'maintenance_strategies' not in st.session_state:
                st.session_state.maintenance_strategies = {}
            
            st.session_state.maintenance_strategies[selected_component] = strategy
            
            st.success("✅ Estratégia calculada!")
            
            # Mostrar resultados
            st.markdown("---")
            st.markdown("## 📋 Estratégia Recomendada")
            
            # Determinar cor do risco
            risk_colors = {
                "Baixo": "🟢",
                "Médio": "🟡",
                "Alto": "🔴"
            }
            risk_icon = risk_colors.get(strategy.risk_level, "⚪")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Intervalo Recomendado",
                    f"{strategy.recommended_interval:.0f} horas"
                )
            
            with col2:
                st.metric(
                    "Confiabilidade",
                    f"{strategy.reliability_at_interval:.1%}"
                )
            
            with col3:
                st.metric(
                    f"{risk_icon} Nível de Risco",
                    strategy.risk_level
                )
            
            # Informações adicionais
            st.markdown("### 📊 Análise de Impacto")
            
            annual_pm_freq = 8760 / strategy.recommended_interval
            annual_pm_cost = annual_pm_freq * cost_pm
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.info(f"""
                **Frequência Anual**
                
                {annual_pm_freq:.1f} PM por ano
                
                (Aproximadamente a cada {strategy.recommended_interval/24:.0f} dias)
                """)
            
            with col2:
                st.info(f"""
                **Custo Anual de PM**
                
                R$ {annual_pm_cost:,.0f}
                
                ({annual_pm_freq:.1f} PM × R$ {cost_pm:,})
                """)
            
            with col3:
                downtime_hours = annual_pm_freq * 4  # Assumir 4h por PM
                st.info(f"""
                **Parada Anual Estimada**
                
                {downtime_hours:.0f} horas
                
                (Assumindo 4h por PM)
                """)
            
            # Recomendações
            st.markdown("### 💡 Recomendações")
            
            if strategy.risk_level == "Baixo":
                st.success("""
                ✅ **Estratégia Conservadora**
                
                - Alta confiabilidade mantida
                - Risco de falha minimizado
                - Pode ser otimizada para reduzir custos
                """)
            elif strategy.risk_level == "Médio":
                st.warning("""
                ⚠️ **Estratégia Balanceada**
                
                - Bom equilíbrio entre custo e confiabilidade
                - Monitorar performance
                - Considerar manutenção preditiva
                """)
            else:
                st.error("""
                🔴 **Estratégia Agressiva**
                
                - Risco elevado de falha
                - Reduzir intervalo recomendado
                - Implementar monitoramento contínuo
                """)
        
        except Exception as e:
            st.error(f"❌ Erro no cálculo: {e}")
            import traceback
            st.code(traceback.format_exc())

# Mostrar estratégia salva
if 'maintenance_strategies' in st.session_state and selected_component in st.session_state.maintenance_strategies:
    st.markdown("---")
    st.info("💾 Estratégia anterior disponível para este componente")
