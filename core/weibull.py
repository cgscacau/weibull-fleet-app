"""
Módulo principal para análise de distribuição Weibull
Implementa ajuste por MLE, gráficos de probabilidade e funções de confiabilidade
"""
import numpy as np
import pandas as pd
from scipy import stats, optimize
from scipy.special import gamma
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Tuple, Optional, List
import warnings


class WeibullAnalysis:
    """Classe principal para análise Weibull"""
    
    def __init__(self):
        self.beta = None
        self.eta = None
        self.fitted = False
        
    def fit_mle(self, times: np.ndarray, censored: Optional[np.ndarray] = None) -> Dict:
        """
        Ajuste Weibull por Maximum Likelihood Estimation
        
        Args:
            times: Tempos de falha/censura
            censored: Array booleano indicando censura (True = censurado)
        
        Returns:
            Dict com parâmetros ajustados e estatísticas
        """
        times = np.asarray(times)
        if censored is None:
            censored = np.zeros(len(times), dtype=bool)
        else:
            censored = np.asarray(censored, dtype=bool)
        
        # Validações
        if len(times) != len(censored):
            raise ValueError("times e censored devem ter mesmo tamanho")
        
        if np.any(times <= 0):
            raise ValueError("Todos os tempos devem ser positivos")
        
        # Separar falhas observadas e censuradas
        failure_times = times[~censored]
        censored_times = times[censored]
        
        if len(failure_times) < 2:
            raise ValueError("Necessário pelo menos 2 falhas observadas")
        
        # Log-likelihood function para Weibull com censura
        def neg_log_likelihood(params):
            beta, eta = params
            if beta <= 0 or eta <= 0:
                return np.inf
            
            # Contribuição das falhas observadas
            ll_failures = 0
            if len(failure_times) > 0:
                ll_failures = np.sum(np.log(beta/eta) + (beta-1)*np.log(failure_times/eta) - 
                                   (failure_times/eta)**beta)
            
            # Contribuição dos itens censurados (função de sobrevivência)
            ll_censored = 0
            if len(censored_times) > 0:
                ll_censored = -np.sum((censored_times/eta)**beta)
            
            return -(ll_failures + ll_censored)
        
        # Estimativas iniciais usando método dos momentos
        if len(failure_times) >= 2:
            # Usar apenas falhas para estimativa inicial
            log_times = np.log(failure_times)
            mean_log = np.mean(log_times)
            var_log = np.var(log_times)
            
            # Aproximação inicial para beta
            beta_init = 1.2 / np.sqrt(var_log) if var_log > 0 else 1.0
            eta_init = np.exp(mean_log + 0.5772/beta_init)  # 0.5772 ≈ constante de Euler
        else:
            beta_init = 1.0
            eta_init = np.mean(times)
        
        # Otimização
        try:
            result = optimize.minimize(
                neg_log_likelihood,
                x0=[beta_init, eta_init],
                method='L-BFGS-B',
                bounds=[(0.1, 10), (np.min(times)*0.1, np.max(times)*10)]
            )
            
            if not result.success:
                # Tentar com Nelder-Mead
                result = optimize.minimize(
                    neg_log_likelihood,
                    x0=[beta_init, eta_init],
                    method='Nelder-Mead'
                )
        except:
            # Fallback para método mais robusto
            result = optimize.minimize(
                neg_log_likelihood,
                x0=[1.0, np.median(times)],
                method='Powell'
            )
        
        self.beta, self.eta = result.x
        self.fitted = True
        
        # Calcular intervalos de confiança (aproximação usando Hessiana)
        ci_results = self._calculate_confidence_intervals(times, censored, result.x)
        
        # Estatísticas do modelo
        n_failures = len(failure_times)
        n_total = len(times)
        censoring_rate = len(censored_times) / n_total
        
        # Critérios de informação
        log_likelihood = -result.fun
        aic = 2 * 2 - 2 * log_likelihood  # 2 parâmetros
        bic = np.log(n_failures) * 2 - 2 * log_likelihood
        
        return {
            'beta': self.beta,
            'eta': self.eta,
            'beta_ci_lower': ci_results['beta_ci'][0],
            'beta_ci_upper': ci_results['beta_ci'][1],
            'eta_ci_lower': ci_results['eta_ci'][0],
            'eta_ci_upper': ci_results['eta_ci'][1],
            'log_likelihood': log_likelihood,
            'aic': aic,
            'bic': bic,
            'sample_size': n_total,
            'n_failures': n_failures,
            'censoring_rate': censoring_rate,
            'convergence': result.success,
            'mtbf': self.mtbf,
            'reliability_at_mtbf': np.exp(-1)
        }
    
    def _calculate_confidence_intervals(self, times, censored, params, alpha=0.05):
        """Calcular intervalos de confiança usando aproximação delta method"""
        beta, eta = params
        
        # Aproximação simples usando desvio padrão assintótico  
        n_failures = np.sum(~censored)
        
        # Desvio padrão aproximado para beta e eta
        beta_se = beta / np.sqrt(n_failures)  # Aproximação
        eta_se = eta / np.sqrt(n_failures)    # Aproximação
        
        # Intervalo de confiança (assumindo normalidade assintótica)
        z_alpha = stats.norm.ppf(1 - alpha/2)
        
        beta_ci = [
            max(0.01, beta - z_alpha * beta_se),
            beta + z_alpha * beta_se
        ]
        
        eta_ci = [
            max(times.min() * 0.01, eta - z_alpha * eta_se),
            eta + z_alpha * eta_se
        ]
        
        return {
            'beta_ci': beta_ci,
            'eta_ci': eta_ci
        }
    
    @property
    def mtbf(self) -> float:
        """Tempo médio até falha"""
        if not self.fitted:
            return None
        return self.eta * gamma(1 + 1/self.beta)
    
    def reliability(self, t: float) -> float:
        """Função de confiabilidade R(t)"""
        if not self.fitted:
            raise ValueError("Modelo não foi ajustado")
        return np.exp(-(t/self.eta)**self.beta)
    
    def cdf(self, t: float) -> float:
        """Função de distribuição acumulada F(t)"""
        return 1 - self.reliability(t)
    
    def pdf(self, t: float) -> float:
        """Função densidade de probabilidade f(t)"""
        if not self.fitted:
            raise ValueError("Modelo não foi ajustado")
        return (self.beta/self.eta) * (t/self.eta)**(self.beta-1) * np.exp(-(t/self.eta)**self.beta)
    
    def hazard(self, t: float) -> float:
        """Função de taxa de falha h(t)"""
        if not self.fitted:
            raise ValueError("Modelo não foi ajustado")
        return (self.beta/self.eta) * (t/self.eta)**(self.beta-1)
    
    def weibull_plot_data(self, times: np.ndarray, censored: Optional[np.ndarray] = None):
        """
        Preparar dados para gráfico de probabilidade Weibull
        """
        times = np.asarray(times)
        if censored is None:
            censored = np.zeros(len(times), dtype=bool)
        
        # Usar apenas falhas observadas para o plot
        failure_times = times[~censored]
        failure_times = np.sort(failure_times)
        
        n = len(failure_times)
        if n == 0:
            raise ValueError("Nenhuma falha observada para criar gráfico")
        
        # Posições de plotagem (approximação median rank)
        ranks = np.arange(1, n + 1)
        prob_points = (ranks - 0.3) / (n + 0.4)  # Aproximação Benard
        
        # Transformação para escala Weibull
        ln_times = np.log(failure_times)
        ln_ln_inv_reliability = np.log(-np.log(1 - prob_points))
        
        return {
            'times': failure_times,
            'ln_times': ln_times,
            'probabilities': prob_points,
            'ln_ln_inv_reliability': ln_ln_inv_reliability,
            'ranks': ranks
        }
    
    def create_probability_plot(self, times: np.ndarray, censored: Optional[np.ndarray] = None):
        """Criar gráfico de probabilidade Weibull com Plotly"""
        plot_data = self.weibull_plot_data(times, censored)
        
        fig = go.Figure()
        
        # Pontos dos dados
        fig.add_trace(go.Scatter(
            x=plot_data['ln_times'],
            y=plot_data['ln_ln_inv_reliability'],
            mode='markers',
            name='Dados Observados',
            marker=dict(size=8, color='blue'),
            hovertemplate='Tempo: %{customdata:.1f}h<br>Prob: %{text:.1%}<extra></extra>',
            customdata=plot_data['times'],
            text=plot_data['probabilities']
        ))
        
        # Linha do modelo ajustado (se disponível)
        if self.fitted:
            x_line = np.linspace(plot_data['ln_times'].min(), plot_data['ln_times'].max(), 100)
            y_line = self.beta * (x_line - np.log(self.eta))
            
            fig.add_trace(go.Scatter(
                x=x_line,
                y=y_line,
                mode='lines',
                name=f'Weibull Ajustada (β={self.beta:.2f}, η={self.eta:.0f})',
                line=dict(color='red', width=2)
            ))
        
        fig.update_layout(
            title='Gráfico de Probabilidade Weibull',
            xaxis_title='ln(Tempo)',
            yaxis_title='ln(-ln(1-F))',
            hovermode='closest',
            showlegend=True,
            template='plotly_white'
        )
        
        return fig
    
    def create_reliability_curves(self, max_time: Optional[float] = None):
        """Criar gráficos das funções de confiabilidade"""
        if not self.fitted:
            raise ValueError("Modelo não foi ajustado")
        
        if max_time is None:
            max_time = self.eta * 3  # 3x vida característica
        
        t = np.linspace(0.1, max_time, 1000)
        
        fig = go.Figure()
        
        # Função de confiabilidade
        R_t = [self.reliability(time) for time in t]
        fig.add_trace(go.Scatter(
            x=t, y=R_t,
            name='Confiabilidade R(t)',
            line=dict(color='green', width=2)
        ))
        
        # Função de distribuição acumulada
        F_t = [self.cdf(time) for time in t]
        fig.add_trace(go.Scatter(
            x=t, y=F_t,
            name='Probabilidade de Falha F(t)',
            line=dict(color='red', width=2)
        ))
        
        # Taxa de falha
        h_t = [self.hazard(time) for time in t]
        # Normalizar para visualização
        h_t_norm = np.array(h_t) / np.max(h_t)
        fig.add_trace(go.Scatter(
            x=t, y=h_t_norm,
            name='Taxa de Falha h(t) [norm]',
            line=dict(color='orange', width=2, dash='dash'),
            yaxis='y2'
        ))
        
        # Linhas de referência
        fig.add_hline(y=0.5, line_dash="dot", annotation_text="50%")
        fig.add_vline(x=self.eta, line_dash="dot", annotation_text=f"η={self.eta:.0f}h")
        fig.add_vline(x=self.mtbf, line_dash="dot", annotation_text=f"MTBF={self.mtbf:.0f}h")
        
        fig.update_layout(
            title=f'Funções Weibull (β={self.beta:.2f}, η={self.eta:.0f})',
            xaxis_title='Tempo (horas)',
            yaxis_title='Probabilidade',
            yaxis2=dict(
                title='Taxa de Falha [normalizada]',
                overlaying='y',
                side='right'
            ),
            template='plotly_white',
            hovermode='x unified'
        )
        
        return fig


def compare_distributions(times: np.ndarray, censored: Optional[np.ndarray] = None):
    """
    Comparar Weibull com outras distribuições (Exponencial, Lognormal)
    """
    results = {}
    
    # Weibull
    weibull = WeibullAnalysis()
    try:
        weibull_fit = weibull.fit_mle(times, censored)
        results['Weibull'] = {
            'aic': weibull_fit['aic'],
            'bic': weibull_fit['bic'],
            'log_likelihood': weibull_fit['log_likelihood'],
            'parameters': {'beta': weibull_fit['beta'], 'eta': weibull_fit['eta']},
            'mtbf': weibull_fit['mtbf']
        }
    except Exception as e:
        results['Weibull'] = {'error': str(e)}
    
    # Exponencial (caso especial Weibull com beta=1)
    failure_times = times[~censored if censored is not None else np.zeros(len(times), dtype=bool)]
    if len(failure_times) >= 2:
        try:
            lambda_mle = len(failure_times) / np.sum(failure_times)
            exp_ll = len(failure_times) * np.log(lambda_mle) - lambda_mle * np.sum(failure_times)
            exp_aic = 2 * 1 - 2 * exp_ll  # 1 parâmetro
            exp_bic = np.log(len(failure_times)) * 1 - 2 * exp_ll
            
            results['Exponencial'] = {
                'aic': exp_aic,
                'bic': exp_bic,
                'log_likelihood': exp_ll,
                'parameters': {'lambda': lambda_mle},
                'mtbf': 1/lambda_mle
            }
        except Exception as e:
            results['Exponencial'] = {'error': str(e)}
    
    # Lognormal
    if len(failure_times) >= 2:
        try:
            log_times = np.log(failure_times)
            mu_mle = np.mean(log_times)
            sigma_mle = np.std(log_times, ddof=1)
            
            # Log-likelihood para lognormal
            lognorm_ll = -len(failure_times) * np.log(sigma_mle * np.sqrt(2*np.pi)) - \
                        np.sum(log_times) - np.sum((log_times - mu_mle)**2) / (2 * sigma_mle**2)
            
            lognorm_aic = 2 * 2 - 2 * lognorm_ll  # 2 parâmetros
            lognorm_bic = np.log(len(failure_times)) * 2 - 2 * lognorm_ll
            
            results['Lognormal'] = {
                'aic': lognorm_aic,
                'bic': lognorm_bic,
                'log_likelihood': lognorm_ll,
                'parameters': {'mu': mu_mle, 'sigma': sigma_mle},
                'mtbf': np.exp(mu_mle + sigma_mle**2/2)
            }
        except Exception as e:
            results['Lognormal'] = {'error': str(e)}
    
    return results