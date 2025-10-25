import streamlit as st
from typing import Optional
import warnings

def safe_navigate(page_path: str, button_text: str, 
                 button_type: str = "primary", 
                 use_container_width: bool = True) -> bool:
    """
    Sistema de navegação robusto com múltiplos fallbacks.
    
    Args:
        page_path: Caminho da página (ex: "pages/1_Dados_UNIFIED.py")
        button_text: Texto do botão
        button_type: Tipo do botão ("primary", "secondary")
        use_container_width: Se deve usar largura completa
    
    Returns:
        True se navegação foi acionada
    """
    
    if st.button(button_text, type=button_type, use_container_width=use_container_width):
        
        # Método 1: st.switch_page (Streamlit >= 1.29)
        try:
            st.switch_page(page_path)
            return True
        except (AttributeError, Exception) as e:
            # Log do erro para debug
            if hasattr(st, 'error'):
                st.warning(f"Navegação automática falhou. Use o menu lateral.")
        
        # Método 2: Session state navigation
        try:
            st.session_state.navigate_to = page_path
            st.rerun()
            return True
        except Exception:
            pass
        
        # Método 3: Query parameters  
        try:
            page_name = page_path.split('/')[-1].replace('.py', '')
            st.query_params.page = page_name
            st.rerun()
            return True
        except Exception:
            pass
        
        # Fallback: Instrução manual
        st.info(f"👈 **Navegue manualmente para:** {page_path}")
        st.info("**Use a barra lateral do Streamlit para acessar a página desejada**")
        return True
    
    return False

def create_page_links():
    """Cria links de navegação como fallback universal."""
    
    st.markdown("---")
    st.subheader("📍 Navegação Manual")
    
    pages = {
        "🏠 Home": "Home.py",
        "📤 Dados UNIFIED": "pages/1_Dados_UNIFIED.py",
        "📈 Ajuste Weibull": "pages/2_Ajuste_Weibull_UNIFIED.py", 
        "🔧 Planejamento PM": "pages/3_Planejamento_PM_Estoque.py"
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Páginas Disponíveis:**")
        for name, path in pages.items():
            st.markdown(f"• {name}")
    
    with col2:
        st.markdown("**Como navegar:**")
        st.markdown("1. Use a **barra lateral** do Streamlit")
        st.markdown("2. Clique na página desejada")
        st.markdown("3. Ou execute: `streamlit run [caminho]`")

def check_streamlit_version():
    """Verifica versão do Streamlit e sugere atualizações."""
    
    try:
        import streamlit as st
        version = st.__version__
        
        # Converte versão para comparação
        version_parts = [int(x) for x in version.split('.')]
        
        if version_parts[0] < 1 or (version_parts[0] == 1 and version_parts[1] < 29):
            st.warning(f"""
            ⚠️ **Versão do Streamlit desatualizada: {version}**
            
            Recomendamos atualizar para >= 1.29.0:
            ```bash
            pip install --upgrade streamlit
            ```
            """)
            return False
        else:
            st.success(f"✅ **Streamlit {version}** - Versão compatível")
            return True
            
    except Exception as e:
        st.error(f"Erro ao verificar versão: {e}")
        return False
