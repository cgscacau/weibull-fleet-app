"""
Página de teste para verificar funcionalidade
"""
import streamlit as st
import sys
from pathlib import Path

# Adicionar raiz ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

st.set_page_config(
    page_title="Teste - Weibull Fleet Analytics",
    page_icon="🧪",
    layout="wide"
)

st.title("🧪 Página de Teste")

st.success("✅ Esta página está carregando corretamente!")

# Testar imports
st.markdown("## 📦 Teste de Módulos")

col1, col2 = st.columns(2)

with col1:
    try:
        from core.weibull import WeibullAnalysis
        st.success("✅ core.weibull importado")
    except Exception as e:
        st.error(f"❌ Erro: {e}")
    
    try:
        from dataops.clean import DataCleaner
        st.success("✅ dataops.clean importado")
    except Exception as e:
        st.error(f"❌ Erro: {e}")

with col2:
    try:
        from ai.ai_assistant import WeibullAIAssistant
        st.success("✅ ai.ai_assistant importado")
    except Exception as e:
        st.error(f"❌ Erro: {e}")
    
    try:
        import pandas as pd
        df = pd.read_csv(project_root / "storage" / "sample_fleet_data.csv")
        st.success(f"✅ Dados carregados: {len(df)} registros")
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {e}")

# Testar botão simples
st.markdown("---")
st.markdown("## 🔘 Teste de Interatividade")

if st.button("🎯 Clique Aqui para Testar"):
    st.balloons()
    st.success("✅ Botão funcionando perfeitamente!")
    
    # Criar contador no session_state
    if 'clicks' not in st.session_state:
        st.session_state.clicks = 0
    
    st.session_state.clicks += 1
    st.info(f"Você clicou {st.session_state.clicks} vez(es)")

# Testar input
st.markdown("---")
st.markdown("## 📝 Teste de Input")

user_input = st.text_input("Digite algo aqui:")
if user_input:
    st.write(f"Você digitou: **{user_input}**")

# Testar slider
valor = st.slider("Teste de Slider", 0, 100, 50)
st.write(f"Valor do slider: {valor}")

# Informações do sistema
st.markdown("---")
st.markdown("## 🔍 Informações do Sistema")

st.code(f"""
Python Path: {sys.path[:3]}
Project Root: {project_root}
Working Dir: {Path.cwd()}
""")

st.markdown("""
### 📋 Próximos Passos

Se você vê esta página e os botões funcionam:
1. ✅ O sistema está funcionando
2. ✅ Navegue para outras páginas usando o menu lateral (seta >)
3. ✅ Comece pelo "🗂️ Dados" para carregar dados
""")
