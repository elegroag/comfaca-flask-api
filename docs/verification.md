# Verificación del Proyecto

## Pruebas Disponibles

Ubicación: `app/test/`

### Archivos de Test

| Archivo | Descripción |
|---|---|
| `run_all_tests.py` | Runner centralizado para todos los tests |
| `test_generacion_pdf.py` | Tests de generación de PDFs |
| `test_valor_solicitud.py` | Tests específicos para valor_solicitud |
| `test_consolidado_pdf.py` | Tests de PDFs consolidados |
| `test_download_pdf.py` | Tests de descarga de PDFs |
| `test_download_pdf_final.py` | Tests de descarga final |

## Ejecutar Pruebas

```bash
# Desde el directorio app/
cd app

# Opción 1: Usar el runner centralizado
python test/run_all_tests.py

# Opción 2: Ejecutar pytest directamente
pytest test/ -v

# Opción 3: Ejecutar un test específico
pytest test/test_generacion_pdf.py -v
```

## Requisitos para Pruebas

```bash
pip install -r test/requirements.txt
```

## Configuración de Tests

`test/config.py` carga variables desde `.env` del proyecto y expone:
- `TestConfig.BASE_URL`: URL base de la API
- `TestConfig.get_auth()`: Tupla (username, password)
- `TestConfig.ensure_output_dir()`: Crea directorio de salida

## Verificación Manual (sin tests)

### Levantar la API

```bash
cd app
python app.py
```

### Health check

```bash
curl http://localhost:8080/api/health
```

### Generar PDF de prueba

```bash
curl -X POST http://localhost:8080/api/creditos/generate-pdf \
  -H "Content-Type: application/json" \
  -u admin:secretpassword \
  -d '{
    "solicitud_id": "TEST-001",
    "solicitud": {
      "numero_solicitud": "TEST-001",
      "valor_solicitud": 5000000,
      "plazo_meses": 12
    },
    "solicitante": {
      "tipo_documento": "CC",
      "numero_documento": "12345678",
      "nombre_completo": "Juan Pérez García"
    }
  }'
```

## Criterios de Éxito

- ✅ Todos los tests pasan
- ✅ La API responde en `/api/health`
- ✅ La generación de PDFs de créditos funciona
- ✅ No hay errores de sintaxis en el código