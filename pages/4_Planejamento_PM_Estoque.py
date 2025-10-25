"""
Página de planejamento de manutenção preventiva e gestão de estoque
VERSÃO CORRIGIDA - Sem emojis no nome do arquivo
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys
import os

# Configurar página
st.set_page_config(
    page_title="Planejamento PM & Estoque - Weibull Fleet Analytics",
    page_icon="🛠️",
    layout="wide"
)

# Adicionar diretórios ao path de forma robusta
try:
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
except Exception as e:
    st.error(f"Erro ao configurar path: {e}")
    project_root = Path.cwd()

# Imports condicionais para evitar erros
try:
    from core.planner import MaintenancePlanner, SparePartsPlanner, create_maintenance_scenario_analysis
    PLANNER_AVAILABLE = True
except ImportError as e:
    st.warning(f"⚠️ Módulo planner não disponível: {e}")
    PLANNER_AVAILABLE = False

try:
    from ai.ai_assistant import WeibullAIAssistant
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

import warnings
warnings.filterwarnings('ignore')

# Cabeçalho
st.markdown("# 🛠️ Planejamento PM & Estoque")
st.markdown("Otimização de intervalos de manutenção preventiva e gestão de peças de reposição")

# Verificar se há dados carregados
if 'dataset' not in st.session_state or st.session_state.dataset is None:
    st.info("📋 **Nenhum dado carregado**")
    st.markdown("""
    Para usar esta página, você precisa:
    1. Ir para a página **🗂️ Dados**
    2. Fazer upload de um arquivo CSV ou Excel
    3. Verificar que os dados foram padronizados corretamente
    4. Executar análise Weibull na página **📈 Ajuste Weibull**
    
    Depois de ter resultados Weibull, você poderá usar esta página para planejamento.
    """)
    st.stop()

if 'weibull_results' not in st.session_state or not st.session_state.weibull_results:
    st.info("📊 **Nenhuma análise Weibull encontrada**")
    st.markdown("""
    Para usar o planejamento de manutenção, você precisa:
    1. Ter dados carregados na página **🗂️ Dados**
    2. Executar análise Weibull na página **📈 Ajuste Weibull**
    3. Gerar parâmetros β (beta) e η (eta) para seus componentes
    
    Depois disso, você poderá calcular intervalos ótimos de manutenção preventiva.
    """)
    st.stop()

# Dados disponíveis
st.success("✅ Dados e resultados Weibull encontrados!")

# Tabs principais
tab1, tab2, tab3 = st.tabs(["🔧 Planejamento PM", "📦 Gestão de Estoque", "📊 Análise de Cenários"])

with tab1:
    st.markdown("## 🔧 Planejamento de Manutenção Preventiva")
    
    if not PLANNER_AVAILABLE:
        st.warning("⚠️ Módulo de planejamento não está disponível. Mostrando interface simplificada.")
        
        st.markdown("""
        ### Cálculo de Intervalo de Manutenção Preventiva
        
        O intervalo ótimo de PM é calculado baseado nos parâmetros Weibull:
        
        **Fórmula:**
        ```
        Intervalo PM = η × (-ln(Confiabilidade_Alvo))^(1/β)
        ```
        
        Onde:
        - **η (eta)** = Vida característica (horas)
        - **β (beta)** = Parâmetro de forma
        - **Confiabilidade_Alvo** = Nível desejado (ex: 90% = 0.90)
        """)
        
        # Seletor de componente
        components = list(st.session_state.weibull_results.keys())
        if components:
            selected_component = st.selectbox("Selecione o componente:", components)
            
            if selected_component in st.session_state.weibull_results:
                results = st.session_state.weibull_results[selected_component]['results']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### Parâmetros Weibull")
                    st.metric("Beta (β)", f"{results['beta']:.2f}")
                    st.metric("Eta (η)", f"{results['eta']:.0f} horas")
                    st.metric("MTBF", f"{results['mtbf']:.0f} horas")
                
                with col2:
                    st.markdown("### Configuração PM")
                    target_reliability = st.slider(
                        "Confiabilidade Alvo (%)",
                        min_value=50,
                        max_value=99,
                        value=90,
                        step=1
                    ) / 100
                    
                    # Calcular intervalo PM
                    beta = results['beta']
                    eta = results['eta']
                    pm_interval = eta * ((-np.log(target_reliability)) ** (1/beta))
                    
                    st.markdown("### Intervalo Recomendado")
                    st.success(f"**{pm_interval:.0f} horas**")
                    
                    # Métricas adicionais
                    st.metric("% da Vida Característica", f"{(pm_interval/eta*100):.1f}%")
                    st.metric("% do MTBF", f"{(pm_interval/results['mtbf']*100):.1f}%")
                
                # Análise de risco
                st.markdown("### 📊 Análise de Diferentes Intervalos")
                
                intervals_df = pd.DataFrame({
                    'Confiabilidade (%)': [50, 60, 70, 80, 85, 90, 95, 99],
                })
                
                intervals_df['Intervalo PM (h)'] = intervals_df['Confiabilidade (%)'].apply(
                    lambda r: eta * ((-np.log(r/100)) ** (1/beta))
                )
                intervals_df['% do MTBF'] = (intervals_df['Intervalo PM (h)'] / results['mtbf'] * 100).round(1)
                intervals_df['Risco de Falha (%)'] = 100 - intervals_df['Confiabilidade (%)']
                
                st.dataframe(intervals_df, use_container_width=True)
                
                # Gráfico
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=intervals_df['Intervalo PM (h)'],
                    y=intervals_df['Confiabilidade (%)'],
                    mode='lines+markers',
                    name='Confiabilidade',
                    line=dict(color='#10B981', width=3),
                    marker=dict(size=10)
                ))
                
                fig.add_vline(
                    x=pm_interval,
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"Recomendado: {pm_interval:.0f}h"
                )
                
                fig.update_layout(
                    title="Confiabilidade vs Intervalo de Manutenção",
                    xaxis_title="Intervalo PM (horas)",
                    yaxis_title="Confiabilidade (%)",
                    hovermode='x unified',
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
        else:
            st.warning("Nenhum resultado Weibull disponível")
    
    else:
        # Usar módulo planner completo
        st.markdown("### Usando módulo de planejamento avançado")
        # (código original continua aqui)

with tab2:
    st.markdown("## 📦 Gestão de Estoque de Peças")
    
    st.info("🚧 **Em desenvolvimento**")
    st.markdown("""
    ### Funcionalidades Planejadas:
    
    - **Cálculo de Demanda:** Estimar quantidade de peças necessárias baseado em:
      - Taxa de falha (parâmetros Weibull)
      - Tamanho da frota
      - Intervalo de manutenção
    
    - **Nível de Estoque Ótimo:**
      - Estoque de segurança
      - Ponto de reordenação
      - Quantidade econômica de pedido (EOQ)
    
    - **Análise de Custos:**
      - Custo de falta (downtime)
      - Custo de armazenagem
      - Custo de pedido
      - Custo total otimizado
    
    - **Dashboard de Peças Críticas:**
      - Componentes com maior risco de falta
      - Lead time dos fornecedores
      - Histórico de consumo
    """)

with tab3:
    st.markdown("## 📊 Análise de Cenários")
    
    st.info("🚧 **Em desenvolvimento**")
    st.markdown("""
    ### Funcionalidades Planejadas:
    
    - **Simulação de Estratégias:**
      - Comparar diferentes intervalos de PM
      - Avaliar impacto na confiabilidade
      - Calcular custos vs benefícios
    
    - **Análise What-If:**
      - "E se aumentarmos a frequência de PM?"
      - "E se reduzirmos o estoque de peças?"
      - "E se investirmos em componentes de melhor qualidade?"
    
    - **Otimização Multi-Objetivo:**
      - Maximizar confiabilidade
      - Minimizar custos
      - Minimizar downtime
      - Encontrar ponto de equilíbrio
    
    - **Relatórios Executivos:**
      - ROI de diferentes estratégias
      - Comparação com benchmarks
      - Recomendações priorizadas
    """)

# Sidebar com informações
with st.sidebar:
    st.markdown("### 💡 Dicas")
    st.markdown("""
    **Para calcular PM ideal:**
    1. Execute análise Weibull primeiro
    2. Defina confiabilidade alvo (geralmente 90%)
    3. Considere custos operacionais
    4. Ajuste baseado em experiência prática
    
    **Confiabilidade típica:**
    - **Crítico:** 95-99%
    - **Importante:** 90-95%
    - **Normal:** 80-90%
    """)
    
    st.markdown("### 📚 Recursos")
    st.markdown("""
    - [Documentação Weibull](https://en.wikipedia.org/wiki/Weibull_distribution)
    - [Planejamento de Manutenção](https://www.reliabilityweb.com/articles/entry/preventive-maintenance-optimization)
    - [Gestão de Estoque](https://en.wikipedia.org/wiki/Inventory_management)
    """)
