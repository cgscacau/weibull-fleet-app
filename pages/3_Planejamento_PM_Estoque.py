import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.optimize import minimize_scalar
from scipy.special import gamma
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

# === FUNÇÕES DE OTIMIZAÇÃO ===

def calculate_weibull_reliability(t, lambda_param, rho_param):
    """Calcula confiabilidade Weibull R(t) = exp(-(t/λ)^ρ)"""
    return np.exp(-((t / lambda_param) ** rho_param))

def calculate_weibull_hazard(t, lambda_param, rho_param):
    """Calcula taxa de falha h(t) = (ρ/λ) * (t/λ)^(ρ-1)"""
    return (rho_param / lambda_param) * ((t / lambda_param) ** (rho_param - 1))

def calculate_mtbf_weibull(lambda_param, rho_param):
    """Calcula MTBF = λ * Γ(1 + 1/ρ)"""
    try:
        return lambda_param * gamma(1 + 1/rho_param)
    except:
        return None

def calculate_age_replacement_cost(interval, lambda_param, rho_param, cost_pm, cost_cm, cost_downtime_pm=0, cost_downtime_cm=0):
    """
    Calcula custo total para política de substituição por idade.
    
    Args:
        interval: Intervalo de manutenção preventiva
        lambda_param, rho_param: Parâmetros Weibull
        cost_pm: Custo da manutenção preventiva
        cost_cm: Custo da manutenção corretiva
        cost_downtime_pm: Custo de parada para MP
        cost_downtime_cm: Custo de parada para MC
    
    Returns:
        Dict com métricas de custo
    """
    if interval <= 0:
        return {"cost_rate": float('inf'), "reliability": 0}
    
    # Confiabilidade no intervalo
    reliability = calculate_weibull_reliability(interval, lambda_param, rho_param)
    
    # Probabilidade de falha no intervalo
    failure_prob = 1 - reliability
    
    # Função de distribuição acumulada
    def weibull_cdf(t):
        return 1 - np.exp(-((t / lambda_param) ** rho_param))
    
    # Função densidade de probabilidade
    def weibull_pdf(t):
        return (rho_param / lambda_param) * ((t / lambda_param) ** (rho_param - 1)) * np.exp(-((t / lambda_param) ** rho_param))
    
    # Tempo esperado até falha (integral de 0 a interval de t*f(t) dt)
    # Para Weibull: E[T|T<=interval] = λ * gamma_lower(1+1/ρ, (interval/λ)^ρ) / F(interval)
    # Aproximação numérica
    if failure_prob > 0:
        dt = interval / 1000
        times = np.linspace(dt, interval, 1000)
        pdf_values = weibull_pdf(times)
        expected_failure_time = np.trapz(times * pdf_values, times) / failure_prob
    else:
        expected_failure_time = interval
    
    # Custos esperados
    cost_pm_total = cost_pm + cost_downtime_pm
    cost_cm_total = cost_cm + cost_downtime_cm
    
    expected_cost = reliability * cost_pm_total + failure_prob * cost_cm_total
    expected_time = reliability * interval + failure_prob * expected_failure_time
    
    # Taxa de custo por unidade de tempo
    cost_rate = expected_cost / expected_time if expected_time > 0 else float('inf')
    
    # Frequência de manutenções por ano (assumindo 8760 horas/ano)
    hours_per_year = 8760
    pm_per_year = reliability * (hours_per_year / interval) if interval > 0 else 0
    cm_per_year = failure_prob * (hours_per_year / expected_time) if expected_time > 0 else 0
    
    return {
        "cost_rate": cost_rate,
        "reliability": reliability,
        "failure_prob": failure_prob,
        "expected_cost": expected_cost,
        "expected_time": expected_time,
        "pm_per_year": pm_per_year,
        "cm_per_year": cm_per_year,
        "total_interventions_per_year": pm_per_year + cm_per_year
    }

def optimize_maintenance_interval(lambda_param, rho_param, cost_pm, cost_cm, cost_downtime_pm=0, cost_downtime_cm=0):
    """
    Encontra o intervalo ótimo de manutenção que minimiza o custo por unidade de tempo.
    """
    def objective(interval):
        result = calculate_age_replacement_cost(
            interval, lambda_param, rho_param, 
            cost_pm, cost_cm, cost_downtime_pm, cost_downtime_cm
        )
        return result["cost_rate"]
    
    # Busca o intervalo ótimo
    mtbf = calculate_mtbf_weibull(lambda_param, rho_param)
    if mtbf:
        # Busca entre 10% e 200% do MTBF
        bounds = (0.1 * mtbf, 2.0 * mtbf)
    else:
        # Busca padrão
        bounds = (100, 10000)
    
    try:
        result = minimize_scalar(objective, bounds=bounds, method='bounded')
        optimal_interval = result.x
        optimal_cost_rate = result.fun
        
        # Calcula métricas para o intervalo ótimo
        optimal_metrics = calculate_age_replacement_cost(
            optimal_interval, lambda_param, rho_param,
            cost_pm, cost_cm, cost_downtime_pm, cost_downtime_cm
        )
        
        return {
            "optimal_interval": optimal_interval,
            "optimal_cost_rate": optimal_cost_rate,
            "reliability_at_optimal": optimal_metrics["reliability"],
            "pm_per_year": optimal_metrics["pm_per_year"],
            "cm_per_year": optimal_metrics["cm_per_year"],
            "success": True
        }
    except:
        return {"success": False, "error": "Falha na otimização"}

def generate_maintenance_scenarios(lambda_param, rho_param, cost_pm, cost_cm, cost_downtime_pm=0, cost_downtime_cm=0):
    """
    Gera cenários de manutenção para diferentes intervalos.
    """
    mtbf = calculate_mtbf_weibull(lambda_param, rho_param)
    
    if mtbf:
        # Intervalos baseados no MTBF
        intervals = np.array([
            0.3 * mtbf,  # Muito conservador
            0.5 * mtbf,  # Conservador
            0.7 * mtbf,  # Moderado
            1.0 * mtbf,  # MTBF
            1.5 * mtbf,  # Agressivo
            2.0 * mtbf   # Muito agressivo
        ])
    else:
        # Intervalos padrão
        intervals = np.array([500, 1000, 1500, 2000, 3000, 4000])
    
    scenarios = []
    
    for interval in intervals:
        metrics = calculate_age_replacement_cost(
            interval, lambda_param, rho_param,
            cost_pm, cost_cm, cost_downtime_pm, cost_downtime_cm
        )
        
        # Classifica nível de risco baseado na confiabilidade
        reliability = metrics["reliability"]
        if reliability >= 0.95:
            risk_level = "Muito Baixo"
            risk_color = "🟢"
        elif reliability >= 0.90:
            risk_level = "Baixo"
            risk_color = "🟡"
        elif reliability >= 0.80:
            risk_level = "Médio"
            risk_color = "🟠"
        elif reliability >= 0.70:
            risk_level = "Alto"
            risk_color = "🔴"
        else:
            risk_level = "Muito Alto"
            risk_color = "⚫"
        
        scenarios.append({
            "Intervalo (h)": round(interval, 0),
            "Confiabilidade": round(reliability, 3),
            "Taxa de Custo ($/h)": round(metrics["cost_rate"], 2),
            "PM por ano": round(metrics["pm_per_year"], 2),
            "CM por ano": round(metrics["cm_per_year"], 2),
            "Custo PM/ano ($)": round(metrics["pm_per_year"] * cost_pm, 0),
            "Custo CM/ano ($)": round(metrics["cm_per_year"] * cost_cm, 0),
            "Custo Total/ano ($)": round((metrics["pm_per_year"] * cost_pm) + (metrics["cm_per_year"] * cost_cm), 0),
            "Nível de Risco": f"{risk_color} {risk_level}"
        })
    
    return pd.DataFrame(scenarios)

def calculate_inventory_parameters(lambda_param, rho_param, optimal_interval, lead_time, service_level=0.95):
    """
    Calcula parâmetros de estoque baseados na estratégia de manutenção.
    """
    # Taxa de demanda (peças por ano)
    hours_per_year = 8760
    
    # Demanda de MP
    pm_per_year = hours_per_year / optimal_interval
    
    # Demanda de MC (aproximação)
    reliability = calculate_weibull_reliability(optimal_interval, lambda_param, rho_param)
    failure_rate = 1 - reliability
    cm_per_year = failure_rate * pm_per_year
    
    total_demand_per_year = pm_per_year + cm_per_year
    
    # Demanda durante lead time
    demand_lead_time = total_demand_per_year * (lead_time / hours_per_year)
    
    # Desvio padrão da demanda (aproximação Poisson)
    demand_std = np.sqrt(demand_lead_time)
    
    # Fator de segurança baseado no nível de serviço
    from scipy.stats import norm
    z_score = norm.ppf(service_level)
    
    # Estoque de segurança
    safety_stock = max(1, round(z_score * demand_std))
    
    # Ponto de reposição
    reorder_point = max(1, round(demand_lead_time + safety_stock))
    
    # Lote econômico de compra (EOQ) - simplificado
    # EOQ = sqrt(2 * D * S / H) onde D=demanda, S=custo pedido, H=custo manutenção
    # Usando valores típicos
    ordering_cost = 100  # Custo típico de pedido
    holding_cost_rate = 0.25  # 25% ao ano
    
    # Estimativa de custo unitário da peça (baseado no custo de MP)
    unit_cost = 500  # Valor padrão
    holding_cost = holding_cost_rate * unit_cost
    
    if holding_cost > 0:
        eoq = np.sqrt(2 * total_demand_per_year * ordering_cost / holding_cost)
    else:
        eoq = 1
    
    return {
        "demand_per_year": round(total_demand_per_year, 2),
        "pm_demand_per_year": round(pm_per_year, 2),
        "cm_demand_per_year": round(cm_per_year, 2),
        "demand_lead_time": round(demand_lead_time, 2),
        "safety_stock": int(safety_stock),
        "reorder_point": int(reorder_point),
        "economic_order_quantity": round(eoq, 0),
        "service_level": service_level,
        "lead_time_hours": lead_time
    }

# === INTERFACE PRINCIPAL ===

# === HEADER ===
st.title("🔧 Planejamento PM & Estoque")
st.markdown("**Otimização de intervalos de manutenção preventiva e gestão de peças de reposição**")
st.markdown("---")

# === STATUS DO PIPELINE ===
st.subheader("📊 Status do Pipeline")
display_pipeline_status()

# === VALIDAÇÃO DE PRÉ-REQUISITOS ===

# 1. Verifica se dados estão carregados
if st.session_state.dataset is None or st.session_state.dataset.empty:
    st.error("❌ **Nenhum dataset carregado**")
    st.info("👈 **Próximo passo:** Vá para 'Dados UNIFIED' e carregue seus dados")
    
    if st.button("🔄 Ir para Dados UNIFIED", type="primary"):
        st.switch_page("pages/1_Dados_UNIFIED.py")
    
    st.stop()

# 2. Verifica se análise Weibull foi executada
is_weibull_valid, weibull_message = validate_weibull_availability()

if not is_weibull_valid:
    st.error(f"❌ **{weibull_message}**")
    st.info("👈 **Próximo passo:** Execute a análise Weibull primeiro")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📈 Ir para Análise Weibull", type="primary", use_container_width=True):
            st.switch_page("pages/2_Ajuste_Weibull_UNIFIED.py")
    
    st.stop()

# === DADOS VALIDADOS - CONTINUA ===
available_components = get_available_components()
st.success(f"✅ **Dados Weibull disponíveis** para {len(available_components)} componentes")

# === SIDEBAR COM CONFIGURAÇÕES ===
with st.sidebar:
    st.header("🎯 Configurações de Otimização")
    
    # === SELEÇÃO DE COMPONENTE ===
    st.subheader("🔩 Componente")
    selected_component = st.selectbox(
        "Selecione o componente:",
        options=available_components,
        index=0,
        key="planning_component_selector"
    )
    
    # === SELEÇÃO DE FROTA ===
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
        st.info("Coluna 'fleet' não encontrada nos dados")
    
    # Atualiza session state
    st.session_state.selected_component = selected_component
    st.session_state.selected_fleet = selected_fleet
    
    st.markdown("---")
    
    # === PARÂMETROS DE CUSTO ===
    st.subheader("💰 Custos de Manutenção")
    
    cost_pm = st.number_input(
        "Custo MP ($):",
        min_value=0.0,
        value=1000.0,
        step=100.0,
        help="Custo da manutenção preventiva"
    )
    
    cost_cm = st.number_input(
        "Custo MC ($):",
        min_value=0.0,
        value=5000.0,
        step=100.0,
        help="Custo da manutenção corretiva"
    )
    
    with st.expander("⏱️ Custos de Parada"):
        cost_downtime_pm = st.number_input(
            "Custo parada MP ($/h):",
            min_value=0.0,
            value=0.0,
            step=10.0
        )
        
        cost_downtime_cm = st.number_input(
            "Custo parada MC ($/h):",
            min_value=0.0,
            value=0.0,
            step=10.0
        )
    
    st.markdown("---")
    
    # === PARÂMETROS DE ESTOQUE ===
    st.subheader("📦 Parâmetros de Estoque")
    
    lead_time = st.number_input(
        "Lead Time (horas):",
        min_value=1,
        value=720,  # 30 dias
        step=24,
        help="Tempo de reposição do estoque"
    )
    
    service_level = st.slider(
        "Nível de Serviço:",
        min_value=0.80,
        max_value=0.99,
        value=0.95,
        step=0.01,
        format="%.2f",
        help="Probabilidade de não haver falta de estoque"
    )
    
    st.markdown("---")
    
    # === INFORMAÇÕES DA SELEÇÃO ===
    st.subheader("📋 Seleção Atual")
    st.write(f"**Componente:** {selected_component}")
    st.write(f"**Frota:** {selected_fleet}")
    st.write(f"**Razão CM/MP:** {cost_cm/cost_pm:.1f}x")

# === VALIDAÇÃO ESPECÍFICA DO COMPONENTE ===
is_comp_valid, comp_message = validate_weibull_availability(selected_component)
if not is_comp_valid:
    st.error(f"❌ {comp_message}")
    st.stop()

# === EXTRAÇÃO DOS PARÂMETROS WEIBULL ===
weibull_params = st.session_state.weibull_results[selected_component]

if not weibull_params.get('success', False):
    st.error(f"❌ **Erro nos parâmetros Weibull:** {weibull_params.get('error', 'Erro desconhecido')}")
    st.stop()

lambda_param = weibull_params['lambda']
rho_param = weibull_params['rho']
mtbf = weibull_params.get('MTBF')

# === SEÇÃO PRINCIPAL ===
st.subheader(f"📊 Análise: {selected_component} | Frota: {selected_fleet}")

# === EXIBE PARÂMETROS WEIBULL ===
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("λ (Escala)", f"{lambda_param:.2f}")

with col2:
    st.metric("ρ (Forma)", f"{rho_param:.2f}")

with col3:
    st.metric("MTBF", f"{mtbf:.0f}h" if mtbf else "N/A")

with col4:
    st.metric("Observações", weibull_params['n_observations'])

with col5:
    # Interpretação do parâmetro de forma
    if rho_param < 1:
        failure_pattern = "🔽 Decrescente"
        pattern_color = "blue"
    elif rho_param == 1:
        failure_pattern = "➡️ Constante"
        pattern_color = "green"
    else:
        failure_pattern = "📈 Crescente"
        pattern_color = "red"
    
    st.metric("Taxa de Falha", failure_pattern)

# === OTIMIZAÇÃO DE MANUTENÇÃO ===
st.markdown("---")
st.subheader("🎯 Otimização de Manutenção Preventiva")

# Executa otimização
with st.spinner("🔄 Otimizando intervalo de manutenção..."):
    optimization_result = optimize_maintenance_interval(
        lambda_param, rho_param, cost_pm, cost_cm, 
        cost_downtime_pm, cost_downtime_cm
    )

if optimization_result.get("success", False):
    optimal_interval = optimization_result["optimal_interval"]
    optimal_cost_rate = optimization_result["optimal_cost_rate"]
    reliability_optimal = optimization_result["reliability_at_optimal"]
    
    # Salva no session state para compatibilidade
    st.session_state.maintenance_strategy_Todos_Todos_Motor = {
        "policy": "Idade ótima",
        "intervalo_h": optimal_interval,
        "cost_rate": optimal_cost_rate,
        "reliability": reliability_optimal,
        "component": selected_component
    }
    
    # === RESULTADOS DA OTIMIZAÇÃO ===
    st.success("✅ **Intervalo ótimo calculado com sucesso!**")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "🎯 Intervalo Ótimo", 
            f"{optimal_interval:.0f}h",
            help="Intervalo que minimiza o custo total por hora"
        )
    
    with col2:
        st.metric(
            "💰 Taxa de Custo", 
            f"${optimal_cost_rate:.2f}/h",
            help="Custo total por hora de operação"
        )
    
    with col3:
        st.metric(
            "📊 Confiabilidade", 
            f"{reliability_optimal:.1%}",
            help="Probabilidade de não falhar no intervalo"
        )
    
    with col4:
        annual_cost = optimal_cost_rate * 8760
        st.metric(
            "📅 Custo Anual", 
            f"${annual_cost:,.0f}",
            help="Custo total estimado por ano"
        )

else:
    st.error("❌ **Falha na otimização**")
    st.info("Verifique os parâmetros de custo e tente novamente")
    st.stop()

# === ANÁLISE DE CENÁRIOS ===
st.markdown("---")
st.subheader("📊 Análise de Cenários")

with st.spinner("🔄 Gerando cenários de manutenção..."):
    scenarios_df = generate_maintenance_scenarios(
        lambda_param, rho_param, cost_pm, cost_cm,
        cost_downtime_pm, cost_downtime_cm
    )

# Salva cenários no session state para compatibilidade
st.session_state.scenarios_Todos_Todos_Motor = scenarios_df

# Exibe tabela de cenários
st.dataframe(
    scenarios_df,
    use_container_width=True,
    hide_index=True
)

# === GRÁFICOS DE ANÁLISE ===
st.markdown("---")
st.subheader("📈 Visualizações")

# Prepara dados para gráficos
intervals_plot = np.linspace(100, 3 * mtbf if mtbf else 5000, 100)
cost_rates = []
reliabilities = []

for interval in intervals_plot:
    metrics = calculate_age_replacement_cost(
        interval, lambda_param, rho_param,
        cost_pm, cost_cm, cost_downtime_pm, cost_downtime_cm
    )
    cost_rates.append(metrics["cost_rate"])
    reliabilities.append(metrics["reliability"])

# Cria subplot com dois eixos Y
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=[
        'Taxa de Custo vs Intervalo de Manutenção',
        'Confiabilidade vs Intervalo de Manutenção',
        'Comparação de Cenários - Custo Total Anual',
        'Comparação de Cenários - Frequência de Manutenções'
    ],
    specs=[[{"secondary_y": False}, {"secondary_y": False}],
           [{"secondary_y": False}, {"secondary_y": False}]]
)

# Gráfico 1: Taxa de custo
fig.add_trace(
    go.Scatter(
        x=intervals_plot,
        y=cost_rates,
        mode='lines',
        name='Taxa de Custo',
        line=dict(color='red', width=2)
    ),
    row=1, col=1
)

# Marca ponto ótimo
fig.add_trace(
    go.Scatter(
        x=[optimal_interval],
        y=[optimal_cost_rate],
        mode='markers',
        name='Ótimo',
        marker=dict(color='red', size=12, symbol='star')
    ),
    row=1, col=1
)

# Gráfico 2: Confiabilidade
fig.add_trace(
    go.Scatter(
        x=intervals_plot,
        y=reliabilities,
        mode='lines',
        name='Confiabilidade',
        line=dict(color='blue', width=2)
    ),
    row=1, col=2
)

# Gráfico 3: Cenários - Custo total
fig.add_trace(
    go.Bar(
        x=scenarios_df['Intervalo (h)'],
        y=scenarios_df['Custo Total/ano ($)'],
        name='Custo Total/ano',
        marker_color='lightblue'
    ),
    row=2, col=1
)

# Gráfico 4: Cenários - Frequência
fig.add_trace(
    go.Bar(
        x=scenarios_df['Intervalo (h)'],
        y=scenarios_df['PM por ano'],
        name='PM por ano',
        marker_color='green',
        opacity=0.7
    ),
    row=2, col=2
)

fig.add_trace(
    go.Bar(
        x=scenarios_df['Intervalo (h)'],
        y=scenarios_df['CM por ano'],
        name='CM por ano',
        marker_color='red',
        opacity=0.7
    ),
    row=2, col=2
)

# Configurações dos eixos
fig.update_xaxes(title_text="Intervalo de Manutenção (h)", row=1, col=1)
fig.update_yaxes(title_text="Taxa de Custo ($/h)", row=1, col=1)

fig.update_xaxes(title_text="Intervalo de Manutenção (h)", row=1, col=2)
fig.update_yaxes(title_text="Confiabilidade", row=1, col=2)

fig.update_xaxes(title_text="Intervalo (h)", row=2, col=1)
fig.update_yaxes(title_text="Custo Anual ($)", row=2, col=1)

fig.update_xaxes(title_text="Intervalo (h)", row=2, col=2)
fig.update_yaxes(title_text="Manutenções por Ano", row=2, col=2)

fig.update_layout(
    height=800,
    showlegend=True,
    title_text="Análise de Otimização de Manutenção"
)

st.plotly_chart(fig, use_container_width=True)

# === GESTÃO DE ESTOQUE ===
st.markdown("---")
st.subheader("📦 Gestão de Estoque")

with st.spinner("🔄 Calculando parâmetros de estoque..."):
    inventory_params = calculate_inventory_parameters(
        lambda_param, rho_param, optimal_interval, 
        lead_time, service_level
    )

# Salva no session state para compatibilidade
st.session_state.inventory_strategy_Todos_Todos_Motor = inventory_params

st.success("✅ **Parâmetros de estoque calculados**")

# Exibe métricas de estoque
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "📊 Demanda Anual", 
        f"{inventory_params['demand_per_year']:.1f} peças",
        help="Total de peças necessárias por ano"
    )

with col2:
    st.metric(
        "🔄 Ponto de Reposição", 
        f"{inventory_params['reorder_point']} peças",
        help="Nível de estoque para fazer novo pedido"
    )

with col3:
    st.metric(
        "🛡️ Estoque de Segurança", 
        f"{inventory_params['safety_stock']} peças",
        help="Estoque adicional para cobrir incertezas"
    )

with col4:
    st.metric(
        "📦 Lote Econômico", 
        f"{inventory_params['economic_order_quantity']:.0f} peças",
        help="Quantidade ótima por pedido"
    )

# Detalhes da demanda
with st.expander("🔍 **Detalhes da Demanda**"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Demanda por Manutenção Preventiva:**")
        st.write(f"• {inventory_params['pm_demand_per_year']:.2f} peças/ano")
        st.write(f"• {inventory_params['pm_demand_per_year']/12:.2f} peças/mês")
        
        st.write("**Demanda por Manutenção Corretiva:**")
        st.write(f"• {inventory_params['cm_demand_per_year']:.2f} peças/ano")
        st.write(f"• {inventory_params['cm_demand_per_year']/12:.2f} peças/mês")
    
    with col2:
        st.write("**Parâmetros de Estoque:**")
        st.write(f"• Lead Time: {lead_time} horas ({lead_time/24:.1f} dias)")
        st.write(f"• Nível de Serviço: {service_level:.1%}")
        st.write(f"• Demanda no Lead Time: {inventory_params['demand_lead_time']:.2f} peças")

# === RESUMO EXECUTIVO ===
st.markdown("---")
st.subheader("📋 Resumo Executivo")

# Calcula economia potencial (comparando com estratégia sem otimização)
no_maintenance_cost = cost_cm * (8760 / mtbf) if mtbf else 0
optimized_annual_cost = optimal_cost_rate * 8760
potential_savings = max(0, no_maintenance_cost - optimized_annual_cost)

summary_col1, summary_col2 = st.columns(2)

with summary_col1:
    st.markdown("### 🎯 **Estratégia Recomendada**")
    st.write(f"**Componente:** {selected_component}")
    st.write(f"**Intervalo de MP:** {optimal_interval:.0f} horas ({optimal_interval/24:.1f} dias)")
    st.write(f"**Confiabilidade:** {reliability_optimal:.1%}")
    st.write(f"**Custo anual:** ${optimized_annual_cost:,.0f}")
    st.write(f"**MP por ano:** {optimization_result['pm_per_year']:.1f}")
    st.write(f"**MC por ano:** {optimization_result['cm_per_year']:.1f}")

with summary_col2:
    st.markdown("### 📦 **Gestão de Estoque**")
    st.write(f"**Demanda anual:** {inventory_params['demand_per_year']:.1f} peças")
    st.write(f"**Ponto de reposição:** {inventory_params['reorder_point']} peças")
    st.write(f"**Estoque de segurança:** {inventory_params['safety_stock']} peças")
    st.write(f"**Lote econômico:** {inventory_params['economic_order_quantity']:.0f} peças")
    st.write(f"**Nível de serviço:** {service_level:.1%}")

if potential_savings > 0:
    st.success(f"💰 **Economia potencial:** ${potential_savings:,.0f}/ano comparado à estratégia reativa")

# === EXPORTAÇÃO DE RESULTADOS ===
st.markdown("---")
st.subheader("📤 Exportação de Resultados")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📊 **Exportar Cenários**", use_container_width=True):
        csv = scenarios_df.to_csv(index=False)
        st.download_button(
            label="💾 Download CSV",
            data=csv,
            file_name=f"cenarios_manutencao_{selected_component}.csv",
            mime="text/csv"
        )

with col2:
    # Cria relatório resumido
    summary_report = {
        "Componente": selected_component,
        "Parâmetros Weibull": {"Lambda": lambda_param, "Rho": rho_param, "MTBF": mtbf},
        "Estratégia Ótima": {
            "Intervalo_h": optimal_interval,
            "Confiabilidade": reliability_optimal,
            "Custo_Rate_h": optimal_cost_rate,
            "Custo_Anual": optimized_annual_cost
        },
        "Gestão de Estoque": inventory_params,
        "Custos": {
            "MP": cost_pm,
            "MC": cost_cm,
            "Parada_MP": cost_downtime_pm,
            "Parada_MC": cost_downtime_cm
        }
    }
    
    if st.button("📋 **Exportar Relatório**", use_container_width=True):
        import json
        report_json = json.dumps(summary_report, indent=2)
        st.download_button(
            label="💾 Download JSON",
            data=report_json,
            file_name=f"relatorio_otimizacao_{selected_component}.json",
            mime="application/json"
        )

with col3:
    if st.button("🔄 **Nova Análise**", use_container_width=True):
        # Limpa resultados para nova análise
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

# === INFORMAÇÕES TÉCNICAS (EXPANDÍVEL) ===
with st.expander("🔧 **Informações Técnicas**"):
    st.markdown("""
    **Metodologia:**
    - **Análise de Confiabilidade:** Distribuição Weibull com parâmetros λ (escala) e ρ (forma)
    - **Otimização:** Minimização da taxa de custo por unidade de tempo
    - **Política de Manutenção:** Substituição por idade (Age Replacement)
    - **Gestão de Estoque:** Modelo (s,S) com estoque de segurança
    
    **Fórmulas Principais:**
    - **Confiabilidade:** R(t) = exp(-(t/λ)^ρ)
    - **MTBF:** λ × Γ(1 + 1/ρ)
    - **Taxa de Custo:** E[Custo]/E[Tempo] = (R(t)×C_MP + F(t)×C_MC)/(R(t)×t + F(t)×E[T|T≤t])
    - **Estoque de Segurança:** Z_α × σ_demanda_lead_time
    
    **Limitações:**
    - Assume distribuição Weibull para tempos de falha
    - Não considera deterioração do estoque
    - Custos considerados constantes no tempo
    - Lead time determinístico
    """)
