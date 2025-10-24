#!/usr/bin/env python3
"""
Script para executar a aplicação Weibull Fleet Analytics
"""
import subprocess
import sys
import os
from pathlib import Path

def check_dependencies():
    """Verificar se todas as dependências estão instaladas"""
    try:
        import streamlit
        import pandas
        import numpy
        import scipy
        import plotly
        print("✅ Dependências verificadas")
        return True
    except ImportError as e:
        print(f"❌ Dependência faltando: {e}")
        return False

def setup_environment():
    """Configurar ambiente"""
    # Adicionar diretório atual ao PYTHONPATH
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    
    # Verificar se dados de exemplo existem
    sample_data = current_dir / "storage" / "sample_fleet_data.csv"
    if not sample_data.exists():
        print("📊 Gerando dados de exemplo...")
        try:
            exec(open(current_dir / "storage" / "sample_data.py").read())
        except Exception as e:
            print(f"⚠️ Erro ao gerar dados de exemplo: {e}")
    
    print("✅ Ambiente configurado")

def run_streamlit():
    """Executar aplicação Streamlit"""
    app_path = Path(__file__).parent / "app" / "Home.py"
    
    cmd = [
        sys.executable, "-m", "streamlit", "run", str(app_path),
        "--server.port", "8501",
        "--server.address", "0.0.0.0",
        "--server.headless", "true",
        "--theme.base", "light"
    ]
    
    print("🚀 Iniciando Weibull Fleet Analytics...")
    print("📱 Acesse: http://localhost:8501")
    print("🛑 Pressione Ctrl+C para parar")
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n👋 Aplicação encerrada")

if __name__ == "__main__":
    print("🛠️ Weibull Fleet Analytics - Inicialização")
    print("=" * 50)
    
    if not check_dependencies():
        print("\n📦 Instale as dependências:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    
    setup_environment()
    run_streamlit()