"""
Página de planejamento de manutenção preventiva e gestão de estoque
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

from core.planner import MaintenancePlanner, SparePartsPlanner, create_maintenance_scenario_analysis
from ai.ai_assistant import WeibullAIAssistant
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="Planejamento PM & Estoque - Weibull Fleet Analytics",
    page_icon="🛠️",
    layout="wide"
)

st.markdown("# 🛠️ Planejamento PM & Estoque")
st.markdown("Otimização de intervalos de manutenção preventiva e gestão de peças de reposição")

def create_maintenance_strategy_card(strategy):
    """Criar card visual para estratégia de manutenção"""
    risk_colors = {
        "Baixo": "#10B981",
        "Médio": "#F59E0B", 
        "Alto": "#EF4444"
    }
    
    risk_color = risk_colors.get(strategy.risk_level, "#6B7280")
    
    return f"""
    <div style="background: linear-gradient(135deg, {risk_color}20 0%, {risk_color}10 100%); 
                padding: 1.5rem; border-radius: 10px; border-left: 4px solid {risk_color}; margin: 1rem 0;">
        <h3 style="color: {risk_color}; margin-top: 0;">🔧 {strategy.component}</h3>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem;">
            <div>
                <strong>Intervalo Recomendado:</strong><br>
                <span style="font-size: 1.2em; color: {risk_color};">{strategy.recommended_interval:.0f} horas</span>
            </div>
            <div>
                <strong>Confiabilidade:</strong><br>
                <span style="font-size: 1.2em;">{strategy.reliability_at_interval:.1%}</span>
            </div>
            <div>
                <strong>Nível de Risco:</strong><br>
                <span style="color: {risk_color}; font-weight: bold;">{strategy.risk_level}</span>
            </div>
            <div>
                <strong>Frequência Anual:</strong><br>
                <span style="font-size: 1.1em;">{8760/strategy.recommended_interval:.1f} PM/ano</span>
            </div>
        </div>
    </div>
    """

def create_spare_parts_card(recommendation):
    """Criar card para recomendação de estoque"""
    return f"""
    <div style="background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%); 
                padding: 1.5rem; border-radius: 10px; color: white; margin: 1rem 0;">
        <h3 style="margin-top: 0;">📦 {recommendation.component}</h3>
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; margin-top: 1rem;">
            <div>
                <strong>Demanda Anual:</strong><br>
                <span style="font-size: 1.2em;">{recommendation.annual_demand:.1f} peças</span>
            </div>
            <div>
                <strong>Ponto de Reposição:</strong><br>
                <span style="font-size: 1.2em;">{recommendation.reorder_point} peças</span>
            </div>
            <div>
                <strong>Lote Econômico:</strong><br>
                <span style="font-size: 1.2em;">{recommendation.economic_order_quantity} peças</span>
            </div>
            <div>
                <strong>Estoque de Segurança:</strong><br>
                <span style="font-size: 1.1em;">{recommendation.safety_stock} peças</span>
            </div>
            <div>
                <strong>Nível de Serviço:</strong><br>
                <span style="font-size: 1.1em;">{recommendation.service_level:.1%}</span>
            </div>
            <div>
                <strong>Custo Total:</strong><br>
                <span style="font-size: 1.1em;">R$ {recommendation.total_cost:,.0f}/ano</span>
            </div>
        </div>
    </div>
    """

def main():
    # Verificar se há resultados Weibull disponíveis
    if 'weibull_results' not in st.session_state or not st.session_state.weibull_results:
        st.warning("📈 Execute a análise Weibull primeiro na página 'Ajuste Weibull'")
        return
    
    # Sidebar com configurações
    with st.sidebar:
        st.markdown("## ⚙️ Configurações")
        
        # Selecionar análise
        available_analyses = list(st.session_state.weibull_results.keys())
        selected_analysis = st.selectbox(
            "Selecionar Análise",
            available_analyses,
            format_func=lambda x: x.replace('_', ' → ')
        )
        
        st.markdown("---")
        st.markdown("## 🎯 Políticas de Manutenção")
        
        maintenance_policy = st.selectbox(
            "Política",
            ["reliability_target", "fraction_of_eta", "cost_optimal"],
            format_func=lambda x: {
                "reliability_target": "Meta de Confiabilidade",
                "fraction_of_eta": "Fração da Vida Característica", 
                "cost_optimal": "Otimização por Custo"
            }[x]
        )
        
        if maintenance_policy == "reliability_target":
            target_reliability = st.slider("Confiabilidade Alvo", 0.5, 0.95, 0.8, 0.05)
        elif maintenance_policy == "fraction_of_eta":
            fraction_of_eta = st.slider("Fração de η", 0.3, 0.9, 0.75, 0.05)
        
        st.markdown("---")
        st.markdown("## 💰 Custos")
        
        cost_failure = st.number_input("Custo de Falha (R$)", 1000, 100000, 10000, 1000)
        cost_pm = st.number_input("Custo de PM (R$)", 100, 10000, 1000, 100)
        
        st.markdown("---")
        st.markdown("## 🏭 Parâmetros Operacionais")
        
        fleet_size = st.number_input("Tamanho da Frota", 1, 100, 10, 1)
        operational_hours_year = st.number_input("Horas/Ano por Equipamento", 1000, 8760, 6000, 100)
        
        st.markdown("---")
        st.markdown("## 📦 Estoque")
        
        lead_time_days = st.number_input("Lead Time (dias)", 1, 365, 30, 5)
        service_level = st.slider("Nível de Serviço", 0.8, 0.99, 0.95, 0.01)
        unit_cost = st.number_input("Custo Unitário (R$)", 100, 50000, 5000, 100)
        holding_cost_rate = st.slider("Taxa de Estoque (%/ano)", 0.1, 0.5, 0.2, 0.01)
    
    # Obter dados da análise selecionada
    analysis_data = st.session_state.weibull_results[selected_analysis]
    results = analysis_data['results']
    component = analysis_data['component']
    
    # Tabs principais
    tab1, tab2, tab3, tab4 = st.tabs(["🛠️ Manutenção Preventiva", "📦 Gestão de Estoque", "📊 Cenários", "🤖 IA Strategic"])
    
    with tab1:
        st.markdown("## 🛠️ Planejamento de Manutenção Preventiva")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.button("🎯 Calcular Estratégia Ótima", type="primary"):
                with st.spinner("Calculando estratégia de manutenção..."):
                    try:
                        # Criar planejador
                        planner = MaintenancePlanner(results['beta'], results['eta'], component)
                        
                        # Parâmetros baseados na política selecionada
                        if maintenance_policy == "reliability_target":
                            strategy = planner.optimal_pm_interval(
                                policy="reliability_target",
                                target_reliability=target_reliability,
                                cost_failure=cost_failure,
                                cost_pm=cost_pm
                            )
                        elif maintenance_policy == "fraction_of_eta":
                            strategy = planner.optimal_pm_interval(
                                policy="fraction_of_eta",
                                fraction_of_eta=fraction_of_eta,
                                cost_failure=cost_failure,
                                cost_pm=cost_pm
                            )
                        else:  # cost_optimal
                            strategy = planner.optimal_pm_interval(
                                policy="cost_optimal",
                                cost_failure=cost_failure,
                                cost_pm=cost_pm
                            )
                        
                        # Salvar no session state
                        st.session_state[f'maintenance_strategy_{selected_analysis}'] = strategy
                        
                        st.success("✅ Estratégia calculada com sucesso!")
                        
                    except Exception as e:
                        st.error(f"❌ Erro no cálculo: {str(e)}")
        
        with col2:
            st.markdown("""
            **Políticas Disponíveis:**
            - **Meta de Confiabilidade:** Intervalo para atingir confiabilidade específica
            - **Fração de η:** Percentual da vida característica
            - **Otimização por Custo:** Minimiza custo total esperado
            """)
        
        # Exibir estratégia se calculada
        strategy_key = f'maintenance_strategy_{selected_analysis}'
        if strategy_key in st.session_state:
            strategy = st.session_state[strategy_key]
            
            st.markdown("---")
            st.markdown(create_maintenance_strategy_card(strategy), unsafe_allow_html=True)
            
            # Métricas detalhadas
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                annual_pm_freq = 8760 / strategy.recommended_interval
                st.metric("PM por Ano", f"{annual_pm_freq:.1f}")
            
            with col2:
                if strategy.total_cost_rate:
                    annual_cost = strategy.total_cost_rate * 8760
                    st.metric("Custo Anual", f"R$ {annual_cost:,.0f}")
                else:
                    st.metric("Custo Anual", "N/A")
            
            with col3:
                pm_cost_year = annual_pm_freq * cost_pm
                st.metric("Custo PM/Ano", f"R$ {pm_cost_year:,.0f}")
            
            with col4:
                downtime_year = annual_pm_freq * 4  # Assumir 4h por PM
                st.metric("Parada/Ano", f"{downtime_year:.0f}h")
            
            # Gráfico de confiabilidade vs tempo
            st.markdown("### 📈 Confiabilidade ao Longo do Tempo")
            
            times = np.linspace(0, strategy.recommended_interval * 2, 100)
            planner = MaintenancePlanner(results['beta'], results['eta'])
            reliability_curve = planner.reliability_over_time(times)
            
            fig_reliability = go.Figure()
            
            fig_reliability.add_trace(go.Scatter(
                x=times,
                y=reliability_curve,
                mode='lines',
                name='Confiabilidade',
                line=dict(color='blue', width=2)
            ))
            
            # Linha do intervalo recomendado
            fig_reliability.add_vline(
                x=strategy.recommended_interval,
                line_dash="dash",
                line_color="red",
                annotation_text=f"PM: {strategy.recommended_interval:.0f}h"
            )
            
            # Linha da confiabilidade no intervalo
            fig_reliability.add_hline(
                y=strategy.reliability_at_interval,
                line_dash="dot",
                line_color="green",
                annotation_text=f"R = {strategy.reliability_at_interval:.1%}"
            )
            
            fig_reliability.update_layout(
                title=f'Confiabilidade - {component}',
                xaxis_title='Tempo (horas)',
                yaxis_title='Confiabilidade',
                template='plotly_white',
                height=400
            )
            
            st.plotly_chart(fig_reliability, use_container_width=True)
    
    with tab2:
        st.markdown("## 📦 Gestão de Estoque de Peças")
        
        if st.button("📊 Calcular Política de Estoque", type="primary"):
            with st.spinner("Calculando política de estoque..."):
                try:
                    # Calcular demanda
                    spare_planner = SparePartsPlanner()
                    
                    demand_info = spare_planner.calculate_demand(
                        mtbf=results['mtbf'],
                        fleet_size=fleet_size,
                        operational_hours_per_year=operational_hours_year
                    )
                    
                    # Otimizar estoque
                    inventory_recommendation = spare_planner.optimize_inventory(
                        annual_demand=demand_info['annual_demand_mean'],
                        lead_time_days=lead_time_days,
                        service_level=service_level,
                        holding_cost_rate=holding_cost_rate,
                        unit_cost=unit_cost
                    )
                    
                    inventory_recommendation.component = component
                    
                    # Salvar resultados
                    st.session_state[f'inventory_strategy_{selected_analysis}'] = {
                        'demand_info': demand_info,
                        'recommendation': inventory_recommendation
                    }
                    
                    st.success("✅ Política de estoque calculada!")
                    
                except Exception as e:
                    st.error(f"❌ Erro no cálculo: {str(e)}")
        
        # Exibir resultados de estoque
        inventory_key = f'inventory_strategy_{selected_analysis}'
        if inventory_key in st.session_state:
            inventory_data = st.session_state[inventory_key]
            demand_info = inventory_data['demand_info']
            recommendation = inventory_data['recommendation']
            
            st.markdown("---")
            st.markdown(create_spare_parts_card(recommendation), unsafe_allow_html=True)
            
            # Informações de demanda
            st.markdown("### 📊 Análise de Demanda")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Demanda Anual Média",
                    f"{demand_info['annual_demand_mean']:.1f} peças",
                    delta=f"±{demand_info['annual_demand_std']:.1f}"
                )
            
            with col2:
                st.metric(
                    "Demanda Mensal",
                    f"{demand_info['monthly_demand_mean']:.1f} peças",
                    delta=f"±{demand_info['monthly_demand_std']:.1f}"
                )
            
            with col3:
                st.metric(
                    "Taxa de Falha",
                    f"{demand_info['failure_rate']:.2e} falhas/h",
                    delta=f"MTBF: {results['mtbf']:.0f}h"
                )
            
            # Simulação de performance
            st.markdown("### 🎲 Simulação de Performance")
            
            if st.button("🎲 Executar Simulação"):
                with st.spinner("Simulando..."):
                    simulation_results = spare_planner.simulate_inventory_performance(
                        eoq=recommendation.economic_order_quantity,
                        reorder_point=recommendation.reorder_point,
                        annual_demand=demand_info['annual_demand_mean'],
                        lead_time_days=lead_time_days,
                        num_simulations=1000
                    )
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        actual_service = simulation_results['simulated_service_level']
                        target_service = service_level
                        delta_service = actual_service - target_service
                        
                        st.metric(
                            "Nível de Serviço Real",
                            f"{actual_service:.1%}",
                            delta=f"{delta_service:+.1%}"
                        )
                    
                    with col2:
                        st.metric(
                            "Estoque Médio",
                            f"{simulation_results['average_inventory']:.1f} peças"
                        )
                    
                    with col3:
                        st.metric(
                            "Prob. Falta de Estoque",
                            f"{simulation_results['stockout_probability']:.1%}"
                        )
            
            # Gráfico de custo vs nível de serviço
            st.markdown("### 💰 Análise de Custo vs Nível de Serviço")
            
            service_levels = np.arange(0.8, 0.995, 0.01)
            costs = []
            
            for sl in service_levels:
                temp_rec = spare_planner.optimize_inventory(
                    annual_demand=demand_info['annual_demand_mean'],
                    lead_time_days=lead_time_days,
                    service_level=sl,
                    holding_cost_rate=holding_cost_rate,
                    unit_cost=unit_cost
                )
                costs.append(temp_rec.total_cost)
            
            fig_cost_service = go.Figure()
            
            fig_cost_service.add_trace(go.Scatter(
                x=service_levels * 100,
                y=costs,
                mode='lines',
                name='Custo Total',
                line=dict(color='blue', width=2)
            ))
            
            # Marcar ponto atual
            current_idx = np.argmin(np.abs(service_levels - service_level))
            fig_cost_service.add_trace(go.Scatter(
                x=[service_level * 100],
                y=[costs[current_idx]],
                mode='markers',
                name='Configuração Atual',
                marker=dict(color='red', size=10)
            ))
            
            fig_cost_service.update_layout(
                title='Custo Total vs Nível de Serviço',
                xaxis_title='Nível de Serviço (%)',
                yaxis_title='Custo Total Anual (R$)',
                template='plotly_white',
                height=400
            )
            
            st.plotly_chart(fig_cost_service, use_container_width=True)
    
    with tab3:
        st.markdown("## 📊 Análise de Cenários")
        
        if st.button("🔄 Gerar Cenários", type="primary"):
            with st.spinner("Gerando análise de cenários..."):
                # Definir intervalos para análise
                eta = results['eta']
                intervals = np.array([
                    eta * 0.5,   # Muito conservador
                    eta * 0.6,   # Conservador
                    eta * 0.7,   # Balanceado
                    eta * 0.8,   # Agressivo
                    eta * 0.9,   # Muito agressivo
                    eta * 1.0    # Vida característica
                ])
                
                scenarios_df = create_maintenance_scenario_analysis(
                    beta=results['beta'],
                    eta=results['eta'],
                    intervals=intervals,
                    cost_failure=cost_failure,
                    cost_pm=cost_pm
                )
                
                st.session_state[f'scenarios_{selected_analysis}'] = scenarios_df
        
        # Exibir cenários
        scenarios_key = f'scenarios_{selected_analysis}'
        if scenarios_key in st.session_state:
            scenarios_df = st.session_state[scenarios_key]
            
            st.markdown("### 📋 Tabela de Cenários")
            st.dataframe(scenarios_df, use_container_width=True)
            
            # Gráficos de cenários
            col1, col2 = st.columns(2)
            
            with col1:
                fig_cost = px.line(
                    scenarios_df,
                    x='Intervalo (h)',
                    y='Taxa de Custo ($/h)',
                    title='Taxa de Custo vs Intervalo de Manutenção',
                    markers=True
                )
                fig_cost.update_layout(template='plotly_white')
                st.plotly_chart(fig_cost, use_container_width=True)
            
            with col2:
                fig_reliability = px.scatter(
                    scenarios_df,
                    x='Intervalo (h)',
                    y='Confiabilidade',
                    color='Nível de Risco',
                    size='PM por ano',
                    title='Confiabilidade vs Intervalo',
                    color_discrete_map={
                        'Baixo': 'green',
                        'Médio': 'orange', 
                        'Alto': 'red'
                    }
                )
                fig_reliability.update_layout(template='plotly_white')
                st.plotly_chart(fig_reliability, use_container_width=True)
            
            # Recomendação de cenário
            optimal_idx = scenarios_df['Taxa de Custo ($/h)'].idxmin()
            optimal_scenario = scenarios_df.iloc[optimal_idx]
            
            st.markdown(f"""
            ### 🎯 Cenário Recomendado (Menor Custo)
            
            **Intervalo:** {optimal_scenario['Intervalo (h)']:.0f} horas  
            **Confiabilidade:** {optimal_scenario['Confiabilidade']:.1%}  
            **Nível de Risco:** {optimal_scenario['Nível de Risco']}  
            **Taxa de Custo:** R$ {optimal_scenario['Taxa de Custo ($/h)']:.2f}/hora  
            **PM por Ano:** {optimal_scenario['PM por ano']:.1f}
            """)
    
    with tab4:
        st.markdown("## 🤖 Análise Estratégica com IA")
        
        # Verificar se há estratégias calculadas
        strategy_key = f'maintenance_strategy_{selected_analysis}'
        inventory_key = f'inventory_strategy_{selected_analysis}'
        
        if strategy_key in st.session_state or inventory_key in st.session_state:
            if st.button("🧠 Gerar Análise Estratégica IA", type="primary"):
                with st.spinner("IA analisando estratégias..."):
                    try:
                        ai_assistant = WeibullAIAssistant()
                        
                        # Preparar contexto
                        analysis_context = {
                            'component': component,
                            'weibull_params': results,
                            'fleet_size': fleet_size,
                            'operational_hours': operational_hours_year
                        }
                        
                        if strategy_key in st.session_state:
                            strategy = st.session_state[strategy_key]
                            analysis_context['maintenance_strategy'] = {
                                'interval': strategy.recommended_interval,
                                'reliability': strategy.reliability_at_interval,
                                'risk_level': strategy.risk_level
                            }
                        
                        if inventory_key in st.session_state:
                            inventory_data = st.session_state[inventory_key]
                            analysis_context['inventory_strategy'] = {
                                'annual_demand': inventory_data['demand_info']['annual_demand_mean'],
                                'reorder_point': inventory_data['recommendation'].reorder_point,
                                'service_level': inventory_data['recommendation'].service_level
                            }
                        
                        # Gerar sugestão estratégica
                        strategic_analysis = ai_assistant.suggest_maintenance_strategy(
                            weibull_params=results,
                            operational_context=analysis_context
                        )
                        
                        if strategic_analysis.success:
                            st.markdown("### 🤖 Análise Estratégica da IA")
                            st.markdown(strategic_analysis.content)
                            
                            if strategic_analysis.suggestions:
                                st.markdown("### 💡 Recomendações Estratégicas")
                                for suggestion in strategic_analysis.suggestions:
                                    st.info(f"💡 {suggestion}")
                        else:
                            st.error(f"❌ Erro na análise: {strategic_analysis.content}")
                    
                    except Exception as e:
                        st.error(f"❌ Erro ao chamar IA: {str(e)}")
        else:
            st.info("🛠️ Calculate maintenance ou inventory strategies primeiro")
    
    # Footer com opções de export
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Exportar Plano de Manutenção"):
            if strategy_key in st.session_state:
                strategy = st.session_state[strategy_key]
                
                plan_df = pd.DataFrame([{
                    'Componente': strategy.component,
                    'Intervalo_PM_horas': strategy.recommended_interval,
                    'Confiabilidade': strategy.reliability_at_interval,
                    'Risco': strategy.risk_level,
                    'PM_por_ano': 8760 / strategy.recommended_interval,
                    'Custo_PM_anual': (8760 / strategy.recommended_interval) * cost_pm
                }])
                
                csv = plan_df.to_csv(index=False).encode('utf-8')
                
                st.download_button(
                    label="📥 Download Plano PM",
                    data=csv,
                    file_name=f'plano_manutencao_{component.replace(" ", "_")}.csv',
                    mime='text/csv'
                )
    
    with col2:
        if st.button("📦 Exportar Plano de Estoque"):
            if inventory_key in st.session_state:
                inventory_data = st.session_state[inventory_key]
                recommendation = inventory_data['recommendation']
                
                inventory_df = pd.DataFrame([{
                    'Componente': component,
                    'Demanda_anual': recommendation.annual_demand,
                    'Ponto_reposicao': recommendation.reorder_point,
                    'Lote_economico': recommendation.economic_order_quantity,
                    'Estoque_seguranca': recommendation.safety_stock,
                    'Nivel_servico': recommendation.service_level,
                    'Custo_total_anual': recommendation.total_cost
                }])
                
                csv = inventory_df.to_csv(index=False).encode('utf-8')
                
                st.download_button(
                    label="📥 Download Plano Estoque",
                    data=csv,
                    file_name=f'plano_estoque_{component.replace(" ", "_")}.csv',
                    mime='text/csv'
                )
    
    with col3:
        if st.button("➡️ Relatório IA"):
            st.info("Navigate to '🧠 Relatório IA' para análise completa")

if __name__ == "__main__":
    main()
