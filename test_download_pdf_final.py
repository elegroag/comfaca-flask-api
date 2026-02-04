#!/usr/bin/env python3
"""
Test final del endpoint /api/download-pdf con autenticación.
"""

import requests
import base64
import json

def test_download_pdf_complete():
    """Test completo del endpoint con autenticación."""
    base_url = "http://localhost:8080"
    auth = ('admin', 'secretpassword')
    
    print("🧪 Test completo endpoint /api/download-pdf")
    print(f"🔐 Usando autenticación: {auth[0]}:***")
    
    # Test 1: Sin parámetro filepath
    print("\n1. Test sin filepath...")
    response = requests.get(f"{base_url}/api/download-pdf", auth=auth)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 2: Path traversal attempt
    print("\n2. Test path traversal...")
    response = requests.get(f"{base_url}/api/download-pdf?filepath=../../../etc/passwd", auth=auth)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 3: Archivo no existente
    print("\n3. Test archivo no existente...")
    response = requests.get(f"{base_url}/api/download-pdf?filepath=no_existe.pdf", auth=auth)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 4: Archivo no PDF
    print("\n4. Test archivo no PDF...")
    response = requests.get(f"{base_url}/api/download-pdf?filepath=test.txt", auth=auth)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 5: Descarga exitosa
    print("\n5. Test descarga exitosa...")
    response = requests.get(f"{base_url}/api/download-pdf?filepath=test.pdf", auth=auth)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success: {data.get('success')}")
        print(f"📄 Filename: {data.get('filename')}")
        print(f"📏 Size: {data.get('size_bytes')} bytes")
        print(f"📦 Base64 length: {len(data.get('base64_content', ''))}")
        
        # Decodificar y guardar PDF
        if data.get('base64_content'):
            try:
                pdf_bytes = base64.b64decode(data['base64_content'])
                with open('downloaded_final_test.pdf', 'wb') as f:
                    f.write(pdf_bytes)
                print("💾 PDF guardado como 'downloaded_final_test.pdf'")
                print(f"📄 Contenido decodificado: {pdf_bytes.decode('utf-8', errors='ignore')}")
            except Exception as e:
                print(f"❌ Error al decodificar PDF: {e}")
    else:
        print(f"❌ Response: {response.json()}")
    
    # Test 6: Verificación de contenido base64
    print("\n6. Test verificación de contenido...")
    if response.status_code == 200:
        data = response.json()
        original_content = "Test PDF content\n"
        decoded_content = base64.b64decode(data['base64_content']).decode('utf-8')
        if decoded_content == original_content:
            print("✅ Contenido decodificado coincide con el original")
        else:
            print("❌ El contenido decodificado no coincide")
            print(f"Original: {repr(original_content)}")
            print(f"Decodificado: {repr(decoded_content)}")

if __name__ == "__main__":
    test_download_pdf_complete()
