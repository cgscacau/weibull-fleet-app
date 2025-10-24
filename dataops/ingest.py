"""
Módulo de ingestão de dados de diferentes fontes
"""
import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine
from typing import Dict, Optional, Union
import requests
import json
from pathlib import Path


class DataIngestor:
    """Classe para ingestão de dados de múltiplas fontes"""
    
    def __init__(self):
        pass
    
    def read_csv(self, file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
        """Ler dados de arquivo CSV"""
        try:
            # Tentar diferentes encodings
            encodings = ['utf-8', 'latin1', 'cp1252']
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding, **kwargs)
                    return df
                except UnicodeDecodeError:
                    continue
            
            # Se todos falharem, usar utf-8 com errors='ignore'
            df = pd.read_csv(file_path, encoding='utf-8', errors='ignore', **kwargs)
            return df
            
        except Exception as e:
            raise Exception(f"Erro ao ler CSV: {str(e)}")
    
    def read_excel(self, file_path: Union[str, Path], sheet_name: Optional[str] = None, **kwargs) -> pd.DataFrame:
        """Ler dados de arquivo Excel"""
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, **kwargs)
            return df
        except Exception as e:
            raise Exception(f"Erro ao ler Excel: {str(e)}")
    
    def read_sql(self, 
                 query: str, 
                 connection_string: str,
                 **kwargs) -> pd.DataFrame:
        """Ler dados de banco SQL"""
        try:
            engine = create_engine(connection_string)
            df = pd.read_sql(query, engine, **kwargs)
            return df
        except Exception as e:
            raise Exception(f"Erro ao conectar SQL: {str(e)}")
    
    def read_sap_api(self,
                     endpoint: str,
                     api_key: str,
                     parameters: Optional[Dict] = None) -> pd.DataFrame:
        """Ler dados de API SAP (exemplo genérico)"""
        try:
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                endpoint,
                headers=headers,
                params=parameters or {},
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Assumir que os dados estão em formato tabular
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict) and 'results' in data:
                df = pd.DataFrame(data['results'])
            elif isinstance(data, dict) and 'data' in data:
                df = pd.DataFrame(data['data'])
            else:
                raise Exception("Formato de resposta API não reconhecido")
            
            return df
            
        except Exception as e:
            raise Exception(f"Erro ao acessar API SAP: {str(e)}")
    
    def read_rest_api(self,
                      endpoint: str,
                      headers: Optional[Dict] = None,
                      parameters: Optional[Dict] = None) -> pd.DataFrame:
        """Ler dados de API REST genérica"""
        try:
            response = requests.get(
                endpoint,
                headers=headers or {},
                params=parameters or {},
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Tentar diferentes estruturas de resposta
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                # Tentar chaves comuns
                for key in ['data', 'results', 'items', 'records']:
                    if key in data and isinstance(data[key], list):
                        df = pd.DataFrame(data[key])
                        break
                else:
                    # Se não encontrar, usar o dict completo
                    df = pd.DataFrame([data])
            else:
                raise Exception("Formato de resposta não suportado")
            
            return df
            
        except Exception as e:
            raise Exception(f"Erro ao acessar API REST: {str(e)}")
    
    def validate_columns(self, df: pd.DataFrame, required_columns: list) -> Dict:
        """Validar se colunas obrigatórias estão presentes"""
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        validation_result = {
            'valid': len(missing_columns) == 0,
            'missing_columns': missing_columns,
            'available_columns': list(df.columns),
            'suggestions': []
        }
        
        # Sugerir colunas similares
        if missing_columns:
            available_lower = [col.lower() for col in df.columns]
            
            for missing in missing_columns:
                missing_lower = missing.lower()
                suggestions = []
                
                for i, available in enumerate(available_lower):
                    if missing_lower in available or available in missing_lower:
                        suggestions.append(df.columns[i])
                
                if suggestions:
                    validation_result['suggestions'].append({
                        'missing': missing,
                        'suggestions': suggestions
                    })
        
        return validation_result
    
    def auto_detect_source_type(self, source: Union[str, Path]) -> str:
        """Detectar automaticamente o tipo de fonte"""
        source_str = str(source)
        
        if source_str.startswith(('http://', 'https://')):
            return 'api'
        elif source_str.startswith(('postgresql://', 'mysql://', 'sqlite://')):
            return 'sql'
        elif source_str.endswith('.csv'):
            return 'csv'
        elif source_str.endswith(('.xlsx', '.xls')):
            return 'excel'
        else:
            return 'unknown'
    
    def smart_ingest(self,
                     source: Union[str, Path],
                     source_type: Optional[str] = None,
                     **kwargs) -> pd.DataFrame:
        """Ingestão inteligente baseada no tipo de fonte"""
        
        if source_type is None:
            source_type = self.auto_detect_source_type(source)
        
        if source_type == 'csv':
            return self.read_csv(source, **kwargs)
        elif source_type == 'excel':
            return self.read_excel(source, **kwargs)
        elif source_type == 'sql':
            query = kwargs.pop('query', 'SELECT * FROM maintenance_data')
            return self.read_sql(query, str(source), **kwargs)
        elif source_type == 'api':
            return self.read_rest_api(str(source), **kwargs)
        else:
            raise Exception(f"Tipo de fonte não suportado: {source_type}")


# Configurações pré-definidas para sistemas comuns
SAP_CONFIG = {
    'maintenance_orders': {
        'endpoint': '/sap/opu/odata/sap/ZMM_MAINTENANCE_SRV/MaintenanceOrders',
        'required_fields': ['OrderNumber', 'Equipment', 'Component', 'Date', 'Hours']
    },
    'work_orders': {
        'endpoint': '/sap/opu/odata/sap/ZPM_WORKORDER_SRV/WorkOrders',
        'required_fields': ['WONumber', 'AssetID', 'Component', 'StartDate', 'EndDate']
    }
}

MAXIMO_CONFIG = {
    'workorders': {
        'endpoint': '/maximo/oslc/os/mxwo',
        'required_fields': ['wonum', 'assetnum', 'description', 'schedstart', 'actfinish']
    }
}

def create_sap_ingestor(base_url: str, client_id: str, client_secret: str):
    """Factory para criar ingestor SAP configurado"""
    # TODO: Implementar autenticação OAuth2 SAP
    pass

def create_sql_ingestor(connection_string: str):
    """Factory para criar ingestor SQL configurado"""
    ingestor = DataIngestor()
    
    # Testar conexão
    try:
        engine = sqlalchemy.create_engine(connection_string)
        with engine.connect() as conn:
            result = conn.execute(sqlalchemy.text("SELECT 1"))
        return ingestor
    except Exception as e:
        raise Exception(f"Falha ao conectar ao banco: {str(e)}")

# Queries SQL pré-definidas para sistemas comuns
COMMON_QUERIES = {
    'maintenance_history': """
        SELECT 
            equipment_id as asset_id,
            component_name as component,
            install_date,
            failure_date,
            operating_hours,
            maintenance_type,
            cost,
            downtime_hours
        FROM maintenance_history
        WHERE install_date >= '{start_date}'
    """,
    
    'work_orders': """
        SELECT 
            asset_number as asset_id,
            component_description as component,
            work_order_date as failure_date,
            meter_reading as operating_hours,
            work_type as maintenance_type,
            total_cost as cost
        FROM work_orders 
        WHERE status = 'COMPLETED'
    """
}