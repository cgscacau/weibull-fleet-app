"""
Página principal de análise Weibull - VERSÃO UNIFICADA
Trabalha com dados padronizados pelo column_mapper
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys


from utils.state_manager import initialize_session_state
initialize_session_state()

# Adicionar diretórios ao path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from core.weibull import WeibullAnalysis, compare_distributions
from ai.ai_assistant import WeibullAIAssistant
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="Análise Weibull - Weibull Fleet Analytics",
    page_icon="📈",
    layout="wide"
)

st.markdown("# 📈 Análise Weibull")
st.markdown("Ajuste de distribuição Weibull e análise de confiabilidade")

# Inicializar session state
if 'weibull_results' not in st.session_state:
    st.session_state.weibull_results = {}
if 'ai_explanations' not in st.session_state:
    st.session_state.ai_explanations = {}


def filter_data_for_analysis(df, fleet=None, component=None, subsystem=None):
    """Filtrar dados para análise"""
    filtered_df = df.copy()
    
    if fleet and fleet != "Todos":
        if 'fleet' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['fleet'] == fleet]
    
    if subsystem and subsystem != "Todos":
        if 'subsystem' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['subsystem'] == subsystem]
    
    if component and component != "Todos":
        if 'component_type' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['component_type'] == component]
    
    return filtered_df


def prepare_weibull_data(df):
    """
    Preparar dados para análise Weibull
    Trabalha com schema padronizado: failure_time, censored
    """
    # Verificar se há colunas necessárias
    if 'failure_time' not in df.columns:
        return None, None
    
    # Remover valores nulos e negativos
    df_clean = df.dropna(subset=['failure_time'])
    df_clean = df_clean[df_clean['failure_time'] > 0]
    
    if len(df_clean) == 0:
        return None, None
    
    times = df_clean['failure_time'].values
    
    # Pegar coluna censored (já deve existir após padronização)
    if 'censored' in df_clean.columns:
        censored = df_clean['censored'].values
    else:
        # Fallback: assumir todas falhas observadas
        censored = np.zeros(len(times), dtype=bool)
    
    return times, censored


def display_weibull_parameters(results):
    """Exibir parâmetros Weibull em cards"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "β (Forma)", 
            f"{results['beta']:.2f}",
            delta=f"CI: {results['beta_ci_lower']:.2f}-{results['beta_ci_upper']:.2f}"
        )
    
    with col2:
        st.metric(
            "η (Escala)", 
            f"{results['eta']:.0f}h",
            delta=f"CI: {results['eta_ci_lower']:.0f}-{results['eta_ci_upper']:.0f}h"
        )
    
    with col3:
        st.metric(
            "MTBF", 
            f"{results['mtbf']:.0f}h",
            delta=f"n={results['sample_size']}"
        )
    
    with col4:
        censoring_pct = results['censoring_rate'] * 100
        st.metric(
            "Taxa de Censura", 
            f"{censoring_pct:.1f}%",
            delta=f"AIC: {results['aic']:.1f}"
        )


def interpret_beta_value(beta):
    """Interpretar valor de beta"""
    if beta < 0.8:
        return "🔵 Falhas Infantis", "Taxa de falha decrescente - problemas de qualidade/instalação"
    elif beta < 1.2:
        return "🟡 Falhas Aleatórias", "Taxa de falha constante - falhas por acaso"
    elif beta < 3.0:
        return "🔴 Falhas por Desgaste", "Taxa de falha crescente - desgaste normal"
    else:
        return "🟣 Desgaste Acelerado", "Taxa de falha muito crescente - desgaste severo"


def create_weibull_summary_card(component, results):
    """Criar card resumo da análise"""
    beta_type, beta_desc = interpret_beta_value(results['beta'])
    
    return f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 1.5rem; border-radius: 10px; color: white; margin: 1rem 0;">
        <h3>🔧 {component}</h3>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem;">
            <div>
                <strong>Tipo de Falha:</strong><br>
                {beta_type}<br>
                <small>{beta_desc}</small>
            </div>
            <div>
                <strong>Vida Característica:</strong><br>
                {results['eta']:.0f} horas<br>
                <small>63.2% falham até este tempo</small>
            </div>
            <div>
                <strong>MTBF:</strong><br>
                {results['mtbf']:.0f} horas<br>
                <small>Tempo médio até falha</small>
            </div>
            <div>
                <strong>Qualidade do Ajuste:</strong><br>
                {"✅ Bom" if results.get('convergence', False) else "⚠️ Verificar"}<br>
                <small>AIC: {results['aic']:.1f}</small>
            </div>
        </div>
    </div>
    """


def main():
    # Verificar se há dados carregados
    if 'dataset' not in st.session_state or st.session_state.dataset is None:
        st.warning("⚠️ Nenhum dado carregado!")
        st.info("📥 Por favor, vá para a página '🗂️ Dados' e carregue um arquivo primeiro.")
        
        # Botão para navegar
        st.markdown("### 👉 Como Proceder:")
        st.markdown("""
        1. Clique em **'🗂️ Dados'** no menu lateral
        2. Faça upload do seu arquivo CSV ou Excel
        3. Aguarde a padronização automática
        4. Volte para esta página para análise
        """)
        return
    
    df = st.session_state.dataset
    
    # Validar que dados estão no formato correto
    required_columns = ['component_id', 'component_type', 'failure_time', 'censored']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        st.error(f"❌ **Erro de Formato:** Colunas obrigatórias faltando: {', '.join(missing_columns)}")
        st.warning("⚠️ Os dados não estão no formato padronizado. Volte para a página de Dados e recarregue o arquivo.")
        return
    
    # Sidebar com filtros
    with st.sidebar:
        st.markdown("## 🎛️ Filtros de Análise")
        
        # Filtro por frota
        frotas_disponiveis = ["Todos"]
        if 'fleet' in df.columns:
            frotas_disponiveis += sorted(df['fleet'].dropna().unique().tolist())
        selected_fleet = st.selectbox("Frota", frotas_disponiveis)
        
        # Filtro por subsistema
        df_filtered = df if selected_fleet == "Todos" else df[df['fleet'] == selected_fleet] if 'fleet' in df.columns else df
        subsistemas_disponiveis = ["Todos"]
        if 'subsystem' in df_filtered.columns:
            subsistemas_disponiveis += sorted(df_filtered['subsystem'].dropna().unique().tolist())
        selected_subsystem = st.selectbox("Subsistema", subsistemas_disponiveis)
        
        # Filtro por componente
        df_filtered = filter_data_for_analysis(df, selected_fleet, None, selected_subsystem)
        componentes_disponiveis = ["Todos"]
        if 'component_type' in df_filtered.columns:
            componentes_disponiveis += sorted(df_filtered['component_type'].dropna().unique().tolist())
        selected_component = st.selectbox("Componente", componentes_disponiveis)
        
        st.markdown("---")
        st.markdown("## ⚙️ Configurações")
        
        confidence_level = st.slider("Nível de Confiança", 0.8, 0.99, 0.95, 0.01)
        show_individual_points = st.checkbox("Mostrar Pontos Individuais", True)
        show_confidence_bands = st.checkbox("Mostrar Bandas de Confiança", True)
        
        st.markdown("---")
        st.markdown(f"""
        ### 📊 Dados Selecionados
        **Frota:** {selected_fleet}  
        **Subsistema:** {selected_subsystem}  
        **Componente:** {selected_component}
        """)
    
    # Filtrar dados
    df_analysis = filter_data_for_analysis(df, selected_fleet, selected_component, selected_subsystem)
    
    if len(df_analysis) == 0:
        st.error("❌ Nenhum dado encontrado com os filtros selecionados")
        st.info("💡 Tente ajustar os filtros no menu lateral")
        return
    
    # Preparar dados para Weibull
    times, censored = prepare_weibull_data(df_analysis)
    
    if times is None or len(times) == 0:
        st.error("❌ Dados insuficientes para análise Weibull após limpeza")
        st.info(f"📊 Registros após filtros: {len(df_analysis)}")
        return
    
    # Verificar quantidade mínima de falhas
    n_failures = np.sum(~censored) if censored is not None else len(times)
    
    if n_failures < 3:
        st.error(f"❌ Necessário pelo menos 3 falhas observadas. Encontradas: {n_failures}")
        st.info("💡 Tente selecionar um filtro diferente ou usar mais dados")
        return
    
    st.success(f"✅ Dados preparados: {len(times)} registros, {n_failures} falhas observadas")
    
    # Tabs principais
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 Ajuste Principal", "📊 Gráficos", "🔍 Comparação de Modelos", "🤖 Análise IA"])
    
    with tab1:
        st.markdown("## 🎯 Análise Weibull Principal")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.button("📈 Executar Análise Weibull", type="primary"):
                with st.spinner("Ajustando distribuição Weibull..."):
                    try:
                        # Executar análise
                        weibull = WeibullAnalysis()
                        results = weibull.fit_mle(times, censored)
                        
                        # Salvar resultados
                        analysis_key = f"{selected_fleet}_{selected_subsystem}_{selected_component}"
                        st.session_state.weibull_results[analysis_key] = {
                            'component': selected_component,
                            'results': results,
                            'weibull_obj': weibull,
                            'data': {'times': times, 'censored': censored}
                        }
                        
                        st.success("✅ Análise concluída com sucesso!")
                        
                    except Exception as e:
                        st.error(f"❌ Erro na análise: {str(e)}")
                        st.exception(e)
        
        with col2:
            st.markdown("""
            **Sobre a Análise:**
            - Ajuste por MLE (Maximum Likelihood)
            - Tratamento automático de censura
            - Intervalos de confiança
            - Validação de convergência
            """)
        
        # Exibir resultados se disponíveis
        analysis_key = f"{selected_fleet}_{selected_subsystem}_{selected_component}"
        
        if analysis_key in st.session_state.weibull_results:
            results_data = st.session_state.weibull_results[analysis_key]
            results = results_data['results']
            weibull_obj = results_data['weibull_obj']
            
            st.markdown("---")
            
            # Card resumo
            st.markdown(create_weibull_summary_card(selected_component, results), unsafe_allow_html=True)
            
            # Parâmetros detalhados
            st.markdown("### 📋 Parâmetros Detalhados")
            display_weibull_parameters(results)
            
            # Interpretação
            st.markdown("### 🔍 Interpretação")
            
            beta_type, beta_desc = interpret_beta_value(results['beta'])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                **Tipo de Falha:** {beta_type}
                
                {beta_desc}
                
                **Implicações:**
                - β = {results['beta']:.2f}
                - {'Manutenção preventiva recomendada' if results['beta'] > 1.2 else 'Investigar causas de falha prematura' if results['beta'] < 0.8 else 'Manutenção por condição adequada'}
                """)
            
            with col2:
                # Recomendações de manutenção
                if results['beta'] > 1.2:  # Desgaste
                    pm_interval_70 = results['eta'] * ((-np.log(0.7))**(1/results['beta']))
                    pm_interval_80 = results['eta'] * ((-np.log(0.8))**(1/results['beta']))
                    
                    st.markdown(f"""
                    **Intervalos de Manutenção Sugeridos:**
                    - **Conservador (80% confiabilidade):** {pm_interval_80:.0f}h
                    - **Balanceado (70% confiabilidade):** {pm_interval_70:.0f}h
                    - **Vida característica:** {results['eta']:.0f}h
                    """)
                else:
                    st.markdown("""
                    **Recomendações:**
                    - Investigar causas raiz das falhas
                    - Melhorar controle de qualidade
                    - Considerar manutenção por condição
                    """)
    
    with tab2:
        st.markdown("## 📊 Gráficos de Análise")
        
        if analysis_key in st.session_state.weibull_results:
            results_data = st.session_state.weibull_results[analysis_key]
            weibull_obj = results_data['weibull_obj']
            data = results_data['data']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📈 Gráfico de Probabilidade Weibull")
                try:
                    fig_prob = weibull_obj.create_probability_plot(data['times'], data['censored'])
                    st.plotly_chart(fig_prob, use_container_width=True)
                except Exception as e:
                    st.error(f"Erro ao criar gráfico: {str(e)}")
            
            with col2:
                st.markdown("### 📉 Funções de Confiabilidade")
                try:
                    fig_reliability = weibull_obj.create_reliability_curves()
                    st.plotly_chart(fig_reliability, use_container_width=True)
                except Exception as e:
                    st.error(f"Erro ao criar gráfico: {str(e)}")
            
            # Gráfico de densidade e histograma
            st.markdown("### 📊 Distribuição dos Dados")
            
            fig_hist = go.Figure()
            
            # Histograma dos dados
            fig_hist.add_trace(go.Histogram(
                x=data['times'][~data['censored']] if data['censored'] is not None else data['times'],
                name='Falhas Observadas',
                opacity=0.7,
                nbinsx=20
            ))
            
            # PDF teórica
            if weibull_obj.fitted:
                x_pdf = np.linspace(min(data['times']), max(data['times']), 100)
                y_pdf = [weibull_obj.pdf(x) for x in x_pdf]
                
                # Normalizar para escala do histograma
                scale_factor = len(data['times']) * (max(data['times']) - min(data['times'])) / 20
                y_pdf_scaled = [y * scale_factor for y in y_pdf]
                
                fig_hist.add_trace(go.Scatter(
                    x=x_pdf,
                    y=y_pdf_scaled,
                    mode='lines',
                    name='PDF Weibull Ajustada',
                    line=dict(color='red', width=2)
                ))
            
            fig_hist.update_layout(
                title='Distribuição dos Tempos de Falha',
                xaxis_title='Tempo (horas)',
                yaxis_title='Frequência',
                template='plotly_white'
            )
            
            st.plotly_chart(fig_hist, use_container_width=True)
        
        else:
            st.info("🎯 Execute a análise na aba 'Ajuste Principal' primeiro")
    
    with tab3:
        st.markdown("## 🔍 Comparação de Modelos")
        
        if st.button("🔄 Comparar Distribuições", type="secondary"):
            with st.spinner("Comparando modelos..."):
                try:
                    comparison_results = compare_distributions(times, censored)
                    
                    # Criar DataFrame para exibição
                    comparison_df = []
                    for model, results in comparison_results.items():
                        if 'error' not in results:
                            comparison_df.append({
                                'Modelo': model,
                                'AIC': results['aic'],
                                'BIC': results['bic'],
                                'Log-Likelihood': results['log_likelihood'],
                                'MTBF': results['mtbf'],
                                'Parâmetros': str(results['parameters'])
                            })
                    
                    if comparison_df:
                        df_comparison = pd.DataFrame(comparison_df)
                        df_comparison = df_comparison.sort_values('AIC')  # Menor AIC é melhor
                        
                        st.markdown("### 📊 Comparação de Modelos")
                        st.dataframe(df_comparison, use_container_width=True)
                        
                        # Recomendação
                        best_model = df_comparison.iloc[0]['Modelo']
                        st.success(f"✅ **Modelo Recomendado:** {best_model} (menor AIC)")
                        
                        # Gráfico de comparação AIC
                        fig_aic = px.bar(
                            df_comparison, 
                            x='Modelo', 
                            y='AIC',
                            title='Comparação AIC (menor é melhor)',
                            color='AIC',
                            color_continuous_scale='RdYlGn_r'
                        )
                        st.plotly_chart(fig_aic, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"❌ Erro na comparação: {str(e)}")
    
    with tab4:
        st.markdown("## 🤖 Análise com IA")
        
        if analysis_key in st.session_state.weibull_results:
            results_data = st.session_state.weibull_results[analysis_key]
            results = results_data['results']
            
            if st.button("🧠 Gerar Explicação IA", type="primary"):
                with st.spinner("IA analisando resultados..."):
                    try:
                        # Inicializar assistente IA
                        ai_assistant = WeibullAIAssistant()
                        
                        # Gerar explicação
                        explanation = ai_assistant.explain_weibull_results(
                            beta=results['beta'],
                            eta=results['eta'],
                            component=selected_component,
                            context={
                                'sample_size': results['sample_size'],
                                'censoring_rate': results['censoring_rate'],
                                'mtbf': results['mtbf'],
                                'fleet': selected_fleet,
                                'subsystem': selected_subsystem
                            }
                        )
                        
                        if explanation.success:
                            st.session_state.ai_explanations[analysis_key] = explanation
                            
                            st.markdown("### 🤖 Explicação da IA")
                            st.markdown(explanation.content)
                            
                            if explanation.suggestions:
                                st.markdown("### 💡 Sugestões da IA")
                                for suggestion in explanation.suggestions:
                                    st.info(f"💡 {suggestion}")
                        else:
                            st.error(f"❌ Erro na análise IA: {explanation.content}")
                    
                    except Exception as e:
                        st.error(f"❌ Erro ao chamar IA: {str(e)}")
            
            # Exibir explicação salva
            if analysis_key in st.session_state.ai_explanations:
                explanation = st.session_state.ai_explanations[analysis_key]
                
                st.markdown("---")
                st.markdown("### 🤖 Última Análise IA")
                
                with st.expander("Ver Explicação Completa", expanded=True):
                    st.markdown(explanation.content)
                    
                    if explanation.suggestions:
                        st.markdown("**Sugestões:**")
                        for suggestion in explanation.suggestions:
                            st.info(f"💡 {suggestion}")
        
        else:
            st.info("🎯 Execute a análise Weibull primeiro")
    
    # Botões de navegação
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("⬅️ Voltar aos Dados"):
            st.info("Use o menu lateral para navegar para '🗂️ Dados'")
    
    with col2:
        if st.button("💾 Salvar Resultados"):
            if analysis_key in st.session_state.weibull_results:
                results = st.session_state.weibull_results[analysis_key]['results']
                
                # Criar DataFrame com resultados
                results_df = pd.DataFrame([{
                    'Component': selected_component,
                    'Fleet': selected_fleet,
                    'Subsystem': selected_subsystem,
                    'Beta': results['beta'],
                    'Eta': results['eta'],
                    'MTBF': results['mtbf'],
                    'Sample_Size': results['sample_size'],
                    'Censoring_Rate': results['censoring_rate'],
                    'AIC': results['aic'],
                    'BIC': results['bic']
                }])
                
                csv = results_df.to_csv(index=False).encode('utf-8')
                
                st.download_button(
                    label="📥 Download Resultados CSV",
                    data=csv,
                    file_name=f'weibull_results_{selected_component.replace(" ", "_")}.csv',
                    mime='text/csv'
                )
    
    with col3:
        if st.button("➡️ Planejamento PM"):
            st.info("Use o menu lateral para navegar para '🛠️ Planejamento PM & Estoque'")

if __name__ == "__main__":
    main()
