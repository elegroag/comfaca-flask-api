#!/usr/bin/env python3
"""
Test específico para verificar el problema del valor_solicitud = 0 en el PDF.
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

def test_valor_solicitud():
    """Test específico para verificar el valor_solicitud en el PDF."""
    
    # Imprimir configuración
    TestConfig.print_config()
    
    print("\n🧪 Test específico para valor_solicitud")
    print("=" * 50)
    
    # Cargar el JSON de prueba
    try:
        with open(TestConfig.JSON_TEST_PATH, 'r') as f:
            test_data = json.load(f)
        
        valor_esperado = test_data.get('solicitud', {}).get('valor_solicitud')
        print(f"💰 Valor esperado en JSON: {valor_esperado}")
        print(f"📋 Solicitud ID: {test_data.get('solicitud_id')}")
        
    except Exception as e:
        print(f"❌ Error cargando JSON: {e}")
        return False
    
    # Test 1: Verificar el payload que se envía
    print("\n1. Verificando payload a enviar...")
    print(f"📦 solicitud.valor_solicitud: {test_data['solicitud']['valor_solicitud']}")
    print(f"📦 Tipo de dato: {type(test_data['solicitud']['valor_solicitud'])}")
    
    # Test 2: Enviar solicitud y verificar logs
    print("\n2. Enviando solicitud de generación...")
    
    if TestConfig.SHOW_REQUESTS:
        print(f"📤 Enviando a: {TestConfig.BASE_URL}/api/generate-pdf")
        print(f"🔐 Autenticación: {TestConfig.API_USERNAME}:***")
    
    response = requests.post(
        f"{TestConfig.BASE_URL}/api/generate-pdf",
        json=test_data,
        headers={'Content-Type': 'application/json'},
        auth=TestConfig.get_auth()
    )
    
    print(f"📊 Status: {response.status_code}")
    
    if TestConfig.SHOW_RESPONSES:
        try:
            response_data = response.json()
            print(f"📥 Response: {json.dumps(response_data, indent=2)}")
        except:
            print(f"📥 Response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ PDF generado: {data.get('api_filename')}")
        
        # Guardar PDF para inspección manual
        if data.get('api_content'):
            try:
                pdf_bytes = base64.b64decode(data['api_content'])
                filename = os.path.join(TestConfig.PDF_OUTPUT_DIR, 
                                      f"test_valor_solicitud_{test_data.get('solicitud_id')}.pdf")
                
                with open(filename, 'wb') as f:
                    f.write(pdf_bytes)
                print(f"💾 PDF guardado como: {filename}")
                print(f"📏 Tamaño: {len(pdf_bytes)} bytes")
                
                # Verificar que sea un PDF válido
                if pdf_bytes.startswith(b'%PDF'):
                    print("✅ PDF válido generado")
                else:
                    print("⚠️  El archivo no es un PDF válido")
                    
            except Exception as e:
                print(f"❌ Error guardando PDF: {e}")
                return False
    else:
        print(f"❌ Error en generación:")
        try:
            error_data = response.json()
            print(f"🔍 Detalles del error: {json.dumps(error_data, indent=2)}")
        except:
            print(f"🔍 Response: {response.text}")
        return False
    
    # Test 3: Probar con diferentes formatos de valor_solicitud
    print("\n3. Test con diferentes formatos de valor...")
    
    test_cases = [
        ("5000000.00", "String con decimales"),
        (5000000.00, "Float"),
        (5000000, "Integer"),
        ("5000000", "String sin decimales"),
    ]
    
    for valor, descripcion in test_cases:
        print(f"\n   📝 Test {descripcion}: {valor} ({type(valor).__name__})")
        
        test_case_data = test_data.copy()
        test_case_data['solicitud']['valor_solicitud'] = valor
        
        response = requests.post(
            f"{TestConfig.BASE_URL}/api/generate-pdf",
            json=test_case_data,
            headers={'Content-Type': 'application/json'},
            auth=TestConfig.get_auth()
        )
        
        if response.status_code == 200:
            print(f"   ✅ Generación exitosa")
            # Guardar con nombre distintivo para comparación manual
            data = response.json()
            if data.get('api_content'):
                try:
                    pdf_bytes = base64.b64decode(data['api_content'])
                    filename = os.path.join(TestConfig.PDF_OUTPUT_DIR, 
                                          f"test_valor_{str(valor).replace('.', '_')}.pdf")
                    with open(filename, 'wb') as f:
                        f.write(pdf_bytes)
                    print(f"   💾 Guardado como: {os.path.basename(filename)}")
                except:
                    print(f"   ⚠️  Error guardando PDF")
        else:
            print(f"   ❌ Falló: {response.status_code}")
    
    # Test 4: Verificación final
    print("\n4. Recomendaciones para depuración:")
    print("   🔍 Revisa los logs del servidor Flask para ver:")
    print("      - 'Payload recibido: ...'")
    print("      - 'Solicitud extraída: ...'")
    print("      - 'Valor de valor_solicitud: ...'")
    print("      - 'Convirtiendo valor a int: ...'")
    print("      - 'Conversión exitosa: ...'")
    
    print(f"\n🎯 Para verificar el valor en el PDF generado:")
    print(f"   1. Abre los PDF en: {TestConfig.PDF_OUTPUT_DIR}")
    print("   2. Busca el campo 'Valor Solicitud'")
    print("   3. Compara entre los diferentes test cases")
    
    print(f"\n� Todos los PDF guardados en: {TestConfig.PDF_OUTPUT_DIR}")
    
    return True

if __name__ == "__main__":
    success = test_valor_solicitud()
    sys.exit(0 if success else 1)
