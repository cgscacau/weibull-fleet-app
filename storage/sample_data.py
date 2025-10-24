"""
Gerador de dados de exemplo para teste do sistema
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy.stats import weibull_min
import random


def generate_sample_fleet_data(n_records: int = 500) -> pd.DataFrame:
    """Gerar dados de exemplo representativos de frota de mineração"""
    
    np.random.seed(42)
    random.seed(42)
    
    # Definir componentes e suas características Weibull
    components_params = {
        'Motor': {'beta': 1.8, 'eta': 8000, 'cost': 25000},
        'Transmissão': {'beta': 2.2, 'eta': 6500, 'cost': 18000},
        'Bomba Hidráulica': {'beta': 2.8, 'eta': 4500, 'cost': 8000},
        'Pneu': {'beta': 2.5, 'eta': 3200, 'cost': 1200},
        'Sistema de Freio': {'beta': 1.9, 'eta': 5500, 'cost': 3500},
        'Radiador': {'beta': 1.6, 'eta': 7200, 'cost': 2800},
        'Bateria': {'beta': 3.2, 'eta': 2800, 'cost': 450},
        'Alternador': {'beta': 2.0, 'eta': 5800, 'cost': 1800},
        'Filtro de Ar': {'beta': 1.4, 'eta': 1500, 'cost': 120},
        'Turbocompressor': {'beta': 2.6, 'eta': 9500, 'cost': 12000}
    }
    
    # Frotas disponíveis
    fleets = ['CAT 777', 'CAT 785', 'CAT 789', 'Komatsu PC930', 'Volvo EC750']
    
    # Ambientes operacionais
    environments = ['Mina A', 'Mina B', 'Pedreira C', 'Porto D']
    
    # Operadores
    operators = [f'Operador_{i:02d}' for i in range(1, 26)]
    
    records = []
    
    for i in range(n_records):
        # Selecionar componente aleatório
        component = random.choice(list(components_params.keys()))
        params = components_params[component]
        
        # Gerar asset_id
        fleet = random.choice(fleets)
        asset_id = f"{fleet.replace(' ', '')}-{random.randint(1000, 9999)}"
        
        # Data de instalação (últimos 3 anos)
        install_date = datetime.now() - timedelta(days=random.randint(1, 1095))
        
        # Gerar tempo até falha usando Weibull
        failure_time = weibull_min.rvs(c=params['beta'], scale=params['eta'])
        
        # Adicionar variabilidade por ambiente (algumas condições mais severas)
        environment = random.choice(environments)
        if environment in ['Mina A', 'Pedreira C']:  # Ambientes mais severos
            failure_time *= 0.7  # Reduzir vida útil
        
        # Decidir se é censurado (20% dos casos)
        is_censored = random.random() < 0.2
        
        if is_censored:
            # Item ainda em operação - usar tempo atual
            operating_hours = random.uniform(100, failure_time * 0.8)
            failure_date = None
        else:
            # Item falhou
            operating_hours = failure_time
            failure_date = install_date + timedelta(hours=failure_time/24)
        
        # Adicionar variabilidade no horímetro (alguns erros de medição)
        operating_hours *= random.uniform(0.95, 1.05)
        operating_hours = max(1, operating_hours)  # Garantir valor positivo
        
        # Tipos de manutenção
        maintenance_types = ['corretiva', 'preventiva', 'preditiva']
        
        record = {
            'asset_id': asset_id,
            'component': component,
            'subsystem': _get_subsystem(component),
            'fleet': fleet,
            'install_date': install_date.date(),
            'failure_date': failure_date.date() if failure_date else None,
            'operating_hours': round(operating_hours, 1),
            'censored': is_censored,
            'failure_mode': _get_failure_mode(component) if not is_censored else None,
            'environment': environment,
            'operator': random.choice(operators),
            'maintenance_type': random.choice(maintenance_types) if not is_censored else None,
            'cost': params['cost'] * random.uniform(0.8, 1.3) if not is_censored else None,
            'downtime_hours': random.uniform(2, 24) if not is_censored else None
        }
        
        records.append(record)
    
    df = pd.DataFrame(records)
    
    # Adicionar alguns dados com problemas intencionais para testar limpeza
    _add_data_quality_issues(df)
    
    return df


def _get_subsystem(component: str) -> str:
    """Mapear componente para subsistema"""
    subsystem_map = {
        'Motor': 'Powertrain',
        'Transmissão': 'Powertrain',
        'Bomba Hidráulica': 'Sistema Hidráulico',
        'Pneu': 'Rodado',
        'Sistema de Freio': 'Freios',
        'Radiador': 'Arrefecimento',
        'Bateria': 'Elétrico',
        'Alternador': 'Elétrico',
        'Filtro de Ar': 'Admissão',
        'Turbocompressor': 'Admissão'
    }
    return subsystem_map.get(component, 'Outros')


def _get_failure_mode(component: str) -> str:
    """Gerar modo de falha típico para o componente"""
    failure_modes = {
        'Motor': ['Desgaste de anéis', 'Superaquecimento', 'Vazamento de óleo'],
        'Transmissão': ['Desgaste de engrenagens', 'Vazamento hidráulico', 'Sobrecarga'],
        'Bomba Hidráulica': ['Desgaste interno', 'Contaminação', 'Cavitação'],
        'Pneu': ['Desgaste excessivo', 'Corte lateral', 'Separação da banda'],
        'Sistema de Freio': ['Desgaste de pastilhas', 'Vazamento', 'Superaquecimento'],
        'Radiador': ['Entupimento', 'Vazamento', 'Corrosão'],
        'Bateria': ['Descarga profunda', 'Sulfatação', 'Célula danificada'],
        'Alternador': ['Desgaste de escovas', 'Curto-circuito', 'Rolamento'],
        'Filtro de Ar': ['Entupimento', 'Rasgo', 'Selo danificado'],
        'Turbocompressor': ['Desgaste de turbina', 'Vazamento de óleo', 'Desbalanceamento']
    }
    
    modes = failure_modes.get(component, ['Falha genérica'])
    return random.choice(modes)


def _add_data_quality_issues(df: pd.DataFrame):
    """Adicionar problemas de qualidade nos dados para testar limpeza"""
    n = len(df)
    
    # 1. Alguns nomes de componentes não padronizados
    problem_indices = np.random.choice(n, size=int(n*0.1), replace=False)
    name_variations = {
        'Bomba Hidráulica': ['bomba hidr', 'Bomba Hid', 'B. Hidraulica'],
        'Sistema de Freio': ['freio', 'Freios', 'Sist Freio'],
        'Motor': ['motor diesel', 'Motor Principal', 'motor'],
    }
    
    for idx in problem_indices:
        component = df.loc[idx, 'component']
        if component in name_variations:
            df.loc[idx, 'component'] = random.choice(name_variations[component])
    
    # 2. Alguns valores extremos (outliers)
    outlier_indices = np.random.choice(n, size=int(n*0.02), replace=False)
    for idx in outlier_indices:
        if random.random() < 0.5:
            # Valor muito alto
            df.loc[idx, 'operating_hours'] *= random.uniform(5, 10)
        else:
            # Valor muito baixo (mas positivo)
            df.loc[idx, 'operating_hours'] *= random.uniform(0.01, 0.1)
    
    # 3. Alguns dados faltantes adicionais
    missing_indices = np.random.choice(n, size=int(n*0.05), replace=False)
    for idx in missing_indices:
        if random.random() < 0.5:
            df.loc[idx, 'operator'] = None
        else:
            df.loc[idx, 'subsystem'] = None
    
    # 4. Alguns formatos de frota inconsistentes
    fleet_indices = np.random.choice(n, size=int(n*0.08), replace=False)
    for idx in fleet_indices:
        fleet = df.loc[idx, 'fleet']
        if 'CAT' in fleet:
            variations = [fleet.replace('CAT ', 'Cat'), fleet.replace(' ', ''), 
                         fleet.lower(), fleet.replace('CAT', 'Caterpillar')]
            df.loc[idx, 'fleet'] = random.choice(variations)


def save_sample_data():
    """Salvar dados de exemplo em diferentes formatos"""
    df = generate_sample_fleet_data(500)
    
    # Salvar como CSV
    df.to_csv('/home/user/weibull-fleet-app/storage/sample_fleet_data.csv', index=False)
    
    # Salvar como Excel
    df.to_excel('/home/user/weibull-fleet-app/storage/sample_fleet_data.xlsx', index=False)
    
    # Salvar subconjuntos por componente para testes específicos
    for component in df['component'].unique():
        if df[df['component'] == component].shape[0] >= 10:  # Apenas componentes com dados suficientes
            component_df = df[df['component'] == component].copy()
            filename = f"sample_{component.replace(' ', '_').lower()}_data.csv"
            component_df.to_csv(f'/home/user/weibull-fleet-app/storage/{filename}', index=False)
    
    print(f"Dados de exemplo salvos com {len(df)} registros")
    print(f"Componentes: {df['component'].unique()}")
    print(f"Frotas: {df['fleet'].unique()}")
    return df


if __name__ == "__main__":
    save_sample_data()