# 🔧 Troubleshooting - Weibull Fleet Analytics

## ❌ Problema: "Botões não funcionam"

### Sintomas
- Tela carrega corretamente
- Você vê o título e conteúdo
- Mas ao clicar em botões, nada acontece
- Páginas não navegam

### 🎯 Causas Possíveis e Soluções

---

## Solução 1: Estrutura de Páginas Incorreta

### Problema
Streamlit busca páginas multipage na pasta `/pages` (na raiz), não em `/app`.

### ✅ Solução
```bash
# Certifique-se de que as páginas estão em /pages
weibull-fleet-app/
├── Home.py              ← Página principal
└── pages/               ← Páginas multipage AQUI
    ├── 0_🧪_Teste.py
    ├── 1_🗂️_Dados.py
    ├── 2_🧼_Qualidade_dos_Dados.py
    ├── 3_📈_Ajuste_Weibull.py
    └── 4_🛠️_Planejamento_PM_Estoque.py
```

### Como Corrigir
1. Copie as páginas de `/app` para `/pages`
2. Faça commit e push
3. Aguarde redeploy

```bash
cp app/*.py pages/
git add pages/
git commit -m "Add pages to correct location"
git push
```

---

## Solução 2: Cache do Navegador

### Problema
Navegador está mostrando versão antiga do app.

### ✅ Solução
1. Pressione **Ctrl + Shift + R** (ou **Cmd + Shift + R** no Mac)
2. Ou limpe o cache do navegador
3. Ou abra em janela anônima

---

## Solução 3: Session State não Inicializado

### Problema
Botões que dependem de `st.session_state` podem não funcionar se não inicializados.

### ✅ Solução
Verifique se cada página inicializa o session_state:

```python
# No início de cada página
if 'dataset' not in st.session_state:
    st.session_state.dataset = None

if 'weibull_results' not in st.session_state:
    st.session_state.weibull_results = {}
```

---

## Solução 4: Erros Silenciosos de Import

### Problema
Módulos não são encontrados, causando falha silenciosa.

### ✅ Solução
Adicione tratamento de erro explícito:

```python
import sys
from pathlib import Path

# Adicionar raiz ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from core.weibull import WeibullAnalysis
except ImportError as e:
    st.error(f"Erro ao importar módulo: {e}")
    st.stop()
```

---

## Solução 5: Testar com Página de Diagnóstico

### Use a página de teste
1. Acesse a página **"🧪 Teste"** no menu lateral
2. Verifique se todos os módulos carregam
3. Teste se botões funcionam nesta página
4. Se funcionar aqui, o problema é específico de outra página

---

## 🔍 Diagnóstico Passo a Passo

### 1. Verifique o Menu Lateral

**O que você deve ver:**
- Seta (>) no canto superior esquerdo
- Menu com páginas:
  - 🧪 Teste
  - 🗂️ Dados
  - 🧼 Qualidade dos Dados
  - 📈 Ajuste Weibull
  - 🛠️ Planejamento PM Estoque

**Se não aparecer:**
- ❌ Páginas não estão em `/pages`
- ✅ Mova para `/pages` e faça redeploy

### 2. Teste a Página de Teste

1. Clique em **"🧪 Teste"** no menu
2. Clique no botão **"🎯 Clique Aqui para Testar"**
3. Digite algo no campo de texto
4. Mova o slider

**Se funcionar:**
- ✅ Streamlit está OK
- ✅ Problema é nas outras páginas

**Se não funcionar:**
- ❌ Problema no Streamlit Cloud
- ✅ Faça "Reboot app" no dashboard

### 3. Verifique os Logs

No Streamlit Cloud:
1. Clique em **"Manage app"**
2. Veja os **logs** em tempo real
3. Procure por erros em vermelho

**Erros Comuns:**
```
ModuleNotFoundError: No module named 'core'
→ Solução: Adicione sys.path no início da página

FileNotFoundError: sample_fleet_data.csv
→ Solução: Verifique se storage/ está no GitHub

AttributeError: 'NoneType' object...
→ Solução: Inicialize session_state
```

---

## 🎯 Testes Específicos por Tipo de Botão

### Botão "Carregar Dados de Exemplo"

**Problema:** Não carrega dados

**Verificar:**
```python
# A página 1_🗂️_Dados.py tem isso?
if st.button("🔄 Carregar Dados de Exemplo"):
    sample_data = load_sample_data()  # Esta função existe?
    if sample_data is not None:
        st.session_state.dataset = sample_data  # Session state inicializado?
```

**Solução:**
1. Certifique-se que `storage/sample_fleet_data.csv` existe
2. Inicialize `st.session_state.dataset = None` no topo
3. Adicione try/except com mensagem de erro

### Botão "Executar Análise Weibull"

**Problema:** Não executa análise

**Verificar:**
- Dados foram carregados primeiro? (`st.session_state.dataset`)
- Filtros selecionados? (frota, componente)
- Módulo WeibullAnalysis importado corretamente?

**Solução:**
```python
# Adicionar validações
if st.button("📈 Executar Análise"):
    if st.session_state.dataset is None:
        st.error("❌ Carregue os dados primeiro!")
        st.stop()
    
    # Resto do código...
```

---

## 🚀 Solução Rápida Universal

Se nada funciona, use esta versão simplificada do Home.py:

```python
import streamlit as st

st.title("🛠️ Weibull Fleet Analytics")

st.success("✅ Sistema funcionando!")

if st.button("🎯 Teste de Botão"):
    st.balloons()
    st.success("Botão funcionou!")

st.info("""
📋 Próximos passos:
1. Navegue usando o menu lateral (seta >)
2. Comece pela página "🗂️ Dados"
3. Carregue dados de exemplo
""")
```

Salve, faça push e teste. Se este funcionar, o problema é em páginas específicas.

---

## 📞 Ainda com Problemas?

### Compartilhe estas informações:

1. **URL do app:** `seu-app.streamlit.app`

2. **O que você vê:**
   - [ ] Menu lateral aparece?
   - [ ] Páginas aparecem no menu?
   - [ ] Consegue navegar entre páginas?
   - [ ] Botões mudam de cor ao clicar?

3. **Qual página não funciona:**
   - [ ] Home
   - [ ] Dados
   - [ ] Qualidade
   - [ ] Weibull
   - [ ] Planejamento

4. **Logs do Streamlit Cloud:**
   - Copie as últimas 20 linhas dos logs

5. **Screenshot:**
   - Da tela principal
   - Do menu lateral aberto

---

## ✅ Checklist de Solução

Marque conforme resolve:

- [ ] Páginas estão em `/pages` (não `/app`)
- [ ] Fez git push com páginas
- [ ] Limpou cache do navegador (Ctrl+Shift+R)
- [ ] Menu lateral aparece (seta >)
- [ ] Página de teste funciona
- [ ] Session state inicializado em cada página
- [ ] Sem erros nos logs do Streamlit Cloud
- [ ] Dados de exemplo existem em `storage/`

---

## 🎉 Quando Funcionar

Você verá:
- ✅ Título "⚙️ Weibull Fleet Analytics"
- ✅ Cards coloridos com funcionalidades
- ✅ Menu lateral com 5 páginas
- ✅ Gráficos interativos
- ✅ Botões respondem ao clique
- ✅ Dados carregam e exibem

---

**Última atualização:** 2025-10-24  
**Versão:** 1.0.1
