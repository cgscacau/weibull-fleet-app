import streamlit as st

# === CONFIGURAÇÃO - DEVE SER A PRIMEIRA CHAMADA ===
st.set_page_config(
    page_title="Ajuste Weibull UNIFIED",
    page_icon="📈",
    layout="wide"
)

# === IMPORTS APÓS CONFIGURAÇÃO ===
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from utils.state_manager import (
    initialize_session_state, 
    display_pipeline_status, 
    reset_downstream_data
)
from utils.weibull_analysis import (
    execute_weibull_analysis,
    generate_data_quality_report,
    display_weibull_results
)
from utils.navigation import (
    handle_navigation,
    create_navigation_button
)

# === PROCESSA NAVEGAÇÃO PENDENTE ===
handle_navigation()

# === INICIALIZAÇÃO ===
initialize_session_state()

# === FUNÇÕES AUXILIARES PARA GRÁFICOS ===

def weibull_reliability_plot(lambda_param: float, rho_param: float, max_time: float = None) -> pd.DataFrame:
    """Gera dados para plotar curva de confiabilidade Weibull"""
    if max_time is None:
        max_time = lambda_param * 2
    
    times = np.linspace(0, max_time, 100)
    reliabilities = np.exp(-((times / lambda_param) ** rho_param))
    
    return pd.DataFrame({
        'Tempo (horas)': times,
        'Confiabilidade R(t)': reliabilities
    })

def weibull_hazard_rate_plot(lambda_param: float, rho_param: float, max_time: float = None) -> pd.DataFrame:
    """Gera dados para plotar taxa de falha Weibull"""
    if max_time is None:
        max_time = lambda_param * 2
    
    times = np.linspace(0.1, max_time, 100)  # Evita divisão por zero
    hazard_rates = (rho_param / lambda_param) * ((times / lambda_param) ** (rho_param - 1))
    
    return pd.DataFrame({
        'Tempo (horas)': times,
        'Taxa de Falha h(t)': hazard_rates
    })

def weibull_pdf_plot(lambda_param: float, rho_param: float, max_time: float = None) -> pd.DataFrame:
    """Gera dados para plotar função densidade de probabilidade Weibull"""
    if max_time is None:
        max_time = lambda_param * 2
    
    times = np.linspace(0.1, max_time, 100)
    pdf_values = (rho_param / lambda_param) * ((times / lambda_param) ** (rho_param - 1)) * \
                 np.exp(-((times / lambda_param) ** rho_param))
    
    return pd.DataFrame({
        'Tempo (horas)': times,
        'Densidade f(t)': pdf_values
    })

def create_histogram_data(failure_times: np.ndarray, n_bins: int = 20) -> pd.DataFrame:
    """Cria dados para histograma de tempos de falha"""
    hist, bin_edges = np.histogram(failure_times, bins=n_bins)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    
    return pd.DataFrame({
        'Tempo (horas)': bin_centers,
        'Frequência': hist
    })

# === HEADER ===
st.title("📈 Ajuste Weibull UNIFIED")
st.markdown("**Análise de confiabilidade usando distribuição Weibull para otimização de manutenção**")
st.markdown("---")

# === STATUS DO PIPELINE ===
st.subheader("📊 Status do Pipeline de Análise")
display_pipeline_status()
st.markdown("---")

# === VERIFICAÇÃO DE PRÉ-REQUISITOS ===
if st.session_state.dataset is None or st.session_state.dataset.empty:
    st.error("❌ **Dataset não carregado**")
    
    st.markdown("""
    ### 📋 **Pré-requisitos não atendidos**
    
    Para executar a análise Weibull, você precisa:
    
    1. **Carregar dados** na página "Dados UNIFIED"
    2. **Garantir formato correto** com as colunas:
       - `component_type`: Tipo do componente
       - `failure_time`: Tempo até falha (horas)
       - `censored`: Indicador de censura (0 ou 1)
       - `fleet`: Frota (opcional)
    
    3. **Ter dados suficientes**: Mínimo 3 observações por componente
    """)
    
    st.info("👈 Use a barra lateral para navegar até 'Dados UNIFIED'")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        create_navigation_button(
            "pages/1_Dados_UNIFIED.py",
            "🔄 **Ir para Dados UNIFIED**",
            key="weibull_to_dados"
        )
    
    st.stop()

# === DADOS CARREGADOS - INFORMAÇÕES ===
dataset = st.session_state.dataset
st.success(f"✅ **Dataset carregado com sucesso:** {len(dataset):,} registros")

# Estatísticas básicas do dataset
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📊 Total de Registros", f"{len(dataset):,}")

with col2:
    if 'component_type' in dataset.columns:
        n_components = dataset['component_type'].nunique()
        st.metric("🔩 Componentes Únicos", n_components)
    else:
        st.metric("🔩 Componentes Únicos", "N/A")

with col3:
    if 'failure_time' in dataset.columns:
        valid_times = pd.to_numeric(dataset['failure_time'], errors='coerce')
        if valid_times.notna().any():
            st.metric("⏱️ Tempo Médio", f"{valid_times.mean():.1f}h")
        else:
            st.metric("⏱️ Tempo Médio", "N/A")
    else:
        st.metric("⏱️ Tempo Médio", "N/A")

with col4:
    if 'fleet' in dataset.columns:
        n_fleets = dataset['fleet'].nunique()
        st.metric("🚛 Frotas", n_fleets)
    else:
        st.metric("🚛 Frotas", "N/A")

# === SIDEBAR - CONTROLES ===
with st.sidebar:
    st.header("🎛️ Controles de Análise")
    
    st.markdown("---")
    
    # === ANÁLISE DE QUALIDADE ===
    st.subheader("📋 Qualidade dos Dados")
    
    if st.button("🔍 **Analisar Qualidade**", use_container_width=True):
        with st.spinner("Analisando qualidade dos dados..."):
            quality_report = generate_data_quality_report(dataset)
            st.session_state.data_quality_report = quality_report
            st.rerun()
    
    # Exibe relatório se disponível
    quality_report = st.session_state.get("data_quality_report", {})
    
    if quality_report:
        status = quality_report.get("status", "unknown")
        
        # Mapeamento de status
        status_display = {
            "excellent": ("🟢", "Excelente"),
            "good": ("🟡", "Boa"), 
            "fair": ("🟠", "Razoável"),
            "poor": ("🔴", "Ruim"),
            "critical": ("⚫", "Crítica"),
            "empty": ("⚪", "Vazio")
        }
        
        icon, label = status_display.get(status, ("❓", "Desconhecido"))
        st.write(f"**Status:** {icon} {label}")
        
        # Problemas encontrados
        if quality_report.get("issues"):
            with st.expander("⚠️ Problemas", expanded=True):
                for issue in quality_report["issues"]:
                    st.warning(f"• {issue}")
        
        # Recomendações
        if quality_report.get("recommendations"):
            with st.expander("💡 Recomendações"):
                for rec in quality_report["recommendations"]:
                    st.info(f"• {rec}")
    
    st.markdown("---")
    
    # === EXECUÇÃO DA ANÁLISE ===
    st.subheader("🚀 Análise Weibull")
    
    # Verifica se pode executar
    can_execute = True
    
    if not quality_report:
        st.warning("Execute a análise de qualidade primeiro")
        can_execute = False
    elif quality_report.get("status") == "critical":
        st.error("Corrija problemas críticos antes de continuar")
        can_execute = False
    
    # Botão de execução
    if st.button("▶️ **Executar Análise Weibull**", 
                type="primary", 
                use_container_width=True,
                disabled=not can_execute):
        
        # Limpa dados downstream
        reset_downstream_data('weibull')
        
        # Executa análise
        with st.spinner("🔄 Executando análise Weibull..."):
            weibull_results = execute_weibull_analysis(dataset)
            
            if weibull_results:
                st.session_state.weibull_results = weibull_results
                st.session_state.analysis_timestamp = pd.Timestamp.now()
                st.success("✅ Análise concluída!")
                st.rerun()
            else:
                st.error("❌ Falha na análise")
    
    # Informação sobre última análise
    if st.session_state.get("analysis_timestamp"):
        timestamp = st.session_state.analysis_timestamp
        st.caption(f"📅 Última análise: {timestamp.strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Botão para limpar resultados
    if st.session_state.get("weibull_results"):
        st.markdown("---")
        if st.button("🗑️ **Limpar Resultados**", use_container_width=True):
            reset_downstream_data('weibull')
            st.rerun()

# === SEÇÃO PRINCIPAL - VISÃO GERAL DOS DADOS ===
st.markdown("---")
st.subheader("📊 Visão Geral dos Dados")

col1, col2 = st.columns([2, 1])

with col1:
    if 'component_type' in dataset.columns:
        st.markdown("#### 📋 Resumo por Componente")
        
        # Conta registros por componente
        component_counts = dataset['component_type'].value_counts().reset_index()
        component_counts.columns = ['Componente', 'Registros']
        
        # Adiciona coluna de adequação
        component_counts['Adequado'] = component_counts['Registros'].apply(
            lambda x: "✅ Sim" if x >= 3 else "❌ Não"
        )
        
        # Adiciona percentual
        component_counts['% do Total'] = (
            component_counts['Registros'] / len(dataset) * 100
        ).round(1).astype(str) + '%'
        
        # Exibe tabela
        st.dataframe(
            component_counts,
            use_container_width=True,
            hide_index=True
        )
        
        # Estatísticas resumidas
        total_adequate = (component_counts['Registros'] >= 3).sum()
        total_components = len(component_counts)
        
        if total_adequate == total_components:
            st.success(f"✅ **Todos os {total_components} componentes** têm dados suficientes")
        else:
            st.warning(f"⚠️ **{total_adequate} de {total_components} componentes** têm dados suficientes")

with col2:
    st.markdown("#### 📈 Distribuição")
    
    if 'component_type' in dataset.columns:
        # Gráfico de barras simples
        chart_data = dataset['component_type'].value_counts().head(10)
        st.bar_chart(chart_data)
    
    # Informações adicionais
    if 'censored' in dataset.columns:
        censored_count = dataset['censored'].sum()
        censored_pct = (censored_count / len(dataset) * 100)
        
        st.metric(
            "📊 Taxa de Censura",
            f"{censored_pct:.1f}%",
            help="Percentual de observações censuradas"
        )

# === PREVIEW DOS DADOS ===
with st.expander("👀 **Preview dos Dados Brutos**"):
    st.dataframe(dataset.head(20), use_container_width=True)

# === RESULTADOS DA ANÁLISE WEIBULL ===
st.markdown("---")
st.subheader("📈 Resultados da Análise Weibull")

weibull_results = st.session_state.get("weibull_results", {})

if weibull_results:
    # Filtra apenas resultados bem-sucedidos
    successful_results = {
        name: result for name, result in weibull_results.items() 
        if result.get('success', False)
    }
    
    failed_results = {
        name: result for name, result in weibull_results.items() 
        if not result.get('success', False)
    }
    
    if successful_results:
        st.success(f"✅ **{len(successful_results)} componentes** analisados com sucesso")
        
        # === TABELA RESUMO ===
        st.markdown("#### 📊 Tabela Resumo dos Parâmetros")
        
        summary_data = []
        for component, result in successful_results.items():
            summary_data.append({
                'Componente': component,
                'λ (Escala)': f"{result['lambda']:.4f}",
                'ρ (Forma)': f"{result['rho']:.4f}",
                'MTBF': f"{result.get('MTBF', 0):.2f}" if result.get('MTBF') else "N/A",
                'Observações': result['n_observations'],
                'Eventos': result['n_events'],
                'AIC': f"{result.get('AIC', 0):.2f}" if result.get('AIC') else "N/A"
            })
        
        df_summary = pd.DataFrame(summary_data)
        st.dataframe(df_summary, use_container_width=True, hide_index=True)
        
        # === SELETOR DE COMPONENTE PARA GRÁFICOS ===
        st.markdown("---")
        st.markdown("#### 📊 Visualizações Detalhadas por Componente")
        
        selected_comp = st.selectbox(
            "Selecione um componente para visualizar gráficos:",
            options=list(successful_results.keys()),
            key="weibull_viz_selector"
        )
        
        if selected_comp:
            result = successful_results[selected_comp]
            lambda_param = result['lambda']
            rho_param = result['rho']
            
            # Garante que MTBF não é None
            mtbf = result.get('MTBF')
            if mtbf is None or np.isnan(mtbf):
                mtbf = lambda_param  # Fallback para lambda
            
            # === MÉTRICAS DO COMPONENTE ===
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("λ (Escala)", f"{lambda_param:.4f}", help="Parâmetro de escala Weibull")
            
            with col2:
                st.metric("ρ (Forma)", f"{rho_param:.4f}", help="Parâmetro de forma Weibull")
            
            with col3:
                st.metric("MTBF", f"{mtbf:.2f}h", help="Tempo médio entre falhas")
            
            with col4:
                st.metric("Observações", result['n_observations'], help="Número de dados usados")
            
            # === INTERPRETAÇÃO DO PADRÃO DE FALHA ===
            st.markdown("---")
            
            if rho_param < 0.9:
                pattern_icon = "🔽"
                pattern_name = "Mortalidade Infantil"
                pattern_desc = "Taxa de falha **decrescente** - Falhas precoces são mais comuns"
            elif rho_param <= 1.1:
                pattern_icon = "➡️"
                pattern_name = "Taxa Constante"
                pattern_desc = "Taxa de falha **constante** - Falhas aleatórias"
            else:
                pattern_icon = "📈"
                pattern_name = "Desgaste"
                pattern_desc = "Taxa de falha **crescente** - Falhas por envelhecimento"
            
            st.info(f"""
            **{pattern_icon} Padrão de Falha Identificado: {pattern_name}**
            
            {pattern_desc}
            
            - **ρ = {rho_param:.3f}** (ρ < 1: decrescente | ρ ≈ 1: constante | ρ > 1: crescente)
            - Este padrão indica como a taxa de falha evolui ao longo do tempo
            """)
            
            # === TABS COM GRÁFICOS ===
            st.markdown("---")
            
            tab1, tab2, tab3, tab4 = st.tabs([
                "📉 Confiabilidade R(t)",
                "📈 Taxa de Falha h(t)",
                "📊 Densidade f(t)",
                "🔢 Dados Brutos"
            ])
            
            # TAB 1: CONFIABILIDADE
            with tab1:
                st.markdown("##### Função de Confiabilidade R(t)")
                st.caption("Probabilidade de o componente sobreviver até o tempo t")
                
                try:
                    reliability_data = weibull_reliability_plot(lambda_param, rho_param, mtbf * 2.5)
                    st.line_chart(reliability_data.set_index('Tempo (horas)'), height=400)
                    
                    # Métricas adicionais
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        # R(MTBF)
                        try:
                            r_mtbf = np.exp(-((mtbf / lambda_param) ** rho_param))
                            st.metric("R(MTBF)", f"{r_mtbf:.1%}", help="Confiabilidade no MTBF")
                        except:
                            st.metric("R(MTBF)", "N/A", help="Não calculável")
                    
                    with col2:
                        # B10 Life
                        try:
                            b10 = lambda_param * ((-np.log(0.9)) ** (1/rho_param))
                            st.metric("B10 Life", f"{b10:.0f}h", help="Tempo para 10% de falhas")
                        except:
                            st.metric("B10 Life", "N/A", help="Não calculável")
                    
                    with col3:
                        # Vida Mediana
                        try:
                            median = lambda_param * (np.log(2) ** (1/rho_param))
                            st.metric("Vida Mediana", f"{median:.0f}h", help="Tempo para 50% de falhas")
                        except:
                            st.metric("Vida Mediana", "N/A", help="Não calculável")
                    
                except Exception as e:
                    st.error(f"Erro ao gerar gráfico de confiabilidade: {str(e)}")
                
                with st.expander("ℹ️ Como interpretar"):
                    st.markdown("""
                    **Função de Confiabilidade R(t):**
                    - **Eixo Y:** Probabilidade de sobrevivência (0 a 1)
                    - **Eixo X:** Tempo em horas
                    - **Curva:** Mostra como a confiabilidade diminui com o tempo
                    
                    **Valores importantes:**
                    - **R(t) = 0.9:** 90% de chance de sobreviver até t
                    - **R(MTBF):** Confiabilidade no tempo médio entre falhas
                    - **B10:** Tempo até 10% de falhas (90% de confiabilidade)
                    """)
            
            # TAB 2: TAXA DE FALHA
            with tab2:
                st.markdown("##### Taxa de Falha h(t)")
                st.caption("Taxa instantânea de falha ao longo do tempo")
                
                try:
                    hazard_data = weibull_hazard_rate_plot(lambda_param, rho_param, mtbf * 2.5)
                    st.line_chart(hazard_data.set_index('Tempo (horas)'), height=400)
                    
                    # Interpretação
                    if rho_param < 1:
                        interpretation = "📉 **Taxa decrescente:** Componente melhora com o tempo (burn-in)"
                    elif rho_param <= 1.1:
                        interpretation = "➡️ **Taxa constante:** Falhas aleatórias, não relacionadas ao tempo"
                    else:
                        interpretation = "📈 **Taxa crescente:** Componente deteriora com o tempo (desgaste)"
                    
                    st.info(interpretation)
                    
                except Exception as e:
                    st.error(f"Erro ao gerar gráfico de taxa de falha: {str(e)}")
                
                with st.expander("ℹ️ Como interpretar"):
                    st.markdown("""
                    **Taxa de Falha h(t):**
                    - **Eixo Y:** Taxa instantânea de falha
                    - **Eixo X:** Tempo em horas
                    - **Curva:** Mostra como o risco de falha evolui
                    
                    **Padrões:**
                    - **Decrescente (ρ < 1):** Mortalidade infantil
                    - **Constante (ρ ≈ 1):** Falhas aleatórias
                    - **Crescente (ρ > 1):** Desgaste/envelhecimento
                    """)
            
            # TAB 3: DENSIDADE
            with tab3:
                st.markdown("##### Função Densidade de Probabilidade f(t)")
                st.caption("Distribuição dos tempos de falha")
                
                try:
                    pdf_data = weibull_pdf_plot(lambda_param, rho_param, mtbf * 2.5)
                    st.area_chart(pdf_data.set_index('Tempo (horas)'), height=400)
                    
                    # Estatísticas
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        # Moda (pico da distribuição)
                        try:
                            if rho_param > 1:
                                mode = lambda_param * ((rho_param - 1) / rho_param) ** (1/rho_param)
                                st.metric("Moda", f"{mode:.0f}h", help="Tempo mais provável de falha")
                            else:
                                st.metric("Moda", "0h", help="Falhas mais prováveis no início")
                        except:
                            st.metric("Moda", "N/A", help="Não calculável")
                    
                    with col2:
                        st.metric("Média (MTBF)", f"{mtbf:.0f}h", help="Tempo médio de falha")
                    
                    with col3:
                        # Desvio padrão aproximado
                        try:
                            if rho_param > 0:
                                # Cálculo mais seguro do desvio padrão
                                gamma_1 = np.exp(np.log(lambda_param) + np.log(2) / rho_param)
                                gamma_2 = np.exp(2 * np.log(lambda_param) + 2 * np.log(2) / rho_param)
                                variance = gamma_2 - gamma_1 ** 2
                                
                                if variance > 0:
                                    std_dev = np.sqrt(variance)
                                    st.metric("Desvio Padrão", f"{std_dev:.0f}h", help="Dispersão dos tempos")
                                else:
                                    st.metric("Desvio Padrão", "N/A", help="Variância negativa")
                            else:
                                st.metric("Desvio Padrão", "N/A", help="ρ inválido")
                        except:
                            st.metric("Desvio Padrão", "N/A", help="Não calculável")
                    
                except Exception as e:
                    st.error(f"Erro ao gerar gráfico de densidade: {str(e)}")
                
                with st.expander("ℹ️ Como interpretar"):
                    st.markdown("""
                    **Função Densidade f(t):**
                    - **Eixo Y:** Densidade de probabilidade
                    - **Eixo X:** Tempo em horas
                    - **Área sob a curva:** Probabilidade de falha em um intervalo
                    
                    **Características:**
                    - **Pico (Moda):** Tempo mais provável de falha
                    - **Largura:** Variabilidade dos tempos de falha
                    - **Assimetria:** Depende do parâmetro ρ
                    """)
            
            # TAB 4: DADOS BRUTOS
            with tab4:
                st.markdown("##### Dados do Componente")
                
                try:
                    # Filtra dados do componente
                    component_data = dataset[dataset['component_type'] == selected_comp].copy()
                    
                    st.write(f"**Total de observações:** {len(component_data)}")
                    
                    if 'censored' in component_data.columns:
                        events = component_data['censored'].sum()
                        censored = len(component_data) - events
                        st.write(f"**Eventos observados:** {events}")
                        st.write(f"**Dados censurados:** {censored}")
                    
                    st.dataframe(component_data, use_container_width=True)
                    
                    # Histograma dos dados
                    if 'failure_time' in component_data.columns:
                        st.markdown("##### Histograma dos Tempos de Falha")
                        
                        failure_times = component_data['failure_time'].dropna()
                        if len(failure_times) > 0:
                            try:
                                hist_data = create_histogram_data(failure_times.values)
                                st.bar_chart(hist_data.set_index('Tempo (horas)'), height=300)
                            except Exception as e:
                                st.warning(f"Não foi possível gerar histograma: {str(e)}")
                
                except Exception as e:
                    st.error(f"Erro ao processar dados do componente: {str(e)}")

        
        # === CLASSIFICAÇÃO POR PADRÃO DE FALHA ===
        st.markdown("---")
        st.markdown("#### 🔍 Classificação por Padrão de Falha")
        
        patterns = {
            "🔽 Mortalidade Infantil (ρ < 1)": [],
            "➡️ Taxa Constante (ρ ≈ 1)": [],
            "📈 Desgaste (ρ > 1)": []
        }
        
        for name, result in successful_results.items():
            rho = result['rho']
            if rho < 0.9:
                patterns["🔽 Mortalidade Infantil (ρ < 1)"].append(name)
            elif rho <= 1.1:
                patterns["➡️ Taxa Constante (ρ ≈ 1)"].append(name)
            else:
                patterns["📈 Desgaste (ρ > 1)"].append(name)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**🔽 Mortalidade Infantil**")
            st.caption("Falhas precoces")
            if patterns["🔽 Mortalidade Infantil (ρ < 1)"]:
                for comp in patterns["🔽 Mortalidade Infantil (ρ < 1)"]:
                    st.write(f"• {comp}")
            else:
                st.write("_Nenhum componente_")
        
        with col2:
            st.markdown("**➡️ Taxa Constante**")
            st.caption("Falhas aleatórias")
            if patterns["➡️ Taxa Constante (ρ ≈ 1)"]:
                for comp in patterns["➡️ Taxa Constante (ρ ≈ 1)"]:
                    st.write(f"• {comp}")
            else:
                st.write("_Nenhum componente_")
        
        with col3:
            st.markdown("**📈 Desgaste**")
            st.caption("Falhas por envelhecimento")
            if patterns["📈 Desgaste (ρ > 1)"]:
                for comp in patterns["📈 Desgaste (ρ > 1)"]:
                    st.write(f"• {comp}")
            else:
                st.write("_Nenhum componente_")
        
        # === COMPONENTES COM FALHA ===
        if failed_results:
            st.markdown("---")
            with st.expander(f"⚠️ **{len(failed_results)} componentes falharam**"):
                for comp_name, result in failed_results.items():
                    error_msg = result.get('error', 'Erro desconhecido')
                    st.error(f"**{comp_name}:** {error_msg}")
        
        # === NAVEGAÇÃO PARA PRÓXIMA ETAPA ===
        st.markdown("---")
        st.markdown("### ➡️ Próxima Etapa")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            create_navigation_button(
                "pages/3_Planejamento_PM_Estoque.py",
                "🔧 **Prosseguir para Planejamento PM & Estoque**",
                key="weibull_to_planning"
            )
        
        st.success(f"🎯 **{len(successful_results)} componentes** prontos para planejamento")
    
    else:
        st.error("❌ **Nenhum componente foi analisado com sucesso**")
        st.warning("Verifique a qualidade dos dados e tente novamente")

else:
    st.info("🔄 **Aguardando execução da análise Weibull**")
    st.markdown("""
    ### 📋 Instruções
    
    1. **Revise** a visão geral dos dados acima
    2. **Execute** a análise de qualidade (barra lateral)
    3. **Clique** em "Executar Análise Weibull" (barra lateral)
    4. **Aguarde** o processamento
    5. **Revise** os resultados e gráficos
    """)

# === FOOTER ===
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p><em>Análise de confiabilidade baseada em distribuição Weibull</em></p>
    <p><small>Desenvolvido para otimização de manutenção industrial</small></p>
</div>
""", unsafe_allow_html=True)
