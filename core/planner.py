"""
Módulo de planejamento de manutenção e gestão de estoque
"""
import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import math


@dataclass
class MaintenanceStrategy:
    """Estratégia de manutenção calculada"""
    component: str
    recommended_interval: float
    reliability_at_interval: float
    risk_level: str
    cost_per_failure: Optional[float] = None
    cost_per_maintenance: Optional[float] = None
    total_cost_rate: Optional[float] = None


@dataclass
class SparePartsRecommendation:
    """Recomendação de estoque de peças"""
    component: str
    annual_demand: float
    lead_time_demand: float
    safety_stock: int
    reorder_point: int
    economic_order_quantity: int
    service_level: float
    total_cost: float


class MaintenancePlanner:
    """Planejador de manutenção baseado em análise Weibull"""
    
    def __init__(self, beta: float, eta: float, component: str = ""):
        self.beta = beta
        self.eta = eta
        self.component = component
        
    def optimal_pm_interval(self, 
                          policy: str = "reliability_target",
                          target_reliability: float = 0.8,
                          fraction_of_eta: float = 0.75,
                          cost_failure: float = None,
                          cost_pm: float = None) -> MaintenanceStrategy:
        """
        Calcular intervalo ótimo de manutenção preventiva
        
        Args:
            policy: "reliability_target", "fraction_of_eta", ou "cost_optimal"
            target_reliability: Nível de confiabilidade desejado (0-1)
            fraction_of_eta: Fração da vida característica (típico 0.7-0.8)
            cost_failure: Custo de falha corretiva
            cost_pm: Custo de manutenção preventiva
        """
        
        if policy == "reliability_target":
            # Calcular tempo para atingir confiabilidade alvo
            if target_reliability <= 0 or target_reliability >= 1:
                raise ValueError("target_reliability deve estar entre 0 e 1")
            
            # R(t) = exp(-(t/η)^β) = target_reliability
            # t = η * (-ln(R))^(1/β)
            interval = self.eta * (-np.log(target_reliability))**(1/self.beta)
            reliability = target_reliability
            
        elif policy == "fraction_of_eta":
            # Usar fração da vida característica
            interval = self.eta * fraction_of_eta
            reliability = np.exp(-(fraction_of_eta)**self.beta)
            
        elif policy == "cost_optimal" and cost_failure and cost_pm:
            # Otimização baseada em custo total
            interval = self._optimize_cost_based_interval(cost_failure, cost_pm)
            reliability = np.exp(-(interval/self.eta)**self.beta)
            
        else:
            raise ValueError("Policy deve ser 'reliability_target', 'fraction_of_eta' ou 'cost_optimal'")
        
        # Avaliar nível de risco
        if reliability >= 0.9:
            risk_level = "Baixo"
        elif reliability >= 0.7:
            risk_level = "Médio"
        else:
            risk_level = "Alto"
        
        # Calcular taxa de custo total se custos fornecidos
        total_cost_rate = None
        if cost_failure and cost_pm:
            total_cost_rate = self._calculate_cost_rate(interval, cost_failure, cost_pm)
        
        return MaintenanceStrategy(
            component=self.component,
            recommended_interval=interval,
            reliability_at_interval=reliability,
            risk_level=risk_level,
            cost_per_failure=cost_failure,
            cost_per_maintenance=cost_pm,
            total_cost_rate=total_cost_rate
        )
    
    def _optimize_cost_based_interval(self, cost_failure: float, cost_pm: float) -> float:
        """Otimizar intervalo baseado no custo total mínimo"""
        
        def cost_rate(t):
            if t <= 0:
                return float('inf')
            
            # Probabilidade de falha até t
            F_t = 1 - np.exp(-(t/self.eta)**self.beta)
            
            # Taxa de custo = (Custo esperado por ciclo) / (Duração esperada do ciclo)
            # Assumindo renovação após PM ou falha
            expected_cost = cost_pm + cost_failure * F_t
            expected_time = t * np.exp(-(t/self.eta)**self.beta) + \
                           (self.eta * math.gamma(1 + 1/self.beta)) * F_t
            
            return expected_cost / expected_time if expected_time > 0 else float('inf')
        
        # Busca pelo mínimo
        from scipy.optimize import minimize_scalar
        
        result = minimize_scalar(
            cost_rate,
            bounds=(0.1 * self.eta, 2 * self.eta),
            method='bounded'
        )
        
        return result.x if result.success else self.eta * 0.75
    
    def _calculate_cost_rate(self, interval: float, cost_failure: float, cost_pm: float) -> float:
        """Calcular taxa de custo para um dado intervalo"""
        if interval <= 0:
            return float('inf')
        
        F_t = 1 - np.exp(-(interval/self.eta)**self.beta)
        expected_cost = cost_pm + cost_failure * F_t
        
        # Duração esperada considerando renovação
        expected_time = interval * np.exp(-(interval/self.eta)**self.beta) + \
                       (self.eta * math.gamma(1 + 1/self.beta)) * F_t
        
        return expected_cost / expected_time if expected_time > 0 else float('inf')
    
    def reliability_over_time(self, times: np.ndarray) -> np.ndarray:
        """Calcular confiabilidade para diferentes tempos"""
        return np.exp(-(times/self.eta)**self.beta)
    
    def mission_reliability(self, mission_time: float, maintenance_intervals: List[float]) -> float:
        """
        Calcular confiabilidade para uma missão com manutenções programadas
        
        Args:
            mission_time: Tempo total da missão
            maintenance_intervals: Lista de tempos de manutenção
        """
        if not maintenance_intervals:
            return self.reliability_over_time(np.array([mission_time]))[0]
        
        # Ordenar intervalos
        intervals = sorted(maintenance_intervals)
        current_time = 0
        total_reliability = 1.0
        
        for maintenance_time in intervals:
            if maintenance_time > mission_time:
                break
            
            # Confiabilidade até próxima manutenção
            segment_time = maintenance_time - current_time
            segment_reliability = np.exp(-(segment_time/self.eta)**self.beta)
            total_reliability *= segment_reliability
            
            current_time = maintenance_time
        
        # Último segmento até fim da missão
        if current_time < mission_time:
            final_segment = mission_time - current_time
            final_reliability = np.exp(-(final_segment/self.eta)**self.beta)
            total_reliability *= final_reliability
        
        return total_reliability


class SparePartsPlanner:
    """Planejador de estoque de peças de reposição"""
    
    def __init__(self):
        pass
    
    def calculate_demand(self, 
                        mtbf: float,
                        fleet_size: int,
                        operational_hours_per_year: float = 8760,
                        demand_variability: str = "poisson") -> Dict:
        """
        Calcular demanda anual esperada de peças
        
        Args:
            mtbf: Tempo médio entre falhas
            fleet_size: Tamanho da frota
            operational_hours_per_year: Horas operacionais por ano
            demand_variability: Modelo de variabilidade ("poisson", "normal")
        """
        
        # Taxa de falha (falhas por hora por equipamento)
        failure_rate = 1.0 / mtbf
        
        # Demanda anual esperada
        annual_demand = fleet_size * failure_rate * operational_hours_per_year
        
        # Demanda mensal
        monthly_demand = annual_demand / 12
        
        # Variância da demanda (depende do modelo)
        if demand_variability == "poisson":
            annual_variance = annual_demand  # Poisson: var = mean
            monthly_variance = monthly_demand
        else:  # normal
            # Assumir CV = 0.3 (coeficiente de variação típico)
            cv = 0.3
            annual_variance = (annual_demand * cv) ** 2
            monthly_variance = (monthly_demand * cv) ** 2
        
        return {
            'annual_demand_mean': annual_demand,
            'annual_demand_std': np.sqrt(annual_variance),
            'monthly_demand_mean': monthly_demand,
            'monthly_demand_std': np.sqrt(monthly_variance),
            'daily_demand_mean': annual_demand / 365,
            'failure_rate': failure_rate
        }
    
    def optimize_inventory(self,
                          annual_demand: float,
                          lead_time_days: int,
                          service_level: float = 0.95,
                          holding_cost_rate: float = 0.2,
                          ordering_cost: float = 50,
                          unit_cost: float = 1000) -> SparePartsRecommendation:
        """
        Otimizar política de estoque (Q,R) considerando incerteza na demanda
        
        Args:
            annual_demand: Demanda anual esperada
            lead_time_days: Tempo de reposição em dias
            service_level: Nível de serviço desejado (0-1)
            holding_cost_rate: Taxa de custo de estoque (fração do valor por ano)
            ordering_cost: Custo fixo por pedido
            unit_cost: Custo unitário da peça
        """
        
        # Converter lead time para fração do ano
        lead_time_years = lead_time_days / 365
        
        # Demanda durante lead time (assumindo Poisson)
        lead_time_demand_mean = annual_demand * lead_time_years
        lead_time_demand_std = np.sqrt(lead_time_demand_mean)  # Poisson
        
        # Economic Order Quantity (EOQ) básico
        eoq = np.sqrt(2 * annual_demand * ordering_cost / (holding_cost_rate * unit_cost))
        
        # Safety stock para atingir nível de serviço
        z_score = stats.norm.ppf(service_level)
        safety_stock = z_score * lead_time_demand_std
        
        # Ponto de reposição
        reorder_point = lead_time_demand_mean + safety_stock
        
        # Custos
        holding_cost = (eoq/2 + safety_stock) * holding_cost_rate * unit_cost
        ordering_cost_annual = (annual_demand / eoq) * ordering_cost
        total_cost = holding_cost + ordering_cost_annual
        
        return SparePartsRecommendation(
            component="",  # Será preenchido externamente
            annual_demand=annual_demand,
            lead_time_demand=lead_time_demand_mean,
            safety_stock=int(np.ceil(safety_stock)),
            reorder_point=int(np.ceil(reorder_point)),
            economic_order_quantity=int(np.ceil(eoq)),
            service_level=service_level,
            total_cost=total_cost
        )
    
    def simulate_inventory_performance(self,
                                     eoq: int,
                                     reorder_point: int,
                                     annual_demand: float,
                                     lead_time_days: int,
                                     num_simulations: int = 1000) -> Dict:
        """
        Simular performance do sistema de estoque
        """
        
        # Parâmetros da simulação
        daily_demand_rate = annual_demand / 365
        lead_time_years = lead_time_days / 365
        
        stockouts = 0
        total_holding = 0
        
        for _ in range(num_simulations):
            # Simular demanda durante lead time
            lead_time_demand = np.random.poisson(annual_demand * lead_time_years)
            
            # Verificar se houve stockout
            if lead_time_demand > reorder_point:
                stockouts += 1
            
            # Estoque médio (simplificado)
            avg_inventory = eoq/2 + max(0, reorder_point - lead_time_demand)
            total_holding += avg_inventory
        
        actual_service_level = 1 - (stockouts / num_simulations)
        avg_inventory = total_holding / num_simulations
        
        return {
            'simulated_service_level': actual_service_level,
            'average_inventory': avg_inventory,
            'stockout_probability': stockouts / num_simulations
        }


def create_maintenance_scenario_analysis(beta: float, eta: float, 
                                       intervals: List[float],
                                       cost_failure: float = 10000,
                                       cost_pm: float = 1000) -> pd.DataFrame:
    """
    Criar análise de cenários para diferentes intervalos de manutenção
    """
    planner = MaintenancePlanner(beta, eta)
    
    scenarios = []
    for interval in intervals:
        reliability = np.exp(-(interval/eta)**beta)
        cost_rate = planner._calculate_cost_rate(interval, cost_failure, cost_pm)
        
        # Frequência de manutenção por ano (assumindo 8760h/ano)
        pm_frequency = 8760 / interval if interval > 0 else float('inf')
        
        scenarios.append({
            'Intervalo (h)': interval,
            'Confiabilidade': reliability,
            'Taxa de Custo ($/h)': cost_rate,
            'PM por ano': pm_frequency,
            'Custo PM/ano ($)': pm_frequency * cost_pm,
            'Nível de Risco': 'Baixo' if reliability >= 0.9 else 'Médio' if reliability >= 0.7 else 'Alto'
        })
    
    return pd.DataFrame(scenarios)