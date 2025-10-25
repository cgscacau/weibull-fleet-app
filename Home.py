"""
Página principal do Weibull Fleet Analytics
ENTRYPOINT para Streamlit Cloud - mantém estrutura multipage
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys
import os

# Adicionar diretórios ao path
project_root = Path(__file__).parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "app"))

# Garantir que o Python encontra os módulos
os.chdir(str(project_root))

from core.weibull import WeibullAnalysis
from dataops.clean import DataCleaner
from ai.ai_assistant import WeibullAIAssistant

# Configuração da página
st.set_page_config(
    page_title="Weibull Fleet Analytics",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1e3a8a;
        text-align: center;
        margin-bottom: 2rem;
    }
    .feature-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
    .metric-card {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #3b82f6;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def load_sample_data():
    """Carregar dados de exemplo se disponíveis"""
    sample_file = project_root / "storage" / "sample_fleet_data.csv"
    if sample_file.exists():
        return pd.read_csv(sample_file)
    return None

def create_overview_dashboard(df):
    """Criar dashboard overview dos dados"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>📊 Total de Registros</h3>
            <h2>{:,}</h2>
        </div>
        """.format(len(df)), unsafe_allow_html=True)
    
    with col2:
        n_components = df['component'].nunique() if 'component' in df.columns else 0
        st.markdown("""
        <div class="metric-card">
            <h3>⚙️ Componentes</h3>
            <h2>{}</h2>
        </div>
        """.format(n_components), unsafe_allow_html=True)
    
    with col3:
        n_fleets = df['fleet'].nunique() if 'fleet' in df.columns else 0
        st.markdown("""
        <div class="metric-card">
            <h3>🚛 Frotas</h3>
            <h2>{}</h2>
        </div>
        """.format(n_fleets), unsafe_allow_html=True)
    
    with col4:
        censoring_rate = df['censored'].mean() * 100 if 'censored' in df.columns else 0
        st.markdown("""
        <div class="metric-card">
            <h3>📈 Taxa de Censura</h3>
            <h2>{:.1f}%</h2>
        </div>
        """.format(censoring_rate), unsafe_allow_html=True)

def create_component_distribution_chart(df):
    """Criar gráfico de distribuição de componentes"""
    if 'component' not in df.columns:
        return None
    
    component_counts = df['component'].value_counts().head(10)
    
    fig = px.bar(
        x=component_counts.values,
        y=component_counts.index,
        orientation='h',
        title="Top 10 Componentes por Número de Registros",
        labels={'x': 'Número de Registros', 'y': 'Componente'}
    )
    
    fig.update_layout(
        height=400,
        template='plotly_white',
        title_font_size=16
    )
    
    return fig

def create_fleet_overview_chart(df):
    """Criar gráfico overview por frota"""
    if 'fleet' not in df.columns:
        return None
    
    fleet_summary = df.groupby('fleet').agg({
        'operating_hours': 'mean',
        'censored': lambda x: (1-x).mean()  # Taxa de falha
    }).round(2)
    
    fig = px.scatter(
        fleet_summary,
        x='operating_hours',
        y='censored',
        size=df['fleet'].value_counts(),
        hover_name=fleet_summary.index,
        title="Overview por Frota: Horas Médias vs Taxa de Falha",
        labels={
            'operating_hours': 'Horas Operacionais Médias',
            'censored': 'Taxa de Falha',
            'size': 'Número de Registros'
        }
    )
    
    fig.update_layout(
        height=400,
        template='plotly_white',
        title_font_size=16
    )
    
    return fig

def main():
    # Header principal
    st.markdown('<h1 class="main-header">⚙️ Weibull Fleet Analytics</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem; font-size: 1.2rem; color: #64748b;">
        Sistema avançado de análise de confiabilidade com IA assistiva para gestão de frotas industriais
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar com informações
    with st.sidebar:
        st.markdown("## 🎯 Navegação")
        st.markdown("""
        **Fluxo Recomendado:**
        1. 📥 **Dados** - Upload e conexão
        2. 🧼 **Qualidade** - Limpeza assistida por IA  
        3. 📈 **Análise Weibull** - Ajuste e gráficos
        4. 🛠️ **Planejamento** - PM e estoque
        5. 🔍 **Comparativos** - Benchmarking
        6. 🧠 **Relatório IA** - Insights automáticos
        """)
        
        st.markdown("---")
        st.markdown("## ⚡ Status do Sistema")
        
        # Verificar dependências
        try:
            import scipy
            st.success("✅ SciPy disponível")
        except:
            st.error("❌ SciPy não encontrado")
        
        try:
            sample_data = load_sample_data()
            if sample_data is not None:
                st.success("✅ Dados de exemplo carregados")
            else:
                st.warning("⚠️ Dados de exemplo não encontrados")
        except:
            st.error("❌ Erro ao carregar dados")
    
    # Seção de funcionalidades
    st.markdown("## 🚀 Funcionalidades Principais")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>📊 Análise Weibull Avançada</h3>
            <ul>
                <li>Ajuste por MLE com censura</li>
                <li>Gráficos de probabilidade</li>
                <li>Intervalos de confiança</li>
                <li>Comparação de modelos</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>🤖 IA Assistiva</h3>
            <ul>
                <li>Limpeza automática de dados</li>
                <li>Explicações em linguagem simples</li>
                <li>Sugestões de estratégias</li>
                <li>Relatórios executivos</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>📋 Planejamento Inteligente</h3>
            <ul>
                <li>Intervalos ótimos de PM</li>
                <li>Gestão de estoque</li>
                <li>Análise de cenários</li>
                <li>ROI de estratégias</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Dashboard overview se dados disponíveis
    sample_data = load_sample_data()
    if sample_data is not None:
        st.markdown("---")
        st.markdown("## 📈 Overview dos Dados de Exemplo")
        
        # Métricas gerais
        create_overview_dashboard(sample_data)
        
        # Gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            fig1 = create_component_distribution_chart(sample_data)
            if fig1:
                st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            fig2 = create_fleet_overview_chart(sample_data)
            if fig2:
                st.plotly_chart(fig2, use_container_width=True)
        
        # Quick analysis
        st.markdown("### 🔍 Análise Rápida")
        
        # Componente com mais falhas
        if 'component' in sample_data.columns and 'censored' in sample_data.columns:
            failure_rate_by_component = sample_data.groupby('component')['censored'].apply(lambda x: (1-x).mean()).sort_values(ascending=False)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**🔴 Componentes Mais Críticos:**")
                for i, (component, rate) in enumerate(failure_rate_by_component.head(3).items()):
                    st.write(f"{i+1}. {component}: {rate:.1%} taxa de falha")
            
            with col2:
                st.markdown("**✅ Componentes Mais Confiáveis:**")
                for i, (component, rate) in enumerate(failure_rate_by_component.tail(3).items()):
                    st.write(f"{i+1}. {component}: {rate:.1%} taxa de falha")
    
    # Seção de primeiros passos
    st.markdown("---")
    st.markdown("## 🎯 Primeiros Passos")
    
    with st.expander("📥 Como carregar seus dados", expanded=False):
        st.markdown("""
        **Formatos Suportados:**
        - CSV, Excel (XLSX)
        - Conexão SQL direta
        - APIs de sistemas ERP/SAP
        
        **Colunas Requeridas:**
        - `asset_id`: ID único do equipamento
        - `component`: Nome do componente
        - `install_date`: Data de instalação
        - `operating_hours`: Horas de operação
        - `failure_date`: Data de falha (opcional se censurado)
        
        **Colunas Opcionais:**
        - `fleet`, `subsystem`, `environment`, `operator`, `cost`, `downtime_hours`
        """)

    with st.expander("📊 Exemplo de análise Weibull"):
        st.markdown("""
        **Processo Típico:**
        1. **Upload de dados** → Validação automática
        2. **Limpeza de dados** → IA identifica e corrige problemas
        3. **Seleção de componente** → Escolher item para análise
        4. **Ajuste Weibull** → Calcular β (forma) e η (escala)
        5. **Interpretação** → IA explica resultados em linguagem simples
        6. **Recomendações** → Intervalos de PM e estratégias
        """)

    with st.expander("🤖 Como a IA pode ajudar"):
        st.markdown("""
        **Limpeza de Dados:**
        - Normalizar nomes de componentes e frotas
        - Detectar e corrigir outliers
        - Identificar dados inconsistentes
        
        **Análise Inteligente:**
        - Explicar significado dos parâmetros Weibull
        - Sugerir modelos alternativos (Exponencial, Lognormal)
        - Recomendar estratégias de manutenção
        
        **Relatórios Automáticos:**
        - Sumários executivos
        - Análises comparativas
        - Recomendações acionáveis
        """)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #64748b; margin-top: 2rem;">
        <strong>Weibull Fleet Analytics</strong> - Sistema de análise de confiabilidade com IA<br>
        Desenvolvido para gestão inteligente de manutenção industrial
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
