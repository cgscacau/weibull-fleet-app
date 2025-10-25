"""
Mapeamento automático de colunas para múltiplos formatos de entrada
"""
import pandas as pd
from typing import Dict, List, Tuple, Optional

# Schema padrão unificado do sistema
STANDARD_SCHEMA = {
    'component_id': str,      # ID único do componente/ativo
    'component_type': str,    # Tipo/nome do componente
    'failure_time': float,    # Tempo até falha (horas)
    'censored': bool          # Se é dado censurado (True) ou falha observada (False)
}

# Colunas opcionais suportadas
OPTIONAL_COLUMNS = [
    'fleet', 'subsystem', 'environment', 
    'install_date', 'failure_date',
    'cost', 'downtime_hours', 'location'
]

# Mapeamentos aceitos (múltiplos nomes aceitos para cada coluna padrão)
COLUMN_MAPPINGS = {
    'component_id': ['component_id', 'asset_id', 'equipment_id', 'id', 'codigo', 'cod_equipamento'],
    'component_type': ['component_type', 'component', 'tipo_componente', 'tipo', 'equipment_type', 'componente'],
    'failure_time': ['failure_time', 'operating_hours', 'hours', 'tempo_falha', 'horas', 'time_to_failure', 'ttf'],
    'censored': ['censored', 'censurado', 'suspended', 'suspenso', 'is_censored']
}


def detect_column_mapping(df: pd.DataFrame) -> Dict[str, str]:
    """
    Detecta automaticamente o mapeamento de colunas do DataFrame
    
    Args:
        df: DataFrame de entrada
        
    Returns:
        Dict mapeando nome padrão -> nome encontrado no DataFrame
    """
    mapping = {}
    df_columns_lower = {col.lower(): col for col in df.columns}
    
    for standard_col, possible_names in COLUMN_MAPPINGS.items():
        for possible_name in possible_names:
            if possible_name.lower() in df_columns_lower:
                mapping[standard_col] = df_columns_lower[possible_name.lower()]
                break
    
    return mapping


def validate_required_columns(df: pd.DataFrame, mapping: Dict[str, str]) -> Tuple[bool, List[str]]:
    """
    Valida se todas as colunas obrigatórias foram encontradas
    
    Args:
        df: DataFrame de entrada
        mapping: Mapeamento detectado
        
    Returns:
        (is_valid, missing_columns)
    """
    required_columns = list(STANDARD_SCHEMA.keys())
    missing = []
    
    for col in required_columns:
        if col not in mapping or mapping[col] not in df.columns:
            missing.append(col)
    
    return len(missing) == 0, missing


def apply_column_mapping(df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
    """
    Aplica o mapeamento de colunas ao DataFrame
    
    Args:
        df: DataFrame original
        mapping: Mapeamento de colunas
        
    Returns:
        DataFrame com colunas renomeadas para padrão
    """
    df_mapped = df.copy()
    
    # Criar mapeamento reverso (nome_original -> nome_padrão)
    rename_dict = {v: k for k, v in mapping.items()}
    
    # Renomear apenas as colunas mapeadas
    df_mapped = df_mapped.rename(columns=rename_dict)
    
    return df_mapped


def infer_censored_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Infere coluna 'censored' se não existir
    
    Args:
        df: DataFrame com colunas já mapeadas
        
    Returns:
        DataFrame com coluna 'censored' adicionada
    """
    if 'censored' not in df.columns:
        # Se há coluna failure_date, usar para inferir censura
        if 'failure_date' in df.columns:
            df['censored'] = df['failure_date'].isna()
        else:
            # Assumir todas como falhas observadas (não censuradas)
            df['censored'] = False
    
    # Garantir tipo booleano
    df['censored'] = df['censored'].astype(bool)
    
    return df


def convert_column_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converte colunas para os tipos corretos
    
    Args:
        df: DataFrame com colunas já mapeadas
        
    Returns:
        DataFrame com tipos de dados corretos
    """
    df_converted = df.copy()
    
    # Converter failure_time para numérico
    if 'failure_time' in df_converted.columns:
        df_converted['failure_time'] = pd.to_numeric(df_converted['failure_time'], errors='coerce')
    
    # Converter component_id e component_type para string
    if 'component_id' in df_converted.columns:
        df_converted['component_id'] = df_converted['component_id'].astype(str)
    
    if 'component_type' in df_converted.columns:
        df_converted['component_type'] = df_converted['component_type'].astype(str)
    
    # Converter censored para bool
    if 'censored' in df_converted.columns:
        df_converted['censored'] = df_converted['censored'].astype(bool)
    
    return df_converted


def clean_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    """
    Limpa dados básicos (remove nulos, valores negativos, etc)
    
    Args:
        df: DataFrame a limpar
        
    Returns:
        (df_clean, cleaning_report)
    """
    df_clean = df.copy()
    report = {
        'initial_rows': len(df),
        'removed_rows': 0,
        'issues': []
    }
    
    # Remover linhas com failure_time nulo
    if 'failure_time' in df_clean.columns:
        nulls = df_clean['failure_time'].isna().sum()
        if nulls > 0:
            df_clean = df_clean.dropna(subset=['failure_time'])
            report['issues'].append(f"Removidas {nulls} linhas com failure_time nulo")
    
    # Remover failure_time negativos ou zero
    if 'failure_time' in df_clean.columns:
        negatives = (df_clean['failure_time'] <= 0).sum()
        if negatives > 0:
            df_clean = df_clean[df_clean['failure_time'] > 0]
            report['issues'].append(f"Removidas {negatives} linhas com failure_time <= 0")
    
    report['removed_rows'] = report['initial_rows'] - len(df_clean)
    report['final_rows'] = len(df_clean)
    
    return df_clean, report


def standardize_dataframe(df: pd.DataFrame) -> Tuple[Optional[pd.DataFrame], Dict]:
    """
    Pipeline completo de padronização de DataFrame
    
    Args:
        df: DataFrame original de entrada
        
    Returns:
        (df_standardized, report) ou (None, report) se falhar
    """
    report = {
        'success': False,
        'mapping': {},
        'missing_columns': [],
        'cleaning': {},
        'warnings': [],
        'original_columns': list(df.columns)
    }
    
    try:
        # 1. Detectar mapeamento de colunas
        mapping = detect_column_mapping(df)
        report['mapping'] = mapping
        
        # 2. Validar colunas obrigatórias
        is_valid, missing = validate_required_columns(df, mapping)
        report['missing_columns'] = missing
        
        if not is_valid:
            # Tentar inferir coluna 'censored' se for a única faltando
            if missing == ['censored']:
                report['warnings'].append("Coluna 'censored' não encontrada - será inferida automaticamente")
            else:
                report['success'] = False
                return None, report
        
        # 3. Aplicar mapeamento
        df_mapped = apply_column_mapping(df, mapping)
        
        # 4. Inferir coluna censored se necessário
        df_mapped = infer_censored_column(df_mapped)
        
        # 5. Converter tipos
        df_converted = convert_column_types(df_mapped)
        
        # 6. Limpar dados
        df_clean, cleaning_report = clean_data(df_converted)
        report['cleaning'] = cleaning_report
        
        # 7. Manter colunas opcionais se existirem
        final_columns = list(STANDARD_SCHEMA.keys())
        for opt_col in OPTIONAL_COLUMNS:
            if opt_col in df_clean.columns:
                final_columns.append(opt_col)
        
        # Manter apenas colunas relevantes
        available_columns = [col for col in final_columns if col in df_clean.columns]
        df_final = df_clean[available_columns].copy()
        
        report['success'] = True
        report['final_columns'] = list(df_final.columns)
        report['final_shape'] = df_final.shape
        
        return df_final, report
    
    except Exception as e:
        report['success'] = False
        report['error'] = str(e)
        return None, report


def create_example_dataframe(format_type: str = 'standard') -> pd.DataFrame:
    """
    Cria DataFrame de exemplo em diferentes formatos
    
    Args:
        format_type: 'standard', 'legacy', 'sap'
        
    Returns:
        DataFrame de exemplo
    """
    import numpy as np
    
    n_samples = 50
    
    if format_type == 'standard':
        return pd.DataFrame({
            'component_id': [f'COMP_{i:03d}' for i in range(n_samples)],
            'component_type': np.random.choice(['Motor', 'Bomba', 'Transmissao', 'Freio'], n_samples),
            'failure_time': np.random.weibull(2, n_samples) * 5000 + 1000,
            'censored': np.random.choice([True, False], n_samples, p=[0.3, 0.7]),
            'fleet': np.random.choice(['Frota_A', 'Frota_B'], n_samples)
        })
    
    elif format_type == 'legacy':
        return pd.DataFrame({
            'asset_id': [f'ASSET_{i:03d}' for i in range(n_samples)],
            'component': np.random.choice(['Motor', 'Bomba', 'Transmissao', 'Freio'], n_samples),
            'operating_hours': np.random.weibull(2, n_samples) * 5000 + 1000,
            'fleet': np.random.choice(['Frota_A', 'Frota_B'], n_samples)
        })
    
    elif format_type == 'sap':
        return pd.DataFrame({
            'equipment_id': [f'EQ_{i:03d}' for i in range(n_samples)],
            'equipment_type': np.random.choice(['Motor', 'Bomba', 'Transmissao', 'Freio'], n_samples),
            'hours': np.random.weibull(2, n_samples) * 5000 + 1000,
            'failure_date': pd.date_range('2023-01-01', periods=n_samples, freq='10D')
        })
    
    return pd.DataFrame()


def get_column_requirements_text() -> str:
    """
    Retorna texto formatado com requisitos de colunas
    
    Returns:
        String markdown com requisitos
    """
    text = """
### 📋 Requisitos de Colunas

**Colunas Obrigatórias** (aceita múltiplos nomes):

1. **ID do Componente/Ativo:**
   - Nomes aceitos: `component_id`, `asset_id`, `equipment_id`, `id`, `codigo`
   - Tipo: Texto (string)

2. **Tipo/Nome do Componente:**
   - Nomes aceitos: `component_type`, `component`, `tipo_componente`, `tipo`, `equipment_type`
   - Tipo: Texto (string)

3. **Tempo até Falha (horas):**
   - Nomes aceitos: `failure_time`, `operating_hours`, `hours`, `tempo_falha`, `horas`
   - Tipo: Número (horas operacionais)

4. **Censura (opcional - será inferido):**
   - Nomes aceitos: `censored`, `censurado`, `suspended`, `suspenso`
   - Tipo: Booleano (True/False ou 0/1)
   - Se não fornecido: será inferido automaticamente

**Colunas Opcionais** (melhoram a análise):
- `fleet`, `subsystem`, `environment`
- `install_date`, `failure_date`
- `cost`, `downtime_hours`, `location`
"""
    return text


if __name__ == "__main__":
    # Teste do mapeamento
    print("=== Teste de Mapeamento de Colunas ===\n")
    
    # Criar exemplo em formato legacy
    df_legacy = create_example_dataframe('legacy')
    print("DataFrame Original (formato legacy):")
    print(df_legacy.head())
    print(f"\nColunas: {df_legacy.columns.tolist()}\n")
    
    # Padronizar
    df_standard, report = standardize_dataframe(df_legacy)
    
    print("Relatório de Padronização:")
    print(f"✅ Sucesso: {report['success']}")
    print(f"📋 Mapeamento: {report['mapping']}")
    print(f"⚠️ Avisos: {report['warnings']}")
    print(f"🧹 Limpeza: {report['cleaning']}")
    print(f"\nShape final: {report['final_shape']}")
    print(f"Colunas finais: {report['final_columns']}")
    
    if df_standard is not None:
        print("\nDataFrame Padronizado:")
        print(df_standard.head())
