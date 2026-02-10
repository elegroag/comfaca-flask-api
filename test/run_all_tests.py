#!/usr/bin/env python3
"""
Script para ejecutar todos los tests de PDF generation.
"""

import subprocess
import sys
import os

def run_test(test_file, description):
    """Ejecuta un test específico y muestra el resultado."""
    print(f"\n{'='*60}")
    print(f"🧪 Ejecutando: {description}")
    print(f"📁 Archivo: {test_file}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, 
                              text=True, 
                              cwd=os.path.dirname(test_file))
        
        print(result.stdout)
        if result.stderr:
            print(f"⚠️  STDERR:\n{result.stderr}")
        
        if result.returncode == 0:
            print(f"✅ {description} - PASÓ")
        else:
            print(f"❌ {description} - FALLÓ (código: {result.returncode})")
            
    except Exception as e:
        print(f"❌ Error ejecutando {test_file}: {e}")
    
    return result.returncode == 0

def main():
    """Ejecuta todos los tests en orden."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    tests = [
        ("test_valor_solicitud.py", "Test específico para valor_solicitud"),
        ("test_generacion_pdf.py", "Test de generación de PDF con datos actualizados"),
        ("test_download_pdf_final.py", "Test completo de descarga de PDF"),
        ("test_download_pdf.py", "Test básico de descarga de PDF"),
    ]
    
    print("🚀 Iniciando suite de tests para generación de PDF")
    print(f"📂 Directorio: {base_dir}")
    
    results = []
    for test_file, description in tests:
        test_path = os.path.join(base_dir, test_file)
        if os.path.exists(test_path):
            success = run_test(test_path, description)
            results.append((test_file, description, success))
        else:
            print(f"⚠️  No se encuentra: {test_path}")
            results.append((test_file, description, False))
    
    # Resumen final
    print(f"\n{'='*60}")
    print("📊 RESUMEN DE TESTS")
    print(f"{'='*60}")
    
    passed = 0
    failed = 0
    
    for test_file, description, success in results:
        status = "✅ PASÓ" if success else "❌ FALLÓ"
        print(f"{status} - {description}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\n📈 Total: {passed + failed} tests")
    print(f"✅ Pasados: {passed}")
    print(f"❌ Fallidos: {failed}")
    
    if failed == 0:
        print("\n🎉 Todos los tests pasaron correctamente!")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) fallaron. Revisa los logs para más detalles.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
