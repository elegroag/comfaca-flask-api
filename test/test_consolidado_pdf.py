#!/usr/bin/env python3
"""
Test para el endpoint de consolidado de PDFs.
"""

import requests
import base64
import json
import os
import sys
from pathlib import Path

# Agregar el directorio de tests al path para importar config
sys.path.insert(0, str(Path(__file__).parent))
from config import TestConfig

def test_consolidado_pdf():
    """Test del endpoint de consolidado de PDF."""
    
    TestConfig.print_config()
    
    print("\n🧪 Test de consolidado de PDF")
    
    # Cargar el JSON de prueba
    try:
        with open(Path(__file__).parent / "test_consolidado_payload.json", 'r') as f:
            test_data = json.load(f)
        print(f"✅ JSON cargado: {test_data.get('templates')}")
    except FileNotFoundError:
        print(f"❌ Error: No se encuentra el archivo test_consolidado_payload.json")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Error decodificando JSON: {e}")
        return False
    
    # Test: Generación de PDF consolidado
    print("\n1. Test generación de PDF consolidado...")
    
    if TestConfig.SHOW_REQUESTS:
        print(f"📤 Enviando a: {TestConfig.BASE_URL}/api/genera-consolidado-pdf")
    
    response = requests.post(
        f"{TestConfig.BASE_URL}/api/genera-consolidado-pdf",
        json=test_data,
        headers={'Content-Type': 'application/json'},
        auth=TestConfig.get_auth()
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ PDF consolidado generado exitosamente")
        print(f"📄 Templates: {data.get('data', {}).get('templates')}")
        print(f"📏 Size bytes: {data.get('data', {}).get('size_bytes')}")
        print(f"📦 Base64 length: {len(data.get('data', {}).get('base64_content', ''))}")
        
        # Decodificar y guardar PDF
        b64_content = data.get('data', {}).get('base64_content')
        if b64_content:
            try:
                pdf_bytes = base64.b64decode(b64_content)
                filename = "consolidado_test.pdf"
                filepath = os.path.join(TestConfig.PDF_OUTPUT_DIR, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(pdf_bytes)
                print(f"💾 PDF guardado como '{filepath}'")
                print(f"📊 Tamaño del PDF: {len(pdf_bytes)} bytes")
                
                # Verificar que sea un PDF válido
                if pdf_bytes.startswith(b'%PDF'):
                    print("✅ El archivo generado es un PDF válido")
                else:
                    print("⚠️  El archivo no parece ser un PDF válido")
                    
                return True
                    
            except Exception as e:
                print(f"❌ Error al decodificar/guardar PDF: {e}")
                return False
        else:
            print("❌ No se recibió contenido base64")
            return False
    else:
        print(f"❌ Error en la generación:")
        try:
            error_data = response.json()
            print(f"Error: {error_data}")
        except:
            print(f"Response text: {response.text}")
        return False

if __name__ == "__main__":
    success = test_consolidado_pdf()
    sys.exit(0 if success else 1)
