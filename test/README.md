# Tests de Generación de PDF

Este directorio contiene tests para el servicio de generación de PDF con configuración basada en variables de entorno.

## 🚀 Configuración Rápida

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

Las variables de entorno se cargan desde el archivo `.env` en el directorio principal del proyecto. Asegúrate que contenga:

```bash
# URL del servidor Flask
BASE_URL=http://localhost:8080

# Credenciales de API
API_USERNAME=admin
API_PASSWORD=tu_password

# Rutas de archivos
JSON_TEST_PATH=/home/elegro/proyectos/python/comfaca-credito/creadte-pdf-model.json
PDF_OUTPUT_DIR=./test/test_output

# Opciones de logging
LOG_LEVEL=INFO
SHOW_REQUESTS=true
SHOW_RESPONSES=true
```

### 3. Crear directorio de salida

```bash
mkdir -p test/test_output
```

## 🧪 Tests Disponibles

### `test_valor_solicitud.py`

**Propósito**: Diagnosticar específicamente el problema del `valor_solicitud = 0` en el PDF.

**Qué hace**:

- Prueba diferentes formatos de valor (string, float, int)
- Genera PDFs comparativos
- Muestra logging detallado del proceso

**Uso**:

```bash
python test_valor_solicitud.py
```

### `test_generacion_pdf.py`

**Propósito**: Test completo de la generación de PDF con la estructura actualizada.

**Qué hace**:

- Prueba con/sin autenticación
- Verifica la estructura del PDF generado
- Maneja errores de forma robusta

**Uso**:

```bash
python test_generacion_pdf.py
```

### `test_download_pdf_final.py`

**Propósito**: Test del endpoint de descarga de PDF.

**Qué hace**:

- Genera un PDF primero
- Prueba la descarga del PDF generado
- Verifica la integridad del archivo

**Uso**:

```bash
python test_download_pdf_final.py
```

### `run_all_tests.py`

**Propósito**: Ejecutar todos los tests en secuencia.

**Qué hace**:

- Ejecuta todos los tests disponibles
- Muestra un resumen de resultados
- Facilita la ejecución masiva

**Uso**:

```bash
python run_all_tests.py
```

## 📁 Estructura de Archivos

```
test/
├── config.py              # Configuración centralizada
├── requirements.txt       # Dependencias Python
├── README.md              # Este archivo
├── run_all_tests.py       # Ejecutor de todos los tests
├── test_valor_solicitud.py
├── test_generacion_pdf.py
├── test_download_pdf_final.py
├── test_download_pdf.py
└── test_output/           # Directorio para PDFs generados
```

## 🔍 Diagnóstico del Problema `valor_solicitud = 0`

### Paso 1: Ejecutar el test específico

```bash
python test_valor_solicitud.py
```

### Paso 2: Revisar los logs del servidor

Busca estos mensajes en los logs del servidor Flask:

- `Payload recibido: ...`
- `Solicitud extraída: ...`
- `Valor de valor_solicitud: ...`
- `Convirtiendo valor a int: ...`
- `Conversión exitosa: ...`

### Paso 3: Comparar PDFs generados

El test genera múltiples PDFs en `test_output/`:

- `test_valor_5000000_00.pdf` (string con decimales)
- `test_valor_5000000_0.pdf` (float)
- `test_valor_5000000.pdf` (integer)
- `test_valor_5000000_str.pdf` (string sin decimales)

### Paso 4: Verificar manualmente

Abre los PDFs y busca el campo "Valor Solicitud" para ver cuál muestra el valor correcto.

## 🛠️ Personalización

### Cambiar la URL del servidor

Edita el archivo `.env` en el directorio principal:

```bash
BASE_URL=http://tu-servidor:puerto
```

### Cambiar credenciales

Edita el archivo `.env` en el directorio principal:

```bash
API_USERNAME=tu_usuario
API_PASSWORD=tu_password
```

### Cambiar archivo JSON de prueba

Edita el archivo `.env` en el directorio principal:

```bash
JSON_TEST_PATH=/ruta/a/tu/json_prueba.json
```

### Habilitar/deshabilitar logging detallado

Edita el archivo `.env` en el directorio principal:

```bash
SHOW_REQUESTS=false
SHOW_RESPONSES=false
```

## 🐛 Solución de Problemas Comunes

### "No se encuentra el archivo JSON"

- Verifica que la ruta en `JSON_TEST_PATH` sea correcta
- Asegúrate que el archivo `creadte-pdf-model.json` exista

### "Error de conexión"

- Verifica que el servidor Flask esté corriendo
- Confirma que `BASE_URL` sea correcta

### "Error de autenticación"

- Verifica las credenciales en `API_USERNAME` y `API_PASSWORD`
- Asegúrate que el usuario tenga permisos para generar PDFs

### "No se puede guardar el PDF"

- Verifica que el directorio `PDF_OUTPUT_DIR` exista
- Asegúrate que tengamos permisos de escritura

## 📝 Notas Adicionales

- Los tests retornan `0` si pasan, `1` si fallan
- Los PDFs generados se guardan en `test_output/`
- Los logs del servidor son clave para diagnosticar problemas
- Puedes agregar más casos de prueba editando los archivos correspondientes
