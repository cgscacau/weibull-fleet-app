"""
Página de upload e gestão de dados
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

from dataops.schemas import FleetDataset, FailureRecord
from dataops.clean import DataCleaner
from dataops.ingest import DataIngestor
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
if 'data_quality_report' not in st.session_state:
    st.session_state.data_quality_report = None

def load_sample_data():
    """Carregar dados de exemplo"""
    sample_file = project_root / "storage" / "sample_fleet_data.csv"
    if sample_file.exists():
        return pd.read_csv(sample_file)
    return None

def validate_uploaded_data(df):
    """Validar dados carregados"""
    issues = []
    suggestions = []
    
    # Verificar colunas essenciais
    required_cols = ['asset_id', 'component', 'operating_hours']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        issues.append(f"Colunas obrigatórias faltando: {missing_cols}")
        suggestions.append("Renomeie ou adicione as colunas necessárias")
    
    # Verificar tipos de dados
    if 'operating_hours' in df.columns:
        non_numeric = df['operating_hours'].apply(lambda x: not isinstance(x, (int, float)) and pd.notna(x)).any()
        if non_numeric:
            issues.append("Coluna 'operating_hours' contém valores não numéricos")
            suggestions.append("Converta valores para números ou remova registros inválidos")
    
    # Verificar valores negativos
    if 'operating_hours' in df.columns:
        negative_hours = (df['operating_hours'] < 0).sum()
        if negative_hours > 0:
            issues.append(f"{negative_hours} registros com horas negativas")
            suggestions.append("Remova ou corrija valores negativos")
    
    # Verificar datas
    date_cols = ['install_date', 'failure_date']
    for col in date_cols:
        if col in df.columns:
            try:
                pd.to_datetime(df[col], errors='coerce')
            except:
                issues.append(f"Formato de data inválido na coluna '{col}'")
                suggestions.append(f"Use formato padrão de data para '{col}'")
    
    return issues, suggestions

def display_data_overview(df):
    """Exibir overview dos dados"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Registros", f"{len(df):,}")
    
    with col2:
        n_components = df['component'].nunique() if 'component' in df.columns else 0
        st.metric("Componentes Únicos", n_components)
    
    with col3:
        n_assets = df['asset_id'].nunique() if 'asset_id' in df.columns else 0
        st.metric("Ativos Únicos", n_assets)
    
    with col4:
        if 'censored' in df.columns:
            censoring_rate = df['censored'].mean() * 100
            st.metric("Taxa de Censura", f"{censoring_rate:.1f}%")
        else:
            st.metric("Taxa de Censura", "N/A")

def create_data_quality_charts(df):
    """Criar gráficos de qualidade dos dados"""
    
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
    
    # Distribuição de horas operacionais
    if 'operating_hours' in df.columns:
        fig_hours = px.histogram(
            df, 
            x='operating_hours',
            title="Distribuição de Horas Operacionais",
            nbins=50
        )
        fig_hours.update_layout(template='plotly_white')
        st.plotly_chart(fig_hours, use_container_width=True)

def main():
    # Sidebar com configurações
    with st.sidebar:
        st.markdown("## ⚙️ Configurações")
        
        data_source = st.selectbox(
            "Fonte de Dados",
            ["Upload de Arquivo", "Dados de Exemplo", "Conexão SQL", "API/SAP"]
        )
        
        if data_source == "Upload de Arquivo":
            file_format = st.selectbox("Formato", ["CSV", "Excel (XLSX)"])
        
        st.markdown("---")
        st.markdown("## 📋 Validações")
        st.markdown("""
        **Colunas Obrigatórias:**
        - `asset_id`: ID do equipamento
        - `component`: Nome do componente  
        - `operating_hours`: Horas de operação
        
        **Colunas Opcionais:**
        - `install_date`, `failure_date`
        - `fleet`, `subsystem`, `environment`
        - `censored`, `cost`, `downtime_hours`
        """)
    
    # Área principal
    tab1, tab2, tab3 = st.tabs(["📥 Upload", "🔍 Exploração", "✅ Validação"])
    
    with tab1:
        st.markdown("## 📥 Carregar Dados")
        
        if data_source == "Upload de Arquivo":
            uploaded_file = st.file_uploader(
                f"Escolha um arquivo {file_format}",
                type=['csv', 'xlsx'] if file_format == "Excel (XLSX)" else ['csv']
            )
            
            if uploaded_file is not None:
                try:
                    if file_format == "CSV":
                        df = pd.read_csv(uploaded_file)
                    else:
                        df = pd.read_excel(uploaded_file)
                    
                    st.success(f"✅ Arquivo carregado: {len(df)} registros, {len(df.columns)} colunas")
                    st.session_state.dataset = df
                    
                except Exception as e:
                    st.error(f"❌ Erro ao carregar arquivo: {str(e)}")
        
        elif data_source == "Dados de Exemplo":
            if st.button("🔄 Carregar Dados de Exemplo", type="primary"):
                sample_data = load_sample_data()
                if sample_data is not None:
                    st.session_state.dataset = sample_data
                    st.success(f"✅ Dados de exemplo carregados: {len(sample_data)} registros")
                else:
                    st.error("❌ Dados de exemplo não encontrados")
        
        elif data_source == "Conexão SQL":
            st.markdown("### 🔌 Configuração SQL")
            
            col1, col2 = st.columns(2)
            with col1:
                db_type = st.selectbox("Tipo de Banco", ["PostgreSQL", "MySQL", "SQL Server", "Oracle"])
                server = st.text_input("Servidor")
                database = st.text_input("Database")
            
            with col2:
                username = st.text_input("Usuário")
                password = st.text_input("Senha", type="password")
                port = st.number_input("Porta", value=5432)
            
            query = st.text_area(
                "Query SQL",
                placeholder="SELECT * FROM maintenance_records WHERE ..."
            )
            
            if st.button("🔌 Conectar e Carregar"):
                st.info("🚧 Funcionalidade em desenvolvimento")
        
        elif data_source == "API/SAP":
            st.markdown("### 🌐 Integração API")
            
            api_type = st.selectbox("Tipo de API", ["SAP", "REST API", "OData"])
            endpoint = st.text_input("Endpoint/URL")
            api_key = st.text_input("API Key", type="password")
            
            if st.button("🌐 Conectar à API"):
                st.info("🚧 Funcionalidade em desenvolvimento")
    
    with tab2:
        if st.session_state.dataset is not None:
            df = st.session_state.dataset
            
            st.markdown("## 🔍 Exploração dos Dados")
            
            # Overview geral
            display_data_overview(df)
            
            st.markdown("---")
            
            # Visualizar amostra dos dados
            st.markdown("### 📋 Amostra dos Dados")
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
                st.dataframe(col_info)
            
            with col2:
                st.markdown("### 🎯 Valores Únicos")
                selected_col = st.selectbox("Selecionar Coluna", df.columns)
                if selected_col:
                    unique_vals = df[selected_col].value_counts().head(10)
                    st.dataframe(unique_vals)
            
            # Gráficos de qualidade
            st.markdown("---")
            st.markdown("### 📈 Análise de Qualidade")
            
            col1, col2 = st.columns(2)
            with col1:
                create_data_quality_charts(df)
        
        else:
            st.info("📥 Carregue os dados primeiro na aba 'Upload'")
    
    with tab3:
        if st.session_state.dataset is not None:
            df = st.session_state.dataset
            
            st.markdown("## ✅ Validação e Qualidade")
            
            # Executar validação
            if st.button("🔍 Executar Validação", type="primary"):
                with st.spinner("Analisando qualidade dos dados..."):
                    # Validação básica
                    issues, suggestions = validate_uploaded_data(df)
                    
                    # Análise detalhada com DataCleaner
                    cleaner = DataCleaner()
                    quality_report = cleaner.validate_data_quality(df)
                    st.session_state.data_quality_report = quality_report
                    
                    # Exibir resultados
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("### 🚨 Problemas Identificados")
                        if issues:
                            for issue in issues:
                                st.error(f"❌ {issue}")
                        else:
                            st.success("✅ Nenhum problema crítico encontrado")
                    
                    with col2:
                        st.markdown("### 💡 Sugestões")
                        if suggestions:
                            for suggestion in suggestions:
                                st.info(f"💡 {suggestion}")
                        else:
                            st.success("✅ Dados parecem estar em boa qualidade")
            
            # Relatório de qualidade detalhado
            if st.session_state.data_quality_report:
                report = st.session_state.data_quality_report
                
                st.markdown("---")
                st.markdown("### 📊 Relatório de Qualidade Detalhado")
                
                # Score geral
                score = report['quality_score']
                score_color = "green" if score >= 0.8 else "orange" if score >= 0.6 else "red"
                
                st.markdown(f"""
                <div style="background: linear-gradient(90deg, {score_color} {score*100}%, #e5e7eb {score*100}%); 
                           padding: 1rem; border-radius: 8px; color: white; font-weight: bold;">
                    Score de Qualidade: {score:.1%}
                </div>
                """, unsafe_allow_html=True)
                
                # Detalhes por categoria
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("#### 📋 Dados Faltantes")
                    missing_df = pd.DataFrame(list(report['missing_data'].items()), 
                                            columns=['Coluna', 'Percentual'])
                    missing_df['Percentual'] = missing_df['Percentual'].round(1)
                    st.dataframe(missing_df)
                
                with col2:
                    st.markdown("#### 🎯 Outliers Detectados")
                    outliers_df = pd.DataFrame(list(report['outliers'].items()), 
                                             columns=['Coluna', 'Quantidade'])
                    st.dataframe(outliers_df)
                
                with col3:
                    st.markdown("#### 📅 Problemas de Data")
                    date_issues_df = pd.DataFrame(list(report['date_issues'].items()), 
                                                columns=['Tipo', 'Quantidade'])
                    st.dataframe(date_issues_df)
            
            # Opções de limpeza
            st.markdown("---")
            st.markdown("### 🧼 Opções de Limpeza")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🤖 Limpeza Automática", type="primary"):
                    with st.spinner("Aplicando limpeza automática..."):
                        cleaner = DataCleaner()
                        df_clean, cleaning_summary = cleaner.full_cleaning_pipeline(df)
                        
                        st.session_state.dataset = df_clean
                        
                        st.success("✅ Limpeza concluída!")
                        st.json(cleaning_summary)
            
            with col2:
                if st.button("🧠 Limpeza Assistida por IA"):
                    st.info("🚧 Funcionalidade em desenvolvimento")
                    # TODO: Implementar limpeza assistida por IA
        
        else:
            st.info("📥 Carregue os dados primeiro na aba 'Upload'")
    
    # Footer com informações
    if st.session_state.dataset is not None:
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Salvar Dataset Limpo"):
                df = st.session_state.dataset
                csv = df.to_csv(index=False).encode('utf-8')
                
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name='dataset_limpo.csv',
                    mime='text/csv'
                )
        
        with col2:
            if st.button("➡️ Prosseguir para Análise"):
                st.info("Navigate to '📈 Ajuste Weibull' para continuar")
        
        with col3:
            if st.button("🔄 Resetar Dados"):
                st.session_state.dataset = None
                st.session_state.data_quality_report = None
                st.experimental_rerun()

if __name__ == "__main__":
    main()