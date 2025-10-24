# 🔬 Detalhes Técnicos - Weibull Fleet Analytics

## 📊 Metodologia Estatística

### Distribuição Weibull
A análise usa a distribuição Weibull de dois parâmetros:

```
f(t) = (β/η) * (t/η)^(β-1) * exp(-(t/η)^β)
R(t) = exp(-(t/η)^β)
h(t) = (β/η) * (t/η)^(β-1)
```

Onde:
- **β**: Parâmetro de forma (caracteriza o tipo de falha)
- **η**: Parâmetro de escala (vida característica)
- **t**: Tempo (horas de operação)

### Maximum Likelihood Estimation (MLE)

#### Com Censura à Direita
Log-likelihood para dados censurados:

```
L(β,η) = Σ[log(f(ti))] + Σ[log(R(tj))]
```

Onde:
- `ti`: tempos de falha observados
- `tj`: tempos censurados

#### Implementação
```python
def neg_log_likelihood(params):
    beta, eta = params
    # Contribuição das falhas
    ll_failures = np.sum(np.log(beta/eta) + (beta-1)*np.log(failure_times/eta) - 
                         (failure_times/eta)**beta)
    # Contribuição dos censurados  
    ll_censored = -np.sum((censored_times/eta)**beta)
    return -(ll_failures + ll_censored)
```

### Intervalos de Confiança
Aproximação usando método delta e matriz de informação de Fisher:

```python
# Desvio padrão assintótico
beta_se = beta / sqrt(n_failures)
eta_se = eta / sqrt(n_failures)

# IC 95%
z_alpha = norm.ppf(0.975)
beta_ci = [beta - z_alpha * beta_se, beta + z_alpha * beta_se]
```

## 🛠️ Algoritmos de Otimização

### Manutenção Preventiva

#### 1. Meta de Confiabilidade
```python
# R(t) = target_reliability
# t = η * (-ln(R))^(1/β)
interval = eta * (-np.log(target_reliability))**(1/beta)
```

#### 2. Fração da Vida Característica
```python
# Típico: 70-80% de η
interval = eta * fraction_of_eta
reliability = exp(-(fraction_of_eta)**beta)
```

#### 3. Otimização por Custo
Minimizar taxa de custo esperado:

```python
def cost_rate(t):
    F_t = 1 - exp(-(t/eta)**beta)  # CDF
    expected_cost = cost_pm + cost_failure * F_t
    expected_time = t * exp(-(t/eta)**beta) + mtbf * F_t
    return expected_cost / expected_time
```

### Gestão de Estoque

#### Economic Order Quantity (EOQ)
```python
eoq = sqrt(2 * annual_demand * ordering_cost / (holding_rate * unit_cost))
```

#### Estoque de Segurança
```python
# Para nível de serviço desejado
z_score = norm.ppf(service_level)
safety_stock = z_score * sqrt(lead_time_demand_variance)
```

#### Ponto de Reposição
```python
reorder_point = lead_time_demand_mean + safety_stock
```

## 🤖 Arquitetura da IA

### Processamento de Linguagem Natural
```python
class WeibullAIAssistant:
    def explain_weibull_results(self, beta, eta, component, context):
        # Contextualizar parâmetros
        failure_type = self._interpret_beta(beta)
        
        # Gerar prompt estruturado
        prompt = f"""
        Componente: {component}
        Beta: {beta} ({failure_type})
        Eta: {eta} horas
        Contexto: {context}
        
        Explique em linguagem simples...
        """
        
        return self._call_llm(prompt)
```

### Normalização de Dados
```python
def normalize_component_names(self, df):
    # Regex patterns para componentes comuns
    patterns = {
        r'motor|engine': 'Motor',
        r'bomba.*hidr': 'Bomba Hidráulica',
        r'transmiss[aã]o': 'Transmissão'
    }
    
    for pattern, replacement in patterns.items():
        mask = df['component'].str.contains(pattern, case=False, regex=True)
        df.loc[mask, 'component'] = replacement
```

## 📊 Estrutura de Dados

### Schema Pydantic
```python
class FailureRecord(BaseModel):
    asset_id: str
    component: str
    operating_hours: float = Field(..., ge=0)
    censored: bool = False
    install_date: date
    failure_date: Optional[date] = None
    
    @validator('failure_date')
    def validate_failure_date(cls, v, values):
        if 'install_date' in values and v:
            if v < values['install_date']:
                raise ValueError('Failure date must be after install date')
        return v
```

### Validações Automáticas
```python
def validate_data_quality(self, df):
    issues = []
    
    # Verificar valores negativos
    if (df['operating_hours'] < 0).any():
        issues.append("Negative operating hours found")
    
    # Verificar consistência temporal
    invalid_dates = (df['failure_date'] < df['install_date']).sum()
    if invalid_dates > 0:
        issues.append(f"{invalid_dates} records with invalid date sequence")
    
    return issues
```

## 🎨 Interface Streamlit

### Multi-page Architecture
```python
# app/Home.py - Página principal
# app/1_🗂️_Dados.py - Upload e validação
# app/2_🧼_Qualidade_dos_Dados.py - Limpeza
# app/3_📈_Ajuste_Weibull.py - Análise principal
# app/4_🛠️_Planejamento_PM_Estoque.py - Otimização
```

### State Management
```python
# Session state para persistir dados entre páginas
if 'dataset' not in st.session_state:
    st.session_state.dataset = None

if 'weibull_results' not in st.session_state:
    st.session_state.weibull_results = {}
```

### Visualizações Interativas
```python
def create_probability_plot(self, times, censored):
    # Transformação para escala Weibull
    ln_times = np.log(failure_times)
    ln_ln_inv_reliability = np.log(-np.log(1 - prob_points))
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ln_times, y=ln_ln_inv_reliability,
        mode='markers', name='Data Points'
    ))
    
    # Linha de ajuste
    if self.fitted:
        x_line = np.linspace(ln_times.min(), ln_times.max(), 100)
        y_line = self.beta * (x_line - np.log(self.eta))
        fig.add_trace(go.Scatter(x=x_line, y=y_line, mode='lines'))
```

## 🔌 Integrações

### Conexões de Banco
```python
def read_sql(self, query, connection_string):
    engine = create_engine(connection_string)
    df = pd.read_sql(query, engine)
    return df

# Suporte para múltiplos SGBDs
SUPPORTED_DATABASES = {
    'postgresql': 'postgresql://user:pass@host:5432/db',
    'mysql': 'mysql://user:pass@host:3306/db',
    'sqlite': 'sqlite:///path/to/db.sqlite3'
}
```

### APIs REST
```python
def read_rest_api(self, endpoint, headers=None):
    response = requests.get(endpoint, headers=headers, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    return pd.DataFrame(data)
```

## 🧪 Testes Automatizados

### Validação de Algoritmos
```python
def test_weibull_fit():
    # Gerar dados sintéticos
    beta_true, eta_true = 2.0, 1000
    times = weibull_min.rvs(c=beta_true, scale=eta_true, size=100)
    
    # Ajustar modelo
    weibull = WeibullAnalysis()
    results = weibull.fit_mle(times)
    
    # Verificar convergência
    assert results['convergence'] == True
    assert abs(results['beta'] - beta_true) < 0.2
    assert abs(results['eta'] - eta_true) < 100
```

### Testes de Integração
```python
def test_full_pipeline():
    # Carregar dados
    df = pd.read_csv('test_data.csv')
    
    # Limpar dados
    cleaner = DataCleaner()
    df_clean, summary = cleaner.full_cleaning_pipeline(df)
    
    # Executar análise
    times = df_clean['operating_hours'].values
    weibull = WeibullAnalysis()
    results = weibull.fit_mle(times)
    
    assert results['convergence'] == True
```

## 🚀 Performance e Escalabilidade

### Otimizações
- **Vectorização NumPy**: Operações em lote para dados grandes
- **Caching**: Resultados de análise em `st.session_state`
- **Lazy Loading**: Carregamento sob demanda de módulos pesados

### Limites Práticos
- **Dataset Size**: Testado até 10,000 registros
- **Components**: Até 100 componentes únicos
- **Memory Usage**: ~100MB para dataset típico

### Escalabilidade Futura
- **Dask**: Para datasets > 100k registros
- **Redis**: Cache distribuído
- **PostgreSQL**: Persistência robusta
- **Docker**: Containerização

## 🔒 Segurança

### Validação de Entrada
```python
class SecureDataIngestor:
    def validate_file(self, file):
        # Verificar extensão
        allowed_extensions = ['.csv', '.xlsx']
        if not any(file.name.endswith(ext) for ext in allowed_extensions):
            raise ValueError("File type not allowed")
        
        # Verificar tamanho
        if file.size > 100 * 1024 * 1024:  # 100MB
            raise ValueError("File too large")
```

### Sanitização
```python
def sanitize_sql_query(self, query):
    # Remover comandos perigosos
    dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT']
    query_upper = query.upper()
    
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            raise ValueError(f"SQL command '{keyword}' not allowed")
    
    return query
```

---

Esta documentação técnica fornece insights profundos sobre a implementação, permitindo extensões e customizações avançadas do sistema.