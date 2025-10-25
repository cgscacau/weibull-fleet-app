"""
🔧 Planejamento PM & Estoque - Versão Final Corrigida
Otimização de intervalos de manutenção preventiva e gestão de peças de reposição
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================================

st.set_page_config(
    page_title="Planejamento PM & Estoque",
    page_icon="🔧",
    layout="wide"
)

# ============================================================================
# FUNÇÕES DE CÁLCULO WEIBULL
# ============================================================================

def calcular_confiabilidade(t, eta, beta):
    """
    Calcula confiabilidade em tempo t usando distribuição Weibull
    R(t) = exp(-(t/η)^β)
    """
    return np.exp(-((t / eta) ** beta))

def calcular_intervalo_pm(eta, beta, confiabilidade_alvo):
    """
    Calcula intervalo PM para atingir confiabilidade alvo
    t = η × (-ln(R))^(1/β)
    """
    if confiabilidade_alvo <= 0 or confiabilidade_alvo >= 1:
        return None
    intervalo = eta * ((-np.log(confiabilidade_alvo)) ** (1 / beta))
    return intervalo

def calcular_mtbf(eta, beta):
    """
    Calcula MTBF usando função gamma
    MTBF = η × Γ(1 + 1/β)
    """
    from scipy.special import gamma
    mtbf = eta * gamma(1 + 1/beta)
    return mtbf

def interpretar_beta(beta):
    """Interpreta o valor de β (parâmetro de forma)"""
    if beta < 1:
        return "⬇️ Mortalidade Infantil", "Falhas decrescem com o tempo"
    elif beta == 1:
        return "➡️ Taxa Constante", "Falhas aleatórias (exponencial)"
    else:
        return "⬆️ Desgaste", "Falhas aumentam com o tempo"

# ============================================================================
# FUNÇÃO DE PLOTAGEM
# ============================================================================

def plotar_curva_confiabilidade(eta, beta, intervalo_pm, confiabilidade_alvo):
    """Plota curva de confiabilidade com intervalo PM recomendado"""
    
    # Gera pontos para a curva
    t_max = min(eta * 3, intervalo_pm * 2.5)
    t = np.linspace(0, t_max, 500)
    R = calcular_confiabilidade(t, eta, beta)
    
    # Cria o gráfico
    fig = go.Figure()
    
    # Curva de confiabilidade
    fig.add_trace(go.Scatter(
        x=t,
        y=R * 100,
        mode='lines',
        name='Confiabilidade',
        line=dict(color='#1f77b4', width=3),
        hovertemplate='<b>Tempo:</b> %{x:.0f}h<br><b>Confiabilidade:</b> %{y:.1f}%<extra></extra>'
    ))
    
    # Linha vertical do intervalo PM
    fig.add_vline(
        x=intervalo_pm,
        line_dash="dash",
        line_color="red",
        line_width=2,
        annotation_text=f"PM Recomendado: {intervalo_pm:.0f}h",
        annotation_position="top"
    )
    
    # Linha horizontal da confiabilidade alvo
    fig.add_hline(
        y=confiabilidade_alvo * 100,
        line_dash="dot",
        line_color="green",
        line_width=2,
        annotation_text=f"Alvo: {confiabilidade_alvo*100:.0f}%",
        annotation_position="left"
    )
    
    # Ponto de intersecção
    fig.add_trace(go.Scatter(
        x=[intervalo_pm],
        y=[confiabilidade_alvo * 100],
        mode='markers',
        name='Ponto PM',
        marker=dict(color='red', size=12, symbol='circle'),
        hovertemplate=f'<b>Intervalo PM:</b> {intervalo_pm:.0f}h<br><b>Confiabilidade:</b> {confiabilidade_alvo*100:.0f}%<extra></extra>'
    ))
    
    # Layout
    fig.update_layout(
        title=dict(
            text='Curva de Confiabilidade Weibull',
            font=dict(size=20, color='#2c3e50')
        ),
        xaxis_title='Tempo (horas)',
        yaxis_title='Confiabilidade (%)',
        hovermode='x unified',
        template='plotly_white',
        height=500,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    fig.update_yaxis(range=[0, 105])
    
    return fig

# ============================================================================
# INTERFACE PRINCIPAL
# ============================================================================

st.title("🔧 Planejamento PM & Estoque")
st.markdown("*Otimização de intervalos de manutenção preventiva e gestão de peças de reposição*")

# ============================================================================
# DETECÇÃO INTELIGENTE DE DADOS
# ============================================================================

# Lista de possíveis chaves onde os dados Weibull podem estar
possible_keys = [
    'weibull_data',
    'df_weibull', 
    'weibull_results',
    'analise_weibull',
    'resultados_weibull',
    'weibull_por_equipamento',
    'weibull_por_componente'
]

# Procura a chave correta
df_weibull = None
key_encontrada = None

for key in possible_keys:
    if key in st.session_state and st.session_state[key] is not None:
        try:
            temp_df = st.session_state[key]
            # Verifica se tem as colunas necessárias
            if isinstance(temp_df, pd.DataFrame):
                # Procura por colunas de identificador
                id_cols = ['identificador', 'equipamento', 'componente', 'item', 'id']
                has_id = any(col in temp_df.columns for col in id_cols)
                
                # Procura por parâmetros Weibull
                has_eta = any(col in temp_df.columns for col in ['eta', 'η', 'scale', 'escala'])
                has_beta = any(col in temp_df.columns for col in ['beta', 'β', 'shape', 'forma'])
                
                if has_id and has_eta and has_beta:
                    df_weibull = temp_df.copy()
                    key_encontrada = key
                    break
        except:
            continue

# Se não encontrou, tenta ver o que tem no session_state
if df_weibull is None:
    st.warning("⚠️ **Nenhum dado Weibull carregado!**")
    
    # Mostra debug info
    with st.expander("🔍 Debug: Session State Disponível"):
        st.write("**Chaves disponíveis:**")
        for key in st.session_state.keys():
            valor = st.session_state[key]
            if isinstance(valor, pd.DataFrame):
                st.write(f"- `{key}`: DataFrame com {len(valor)} linhas e colunas: {list(valor.columns)}")
            else:
                st.write(f"- `{key}`: {type(valor).__name__}")
    
    st.info("""
    📋 **Para usar esta página, você precisa:**
    
    1. Ir para a página **"Ajuste Weibull UNIFIED"**
    2. Fazer upload dos dados
    3. Executar a análise Weibull
    4. Depois voltar para esta página
    
    Os dados devem conter as colunas:
    - Identificador (equipamento/componente)
    - `eta` ou `η` (parâmetro de escala)
    - `beta` ou `β` (parâmetro de forma)
    """)
    st.stop()

# ============================================================================
# NORMALIZAÇÃO DE NOMES DE COLUNAS
# ============================================================================

# Identifica a coluna de identificador
id_col = None
for col in ['identificador', 'equipamento', 'componente', 'item', 'id']:
    if col in df_weibull.columns:
        id_col = col
        break

if id_col is None:
    st.error("❌ Coluna de identificador não encontrada!")
    st.stop()

# Padroniza nome para 'identificador'
if id_col != 'identificador':
    df_weibull = df_weibull.rename(columns={id_col: 'identificador'})

# Identifica coluna eta
eta_col = None
for col in ['eta', 'η', 'scale', 'escala']:
    if col in df_weibull.columns:
        eta_col = col
        break

if eta_col and eta_col != 'eta':
    df_weibull = df_weibull.rename(columns={eta_col: 'eta'})

# Identifica coluna beta
beta_col = None
for col in ['beta', 'β', 'shape', 'forma']:
    if col in df_weibull.columns:
        beta_col = col
        break

if beta_col and beta_col != 'beta':
    df_weibull = df_weibull.rename(columns={beta_col: 'beta'})

# Valida colunas necessárias
if 'eta' not in df_weibull.columns or 'beta' not in df_weibull.columns:
    st.error(f"❌ **Erro:** Dados não contêm parâmetros Weibull necessários (eta e beta)")
    st.write("**Colunas disponíveis:**", list(df_weibull.columns))
    st.stop()

# Remove registros com valores inválidos
df_weibull = df_weibull[
    (df_weibull['eta'].notna()) & 
    (df_weibull['beta'].notna()) &
    (df_weibull['eta'] > 0) &
    (df_weibull['beta'] > 0)
].copy()

if len(df_weibull) == 0:
    st.error("❌ **Erro:** Nenhum registro válido encontrado nos dados Weibull.")
    st.stop()

# ============================================================================
# MENSAGEM DE SUCESSO
# ============================================================================

st.success(f"✅ **Dados Weibull encontrados!** (Fonte: `{key_encontrada}` com {len(df_weibull)} registros)")

# ============================================================================
# TABS
# ============================================================================

tab1, tab2, tab3 = st.tabs([
    "🔧 Planejamento PM",
    "📦 Gestão de Estoque", 
    "📊 Análise de Cenários"
])

# ============================================================================
# TAB 1: PLANEJAMENTO PM
# ============================================================================

with tab1:
    st.header("🔧 Planejamento de Manutenção Preventiva")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("⚙️ Parâmetros")
        
        # Seleção de equipamento/componente
        identificador_selecionado = st.selectbox(
            "Selecione o Equipamento/Componente:",
            options=sorted(df_weibull['identificador'].unique()),
            help="Escolha o equipamento ou componente para calcular o intervalo PM"
        )
        
        # Filtra dados do equipamento selecionado
        registro = df_weibull[df_weibull['identificador'] == identificador_selecionado].iloc[0]
        
        eta = registro['eta']
        beta = registro['beta']
        
        # Exibe parâmetros Weibull
        st.markdown("---")
        st.markdown("**📊 Parâmetros Weibull:**")
        
        param_col1, param_col2 = st.columns(2)
        with param_col1:
            st.metric("η (Escala)", f"{eta:.1f}h", help="Tempo característico")
        with param_col2:
            st.metric("β (Forma)", f"{beta:.2f}", help="Comportamento da falha")
        
        # Interpreta beta
        tipo_falha, descricao = interpretar_beta(beta)
        st.info(f"**{tipo_falha}**\n\n{descricao}")
        
        # MTBF
        mtbf = calcular_mtbf(eta, beta)
        st.metric("MTBF", f"{mtbf:.1f}h", help="Mean Time Between Failures")
        
        st.markdown("---")
        
        # Nível de confiabilidade desejado
        confiabilidade_alvo = st.slider(
            "Nível de Confiabilidade Alvo:",
            min_value=0.80,
            max_value=0.99,
            value=0.90,
            step=0.01,
            format="%.0f%%",
            help="Define o nível mínimo de confiabilidade desejado"
        ) 
        
        # Calcula intervalo PM
        intervalo_pm = calcular_intervalo_pm(eta, beta, confiabilidade_alvo)
        
        st.markdown("---")
        
        # Resultado principal
        st.markdown("### 🎯 **Resultado:**")
        st.metric(
            label="Intervalo PM Recomendado",
            value=f"{intervalo_pm:.0f} horas",
            delta=f"{(intervalo_pm/mtbf - 1)*100:+.1f}% vs MTBF",
            help=f"Executar PM a cada {intervalo_pm:.0f}h garante {confiabilidade_alvo*100:.0f}% de confiabilidade"
        )
        
        # Informações adicionais
        with st.expander("ℹ️ Como Interpretar"):
            st.markdown(f"""
            **Intervalo PM Calculado:** `{intervalo_pm:.0f} horas`
            
            Isso significa que você deve executar manutenção preventiva a cada **{intervalo_pm:.0f} horas** 
            de operação para garantir que o equipamento/componente mantenha pelo menos 
            **{confiabilidade_alvo*100:.0f}% de confiabilidade**.
            
            ---
            
            **Comparação com MTBF:**
            - MTBF = {mtbf:.0f}h (tempo médio entre falhas)
            - Intervalo PM = {intervalo_pm:.0f}h
            - Razão PM/MTBF = {intervalo_pm/mtbf:.2f}
            
            {"✅ Intervalo PM **menor** que MTBF = Manutenção **proativa**" if intervalo_pm < mtbf else "⚠️ Intervalo PM **maior** que MTBF = Revise a estratégia"}
            
            ---
            
            **Fórmula Utilizada:**
            ```
            t_PM = η × (-ln(R))^(1/β)
            ```
            Onde:
            - t_PM = Intervalo PM
            - η = {eta:.1f} (parâmetro de escala)
            - β = {beta:.2f} (parâmetro de forma)
            - R = {confiabilidade_alvo:.2f} (confiabilidade alvo)
            """)
    
    with col2:
        st.subheader("📈 Análise Gráfica")
        
        # Plota curva de confiabilidade
        fig = plotar_curva_confiabilidade(eta, beta, intervalo_pm, confiabilidade_alvo)
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabela de intervalos para diferentes confiabilidades
        st.markdown("---")
        st.markdown("### 📋 Tabela de Intervalos PM por Confiabilidade")
        
        confs = [0.80, 0.85, 0.90, 0.95, 0.99]
        dados_tabela = []
        
        for conf in confs:
            int_pm = calcular_intervalo_pm(eta, beta, conf)
            conf_no_mtbf = calcular_confiabilidade(mtbf, eta, beta)
            dados_tabela.append({
                'Confiabilidade Alvo': f"{conf*100:.0f}%",
                'Intervalo PM (h)': f"{int_pm:.0f}",
                'Dias (24h/dia)': f"{int_pm/24:.1f}",
                'Razão PM/MTBF': f"{int_pm/mtbf:.2f}",
                'Status': '✅ Recomendado' if conf == confiabilidade_alvo else ''
            })
        
        df_tabela = pd.DataFrame(dados_tabela)
        st.dataframe(df_tabela, use_container_width=True, hide_index=True)
        
        # Recomendações
        st.markdown("---")
        st.markdown("### 💡 Recomendações")
        
        if beta < 1:
            st.info("""
            **🔍 Mortalidade Infantil Detectada (β < 1)**
            
            - Falhas ocorrem mais no início da vida útil
            - **Recomendação:** Melhore o processo de instalação e burn-in
            - Considere período de garantia estendido
            """)
        elif beta > 3:
            st.warning("""
            **⚠️ Desgaste Acelerado (β > 3)**
            
            - Taxa de falha aumenta rapidamente com o tempo
            - **Recomendação:** Intervalos PM mais curtos são críticos
            - Considere substituição preventiva antes do desgaste
            """)
        else:
            st.success("""
            **✅ Comportamento Normal de Desgaste**
            
            - Taxa de falha aumenta gradualmente
            - Intervalos PM calculados são adequados
            - Mantenha registro e monitore a efetividade
            """)

# ============================================================================
# TAB 2: GESTÃO DE ESTOQUE
# ============================================================================

with tab2:
    st.header("📦 Gestão de Estoque de Peças")
    st.info("🚧 **Módulo em desenvolvimento**")
    
    st.markdown("""
    ### Funcionalidades Planejadas:
    
    - 📊 Cálculo de estoque de segurança
    - 🔄 Política de reposição automática
    - 💰 Otimização de custos de estoque
    - 📈 Previsão de demanda de peças
    - 🎯 Análise ABC de peças críticas
    """)

# ============================================================================
# TAB 3: ANÁLISE DE CENÁRIOS
# ============================================================================

with tab3:
    st.header("📊 Análise de Cenários")
    st.info("🚧 **Módulo em desenvolvimento**")
    
    st.markdown("""
    ### Funcionalidades Planejadas:
    
    - 🔮 Simulação What-If
    - 📉 Análise de sensibilidade
    - ⚖️ Comparação de estratégias PM
    - 💵 Análise custo-benefício
    - 🎲 Simulação Monte Carlo
    """)

# ============================================================================
# SIDEBAR COM DICAS
# ============================================================================

with st.sidebar:
    st.markdown("---")
    st.markdown("### 💡 Dicas")
    
    st.markdown("""
    **Para calcular PM ideal:**
    
    1. Execute análise Weibull primeiro
    2. Defina confiabilidade alvo (geralmente 90%)
    3. Considere custos operacionais
    4. Ajuste baseado em experiência prática
    """)
    
    st.markdown("---")
    st.markdown("### 📚 Confiabilidade típica:")
    
    st.markdown("""
    - **Crítico:** 95-99%
    - **Importante:** 90-95%
    - **Normal:** 80-90%
    """)
    
    st.markdown("---")
    
    # Estatísticas dos dados
    if len(df_weibull) > 0:
        st.markdown("### 📊 Estatísticas dos Dados")
        st.metric("Total de Equipamentos/Componentes", len(df_weibull))
        st.metric("β Médio", f"{df_weibull['beta'].mean():.2f}")
        st.metric("η Médio", f"{df_weibull['eta'].mean():.1f}h")
        
        # Mostra fonte dos dados
        st.markdown("---")
        st.markdown(f"**🔗 Fonte dos dados:**")
        st.code(key_encontrada, language=None)
