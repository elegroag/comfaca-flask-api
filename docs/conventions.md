# Convenciones de Código

## Estilo General

- **Python 3.x** con type hints opcionales pero recomendados
- **PEP 8** como guía de estilo base
- **4 espacios** para indentación (no tabs)

## Convenciones de Nombres

| Tipo | Convención | Ejemplo |
|---|---|---|
| Clases | PascalCase | `CreditosGeneratorService` |
| Funciones/methods | snake_case | `generar_pdf`, `_validar_estructura_solicitud` |
| Variables | snake_case | `solicitud_id`, `pdf_content` |
| Constantes | UPPER_SNAKE | `LOG_LEVEL`, `API_TIMEOUT` |
| Files/modules | snake_case | `generate_pdf_service.py` |
| Templates Jinja2 | kebab-case + .html.j2 | `formato-credito-front.html.j2` |

## Patrones de Diseño

### Service Layer Pattern

Los servicios encapsulan la lógica de negocio:
- `GeneratePdfService`: generación genérica de PDFs
- `CreditosGeneratorService`: lógica específica de créditos

### Silent Undefined (Jinja2)

Se usa una clase `SilentUndefined` personalizada para que las variables faltantes en templates no exploten sino que retornen string vacío.

### Normalización de Datos

El `CreditosGeneratorService._preparar_contexto()` normaliza datos del JSON de entrada:
- Renombra campos con nombres alternativos
- Convierte estructuras (dict→lista con campo `tipo`)
- Limpia datos antes de pasar al template

## Validación

- Validación temprana: `_validar_estructura_solicitud()` y `_validar_contexto_template()` lanzan `ValueError` o `ValidationError` con mensajes descriptivos.
- Logging de advertencias para campos opcionales faltantes.

## Filtros Jinja2 Personalizados

| Filtro | Uso | Descripción |
|---|---|---|
| `\|currency` | `{{ valor\|currency }}` | Formatea como `$ 1.500.000` |
| `\|format_date` | `{{ fecha\|format_date }}` | Formatea fecha ISO a `dd/mm/YYYY` |
| `\|format_document` | `{{ doc\|format_document }}` | Formatea documento con puntos |

## Manejo de Errores

```python
try:
    # operación
except ValueError as e:
    # error de validación → 400
    return jsonify({"error": str(e)}), 400
except RuntimeError as e:
    # error de runtime → 500
    return jsonify({"error": str(e)}), 500
except Exception as e:
    # error inesperado → 500 con logging
    logger.exception("Error inesperado")
    return jsonify({"error": f"Error inesperado: {e}"}), 500
```

## Path Traversal Prevention

Siempre usar `Path().name` para extraer solo el nombre de archivo y validar contra path traversal:
```python
safe_filepath = Path(filepath).name
if safe_filepath != filepath or '/' in filepath:
    return jsonify({"error": "Path inválido"}), 400
```

## Logging

Usar `logging.getLogger(__name__)` con el patrón:
```python
logger = logging.getLogger(__name__)
logger.info("Mensaje", extra={"key": "value"})
logger.warning("Advertencia", extra={"key": "value"})
logger.error("Error", extra={"key": "value"})
logger.exception("Error con traceback")
```

## Estructura de Respuesta JSON

Éxito:
```json
{
  "success": true,
  "message": "Descripción del resultado",
  "data": { ... }
}
```

Error:
```json
{
  "success": false,
  "error": "Mensaje descriptivo del error"
}
```