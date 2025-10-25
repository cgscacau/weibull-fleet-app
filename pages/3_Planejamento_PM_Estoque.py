import streamlit as st
import pandas as pd
import numpy as np
import math
from typing import Dict, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

from utils.state_manager import (
    initialize_session_state,
    display_pipeline_status, 
    validate_weibull_availability,
    get_available_components
)

# === INICIALIZAÇÃO ===
initialize_session_state()

st.set_page_config(
    page_title="Planejamento PM & Estoque",
    page_icon="🔧",
    layout="wide"
)

# === FUNÇÕES MATEMÁTICAS CORE ===

def weibull_reliability(t: float, lambda_param: float, rho_param: float) -> float:
    """
    Calcula a confiabilidade Weibull R(t) = exp(-(t/λ)^ρ)
    
    Args:
        t: Tempo
        lambda_param: Parâmetro de escala (λ)
        rho_param: Parâmetro de forma (ρ)
    
    Returns:
        Confiabilidade no tempo t
    """
    if t <= 0:
        return 1.0
    return math.exp(-((t / lambda_param) ** rho_param))

def weibull_pdf(t: float, lambda_param: float, rho_param: float) -> float:
    """
    Calcula a função densidade de probabilidade Weibull
    f(t) = (ρ/λ) * (t/λ)^(ρ-1) * exp(-(t/λ)^ρ)
    """
    if t <= 0:
        return 0.0
    
    scale_ratio = t / lambda_param
    return (rho_param / lambda_param) * (scale_ratio ** (rho_param - 1)) * math.exp(-(scale_ratio ** rho_param))

def calculate_mtbf_weibull(lambda_param: float, rho_param: float) -> float:
    """
    Calcula MTBF = λ * Γ(1 + 1/ρ) usando aproximação de Stirling
    """
    try:
        # Aproximação da função gama usando série de Lanczos (simplificada)
        def gamma_approx(z):
            if z == 1:
                return 1.0
            if z < 1:
                return gamma_approx(z + 1) / z
            
            # Aproximação de Stirling melhorada
            return math.sqrt(2 * math.pi / z) * ((z / math.e) ** z) * (1 + 1/(12*z))
        
        gamma_value = gamma_approx(1 + 1/rho_param)
        return lambda_param * gamma_value
    except:
        # Fallback para casos extremos
        return lambda_param

def expected_cycle_length_numerical(T: float, lambda_param: float, rho_param: float, n_points: int = 1000) -> float:
    """
    Calcula E[min(T, X)] numericamente usando integração trapezoidal
    E[min(T, X)] = ∫₀ᵀ R(t) dt
    """
    if T <= 0:
        return 0.0
    
    dt = T / n_points
    times = np.linspace(dt, T, n_points)
    reliabilities = [weibull_reliability(t, lambda_param, rho_param) for t in times]
    
    # Integração trapezoidal
    integral = dt * (0.5 * reliabilities[0] + sum(reliabilities[1:-1]) + 0.5 * reliabilities[-1])
    return integral

def age_replacement_optimization(lambda_param: float, rho_param: float, cost_pm: float, cost_cm: float, 
                                cost_downtime_pm: float = 0, cost_downtime_cm: float = 0) -> Dict[str, Any]:
    """
    Otimização da política de substituição por idade
    Minimiza: C(T) = [C_PM * R(T) + C_CM * (1-R(T))] / E[min(T,X)]
    """
    
    # Custos totais
    total_cost_pm = cost_pm + cost_downtime_pm
    total_cost_cm = cost_cm + cost_downtime_cm
    
    def cost_rate_function(T: float) -> float:
        """Taxa de custo por unidade de tempo"""
        if T <= 0:
            return float('inf')
        
        reliability = weibull_reliability(T, lambda_param, rho_param)
        expected_cycle = expected_cycle_length_numerical(T, lambda_param, rho_param)
        
        if expected_cycle <= 0:
            return float('inf')
        
        numerator = total_cost_pm * reliability + total_cost_cm * (1 - reliability)
        return numerator / expected_cycle
    
    # Busca do intervalo ótimo usando busca ternária
    mtbf = calculate_mtbf_weibull(lambda_param, rho_param)
    
    # Limites de busca baseados no MTBF
    left = 0.1 * mtbf
    right = 3.0 * mtbf
    
    # Busca ternária para encontrar o mínimo
    tolerance = 1.0  # Tolerância em horas
    
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

def calculate_maintenance_scenarios(lambda_param: float, rho_param: float, cost_pm: float, cost_cm: float,
                                  cost_downtime_pm: float = 0, cost_downtime_cm: float = 0,
                                  hours_per_year: float = 8760) -> pd.DataFrame:
    """
    Gera cenários de manutenção para diferentes intervalos
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
        reliability = weibull_reliability(interval, lambda_param, rho_param)
        expected_cycle = expected_cycle_length_numerical(interval, lambda_param, rho_param)
        
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
    
    return pd.DataFrame(scenarios)

def calculate_inventory_strategy(optimal_interval: float, lambda_param: float, rho_param: float,
                               lead_time_hours: float, service_level: float = 0.95,
                               unit_cost: float = 1000, holding_rate: float = 0.20,
                               ordering_cost: float = 100, hours_per_year: float = 8760) -> Dict[str, Any]:
    """
    Calcula parâmetros de gestão de estoque
    """
    
    # Demanda anual estimada
    reliability = weibull_reliability(optimal_interval, lambda_param, rho_param)
    expected_cycle = expected_cycle_length_numerical(optimal_interval, lambda_param, rho_param)
    
    cycles_per_year = hours_per_year / expected_cycle
    pm_per_year = reliability * cycles_per_year
    cm_per_year = (1 - reliability) * cycles_per_year
    
    # Assume 1 peça por manutenção
    annual_demand = pm_per_year + cm_per_year
    
    # Demanda durante lead time
    demand_rate_per_hour = annual_demand / hours_per_year
    mean_demand_lt = demand_rate_per_hour * lead_time_hours
    
    # Aproximação normal para o ponto de reposição
    # Z-score para o nível de serviço (aproximação)
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
    if holding_cost > 0:
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
        "annual_holding_cost": round(safety_stock * holding_cost, 2)
    }

# === INTERFACE PRINCIPAL ===

# Header
st.title("🔧 Planejamento PM & Estoque")
st.markdown("**Otimização de intervalos de manutenção preventiva e gestão de peças de reposição**")
st.markdown("---")

# Status do Pipeline
st.subheader("📊 Status do Pipeline")
display_pipeline_status()

# === VALIDAÇÃO DE PRÉ-REQUISITOS ===

# 1. Dataset carregado
if st.session_state.dataset is None or st.session_state.dataset.empty:
    st.error("❌ **Nenhum dataset carregado**")
    st.info("👈 **Próximo passo:** Vá para 'Dados UNIFIED' e carregue seus dados")
    
    if st.button("🔄 Ir para Dados UNIFIED", type="primary"):
        st.switch_page("pages/1_Dados_UNIFIED.py")
    
    st.stop()

# 2. Análise Weibull executada
is_weibull_valid, weibull_message = validate_weibull_availability()

if not is_weibull_valid:
    st.error(f"❌ **{weibull_message}**")
    st.info("👈 **Próximo passo:** Execute a análise Weibull primeiro")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📈 Ir para Análise Weibull", type="primary", use_container_width=True):
            st.switch_page("pages/2_Ajuste_Weibull_UNIFIED.py")
    
    st.stop()

# === DADOS VALIDADOS ===
available_components = get_available_components()
st.success(f"✅ **Dados Weibull disponíveis** para {len(available_components)} componentes")

# === SIDEBAR ===
with st.sidebar:
    st.header("🎯 Configurações")
    
    # Seleção de componente
    st.subheader("🔩 Componente")
    selected_component = st.selectbox(
        "Selecione o componente:",
        options=available_components,
        index=0,
        key="planning_component_selector"
    )
    
    # Seleção de frota
    st.subheader("🚛 Frota")
    if 'fleet' in st.session_state.dataset.columns:
        available_fleets = ["Todos"] + list(st.session_state.dataset['fleet'].unique())
        selected_fleet = st.selectbox(
            "Selecione a frota:",
            options=available_fleets,
            index=0,
            key="planning_fleet_selector"
        )
    else:
        selected_fleet = "Todos"
        st.info("Coluna 'fleet' não encontrada")
    
    st.session_state.selected_component = selected_component
    st.session_state.selected_fleet = selected_fleet
    
    st.markdown("---")
    
    # Parâmetros de custo
    st.subheader("💰 Custos")
    cost_pm = st.number_input("Custo MP ($):", min_value=0.0, value=1000.0, step=100.0)
    cost_cm = st.number_input("Custo MC ($):", min_value=0.0, value=5000.0, step=100.0)
    
    with st.expander("⏱️ Custos de Parada"):
        cost_downtime_pm = st.number_input("Parada MP ($/h):", min_value=0.0, value=0.0, step=10.0)
        cost_downtime_cm = st.number_input("Parada MC ($/h):", min_value=0.0, value=0.0, step=10.0)
    
    st.markdown("---")
    
    # Parâmetros de estoque
    st.subheader("📦 Estoque")
    lead_time_days = st.number_input("Lead Time (dias):", min_value=1, value=30, step=1)
    service_level = st.slider("Nível de Serviço:", min_value=0.80, max_value=0.99, value=0.95, step=0.01)
    
    with st.expander("💲 Custos de Estoque"):
        unit_cost = st.number_input("Custo unitário ($):", min_value=0.0, value=1000.0, step=100.0)
        holding_rate = st.slider("Taxa de posse (% ano):", min_value=0.05, max_value=0.50, value=0.20, step=0.01)
        ordering_cost = st.number_input("Custo de pedido ($):", min_value=0.0, value=100.0, step=10.0)
    
    st.markdown("---")
    st.subheader("📋 Seleção Atual")
    st.write(f"**Componente:** {selected_component}")
    st.write(f"**Frota:** {selected_fleet}")
    st.write(f"**Razão CM/MP:** {cost_cm/cost_pm:.1f}x")

# === VALIDAÇÃO DO COMPONENTE ===
is_comp_valid, comp_message = validate_weibull_availability(selected_component)
if not is_comp_valid:
    st.error(f"❌ {comp_message}")
    st.stop()

# === PARÂMETROS WEIBULL ===
weibull_params = st.session_state.weibull_results[selected_component]

if not weibull_params.get('success', False):
    st.error(f"❌ **Erro nos parâmetros Weibull:** {weibull_params.get('error', 'Erro desconhecido')}")
    st.stop()

lambda_param = weibull_params['lambda']
rho_param = weibull_params['rho']
mtbf = weibull_params.get('MTBF') or calculate_mtbf_weibull(lambda_param, rho_param)

# === SEÇÃO PRINCIPAL ===
st.subheader(f"📊 Análise: {selected_component} | Frota: {selected_fleet}")

# Parâmetros Weibull
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("λ (Escala)", f"{lambda_param:.2f}")

with col2:
    st.metric("ρ (Forma)", f"{rho_param:.2f}")

with col3:
    st.metric("MTBF", f"{mtbf:.0f}h")

with col4:
    st.metric("Observações", weibull_params['n_observations'])

with col5:
    if rho_param < 1:
        pattern = "🔽 Decrescente"
    elif rho_param == 1:
        pattern = "➡️ Constante"
    else:
        pattern = "📈 Crescente"
    st.metric("Taxa de Falha", pattern)

# === OTIMIZAÇÃO ===
st.markdown("---")
st.subheader("🎯 Otimização de Manutenção")

with st.spinner("🔄 Calculando intervalo ótimo..."):
    optimization_result = age_replacement_optimization(
        lambda_param, rho_param, cost_pm, cost_cm,
        cost_downtime_pm, cost_downtime_cm
    )

if optimization_result.get("success", False):
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
    
    st.success("✅ **Intervalo ótimo calculado!**")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🎯 Intervalo Ótimo", f"{optimal_interval:.0f}h")
    
    with col2:
        st.metric("💰 Taxa de Custo", f"${optimal_cost_rate:.2f}/h")
    
    with col3:
        st.metric("📊 Confiabilidade", f"{reliability_optimal:.1%}")
    
    with col4:
        annual_cost = optimal_cost_rate * 8760
        st.metric("📅 Custo Anual", f"${annual_cost:,.0f}")

else:
    st.error("❌ **Falha na otimização**")
    st.stop()

# === CENÁRIOS ===
st.markdown("---")
st.subheader("📊 Análise de Cenários")

with st.spinner("🔄 Gerando cenários..."):
    scenarios_df = calculate_maintenance_scenarios(
        lambda_param, rho_param, cost_pm, cost_cm,
        cost_downtime_pm, cost_downtime_cm
    )

st.session_state.scenarios_Todos_Todos_Motor = scenarios_df

st.dataframe(scenarios_df, use_container_width=True, hide_index=True)

# === GRÁFICO SIMPLES ===
st.markdown("---")
st.subheader("📈 Análise Visual")

# Prepara dados para gráfico
intervals_range = np.linspace(mtbf * 0.2, mtbf * 2, 50)
cost_rates = []

for interval in intervals_range:
    reliability = weibull_reliability(interval, lambda_param, rho_param)
    expected_cycle = expected_cycle_length_numerical(interval, lambda_param, rho_param)
    cost_rate = ((cost_pm + cost_downtime_pm) * reliability + (cost_cm + cost_downtime_cm) * (1 - reliability)) / expected_cycle
    cost_rates.append(cost_rate)

# Cria DataFrame para gráfico
chart_data = pd.DataFrame({
    'Intervalo (h)': intervals_range,
    'Taxa de Custo ($/h)': cost_rates
})

st.line_chart(chart_data.set_index('Intervalo (h)'), height=300)

# Marca ponto ótimo
st.info(f"🎯 **Ponto ótimo:** {optimal_interval:.0f}h com taxa de custo de ${optimal_cost_rate:.2f}/h")

# === GESTÃO DE ESTOQUE ===
st.markdown("---")
st.subheader("📦 Gestão de Estoque")

lead_time_hours = lead_time_days * 24

with st.spinner("🔄 Calculando parâmetros de estoque..."):
    inventory_params = calculate_inventory_strategy(
        optimal_interval, lambda_param, rho_param,
        lead_time_hours, service_level, unit_cost, holding_rate, ordering_cost
    )

st.session_state.inventory_strategy_Todos_Todos_Motor = inventory_params

st.success("✅ **Parâmetros de estoque calculados**")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📊 Demanda Anual", f"{inventory_params['annual_demand']:.1f} peças")

with col2:
    st.metric("🔄 Ponto de Reposição", f"{inventory_params['reorder_point']:.0f} peças")

with col3:
    st.metric("🛡️ Estoque de Segurança", f"{inventory_params['safety_stock']:.0f} peças")

with col4:
    st.metric("📦 Lote Econômico", f"{inventory_params['economic_order_quantity']:.0f} peças")

# Detalhes da demanda
with st.expander("🔍 **Detalhes da Estratégia de Estoque**"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Composição da Demanda:**")
        st.write(f"• MP: {inventory_params['pm_demand']:.2f} peças/ano")
        st.write(f"• MC: {inventory_params['cm_demand']:.2f} peças/ano")
        st.write(f"• Total: {inventory_params['annual_demand']:.2f} peças/ano")
        
    with col2:
        st.write("**Parâmetros de Controle:**")
        st.write(f"• Lead Time: {lead_time_days} dias")
        st.write(f"• Nível de Serviço: {service_level:.1%}")
        st.write(f"• Custo anual de posse: ${inventory_params['annual_holding_cost']:.2f}")

# === RESUMO EXECUTIVO ===
st.markdown("---")
st.subheader("📋 Resumo Executivo")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🎯 **Estratégia de Manutenção**")
    st.write(f"**Componente:** {selected_component}")
    st.write(f"**Política:** Substituição por idade")
    st.write(f"**Intervalo:** {optimal_interval:.0f} horas ({optimal_interval/24:.1f} dias)")
    st.write(f"**Confiabilidade:** {reliability_optimal:.1%}")
    st.write(f"**Custo anual:** ${optimal_cost_rate * 8760:,.0f}")

with col2:
    st.markdown("### 📦 **Estratégia de Estoque**")
    st.write(f"**Demanda anual:** {inventory_params['annual_demand']:.1f} peças")
    st.write(f"**Ponto de reposição:** {inventory_params['reorder_point']:.0f} peças")
    st.write(f"**Estoque de segurança:** {inventory_params['safety_stock']:.0f} peças")
    st.write(f"**Lote econômico:** {inventory_params['economic_order_quantity']:.0f} peças")
    st.write(f"**Custo de posse:** ${inventory_params['annual_holding_cost']:.2f}/ano")

# === EXPORTAÇÃO ===
st.markdown("---")
st.subheader("📤 Exportar Resultados")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📊 **Exportar Cenários**", use_container_width=True):
        csv = scenarios_df.to_csv(index=False)
        st.download_button(
            "💾 Download CSV",
            data=csv,
            file_name=f"cenarios_{selected_component}.csv",
            mime="text/csv"
        )

with col2:
    if st.button("📋 **Exportar Estratégias**", use_container_width=True):
        summary = {
            "maintenance_strategy": st.session_state.maintenance_strategy_Todos_Todos_Motor,
            "inventory_strategy": st.session_state.inventory_strategy_Todos_Todos_Motor,
            "scenarios": scenarios_df.to_dict('records')
        }
        
        import json
        json_str = json.dumps(summary, indent=2)
        st.download_button(
            "💾 Download JSON",
            data=json_str,
            file_name=f"estrategias_{selected_component}.json",
            mime="application/json"
        )

with col3:
    if st.button("🔄 **Nova Análise**", use_container_width=True):
        # Limpa resultados
        keys_to_clear = [
            'scenarios_Todos_Todos_Motor',
            'maintenance_strategy_Todos_Todos_Motor',
            'inventory_strategy_Todos_Todos_Motor'
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# === FOOTER ===
st.markdown("---")
st.markdown("*Análise baseada em distribuição Weibull e teoria de confiabilidade*")

# Informações técnicas
with st.expander("🔧 **Informações Técnicas**"):
    st.markdown("""
    **Metodologia Aplicada:**
    - **Distribuição Weibull:** Modelagem de tempos de falha com parâmetros λ (escala) e ρ (forma)
    - **Política de Manutenção:** Substituição por idade com otimização de custo
    - **Gestão de Estoque:** Modelo (s,S) com estoque de segurança baseado em nível de serviço
    - **Otimização:** Busca ternária para minimização da taxa de custo por hora
    
    **Fórmulas Principais:**
    - Confiabilidade: R(t) = exp(-(t/λ)^ρ)
    - MTBF: λ × Γ(1 + 1/ρ)
    - Taxa de Custo: [C_PM × R(T) + C_CM × (1-R(T))] / E[min(T,X)]
    - Ponto de Reposição: μ_LT + z_α × σ_LT
    
    **Limitações:**
    - Assume tempos de falha seguem distribuição Weibull
    - Custos considerados constantes
    - Lead time determinístico
    - Uma peça por manutenção
    """)
