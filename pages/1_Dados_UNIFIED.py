"""
Página de upload e gestão de dados - VERSÃO FINAL COMPLETA
Com mapeamento automático de colunas, multi-encoding E detecção de separador
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys
import io

# Adicionar diretórios ao path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from dataops.column_mapper import (
    standardize_dataframe, 
    get_column_requirements_text,
    create_example_dataframe,
    STANDARD_SCHEMA
)
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="Dados - Weibull Fleet Analytics",
    page_icon="🗂️",
    layout="wide"
)

st.markdown("# 🗂️ Gestão de Dados")
st.markdown("Upload, validação e preparação de dados para análise de confiabilidade")

# Inicializar session state
if 'dataset' not in st.session_state:
    st.session_state.dataset = None
if 'standardization_report' not in st.session_state:
    st.session_state.standardization_report = None
if 'data_quality_report' not in st.session_state:
    st.session_state.data_quality_report = None


def detect_csv_separator(file_content):
    """
    Detecta automaticamente o separador do CSV (vírgula ou ponto-e-vírgula)
    """
    # Ler primeiras linhas para detectar
    first_lines = file_content.split('\n')[:3]
    
    comma_count = sum(line.count(',') for line in first_lines)
    semicolon_count = sum(line.count(';') for line in first_lines)
    
    if semicolon_count > comma_count:
        return ';'
    else:
        return ','


def read_csv_smart(uploaded_file):
    """
    Lê CSV com detecção automática de encoding E separador
    
    Returns:
        tuple: (dataframe, encoding_usado, separador_usado)
    """
    # Tentar múltiplos encodings
    encodings_to_try = [
        ('utf-8', 'UTF-8'),
        ('latin-1', 'Latin-1 (ISO-8859-1)'),
        ('cp1252', 'Windows-1252 (CP1252)')
    ]
    
    df_raw = None
    encoding_used = None
    separator_used = None
    
    for encoding, encoding_name in encodings_to_try:
        try:
            # Ler arquivo como texto primeiro
            uploaded_file.seek(0)
            content = uploaded_file.read().decode(encoding)
            
            # Detectar separador
            separator = detect_csv_separator(content)
            
            # Tentar ler como DataFrame
            df_raw = pd.read_csv(io.StringIO(content), sep=separator)
            
            # Se chegou aqui, sucesso!
            encoding_used = encoding_name
            separator_used = 'ponto-e-vírgula (;)' if separator == ';' else 'vírgula (,)'
            break
            
        except UnicodeDecodeError:
            continue
        except Exception as e:
            # Se falhar por outro motivo, tentar próximo encoding
            continue
    
    if df_raw is None:
        raise Exception("Não foi possível ler o arquivo com nenhum encoding suportado")
    
    return df_raw, encoding_used, separator_used


def display_data_overview(df):
    """Exibir overview dos dados"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Registros", f"{len(df):,}")
    
    with col2:
        n_components = df['component_type'].nunique() if 'component_type' in df.columns else 0
        st.metric("Tipos de Componentes", n_components)
    
    with col3:
        n_assets = df['component_id'].nunique() if 'component_id' in df.columns else 0
        st.metric("Componentes Únicos", n_assets)
    
    with col4:
        if 'censored' in df.columns:
            censoring_rate = df['censored'].mean() * 100
            st.metric("Taxa de Censura", f"{censoring_rate:.1f}%")
        else:
            st.metric("Taxa de Censura", "N/A")


def display_standardization_report(report):
    """Exibe relatório de padronização"""
    st.markdown("### 📊 Relatório de Padronização")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### ✅ Mapeamento de Colunas")
        if report['mapping']:
            mapping_df = pd.DataFrame([
                {'Coluna Padrão': k, 'Coluna Original': v} 
                for k, v in report['mapping'].items()
            ])
            st.dataframe(mapping_df, use_container_width=True)
        else:
            st.warning("Nenhum mapeamento detectado")
    
    with col2:
        st.markdown("#### 🧹 Limpeza de Dados")
        if 'cleaning' in report and report['cleaning']:
            cleaning = report['cleaning']
            st.metric("Linhas Iniciais", cleaning.get('initial_rows', 0))
            st.metric("Linhas Removidas", cleaning.get('removed_rows', 0))
            st.metric("Linhas Finais", cleaning.get('final_rows', 0))
            
            if cleaning.get('issues'):
                for issue in cleaning['issues']:
                    st.info(f"ℹ️ {issue}")
    
    # Avisos
    if report.get('warnings'):
        st.markdown("#### ⚠️ Avisos")
        for warning in report['warnings']:
            st.warning(warning)


def create_data_quality_charts(df):
    """Criar gráficos de qualidade dos dados"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de dados faltantes
        missing_data = df.isnull().sum()
        missing_pct = (missing_data / len(df) * 100).round(1)
        
        if missing_pct.sum() > 0:
            fig_missing = px.bar(
                x=missing_pct.values,
                y=missing_pct.index,
                orientation='h',
                title="Dados Faltantes por Coluna (%)",
                labels={'x': 'Percentual Faltante', 'y': 'Coluna'}
            )
            fig_missing.update_layout(height=300, template='plotly_white')
            st.plotly_chart(fig_missing, use_container_width=True)
        else:
            st.success("✅ Nenhum dado faltante detectado!")
    
    with col2:
        # Distribuição de componentes
        if 'component_type' in df.columns:
            component_counts = df['component_type'].value_counts().head(10)
            fig_components = px.bar(
                x=component_counts.values,
                y=component_counts.index,
                orientation='h',
                title="Top 10 Tipos de Componentes",
                labels={'x': 'Quantidade', 'y': 'Tipo'}
            )
            fig_components.update_layout(height=300, template='plotly_white')
            st.plotly_chart(fig_components, use_container_width=True)
    
    # Distribuição de tempos de falha
    if 'failure_time' in df.columns:
        # Separar censurados e não censurados
        if 'censored' in df.columns:
            df_failures = df[~df['censored']]
            df_censored = df[df['censored']]
            
            fig_times = go.Figure()
            
            fig_times.add_trace(go.Histogram(
                x=df_failures['failure_time'],
                name='Falhas Observadas',
                opacity=0.7,
                nbinsx=30
            ))
            
            if len(df_censored) > 0:
                fig_times.add_trace(go.Histogram(
                    x=df_censored['failure_time'],
                    name='Dados Censurados',
                    opacity=0.7,
                    nbinsx=30
                ))
            
            fig_times.update_layout(
                title="Distribuição dos Tempos de Falha",
                xaxis_title="Tempo (horas)",
                yaxis_title="Frequência",
                template='plotly_white',
                barmode='stack'
            )
        else:
            fig_times = px.histogram(
                df, 
                x='failure_time',
                title="Distribuição dos Tempos de Falha",
                nbins=50
            )
            fig_times.update_layout(template='plotly_white')
        
        st.plotly_chart(fig_times, use_container_width=True)


def main():
    # Sidebar com configurações
    with st.sidebar:
        st.markdown("## ⚙️ Configurações")
        
        data_source = st.selectbox(
            "Fonte de Dados",
            ["Upload de Arquivo", "Dados de Exemplo"]
        )
        
        if data_source == "Upload de Arquivo":
            file_format = st.selectbox("Formato", ["CSV", "Excel (XLSX/XLS)"])
        
        st.markdown("---")
        
        # Mostrar requisitos de colunas
        with st.expander("📋 Requisitos de Colunas", expanded=False):
            st.markdown(get_column_requirements_text())
    
    # Área principal
    tab1, tab2, tab3 = st.tabs(["📥 Upload", "🔍 Exploração", "✅ Validação"])
    
    with tab1:
        st.markdown("## 📥 Carregar Dados")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if data_source == "Upload de Arquivo":
                uploaded_file = st.file_uploader(
                    f"Escolha um arquivo {file_format}",
                    type=['csv', 'xlsx', 'xls']
                )
                
                if uploaded_file is not None:
                    try:
                        # ===================================================================
                        # CORREÇÃO COMPLETA: Multi-encoding + Detecção de Separador
                        # ===================================================================
                        if file_format == "CSV" or uploaded_file.name.endswith('.csv'):
                            # Usar função inteligente de leitura
                            df_raw, encoding_used, separator_used = read_csv_smart(uploaded_file)
                            
                            # Mostrar detecção
                            st.success(f"✅ **Encoding detectado:** {encoding_used}")
                            st.success(f"✅ **Separador detectado:** {separator_used}")
                        
                        else:
                            # Excel: pandas detecta automaticamente
                            df_raw = pd.read_excel(uploaded_file)
                            encoding_used = 'Excel (auto-detectado)'
                            separator_used = 'N/A'
                        # ===================================================================
                        # FIM DA CORREÇÃO
                        # ===================================================================
                        
                        st.info(f"📄 Arquivo lido: {len(df_raw)} registros, {len(df_raw.columns)} colunas")
                        
                        # Mostrar preview dos dados originais
                        with st.expander("👁️ Preview dos Dados Originais", expanded=True):
                            st.dataframe(df_raw.head(10), use_container_width=True)
                            st.text(f"Colunas encontradas: {', '.join(df_raw.columns.tolist())}")
                        
                        # Padronizar automaticamente
                        with st.spinner("🔄 Padronizando formato dos dados..."):
                            df_standardized, report = standardize_dataframe(df_raw)
                            
                            if report['success']:
                                st.success("✅ Dados padronizados com sucesso!")
                                
                                # Salvar no session state
                                st.session_state.dataset = df_standardized
                                st.session_state.standardization_report = report
                                
                                # Mostrar relatório de padronização
                                display_standardization_report(report)
                                
                                # Preview dos dados padronizados
                                st.markdown("#### 📊 Dados Padronizados")
                                st.dataframe(df_standardized.head(10), use_container_width=True)
                                
                                # Estatísticas rápidas
                                col_a, col_b, col_c = st.columns(3)
                                with col_a:
                                    st.metric("Registros Válidos", len(df_standardized))
                                with col_b:
                                    failures = (~df_standardized['censored']).sum()
                                    st.metric("Falhas Observadas", failures)
                                with col_c:
                                    censored = df_standardized['censored'].sum()
                                    st.metric("Dados Censurados", censored)
                            
                            else:
                                st.error("❌ Falha na padronização dos dados")
                                
                                if report['missing_columns']:
                                    st.error(f"**Colunas Obrigatórias Faltando:** {', '.join(report['missing_columns'])}")
                                    
                                    st.markdown("### 💡 Solução:")
                                    st.markdown("""
                                    Seu arquivo precisa ter pelo menos estas 3 colunas (com nomes aceitos):
                                    
                                    1. **ID do Componente**: `component_id`, `asset_id`, `equipment_id`, ou `id`
                                    2. **Tipo do Componente**: `component_type`, `component`, ou `tipo`
                                    3. **Tempo de Falha**: `failure_time`, `operating_hours`, ou `hours`
                                    
                                    A coluna `censored` é opcional - será inferida automaticamente se não fornecida.
                                    """)
                                
                                if 'error' in report:
                                    st.error(f"**Erro:** {report['error']}")
                                
                                # Mostrar colunas encontradas
                                st.markdown("#### 📋 Colunas Encontradas no Arquivo:")
                                st.code(", ".join(report.get('original_columns', df_raw.columns.tolist())))
                    
                    except Exception as e:
                        st.error(f"❌ Erro ao processar arquivo: {str(e)}")
                        st.exception(e)
            
            elif data_source == "Dados de Exemplo":
                st.markdown("### 📦 Carregar Dados de Exemplo")
                
                example_format = st.radio(
                    "Escolha o formato de exemplo:",
                    ["Padrão (standard)", "Legado (legacy)", "SAP"],
                    help="Diferentes formatos para demonstrar o mapeamento automático"
                )
                
                format_map = {
                    "Padrão (standard)": "standard",
                    "Legado (legacy)": "legacy",
                    "SAP": "sap"
                }
                
                if st.button("🔄 Carregar Dados de Exemplo", type="primary"):
                    try:
                        # Criar dados de exemplo
                        df_example = create_example_dataframe(format_map[example_format])
                        
                        # Padronizar
                        df_standardized, report = standardize_dataframe(df_example)
                        
                        if report['success']:
                            st.session_state.dataset = df_standardized
                            st.session_state.standardization_report = report
                            
                            st.success(f"✅ Dados de exemplo carregados: {len(df_standardized)} registros")
                            
                            display_standardization_report(report)
                        else:
                            st.error("❌ Erro ao padronizar dados de exemplo")
                    
                    except Exception as e:
                        st.error(f"❌ Erro: {str(e)}")
        
        with col2:
            st.markdown("### ℹ️ Informações")
            st.info("""
            **Formatos Aceitos:**
            - CSV (.csv)
            - Excel (.xlsx, .xls)
            
            **Encodings Suportados:**
            - UTF-8
            - Latin-1 (ISO-8859-1)
            - Windows-1252 (CP1252)
            
            **Separadores Suportados:**
            - Vírgula (,)
            - Ponto-e-vírgula (;)
            
            **Detecção Automática:**
            - Encoding
            - Separador
            - Nomes de colunas
            
            **Validação:**
            - Remove valores nulos
            - Remove tempos negativos
            - Infere censura automática
            - Valida tipos de dados
            """)
    
    with tab2:
        if st.session_state.dataset is not None:
            df = st.session_state.dataset
            
            st.markdown("## 🔍 Exploração dos Dados")
            
            # Overview geral
            display_data_overview(df)
            
            st.markdown("---")
            
            # Visualizar amostra dos dados
            st.markdown("### 📋 Amostra dos Dados Padronizados")
            n_rows = st.slider("Número de linhas para exibir", 5, 50, 10)
            st.dataframe(df.head(n_rows), use_container_width=True)
            
            # Informações das colunas
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📊 Informações das Colunas")
                col_info = pd.DataFrame({
                    'Tipo': df.dtypes.astype(str),
                    'Não Nulos': df.count(),
                    'Valores Únicos': df.nunique(),
                    'Faltantes': df.isnull().sum()
                })
                st.dataframe(col_info, use_container_width=True)
            
            with col2:
                st.markdown("### 🎯 Valores Únicos")
                selected_col = st.selectbox("Selecionar Coluna", df.columns)
                if selected_col:
                    unique_vals = df[selected_col].value_counts().head(10)
                    st.dataframe(unique_vals, use_container_width=True)
            
            # Gráficos de qualidade
            st.markdown("---")
            st.markdown("### 📈 Visualizações")
            create_data_quality_charts(df)
        
        else:
            st.info("📥 Carregue os dados primeiro na aba 'Upload'")
    
    with tab3:
        if st.session_state.dataset is not None:
            df = st.session_state.dataset
            
            st.markdown("## ✅ Validação e Qualidade")
            
            # Validação de schema
            st.markdown("### 🔍 Validação de Schema")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### ✅ Colunas Obrigatórias")
                for col in STANDARD_SCHEMA.keys():
                    if col in df.columns:
                        st.success(f"✅ `{col}` - OK")
                    else:
                        st.error(f"❌ `{col}` - FALTANDO")
            
            with col2:
                st.markdown("#### 📊 Estatísticas de Qualidade")
                
                # Taxa de completude
                completeness = (1 - df.isnull().sum() / len(df)) * 100
                avg_completeness = completeness.mean()
                
                st.metric("Completude Média", f"{avg_completeness:.1f}%")
                
                # Contagem de registros válidos
                valid_records = len(df)
                st.metric("Registros Válidos", valid_records)
                
                # Falhas vs Censura
                failures = (~df['censored']).sum()
                censored = df['censored'].sum()
                failure_rate = failures / len(df) * 100
                
                st.metric("Taxa de Falhas", f"{failure_rate:.1f}%")
            
            # Análise detalhada
            st.markdown("---")
            st.markdown("### 📊 Análise Detalhada")
            
            # Estatísticas descritivas
            if 'failure_time' in df.columns:
                st.markdown("#### ⏱️ Estatísticas de Tempo de Falha")
                
                stats_df = df['failure_time'].describe().to_frame()
                stats_df.columns = ['Valor']
                st.dataframe(stats_df, use_container_width=True)
                
                # Boxplot
                fig_box = px.box(
                    df, 
                    y='failure_time',
                    x='component_type' if 'component_type' in df.columns else None,
                    title="Distribuição de Tempos por Tipo de Componente",
                    color='censored' if 'censored' in df.columns else None
                )
                fig_box.update_layout(template='plotly_white')
                st.plotly_chart(fig_box, use_container_width=True)
        
        else:
            st.info("📥 Carregue os dados primeiro na aba 'Upload'")
    
    # Footer com ações
    if st.session_state.dataset is not None:
        st.markdown("---")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Download dados padronizados
            df = st.session_state.dataset
            csv = df.to_csv(index=False).encode('utf-8')
            
            st.download_button(
                label="💾 Download CSV Padronizado",
                data=csv,
                file_name='dados_padronizados.csv',
                mime='text/csv'
            )
        
        with col2:
            # Download relatório de padronização
            if st.session_state.standardization_report:
                report = st.session_state.standardization_report
                report_text = f"""
RELATÓRIO DE PADRONIZAÇÃO
=========================

Sucesso: {report['success']}
Linhas Finais: {report.get('final_shape', ('?', '?'))[0]}
Colunas Finais: {', '.join(report.get('final_columns', []))}

MAPEAMENTO:
{chr(10).join([f"  {k} <- {v}" for k, v in report.get('mapping', {}).items()])}

LIMPEZA:
{chr(10).join([f"  - {issue}" for issue in report.get('cleaning', {}).get('issues', [])])}

AVISOS:
{chr(10).join([f"  - {warning}" for warning in report.get('warnings', [])])}
"""
                st.download_button(
                    label="📄 Download Relatório",
                    data=report_text,
                    file_name='relatorio_padronizacao.txt',
                    mime='text/plain'
                )
        
        with col3:
            if st.button("➡️ Prosseguir para Análise Weibull", type="primary"):
                st.success("✅ Dados prontos! Vá para a página '📈 Ajuste Weibull'")
        
        with col4:
            if st.button("🔄 Resetar Tudo"):
                st.session_state.dataset = None
                st.session_state.standardization_report = None
                st.session_state.data_quality_report = None
                st.rerun()

if __name__ == "__main__":
    main()
