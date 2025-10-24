"""
Módulo de limpeza e padronização de dados
"""
import pandas as pd
import numpy as np
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import warnings


class DataCleaner:
    """Classe para limpeza e padronização de dados de confiabilidade"""
    
    def __init__(self):
        # Mapeamentos padrão para normalização
        self.component_mappings = {
            # Motores
            r'motor|engine|powertrain': 'Motor',
            r'transmiss[aã]o|transmission|gearbox': 'Transmissão',
            r'diferencial|differential': 'Diferencial',
            
            # Sistema hidráulico
            r'bomba.*hidr|hydraulic.*pump|bomba.*hyd': 'Bomba Hidráulica',
            r'cilindro.*hidr|hydraulic.*cylinder': 'Cilindro Hidráulico',
            r'filtro.*hidr|hydraulic.*filter': 'Filtro Hidráulico',
            r'mangueira.*hidr|hydraulic.*hose': 'Mangueira Hidráulica',
            
            # Rodas e pneus
            r'pneu|tire|wheel': 'Pneu',
            r'aro|rim': 'Aro',
            r'cubo|hub': 'Cubo de Roda',
            
            # Sistema de freios
            r'freio|brake': 'Sistema de Freio',
            r'pastilha|pad': 'Pastilha de Freio',
            r'disco.*freio|brake.*disc': 'Disco de Freio',
            
            # Elétrico
            r'bateria|battery': 'Bateria',
            r'alternador|alternator': 'Alternador',
            r'motor.*partida|starter': 'Motor de Partida',
            
            # Filtros
            r'filtro.*ar|air.*filter': 'Filtro de Ar',
            r'filtro.*combustivel|fuel.*filter': 'Filtro de Combustível',
            r'filtro.*oleo|oil.*filter': 'Filtro de Óleo',
            
            # Sistemas específicos
            r'radiador|radiator': 'Radiador',
            r'turbo|turbocharger': 'Turbocompressor',
            r'injetor|injector': 'Injetor',
        }
        
        self.fleet_mappings = {
            r'cat.*777|777': 'CAT 777',
            r'cat.*785|785': 'CAT 785',
            r'cat.*789|789': 'CAT 789',
            r'cat.*797|797': 'CAT 797',
            r'cat.*336|336': 'CAT 336',
            r'cat.*349|349': 'CAT 349',
            r'komatsu.*930|930': 'Komatsu PC930',
            r'komatsu.*450|450': 'Komatsu PC450',
            r'volvo.*ec750|ec750': 'Volvo EC750',
        }
    
    def standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Padronizar nomes e tipos das colunas"""
        df = df.copy()
        
        # Mapeamento de colunas comuns
        column_mappings = {
            'equipamento': 'asset_id',
            'equipment': 'asset_id',
            'ativo': 'asset_id',
            'asset': 'asset_id',
            'componente': 'component',
            'component_name': 'component',
            'parte': 'component',
            'sistema': 'subsystem',
            'subsistema': 'subsystem',
            'system': 'subsystem',
            'frota': 'fleet',
            'modelo': 'fleet',
            'model': 'fleet',
            'data_instalacao': 'install_date',
            'install': 'install_date',
            'instalacao': 'install_date',
            'data_falha': 'failure_date',
            'failure': 'failure_date',
            'falha': 'failure_date',
            'horas': 'operating_hours',
            'hours': 'operating_hours',
            'horimetro': 'operating_hours',
            'odometer': 'operating_hours',
            'km': 'operating_hours',
            'censurado': 'censored',
            'censored_flag': 'censored',
            'right_censored': 'censored',
            'modo_falha': 'failure_mode',
            'failure_mode_desc': 'failure_mode',
            'ambiente': 'environment',
            'operador': 'operator',
            'custo': 'cost',
            'cost_usd': 'cost',
            'valor': 'cost',
            'parada': 'downtime_hours',
            'downtime': 'downtime_hours',
            'tempo_parada': 'downtime_hours'
        }
        
        # Renomear colunas (case insensitive)
        df_columns_lower = {col.lower().strip(): col for col in df.columns}
        rename_dict = {}
        
        for old_name, new_name in column_mappings.items():
            for df_col_lower, df_col_original in df_columns_lower.items():
                if old_name.lower() in df_col_lower or df_col_lower in old_name.lower():
                    rename_dict[df_col_original] = new_name
                    break
        
        df = df.rename(columns=rename_dict)
        
        # Converter tipos de dados
        if 'operating_hours' in df.columns:
            df['operating_hours'] = pd.to_numeric(df['operating_hours'], errors='coerce')
        
        if 'cost' in df.columns:
            df['cost'] = pd.to_numeric(df['cost'], errors='coerce')
        
        if 'downtime_hours' in df.columns:
            df['downtime_hours'] = pd.to_numeric(df['downtime_hours'], errors='coerce')
        
        # Converter datas
        for date_col in ['install_date', 'failure_date']:
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        
        return df
    
    def fix_units(self, df: pd.DataFrame) -> pd.DataFrame:
        """Padronizar unidades (converter km para horas, etc.)"""
        df = df.copy()
        
        if 'operating_hours' not in df.columns:
            return df
        
        # Detectar se valores estão em km (valores muito altos)
        median_hours = df['operating_hours'].median()
        
        # Se mediana > 50000, provavelmente está em km
        if median_hours > 50000:
            warnings.warn("Detectados valores altos em operating_hours. Convertendo de km para horas (assumindo 25 km/h médio)")
            df['operating_hours'] = df['operating_hours'] / 25  # Assumir 25 km/h médio
        
        # Remover valores negativos
        df.loc[df['operating_hours'] < 0, 'operating_hours'] = np.nan
        
        return df
    
    def deduplicate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remover duplicatas baseado em colunas chave"""
        df = df.copy()
        
        # Colunas para identificar duplicatas
        key_columns = ['asset_id', 'component', 'install_date']
        key_columns = [col for col in key_columns if col in df.columns]
        
        if len(key_columns) >= 2:
            # Manter registro mais recente em caso de duplicata
            df = df.sort_values('failure_date', na_last=True)
            df = df.drop_duplicates(subset=key_columns, keep='last')
        
        return df
    
    def normalize_component_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalizar nomes de componentes usando regex"""
        df = df.copy()
        
        if 'component' not in df.columns:
            return df
        
        # Aplicar mapeamentos
        df['component_original'] = df['component'].copy()
        
        for pattern, replacement in self.component_mappings.items():
            mask = df['component'].str.contains(pattern, case=False, regex=True, na=False)
            df.loc[mask, 'component'] = replacement
        
        return df
    
    def normalize_fleet_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalizar nomes de frota/modelo"""
        df = df.copy()
        
        if 'fleet' not in df.columns:
            return df
        
        # Aplicar mapeamentos
        df['fleet_original'] = df['fleet'].copy()
        
        for pattern, replacement in self.fleet_mappings.items():
            mask = df['fleet'].str.contains(pattern, case=False, regex=True, na=False)
            df.loc[mask, 'fleet'] = replacement
        
        return df
    
    def detect_outliers(self, df: pd.DataFrame, column: str = 'operating_hours') -> pd.DataFrame:
        """Detectar outliers usando IQR"""
        if column not in df.columns:
            return df
        
        df = df.copy()
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        df['is_outlier'] = (df[column] < lower_bound) | (df[column] > upper_bound)
        
        return df
    
    def infer_censoring(self, df: pd.DataFrame) -> pd.DataFrame:
        """Inferir censura baseado em dados disponíveis"""
        df = df.copy()
        
        if 'censored' not in df.columns:
            df['censored'] = False
        
        # Se não há data de falha, assumir censurado
        if 'failure_date' in df.columns:
            df.loc[df['failure_date'].isna(), 'censored'] = True
            df.loc[df['failure_date'].notna(), 'censored'] = False
        
        # Se operating_hours é muito baixo, pode ser instalação recente (censurar)
        if 'operating_hours' in df.columns and 'install_date' in df.columns:
            recent_installs = (datetime.now().date() - df['install_date'].dt.date) < timedelta(days=30)
            low_hours = df['operating_hours'] < 100
            df.loc[recent_installs & low_hours, 'censored'] = True
        
        return df
    
    def validate_data_quality(self, df: pd.DataFrame) -> Dict:
        """Validar qualidade dos dados e gerar relatório"""
        report = {
            'total_records': len(df),
            'missing_data': {},
            'data_types': {},
            'outliers': {},
            'date_issues': {},
            'quality_score': 0.0
        }
        
        # Analisar dados faltantes
        for col in df.columns:
            missing_pct = df[col].isna().sum() / len(df) * 100
            report['missing_data'][col] = missing_pct
        
        # Analisar tipos de dados
        report['data_types'] = df.dtypes.to_dict()
        
        # Detectar outliers em colunas numéricas
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col in df.columns and df[col].notna().sum() > 0:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower = Q1 - 1.5 * IQR
                upper = Q3 + 1.5 * IQR
                outliers = ((df[col] < lower) | (df[col] > upper)).sum()
                report['outliers'][col] = outliers
        
        # Validar datas
        for date_col in ['install_date', 'failure_date']:
            if date_col in df.columns:
                future_dates = (df[date_col] > datetime.now()).sum()
                report['date_issues'][f'{date_col}_future'] = future_dates
        
        if 'install_date' in df.columns and 'failure_date' in df.columns:
            invalid_sequence = (df['failure_date'] < df['install_date']).sum()
            report['date_issues']['failure_before_install'] = invalid_sequence
        
        # Calcular score de qualidade
        quality_factors = []
        
        # Fator 1: Completude dos dados essenciais
        essential_cols = ['asset_id', 'component', 'operating_hours']
        essential_complete = sum([
            1 - (report['missing_data'].get(col, 100) / 100) 
            for col in essential_cols if col in df.columns
        ]) / len(essential_cols)
        quality_factors.append(essential_complete)
        
        # Fator 2: Proporção de outliers
        total_outliers = sum(report['outliers'].values())
        outlier_factor = max(0, 1 - (total_outliers / len(df)))
        quality_factors.append(outlier_factor)
        
        # Fator 3: Problemas de data
        date_problems = sum(report['date_issues'].values())
        date_factor = max(0, 1 - (date_problems / len(df)))
        quality_factors.append(date_factor)
        
        report['quality_score'] = np.mean(quality_factors)
        
        return report
    
    def full_cleaning_pipeline(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """Pipeline completo de limpeza"""
        original_shape = df.shape
        
        # Aplicar todas as etapas
        df_clean = df.copy()
        df_clean = self.standardize_columns(df_clean)
        df_clean = self.fix_units(df_clean)
        df_clean = self.normalize_component_names(df_clean)
        df_clean = self.normalize_fleet_names(df_clean)
        df_clean = self.deduplicate(df_clean)
        df_clean = self.infer_censoring(df_clean)
        df_clean = self.detect_outliers(df_clean)
        
        # Relatório de qualidade
        quality_report = self.validate_data_quality(df_clean)
        
        # Adicionar informações sobre limpeza
        cleaning_summary = {
            'original_records': original_shape[0],
            'cleaned_records': df_clean.shape[0],
            'records_removed': original_shape[0] - df_clean.shape[0],
            'columns_added': df_clean.shape[1] - original_shape[1],
            'quality_report': quality_report
        }
        
        return df_clean, cleaning_summary


def apply_ai_normalization(df: pd.DataFrame, 
                          columns: List[str] = ['component', 'fleet'],
                          ai_assistant=None) -> pd.DataFrame:
    """
    Aplicar normalização assistida por IA (placeholder para integração futura)
    """
    df_norm = df.copy()
    
    if ai_assistant is None:
        # Fallback para limpeza baseada em regras
        cleaner = DataCleaner()
        if 'component' in columns:
            df_norm = cleaner.normalize_component_names(df_norm)
        if 'fleet' in columns:
            df_norm = cleaner.normalize_fleet_names(df_norm)
        return df_norm
    
    # TODO: Implementar chamada para IA
    # unique_values = {}
    # for col in columns:
    #     if col in df.columns:
    #         unique_values[col] = df[col].unique().tolist()
    # 
    # normalized_mappings = ai_assistant.normalize_categories(unique_values)
    # 
    # for col, mappings in normalized_mappings.items():
    #     for old_value, new_value in mappings.items():
    #         df_norm.loc[df_norm[col] == old_value, col] = new_value
    
    return df_norm