"""
Página de qualidade e limpeza de dados
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

# Adicionar diretórios ao path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from dataops.clean import DataCleaner, apply_ai_normalization
from ai.ai_assistant import WeibullAIAssistant
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="Qualidade dos Dados - Weibull Fleet Analytics",
    page_icon="🧼",
    layout="wide"
)

st.markdown("# 🧼 Qualidade dos Dados")
st.markdown("Análise e limpeza assistida por IA para garantir dados de alta qualidade")

def create_data_quality_dashboard(df, quality_report):
    """Criar dashboard de qualidade dos dados"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Score geral
    score = quality_report['quality_score']
    score_color = "🟢" if score >= 0.8 else "🟡" if score >= 0.6 else "🔴"
    
    with col1:
        st.metric(
            f"{score_color} Score de Qualidade",
            f"{score:.1%}",
            delta=f"{'Excelente' if score >= 0.8 else 'Bom' if score >= 0.6 else 'Precisa Melhorar'}"
        )
    
    with col2:
        total_missing = sum(quality_report['missing_data'].values())
        st.metric(
            "📊 Dados Faltantes",
            f"{total_missing}",
            delta=f"{total_missing/len(df)*100:.1f}% do total"
        )
    
    with col3:
        total_outliers = sum(quality_report['outliers'].values())
        st.metric(
            "🎯 Outliers Detectados",
            f"{total_outliers}",
            delta=f"{total_outliers/len(df)*100:.1f}% do total"
        )
    
    with col4:
        date_issues = sum(quality_report['date_issues'].values())
        st.metric(
            "📅 Problemas de Data",
            f"{date_issues}",
            delta=f"{'OK' if date_issues == 0 else 'Verificar'}"
        )

def create_missing_data_chart(quality_report):
    """Criar gráfico de dados faltantes"""
    missing_data = quality_report['missing_data']
    
    if sum(missing_data.values()) > 0:
        missing_df = pd.DataFrame(list(missing_data.items()), columns=['Coluna', 'Percentual'])
        missing_df = missing_df[missing_df['Percentual'] > 0].sort_values('Percentual', ascending=True)
        
        if len(missing_df) > 0:
            fig = px.bar(
                missing_df,
                x='Percentual',
                y='Coluna',
                orientation='h',
                title='Dados Faltantes por Coluna (%)',
                color='Percentual',
                color_continuous_scale=['green', 'yellow', 'red']
            )
            fig.update_layout(height=300, template='plotly_white')
            return fig
    
    return None

def create_outliers_chart(df, outlier_columns):
    """Criar gráfico de outliers"""
    if not outlier_columns:
        return None
    
    # Selecionar coluna com mais outliers
    selected_col = outlier_columns[0]
    
    fig = px.box(
        df,
        y=selected_col,
        title=f'Distribuição e Outliers - {selected_col}',
        points='outliers'
    )
    fig.update_layout(template='plotly_white')
    return fig

def analyze_component_names(df):
    """Analisar consistência de nomes de componentes"""
    if 'component' not in df.columns:
        return None
    
    component_counts = df['component'].value_counts()
    
    # Detectar possíveis duplicatas
    component_names = component_counts.index.tolist()
    potential_duplicates = []
    
    for i, name1 in enumerate(component_names):
        for name2 in component_names[i+1:]:
            # Similaridade simples baseada em palavras comuns
            words1 = set(name1.lower().split())
            words2 = set(name2.lower().split())
            
            if words1 & words2:  # Se há palavras em comum
                potential_duplicates.append((name1, name2))
    
    return component_counts, potential_duplicates

def main():
    # Verificar se há dados carregados
    if 'dataset' not in st.session_state or st.session_state.dataset is None:
        st.warning("📥 Carregue os dados primeiro na página '🗂️ Dados'")
        return
    
    df = st.session_state.dataset.copy()
    
    # Sidebar com configurações
    with st.sidebar:
        st.markdown("## 🎛️ Configurações de Limpeza")
        
        auto_clean = st.checkbox("Limpeza Automática", True)
        normalize_names = st.checkbox("Normalizar Nomes", True)
        remove_outliers = st.checkbox("Remover Outliers", False)
        fill_missing = st.checkbox("Preencher Faltantes", True)
        
        st.markdown("---")
        st.markdown("## 🤖 IA Assistiva")
        
        use_ai_cleaning = st.checkbox("Usar IA para Limpeza", True)
        ai_confidence_threshold = st.slider("Confiança Mínima IA", 0.5, 1.0, 0.8)
        
        st.markdown("---")
        st.markdown("## 📊 Filtros de Qualidade")
        
        min_operating_hours = st.number_input("Horas Mínimas", 0, 1000, 1)
        max_operating_hours = st.number_input("Horas Máximas", 1000, 50000, 30000)
    
    # Tabs principais
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Análise de Qualidade", "🧼 Limpeza", "🤖 IA Assistida", "✅ Validação"])
    
    with tab1:
        st.markdown("## 📊 Análise de Qualidade dos Dados")
        
        if st.button("🔍 Executar Análise de Qualidade", type="primary"):
            with st.spinner("Analisando qualidade dos dados..."):
                cleaner = DataCleaner()
                quality_report = cleaner.validate_data_quality(df)
                st.session_state.quality_report = quality_report
                
                st.success("✅ Análise de qualidade concluída!")
        
        # Exibir relatório se disponível
        if 'quality_report' in st.session_state:
            quality_report = st.session_state.quality_report
            
            # Dashboard geral
            create_data_quality_dashboard(df, quality_report)
            
            st.markdown("---")
            
            # Gráficos detalhados
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📊 Dados Faltantes")
                fig_missing = create_missing_data_chart(quality_report)
                if fig_missing:
                    st.plotly_chart(fig_missing, use_container_width=True)
                else:
                    st.success("✅ Nenhum dado faltante encontrado!")
            
            with col2:
                st.markdown("### 🎯 Outliers")
                outlier_cols = [col for col, count in quality_report['outliers'].items() if count > 0]
                if outlier_cols:
                    fig_outliers = create_outliers_chart(df, outlier_cols)
                    if fig_outliers:
                        st.plotly_chart(fig_outliers, use_container_width=True)
                else:
                    st.success("✅ Nenhum outlier detectado!")
            
            # Análise de consistência
            st.markdown("### 🔍 Análise de Consistência")
            
            if 'component' in df.columns:
                component_analysis = analyze_component_names(df)
                if component_analysis:
                    component_counts, potential_duplicates = component_analysis
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Top 10 Componentes:**")
                        st.dataframe(component_counts.head(10))
                    
                    with col2:
                        if potential_duplicates:
                            st.markdown("**⚠️ Possíveis Duplicatas:**")
                            for name1, name2 in potential_duplicates[:5]:
                                st.warning(f"• '{name1}' ↔ '{name2}'")
                        else:
                            st.success("✅ Nenhuma duplicata óbvia encontrada")
    
    with tab2:
        st.markdown("## 🧼 Limpeza Automática dos Dados")
        
        if st.button("🛠️ Executar Limpeza Completa", type="primary"):
            with st.spinner("Executando pipeline de limpeza..."):
                cleaner = DataCleaner()
                
                # Pipeline de limpeza
                df_clean, cleaning_summary = cleaner.full_cleaning_pipeline(df)
                
                # Salvar no session state
                st.session_state.dataset_clean = df_clean
                st.session_state.cleaning_summary = cleaning_summary
                
                st.success("✅ Limpeza concluída!")
        
        # Exibir resultados da limpeza
        if 'cleaning_summary' in st.session_state:
            summary = st.session_state.cleaning_summary
            
            st.markdown("### 📋 Resumo da Limpeza")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Registros Originais",
                    f"{summary['original_records']:,}",
                )
            
            with col2:
                st.metric(
                    "Registros Limpos",
                    f"{summary['cleaned_records']:,}",
                    delta=f"-{summary['records_removed']}"
                )
            
            with col3:
                quality_score = summary['quality_report']['quality_score']
                st.metric(
                    "Score de Qualidade",
                    f"{quality_score:.1%}",
                    delta=f"{'🟢 Bom' if quality_score >= 0.8 else '🟡 OK' if quality_score >= 0.6 else '🔴 Melhorar'}"
                )
            
            # Detalhes das operações
            st.markdown("### 🔧 Operações Realizadas")
            
            operations = [
                "✅ Padronização de colunas",
                "✅ Correção de unidades",
                "✅ Normalização de nomes",
                "✅ Remoção de duplicatas",
                "✅ Inferência de censura",
                "✅ Detecção de outliers"
            ]
            
            for op in operations:
                st.success(op)
            
            # Comparação antes/depois
            if 'dataset_clean' in st.session_state:
                st.markdown("### 📊 Comparação Antes/Depois")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Dados Originais:**")
                    st.dataframe(df.head(5))
                
                with col2:
                    st.markdown("**Dados Limpos:**")
                    st.dataframe(st.session_state.dataset_clean.head(5))
    
    with tab3:
        st.markdown("## 🤖 Limpeza Assistida por IA")
        
        if use_ai_cleaning:
            if st.button("🧠 Executar Limpeza com IA", type="primary"):
                with st.spinner("IA analisando e limpando dados..."):
                    try:
                        ai_assistant = WeibullAIAssistant()
                        
                        # Sugerir limpeza
                        cleaning_suggestion = ai_assistant.suggest_data_cleaning(df)
                        
                        if cleaning_suggestion.success:
                            st.markdown("### 🤖 Análise da IA")
                            st.markdown(cleaning_suggestion.content)
                            
                            if cleaning_suggestion.suggestions:
                                st.markdown("### 💡 Sugestões da IA")
                                for suggestion in cleaning_suggestion.suggestions:
                                    st.info(f"💡 {suggestion}")
                            
                            # Aplicar normalização
                            if normalize_names:
                                df_normalized = apply_ai_normalization(
                                    df, 
                                    columns=['component', 'fleet'] if 'fleet' in df.columns else ['component']
                                )
                                
                                st.session_state.dataset_ai_clean = df_normalized
                                
                                st.success("✅ Normalização IA aplicada!")
                        
                        else:
                            st.error(f"❌ Erro na análise IA: {cleaning_suggestion.content}")
                    
                    except Exception as e:
                        st.error(f"❌ Erro ao chamar IA: {str(e)}")
                        
                        # Fallback para limpeza baseada em regras
                        st.info("🔄 Executando limpeza baseada em regras como fallback...")
                        
                        cleaner = DataCleaner()
                        df_normalized = apply_ai_normalization(df)
                        st.session_state.dataset_ai_clean = df_normalized
                        
                        st.success("✅ Limpeza alternativa aplicada!")
            
            # Exibir resultados da IA
            if 'dataset_ai_clean' in st.session_state:
                st.markdown("### 📊 Resultados da Normalização IA")
                
                df_ai = st.session_state.dataset_ai_clean
                
                # Comparar nomes antes/depois
                if 'component' in df.columns:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Componentes Originais:**")
                        original_components = df['component'].value_counts().head(10)
                        st.dataframe(original_components)
                    
                    with col2:
                        st.markdown("**Componentes Normalizados:**")
                        normalized_components = df_ai['component'].value_counts().head(10)
                        st.dataframe(normalized_components)
                
                # Estatísticas de normalização
                if 'component_original' in df_ai.columns:
                    changes = (df_ai['component'] != df_ai['component_original']).sum()
                    st.metric(
                        "Componentes Normalizados",
                        changes,
                        delta=f"{changes/len(df_ai)*100:.1f}% do total"
                    )
        
        else:
            st.info("🤖 Habilite 'Usar IA para Limpeza' no sidebar para usar esta funcionalidade")
    
    with tab4:
        st.markdown("## ✅ Validação Final")
        
        # Selecionar dataset final
        dataset_options = {
            "Original": df,
        }
        
        if 'dataset_clean' in st.session_state:
            dataset_options["Limpo (Automático)"] = st.session_state.dataset_clean
        
        if 'dataset_ai_clean' in st.session_state:
            dataset_options["Limpo (IA)"] = st.session_state.dataset_ai_clean
        
        selected_dataset = st.selectbox(
            "Selecionar Dataset Final:",
            list(dataset_options.keys())
        )
        
        final_df = dataset_options[selected_dataset]
        
        if st.button("🔍 Validar Dataset Final", type="primary"):
            with st.spinner("Validando dataset final..."):
                cleaner = DataCleaner()
                final_quality = cleaner.validate_data_quality(final_df)
                
                # Dashboard final
                st.markdown("### 📊 Qualidade Final")
                create_data_quality_dashboard(final_df, final_quality)
                
                # Recomendação
                score = final_quality['quality_score']
                if score >= 0.8:
                    st.success("🎉 Dataset está pronto para análise Weibull!")
                elif score >= 0.6:
                    st.warning("⚠️ Dataset tem qualidade razoável, mas pode ser melhorado")
                else:
                    st.error("❌ Dataset precisa de mais limpeza antes da análise")
        
        # Botões de ação
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Salvar Dataset Final"):
                st.session_state.dataset = final_df
                st.success("✅ Dataset salvo como versão principal!")
        
        with col2:
            if st.button("📥 Download Dataset"):
                csv = final_df.to_csv(index=False).encode('utf-8')
                
                st.download_button(
                    label="📥 Download CSV Limpo",
                    data=csv,
                    file_name=f'dataset_limpo_{selected_dataset.lower()}.csv',
                    mime='text/csv'
                )
        
        with col3:
            if st.button("➡️ Próxima Etapa"):
                st.info("Navigate to '📈 Ajuste Weibull' para análise")

if __name__ == "__main__":
    main()