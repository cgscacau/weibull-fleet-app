import streamlit as st

# === CONFIGURAÇÃO DEVE SER A PRIMEIRA CHAMADA ===
st.set_page_config(
    page_title="Ajuste Weibull UNIFIED",
    page_icon="📈",
    layout="wide"
)

# Imports após configuração
import pandas as pd
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
st.markdown("**Análise de confiabilidade usando distribuição Weibull**")
st.markdown("---")

# === STATUS DO PIPELINE ===
st.subheader("📊 Status do Pipeline")
display_pipeline_status()

# === VERIFICAÇÃO DE PRÉ-REQUISITOS ===
if st.session_state.dataset is None or st.session_state.dataset.empty:
    st.error("❌ **Nenhum dataset carregado**")
    st.info("👈 **Próximo passo:** Vá para 'Dados UNIFIED' e carregue seus dados")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        safe_navigate(
            "pages/1_Dados_UNIFIED.py",
            "🔄 Ir para Dados UNIFIED"
        )
    
    st.stop()
# === INFORMAÇÕES DO DATASET ===
dataset = st.session_state.dataset
st.success(f"✅ **Dataset carregado:** {len(dataset):,} registros")

# === SIDEBAR COM CONTROLES ===
with st.sidebar:
    st.header("🎛️ Controles")
    
    # Relatório de qualidade
    st.subheader("📋 Qualidade dos Dados")
    
    if st.button("🔍 Analisar Qualidade", use_container_width=True):
        with st.spinner("Analisando qualidade dos dados..."):
            quality_report = generate_data_quality_report(dataset)
            st.session_state.data_quality_report = quality_report
    
    # Exibe relatório se disponível
    quality_report = st.session_state.get("data_quality_report", {})
    if quality_report:
        status = quality_report.get("status", "unknown")
        
        # Ícones de status
        status_icons = {
            "excellent": "🟢 Excelente",
            "good": "🟡 Boa", 
            "fair": "🟠 Razoável",
            "poor": "🔴 Ruim",
            "critical": "⚫ Crítica",
            "empty": "⚪ Vazio"
        }
        
        st.write(f"**Status:** {status_icons.get(status, '❓ Desconhecido')}")
        
        if quality_report.get("issues"):
            with st.expander("⚠️ Problemas"):
                for issue in quality_report["issues"]:
                    st.warning(issue)
        
        if quality_report.get("recommendations"):
            with st.expander("💡 Recomendações"):
                for rec in quality_report["recommendations"]:
                    st.info(rec)
    
    st.markdown("---")
    
    # Controles de análise
    st.subheader("🚀 Análise Weibull")
    
    # Botão principal
    if st.button("▶️ Executar Análise", type="primary", use_container_width=True):
        # Verifica qualidade primeiro
        if not quality_report:
            st.warning("Execute a análise de qualidade primeiro")
        elif quality_report.get("status") == "critical":
            st.error("Corrija os problemas críticos antes de continuar")
        else:
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
    
    # Informações sobre última análise
    if st.session_state.get("analysis_timestamp"):
        timestamp = st.session_state.analysis_timestamp
        st.caption(f"Última análise: {timestamp.strftime('%d/%m/%Y %H:%M')}")
    
    # Botão para limpar
    if st.session_state.get("weibull_results"):
        st.markdown("---")
        if st.button("🗑️ Limpar Resultados", use_container_width=True):
            reset_downstream_data('weibull')
            st.rerun()

# === SEÇÃO PRINCIPAL ===
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📊 Visão Geral dos Dados")
    
    if 'component_type' in dataset.columns:
        # Estatísticas por componente
        component_counts = dataset['component_type'].value_counts()
        
        # Tabela resumo
        summary_data = []
        for comp, count in component_counts.items():
            adequado = "✅ Sim" if count >= 3 else "❌ Não"
            summary_data.append({
                'Componente': comp,
                'Registros': count,
                'Adequado para Weibull': adequado
            })
        
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True)
        
        # Estatísticas gerais
        total_adequate = sum(1 for count in component_counts.values if count >= 3)
        st.info(f"📈 **{total_adequate}** de **{len(component_counts)}** componentes têm dados suficientes para análise Weibull")

with col2:
    st.subheader("📋 Resumo")
    
    # Métricas do dataset
    st.metric("Total de Registros", f"{len(dataset):,}")
    st.metric("Componentes Únicos", dataset['component_type'].nunique() if 'component_type' in dataset.columns else 0)
    
    if 'failure_time' in dataset.columns:
        valid_times = pd.to_numeric(dataset['failure_time'], errors='coerce')
        st.metric("Tempo Médio de Falha", f"{valid_times.mean():.1f}" if valid_times.notna().any() else "N/A")

# === RESULTADOS DA ANÁLISE ===
st.markdown("---")
st.subheader("📈 Resultados da Análise Weibull")

weibull_results = st.session_state.get("weibull_results", {})

if weibull_results:
    display_weibull_results(weibull_results)
    
    # Botão para próxima etapa
    st.markdown("---")
    
    successful_components = [
        name for name, result in weibull_results.items() 
        if result.get('success', False)
    ]
    
# === BOTÃO PARA PRÓXIMA ETAPA (CORRIGIDO) ===
if successful_components:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if safe_navigate(
            "pages/3_Planejamento_PM_Estoque.py",
            "➡️ **Prosseguir para Planejamento PM & Estoque**"
        ):
            # Define componente padrão se não houver seleção
            if not st.session_state.get("selected_component"):
                st.session_state.selected_component = successful_components[0]
    
    st.success(f"🎯 **{len(successful_components)} componentes** prontos para planejamento de manutenção")
    else:
        st.warning("⚠️ Nenhum componente foi analisado com sucesso. Verifique a qualidade dos dados.")

else:
    st.info("🔄 **Execute a análise Weibull** usando o botão na barra lateral")
    
    # Preview dos dados
    with st.expander("👀 **Preview dos Dados**"):
        st.dataframe(dataset.head(10), use_container_width=True)

# === SEÇÃO DE DEBUG (OPCIONAL) ===
if st.sidebar.checkbox("🐛 Modo Debug"):
    st.markdown("---")
    st.subheader("🔍 Informações de Debug")
    
    debug_info = {
        "Shape do Dataset": dataset.shape,
        "Colunas": list(dataset.columns),
        "Resultados Weibull": len(weibull_results),
        "Relatório de Qualidade": "Disponível" if quality_report else "Não gerado",
        "Timestamp da Análise": st.session_state.get("analysis_timestamp", "Nunca executada")
    }
    
    for key, value in debug_info.items():
        st.write(f"**{key}:** {value}")
    
    if weibull_results:
        with st.expander("Resultados Weibull Brutos"):
            st.json(weibull_results)
