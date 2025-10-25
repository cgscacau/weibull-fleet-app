import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Dados", page_icon="📊", layout="wide")

st.title("📊 Importação e Visualização de Dados")

st.markdown("""
### Instruções para Upload de Dados

Faça upload de um arquivo CSV contendo os dados de falhas da frota. O arquivo deve conter pelo menos as seguintes colunas:

**Colunas Obrigatórias:**
- **Tempo**: tempo até a falha ou censura (valores numéricos positivos)
- **Status**: indicador de falha (1) ou censura (0)

**Colunas Opcionais:**
- **ID**: identificador único do equipamento
- **Modelo**: modelo do equipamento
- Outras variáveis relevantes para análise
""")

# Upload do arquivo
uploaded_file = st.file_uploader("Escolha um arquivo CSV", type="csv")

if uploaded_file is not None:
    try:
        # Leitura do arquivo
        df = pd.read_csv(uploaded_file)
        
        # Validação das colunas obrigatórias
        colunas_obrigatorias = ['Tempo', 'Status']
        colunas_faltantes = [col for col in colunas_obrigatorias if col not in df.columns]
        
        if colunas_faltantes:
            st.error(f"❌ Colunas obrigatórias faltando: {', '.join(colunas_faltantes)}")
            st.info("Por favor, certifique-se de que seu arquivo CSV contém as colunas 'Tempo' e 'Status'.")
        else:
            # Validação dos dados
            erros = []
            
            # Verificar se Tempo é numérico e positivo
            if not pd.api.types.is_numeric_dtype(df['Tempo']):
                erros.append("A coluna 'Tempo' deve conter apenas valores numéricos.")
            elif (df['Tempo'] <= 0).any():
                erros.append("A coluna 'Tempo' deve conter apenas valores positivos.")
            
            # Verificar se Status contém apenas 0 e 1
            if not df['Status'].isin([0, 1]).all():
                erros.append("A coluna 'Status' deve conter apenas valores 0 (censura) ou 1 (falha).")
            
            # Verificar valores nulos
            if df[colunas_obrigatorias].isnull().any().any():
                erros.append("Existem valores nulos nas colunas obrigatórias.")
            
            if erros:
                st.error("❌ Erros encontrados nos dados:")
                for erro in erros:
                    st.write(f"- {erro}")
            else:
                # Salvar dados na sessão
                st.session_state.df = df
                st.session_state.dados_carregados = True
                
                st.success("✅ Arquivo carregado e validado com sucesso!")
                
                # Divisor
                st.divider()
                
                # Seção de Prévia dos Dados
                st.subheader("📋 Prévia dos Dados")
                st.dataframe(df.head(10), use_container_width=True)
                
                # Seção de Métricas Gerais
                st.subheader("📈 Métricas Gerais")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total de Registros", len(df))
                
                with col2:
                    st.metric("Número de Colunas", len(df.columns))
                
                with col3:
                    falhas = int(df['Status'].sum())
                    st.metric("Número de Falhas", falhas)
                
                with col4:
                    censuras = int((df['Status'] == 0).sum())
                    st.metric("Número de Censuras", censuras)
                
                # Divisor
                st.divider()
                
                # Seção de Estatísticas Descritivas
                st.subheader("📊 Estatísticas Descritivas")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Coluna Tempo:**")
                    stats_tempo = df['Tempo'].describe()
                    st.dataframe(stats_tempo, use_container_width=True)
                
                with col2:
                    st.write("**Distribuição de Status:**")
                    status_counts = df['Status'].value_counts().sort_index()
                    status_df = pd.DataFrame({
                        'Status': ['Censura (0)', 'Falha (1)'],
                        'Quantidade': [status_counts.get(0, 0), status_counts.get(1, 0)],
                        'Percentual': [
                            f"{(status_counts.get(0, 0) / len(df) * 100):.2f}%",
                            f"{(status_counts.get(1, 0) / len(df) * 100):.2f}%"
                        ]
                    })
                    st.dataframe(status_df, use_container_width=True, hide_index=True)
                
                # Divisor
                st.divider()
                
                # Seção de Visualizações
                st.subheader("📉 Visualizações dos Dados")
                
                tab1, tab2, tab3 = st.tabs(["Histograma de Tempo", "Distribuição de Status", "Box Plot"])
                
                with tab1:
                    fig_hist = px.histogram(
                        df, 
                        x='Tempo', 
                        nbins=30,
                        title='Distribuição do Tempo até Falha/Censura',
                        labels={'Tempo': 'Tempo', 'count': 'Frequência'},
                        color_discrete_sequence=['#1f77b4']
                    )
                    fig_hist.update_layout(showlegend=False, height=400)
                    st.plotly_chart(fig_hist, use_container_width=True)
                
                with tab2:
                    status_labels = {0: 'Censura', 1: 'Falha'}
                    df_temp = df.copy()
                    df_temp['Status_Label'] = df_temp['Status'].map(status_labels)
                    
                    fig_pie = px.pie(
                        df_temp, 
                        names='Status_Label',
                        title='Proporção de Falhas vs Censuras',
                        color='Status_Label',
                        color_discrete_map={'Censura': '#ff7f0e', 'Falha': '#2ca02c'}
                    )
                    fig_pie.update_layout(height=400)
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with tab3:
                    df_temp = df.copy()
                    df_temp['Status_Label'] = df_temp['Status'].map(status_labels)
                    
                    fig_box = px.box(
                        df_temp,
                        x='Status_Label',
                        y='Tempo',
                        title='Distribuição do Tempo por Status',
                        labels={'Status_Label': 'Status', 'Tempo': 'Tempo'},
                        color='Status_Label',
                        color_discrete_map={'Censura': '#ff7f0e', 'Falha': '#2ca02c'}
                    )
                    fig_box.update_layout(showlegend=False, height=400)
                    st.plotly_chart(fig_box, use_container_width=True)
                
                # Divisor
                st.divider()
                
                # Seção de Download
                st.subheader("💾 Download dos Dados")
                
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Baixar dados processados (CSV)",
                    data=csv,
                    file_name='dados_processados.csv',
                    mime='text/csv',
                )
                
    except Exception as e:
        st.error(f"❌ Erro ao processar o arquivo: {str(e)}")
        st.info("Verifique se o arquivo está no formato CSV correto e tente novamente.")

else:
    st.info("👆 Por favor, faça upload de um arquivo CSV para começar a análise.")
    
    # Verificar se existem dados na sessão
    if 'df' in st.session_state and 'dados_carregados' in st.session_state:
        st.divider()
        st.warning("⚠️ Dados anteriores ainda estão carregados na sessão.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Registros na Sessão", len(st.session_state.df))
        
        with col2:
            if st.button("🗑️ Limpar dados da sessão", type="secondary"):
                del st.session_state.df
                if 'dados_carregados' in st.session_state:
                    del st.session_state.dados_carregados
                st.rerun()

# Rodapé informativo
st.divider()
st.markdown("""
**💡 Dicas:**
- Certifique-se de que seu arquivo CSV está codificado em UTF-8
- Os valores de tempo devem ser numéricos e positivos
- A coluna Status deve conter apenas 0 (censura) ou 1 (falha)
- Após carregar os dados, você pode prosseguir para a página de análise Weibull
""")
