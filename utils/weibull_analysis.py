import streamlit as st
import pandas as pd
import numpy as np
from lifelines import WeibullFitter
from typing import Dict, Any, Tuple
import warnings
warnings.filterwarnings('ignore')

def validate_dataset_for_weibull(df: pd.DataFrame) -> Tuple[bool, list, pd.DataFrame]:
    """
    Valida e limpa dataset para análise Weibull.
    
    Returns:
        Tuple (is_valid, issues_list, cleaned_dataframe)
    """
    issues = []
    
    if df is None or df.empty:
        return False, ["Dataset vazio"], pd.DataFrame()
    
    # Verifica colunas obrigatórias
    required_cols = ['component_type', 'failure_time', 'censored']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        return False, [f"Colunas ausentes: {missing_cols}"], pd.DataFrame()
    
    # Cria cópia para limpeza
    df_clean = df.copy()
    initial_count = len(df_clean)
    
    # Remove registros com valores nulos em colunas críticas
    df_clean = df_clean.dropna(subset=required_cols)
    null_removed = initial_count - len(df_clean)
    if null_removed > 0:
        issues.append(f"Removidos {null_removed} registros com valores nulos")
    
    # Converte failure_time para numérico
    df_clean['failure_time'] = pd.to_numeric(df_clean['failure_time'], errors='coerce')
    df_clean = df_clean.dropna(subset=['failure_time'])
    
    # Remove tempos inválidos (≤ 0)
    invalid_mask = df_clean['failure_time'] <= 0
    if invalid_mask.any():
        invalid_count = invalid_mask.sum()
        df_clean = df_clean[~invalid_mask]
        issues.append(f"Removidos {invalid_count} registros com failure_time ≤ 0")
    
    # Padroniza coluna censored para boolean
    df_clean['censored'] = df_clean['censored'].astype(bool)
    
    # Verifica dados suficientes por componente
    component_counts = df_clean['component_type'].value_counts()
    insufficient = component_counts[component_counts < 3]
    if len(insufficient) > 0:
        insufficient_list = insufficient.index.tolist()
        issues.append(f"Componentes com < 3 observações removidos: {insufficient_list}")
        df_clean = df_clean[~df_clean['component_type'].isin(insufficient_list)]
    
    is_valid = len(df_clean) > 0 and len(df_clean['component_type'].unique()) > 0
    
    return is_valid, issues, df_clean

def fit_weibull_single_component(df_component: pd.DataFrame, component_name: str) -> Dict[str, Any]:
    """
    Executa ajuste Weibull para um único componente.
    
    Returns:
        Dict com parâmetros Weibull ou informações de erro
    """
    try:
        if len(df_component) < 3:
            return {
                "error": f"Dados insuficientes: {len(df_component)} observações (mínimo: 3)",
                "success": False
            }
        
        # Prepara dados
        durations = df_component['failure_time'].values
        event_observed = df_component['censored'].values.astype(bool)
        
        # Verifica se há eventos observados
        if not event_observed.any():
            return {
                "error": "Nenhum evento observado (todos censurados)",
                "success": False
            }
        
        # Ajuste Weibull
        wf = WeibullFitter()
        wf.fit(durations=durations, event_observed=event_observed)
        
        # Extrai parâmetros
        lambda_param = float(wf.lambda_)  # Parâmetro de escala
        rho_param = float(wf.rho_)        # Parâmetro de forma
        
        # Calcula MTBF
        try:
            mtbf = lambda_param * np.math.gamma(1 + 1/rho_param)
        except:
            mtbf = None
        
        # Monta resultado
        result = {
            'lambda': lambda_param,
            'rho': rho_param,
            'eta': lambda_param,     # Alias para compatibilidade
            'beta': rho_param,       # Alias para compatibilidade
            'MTBF': mtbf,
            'AIC': float(wf.AIC_) if hasattr(wf, 'AIC_') else None,
            'BIC': float(wf.BIC_) if hasattr(wf, 'BIC_') else None,
            'n_observations': len(df_component),
            'n_events': int(event_observed.sum()),
            'n_censored': int((~event_observed).sum()),
            'success': True,
            'component_name': component_name
        }
        
        return result
        
    except Exception as e:
        return {
            'error': f"Erro no ajuste: {str(e)}",
            'success': False,
            'component_name': component_name
        }

@st.cache_data
def execute_weibull_analysis(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """
    Executa análise Weibull completa para todos os componentes.
    
    Returns:
        Dict com resultados por componente
    """
    # Validação e limpeza
    is_valid, issues, df_clean = validate_dataset_for_weibull(df)
    
    if not is_valid:
        st.error("❌ **Dados inválidos para análise Weibull:**")
        for issue in issues:
            st.error(f"  • {issue}")
        return {}
    
    # Exibe avisos se houver limpeza
    if issues:
        st.warning("⚠️ **Ajustes realizados nos dados:**")
        for issue in issues:
            st.warning(f"  • {issue}")
    
    results = {}
    components = df_clean['component_type'].unique()
    
    # Barra de progresso
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_components = len(components)
    successful_fits = 0
    
    for i, component_type in enumerate(components):
        status_text.text(f"Analisando {component_type}... ({i+1}/{total_components})")
        
        # Filtra dados do componente
        df_component = df_clean[df_clean['component_type'] == component_type].copy()
        
        # Executa ajuste
        result = fit_weibull_single_component(df_component, component_type)
        results[component_type] = result
        
        if result.get('success', False):
            successful_fits += 1
        
        # Atualiza progresso
        progress_bar.progress((i + 1) / total_components)
    
    # Limpa elementos temporários
    progress_bar.empty()
    status_text.empty()
    
    # Relatório final
    failed_fits = total_components - successful_fits
    
    if successful_fits > 0:
        st.success(f"✅ **Análise concluída:** {successful_fits} componentes ajustados")
        
        if failed_fits > 0:
            st.warning(f"⚠️ **{failed_fits} componentes falharam no ajuste**")
            
            failed_components = [
                name for name, result in results.items() 
                if not result.get('success', False)
            ]
            
            with st.expander("🔍 **Ver componentes com falha**"):
                for comp in failed_components:
                    error_msg = results[comp].get('error', 'Erro desconhecido')
                    st.error(f"**{comp}:** {error_msg}")
    else:
        st.error("❌ **Nenhum componente foi ajustado com sucesso**")
    
    return results

def generate_data_quality_report(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Gera relatório detalhado de qualidade dos dados.
    """
    if df is None or df.empty:
        return {
            "status": "empty",
            "issues": ["Dataset vazio ou não carregado"],
            "recommendations": ["Carregue dados válidos na página 'Dados UNIFIED'"],
            "statistics": {}
        }
    
    issues = []
    recommendations = []
    stats = {
        'total_records': len(df),
        'total_columns': len(df.columns)
    }
    
    # Verifica colunas obrigatórias
    required_cols = ['component_type', 'failure_time', 'censored']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        issues.append(f"Colunas obrigatórias ausentes: {missing_cols}")
        recommendations.append("Certifique-se que o dataset contém: component_type, failure_time, censored")
        return {
            "status": "critical",
            "issues": issues,
            "recommendations": recommendations,
            "statistics": stats
        }
    
    # Análise de component_type
    if 'component_type' in df.columns:
        stats['unique_components'] = df['component_type'].nunique()
        component_counts = df['component_type'].value_counts()
        insufficient = component_counts[component_counts < 3]
        
        if len(insufficient) > 0:
            issues.append(f"{len(insufficient)} componentes com menos de 3 observações")
            recommendations.append("Cada componente precisa de pelo menos 3 observações para análise Weibull")
    
    # Análise de failure_time
    if 'failure_time' in df.columns:
        null_count = df['failure_time'].isnull().sum()
        if null_count > 0:
            issues.append(f"{null_count} valores nulos em failure_time")
            recommendations.append("Remova ou trate valores nulos em failure_time")
        
        # Converte para numérico para análise
        numeric_times = pd.to_numeric(df['failure_time'], errors='coerce')
        non_numeric = numeric_times.isnull().sum() - null_count
        
        if non_numeric > 0:
            issues.append(f"{non_numeric} valores não-numéricos em failure_time")
            recommendations.append("failure_time deve conter apenas valores numéricos")
        
        # Valores <= 0
        if numeric_times.notna().any():
            invalid_times = (numeric_times <= 0).sum()
            if invalid_times > 0:
                issues.append(f"{invalid_times} valores ≤ 0 em failure_time")
                recommendations.append("Tempos de falha devem ser maiores que zero")
            
            stats.update({
                'failure_time_min': float(numeric_times.min()) if numeric_times.notna().any() else None,
                'failure_time_max': float(numeric_times.max()) if numeric_times.notna().any() else None,
                'failure_time_mean': float(numeric_times.mean()) if numeric_times.notna().any() else None
            })
    
    # Análise de censored
    if 'censored' in df.columns:
        valid_values = df['censored'].isin([0, 1, True, False])
        invalid_censored = (~valid_values).sum()
        
        if invalid_censored > 0:
            issues.append(f"{invalid_censored} valores inválidos em censored")
            recommendations.append("censored deve conter apenas 0, 1, True ou False")
        
        if valid_values.any():
            stats['censored_rate'] = float(df[valid_values]['censored'].mean())
            stats['total_events'] = int(df[valid_values]['censored'].sum())
    
    # Determina status geral
    if not issues:
        status = "excellent"
    elif len(issues) <= 2:
        status = "good"
    elif len(issues) <= 4:
        status = "fair"
    else:
        status = "poor"
    
    return {
        "status": status,
        "issues": issues,
        "recommendations": recommendations,
        "statistics": stats
    }

def display_weibull_results(results: Dict[str, Dict[str, Any]]):
    """Exibe resultados da análise Weibull de forma organizada."""
    if not results:
        st.info("Execute a análise Weibull para ver os resultados")
        return
    
    # Filtra apenas resultados bem-sucedidos
    successful_results = {
        name: result for name, result in results.items() 
        if result.get('success', False)
    }
    
    if not successful_results:
        st.error("Nenhum resultado Weibull bem-sucedido para exibir")
        return
    
    st.subheader("📊 **Resultados da Análise Weibull**")
    
    # Tabela resumo
    summary_data = []
    for component, result in successful_results.items():
        summary_data.append({
            'Componente': component,
            'λ (Escala)': f"{result['lambda']:.4f}",
            'ρ (Forma)': f"{result['rho']:.4f}",
            'MTBF': f"{result.get('MTBF', 0):.2f}" if result.get('MTBF') else "N/A",
            'Observações': result['n_observations'],
            'Eventos': result['n_events'],
            'AIC': f"{result.get('AIC', 0):.2f}" if result.get('AIC') else "N/A"
        })
    
    df_summary = pd.DataFrame(summary_data)
    st.dataframe(df_summary, use_container_width=True)
    
    # Seletor para detalhes
    with st.expander("🔍 **Detalhes por Componente**"):
        selected_comp = st.selectbox(
            "Selecione um componente:",
            options=list(successful_results.keys()),
            key="weibull_detail_selector"
        )
        
        if selected_comp:
            result = successful_results[selected_comp]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Parâmetro λ", f"{result['lambda']:.4f}")
                st.metric("Parâmetro ρ", f"{result['rho']:.4f}")
            
            with col2:
                st.metric("MTBF", f"{result.get('MTBF', 0):.2f}" if result.get('MTBF') else "N/A")
                st.metric("Observações", result['n_observations'])
            
            with col3:
                st.metric("Eventos", result['n_events'])
                st.metric("Censurados", result['n_censored'])
