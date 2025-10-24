# 🚀 Quickstart - Weibull Fleet Analytics

## Instalação e Execução Rápida

### 1. Pré-requisitos
```bash
# Python 3.8+ requerido
python --version
```

### 2. Instalação
```bash
# Clonar/baixar o projeto
cd weibull-fleet-app

# Instalar dependências
pip install -r requirements.txt
```

### 3. Executar Aplicação
```bash
# Método 1: Script automático
python run_app.py

# Método 2: Streamlit direto
streamlit run app/Home.py

# A aplicação estará disponível em: http://localhost:8501
```

## 📋 Fluxo de Uso Recomendado

### Passo 1: Dados (🗂️)
1. Acesse a página "🗂️ Dados"
2. Carregue seus dados ou use "Dados de Exemplo"
3. Verifique se as colunas essenciais estão presentes:
   - `asset_id`: ID do equipamento
   - `component`: Nome do componente
   - `operating_hours`: Horas de operação

### Passo 2: Qualidade (🧼)
1. Vá para "🧼 Qualidade dos Dados"
2. Execute "Análise de Qualidade"
3. Aplique "Limpeza Automática" ou "IA Assistida"
4. Valide o dataset final

### Passo 3: Análise Weibull (📈)
1. Acesse "📈 Ajuste Weibull"
2. Selecione Frota → Subsistema → Componente
3. Execute "Análise Weibull"
4. Interprete os parâmetros β (forma) e η (escala)
5. Use "Análise IA" para explicações detalhadas

### Passo 4: Planejamento (🛠️)
1. Vá para "🛠️ Planejamento PM & Estoque"
2. Configure custos e parâmetros operacionais
3. Calcule "Estratégia Ótima" de manutenção
4. Otimize "Política de Estoque"
5. Analise diferentes "Cenários"

## 🎯 Exemplo Prático

### Dados de Exemplo Inclusos
O sistema vem com 500 registros de exemplo simulando:
- **Frotas**: CAT 777, CAT 785, Komatsu PC930, etc.
- **Componentes**: Motor, Transmissão, Bomba Hidráulica, etc.
- **Ambientes**: Diferentes condições operacionais
- **Censura**: ~20% dos dados são censurados

### Interpretação Típica
```
β = 2.1, η = 4500h para Bomba Hidráulica:

✅ β > 1: Falhas por desgaste (taxa crescente)
✅ η = 4500h: 63% falham até 4500 horas
✅ MTBF ≈ 4000h: Tempo médio até falha
➡️ Manutenção preventiva recomendada a cada 3000-3500h
```

## 🤖 Configuração da IA (Opcional)

### Para usar IA avançada:
1. Edite `.streamlit/secrets.toml`
2. Configure sua API key:
```toml
[ai]
model_provider = "openai"
openai_api_key = "sk-..."
```

### Funcionalidades IA:
- **Limpeza de Dados**: Normalização automática
- **Explicações**: Interpretação em linguagem simples
- **Recomendações**: Estratégias personalizadas
- **Relatórios**: Sumários executivos automáticos

## 📊 Formato de Dados

### Estrutura Mínima (CSV)
```csv
asset_id,component,operating_hours,failure_date
CAT777-001,Motor,8450,2023-08-20
CAT777-001,Transmissão,6200,
CAT785-002,Bomba Hidráulica,4850,2023-09-15
```

### Estrutura Completa
```csv
asset_id,component,fleet,subsystem,install_date,failure_date,operating_hours,censored,environment,cost
CAT777-001,Motor,CAT 777,Powertrain,2023-01-15,2023-08-20,8450,false,Mina A,25000
CAT777-001,Transmissão,CAT 777,Powertrain,2023-01-15,,6200,true,Mina A,
```

## 🔧 Solução de Problemas

### Erro: "Dados insuficientes"
- **Causa**: Menos de 3 falhas observadas
- **Solução**: Combine dados de componentes similares ou adicione mais histórico

### Erro: "Convergência falhou"
- **Causa**: Dados com muita variabilidade ou outliers
- **Solução**: Use limpeza automática na página "Qualidade dos Dados"

### IA não funciona
- **Causa**: API key não configurada
- **Solução**: Configure em `.streamlit/secrets.toml` ou use modo "local"

## 📈 Métricas de Sucesso

### Score de Qualidade > 80%
- Dados limpos e consistentes
- Poucos outliers e valores faltantes
- Pronto para análise confiável

### Convergência do Modelo
- `convergence: true` nos resultados
- AIC/BIC razoáveis
- Gráfico de probabilidade alinhado

### Intervalos Realistas
- PM entre 50-90% da vida característica
- Confiabilidade entre 70-90%
- ROI positivo da estratégia

## 🎨 Personalização

### Temas e Cores
- Edite CSS em `app/Home.py`
- Modifique paleta de cores nos gráficos
- Customize logotipos e branding

### Modelos Adicionais
- Adicione distribuições em `core/weibull.py`
- Implemente novos algoritmos de otimização
- Estenda funcionalidades de IA

### Integrações
- Configure conexões SQL em `dataops/ingest.py`
- Adicione APIs customizadas
- Implemente exportadores específicos

## 📞 Suporte

- **Documentação**: README.md completo
- **Exemplos**: Pasta `examples/` (se disponível)
- **Issues**: Use GitHub Issues para bugs
- **Melhorias**: Pull Requests são bem-vindos!

---
**Desenvolvido para otimizar manutenção industrial através de análise de confiabilidade e IA 🛠️📊🤖**