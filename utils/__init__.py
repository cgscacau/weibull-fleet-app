"""
Módulo de utilitários para o sistema de otimização PM & Estoque.
"""

# Facilita imports
from .state_manager import (
    initialize_session_state,
    display_pipeline_status,
    validate_weibull_availability,
    get_available_components,
    update_pipeline_status,
    reset_downstream_data
)

from .navigation import (
    handle_navigation,
    create_navigation_button,
    safe_navigate,
    create_page_navigation_links,
    check_streamlit_version
)

__all__ = [
    # State Manager
    'initialize_session_state',
    'display_pipeline_status',
    'validate_weibull_availability',
    'get_available_components',
    'update_pipeline_status',
    'reset_downstream_data',
    
    # Navigation
    'handle_navigation',
    'create_navigation_button',
    'safe_navigate',
    'create_page_navigation_links',
    'check_streamlit_version'
]
