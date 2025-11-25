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

La API utiliza un middleware de autenticación básica (Basic Auth) definido en `services/auth_middleware.py`.

- El middleware está registrado para todas las rutas excepto `/api/health` y `/favicon.ico`.
- Las credenciales se leen desde el archivo `.env`.

Consulta `services/auth_middleware.py` para ver los nombres exactos de las variables de entorno y la lógica de validación.

## Estructura principal

- `app.py`: aplicación Flask y definición de endpoints.
- `services/generate_pdf_service.py`: servicio que encapsula la lógica de renderizado HTML y generación de PDF con WeasyPrint.
- `templates/`: plantillas HTML/Jinja2 utilizadas para generar los documentos.

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

El archivo JSON se busca en el mismo directorio donde está `app.py`.

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

## Notas sobre las plantillas

- Las plantillas se almacenan en el directorio `templates/`.
- El servicio `GeneratePdfService` espera nombres de archivo con extensión `.j2`.
- Desde los endpoints, se suele trabajar con un nombre lógico (por ejemplo `adicion-old.html`) y el código agrega la extensión `.j2` internamente.

## Desarrollo y pruebas

- Puedes crear nuevas plantillas en `templates/` y probar su renderizado primero con `/api/render-template` usando un archivo JSON de configuración.
- Una vez validado el HTML, puedes generar el PDF usando `/api/generate-pdf` con la misma plantilla y contexto.
