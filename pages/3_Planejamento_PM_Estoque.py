import streamlit as st

st.set_page_config(
    page_title="Planejamento PM & Estoque",
    page_icon="🔧",
    layout="wide"
)

import pandas as pd
import numpy as np
import math
from typing import Dict, Any, Optional, Tuple
import warnings
import sys
from pathlib import Path

warnings.filterwarnings('ignore')

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from utils.state_manager import (
    initialize_session_state,
    display_pipeline_status, 
    validate_weibull_availability,
    get_available_components
)

from utils.navigation import (
    handle_navigation,
    create_navigation_button
)

# === PROCESSA NAVEGAÇÃO ===
handle_navigation()

# === INICIALIZAÇÃO ===
initialize_session_state()


# === FUNÇÕES MATEMÁTICAS CORE ===

def weibull_reliability(t: float, lambda_param: float, rho_param: float) -> float:
    """
    Calcula a confiabilidade Weibull: R(t) = exp(-(t/λ)^ρ)
    
    Args:
        t: Tempo
        lambda_param: Parâmetro de escala (λ)
        rho_param: Parâmetro de forma (ρ)
    
    Returns:
        Confiabilidade no tempo t (entre 0 e 1)
    """
    if t <= 0:
        return 1.0
    try:
        return math.exp(-((t / lambda_param) ** rho_param))
    except:
        return 0.0

def weibull_pdf(t: float, lambda_param: float, rho_param: float) -> float:
    """
    Calcula a função densidade de probabilidade Weibull.
    f(t) = (ρ/λ) × (t/λ)^(ρ-1) × exp(-(t/λ)^ρ)
    """
    if t <= 0:
        return 0.0
    
    try:
        scale_ratio = t / lambda_param
        return (rho_param / lambda_param) * (scale_ratio ** (rho_param - 1)) * \
               math.exp(-(scale_ratio ** rho_param))
    except:
        return 0.0

def calculate_mtbf_weibull(lambda_param: float, rho_param: float) -> float:
    """
    Calcula MTBF = λ × Γ(1 + 1/ρ) usando aproximação numérica.
    """
    try:
        def gamma_approx(z):
            """Aproximação da função gama usando série de Lanczos simplificada."""
            if z == 1:
                return 1.0
            if z < 1:
                return gamma_approx(z + 1) / z
            
            # Aproximação de Stirling melhorada
            return math.sqrt(2 * math.pi / z) * ((z / math.e) ** z) * (1 + 1/(12*z))
        
        gamma_value = gamma_approx(1 + 1/rho_param)
        return lambda_param * gamma_value
    except:
        return lambda_param

def expected_cycle_length_numerical(T: float, lambda_param: float, rho_param: float, 
                                   n_points: int = 1000) -> float:
    """
    Calcula E[min(T, X)] numericamente usando integração trapezoidal.
    E[min(T, X)] = ∫₀ᵀ R(t) dt
    """
    if T <= 0:
        return 0.0
    
    try:
        dt = T / n_points
        times = np.linspace(dt, T, n_points)
        reliabilities = [weibull_reliability(t, lambda_param, rho_param) for t in times]
        
        # Integração trapezoidal
        integral = dt * (0.5 * reliabilities[0] + sum(reliabilities[1:-1]) + 0.5 * reliabilities[-1])
        return integral
    except:
        return T * 0.5  # Fallback

def age_replacement_optimization(lambda_param: float, rho_param: float, 
                                cost_pm: float, cost_cm: float, 
                                cost_downtime_pm: float = 0, 
                                cost_downtime_cm: float = 0) -> Dict[str, Any]:
    """
    Otimização da política de substituição por idade.
    Minimiza: C(T) = [C_PM × R(T) + C_CM × (1-R(T))] / E[min(T,X)]
    """
    
    # Custos totais
    total_cost_pm = cost_pm + cost_downtime_pm
    total_cost_cm = cost_cm + cost_downtime_cm
    
    def cost_rate_function(T: float) -> float:
        """Taxa de custo por unidade de tempo."""
        if T <= 0:
            return float('inf')
        
        try:
            reliability = weibull_reliability(T, lambda_param, rho_param)
            expected_cycle = expected_cycle_length_numerical(T, lambda_param, rho_param)
            
            if expected_cycle <= 0:
                return float('inf')
            
            numerator = total_cost_pm * reliability + total_cost_cm * (1 - reliability)
            return numerator / expected_cycle
        except:
            return float('inf')
    
    # Busca do intervalo ótimo usando busca ternária
    mtbf = calculate_mtbf_weibull(lambda_param, rho_param)
    
    # Limites de busca baseados no MTBF
    left = 0.1 * mtbf
    right = 3.0 * mtbf
    
    # Busca ternária para encontrar o mínimo
    tolerance = 1.0
    
    try:
        while (right - left) > tolerance:
            mid1 = left + (right - left) / 3
            mid2 = right - (right - left) / 3
            
            if cost_rate_function(mid1) > cost_rate_function(mid2):
                left = mid1
            else:
                right = mid2
        
        optimal_interval = (left + right) / 2
        optimal_cost_rate = cost_rate_function(optimal_interval)
        reliability_optimal = weibull_reliability(optimal_interval, lambda_param, rho_param)
        
        return {
            "optimal_interval": optimal_interval,
            "optimal_cost_rate": optimal_cost_rate,
            "reliability_at_optimal": reliability_optimal,
            "mtbf": mtbf,
            "success": True
        }
    except Exception as e:
        return {
            "error": str(e),
            "success": False
        }

def calculate_maintenance_scenarios(lambda_param: float, rho_param: float, 
                                  cost_pm: float, cost_cm: float,
                                  cost_downtime_pm: float = 0, 
                                  cost_downtime_cm: float = 0,
                                  hours_per_year: float = 8760) -> pd.DataFrame:
    """
    Gera cenários de manutenção para diferentes intervalos.
    """
    mtbf = calculate_mtbf_weibull(lambda_param, rho_param)
    
    # Define intervalos baseados no MTBF
    intervals = np.array([
        0.3 * mtbf,  # Muito conservador
        0.5 * mtbf,  # Conservador  
        0.7 * mtbf,  # Moderado
        1.0 * mtbf,  # MTBF
        1.2 * mtbf,  # Moderado-agressivo
        1.5 * mtbf   # Agressivo
    ])
    
    scenarios = []
    total_cost_pm = cost_pm + cost_downtime_pm
    total_cost_cm = cost_cm + cost_downtime_cm
    
    for interval in intervals:
        try:
            reliability = weibull_reliability(interval, lambda_param, rho_param)
            expected_cycle = expected_cycle_length_numerical(interval, lambda_param, rho_param)
            
            if expected_cycle <= 0:
                continue
            
            # Taxa de custo
            cost_rate = (total_cost_pm * reliability + total_cost_cm * (1 - reliability)) / expected_cycle
            
            # Frequências anuais
            cycles_per_year = hours_per_year / expected_cycle
            pm_per_year = reliability * cycles_per_year
            cm_per_year = (1 - reliability) * cycles_per_year
            
            # Custos anuais
            cost_pm_annual = pm_per_year * cost_pm
            cost_cm_annual = cm_per_year * cost_cm
            cost_total_annual = cost_pm_annual + cost_cm_annual
            
            # Classificação de risco
            failure_prob = 1 - reliability
            if failure_prob <= 0.05:
                risk_level = "🟢 Muito Baixo"
            elif failure_prob <= 0.10:
                risk_level = "🟡 Baixo"
            elif failure_prob <= 0.20:
                risk_level = "🟠 Médio"
            elif failure_prob <= 0.30:
                risk_level = "🔴 Alto"
            else:
                risk_level = "⚫ Muito Alto"
            
            scenarios.append({
                "Intervalo (h)": round(interval, 0),
                "Confiabilidade": round(reliability, 3),
                "Taxa de Custo ($/h)": round(cost_rate, 2),
                "PM por ano": round(pm_per_year, 2),
                "CM por ano": round(cm_per_year, 2),
                "CustoPM/ano": round(cost_pm_annual, 0),
                "CustoCM/ano": round(cost_cm_annual, 0),
                "Custo Total/ano": round(cost_total_annual, 0),
                "Nível de Risco": risk_level
            })
        except:
            continue
    
    return pd.DataFrame(scenarios)

def calculate_inventory_strategy(optimal_interval: float, lambda_param: float, rho_param: float,
                               lead_time_hours: float, service_level: float = 0.95,
                               unit_cost: float = 1000, holding_rate: float = 0.20,
                               ordering_cost: float = 100, 
                               hours_per_year: float = 8760) -> Dict[str, Any]:
    """
    Calcula parâmetros de gestão de estoque baseado na estratégia de manutenção.
    """
    
    try:
        # Demanda anual estimada
        reliability = weibull_reliability(optimal_interval, lambda_param, rho_param)
        expected_cycle = expected_cycle_length_numerical(optimal_interval, lambda_param, rho_param)
        
        if expected_cycle <= 0:
            return {"error": "Ciclo esperado inválido", "success": False}
        
        cycles_per_year = hours_per_year / expected_cycle
        pm_per_year = reliability * cycles_per_year
        cm_per_year = (1 - reliability) * cycles_per_year
        
        # Assume 1 peça por manutenção
        annual_demand = pm_per_year + cm_per_year
        
        # Demanda durante lead time
        demand_rate_per_hour = annual_demand / hours_per_year
        mean_demand_lt = demand_rate_per_hour * lead_time_hours
        
        # Z-score para o nível de serviço
        if service_level >= 0.99:
            z_score = 2.33
        elif service_level >= 0.95:
            z_score = 1.65
        elif service_level >= 0.90:
            z_score = 1.28
        else:
            z_score = 0.84
        
        # Desvio padrão (aproximação Poisson)
        std_demand_lt = math.sqrt(mean_demand_lt)
        
        # Estoque de segurança
        safety_stock = z_score * std_demand_lt
        
        # Ponto de reposição
        reorder_point = mean_demand_lt + safety_stock
        
        # EOQ (Lote Econômico)
        holding_cost = unit_cost * holding_rate
        if holding_cost > 0 and annual_demand > 0:
            eoq = math.sqrt(2 * annual_demand * ordering_cost / holding_cost)
        else:
            eoq = 1.0
        
        return {
            "annual_demand": round(annual_demand, 2),
            "pm_demand": round(pm_per_year, 2),
            "cm_demand": round(cm_per_year, 2),
            "lead_time_hours": lead_time_hours,
            "mean_demand_lead_time": round(mean_demand_lt, 2),
            "safety_stock": max(1, round(safety_stock, 0)),
            "reorder_point": max(1, round(reorder_point, 0)),
            "economic_order_quantity": max(1, round(eoq, 0)),
            "service_level": service_level,
            "unit_cost": unit_cost,
            "annual_holding_cost": round(safety_stock * holding_cost, 2),
            "success": True
        }
    except Exception as e:
        return {
            "error": str(e),
            "success": False
        }

# === INTERFACE PRINCIPAL ===

# Header
st.title("🔧 Planejamento PM & Estoque")
st.markdown("**Otimização de intervalos de manutenção preventiva e gestão de peças de reposição**")
st.markdown("---")

# Status do Pipeline
st.subheader("📊 Status do Pipeline de Otimização")
display_pipeline_status()

st.markdown("---")

# === VALIDAÇÃO DE PRÉ-REQUISITOS ===

# 1. Dataset carregado
if st.session_state.dataset is None or st.session_state.dataset.empty:
    st.error("❌ **Dataset não carregado**")
    
    st.markdown("""
    ### 📋 **Pré-requisitos não atendidos**
    
    Para executar o planejamento, você precisa:
    
    1. **Carregar dados** na página "Dados UNIFIED"
    2. **Executar análise Weibull** na página "Ajuste Weibull UNIFIED"
    """)
    
    st.info("👈 **Próximo passo:** Use a barra lateral para navegar até 'Dados UNIFIED'")
    
    if st.button("🔄 **Ir para Dados UNIFIED**", type="primary"):
        try:
            st.switch_page("pages/1_Dados_UNIFIED.py")
        except:
            st.info("👈 Use o menu lateral para navegar")
    
    st.stop()

# 2. Análise Weibull executada
is_weibull_valid, weibull_message = validate_weibull_availability()

if not is_weibull_valid:
    st.error(f"❌ **{weibull_message}**")
    
    st.markdown("""
    ### 📋 **Análise Weibull Pendente**
    
    Para prosseguir com o planejamento, você precisa:
    
    1. **Executar a análise Weibull** na página correspondente
    2. **Garantir** que pelo menos um componente foi analisado com sucesso
    """)
    
    st.info("👈 **Próximo passo:** Execute a análise Weibull primeiro")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📈 **Ir para Análise Weibull**", type="primary", use_container_width=True):
            try:
                st.switch_page("pages/2_Ajuste_Weibull_UNIFIED.py")
            except:
                st.info("👈 Use o menu lateral para navegar")
    
    # Debug info
    with st.expander("🔍 **Informações de Debug**"):
        st.write("**Dados disponíveis no Session State:**")
        
        debug_items = [
            ("dataset", "Carregado" if st.session_state.get("dataset") is not None else "Ausente"),
            ("weibull_results", f"{len(st.session_state.get('weibull_results', {}))} componentes"),
            ("data_quality_report", "Disponível" if st.session_state.get("data_quality_report") else "Ausente"),
        ]
        
        for key, value in debug_items:
            st.write(f"• **{key}:** {value}")
        
        if st.session_state.get("weibull_results"):
            st.write("\n**Componentes com análise Weibull:**")
            for comp in st.session_state.weibull_results.keys():
                result = st.session_state.weibull_results[comp]
                status = "✅ Sucesso" if result.get("success", False) else "❌ Falha"
                st.write(f"  • {comp}: {status}")
    
    st.stop()

# === DADOS VALIDADOS ===
available_components = get_available_components()
st.success(f"✅ **Dados Weibull disponíveis** para {len(available_components)} componentes")

# === SIDEBAR - CONFIGURAÇÕES ===
with st.sidebar:
    st.header("🎯 Configurações de Otimização")
    
    st.markdown("---")
    
    # === SELEÇÃO DE COMPONENTE ===
    st.subheader("🔩 Componente")
    selected_component = st.selectbox(
        "Selecione o componente:",
        options=available_components,
        index=0,
        key="planning_component_selector",
        help="Escolha o componente para análise detalhada"
    )
    
    # === SELEÇÃO DE FROTA ===
    st.subheader("🚛 Frota")
    if 'fleet' in st.session_state.dataset.columns:
        available_fleets = ["Todos"] + list(st.session_state.dataset['fleet'].unique())
        selected_fleet = st.selectbox(
            "Selecione a frota:",
            options=available_fleets,
            index=0,
            key="planning_fleet_selector",
            help="Filtre por frota específica ou analise todas"
        )
    else:
        selected_fleet = "Todos"
        st.info("Coluna 'fleet' não encontrada nos dados")
    
    # Atualiza session state
    st.session_state.selected_component = selected_component
    st.session_state.selected_fleet = selected_fleet
    
    st.markdown("---")
    
    # === PARÂMETROS DE CUSTO ===
    st.subheader("💰 Custos de Manutenção")
    
    cost_pm = st.number_input(
        "Custo de Manutenção Preventiva ($):",
        min_value=0.0,
        value=1000.0,
        step=100.0,
        help="Custo para realizar uma MP planejada"
    )
    
    cost_cm = st.number_input(
        "Custo de Manutenção Corretiva ($):",
        min_value=0.0,
        value=5000.0,
        step=100.0,
        help="Custo para realizar uma MC não planejada"
    )
    
    # Razão de custos
    cost_ratio = cost_cm / cost_pm if cost_pm > 0 else 0
    st.metric("Razão CM/MP", f"{cost_ratio:.1f}x", help="Quantas vezes a MC é mais cara que a MP")
    
    with st.expander("⏱️ Custos de Parada"):
        cost_downtime_pm = st.number_input(
            "Custo de parada para MP ($/h):",
            min_value=0.0,
            value=0.0,
            step=10.0,
            help="Custo por hora de parada durante MP"
        )
        
        cost_downtime_cm = st.number_input(
            "Custo de parada para MC ($/h):",
            min_value=0.0,
            value=0.0,
            step=10.0,
            help="Custo por hora de parada durante MC"
        )
    
    st.markdown("---")
    
    # === PARÂMETROS DE ESTOQUE ===
    st.subheader("📦 Parâmetros de Estoque")
    
    lead_time_days = st.number_input(
        "Lead Time (dias):",
        min_value=1,
        value=30,
        step=1,
        help="Tempo entre pedido e recebimento da peça"
    )
    
    service_level = st.slider(
        "Nível de Serviço:",
        min_value=0.80,
        max_value=0.99,
        value=0.95,
        step=0.01,
        format="%.0f%%",
        help="Probabilidade de não faltar estoque"
    )
    
    with st.expander("💲 Custos de Estoque"):
        unit_cost = st.number_input(
            "Custo unitário da peça ($):",
            min_value=0.0,
            value=1000.0,
            step=100.0,
            help="Preço de compra de uma unidade"
        )
        
        holding_rate = st.slider(
            "Taxa de posse anual:",
            min_value=0.05,
            max_value=0.50,
            value=0.20,
            step=0.01,
            format="%.0f%%",
            help="Percentual do custo da peça para mantê-la em estoque por ano"
        )
        
        ordering_cost = st.number_input(
            "Custo de pedido ($):",
            min_value=0.0,
            value=100.0,
            step=10.0,
            help="Custo fixo para fazer um pedido"
        )
    
    st.markdown("---")
    
    # === RESUMO DA SELEÇÃO ===
    st.subheader("📋 Resumo da Seleção")
    st.write(f"**Componente:** {selected_component}")
    st.write(f"**Frota:** {selected_fleet}")
    st.write(f"**Razão CM/MP:** {cost_ratio:.1f}x")
    st.write(f"**Lead Time:** {lead_time_days} dias")
    st.write(f"**Nível de Serviço:** {service_level:.0%}")

# === VALIDAÇÃO DO COMPONENTE SELECIONADO ===
is_comp_valid, comp_message = validate_weibull_availability(selected_component)
if not is_comp_valid:
    st.error(f"❌ {comp_message}")
    st.stop()

# === PARÂMETROS WEIBULL DO COMPONENTE ===
weibull_params = st.session_state.weibull_results[selected_component]

if not weibull_params.get('success', False):
    st.error(f"❌ **Erro nos parâmetros Weibull:** {weibull_params.get('error', 'Erro desconhecido')}")
    st.stop()

lambda_param = weibull_params['lambda']
rho_param = weibull_params['rho']
mtbf = weibull_params.get('MTBF') or calculate_mtbf_weibull(lambda_param, rho_param)

# === EXIBIÇÃO DOS PARÂMETROS ===
st.subheader(f"📊 Análise: {selected_component} | Frota: {selected_fleet}")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "λ (Escala)", 
        f"{lambda_param:.2f}",
        help="Parâmetro de escala da distribuição Weibull"
    )

with col2:
    st.metric(
        "ρ (Forma)", 
        f"{rho_param:.2f}",
        help="Parâmetro de forma da distribuição Weibull"
    )

with col3:
    st.metric(
        "MTBF", 
        f"{mtbf:.0f}h",
        help="Tempo Médio Entre Falhas"
    )

with col4:
    st.metric(
        "Observações", 
        weibull_params['n_observations'],
        help="Número de observações usadas no ajuste"
    )

with col5:
    if rho_param < 1:
        pattern = "🔽 Decrescente"
        pattern_help = "Mortalidade infantil - falhas precoces"
    elif rho_param <= 1.1:
        pattern = "➡️ Constante"
        pattern_help = "Taxa de falha constante - falhas aleatórias"
    else:
        pattern = "📈 Crescente"
        pattern_help = "Desgaste - falhas por envelhecimento"
    
    st.metric(
        "Taxa de Falha", 
        pattern,
        help=pattern_help
    )

# === OTIMIZAÇÃO DE MANUTENÇÃO ===
st.markdown("---")
st.subheader("🎯 Otimização de Intervalo de Manutenção")

with st.spinner("🔄 Calculando intervalo ótimo..."):
    optimization_result = age_replacement_optimization(
        lambda_param, rho_param, cost_pm, cost_cm,
        cost_downtime_pm, cost_downtime_cm
    )

if not optimization_result.get("success", False):
    st.error(f"❌ **Falha na otimização:** {optimization_result.get('error', 'Erro desconhecido')}")
    st.stop()

optimal_interval = optimization_result["optimal_interval"]
optimal_cost_rate = optimization_result["optimal_cost_rate"]
reliability_optimal = optimization_result["reliability_at_optimal"]

# Salva no session state
st.session_state.maintenance_strategy_Todos_Todos_Motor = {
    "policy": "Substituição por idade otimizada",
    "component": selected_component,
    "intervalo_h": optimal_interval,
    "cost_rate": optimal_cost_rate,
    "reliability": reliability_optimal,
    "mtbf": mtbf
}

st.success("✅ **Intervalo ótimo calculado com sucesso!**")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "🎯 Intervalo Ótimo",
        f"{optimal_interval:.0f}h",
        delta=f"{optimal_interval/24:.1f} dias",
        help="Intervalo que minimiza o custo total"
    )

with col2:
    st.metric(
        "💰 Taxa de Custo",
        f"${optimal_cost_rate:.2f}/h",
        help="Custo por hora de operação"
    )

with col3:
    st.metric(
        "📊 Confiabilidade",
        f"{reliability_optimal:.1%}",
        help="Probabilidade de não falhar até o intervalo ótimo"
    )

with col4:
    annual_cost = optimal_cost_rate * 8760
    st.metric(
        "📅 Custo Anual",
        f"${annual_cost:,.0f}",
        help="Custo estimado por ano (8760h)"
    )

# Comparação com MTBF
st.info(f"""
📊 **Análise Comparativa:**
- Intervalo ótimo é **{(optimal_interval/mtbf):.1%}** do MTBF
- Realizar manutenção a cada **{optimal_interval:.0f} horas** ({optimal_interval/24:.1f} dias)
- Probabilidade de falha antes da MP: **{(1-reliability_optimal):.1%}**
""")

# === ANÁLISE DE CENÁRIOS ===
st.markdown("---")
st.subheader("📊 Análise de Cenários Alternativos")

with st.spinner("🔄 Gerando cenários..."):
    scenarios_df = calculate_maintenance_scenarios(
        lambda_param, rho_param, cost_pm, cost_cm,
        cost_downtime_pm, cost_downtime_cm
    )

if scenarios_df.empty:
    st.error("❌ Falha ao gerar cenários")
else:
    st.session_state.scenarios_Todos_Todos_Motor = scenarios_df
    
    st.dataframe(
        scenarios_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Destaca o melhor cenário
    best_scenario_idx = scenarios_df["Taxa de Custo ($/h)"].idxmin()
    best_interval = scenarios_df.loc[best_scenario_idx, "Intervalo (h)"]
    
    st.success(f"✨ **Melhor cenário:** Intervalo de {best_interval:.0f}h")

# === GRÁFICO DE ANÁLISE ===
st.markdown("---")
st.subheader("📈 Análise Visual: Custo vs Intervalo")

# Prepara dados para gráfico
intervals_range = np.linspace(mtbf * 0.2, mtbf * 2, 50)
cost_rates = []

for interval in intervals_range:
    reliability = weibull_reliability(interval, lambda_param, rho_param)
    expected_cycle = expected_cycle_length_numerical(interval, lambda_param, rho_param)
    
    if expected_cycle > 0:
        cost_rate = ((cost_pm + cost_downtime_pm) * reliability + 
                    (cost_cm + cost_downtime_cm) * (1 - reliability)) / expected_cycle
        cost_rates.append(cost_rate)
    else:
        cost_rates.append(None)

# Cria DataFrame para gráfico
chart_data = pd.DataFrame({
    'Intervalo (h)': intervals_range,
    'Taxa de Custo ($/h)': cost_rates
})

st.line_chart(chart_data.set_index('Intervalo (h)'), height=400)

# Marca ponto ótimo
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.info(f"🎯 **Ponto ótimo:** {optimal_interval:.0f}h com taxa de ${optimal_cost_rate:.2f}/h")

# === GESTÃO DE ESTOQUE ===
st.markdown("---")
st.subheader("📦 Estratégia de Gestão de Estoque")

lead_time_hours = lead_time_days * 24

with st.spinner("🔄 Calculando parâmetros de estoque..."):
    inventory_params = calculate_inventory_strategy(
        optimal_interval, lambda_param, rho_param,
        lead_time_hours, service_level, unit_cost, holding_rate, ordering_cost
    )

if not inventory_params.get("success", False):
    st.error(f"❌ **Falha no cálculo de estoque:** {inventory_params.get('error', 'Erro desconhecido')}")
else:
    st.session_state.inventory_strategy_Todos_Todos_Motor = inventory_params
    
    st.success("✅ **Parâmetros de estoque calculados com sucesso!**")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📊 Demanda Anual",
            f"{inventory_params['annual_demand']:.1f}",
            delta="peças/ano",
            help="Quantidade estimada de peças necessárias por ano"
        )
    
    with col2:
        st.metric(
            "🔄 Ponto de Reposição",
            f"{inventory_params['reorder_point']:.0f}",
            delta="peças",
            help="Quando o estoque atingir este nível, faça um novo pedido"
        )
    
    with col3:
        st.metric(
            "🛡️ Estoque de Segurança",
            f"{inventory_params['safety_stock']:.0f}",
            delta="peças",
            help="Quantidade mínima para proteger contra variações"
        )
    
    with col4:
        st.metric(
            "📦 Lote Econômico",
            f"{inventory_params['economic_order_quantity']:.0f}",
            delta="peças",
            help="Quantidade ideal a pedir em cada pedido"
        )
    
    # Detalhes expandidos
    with st.expander("🔍 **Detalhes da Estratégia de Estoque**"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Composição da Demanda")
            st.write(f"• **Manutenção Preventiva:** {inventory_params['pm_demand']:.2f} peças/ano")
            st.write(f"• **Manutenção Corretiva:** {inventory_params['cm_demand']:.2f} peças/ano")
            st.write(f"• **Demanda Total:** {inventory_params['annual_demand']:.2f} peças/ano")
            
            st.markdown("#### 💰 Custos de Estoque")
            st.write(f"• **Custo unitário:** ${inventory_params['unit_cost']:.2f}")
            st.write(f"• **Taxa de posse:** {holding_rate:.1%}/ano")
            st.write(f"• **Custo anual de posse:** ${inventory_params['annual_holding_cost']:.2f}")
        
        with col2:
            st.markdown("#### 🎯 Parâmetros de Controle")
            st.write(f"• **Lead Time:** {lead_time_days} dias ({lead_time_hours:.0f} horas)")
            st.write(f"• **Nível de Serviço:** {inventory_params['service_level']:.1%}")
            st.write(f"• **Demanda no Lead Time:** {inventory_params['mean_demand_lead_time']:.2f} peças")
            
            st.markdown("#### 📋 Política Recomendada")
            st.write(f"• **Quando estoque ≤ {inventory_params['reorder_point']:.0f}:** Fazer pedido")
            st.write(f"• **Quantidade a pedir:** {inventory_params['economic_order_quantity']:.0f} peças")
            st.write(f"• **Manter sempre:** {inventory_params['safety_stock']:.0f} peças de segurança")

# === RESUMO EXECUTIVO ===
st.markdown("---")
st.subheader("📋 Resumo Executivo")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🎯 **Estratégia de Manutenção Recomendada**")
    st.markdown(f"""
    **Componente Analisado:** {selected_component}  
    **Política:** Substituição por idade (Age Replacement)  
    **Intervalo Ótimo:** {optimal_interval:.0f} horas ({optimal_interval/24:.1f} dias)  
    **Confiabilidade no Intervalo:** {reliability_optimal:.1%}  
    **Taxa de Custo:** ${optimal_cost_rate:.2f}/hora  
    **Custo Anual Estimado:** ${optimal_cost_rate * 8760:,.0f}
    
    **Interpretação:**  
    Realizar manutenção preventiva a cada **{optimal_interval:.0f} horas** minimiza 
    o custo total considerando tanto custos de MP quanto de MC.
    """)

with col2:
    st.markdown("### 📦 **Estratégia de Estoque Recomendada**")
    
    if inventory_params.get("success"):
        st.markdown(f"""
        **Demanda Anual Estimada:** {inventory_params['annual_demand']:.1f} peças  
        **Ponto de Reposição:** {inventory_params['reorder_point']:.0f} peças  
        **Estoque de Segurança:** {inventory_params['safety_stock']:.0f} peças  
        **Lote Econômico de Compra:** {inventory_params['economic_order_quantity']:.0f} peças  
        **Nível de Serviço:** {inventory_params['service_level']:.0%}  
        **Custo Anual de Posse:** ${inventory_params['annual_holding_cost']:.2f}
        
        **Interpretação:**  
        Quando o estoque atingir **{inventory_params['reorder_point']:.0f} peças**, 
        faça um pedido de **{inventory_params['economic_order_quantity']:.0f} peças**. 
        Mantenha sempre pelo menos **{inventory_params['safety_stock']:.0f} peças** 
        como estoque de segurança.
        """)

# === EXPORTAÇÃO DE RESULTADOS ===
st.markdown("---")
st.subheader("📤 Exportar Resultados")

col1, col2, col3 = st.columns(3)

with col1:
    if not scenarios_df.empty:
        csv_scenarios = scenarios_df.to_csv(index=False)
        st.download_button(
            "📊 **Baixar Cenários (CSV)**",
            data=csv_scenarios,
            file_name=f"cenarios_{selected_component}_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

with col2:
    if st.button("📋 **Exportar Estratégias (JSON)**", use_container_width=True):
        import json
        
        summary = {
            "component": selected_component,
            "fleet": selected_fleet,
            "analysis_date": pd.Timestamp.now().isoformat(),
            "weibull_parameters": {
                "lambda": lambda_param,
                "rho": rho_param,
                "mtbf": mtbf
            },
            "maintenance_strategy": st.session_state.maintenance_strategy_Todos_Todos_Motor,
            "inventory_strategy": st.session_state.inventory_strategy_Todos_Todos_Motor,
            "scenarios": scenarios_df.to_dict('records') if not scenarios_df.empty else []
        }
        
        json_str = json.dumps(summary, indent=2)
        st.download_button(
            "💾 **Download JSON**",
            data=json_str,
            file_name=f"estrategias_{selected_component}_{pd.Timestamp.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )

with col3:
    if st.button("🔄 **Nova Análise**", use_container_width=True):
        # Limpa apenas os resultados, mantém configurações
        keys_to_clear = [
            'scenarios_Todos_Todos_Motor',
            'maintenance_strategy_Todos_Todos_Motor',
            'inventory_strategy_Todos_Todos_Motor'
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# === INFORMAÇÕES TÉCNICAS ===
st.markdown("---")
with st.expander("🔧 **Metodologia e Informações Técnicas**"):
    st.markdown("""
    ### 📚 **Metodologia Aplicada**
    
    #### **1. Distribuição Weibull**
    A análise de confiabilidade utiliza a distribuição Weibull de dois parâmetros:
    - **λ (lambda)**: Parâmetro de escala - caracteriza a vida característica
    - **ρ (rho)**: Parâmetro de forma - caracteriza o tipo de falha
    
    **Função de Confiabilidade:**  

    $$R(t) = \exp\left(-\left(\frac{t}{\lambda}\right)^\rho\right)$$
    
    **MTBF (Mean Time Between Failures):**  

    $$MTBF = \lambda \times \Gamma\left(1 + \frac{1}{\rho}\right)$$
    
    #### **2. Otimização de Manutenção Preventiva**
    Utiliza a política de **Substituição por Idade (Age Replacement)**:
    
    **Função Objetivo (minimizar):**  

    $$C(T) = \frac{C_{PM} \times R(T) + C_{CM} \times [1-R(T)]}{E[\min(T,X)]}$$
    
    Onde:
    - $$C_{PM}$$: Custo de manutenção preventiva
    - $$C_{CM}$$: Custo de manutenção corretiva
    - $$R(T)$$: Confiabilidade no intervalo T
    - $$E[\min(T,X)]$$: Duração esperada do ciclo
    
    **Método de Otimização:** Busca ternária
    
    #### **3. Gestão de Estoque**
    Modelo **(s, S)** com estoque de segurança:
    
    **Ponto de Reposição:**  

    $$s = \mu_{LT} + z_\alpha \times \sigma_{LT}$$
    
    **Lote Econômico (EOQ):**  

    $$Q^* = \sqrt{\frac{2 \times D \times S}{H}}$$
    
    Onde:
    - $$\mu_{LT}$$: Demanda média durante lead time
    - $$z_\alpha$$: Z-score para nível de serviço α
    - $$\sigma_{LT}$$: Desvio padrão da demanda no lead time
    - $$D$$: Demanda anual
    - $$S$$: Custo de pedido
    - $$H$$: Custo de posse unitário
    
    ### ⚠️ **Premissas e Limitações**
    
    1. **Tempos de falha** seguem distribuição Weibull
    2. **Custos** são considerados constantes ao longo do tempo
    3. **Lead time** é determinístico
    4. **Uma peça por manutenção** (proporção 1:1)
    5. **Demanda independente** entre períodos
    6. **Sistema de reposição contínua**
    
    ### 📖 **Referências**
    
    - Barlow & Proschan (1965) - Mathematical Theory of Reliability
    - Nakagawa (2005) - Maintenance Theory of Reliability
    - Silver, Pyke & Peterson (1998) - Inventory Management
    """)

# === FOOTER ===
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p><em>Otimização baseada em análise de confiabilidade Weibull e teoria de gestão de operações</em></p>
    <p><small>Desenvolvido para suporte à decisão em manutenção industrial</small></p>
</div>
""", unsafe_allow_html=True)

# === DEBUG (OPCIONAL) ===
if st.sidebar.checkbox("🐛 **Modo Debug**"):
    st.markdown("---")
    st.subheader("🔍 Informações de Debug")
    
    debug_tabs = st.tabs(["📊 Parâmetros", "🔧 Otimização", "📦 Estoque", "💾 Session"])
    
    with debug_tabs[0]:
        st.write("**Parâmetros Weibull:**")
        st.json({
            "lambda": lambda_param,
            "rho": rho_param,
            "mtbf": mtbf,
            "n_observations": weibull_params['n_observations']
        })
    
    with debug_tabs[1]:
        st.write("**Resultado da Otimização:**")
        st.json(optimization_result)
    
    with debug_tabs[2]:
        st.write("**Parâmetros de Estoque:**")
        st.json(inventory_params)
    
    with debug_tabs[3]:
        st.write("**Session State Keys:**")
        st.write(list(st.session_state.keys()))
