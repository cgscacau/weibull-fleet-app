"""
Schemas de validação para dados de confiabilidade usando Pydantic
"""
from datetime import datetime, date
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, validator
import pandas as pd


class FailureRecord(BaseModel):
    """Schema para registro individual de falha/manutenção"""
    asset_id: str = Field(..., description="ID único do ativo")
    component: str = Field(..., description="Nome do componente")
    subsystem: Optional[str] = Field(None, description="Subsistema do equipamento")
    fleet: Optional[str] = Field(None, description="Frota ou modelo do equipamento")
    install_date: date = Field(..., description="Data de instalação do componente")
    failure_date: Optional[date] = Field(None, description="Data da falha (None se censurado)")
    operating_hours: float = Field(..., ge=0, description="Horas de operação até falha/censura")
    censored: bool = Field(default=False, description="Se verdadeiro, item foi censurado (sem falha)")
    failure_mode: Optional[str] = Field(None, description="Modo de falha específico")
    environment: Optional[str] = Field(None, description="Ambiente operacional")
    operator: Optional[str] = Field(None, description="Operador responsável")
    maintenance_type: Optional[Literal["preventiva", "corretiva", "preditiva"]] = Field(None)
    cost: Optional[float] = Field(None, ge=0, description="Custo da manutenção")
    downtime_hours: Optional[float] = Field(None, ge=0, description="Horas de parada")
    
    @validator('failure_date')
    def validate_failure_date(cls, v, values):
        if 'install_date' in values and v is not None:
            if v < values['install_date']:
                raise ValueError('Data de falha deve ser posterior à instalação')
        return v
    
    @validator('censored')
    def validate_censored_consistency(cls, v, values):
        if v and 'failure_date' in values and values['failure_date'] is not None:
            raise ValueError('Item censurado não pode ter data de falha')
        if not v and 'failure_date' in values and values['failure_date'] is None:
            raise ValueError('Item não censurado deve ter data de falha')
        return v


class FleetDataset(BaseModel):
    """Schema para dataset completo de frota"""
    records: List[FailureRecord]
    dataset_name: str = Field(..., description="Nome do dataset")
    created_at: datetime = Field(default_factory=datetime.now)
    data_source: Optional[str] = Field(None, description="Fonte dos dados (SAP, Excel, etc.)")
    quality_score: Optional[float] = Field(None, ge=0, le=1, description="Score de qualidade dos dados")
    
    @validator('records')
    def validate_non_empty(cls, v):
        if len(v) == 0:
            raise ValueError('Dataset não pode estar vazio')
        return v
    
    def to_dataframe(self) -> pd.DataFrame:
        """Converte para DataFrame pandas"""
        data = []
        for record in self.records:
            data.append(record.dict())
        return pd.DataFrame(data)
    
    @classmethod
    def from_dataframe(cls, df: pd.DataFrame, dataset_name: str = "Imported Dataset"):
        """Cria FleetDataset a partir de DataFrame"""
        records = []
        for _, row in df.iterrows():
            record_data = row.to_dict()
            # Converter datas se necessário
            for date_col in ['install_date', 'failure_date']:
                if date_col in record_data and pd.notna(record_data[date_col]):
                    if isinstance(record_data[date_col], str):
                        record_data[date_col] = pd.to_datetime(record_data[date_col]).date()
                    elif hasattr(record_data[date_col], 'date'):
                        record_data[date_col] = record_data[date_col].date()
                else:
                    record_data[date_col] = None
            
            # Inferir censura se não especificado
            if 'censored' not in record_data:
                record_data['censored'] = pd.isna(record_data.get('failure_date'))
            
            records.append(FailureRecord(**record_data))
        
        return cls(records=records, dataset_name=dataset_name)


class WeibullParameters(BaseModel):
    """Parâmetros ajustados da distribuição Weibull"""
    component: str
    fleet: Optional[str] = None
    beta: float = Field(..., gt=0, description="Parâmetro de forma")
    eta: float = Field(..., gt=0, description="Parâmetro de escala (vida característica)")
    beta_ci_lower: Optional[float] = None
    beta_ci_upper: Optional[float] = None
    eta_ci_lower: Optional[float] = None
    eta_ci_upper: Optional[float] = None
    log_likelihood: Optional[float] = None
    aic: Optional[float] = None
    bic: Optional[float] = None
    sample_size: int = Field(..., gt=0)
    censoring_rate: float = Field(..., ge=0, le=1)
    fit_date: datetime = Field(default_factory=datetime.now)
    goodness_of_fit: Optional[float] = Field(None, description="P-value do teste de ajuste")
    
    @property
    def mtbf(self) -> float:
        """Tempo médio até falha"""
        import math
        from scipy.special import gamma
        return self.eta * gamma(1 + 1/self.beta)
    
    @property
    def reliability_at_mtbf(self) -> float:
        """Confiabilidade no MTBF"""
        import math
        return math.exp(-1)  # ≈ 0.368


class MaintenanceRecommendation(BaseModel):
    """Recomendação de manutenção baseada em análise Weibull"""
    component: str
    recommended_interval: float = Field(..., gt=0, description="Intervalo recomendado em horas")
    confidence_level: float = Field(default=0.8, ge=0, le=1)
    reliability_at_interval: float = Field(..., ge=0, le=1)
    risk_assessment: Literal["baixo", "médio", "alto"]
    cost_impact: Optional[str] = None
    reasoning: str = Field(..., description="Justificativa da recomendação")
    
    @validator('risk_assessment')
    def assess_risk(cls, v, values):
        if 'reliability_at_interval' in values:
            rel = values['reliability_at_interval']
            if rel >= 0.9:
                return "baixo"
            elif rel >= 0.7:
                return "médio"
            else:
                return "alto"
        return v