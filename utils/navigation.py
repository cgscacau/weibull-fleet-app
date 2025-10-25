"""
Sistema de navegação robusto para Streamlit com múltiplos fallbacks.
"""

import streamlit as st
from typing import Optional
import warnings

def handle_navigation():
    """
    Processa navegação pendente armazenada no session state.
    Deve ser chamada no início de cada página, logo após st.set_page_config().
    """
    if st.session_state.get("navigation_triggered", False):
        page_path = st.session_state.get("navigate_to")
        
        if page_path:
            # Limpa flags
            st.session_state.navigation_triggered = False
            st.session_state.navigate_to = None
            
            # Executa navegação
            try:
                st.switch_page(page_path)
            except Exception as e:
                st.error(f"Erro ao navegar: {str(e)}")
                st.info(f"👈 Use a barra lateral para acessar: **{page_path}**")

def create_navigation_button(page_path: str, button_text: str, 
                            button_type: str = "primary", 
                            use_container_width: bool = True,
                            key: Optional[str] = None) -> bool:
    """
    Cria um botão de navegação que armazena a intenção no session state.
    
    Args:
        page_path: Caminho da página (ex: "pages/1_Dados_UNIFIED.py")
        button_text: Texto do botão
        button_type: Tipo do botão ("primary", "secondary")
        use_container_width: Se deve usar largura completa
        key: Chave única para o botão
    
    Returns:
        True se botão foi clicado
    """
    # Gera key única se não fornecida
    if key is None:
        key = f"nav_btn_{page_path.replace('/', '_').replace('.py', '')}"
    
    # Cria o botão
    if st.button(button_text, type=button_type, use_container_width=use_container_width, key=key):
        # Armazena no session state
        st.session_state.navigate_to = page_path
        st.session_state.navigation_triggered = True
        return True
    
    return False

def safe_navigate(page_path: str, button_text: str, 
                 button_type: str = "primary", 
                 use_container_width: bool = True,
                 key: Optional[str] = None) -> bool:
    """
    Alias para create_navigation_button (compatibilidade com código antigo).
    """
    return create_navigation_button(page_path, button_text, button_type, use_container_width, key)

def create_page_navigation_links():
    """
    Cria seção com instruções de navegação manual.
    """
    st.markdown("---")
    st.markdown("### 📍 Navegação Manual")
    
    st.info("""
    **Como navegar entre páginas:**
    
    1. Use a **barra lateral** (clique no ☰ no canto superior esquerdo)
    2. Selecione a página desejada no menu
    3. A página será carregada automaticamente
    """)
    
    pages_info = {
        "🏠 Home": ("Home.py", "Página inicial do sistema"),
        "📤 Dados UNIFIED": ("pages/1_Dados_UNIFIED.py", "Carregamento de dados"),
        "📈 Ajuste Weibull": ("pages/2_Ajuste_Weibull_UNIFIED.py", "Análise de confiabilidade"), 
        "🔧 Planejamento PM": ("pages/3_Planejamento_PM_Estoque.py", "Otimização de manutenção")
    }
    
    st.markdown("**Páginas Disponíveis:**")
    for name, (path, description) in pages_info.items():
        st.markdown(f"• **{name}** - {description}")

def check_streamlit_version():
    """
    Verifica versão do Streamlit e exibe informações.
    """
    try:
        version = st.__version__
        version_parts = [int(x) for x in version.split('.')]
        
        if version_parts[0] < 1 or (version_parts[0] == 1 and version_parts[1] < 29):
            st.warning(f"""
            ⚠️ **Versão do Streamlit: {version}**
            
            Recomendamos atualizar para >= 1.29.0 para melhor suporte à navegação:
            ```bash
            pip install --upgrade streamlit>=1.29.0
            ```
            """)
            return False
        else:
            st.success(f"✅ Streamlit {version} - Versão compatível")
            return True
            
    except Exception as e:
        st.error(f"Erro ao verificar versão: {e}")
        return False
