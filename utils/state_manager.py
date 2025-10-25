import streamlit as st
import pandas as pd

def initialize_session_state():
    """Garante que todas as variáveis essenciais estejam inicializadas"""
    defaults = {
        "dataset": None,
        "weibull_results": {},
        "data_quality_report": {},
        "standardization_report": {},
        "selected_component": None,
        "selected_fleet": "Todos",
        "ai_explanations": {}
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value
