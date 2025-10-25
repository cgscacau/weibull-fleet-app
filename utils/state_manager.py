import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime

def initialize_session_state():
    """
    Inicializa todas as variáveis essenciais do session state.
    Deve ser chamada no início de TODAS as páginas.
    """
    defaults = {
        # === DADOS PRINCIPAIS ===
        "dataset": None,
        "original_dataset": None,
        
        # === RESULTADOS DE ANÁLISES ===
        "weibull_results": {},
        "data_quality_report": {},
        "standardization_report": {},
        
        # === SELEÇÕES DO USUÁRIO ===
        "selected_component": None,
        "selected_fleet": "Todos",
        
        # === ESTRATÉGIAS E CENÁRIOS ===
        "maintenance_strategy_Todos_Todos_Motor": None,
        "inventory_strategy_Todos_Todos_Motor": {},
        "scenarios_Todos_Todos_Motor": None,
        "scenarios_Todos_Todos_Todos": None,
        
        # === VARIÁVEIS DE COMPATIBILIDADE ===
        "df": None,
        "ai_explanations": {},
        
        # === CONTROLE DE FLUXO ===
        "analysis_timestamp": None,
        "pipeline_status": {
            "data_loaded": False,
            "weibull_completed": False,
            "planning_ready": False
        }
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

def update_pipeline_status():
    """Atualiza o status do pipeline baseado nos dados disponíveis."""
    status = st.session_state.pipeline_status
    
    # Verifica se dados estão carregados
    status["data_loaded"] = (
        st.session_state.get("dataset") is not None and 
        not st.session_state.dataset.empty
    )
    
    # Verifica se análise Weibull foi concluída
    status["weibull_completed"] = bool(st.session_state.get("weibull_results", {}))
    
    # Verifica se planejamento está pronto
    status["planning_ready"] = (
        status["weibull_completed"] and
        st.session_state.get("selected_component") is not None
    )

def display_pipeline_status():
    """Exibe status visual do pipeline de dados."""
    update_pipeline_status()
    status = st.session_state.pipeline_status
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if status["data_loaded"]:
            count = len(st.session_state.dataset)
            st.success(f"✅ **Dados Carregados**\n{count:,} registros")
        else:
            st.error("❌ **Dados Pendentes**\nCarregue na página 'Dados UNIFIED'")
    
    with col2:
        if status["weibull_completed"]:
            count = len(st.session_state.weibull_results)
            st.success(f"✅ **Análise Weibull**\n{count} componentes")
        else:
            st.warning("⚠️ **Weibull Pendente**\nExecute na página 'Ajuste Weibull'")
    
    with col3:
        if status["planning_ready"]:
            st.success("✅ **Planejamento Pronto**\nTodos os dados disponíveis")
        else:
            st.warning("⚠️ **Planejamento Bloqueado**\nComplete etapas anteriores")

def validate_weibull_availability(component: Optional[str] = None) -> tuple[bool, str]:
    """
    Valida se dados Weibull estão disponíveis.
    
    Args:
        component: Componente específico para validar (opcional)
    
    Returns:
        Tuple (is_valid, message)
    """
    weibull_results = st.session_state.get("weibull_results", {})
    
    if not weibull_results:
        return False, "Execute a análise Weibull primeiro na página 'Ajuste Weibull UNIFIED'"
    
    if component and component != "Todos":
        if component not in weibull_results:
            available = list(weibull_results.keys())
            return False, f"Componente '{component}' não analisado. Disponíveis: {available}"
        
        # Verifica parâmetros essenciais
        result = weibull_results[component]
        required_params = ['lambda', 'rho']
        missing = [p for p in required_params if p not in result or result[p] is None]
        
        if missing:
            return False, f"Parâmetros Weibull incompletos para '{component}': {missing}"
    
    return True, "Dados Weibull válidos"

def reset_downstream_data(from_step: str):
    """
    Limpa dados downstream quando etapas anteriores são alteradas.
    
    Args:
        from_step: 'dataset', 'weibull', 'planning'
    """
    if from_step == 'dataset':
        st.session_state.weibull_results = {}
        st.session_state.data_quality_report = {}
        reset_downstream_data('weibull')
        
    elif from_step == 'weibull':
        # Limpa resultados de planejamento
        keys_to_reset = [
            'maintenance_strategy_Todos_Todos_Motor',
            'inventory_strategy_Todos_Todos_Motor', 
            'scenarios_Todos_Todos_Motor',
            'scenarios_Todos_Todos_Todos'
        ]
        for key in keys_to_reset:
            if key in st.session_state:
                st.session_state[key] = None if 'strategy' not in key else {}

def get_available_components() -> list:
    """Retorna lista de componentes com análise Weibull disponível."""
    return list(st.session_state.get("weibull_results", {}).keys())
