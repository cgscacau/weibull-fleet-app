"""
Página de análise Weibull
"""
import streamlit as st
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Adicionar raiz ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from core.weibull import WeibullAnalysis
except ImportError:
    st.error("❌ Erro ao importar módulo Weibull")
    st.stop()

st.set_page_config(
    page_title="Análise Weibull",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Análise Weibull")

# Verificar dados
if 'dataset' not in st.session_state or st.session_state.dataset is None:
    st.warning("📥 Carregue os dados primeiro na página 'Dados'")
    st.stop()

df = st.session_state.dataset

# Filtros
st.sidebar.markdown("## 🎛️ Filtros")

# Selecionar componente
if 'component' in df.columns:
    components = ["Todos"] + sorted(df['component'].unique().tolist())
    selected_component = st.sidebar.selectbox("Componente", components)
    
    if selected_component != "Todos":
        df_filtered = df[df['component'] == selected_component]
    else:
        df_filtered = df
else:
    st.error("❌ Coluna 'component' não encontrada nos dados")
    st.stop()

# Preparar dados para análise
if 'operating_hours' not in df_filtered.columns:
    st.error("❌ Coluna 'operating_hours' não encontrada")
    st.stop()

times = df_filtered['operating_hours'].dropna().values

if 'censored' in df_filtered.columns:
    censored = df_filtered['censored'].values[:len(times)]
else:
    censored = np.zeros(len(times), dtype=bool)

# Verificar quantidade mínima
n_failures = np.sum(~censored)

st.markdown(f"""
### 📊 Dados Selecionados

**Componente:** {selected_component}  
**Total de registros:** {len(times)}  
**Falhas observadas:** {n_failures}  
**Taxa de censura:** {(1 - n_failures/len(times))*100:.1f}%
""")

if n_failures < 3:
    st.error(f"❌ Necessário pelo menos 3 falhas observadas. Encontradas: {n_failures}")
    st.stop()

# Executar análise
if st.button("📈 Executar Análise Weibull", type="primary"):
    with st.spinner("Ajustando distribuição Weibull..."):
        try:
            weibull = WeibullAnalysis()
            results = weibull.fit_mle(times, censored)
            
            # Salvar resultados
            if 'weibull_results' not in st.session_state:
                st.session_state.weibull_results = {}
            
            st.session_state.weibull_results[selected_component] = {
                'results': results,
                'weibull_obj': weibull
            }
            
            st.success("✅ Análise concluída!")
            
            # Mostrar resultados
            st.markdown("---")
            st.markdown("## 📋 Resultados")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("β (Forma)", f"{results['beta']:.2f}")
            
            with col2:
                st.metric("η (Escala)", f"{results['eta']:.0f}h")
            
            with col3:
                st.metric("MTBF", f"{results['mtbf']:.0f}h")
            
            with col4:
                st.metric("AIC", f"{results['aic']:.1f}")
            
            # Interpretação
            st.markdown("### 🔍 Interpretação")
            
            beta = results['beta']
            if beta < 0.8:
                tipo_falha = "🔵 Falhas Infantis"
                desc = "Taxa de falha decrescente - problemas de qualidade/instalação"
            elif beta < 1.2:
                tipo_falha = "🟡 Falhas Aleatórias"
                desc = "Taxa de falha constante - falhas por acaso"
            else:
                tipo_falha = "🔴 Falhas por Desgaste"
                desc = "Taxa de falha crescente - desgaste normal"
            
            st.info(f"""
            **Tipo de Falha:** {tipo_falha}
            
            {desc}
            
            **Vida Característica (η):** {results['eta']:.0f} horas  
            (63.2% dos componentes falham até este tempo)
            
            **MTBF:** {results['mtbf']:.0f} horas  
            (Tempo médio até falha)
            """)
            
            # Gráfico
            try:
                fig = weibull.create_probability_plot(times, censored)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"⚠️ Não foi possível gerar gráfico: {e}")
        
        except Exception as e:
            st.error(f"❌ Erro na análise: {e}")
            import traceback
            st.code(traceback.format_exc())

# Mostrar resultados salvos
if 'weibull_results' in st.session_state and selected_component in st.session_state.weibull_results:
    st.markdown("---")
    st.success("✅ Resultados anteriores disponíveis para este componente")
    
    if st.button("📊 Ver Resultados Anteriores"):
        saved_results = st.session_state.weibull_results[selected_component]['results']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("β", f"{saved_results['beta']:.2f}")
        with col2:
            st.metric("η", f"{saved_results['eta']:.0f}h")
        with col3:
            st.metric("MTBF", f"{saved_results['mtbf']:.0f}h")
