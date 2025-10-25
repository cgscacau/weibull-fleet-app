import streamlit as st

# === CONFIGURAÇÃO - DEVE SER A PRIMEIRA CHAMADA ===
st.set_page_config(
    page_title="Ajuste Weibull UNIFIED",
    page_icon="📈",
    layout="wide"
)

# === IMPORTS APÓS CONFIGURAÇÃO ===
import pandas as pd
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
from utils.navigation import safe_navigate

# === INICIALIZAÇÃO ===
initialize_session_state()

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
    
    st.info("👈 **Próximo passo:** Use a barra lateral para navegar até 'Dados UNIFIED'")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 **Ir para Dados UNIFIED**", type="primary", use_container_width=True):
            try:
                st.switch_page("pages/1_Dados_UNIFIED.py")
            except:
                st.info("👈 Use o menu lateral para navegar até **Dados UNIFIED**")
    
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
            with st.expander("⚠️ Problemas Encontrados", expanded=True):
                for issue in quality_report["issues"]:
                    st.warning(f"• {issue}")
        
        # Recomendações
        if quality_report.get("recommendations"):
            with st.expander("💡 Recomendações"):
                for rec in quality_report["recommendations"]:
                    st.info(f"• {rec}")
        
        # Estatísticas
        if quality_report.get("statistics"):
            with st.expander("📊 Estatísticas"):
                stats = quality_report["statistics"]
                for key, value in stats.items():
                    if value is not None:
                        st.write(f"**{key}:** {value}")
    
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
        with st.spinner("🔄 Executando análise Weibull... Isso pode levar alguns segundos."):
            weibull_results = execute_weibull_analysis(dataset)
            
            if weibull_results:
                st.session_state.weibull_results = weibull_results
                st.session_state.analysis_timestamp = pd.Timestamp.now()
                st.success("✅ Análise concluída com sucesso!")
                st.rerun()
            else:
                st.error("❌ Falha na execução da análise")
    
    # Informação sobre última análise
    if st.session_state.get("analysis_timestamp"):
        timestamp = st.session_state.analysis_timestamp
        st.caption(f"📅 Última análise: {timestamp.strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Botão para limpar resultados
    if st.session_state.get("weibull_results"):
        st.markdown("---")
        if st.button("🗑️ **Limpar Resultados**", use_container_width=True):
            reset_downstream_data('weibull')
            st.success("Resultados limpos!")
            st.rerun()
    
    st.markdown("---")
    
    # === AJUDA ===
    with st.expander("❓ Ajuda"):
        st.markdown("""
        **Como usar esta página:**
        
        1. **Analisar Qualidade**: Verifica se os dados estão adequados
        2. **Executar Análise**: Ajusta parâmetros Weibull para cada componente
        3. **Revisar Resultados**: Examine os parâmetros calculados
        4. **Prosseguir**: Vá para o Planejamento PM
        
        **Requisitos mínimos:**
        - 3+ observações por componente
        - Tempos de falha > 0
        - Valores de censura válidos (0 ou 1)
        """)

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
            st.success(f"✅ **Todos os {total_components} componentes** têm dados suficientes para análise Weibull")
        else:
            st.warning(f"⚠️ **{total_adequate} de {total_components} componentes** têm dados suficientes para análise")

with col2:
    st.markdown("#### 📈 Distribuição de Dados")
    
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
    
    # Botão para download
    csv = dataset.to_csv(index=False)
    st.download_button(
        "💾 **Download Dataset Completo (CSV)**",
        data=csv,
        file_name="dataset_weibull.csv",
        mime="text/csv"
    )

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
        
        # Exibe resultados
        display_weibull_results(weibull_results)
        
        # Resumo estatístico
        st.markdown("---")
        st.markdown("#### 📊 Resumo Estatístico")
        
        col1, col2, col3, col4 = st.columns(4)
        
        # Calcula estatísticas
        lambdas = [r['lambda'] for r in successful_results.values()]
        rhos = [r['rho'] for r in successful_results.values()]
        mtbfs = [r.get('MTBF', 0) for r in successful_results.values() if r.get('MTBF')]
        
        with col1:
            st.metric("λ Médio", f"{sum(lambdas)/len(lambdas):.2f}")
        
        with col2:
            st.metric("ρ Médio", f"{sum(rhos)/len(rhos):.2f}")
        
        with col3:
            if mtbfs:
                st.metric("MTBF Médio", f"{sum(mtbfs)/len(mtbfs):.0f}h")
        
        with col4:
            total_obs = sum(r['n_observations'] for r in successful_results.values())
            st.metric("Total Observações", f"{total_obs:,}")
        
        # Classificação por padrão de falha
        st.markdown("---")
        st.markdown("#### 🔍 Classificação por Padrão de Falha")
        
        patterns = {
            "Mortalidade Infantil (ρ < 1)": [],
            "Taxa Constante (ρ ≈ 1)": [],
            "Desgaste (ρ > 1)": []
        }
        
        for name, result in successful_results.items():
            rho = result['rho']
            if rho < 0.9:
                patterns["Mortalidade Infantil (ρ < 1)"].append(name)
            elif rho <= 1.1:
                patterns["Taxa Constante (ρ ≈ 1)"].append(name)
            else:
                patterns["Desgaste (ρ > 1)"].append(name)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**🔽 Mortalidade Infantil**")
            st.caption("Falhas precoces")
            if patterns["Mortalidade Infantil (ρ < 1)"]:
                for comp in patterns["Mortalidade Infantil (ρ < 1)"]:
                    st.write(f"• {comp}")
            else:
                st.write("_Nenhum componente_")
        
        with col2:
            st.markdown("**➡️ Taxa Constante**")
            st.caption("Falhas aleatórias")
            if patterns["Taxa Constante (ρ ≈ 1)"]:
                for comp in patterns["Taxa Constante (ρ ≈ 1)"]:
                    st.write(f"• {comp}")
            else:
                st.write("_Nenhum componente_")
        
        with col3:
            st.markdown("**📈 Desgaste**")
            st.caption("Falhas por envelhecimento")
            if patterns["Desgaste (ρ > 1)"]:
                for comp in patterns["Desgaste (ρ > 1)"]:
                    st.write(f"• {comp}")
            else:
                st.write("_Nenhum componente_")
        
        # Componentes com falha
        if failed_results:
            st.markdown("---")
            with st.expander(f"⚠️ **{len(failed_results)} componentes falharam** (clique para detalhes)"):
                for comp_name, result in failed_results.items():
                    error_msg = result.get('error', 'Erro desconhecido')
                    st.error(f"**{comp_name}:** {error_msg}")
        
        # === NAVEGAÇÃO PARA PRÓXIMA ETAPA ===
        st.markdown("---")
        st.markdown("### ➡️ Próxima Etapa")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔧 **Prosseguir para Planejamento PM & Estoque**", 
                        type="primary", 
                        use_container_width=True):
                
                # Define componente padrão se não houver seleção
                if not st.session_state.get("selected_component"):
                    st.session_state.selected_component = list(successful_results.keys())[0]
                
                try:
                    st.switch_page("pages/3_Planejamento_PM_Estoque.py")
                except:
                    st.info("👈 Use o menu lateral para navegar até **Planejamento PM & Estoque**")
        
        st.success(f"🎯 **{len(successful_results)} componentes** prontos para planejamento de manutenção")
    
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
    4. **Aguarde** o processamento (pode levar alguns segundos)
    5. **Revise** os resultados nesta seção
    """)
    
    # Preview dos dados como guia
    with st.expander("👀 **Preview dos Dados**"):
        st.dataframe(dataset.head(10), use_container_width=True)

# === SEÇÃO DE DEBUG (OPCIONAL) ===
if st.sidebar.checkbox("🐛 **Modo Debug**"):
    st.markdown("---")
    st.subheader("🔍 Informações de Debug")
    
    debug_tabs = st.tabs(["📊 Dataset", "🔧 Weibull", "💾 Session State"])
    
    with debug_tabs[0]:
        st.write("**Informações do Dataset:**")
        st.write(f"- Shape: {dataset.shape}")
        st.write(f"- Colunas: {list(dataset.columns)}")
        st.write(f"- Tipos: {dataset.dtypes.to_dict()}")
        st.write(f"- Memória: {dataset.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    
    with debug_tabs[1]:
        st.write("**Informações Weibull:**")
        st.write(f"- Resultados disponíveis: {len(weibull_results)}")
        st.write(f"- Análises bem-sucedidas: {sum(1 for r in weibull_results.values() if r.get('success'))}")
        
        if weibull_results:
            st.json(weibull_results)
    
    with debug_tabs[2]:
        st.write("**Session State:**")
        state_info = {
            "dataset": "Carregado" if st.session_state.get("dataset") is not None else "None",
            "weibull_results": len(st.session_state.get("weibull_results", {})),
            "data_quality_report": "Disponível" if st.session_state.get("data_quality_report") else "None",
            "analysis_timestamp": str(st.session_state.get("analysis_timestamp", "Nunca"))
        }
        
        for key, value in state_info.items():
            st.write(f"- **{key}:** {value}")

# === FOOTER ===
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p><em>Análise de confiabilidade baseada em distribuição Weibull</em></p>
    <p><small>Desenvolvido para otimização de manutenção industrial</small></p>
</div>
""", unsafe_allow_html=True)
