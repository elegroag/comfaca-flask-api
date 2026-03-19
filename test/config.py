#!/usr/bin/env python3
"""
Configuración centralizada para tests usando variables de entorno.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env del directorio principal
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

class TestConfig:
    """Clase de configuración para tests."""
    
    # Configuración de API
    BASE_URL = os.getenv('BASE_URL', 'http://localhost:8080')
    API_USERNAME = os.getenv('API_USERNAME', 'admin')
    API_PASSWORD = os.getenv('API_PASSWORD', 'secretpassword')
    
    # Rutas de archivos
    JSON_TEST_PATH = os.getenv('JSON_TEST_PATH', 
                               str(Path(__file__).parent / 'test_consolidado_payload.json'))
    PDF_OUTPUT_DIR = os.getenv('PDF_OUTPUT_DIR', './test_output')
    
    # Configuración de logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    SHOW_REQUESTS = os.getenv('SHOW_REQUESTS', 'true').lower() == 'true'
    SHOW_RESPONSES = os.getenv('SHOW_RESPONSES', 'true').lower() == 'true'
    
    @classmethod
    def get_auth(cls):
        """Retorna la tupla de autenticación."""
        return (cls.API_USERNAME, cls.API_PASSWORD)
    
    @classmethod
    def ensure_output_dir(cls):
        """Asegura que el directorio de salida exista."""
        Path(cls.PDF_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def print_config(cls):
        """Imprime la configuración actual (sin passwords)."""
        print("🔧 Configuración de tests:")
        print(f"   🌐 Base URL: {cls.BASE_URL}")
        print(f"   👤 API User: {cls.API_USERNAME}")
        print(f"   📁 JSON Path: {cls.JSON_TEST_PATH}")
        print(f"   📁 Output Dir: {cls.PDF_OUTPUT_DIR}")
        print(f"   📊 Log Level: {cls.LOG_LEVEL}")
        print(f"   📝 Show Requests: {cls.SHOW_REQUESTS}")
        print(f"   📝 Show Responses: {cls.SHOW_RESPONSES}")

# Crear directorio de salida al importar
TestConfig.ensure_output_dir()
