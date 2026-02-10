#!/usr/bin/env python3
"""
Test script para el endpoint de descarga de PDF.
"""

import requests
import base64
import json

def test_download_pdf():
    """Test del endpoint /api/download-pdf"""
    base_url = "http://localhost:8080"
    
    print("🧪 Testeando endpoint /api/download-pdf")
    
    # Test 1: Sin parámetro filepath
    print("\n1. Test sin filepath...")
    response = requests.get(f"{base_url}/api/download-pdf")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 2: Path traversal attempt
    print("\n2. Test path traversal...")
    response = requests.get(f"{base_url}/api/download-pdf?filepath=../../../etc/passwd")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 3: Archivo no existente
    print("\n3. Test archivo no existente...")
    response = requests.get(f"{base_url}/api/download-pdf?filepath=no_existe.pdf")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 4: Archivo no PDF
    print("\n4. Test archivo no PDF...")
    response = requests.get(f"{base_url}/api/download-pdf?filepath=test.txt")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 5: Descarga exitosa (si existe un PDF)
    print("\n5. Test descarga exitosa...")
    response = requests.get(f"{base_url}/api/download-pdf?filepath=solicitud_TEST001.pdf")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data.get('success')}")
        print(f"Filename: {data.get('filename')}")
        print(f"Size: {data.get('size_bytes')} bytes")
        print(f"Base64 length: {len(data.get('base64_content', ''))}")
        
        # Opcional: Guardar el PDF decodificado
        if data.get('base64_content'):
            try:
                pdf_bytes = base64.b64decode(data['base64_content'])
                with open('downloaded_test.pdf', 'wb') as f:
                    f.write(pdf_bytes)
                print("PDF guardado como 'downloaded_test.pdf'")
            except Exception as e:
                print(f"Error al decodificar PDF: {e}")
    else:
        print(f"Response: {response.json()}")

if __name__ == "__main__":
    test_download_pdf()
