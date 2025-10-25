import streamlit as st

# === CONFIGURAÇÃO - DEVE SER A PRIMEIRA CHAMADA ===
st.set_page_config(
    page_title="Planejamento PM & Estoque",
    page_icon="🔧",
    layout="wide"
)

# === IMPORTS APÓS CONFIGURAÇÃO ===
import pandas as pd
import numpy as np
import math
from typing import Dict, Any, Optional, Tuple
import warnings
import sys
from pathlib import Path

warnings.filterwarnings('ignore')

# Adiciona o diretório raiz ao path
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

# === PROCESSA NAVEGAÇÃO PENDENTE ===
handle_navigation()

# === INICIALIZAÇÃO ===
initialize_session_state()

# === FUNÇÕES MATEMÁTICAS CORE ===

def weibull_reliability(t: float, lambda_param: float, rho_param: float) -> float:
    """Calcula a confiabilidade Weibull: R(t) = exp(-(t/λ)^ρ)"""
    if t <= 0:
        return 1.0
    try:
        return math.exp(-((t / lambda_param) ** rho_param))
    except:
        return 0.0

def weibull_pdf(t: float, lambda_param: float, rho_param: float) -> float:
    """Calcula a função densidade de probabilidade Weibull"""
    if t <= 0:
        return 0.0
    try:
        scale_ratio = t / lambda_param
        return (rho_param / lambda_param) * (scale_ratio ** (rho_param - 1)) * \
               math.exp(-(scale_ratio ** rho_param))
    except:
        return 0.0

def calculate_mtbf_weibull(lambda_param: float, rho_param: float) -> float:
    """Calcula MTBF = λ × Γ(1 + 1/ρ)"""
    try:
        def gamma_approx(z):
            if z == 1:
                return 1.0
            if z < 1:
                return gamma_approx(z + 1) / z
            return math.sqrt(2 * math.pi / z) * ((z / math.e) ** z) * (1 + 1/(12*z))
        
        gamma_value = gamma_approx(1 + 1/rho_param)
        return lambda_param * gamma_value
    except:
        return lambda_param

def expected_cycle_length_numerical(T: float, lambda_param: float, rho_param: float, 
                                   n_points: int = 1000) -> float:
    """Calcula E[min(T, X)] numericamente"""
    if T <= 0:
        return 0.0
    try:
        dt = T / n_points
        times = np.linspace(dt, T, n_points)
        reliabilities = [weibull_reliability(t, lambda_param, rho_param) for t in times]
        integral = dt * (0.5 * reliabilities[0] + sum(reliabilities[1:-1]) + 0.5 * reliabilities[-1])
        return integral
    except:
        return T * 0.5

def age_replacement_optimization(lambda_param: float, rho_param: float, 
                                cost_pm: float, cost_cm: float, 
                                cost_downtime_pm: float = 0, 
                                cost_downtime_cm: float = 0) -> Dict[str, Any]:
    """Otimização da política de substituição por idade"""
    
    total_cost_pm = cost_pm + cost_downtime_pm
    total_cost_cm = cost_cm + cost_downtime_cm
    
    def cost_rate_function(T: float) -> float:
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
    
    mtbf = calculate_mtbf_weibull(lambda_param, rho_param)
    left = 0.1 * mtbf
    right = 3.0 * mtbf
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
        return {"error": str(e), "success": False}

def calculate_maintenance_scenarios(lambda_param: float, rho_param: float, 
                                  cost_pm: float, cost_cm: float,
                                  cost_downtime_pm: float = 0, 
                                  cost_downtime_cm: float = 0,
                                  hours_per_year: float = 8760) -> pd.DataFrame:
    """Gera cenários de manutenção"""
    mtbf = calculate_mtbf_weibull(lambda_param, rho_param)
    
    intervals = np.array([0.3, 0.5, 0.7, 1.0, 1.2, 1.5]) * mtbf
    
    scenarios = []
    total_cost_pm = cost_pm + cost_downtime_pm
    total_cost_cm = cost_cm + cost_downtime_cm
    
    for interval in intervals:
        try:
            reliability = weibull_reliability(interval, lambda_param, rho_param)
            expected_cycle = expected_cycle_length_numerical(interval, lambda_param, rho_param)
            
            if expected_cycle <= 0:
                continue
            
            cost_rate = (total_cost_pm * reliability + total_cost_cm * (1 - reliability)) / expected_cycle
            cycles_per_year = hours_per_year / expected_cycle
            pm_per_year = reliability * cycles_per_year
            cm_per_year = (1 - reliability) * cycles_per_year
            
            cost_pm_annual = pm_per_year * cost_pm
            cost_cm_annual = cm_per_year * cost_cm
            cost_total_annual = cost_pm_annual + cost_cm_annual
            
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
    """Calcula parâmetros de gestão de estoque"""
    
    try:
        reliability = weibull_reliability(optimal_interval, lambda_param, rho_param)
        expected_cycle = expected_cycle_length_numerical(optimal_interval, lambda_param, rho_param)
        
        if expected_cycle <= 0:
            return {"error": "Ciclo esperado inválido", "success": False}
        
        cycles_per_year = hours_per_year / expected_cycle
        pm_per_year = reliability * cycles_per_year
        cm_per_year = (1 - reliability) * cycles_per_year
        annual_demand = pm_per_year + cm_per_year
        
        demand_rate_per_hour = annual_demand / hours_per_year
        mean_demand_lt = demand_rate_per_hour * lead_time_hours
        
        if service_level >= 0.99:
            z_score = 2.33
        elif service_level >= 0.95:
            z_score = 1.65
        elif service_level >= 0.90:
            z_score = 1.28
        else:
            z_score = 0.84
        
        std_demand_lt = math.sqrt(mean_demand_lt)
        safety_stock = z_score * std_demand_lt
        reorder_point = mean_demand_lt + safety_stock
        
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
        return {"error": str(e), "success": False}

# === HEADER ===
st.title("🔧 Planejamento PM & Estoque")
st.markdown("**Otimização de intervalos de manutenção preventiva e gestão de peças de reposição**")
st.markdown("---")

# === STATUS DO PIPELINE ===
st.subheader("📊 Status do Pipeline")
display_pipeline_status()
st.markdown("---")

# === VALIDAÇÃO DE PRÉ-REQUISITOS ===

# 1. Dataset carregado
if st.session_state.dataset is None or st.session_state.dataset.empty:
    st.error("❌ **Dataset não carregado**")
    st.info("👈 Use a barra lateral para navegar até 'Dados UNIFIED'")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        create_navigation_button(
            "pages/1_Dados_UNIFIED.py",
            "🔄 **Ir para Dados UNIFIED**",
            key="planning_to_dados"
        )
    st.stop()

# 2. Análise Weibull executada
is_weibull_valid, weibull_message = validate_weibull_availability()

if not is_weibull_valid:
    st.error(f"❌ **{weibull_message}**")
    st.info("👈 Execute a análise Weibull primeiro")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        create_navigation_button(
            "pages/2_Ajuste_Weibull_UNIFIED.py",
            "📈 **Ir para Análise Weibull**",
            key="planning_to_weibull"
        )
    st.stop()

# === DADOS VALIDADOS ===
available_components = get_available_components()
st.success(f"✅ **Dados Weibull disponíveis** para {len(available_components)} componentes")

# === SIDEBAR - CONFIGURAÇÕES ===
with st.sidebar:
    st.header("🎯 Configurações")
    
    st.markdown("---")
    st.subheader("🔩 Componente")
    selected_component = st.selectbox(
        "Selecione:",
        options=available_components,
        index=0,
        key="planning_component_selector"
    )
    
    st.subheader("🚛 Frota")
    if 'fleet' in st.session_state.dataset.columns:
        available_fleets = ["Todos"] + list(st.session_state.dataset['fleet'].unique())
        selected_fleet = st.selectbox(
            "Selecione:",
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
    st.subheader("💰 Custos")
    cost_pm = st.number_input("Custo MP ($):", min_value=0.0, value=1000.0, step=100.0)
    cost_cm = st.number_input("Custo MC ($):", min_value=0.0, value=5000.0, step=100.0)
    
    with st.expander("⏱️ Custos de Parada"):
        cost_downtime_pm = st.number_input("Parada MP ($/h):", min_value=0.0, value=0.0, step=10.0)
        cost_downtime_cm = st.number_input("Parada MC ($/h):", min_value=0.0, value=0.0, step=10.0)
    
    st.markdown("---")
    st.subheader("📦 Estoque")
    lead_time_days = st.number_input("Lead Time (dias):", min_value=1, value=30, step=1)
    service_level = st.slider("Nível de Serviço:", 0.80, 0.99, 0.95, 0.01)
    
    with st.expander("💲 Custos de Estoque"):
        unit_cost = st.number_input("Custo unitário ($):", min_value=0.0, value=1000.0, step=100.0)
        holding_rate = st.slider("Taxa de posse:", 0.05, 0.50, 0.20, 0.01)
        ordering_cost = st.number_input("Custo de pedido ($):", min_value=0.0, value=100.0, step=10.0)
    
    st.markdown("---")
    st.subheader("📋 Resumo")
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

# === EXIBIÇÃO DOS PARÂMETROS ===
st.subheader(f"📊 Análise: {selected_component} | Frota: {selected_fleet}")

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
    elif rho_param <= 1.1:
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

if not optimization_result.get("success", False):
    st.error(f"❌ **Falha na otimização:** {optimization_result.get('error', 'Erro desconhecido')}")
    st.stop()

optimal_interval = optimization_result["optimal_interval"]
optimal_cost_rate = optimization_result["optimal_cost_rate"]
reliability_optimal = optimization_result["reliability_at_optimal"]

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
    st.metric("🎯 Intervalo Ótimo", f"{optimal_interval:.0f}h", f"{optimal_interval/24:.1f} dias")

with col2:
    st.metric("💰 Taxa de Custo", f"${optimal_cost_rate:.2f}/h")

with col3:
    st.metric("📊 Confiabilidade", f"{reliability_optimal:.1%}")

with col4:
    annual_cost = optimal_cost_rate * 8760
    st.metric("📅 Custo Anual", f"${annual_cost:,.0f}")

# === CENÁRIOS ===
st.markdown("---")
st.subheader("📊 Análise de Cenários")

with st.spinner("🔄 Gerando cenários..."):
    scenarios_df = calculate_maintenance_scenarios(
        lambda_param, rho_param, cost_pm, cost_cm,
        cost_downtime_pm, cost_downtime_cm
    )

if scenarios_df.empty:
    st.error("❌ Falha ao gerar cenários")
else:
    st.session_state.scenarios_Todos_Todos_Motor = scenarios_df
    st.dataframe(scenarios_df, use_container_width=True, hide_index=True)

# === GRÁFICOS ===
st.markdown("---")
st.subheader("📈 Visualizações")

tab1, tab2, tab3 = st.tabs(["📊 Custo vs Intervalo", "📉 Confiabilidade", "💰 Custos Anuais"])

with tab1:
    st.markdown("#### Taxa de Custo por Intervalo")
    
    intervals_range = np.linspace(mtbf * 0.2, mtbf * 2.5, 100)
    cost_rates = []
    
    total_cost_pm = cost_pm + cost_downtime_pm
    total_cost_cm = cost_cm + cost_downtime_cm
    
    for interval in intervals_range:
        reliability = weibull_reliability(interval, lambda_param, rho_param)
        expected_cycle = expected_cycle_length_numerical(interval, lambda_param, rho_param)
        
        if expected_cycle > 0:
            cost_rate = ((total_cost_pm * reliability + total_cost_cm * (1 - reliability)) / expected_cycle)
            cost_rates.append(cost_rate)
        else:
            cost_rates.append(None)
    
    valid_data = [(i, c) for i, c in zip(intervals_range, cost_rates) if c is not None]
    if valid_data:
        intervals_valid, costs_valid = zip(*valid_data)
        chart_data = pd.DataFrame({
            'Intervalo (h)': intervals_valid,
            'Taxa de Custo ($/h)': costs_valid
        })
        st.line_chart(chart_data.set_index('Intervalo (h)'), height=400)
        
        st.info(f"🎯 **Ponto Ótimo:** {optimal_interval:.0f}h com taxa de ${optimal_cost_rate:.2f}/h")

with tab2:
    st.markdown("#### Curva de Confiabilidade")
    
    time_range = np.linspace(0, mtbf * 2, 100)
    reliability_values = [weibull_reliability(t, lambda_param, rho_param) for t in time_range]
    
    reliability_df = pd.DataFrame({
        'Tempo (h)': time_range,
        'Confiabilidade': reliability_values
    })
    
    st.line_chart(reliability_df.set_index('Tempo (h)'), height=400)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("R(T*)", f"{reliability_optimal:.1%}")
    with col2:
        r_mtbf = weibull_reliability(mtbf, lambda_param, rho_param)
        st.metric("R(MTBF)", f"{r_mtbf:.1%}")
    with col3:
        b10 = lambda_param * ((-np.log(0.9)) ** (1/rho_param))
        st.metric("B10 Life", f"{b10:.0f}h")

with tab3:
    st.markdown("#### Decomposição de Custos")
    
    if not scenarios_df.empty:
        costs_chart = scenarios_df[['Intervalo (h)', 'CustoPM/ano', 'CustoCM/ano']].copy()
        costs_chart = costs_chart.set_index('Intervalo (h)')
        st.bar_chart(costs_chart, height=400)
        
        best_idx = scenarios_df['Taxa de Custo ($/h)'].idxmin()
        best_scenario = scenarios_df.loc[best_idx]
        
        st.success(f"✨ **Melhor cenário:** {best_scenario['Intervalo (h)']:.0f}h com custo total de ${best_scenario['Custo Total/ano']:,.0f}/ano")

# === GESTÃO DE ESTOQUE ===
st.markdown("---")
st.subheader("📦 Gestão de Estoque")

lead_time_hours = lead_time_days * 24

with st.spinner("🔄 Calculando parâmetros..."):
    inventory_params = calculate_inventory_strategy(
        optimal_interval, lambda_param, rho_param,
        lead_time_hours, service_level, unit_cost, holding_rate, ordering_cost
    )

if not inventory_params.get("success", False):
    st.error(f"❌ **Falha:** {inventory_params.get('error', 'Erro desconhecido')}")
else:
    st.session_state.inventory_strategy_Todos_Todos_Motor = inventory_params
    
    st.success("✅ **Parâmetros calculados!**")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Demanda Anual", f"{inventory_params['annual_demand']:.1f} peças")
    
    with col2:
        st.metric("🔄 Ponto de Reposição", f"{inventory_params['reorder_point']:.0f} peças")
    
    with col3:
        st.metric("🛡️ Estoque de Segurança", f"{inventory_params['safety_stock']:.0f} peças")
    
    with col4:
        st.metric("📦 Lote Econômico", f"{inventory_params['economic_order_quantity']:.0f} peças")

# === RESUMO EXECUTIVO ===
st.markdown("---")
st.subheader("📋 Resumo Executivo")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🎯 **Estratégia de Manutenção**")
    st.write(f"**Componente:** {selected_component}")
    st.write(f"**Política:** Substituição por idade")
    st.write(f"**Intervalo:** {optimal_interval:.0f}h ({optimal_interval/24:.1f} dias)")
    st.write(f"**Confiabilidade:** {reliability_optimal:.1%}")
    st.write(f"**Custo anual:** ${optimal_cost_rate * 8760:,.0f}")

with col2:
    st.markdown("### 📦 **Estratégia de Estoque**")
    if inventory_params.get("success"):
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
    if not scenarios_df.empty:
        csv = scenarios_df.to_csv(index=False)
        st.download_button(
            "📊 **Download Cenários (CSV)**",
            data=csv,
            file_name=f"cenarios_{selected_component}.csv",
            mime="text/csv",
            use_container_width=True
        )

with col2:
    if st.button("📋 **Gerar Relatório JSON**", use_container_width=True):
        import json
        summary = {
            "component": selected_component,
            "maintenance_strategy": st.session_state.maintenance_strategy_Todos_Todos_Motor,
            "inventory_strategy": st.session_state.inventory_strategy_Todos_Todos_Motor,
            "scenarios": scenarios_df.to_dict('records') if not scenarios_df.empty else []
        }
        json_str = json.dumps(summary, indent=2)
        st.download_button(
            "💾 **Download JSON**",
            data=json_str,
            file_name=f"estrategias_{selected_component}.json",
            mime="application/json"
        )

with col3:
    if st.button("🔄 **Nova Análise**", use_container_width=True):
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
