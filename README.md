# API Flask para generación de PDFs

Servicio Flask que genera archivos PDF a partir de plantillas HTML/Jinja2 utilizando WeasyPrint. Expone endpoints REST para generar el PDF y para renderizar las plantillas directamente en el navegador.

## Requisitos

- Python 3.10+ (recomendado)
- Dependencias del proyecto instaladas (por ejemplo mediante `uv` o `pip`)
- Sistema con las fuentes y librerías necesarias para que WeasyPrint pueda generar PDFs

## Instalación

1. Clonar el repositorio (o ubicar el proyecto en tu entorno de trabajo).
2. Crear y activar un entorno virtual (opcional pero recomendado).
3. Instalar dependencias (ejemplos):

```bash
uv sync
# o, si usas pip y requirements.txt
pip install -r requirements.txt
```

4. Crear un archivo `.env` en la raíz del proyecto (junto a `app.py`) con las variables necesarias para la autenticación básica y configuración. Revisa `services/auth_middleware.py` para ver exactamente qué variables se usan.

## Ejecución del servidor

Desde la carpeta del proyecto:

```bash
uv run python app.py
```

El servidor se inicia por defecto en:

- Host: `0.0.0.0`
- Puerto: `80`

Por lo tanto, la API estará disponible (por ejemplo en local) en: `http://localhost/`.

> Si necesitas cambiar el puerto o modo debug, modifica la sección `if __name__ == '__main__':` en `app.py`.

## Autenticación

La API utiliza un middleware de autenticación básica (Basic Auth) definido en `services/auth_middleware.py`. Las credenciales se leen desde `.env` (`BASIC_USER`, `BASIC_PASSWORD`).

**Rutas exentas** (no requieren auth):

- `/api/health`
- `/api/favicon.ico`
- `/api/creditos/generate-pdf`
- `/api/creditos/v2/generate-pdf`
- `/api/creditos/v2/render-template`
- `/api/download-pdf`

**Prefijos exentos**:

- `/api/creditos/v2/assets/` (CSS y estáticos para previsualización HTML)

## Estructura principal

- `app.py`: aplicación Flask y definición de endpoints.
- `services/generate_pdf_service.py`: generación genérica HTML → PDF (WeasyPrint).
- `services/creditos_generator_service.py`: PDF de solicitud de crédito (formato v1).
- `services/creditos_v2_generator_service.py`: PDF/HTML de solicitud de crédito (formato v2).
- `services/auth_middleware.py`: Basic Auth.
- `templates/`: plantillas genéricas.
- `templates_creditos/`: plantillas del formato de crédito v1.
- `templates_creditos_v2/`: plantillas del formato de crédito v2 (layout, includes, styles).
- `credito-new-format.html`: referencia visual del diseño v2.
- `public/`: JSON de configuración y fixtures para `render-template` (p. ej. `render_config_creditos_v2.json`).

## Endpoints

### 1. `POST /api/generate-pdf`

Genera un PDF a partir de una plantilla y un contexto de datos.

**Request**

- Método: `POST`
- URL: `/api/generate-pdf`
- Cabeceras:
  - `Content-Type: application/json`
  - Cabecera `Authorization: Basic ...` si la autenticación está habilitada

**Body JSON**

```json
{
  "template": "empresa.html",
  "context": {
    "razon": "Empresa S.A.",
    "direccion": "Calle 123"
  },
  "output": "output/empresa.pdf"
}
```

- `template`: nombre lógico de la plantilla (el servicio internamente usará `template + ".j2"`).
- `context`: objeto JSON con las variables que se usarán al renderizar la plantilla.
- `output`: ruta (dentro de `/app/output/`) donde se guardará el PDF generado.

**Respuestas**

- **200 OK** (cuando se especifica `output`):

  ```json
  {
    "success": true,
    "message": "PDF generado exitosamente",
    "path": "<ruta completa del archivo>"
  }
  ```

- **Errores comunes**:
  - `400`: cuerpo JSON inválido o campos requeridos faltantes.
  - `404`: plantilla no encontrada.
  - `415`: `Content-Type` distinto de `application/json`.
  - `500`: error interno al generar el PDF.

**Ejemplo con curl**

```bash
curl -X POST "http://localhost/api/generate-pdf" \
  -H "Content-Type: application/json" \
  -u usuario:clave \
  -d '{
        "template": "empresa.html",
        "context": {"razon": "Empresa S.A.", "direccion": "Calle 123"},
        "output": "empresa.pdf"
      }'
```

### 2. `GET /api/render-template`

Renderiza una plantilla HTML en el navegador leyendo su configuración desde un archivo JSON.

**Request**

- Método: `GET`
- URL: `/api/render-template`
- Parámetros de query:
  - `config` (opcional): nombre del archivo JSON de configuración. Por defecto `render_config.json`.

El archivo JSON se busca en el directorio `public/` del proyecto.

**Formato del archivo JSON**

```json
{
  "template": "adicion-old.html",
  "context": {
    "campo1": "valor1",
    "campo2": "valor2"
  },
  "output_path": "opcional/ruta/salida.pdf"
}
```

- `template`: nombre lógico de la plantilla (el código usa internamente `template + ".j2"`).
- `context`: objeto JSON con las variables que usará la plantilla.
- `output_path` / `output`: valor opcional, actualmente solo se lee pero este endpoint se limita a renderizar HTML en el navegador.

**Respuestas**

- **200 OK**: HTML renderizado de la plantilla, mostrado directamente en el navegador.
- **Errores comunes**:
  - `400`: nombre de archivo JSON inválido o campo `template`/`context` inválidos.
  - `404`: archivo JSON de configuración o plantilla no encontrados.
  - `500`: error interno al renderizar.

**Ejemplos de uso**

1. Usando el archivo por defecto `render_config.json`:

```bash
curl -X GET "http://localhost/api/render-template" -u usuario:clave
```

2. Usando un archivo de configuración específico `mi_config.json`:

```bash
curl -X GET "http://localhost/api/render-template?config=mi_config.json" -u usuario:clave
```

### 3. `GET /api/health`

Endpoint de verificación de salud.

- Método: `GET`
- URL: `/api/health`
- Respuesta:

```json
{
  "status": "healthy",
  "service": "pdf-generator"
}
```

Este endpoint no requiere autenticación.

### 4. `POST /api/creditos/generate-pdf` (formato v1)

Genera el PDF de solicitud de crédito con las plantillas de `templates_creditos/` (`CreditosGeneratorService`).

- **Auth**: no requiere Basic Auth.
- **Body**: JSON de dominio de crédito (`solicitud_id`, `solicitud`, `solicitante`, etc.). Ver `docs/variables-oficio-credito.md`.
- **Salida**: `temp_output/solicitudes/{solicitud_id}/`.

```bash
curl -X POST "http://localhost:5000/api/creditos/generate-pdf" \
  -H "Content-Type: application/json" \
  -d @payload_credito.json
```

### 5. Créditos formato v2

Nuevo formato basado en `credito-new-format.html`, implementado en `templates_creditos_v2/` y `CreditosV2GeneratorService`.

Comparte el **mismo contrato JSON** que el endpoint v1 (con normalización de `referencias`, `conyuge`, `economica`, etc.).

#### Productos (`solicitud.producto_tipo`)

| Código | Producto              |
|--------|-----------------------|
| `04`   | Educación             |
| `05`   | Salud                 |
| `02`   | Vivienda              |
| `01`   | Libre Inversión       |
| `03`   | Recreación y Turismo  |

#### Estructura de plantillas v2

```
templates_creditos_v2/
  layout.html.j2
  formato-credito.html.j2
  styles/main.css
  macros/macros.html.j2
  includes/
    header.html.j2
    solicitud.html.j2
    producto_solicitado.html.j2
    datos_solicitante.html.j2
    informacion_laboral.html.j2
    informacion_economica.html.j2
```

#### 5.1. `POST /api/creditos/v2/generate-pdf`

Genera el PDF con el formato v2.

- **Auth**: no requiere Basic Auth.
- **Body**: mismo JSON de dominio que v1 (`solicitud_id` obligatorio).
- **Salida**: `temp_output/solicitudes_v2/{solicitud_id}/solicitud_v2_*.pdf`.
- **Respuesta**:

```json
{
  "success": true,
  "message": "PDF v2 generado exitosamente",
  "data": {
    "api_content": "<base64>",
    "api_path": ".../temp_output/solicitudes_v2/.../archivo.pdf",
    "api_filename": "solicitud_v2_....pdf"
  }
}
```

```bash
curl -X POST "http://localhost:5000/api/creditos/v2/generate-pdf" \
  -H "Content-Type: application/json" \
  -d @public/render_config_creditos_v2.json
```

#### 5.2. `POST|GET /api/creditos/v2/render-template`

Renderiza el HTML del formato v2 para validar la presentación en el navegador (sin generar PDF).

- **Auth**: no requiere Basic Auth.
- **Respuesta**: `text/html` (CSS servido desde `/api/creditos/v2/assets/...`).
- **GET**: los archivos JSON se leen desde `public/`.

**POST** — body JSON (mismo contrato que generate-pdf; también acepta `{ "context": { ... } }`):

```bash
curl -X POST "http://localhost:5000/api/creditos/v2/render-template" \
  -H "Content-Type: application/json" \
  -d @public/render_config_creditos_v2.json \
  -o preview-v2.html
```

**GET** — lee un JSON desde `public/` (`config` por defecto: `render_config_creditos_v2.json`):

```bash
curl "http://localhost:5000/api/creditos/v2/render-template?config=render_config_creditos_v2.json" \
  -o preview-v2.html
```

Abrir `preview-v2.html` en el navegador (o apuntar el navegador al endpoint GET si el servidor está en marcha) para validar layout, checkboxes, montos y secciones.

#### 5.3. `GET /api/creditos/v2/assets/<path>`

Sirve archivos estáticos de `templates_creditos_v2/` (p. ej. `styles/main.css`) usados por la previsualización HTML. Sin autenticación.

## Notas sobre las plantillas

- Las plantillas genéricas viven en `templates/`; las de crédito en `templates_creditos/` (v1) y `templates_creditos_v2/` (v2).
- El servicio `GeneratePdfService` espera nombres de archivo con extensión `.j2`.
- Desde los endpoints genéricos se usa un nombre lógico (por ejemplo `empresa.html`) y el código agrega `.j2` internamente.
- Los endpoints de créditos no reciben `template` en el body: cada servicio fija su plantilla principal (`formato-credito-front.html.j2` / `formato-credito.html.j2`).

## Desarrollo y pruebas

- Plantillas genéricas: probar con `/api/render-template` y luego `/api/generate-pdf`.
- Créditos v2: validar presentación con `/api/creditos/v2/render-template` (fixture `public/render_config_creditos_v2.json`) y luego generar PDF con `/api/creditos/v2/generate-pdf`.
- Coloca los JSON de prueba/configuración en `public/`; los endpoints `render-template` solo leen archivos de esa carpeta.
- Referencia de variables del JSON de crédito: `docs/variables-oficio-credito.md`.

## Para volver a crear el venv con `uv` en [flask-api](cci:9://file:///home/elegro/proyectos/python/comfaca-credito/flask-api:0:0-0:0)

### 1) Eliminar venv anterior (si existe)

```bash
rm -rf .venv
```

### 2) Crear nuevo entorno con uv

```bash
cd /home/elegro/proyectos/python/comfaca-credito/flask-api
uv venv
```

### 3) Activar e instalar dependencias

```bash
source .venv/bin/activate
uv pip install -e .
# o simplemente:
uv sync


uv pip freeze > requirements.txt
uv pip compile pyproject.toml -o requirements.txt

uv venv --python 3.12.2
```

### 4) Verificar instalación

```bash
uv pip list
python -c "import flask, weasyprint; print('OK')"


# Iniciar la aplicación
pm2 start ecosystem.config.js

# Ver estado
pm2 status

# Ver logs
pm2 logs flask-api

# Reiniciar
pm2 restart flask-api

# Detener
pm2 stop flask-api
```
