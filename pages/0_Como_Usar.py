import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import io

from utils.state_manager import initialize_session_state
initialize_session_state()


# Adiciona o diretório raiz ao path
root_path = Path(__file__).parent.parent
sys.path.insert(0, str(root_path))

# Configuração da página
st.set_page_config(
    page_title="Como Usar - Tutorial",
    page_icon="📚",
    layout="wide"
)

# === IMPORTS ===
from utils.navigation import handle_navigation
# ... outros imports ...

# === PROCESSA NAVEGAÇÃO PENDENTE ===
handle_navigation()

# CSS customizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .tutorial-card {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    .step-number {
        display: inline-block;
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 50%;
        text-align: center;
        line-height: 40px;
        font-weight: bold;
        font-size: 1.2rem;
        margin-right: 1rem;
    }
    .download-section {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin: 2rem 0;
    }
    .glossary-term {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        border-left: 3px solid #667eea;
    }
    .example-box {
        background: #e7f3ff;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
        border: 2px dashed #2196f3;
    }
    .warning-box {
        background: #fff3cd;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
    .success-box {
        background: #d4edda;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .info-box {
        background: #d1ecf1;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #17a2b8;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">📚 Como Usar o Sistema Weibull Fleet Analytics</div>', unsafe_allow_html=True)
st.markdown("**Guia completo para análise de confiabilidade e otimização de manutenção**")

# Tabs principais
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎯 Visão Geral",
    "📊 Tutorial Passo-a-Passo",
    "📥 Templates e Downloads",
    "📖 Glossário",
    "❓ FAQ"
])

# ============================================================================
# TAB 1: VISÃO GERAL
# ============================================================================
with tab1:
    st.markdown("## 🎯 O que é Análise de Weibull?")
    
    st.markdown("""
    <div class="tutorial-card">
    <h3>📊 Análise de Confiabilidade com Distribuição de Weibull</h3>
    
    A **Distribuição de Weibull** é o método estatístico mais utilizado mundialmente para:
    
    - ✅ **Prever quando equipamentos vão falhar**
    - ✅ **Calcular intervalos ótimos de manutenção preventiva**
    - ✅ **Dimensionar estoques de peças sobressalentes**
    - ✅ **Reduzir custos de manutenção em 30-50%**
    - ✅ **Evitar paradas não planejadas**
    
    <br>
    
    ### 🏭 Aplicações Práticas:
    
    - **Frotas de Veículos:** Caminhões, ônibus, tratores
    - **Indústria:** Motores, bombas, válvulas, rolamentos
    - **Mineração:** Equipamentos pesados, correias transportadoras
    - **Oil & Gas:** Compressores, turbinas, trocadores de calor
    - **Manufatura:** Linhas de produção, robôs, prensas
    
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="success-box">
        <h4>✅ Benefícios Comprovados</h4>
        
        - 📉 Redução de 30-50% em paradas não planejadas
        - 💰 Economia de 20-40% em custos de manutenção
        - 📦 Otimização de 25-35% no estoque de peças
        - ⏱️ Aumento de 15-25% na disponibilidade
        - 📊 Decisões baseadas em dados reais
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="info-box">
        <h4>📋 O que Você Precisa</h4>
        
        - 📁 Histórico de falhas dos equipamentos
        - ⏱️ Tempos de operação até falha (horas)
        - 🔧 Identificação dos componentes
        - 📊 Mínimo de 20-30 observações por tipo
        - 🎯 Dados de censura (opcional)
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("## 🔄 Fluxo de Trabalho do Sistema")
    
    st.markdown("""
    <div class="tutorial-card">
    
    <div style="margin: 2rem 0;">
        <span class="step-number">1</span>
        <strong style="font-size: 1.2rem;">📁 Upload de Dados</strong>
        <p style="margin-left: 4rem; color: #666;">
        Carregue sua planilha CSV/Excel com histórico de falhas
        </p>
    </div>
    
    <div style="margin: 2rem 0;">
        <span class="step-number">2</span>
        <strong style="font-size: 1.2rem;">🧼 Qualidade dos Dados</strong>
        <p style="margin-left: 4rem; color: #666;">
        Sistema verifica e limpa automaticamente dados inconsistentes
        </p>
    </div>
    
    <div style="margin: 2rem 0;">
        <span class="step-number">3</span>
        <strong style="font-size: 1.2rem;">📈 Ajuste Weibull</strong>
        <p style="margin-left: 4rem; color: #666;">
        Calcula parâmetros β (forma) e η (escala) para cada componente
        </p>
    </div>
    
    <div style="margin: 2rem 0;">
        <span class="step-number">4</span>
        <strong style="font-size: 1.2rem;">🛠️ Planejamento PM</strong>
        <p style="margin-left: 4rem; color: #666;">
        Define intervalos ótimos de manutenção preventiva
        </p>
    </div>
    
    <div style="margin: 2rem 0;">
        <span class="step-number">5</span>
        <strong style="font-size: 1.2rem;">📦 Gestão de Estoque</strong>
        <p style="margin-left: 4rem; color: #666;">
        Calcula quantidade ótima de peças sobressalentes
        </p>
    </div>
    
    <div style="margin: 2rem 0;">
        <span class="step-number">6</span>
        <strong style="font-size: 1.2rem;">📊 Relatórios</strong>
        <p style="margin-left: 4rem; color: #666;">
        Gera relatórios executivos e comparativos
        </p>
    </div>
    
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# TAB 2: TUTORIAL PASSO-A-PASSO
# ============================================================================
with tab2:
    st.markdown("## 📊 Tutorial Completo - Do Zero ao Resultado")
    
    # PASSO 1
    st.markdown("### 📁 PASSO 1: Preparar e Carregar Dados")
    
    st.markdown("""
    <div class="tutorial-card">
    
    <h4>📋 Estrutura da Planilha</h4>
    
    Sua planilha deve conter estas colunas (nomes exatos):
    
    | Coluna | Descrição | Exemplo | Obrigatório |
    |--------|-----------|---------|-------------|
    | `component_id` | Identificador único do equipamento | "MOTOR_001" | ✅ Sim |
    | `component_type` | Tipo/modelo do componente | "Motor Elétrico" | ✅ Sim |
    | `failure_time` | Tempo até falha (horas) | 5420 | ✅ Sim |
    | `censored` | 0=falhou, 1=ainda funcionando | 0 ou 1 | ✅ Sim |
    | `installation_date` | Data de instalação | "2020-01-15" | ❌ Opcional |
    | `failure_date` | Data da falha | "2021-08-20" | ❌ Opcional |
    | `location` | Localização | "Planta A" | ❌ Opcional |
    | `severity` | Gravidade (1-5) | 3 | ❌ Opcional |
    
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="example-box">
    <h4>💡 Exemplo Prático</h4>
    
    **Cenário:** Você tem 50 motores elétricos instalados na sua frota.
    
    - **Motor_001** falhou após **5.420 horas** → `failure_time=5420`, `censored=0`
    - **Motor_002** falhou após **3.890 horas** → `failure_time=3890`, `censored=0`
    - **Motor_003** está funcionando há **6.100 horas** → `failure_time=6100`, `censored=1`
    
    ✅ **Motor_003 é "censurado"** porque ainda não falhou (dados até hoje)
    
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="warning-box">
    <h4>⚠️ Erros Comuns a Evitar</h4>
    
    - ❌ **Nomes de colunas errados** (use exatamente: `component_id`, `component_type`, `failure_time`, `censored`)
    - ❌ **Tempos negativos ou zero**
    - ❌ **Valores de `censored` diferentes de 0 ou 1**
    - ❌ **Dados faltando em colunas obrigatórias**
    - ❌ **Unidades inconsistentes** (misturar horas com dias)
    - ❌ **Menos de 20 observações por componente** (mínimo recomendado)
    
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # PASSO 2
    st.markdown("### 🧼 PASSO 2: Verificar Qualidade dos Dados")
    
    st.markdown("""
    <div class="tutorial-card">
    
    <h4>🔍 O que o Sistema Verifica Automaticamente</h4>
    
    1. **Valores Faltando:** Identifica células vazias em colunas críticas
    2. **Outliers:** Detecta valores anormalmente altos ou baixos
    3. **Duplicatas:** Encontra registros duplicados
    4. **Inconsistências:** Valida tipos de dados e formatos
    5. **Qualidade Estatística:** Verifica se há dados suficientes
    
    <br>
    
    <h4>🤖 IA Assistente</h4>
    
    O sistema usa IA para:
    - 💡 **Sugerir correções** automáticas
    - 📊 **Explicar problemas** encontrados
    - 🔧 **Recomendar tratamentos** de dados
    - ✅ **Validar qualidade** antes da análise
    
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # PASSO 3
    st.markdown("### 📈 PASSO 3: Realizar Ajuste Weibull")
    
    st.markdown("""
    <div class="tutorial-card">
    
    <h4>📊 Entendendo os Parâmetros Weibull</h4>
    
    A distribuição de Weibull tem 2 parâmetros principais:
    
    <br>
    
    **1. β (Beta) - Parâmetro de Forma** 🎯
    
    Define o **tipo de falha** do componente:
    
    - **β < 1** (ex: β = 0.8)
      - 📉 Taxa de falha **decrescente**
      - 🔧 **Falhas infantis** (defeitos de fabricação)
      - 💡 **Ação:** Implementar burn-in, melhorar QC
      
    - **β ≈ 1** (ex: β = 0.9 a 1.1)
      - 📊 Taxa de falha **constante**
      - 🎲 **Falhas aleatórias** (não previsíveis)
      - 💡 **Ação:** Manter peças de reposição, manutenção reativa
      
    - **β > 1** (ex: β = 2.5)
      - 📈 Taxa de falha **crescente**
      - ⏰ **Falhas por desgaste** (envelhecimento)
      - 💡 **Ação:** Manutenção preventiva é MUITO eficaz
    
    <br>
    
    **2. η (Eta) - Parâmetro de Escala** ⏱️
    
    - É o **tempo característico** de vida
    - Aos **η horas**, **63,2% dos componentes já falharam**
    - Também chamado de "vida característica"
    - Usado para calcular intervalos de PM
    
    <br>
    
    **Exemplo Prático:**
    
    Se um motor tem **β = 2.5** e **η = 8.000 horas**:
    
    - ✅ β > 1 significa que **falhas por desgaste dominam**
    - ⏰ Aos 8.000h, 63,2% dos motores terão falhado
    - 🛠️ **Manutenção preventiva é muito eficaz** neste caso
    - 📊 Recomendação: trocar entre 5.000-6.000 horas
    
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
    <h4>📊 Interpretando o Gráfico de Weibull</h4>
    
    **Probability Plot (Gráfico de Probabilidade):**
    - Se os pontos ficam em **linha reta** = Weibull é um bom modelo ✅
    - Se pontos estão **dispersos** = modelo não se ajusta bem ❌
    
    **Reliability Plot (Confiabilidade ao Longo do Tempo):**
    - Mostra a **probabilidade de sobrevivência** R(t)
    - Curva descendente = confiabilidade diminui com o tempo
    - Use para determinar quando fazer PM
    
    **Hazard Rate (Taxa de Falha):**
    - **Descendente** (β<1): falhas infantis
    - **Constante** (β≈1): falhas aleatórias
    - **Crescente** (β>1): falhas por desgaste
    
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # PASSO 4
    st.markdown("### 🛠️ PASSO 4: Planejar Manutenção Preventiva")
    
    st.markdown("""
    <div class="tutorial-card">
    
    <h4>🎯 3 Políticas de Manutenção</h4>
    
    <br>
    
    **Política 1: Meta de Confiabilidade** 🎯
    
    - **Como funciona:** Você define uma confiabilidade mínima (ex: 90%)
    - **Sistema calcula:** Em quantas horas a confiabilidade cai para 90%
    - **Exemplo:** Se confiabilidade chega a 90% em 5.500h → trocar aos 5.500h
    - **Quando usar:** Equipamentos críticos que não podem falhar
    
    <br>
    
    **Política 2: Fração de η** 📏
    
    - **Como funciona:** Troca aos X% do tempo característico η
    - **Regra comum:** 70% de η (conservador) ou 80% (moderado)
    - **Exemplo:** Se η = 8.000h e você escolhe 70% → trocar aos 5.600h
    - **Quando usar:** Abordagem pragmática e fácil de comunicar
    
    <br>
    
    **Política 3: Custo Ótimo** 💰
    
    - **Como funciona:** Minimiza o custo total (PM + falhas)
    - **Sistema calcula:** Ponto onde custo por hora é mínimo
    - **Considera:** Custo de PM, custo de falha, custo de parada
    - **Quando usar:** Quando custo é prioridade máxima
    
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="example-box">
    <h4>💡 Exemplo Completo de Decisão</h4>
    
    **Situação:** Motor elétrico com:
    - β = 2.8 (desgaste crescente)
    - η = 7.500 horas
    - Custo PM = R$ 1.000
    - Custo falha = R$ 8.000
    - Custo parada = R$ 500/hora
    
    **Resultados das 3 Políticas:**
    
    | Política | Intervalo PM | Confiabilidade | Custo/Hora | Recomendação |
    |----------|--------------|----------------|------------|--------------|
    | Meta 90% | 4.800h | 90% | R$ 0,28 | Muito conservador |
    | 70% de η | 5.250h | 86% | R$ 0,24 | Equilibrado ✅ |
    | Custo Ótimo | 5.100h | 88% | R$ 0,22 | Menor custo 🏆 |
    
    **Decisão Final:** Usar **Política 3 (Custo Ótimo)** - trocar aos **5.100 horas**
    
    **Resultado Esperado:**
    - ✅ Economia de R$ 0,06/hora vs atual
    - ✅ 88% de confiabilidade (aceitável)
    - ✅ ~23 PMs por ano (frota de 100 motores)
    
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # PASSO 5
    st.markdown("### 📦 PASSO 5: Dimensionar Estoque")
    
    st.markdown("""
    <div class="tutorial-card">
    
    <h4>📊 Conceitos de Gestão de Estoque</h4>
    
    <br>
    
    **EOQ - Economic Order Quantity (Lote Econômico)** 📦
    
    - Quantidade **ótima** a comprar em cada pedido
    - Equilibra custo de pedido vs custo de estocagem
    - **Fórmula:** EOQ = √(2 × Demanda Anual × Custo Pedido / Custo Estocagem)
    - **Exemplo:** Se EOQ = 15 → compre 15 peças por vez
    
    <br>
    
    **Safety Stock (Estoque de Segurança)** 🛡️
    
    - Quantidade **extra** para evitar falta de peça
    - Protege contra variações na demanda e atrasos de entrega
    - Baseado no **nível de serviço** desejado (ex: 95% = 5% de risco de falta)
    - **Exemplo:** Safety Stock = 5 peças
    
    <br>
    
    **Reorder Point (Ponto de Reposição)** 🔔
    
    - Quando o estoque chega neste nível → **fazer novo pedido**
    - Calcula considerando demanda durante lead time + safety stock
    - **Fórmula:** ROP = (Demanda Diária × Lead Time) + Safety Stock
    - **Exemplo:** Se ROP = 12 → quando estoque chegar a 12, pedir mais
    
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="example-box">
    <h4>💡 Exemplo Prático de Estoque</h4>
    
    **Situação:** Bomba hidráulica com:
    - Frota: 80 equipamentos
    - Intervalo PM: 6.000 horas
    - Utilização: 4.000 horas/ano por equipamento
    - Custo peça: R$ 2.000
    - Custo estocagem: 25%/ano
    - Custo pedido: R$ 150
    - Lead time: 30 dias
    - Nível de serviço desejado: 95%
    
    **Cálculos:**
    
    1. **Demanda Anual:** 80 equipamentos × (4.000h/ano ÷ 6.000h) = 53 peças/ano
    
    2. **EOQ:** √(2 × 53 × 150 / 500) = 5,6 ≈ **6 peças por pedido**
    
    3. **Safety Stock:** (considerando variabilidade) = **3 peças**
    
    4. **Reorder Point:** (53/365 × 30) + 3 = 4,4 + 3 = **7 peças**
    
    **Política Recomendada:**
    - 🏁 **Estoque inicial:** 6 + 3 = 9 peças
    - 🔔 **Fazer pedido quando:** estoque chegar a 7 peças
    - 📦 **Quantidade do pedido:** 6 peças
    - 📊 **Pedidos por ano:** ~9 vezes
    - 💰 **Custo total:** R$ 3.250/ano
    
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# TAB 3: TEMPLATES E DOWNLOADS
# ============================================================================
with tab3:
    st.markdown("## 📥 Templates de Planilhas para Download")
    
    st.markdown("""
    <div class="download-section">
    <h3 style="color: white;">📊 Baixe Templates Prontos para Uso</h3>
    <p style="color: white; opacity: 0.9;">
    Planilhas pré-formatadas com exemplos e instruções detalhadas
    </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Template 1: Básico
    st.markdown("### 📋 Template 1: Planilha Básica (Mínimo Necessário)")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        **Contém:**
        - ✅ 4 colunas obrigatórias
        - ✅ 100 linhas de exemplo
        - ✅ Instruções em cada coluna
        - ✅ Validação de dados automática
        
        **Ideal para:** Começar rapidamente com dados simples
        """)
    
    with col2:
        # Cria template básico
        template_basico = pd.DataFrame({
            'component_id': [f'EQUIP_{i:03d}' for i in range(1, 101)],
            'component_type': ['Motor Elétrico'] * 30 + ['Bomba Hidráulica'] * 30 + ['Válvula'] * 40,
            'failure_time': [5000 + i * 50 for i in range(100)],
            'censored': [0] * 70 + [1] * 30
        })
        
        # Adiciona linha de instruções
        instructions = pd.DataFrame({
            'component_id': ['Ex: MOTOR_001'],
            'component_type': ['Ex: Motor Elétrico'],
            'failure_time': ['Horas até falha'],
            'censored': ['0=falhou, 1=ativo']
        })
        
        template_final = pd.concat([instructions, template_basico], ignore_index=True)
        
        # Converte para Excel em memória
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            template_final.to_excel(writer, sheet_name='Dados', index=False)
            
            # Adiciona aba de instruções
            instrucoes = pd.DataFrame({
                'INSTRUÇÕES': [
                    '1. Preencha cada coluna conforme indicado',
                    '2. component_id: Identificador único do equipamento',
                    '3. component_type: Tipo ou modelo do componente',
                    '4. failure_time: Tempo até falha em HORAS',
                    '5. censored: 0 se falhou, 1 se ainda está funcionando',
                    '6. Apague a primeira linha de exemplo antes de enviar',
                    '7. Mínimo recomendado: 20-30 observações por tipo',
                    '8. Use unidade consistente (sempre horas)',
                ]
            })
            instrucoes.to_excel(writer, sheet_name='LEIA PRIMEIRO', index=False)
        
        output.seek(0)
        
        st.download_button(
            label="📥 Download Template Básico",
            data=output,
            file_name="template_weibull_basico.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    st.markdown("---")
    
    # Template 2: Completo
    st.markdown("### 📊 Template 2: Planilha Completa (Dados Avançados)")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        **Contém:**
        - ✅ 10 colunas (obrigatórias + opcionais)
        - ✅ 200 linhas de exemplo realistas
        - ✅ Múltiplos tipos de componentes
        - ✅ Dados de censura variados
        - ✅ Campos de localização e severidade
        
        **Ideal para:** Análise completa com dados detalhados
        """)
    
    with col2:
        # Cria template completo
        import numpy as np
        np.random.seed(42)
        
        n_samples = 200
        tipos = ['Motor Elétrico', 'Bomba Hidráulica', 'Válvula', 'Rolamento', 'Correia']
        locais = ['Planta A', 'Planta B', 'Planta C']
        
        template_completo = pd.DataFrame({
            'component_id': [f'{tipo[:3].upper()}_{i:03d}' for i, tipo in enumerate(np.random.choice(tipos, n_samples))],
            'component_type': np.random.choice(tipos, n_samples),
            'failure_time': np.random.weibull(2, n_samples) * 5000 + 1000,
            'censored': np.random.choice([0, 1], n_samples, p=[0.7, 0.3]),
            'installation_date': pd.date_range('2020-01-01', periods=n_samples, freq='D').strftime('%Y-%m-%d'),
            'failure_date': pd.date_range('2021-01-01', periods=n_samples, freq='2D').strftime('%Y-%m-%d'),
            'location': np.random.choice(locais, n_samples),
            'severity': np.random.randint(1, 6, n_samples),
            'operating_hours_per_day': np.random.choice([8, 12, 16, 24], n_samples),
            'maintenance_history': np.random.choice(['Sim', 'Não'], n_samples, p=[0.6, 0.4])
        })
        
        output2 = io.BytesIO()
        with pd.ExcelWriter(output2, engine='openpyxl') as writer:
            template_completo.to_excel(writer, sheet_name='Dados', index=False)
            
            # Aba de dicionário de dados
            dicionario = pd.DataFrame({
                'Coluna': [
                    'component_id',
                    'component_type',
                    'failure_time',
                    'censored',
                    'installation_date',
                    'failure_date',
                    'location',
                    'severity',
                    'operating_hours_per_day',
                    'maintenance_history'
                ],
                'Obrigatório': [
                    'SIM', 'SIM', 'SIM', 'SIM',
                    'NÃO', 'NÃO', 'NÃO', 'NÃO', 'NÃO', 'NÃO'
                ],
                'Descrição': [
                    'Identificador único do equipamento',
                    'Tipo ou modelo do componente',
                    'Tempo de operação até falha (em horas)',
                    '0 = equipamento falhou | 1 = ainda funcionando (censurado)',
                    'Data de instalação do equipamento (formato YYYY-MM-DD)',
                    'Data da falha (se aplicável)',
                    'Localização física do equipamento',
                    'Gravidade da falha (1=baixa, 5=crítica)',
                    'Horas de operação por dia',
                    'Se teve manutenção preventiva antes'
                ],
                'Exemplo': [
                    'MOTOR_001',
                    'Motor Elétrico',
                    '5420',
                    '0',
                    '2020-01-15',
                    '2021-08-20',
                    'Planta A',
                    '3',
                    '24',
                    'Sim'
                ]
            })
            dicionario.to_excel(writer, sheet_name='Dicionário de Dados', index=False)
        
        output2.seek(0)
        
        st.download_button(
            label="📥 Download Template Completo",
            data=output2,
            file_name="template_weibull_completo.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    st.markdown("---")
    
    # Template 3: Exemplo Real
    st.markdown("### 🏭 Template 3: Caso Real - Frota de Caminhões")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        **Contém:**
        - ✅ Dados realistas de frota de 50 caminhões
        - ✅ 5 tipos de componentes (Motor, Transmissão, etc.)
        - ✅ Histórico de 2 anos de operação
        - ✅ Análise já configurada e pronta
        
        **Ideal para:** Ver exemplo completo antes de usar seus dados
        """)
    
    with col2:
        # Cria exemplo de frota
        np.random.seed(123)
        
        componentes = ['Motor', 'Transmissão', 'Diferencial', 'Embreagem', 'Turbina']
        n_frota = 250
        
        exemplo_frota = pd.DataFrame({
            'component_id': [f'CAM{i//5:02d}_{comp[:3]}' for i in range(n_frota) for comp in [componentes[i % 5]]],
            'component_type': [componentes[i % 5] for i in range(n_frota)],
            'failure_time': np.concatenate([
                np.random.weibull(1.5, 50) * 8000 + 2000,  # Motor
                np.random.weibull(2.2, 50) * 12000 + 3000,  # Transmissão
                np.random.weibull(2.8, 50) * 15000 + 5000,  # Diferencial
                np.random.weibull(1.8, 50) * 6000 + 1000,   # Embreagem
                np.random.weibull(3.0, 50) * 20000 + 8000   # Turbina
            ]),
            'censored': np.random.choice([0, 1], n_frota, p=[0.65, 0.35]),
            'installation_date': np.tile(pd.date_range('2022-01-01', periods=50, freq='7D').strftime('%Y-%m-%d'), 5),
            'location': np.random.choice(['Filial SP', 'Filial RJ', 'Filial MG'], n_frota),
            'km_rodados': np.random.normal(150000, 50000, n_frota).astype(int)
        })
        
        output3 = io.BytesIO()
        with pd.ExcelWriter(output3, engine='openpyxl') as writer:
            exemplo_frota.to_excel(writer, sheet_name='Frota Caminhões', index=False)
            
            # Aba com análise prévia
            resumo = pd.DataFrame({
                'Componente': componentes,
                'Qtd Observações': [50] * 5,
                'Beta Esperado': [1.5, 2.2, 2.8, 1.8, 3.0],
                'Interpretação': [
                    'Desgaste leve',
                    'Desgaste moderado',
                    'Desgaste forte',
                    'Desgaste leve-moderado',
                    'Desgaste muito forte'
                ],
                'Recomendação': [
                    'PM aos 6.000h',
                    'PM aos 8.000h',
                    'PM aos 10.000h',
                    'PM aos 4.000h',
                    'PM aos 15.000h'
                ]
            })
            resumo.to_excel(writer, sheet_name='Análise Prévia', index=False)
        
        output3.seek(0)
        
        st.download_button(
            label="📥 Download Exemplo Frota",
            data=output3,
            file_name="exemplo_frota_caminhoes.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    st.markdown("---")
    
    # Guia de conversão de unidades
    st.markdown("### 🔄 Guia de Conversão de Unidades")
    
    st.markdown("""
    <div class="info-box">
    <h4>⏱️ Conversão de Tempo para Horas</h4>
    
    O sistema trabalha com **HORAS** como unidade padrão. Converta seus dados:
    
    | Sua Unidade | Multiplicar por | Exemplo | Resultado em Horas |
    |-------------|-----------------|---------|-------------------|
    | Dias | 24 | 150 dias | 3.600 horas |
    | Semanas | 168 | 52 semanas | 8.736 horas |
    | Meses | 730 | 18 meses | 13.140 horas |
    | Anos | 8.760 | 2 anos | 17.520 horas |
    | Quilômetros* | (1/velocidade média) | 100.000 km a 50 km/h | 2.000 horas |
    | Ciclos* | (horas por ciclo) | 5.000 ciclos × 2h | 10.000 horas |
    
    *Para equipamentos que trabalham por km ou ciclos
    
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# TAB 4: GLOSSÁRIO
# ============================================================================
with tab4:
    st.markdown("## 📖 Glossário de Termos Técnicos")
    
    glossary = {
        "Análise de Weibull": "Método estatístico para modelar tempo até falha e prever confiabilidade de equipamentos.",
        
        "β (Beta) - Parâmetro de Forma": "Define o tipo de falha: β<1 (infantil), β≈1 (aleatória), β>1 (desgaste).",
        
        "η (Eta) - Parâmetro de Escala": "Tempo característico onde 63,2% dos componentes falharam. Também chamado de 'vida característica'.",
        
        "Censura à Direita": "Dados de equipamentos que ainda não falharam até o momento da análise. Exemplo: motor com 5.000h ainda funcionando.",
        
        "Confiabilidade R(t)": "Probabilidade de um componente sobreviver até o tempo t sem falhar. Ex: R(5000h) = 0,90 significa 90% de chance de funcionar até 5.000 horas.",
        
        "Taxa de Falha h(t)": "Probabilidade instantânea de falha em um dado momento. Taxa crescente indica desgaste progressivo.",
        
        "MTTF": "Mean Time To Failure - Tempo médio até falha. É a média do tempo de vida de todos os componentes.",
        
        "Manutenção Preventiva (PM)": "Manutenção planejada realizada antes da falha para evitar paradas não programadas.",
        
        "Manutenção Corretiva (CM)": "Manutenção realizada após a falha do equipamento (também chamada de 'quebra').",
        
        "EOQ": "Economic Order Quantity - Quantidade econômica de pedido. Lote ótimo a comprar que minimiza custos totais de estoque.",
        
        "Safety Stock": "Estoque de segurança mantido para proteger contra variações de demanda e atrasos de entrega.",
        
        "Reorder Point (ROP)": "Nível de estoque que dispara um novo pedido de compra.",
        
        "Lead Time": "Tempo entre fazer um pedido e receber a peça (prazo de entrega).",
        
        "Nível de Serviço": "Probabilidade de ter peça disponível quando necessário. Ex: 95% = 5% de risco de falta.",
        
        "MLE": "Maximum Likelihood Estimation - Método estatístico usado para estimar os parâmetros β e η.",
        
        "Intervalo de Confiança": "Faixa onde os verdadeiros valores dos parâmetros provavelmente estão. Ex: β = 2,5 ± 0,3 com 95% de confiança.",
        
        "Downtime": "Tempo de parada do equipamento (sem produzir). Usado para calcular custos de falha.",
        
        "Frota": "Conjunto de equipamentos similares analisados em grupo.",
        
        "Curva da Banheira": "Padrão típico de falhas ao longo do tempo: alta no início (infantil), baixa no meio (vida útil), alta no fim (desgaste)."
    }
    
    for term, definition in glossary.items():
        st.markdown(f"""
        <div class="glossary-term">
        <strong style="color: #667eea; font-size: 1.1rem;">{term}</strong>
        <p style="margin-top: 0.5rem; color: #555;">{definition}</p>
        </div>
        """, unsafe_allow_html=True)

# ============================================================================
# TAB 5: FAQ
# ============================================================================
with tab5:
    st.markdown("## ❓ Perguntas Frequentes (FAQ)")
    
    faqs = [
        {
            "q": "❓ Quantos dados eu preciso para fazer uma análise confiável?",
            "a": """
            **Resposta:**
            - **Mínimo absoluto:** 15-20 observações por tipo de componente
            - **Recomendado:** 30-50 observações
            - **Ideal:** 50+ observações
            
            ⚠️ Com menos de 20 dados, os intervalos de confiança ficam muito amplos e as previsões menos confiáveis.
            
            💡 **Dica:** Se você tem poucos dados, agrupe componentes similares (ex: todos os motores de 100HP juntos).
            """
        },
        {
            "q": "❓ O que fazer se meus dados são em quilômetros, não horas?",
            "a": """
            **Resposta:**
            
            Você tem 2 opções:
            
            **Opção 1 (Recomendada):** Converter para horas
            - Calcule a velocidade média de operação
            - Divida km por velocidade média
            - Exemplo: 100.000 km ÷ 50 km/h = 2.000 horas
            
            **Opção 2:** Usar km diretamente
            - O sistema aceita qualquer unidade de tempo
            - Basta ser consistente (todos os valores em km)
            - Resultados serão em km (ex: PM aos 150.000 km)
            """
        },
        {
            "q": "❓ Como tratar equipamentos que nunca falharam?",
            "a": """
            **Resposta:**
            
            Use **censura à direita** (campo `censored = 1`):
            
            - `failure_time` = tempo de operação até hoje
            - `censored = 1` indica que ainda está funcionando
            
            **Exemplo:**
            - Motor com 8.000 horas e funcionando: `failure_time=8000, censored=1`
            
            ⚠️ **Importante:** Dados censurados são ESSENCIAIS para análise correta. Não os exclua!
            
            💡 **Regra:** É normal ter 20-40% de dados censurados em análises reais.
            """
        },
        {
            "q": "❓ Beta deu menor que 1. O que isso significa?",
            "a": """
            **Resposta:**
            
            **β < 1 indica falhas infantis:**
            
            - Taxa de falha DECRESCE com o tempo
            - Problemas de fabricação, instalação ou burn-in
            - Componentes que "sobrevivem" aos primeiros meses tendem a durar
            
            **Ações Recomendadas:**
            
            1. ✅ Melhorar controle de qualidade na compra
            2. ✅ Implementar período de burn-in (rodar em teste antes de instalar)
            3. ✅ Revisar processo de instalação
            4. ✅ Trocar fornecedor se problema persistir
            5. ❌ Manutenção preventiva NÃO é eficaz (falhas são aleatórias no início)
            
            💡 **Nota:** β < 1 não é "ruim" - apenas mostra que estratégia deve ser diferente.
            """
        },
        {
            "q": "❓ A manutenção preventiva sempre vale a pena?",
            "a": """
            **Resposta: DEPENDE do valor de β!**
            
            **β > 1,5:** PM é MUITO eficaz ✅
            - Falhas por desgaste dominam
            - PM previne maioria das falhas
            - ROI positivo
            
            **β ≈ 1:** PM tem eficácia LIMITADA ⚠️
            - Falhas são aleatórias
            - PM não previne falhas futuras
            - Foque em manter peças de reposição
            
            **β < 1:** PM pode ser PREJUDICIAL ❌
            - Falhas infantis dominam
            - Trocar componente "bom" aumenta risco
            - Foque em qualidade, não em PM
            
            💡 Use o sistema para calcular o **custo ótimo** e validar se PM vale a pena no seu caso!
            """
        },
        {
            "q": "❓ Como explicar Weibull para minha gerência?",
            "a": """
            **Resposta: Use linguagem simples e ROI**
            
            **Mensagem Principal:**
            
            "Weibull nos diz QUANDO trocar peças para minimizar custos e evitar paradas."
            
            **Pontos-Chave:**
            
            1. 📊 **Análise científica** (não "achismo")
            2. 💰 **Economia comprovada:** 20-40% em custos de manutenção
            3. ⏱️ **Menos paradas:** 30-50% redução em downtime não planejado
            4. 📦 **Estoque otimizado:** Saber exatamente quantas peças ter
            5. 📈 **ROI rápido:** Payback típico em 6-18 meses
            
            💡 **Dica:** Use a página de "Relatório IA" para gerar um executive summary automático!
            """
        },
        {
            "q": "❓ Meus dados têm muitos outliers. Devo removê-los?",
            "a": """
            **Resposta: CUIDADO! Nem sempre.**
            
            **Antes de remover, pergunte:**
            
            1. 🔍 **É um erro de digitação?** (ex: 500.000h em vez de 5.000h)
               - SIM → Corrija ou remova
            
            2. 🔍 **É uma falha catastrófica real?** (ex: acidente, operação inadequada)
               - Depende do objetivo da análise
               - Se quer prever falhas normais → remova
               - Se quer incluir todos os modos de falha → mantenha
            
            3. 🔍 **É uma falha prematura legítima?** (ex: defeito de fabricação)
               - MANTENHA! Faz parte da realidade
            
            💡 **Use a página "Qualidade dos Dados"** - o sistema detecta outliers e sugere ações.
            
            ⚠️ **Regra de Ouro:** Documente TUDO que foi removido e o porquê.
            """
        },
        {
            "q": "❓ Posso comparar resultados entre diferentes tipos de equipamentos?",
            "a": """
            **Resposta: Sim, mas com cuidado!**
            
            **O que PODE comparar:**
            
            ✅ **Parâmetro β** (tipo de falha)
            - Motor com β=2,5 vs Bomba com β=1,8
            - Identifica quais componentes têm mais desgaste
            
            ✅ **Confiabilidade em tempo específico**
            - R(5000h) do Motor vs R(5000h) da Bomba
            - Mostra qual é mais confiável no mesmo período
            
            **O que NÃO DEVE comparar diretamente:**
            
            ❌ **η (eta) absoluto** entre equipamentos DIFERENTES
            - η depende da aplicação e uso
            - Motor vs Bomba têm vidas características diferentes por natureza
            
            💡 **Use a página "Comparativos"** para análises seguras entre componentes!
            """
        },
        {
            "q": "❓ Sistema diz 'dados insuficientes'. E agora?",
            "a": """
            **Resposta: Você tem opções!**
            
            **Opção 1: Aguardar mais dados** (Ideal)
            - Continue coletando falhas
            - Volte quando tiver 20+ observações
            
            **Opção 2: Agrupar dados similares**
            - Junte modelos similares
            - Ex: "Motor 100HP" + "Motor 120HP" = "Motores Grandes"
            - Aumenta amostra rapidamente
            
            **Opção 3: Usar dados históricos**
            - Busque dados antigos em planilhas, sistemas legados
            - Dados de 5-10 anos atrás ainda são úteis
            
            **Opção 4: Usar dados do fabricante**
            - MTBF do manual do equipamento
            - Curvas de confiabilidade publicadas
            - Combine com seus poucos dados reais
            
            **Opção 5: Análise preliminar com ressalvas**
            - Sistema permite análise com poucos dados
            - Mas marca resultados como "baixa confiança"
            - Use apenas para estimativas iniciais
            """
        },
        {
            "q": "❓ Como integrar o sistema com meu SAP/CMMS?",
            "a": """
            **Resposta: Via exportação de dados**
            
            **Processo Recomendado:**
            
            1. **Extrair dados do SAP/CMMS:**
               - Relatório de ordens de serviço
               - Histórico de falhas
               - Registro de equipamentos
            
            2. **Formatar no Excel:**
               - Use os templates fornecidos
               - Faça correspondência de campos
               - Salve como CSV
            
            3. **Carregar no sistema:**
               - Página "Dados"
               - Upload do arquivo CSV
            
            4. **Exportar resultados:**
               - Sistema gera relatórios em Excel
               - Importe de volta no SAP (planejamento PM)
            
            🔮 **Futuro:** Integração API direta está planejada para versão 2.0
            
            💡 **Dica:** Configure exportação automática mensal do SAP → análise atualizada sempre!
            """
        }
    ]
    
    for i, faq in enumerate(faqs, 1):
        with st.expander(f"**{faq['q']}**"):
            st.markdown(faq['a'])

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p><strong>📚 Weibull Fleet Analytics - Central de Ajuda</strong></p>
    <p>💡 Tem dúvidas? Entre em contato ou consulte a documentação técnica</p>
    <p style='font-size: 0.9rem; color: #999;'>Desenvolvido com ❤️ para otimização de manutenção industrial</p>
</div>
""", unsafe_allow_html=True)
