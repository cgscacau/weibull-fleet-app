"""
Assistente de IA para análise Weibull e limpeza de dados
"""
import json
import requests
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from dataclasses import dataclass
import os
from scipy.special import gamma


@dataclass
class AIResponse:
    """Resposta padronizada do assistente de IA"""
    success: bool
    content: str
    data: Optional[Dict] = None
    confidence: Optional[float] = None
    suggestions: Optional[List[str]] = None


class WeibullAIAssistant:
    """Assistente de IA para análise Weibull e gestão de dados"""
    
    def __init__(self, model_provider: str = "local", api_key: Optional[str] = None):
        self.model_provider = model_provider
        self.api_key = api_key
        self.prompts_path = os.path.join(os.path.dirname(__file__), 'prompts')
        
    def load_prompt(self, prompt_name: str) -> str:
        """Carregar prompt de arquivo"""
        try:
            prompt_file = os.path.join(self.prompts_path, f"{prompt_name}.txt")
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return f"Prompt padrão para {prompt_name}"
    
    def _call_ai_model(self, prompt: str, context: str = "") -> AIResponse:
        """Chamar modelo de IA (implementação genérica)"""
        
        full_prompt = f"{prompt}\n\nContexto:\n{context}"
        
        if self.model_provider == "local":
            # Simulação de resposta local (para desenvolvimento)
            return self._mock_ai_response(prompt, context)
        
        elif self.model_provider == "openai":
            return self._call_openai(full_prompt)
        
        elif self.model_provider == "anthropic":
            return self._call_anthropic(full_prompt)
        
        else:
            return AIResponse(
                success=False, 
                content="Provedor de IA não suportado",
                confidence=0.0
            )
    
    def _mock_ai_response(self, prompt: str, context: str) -> AIResponse:
        """Resposta simulada para desenvolvimento/teste"""
        
        if "component" in prompt.lower() and "normalizar" in prompt.lower():
            return AIResponse(
                success=True,
                content="Sugestões de normalização aplicadas com base em padrões da indústria",
                data={
                    "normalized_components": {
                        "bomba hidr": "Bomba Hidráulica",
                        "motor diesel": "Motor",
                        "pneu dianteiro": "Pneu"
                    }
                },
                confidence=0.85,
                suggestions=[
                    "Considere criar categorias hierárquicas (Sistema > Subsistema > Componente)",
                    "Padronize códigos de fabricante",
                    "Implemente validação automática de novos componentes"
                ]
            )
        
        elif "weibull" in prompt.lower() and "explicar" in prompt.lower():
            return AIResponse(
                success=True,
                content="""
                **Análise da Distribuição Weibull:**
                
                Com β = 2.1, o componente apresenta comportamento de desgaste (β > 1), indicando que a taxa de falha aumenta com o tempo. 
                
                A vida característica η = 4500 horas sugere que aproximadamente 63% dos componentes falharão até 4500 horas de operação.
                
                **Recomendações:**
                - Manutenção preventiva recomendada a cada 3000-3500 horas (70-80% de η)
                - Monitorar tendências de deterioração
                - Considerar fatores ambientais que podem acelerar o desgaste
                """,
                confidence=0.92,
                suggestions=[
                    "Implementar manutenção preditiva com sensores",
                    "Analisar correlação com ambiente operacional",
                    "Comparar com benchmarks da indústria"
                ]
            )
        
        elif "relatório" in prompt.lower() or "sumário" in prompt.lower():
            return AIResponse(
                success=True,
                content="""
                ## Relatório Executivo - Análise de Confiabilidade
                
                ### Resumo dos Achados
                - **Componente Crítico**: Bomba Hidráulica apresenta maior risco
                - **Intervalo PM Recomendado**: 3200 horas (confiabilidade de 80%)
                - **Impacto Financeiro**: Redução estimada de 25% nos custos de manutenção
                
                ### Ações Prioritárias
                1. Implementar PM na Bomba Hidráulica
                2. Revisar estoque de peças críticas
                3. Treinar equipe em manutenção preditiva
                
                ### Próximos Passos
                - Validar resultados com dados históricos adicionais
                - Implementar sistema de monitoramento contínuo
                """,
                confidence=0.88
            )
        
        else:
            return AIResponse(
                success=True,
                content="Análise concluída. Verifique os resultados nos dados processados.",
                confidence=0.75
            )
    
    def _call_openai(self, prompt: str) -> AIResponse:
        """Chamar API OpenAI (implementação exemplo)"""
        if not self.api_key:
            return AIResponse(success=False, content="API key não configurada")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-4",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return AIResponse(success=True, content=content, confidence=0.9)
            else:
                return AIResponse(success=False, content=f"Erro API: {response.status_code}")
                
        except Exception as e:
            return AIResponse(success=False, content=f"Erro: {str(e)}")
    
    def _call_anthropic(self, prompt: str) -> AIResponse:
        """Chamar API Anthropic (implementação exemplo)"""
        # Implementação similar à OpenAI
        return AIResponse(success=False, content="Anthropic não implementado ainda")
    
    def suggest_data_cleaning(self, df: pd.DataFrame) -> AIResponse:
        """Sugerir limpeza de dados baseada no dataset"""
        
        # Análise básica do dataset
        data_summary = {
            "total_records": len(df),
            "columns": list(df.columns),
            "missing_data": df.isnull().sum().to_dict(),
            "data_types": df.dtypes.astype(str).to_dict(),
            "sample_values": {col: df[col].dropna().unique()[:5].tolist() 
                            for col in df.columns if df[col].dtype == 'object'}
        }
        
        prompt = self.load_prompt("clean_prompt")
        context = f"Análise do dataset:\n{json.dumps(data_summary, indent=2, default=str)}"
        
        return self._call_ai_model(prompt, context)
    
    def explain_weibull_results(self, beta: float, eta: float, 
                               component: str, context: Dict = None) -> AIResponse:
        """Explicar resultados da análise Weibull em linguagem simples"""
        
        prompt = self.load_prompt("explain_prompt")
        
        analysis_context = f"""
        Componente: {component}
        Parâmetros Weibull:
        - Beta (forma): {beta:.2f}
        - Eta (escala): {eta:.0f} horas
        - MTBF: {eta * gamma(1 + 1/beta):.0f} horas
        
        Contexto adicional: {json.dumps(context or {}, indent=2, default=str)}
        """
        
        return self._call_ai_model(prompt, analysis_context)
    
    def suggest_maintenance_strategy(self, weibull_params: Dict, 
                                   operational_context: Dict = None) -> AIResponse:
        """Sugerir estratégia de manutenção baseada nos parâmetros Weibull"""
        
        prompt = """
        Como especialista em confiabilidade, analise os parâmetros Weibull fornecidos e sugira uma estratégia de manutenção otimizada.
        
        Considere:
        1. Tipo de falha (baseado em beta)
        2. Intervalo ótimo de manutenção preventiva
        3. Nível de risco aceitável
        4. Impacto operacional e financeiro
        5. Estratégias de monitoramento
        
        Forneça recomendações práticas e justificativas técnicas.
        """
        
        context = f"""
        Parâmetros Weibull: {json.dumps(weibull_params, indent=2, default=str)}
        Contexto operacional: {json.dumps(operational_context or {}, indent=2, default=str)}
        """
        
        return self._call_ai_model(prompt, context)
    
    def generate_executive_summary(self, analysis_results: Dict, 
                                 business_context: Dict = None) -> AIResponse:
        """Gerar sumário executivo dos resultados"""
        
        prompt = self.load_prompt("exec_summary_prompt")
        
        context = f"""
        Resultados da análise: {json.dumps(analysis_results, indent=2, default=str)}
        Contexto do negócio: {json.dumps(business_context or {}, indent=2, default=str)}
        """
        
        return self._call_ai_model(prompt, context)
    
    def detect_anomalies(self, df: pd.DataFrame, component: str) -> AIResponse:
        """Detectar anomalias nos dados de um componente específico"""
        
        component_data = df[df['component'] == component] if 'component' in df.columns else df
        
        # Estatísticas básicas para detecção de anomalias
        stats = {
            "count": len(component_data),
            "mean_hours": component_data['operating_hours'].mean() if 'operating_hours' in component_data.columns else None,
            "std_hours": component_data['operating_hours'].std() if 'operating_hours' in component_data.columns else None,
            "min_hours": component_data['operating_hours'].min() if 'operating_hours' in component_data.columns else None,
            "max_hours": component_data['operating_hours'].max() if 'operating_hours' in component_data.columns else None,
            "censoring_rate": component_data['censored'].mean() if 'censored' in component_data.columns else None
        }
        
        prompt = """
        Analise as estatísticas do componente e identifique possíveis anomalias ou problemas nos dados.
        
        Verifique:
        1. Valores extremos (outliers)
        2. Padrões inconsistentes
        3. Taxa de censura anômala
        4. Possíveis erros de coleta
        
        Forneça recomendações para investigação adicional.
        """
        
        context = f"Componente: {component}\nEstatísticas: {json.dumps(stats, indent=2, default=str)}"
        
        return self._call_ai_model(prompt, context)
    
    def compare_components(self, comparison_results: Dict) -> AIResponse:
        """Comparar diferentes componentes e fornecer insights"""
        
        prompt = """
        Compare os componentes analisados e forneça insights sobre:
        
        1. Quais componentes são mais críticos
        2. Diferenças nos padrões de falha
        3. Oportunidades de padronização
        4. Prioridades de melhoria
        5. Benchmarking interno
        
        Forneça recomendações estratégicas baseadas na comparação.
        """
        
        context = json.dumps(comparison_results, indent=2, default=str)
        
        return self._call_ai_model(prompt, context)
    
    def validate_model_assumptions(self, data_summary: Dict, fit_results: Dict) -> AIResponse:
        """Validar se as suposições do modelo Weibull são adequadas"""
        
        prompt = """
        Como especialista em análise de confiabilidade, avalie se o modelo Weibull é apropriado para este dataset.
        
        Considere:
        1. Adequação da distribuição Weibull vs outras (exponencial, lognormal)
        2. Qualidade do ajuste
        3. Tamanho da amostra
        4. Taxa de censura
        5. Possíveis violações das suposições
        
        Recomende modelos alternativos se necessário.
        """
        
        context = f"""
        Resumo dos dados: {json.dumps(data_summary, indent=2, default=str)}
        Resultados do ajuste: {json.dumps(fit_results, indent=2, default=str)}
        """
        
        return self._call_ai_model(prompt, context)
