# Arquitectura del Proyecto

## Visión General

**flask-generador-oficios** es una API Flask para generar PDFs de solicitudes de crédito y oficios empresariales usando templates HTML (Jinja2) + WeasyPrint.

## Estructura de Directorios

```
flask-generador-oficios/
├── app/                          # Aplicación principal
│   ├── .hermes/                  # Metadatos del agente (Kanban)
│   │   ├── feature_list.json     # Lista de features del proyecto
│   │   └── progress/
│   │       └── current.md        # Feature actualmente en desarrollo
│   ├── docs/                     # Documentación del proyecto
│   │   └── variables-oficio-credito.md  # Referencia de variables del JSON
│   ├── services/                 # Capa de servicios
│   │   ├── auth_middleware.py    # Middleware de autenticación Basic Auth
│   │   ├── creditos_generator_service.py  # Servicio de créditos
│   │   └── generate_pdf_service.py  # Servicio de generación PDF
│   ├── templates/               # Templates Jinja2 para oficios/empresa
│   │   ├── styles/
│   │   ├── fonts/
│   │   ├── img/
│   │   └── layout/
│   ├── templates_creditos/       # Templates específicos para créditos
│   │   ├── formato-credito-front.html.j2
│   │   ├── formato-credito-back.html.j2
│   │   ├── layout.html.j2
│   │   └── includes/
│   ├── test/                     # Pruebas
│   ├── temp_output/              # PDFs generados (temporal)
│   ├── app.py                    # Punto de entrada Flask
│   └── wsgi.py                   # WSGI entry point
├── .env                          # Variables de entorno
├── requirements.txt              # Dependencias Python
└── compose.yml                   # Docker Compose
```

## Capas de la Aplicación

### 1. Capa de Presentación (Flask Routes)

`app.py` contiene todos los endpoints de la API:

| Endpoint | Método | Descripción |
|---|---|---|
| `/api/health` | GET | Health check |
| `/api/generate-pdf` | POST | Genera PDF genérico |
| `/api/genera-consolidado-pdf` | POST | Genera PDF consolidado (múltiples templates) |
| `/api/creditos/generate-pdf` | POST | Genera PDF de solicitud de crédito |
| `/api/download-pdf` | GET | Descarga PDF por filepath |
| `/api/render-template` | GET | Renderiza template a HTML |

### 2. Capa de Servicios

- **`GeneratePdfService`**: Renderiza templates Jinja2 y genera PDFs con WeasyPrint. Usa templates de `templates/`.
- **`CreditosGeneratorService`**: Servicio especializado para créditos. Normaliza datos, valida estructura y usa templates de `templates_creditos/`.

### 3. Capa de Templates (Jinja2)

- **`templates/`**: Templates para oficios empresariales (relación nómina, política empresa/trabajador, etc.)
- **`templates_creditos/`**: Templates para solicitudes de crédito (formato-credito-front/back)

### 4. Autenticación

`auth_middleware.py` implementa Basic Auth sobre Flask. Rutas exentas: `/api/health`, `/api/favicon.ico`, `/api/creditos/generate-pdf`, `/api/download-pdf`.

## Flujo de Datos

```
Request JSON → Flask Route → Service.generar_pdf()
                                    ↓
                            Jinja2 Template + context
                                    ↓
                              WeasyPrint HTML→PDF
                                    ↓
                              PDF en base64 + archivo en disco
                                    ↓
                              Response JSON
```

## Tecnologías

- **Flask 3.x**: Framework web
- **WeasyPrint 68.x**: Conversión HTML→PDF
- **Jinja2 3.x**: Motor de templates
- **pypdf 6.x**: Manipulación de PDFs (consolidado)
- **python-dotenv**: Gestión de variables de entorno

## Configuración

| Variable | Descripción | Default |
|---|---|---|
| `BASIC_USER` | Usuario Basic Auth | admin |
| `BASIC_PASSWORD` | Password Basic Auth | secretpassword |
| `OUTPUT_PATH` | Directorio de PDFs generados | /app/temp_output/ |
| `TEMPLATE_PATH` | Directorio de templates | /app/templates/ |
| `BASE_URL` | Host de la API | http://0.0.0.0 |
| `BASE_PORT` | Puerto de la API | 80 |