import streamlit as st
import pandas as pd
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
    
    # Mostra debug para ajudar na resolução
    with st.expander("🔍 **Informações de Debug**"):
        st.write("**Dados disponíveis no Session State:**")
        
        debug_items = [
            ("dataset", "DataFrame" if st.session_state.get("dataset") is not None else "None"),
            ("weibull_results", len(st.session_state.get("weibull_results", {}))),
            ("data_quality_report", "Disponível" if st.session_state.get("data_quality_report") else "None"),
        ]
        
        for key, value in debug_items:
            st.write(f"- **{key}:** {value}")
        
        if st.session_state.get("weibull_results"):
            st.write("**Componentes com análise Weibull:**")
            for comp in st.session_state.weibull_results.keys():
                result = st.session_state.weibull_results[comp]
                status = "✅ Sucesso" if result.get("success", False) else "❌ Falha"
                st.write(f"  - {comp}: {status}")
    
    st.stop()

# === SE CHEGOU ATÉ AQUI, DADOS WEIBULL ESTÃO DISPONÍVEIS ===
available_components = get_available_components()
st.success(f"✅ **Dados Weibull disponíveis** para {len(available_components)} componentes")

# === SIDEBAR COM SELEÇÕES ===
with st.sidebar:
    st.header("🎯 Configurações")
    
    # Seleção de componente
    st.subheader("Componente")
    selected_component = st.selectbox(
        "Selecione o componente:",
        options=["Todos"] + available_components,
        index=0,
        key="planning_component_selector"
    )
    
    # Seleção de frota (se disponível)
    st.subheader("Frota")
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
    
    # Atualiza session state
    st.session_state.selected_component = selected_component
    st.session_state.selected_fleet = selected_fleet
    
    st.markdown("---")
    
    # Informações da seleção atual
    st.subheader("📋 Seleção Atual")
    st.write(f"**Componente:** {selected_component}")
    st.write(f"**Frota:** {selected_fleet}")

# === VALIDAÇÃO ESPECÍFICA DO COMPONENTE ===
if selected_component != "Todos":
    is_comp_valid, comp_message = validate_weibull_availability(selected_component)
    if not is_comp_valid:
        st.error(f"❌ {comp_message}")
        st.stop()

# === SEÇÃO PRINCIPAL ===
st.subheader(f"📊 Análise: {selected_component} | Frota: {selected_fleet}")

# === EXIBE PARÂMETROS WEIBULL ===
if selected_component != "Todos":
    weibull_params = st.session_state.weibull_results[selected_component]
    
    if weibull_params.get('success', False):
        st.success(f"✅ **Parâmetros Weibull para {selected_component}:**")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("λ (Escala)", f"{weibull_params['lambda']:.4f}")
        
        with col2:
            st.metric("ρ (Forma)", f"{weibull_params['rho']:.4f}")
        
        with col3:
            mtbf = weibull_params.get('MTBF')
            st.metric("MTBF", f"{mtbf:.2f}" if mtbf else "N/A")
        
        with col4:
            st.metric("Observações", weibull_params['n_observations'])
    else:
        st.error(f"❌ **Erro nos parâmetros Weibull:** {weibull_params.get('error', 'Erro desconhecido')}")
        st.stop()

else:
    # Visão geral de todos os componentes
    st.info("📊 **Visão geral de todos os componentes com análise Weibull**")
    
    summary_data = []
    for comp, params in st.session_state.weibull_results.items():
        if params.get('success', False):
            summary_data.append({
                'Componente': comp,
                'λ (Escala)': f"{params['lambda']:.4f}",
                'ρ (Forma)': f"{params['rho']:.4f}",
                'MTBF': f"{params.get('MTBF', 0):.2f}" if params.get('MTBF') else "N/A",
                'Observações': params['n_observations']
            })
    
    if summary_data:
        df_summary = pd.DataFrame(summary_data)
        st.dataframe(df_summary, use_container_width=True)

# === SEÇÕES DE PLANEJAMENTO ===
st.markdown("---")

# Aqui você continuaria com suas funcionalidades específicas de otimização
# Mantendo compatibilidade com as variáveis do session_state existentes

st.subheader("🔧 Otimização de Manutenção Preventiva")
st.info("🚧 **Seção em desenvolvimento**")

st.write("**Com os dados Weibull validados, você pode implementar:**")
st.write("- ⏱️ Otimização de intervalos de manutenção")
st.write("- 💰 Cálculo de custos de manutenção") 
st.write("- 📦 Gestão de inventário de peças")
st.write("- 📊 Análise de cenários")

# Placeholder para manter compatibilidade com código existente
if st.button("🎯 Gerar Cenários de Exemplo"):
    # Exemplo básico para manter compatibilidade
    st.session_state.scenarios_Todos_Todos_Motor = pd.DataFrame([
        {
            "Intervalo (h)": 500,
            "Confiabilidade": 0.9,
            "Taxa de Custo (/h)": 12.0,
            "PMporano": 1.75,
            "CustoPM/ano": 12000,
            "Nível de Risco": "Médio"
        },
        {
            "Intervalo (h)": 800,
            "Confiabilidade": 0.8,
            "Taxa de Custo (/h)": 10.2,
            "PMporano": 1.10,
            "CustoPM/ano": 9000,
            "Nível de Risco": "Baixo"
        }
    ])
    
    st.session_state.maintenance_strategy_Todos_Todos_Motor = {
        "policy": "Idade ótima",
        "intervalo_h": 800
    }
    
    st.session_state.inventory_strategy_Todos_Todos_Motor = {
        "reorder_point": 2,
        "safety_stock": 1
    }
    
    st.success("✅ Cenários de exemplo gerados!")

# Exibe resultados se existirem
if st.session_state.get("scenarios_Todos_Todos_Motor") is not None:
    st.subheader("📊 Cenários de Manutenção")
    st.dataframe(st.session_state.scenarios_Todos_Todos_Motor, use_container_width=True)

if st.session_state.get("maintenance_strategy_Todos_Todos_Motor"):
    st.subheader("🎯 Estratégia de Manutenção")
    st.json(st.session_state.maintenance_strategy_Todos_Todos_Motor)

if st.session_state.get("inventory_strategy_Todos_Todos_Motor"):
    st.subheader("📦 Estratégia de Estoque")
    st.json(st.session_state.inventory_strategy_Todos_Todos_Motor)
