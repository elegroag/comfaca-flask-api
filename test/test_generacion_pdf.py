#!/usr/bin/env python3
"""
Test para el endpoint de generación de PDF con datos actualizados.
Usa variables de entorno para configuración.
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

def test_generacion_pdf():
    """Test del endpoint de generación de PDF con el JSON actualizado."""
    
    # Imprimir configuración
    TestConfig.print_config()
    
    print("\n🧪 Test de generación de PDF con datos actualizados")
    
    # Cargar el JSON de prueba
    try:
        with open(TestConfig.JSON_TEST_PATH, 'r') as f:
            test_data = json.load(f)
        print(f"✅ JSON cargado desde: {TestConfig.JSON_TEST_PATH}")
        print(f"📋 Solicitud ID: {test_data.get('solicitud_id')}")
        print(f"💰 Valor solicitud: {test_data.get('solicitud', {}).get('valor_solicitud')}")
        
    except FileNotFoundError:
        print(f"❌ Error: No se encuentra el archivo {TestConfig.JSON_TEST_PATH}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Error decodificando JSON: {e}")
        return False
    
    # Test 1: Generación de PDF sin autenticación
    print("\n1. Test generación sin autenticación...")
    
    if TestConfig.SHOW_REQUESTS:
        print(f"📤 Enviando a: {TestConfig.BASE_URL}/api/generate-pdf (sin auth)")
    
    response = requests.post(
        f"{TestConfig.BASE_URL}/api/generate-pdf",
        json=test_data,
        headers={'Content-Type': 'application/json'}
    )
    print(f"Status: {response.status_code}")
    
    if TestConfig.SHOW_RESPONSES:
        try:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Response: {response.text}")
    
    # Test 2: Generación de PDF con autenticación
    print("\n2. Test generación con autenticación...")
    
    if TestConfig.SHOW_REQUESTS:
        print(f"📤 Enviando a: {TestConfig.BASE_URL}/api/generate-pdf")
        print(f"🔐 Autenticación: {TestConfig.API_USERNAME}:***")
    
    response = requests.post(
        f"{TestConfig.BASE_URL}/api/generate-pdf",
        json=test_data,
        headers={'Content-Type': 'application/json'},
        auth=TestConfig.get_auth()
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ PDF generado exitosamente")
        print(f"📄 Filename: {data.get('api_filename')}")
        print(f"📏 Path: {data.get('api_path')}")
        print(f"📦 Base64 length: {len(data.get('api_content', ''))}")
        
        # Decodificar y guardar PDF
        if data.get('api_content'):
            try:
                pdf_bytes = base64.b64decode(data['api_content'])
                filename = data.get('api_filename', 'generated_test.pdf')
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
    
    # Test 3: Verificación del valor_solicitud en el PDF generado
    print("\n3. Test verificación del valor_solicitud...")
    
    # Buscar si hay un PDF generado para descargar
    if response.status_code == 200 and data.get('api_path'):
        pdf_path = os.path.basename(data.get('api_path'))
        print(f"🔍 Intentando descargar PDF: {pdf_path}")
        
        download_response = requests.get(
            f"{TestConfig.BASE_URL}/api/download-pdf",
            params={'filepath': pdf_path},
            auth=TestConfig.get_auth()
        )
        
        if download_response.status_code == 200:
            download_data = download_response.json()
            if download_data.get('base64_content'):
                print("✅ PDF descargado exitosamente para verificación")
                print("📝 NOTA: Para verificar el valor_solicitud en el PDF,")
                print("   necesitaríamos una librería como PyPDF2 o pdfplumber")
            else:
                print("❌ No se pudo obtener contenido del PDF para verificación")
        else:
            print(f"❌ Error descargando PDF: {download_response.status_code}")
    
    # Test 4: Test con datos inválidos
    print("\n4. Test con datos inválidos...")
    invalid_data = {"solicitud_id": "test", "solicitud": {}}
    
    response = requests.post(
        f"{TestConfig.BASE_URL}/api/generate-pdf",
        json=invalid_data,
        headers={'Content-Type': 'application/json'},
        auth=TestConfig.get_auth()
    )
    print(f"Status: {response.status_code}")
    
    if TestConfig.SHOW_RESPONSES:
        try:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Response: {response.text}")
    
    print(f"\n🎉 Test completado")
    print(f"📂 PDFs guardados en: {TestConfig.PDF_OUTPUT_DIR}")
    
    return True

if __name__ == "__main__":
    success = test_generacion_pdf()
    sys.exit(0 if success else 1)
