# 🛠️ Weibull Fleet Analytics

Sistema avançado de análise de confiabilidade com IA assistiva para gestão de frotas industriais.

## 🚀 Visão Geral

O **Weibull Fleet Analytics** é uma aplicação completa que combina análise estatística robusta (distribuição Weibull) com inteligência artificial para otimizar estratégias de manutenção e gestão de estoque em frotas industriais.

### ✨ Principais Funcionalidades

- **📊 Análise Weibull Avançada**: Ajuste por MLE com tratamento de censura
- **🤖 IA Assistiva**: Limpeza automática de dados e explicações em linguagem simples
- **🛠️ Planejamento Inteligente**: Intervalos ótimos de manutenção preventiva
- **📦 Gestão de Estoque**: Políticas otimizadas de peças de reposição
- **📈 Visualizações Interativas**: Gráficos de probabilidade e curvas de confiabilidade
- **🔍 Análise Comparativa**: Benchmarking entre componentes e frotas

## 🏗️ Arquitetura

```
weibull-fleet-app/
├── app/                          # Interface Streamlit (multipage)
│   ├── Home.py                   # Página principal
│   ├── 1_🗂️_Dados.py           # Upload e gestão de dados
│   ├── 2_🧼_Qualidade_dos_Dados.py # Limpeza assistida por IA
│   ├── 3_📈_Ajuste_Weibull.py   # Análise Weibull principal
│   ├── 4_🛠️_Planejamento_PM_Estoque.py # Planejamento de manutenção
│   ├── 5_🔍_Comparativos.py     # Análises comparativas
│   └── 6_🧠_Relatório_IA.py     # Relatórios automáticos
├── core/                         # Módulos de análise
│   ├── weibull.py               # Análise Weibull e MLE
│   ├── censoring.py             # Tratamento de censura
│   ├── planner.py               # Planejamento de manutenção
│   └── compare.py               # Comparação de modelos
├── dataops/                      # Operações de dados
│   ├── ingest.py                # Ingestão de múltiplas fontes
│   ├── clean.py                 # Limpeza e padronização
│   ├── schemas.py               # Validação com Pydantic
│   └── validators.py            # Validadores específicos
├── ai/                          # Assistente de IA
│   ├── ai_assistant.py          # Interface principal da IA
│   └── prompts/                 # Prompts especializados
├── storage/                     # Persistência
│   ├── db.sqlite3              # Banco local
│   └── exports/                # Exports de relatórios
└── tests/                       # Testes automatizados
```

## 🔧 Instalação

### Pré-requisitos

- Python 3.8+
- pip ou conda

### Instalação Local

1. **Clone o repositório:**
```bash
git clone <repository-url>
cd weibull-fleet-app
```

2. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

3. **Configure as variáveis de ambiente:**
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edite o arquivo com suas configurações
```

4. **Execute a aplicação:**
```bash
streamlit run app/Home.py
```

### Deploy na Nuvem

#### Streamlit Cloud
1. Faça fork do repositório
2. Conecte ao Streamlit Cloud
3. Configure os secrets necessários
4. Deploy automático

#### Docker
```bash
docker build -t weibull-fleet-app .
docker run -p 8501:8501 weibull-fleet-app
```

## 📊 Fluxo de Uso

### 1. 📥 Carregamento de Dados
- Upload de CSV/Excel
- Conexão direta a SAP/SQL
- APIs de sistemas ERP
- Dados de exemplo inclusos

### 2. 🧼 Qualidade dos Dados
- Validação automática
- Limpeza assistida por IA
- Detecção de outliers
- Padronização de nomenclaturas

### 3. 📈 Análise Weibull
- Seleção por frota/componente
- Ajuste MLE com censura
- Gráficos de probabilidade
- Intervalos de confiança

### 4. 🛠️ Planejamento
- Intervalos ótimos de PM
- Análise de cenários
- Gestão de estoque
- ROI de estratégias

### 5. 🤖 Insights IA
- Explicações técnicas
- Recomendações estratégicas
- Relatórios executivos
- Análises comparativas

## 📋 Formato dos Dados

### Colunas Obrigatórias
- `asset_id`: ID único do equipamento
- `component`: Nome do componente
- `operating_hours`: Horas de operação até falha/censura

### Colunas Opcionais
- `install_date`: Data de instalação
- `failure_date`: Data da falha (null se censurado)
- `fleet`: Modelo/frota do equipamento
- `subsystem`: Subsistema do componente
- `censored`: Flag de censura (inferido automaticamente)
- `environment`: Ambiente operacional
- `operator`: Operador responsável
- `maintenance_type`: Tipo de manutenção
- `cost`: Custo da manutenção
- `downtime_hours`: Horas de parada

### Exemplo de Dataset
```csv
asset_id,component,fleet,install_date,failure_date,operating_hours,censored
CAT777-1001,Motor,CAT 777,2023-01-15,2023-08-20,8450,false
CAT777-1001,Transmissão,CAT 777,2023-01-15,,6200,true
CAT785-2001,Bomba Hidráulica,CAT 785,2022-12-10,2023-09-15,4850,false
```

## 🤖 Configuração da IA

### Provedores Suportados
- **OpenAI GPT-4**: Melhor qualidade, requer API key
- **Anthropic Claude**: Alternativa robusta
- **Modelos Locais**: Para ambientes restritos

### Configuração
```toml
# .streamlit/secrets.toml
[ai]
model_provider = "openai"  # "openai", "anthropic", "local"
openai_api_key = "sk-..."
model_name = "gpt-4"
```

### Funcionalidades IA
- **Limpeza de Dados**: Normalização automática de nomes
- **Explicações**: Interpretação de parâmetros Weibull
- **Estratégias**: Recomendações de manutenção
- **Relatórios**: Sumários executivos automáticos

## 📊 Exemplos de Análise

### Interpretação de Parâmetros Weibull

- **β < 1**: Falhas infantis (taxa decrescente)
  - Problemas de qualidade/instalação
  - Investigar fornecedores e processos

- **β ≈ 1**: Falhas aleatórias (taxa constante)
  - Manutenção por condição adequada
  - Focar em detecção precoce

- **β > 1**: Falhas por desgaste (taxa crescente)
  - Manutenção preventiva recomendada
  - Intervalos baseados em confiabilidade

### Estratégias de Manutenção

```python
# Exemplo de cálculo
planner = MaintenancePlanner(beta=2.1, eta=4500)

# Intervalo para 80% de confiabilidade
strategy = planner.optimal_pm_interval(
    policy="reliability_target",
    target_reliability=0.8
)

print(f"Intervalo recomendado: {strategy.recommended_interval:.0f}h")
print(f"Confiabilidade: {strategy.reliability_at_interval:.1%}")
```

## 🔒 Segurança e Governança

### Autenticação
- Sistema básico incluso
- Integração SSO disponível
- Controle de acesso por função

### Auditoria
- Log de todas as análises
- Trilha de modificações
- Backup automático de resultados

### Dados Sensíveis
- Criptografia em trânsito
- Anonimização opcional
- Compliance LGPD/GDPR

## 🧪 Testes

### Executar Testes
```bash
pytest tests/ -v
```

### Cobertura
```bash
pytest --cov=core --cov=dataops tests/
```

### Testes Inclusos
- Validação de ajuste Weibull
- Tratamento de censura
- Limpeza de dados
- Planejamento de manutenção

## 🚀 Roadmap

### v1.0 (Atual)
- ✅ MVP com funcionalidades core
- ✅ Interface Streamlit multipage
- ✅ Análise Weibull completa
- ✅ IA assistiva básica

### v1.1 (Próxima)
- 🔄 Integração SAP/Maximo
- 🔄 Análise de múltiplos componentes
- 🔄 Dashboard executivo
- 🔄 Exportação para PowerBI

### v2.0 (Futuro)
- 📋 Machine Learning avançado
- 📋 Análise preditiva
- 📋 IoT integration
- 📋 Mobile app

## 🤝 Contribuição

### Como Contribuir
1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

### Diretrizes
- Siga PEP 8 para Python
- Adicione testes para novas funcionalidades
- Documente APIs e mudanças importantes
- Use mensagens de commit descritivas

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 📞 Suporte

### Documentação
- [Wiki do Projeto](wiki/)
- [Exemplos de Uso](examples/)
- [FAQ](docs/faq.md)

### Contato
- Email: support@weibull-analytics.com
- Issues: [GitHub Issues](issues/)
- Discussões: [GitHub Discussions](discussions/)

## 🙏 Agradecimentos

- **SciPy**: Biblioteca fundamental para análise estatística
- **Streamlit**: Framework web para aplicações de dados
- **Plotly**: Visualizações interativas
- **Comunidade**: Contribuidores e usuários que tornam este projeto possível

---

**Desenvolvido com ❤️ para otimizar a manutenção industrial através da ciência de dados e IA.**