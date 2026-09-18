#!/usr/bin/env python3
"""
Flask API para generar PDFs desde templates HTML usando WeasyPrint.
Recibe parámetros por POST method y retorna el PDF generado.

Uso:
    uv run python app.py
    curl -X POST http://localhost:5000/generate-pdf \
         -H "Content-Type: application/json" \
         -d '{"template": "empresa.html", "context": {"razon": "Empresa S.A.", "direccion": "Calle 123"}, "output": "output.pdf"}'
"""

from pathlib import Path
from flask import Flask, request, jsonify, send_file, send_from_directory, Response
from dotenv import dotenv_values, load_dotenv
from flasgger import Swagger, swag_from
import base64
import io
import os
import uuid
import importlib
import json

from pypdf import PdfReader, PdfWriter

# Workaround: fontTools deprecated `instantiateVariableFont` location
# Newer fonttools expose the function in `fontTools.varLib.instancer`.
# We ensure `fontTools.varLib.mutator.instantiateVariableFont` points to
# the up-to-date implementation before WeasyPrint imports it. This
# prevents the deprecation UserWarning emitted by older WeasyPrint code
# that imports the symbol from `mutator`.
try:
    instancer = importlib.import_module('fontTools.varLib.instancer')
    mutator = importlib.import_module('fontTools.varLib.mutator')
    if hasattr(instancer, 'instantiateVariableFont'):
        mutator.instantiateVariableFont = instancer.instantiateVariableFont
except Exception:
    # If anything fails, don't break startup; the warning may still appear.
    pass


from services.generate_pdf_service import GeneratePdfService
from services.creditos_generator_service import CreditosGeneratorService
from services.creditos_v2_generator_service import CreditosV2GeneratorService
# Cargar variables de entorno lo antes posible para que el middleware pueda leerlas
load_dotenv(".env")
config = dotenv_values(".env")

app = Flask(__name__)

# JSON de configuración / fixtures para render-template
BASE_DIR = Path(__file__).parent
PUBLIC_DIR = BASE_DIR / 'public'
PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
SWAGGER_DIR = BASE_DIR / 'swagger'

# Documentación Swagger UI (Flasgger)
swagger_config = {
    'headers': [],
    'specs': [
        {
            'endpoint': 'apispec_1',
            'route': '/apispec_1.json',
            'rule_filter': lambda rule: True,
            'model_filter': lambda tag: True,
        }
    ],
    'static_url_path': '/flasgger_static',
    'swagger_ui': True,
    'specs_route': '/docs/',
}
Swagger(
    app,
    config=swagger_config,
    template_file=str(SWAGGER_DIR / 'openapi_template.yml'),
)

# Registrar middleware de autenticación Basic (excluir /health)
from services.auth_middleware import register_basic_auth

register_basic_auth(
    app,
    config,
    exempt_paths=[
        '/api/health',
        '/api/favicon.ico',
        '/api/creditos/generate-pdf',
        '/api/creditos/v2/generate-pdf',
        '/api/creditos/v2/render-template',
        '/api/download-pdf',
        '/apispec_1.json',
    ],
    exempt_prefixes=[
        '/api/creditos/v2/assets/',
        '/docs',
        '/flasgger_static',
    ],
)

# Instantiate PDF service
pdf_service = GeneratePdfService()

@app.route('/api/generate-pdf', methods=['POST'])
@swag_from(str(SWAGGER_DIR / 'paths' / 'generate_pdf.yml'))
def generate_pdf_endpoint():
    """Genera un PDF a partir de una plantilla y un contexto JSON."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        if not request.is_json:
            raise ValueError("Content-Type debe ser application/json")
        data = request.get_json()

        if not data:
            raise ValueError("JSON requerido")

        template = data.get('template')
        context = data.get('context', {})
        output = data.get('output')
        project_dir = Path(__file__).parent
        if output:
            output_path = str(project_dir / "temp_output" / "enlinea" / output)
        else:
            output_path = str(project_dir / "temp_output" / "enlinea" / (uuid.uuid4().hex + ".pdf"))

        logger.info(f"Output path: {output_path}")

        if not template:
            raise ValueError("Campo 'template' requerido")

        if not isinstance(context, dict):
            raise ValueError("Campo 'context' debe ser un objeto JSON")

        logger.info(f"Recibida solicitud de PDF para template: {template}")

        # Generar PDF via service
        resultado = pdf_service.generate_pdf("{}.j2".format(template), context, output_path)

        # Retornar confirmación de guardado
        logger.info(f"PDF generado exitosamente: {resultado['api_filename']}")
        return jsonify({
            "success": True,
            "message": "PDF generado exitosamente",
            "data": resultado
        })
        
    except ValueError as e:
        logger.error(f"Error de validación: {e}")
        return jsonify({"success": False, "error": str(e)}), 400
    except RuntimeError as e:
        logger.error(f"Error de runtime: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return jsonify({"success": False, "error": f"Error inesperado: {e}"}), 500


@app.route('/api/genera-consolidado-pdf', methods=['POST'])
@swag_from(str(SWAGGER_DIR / 'paths' / 'genera_consolidado_pdf.yml'))
def genera_consolidado_pdf_endpoint():
    import logging
    logger = logging.getLogger(__name__)

    try:
        if not request.is_json:
            raise ValueError("Content-Type debe ser application/json")

        data = request.get_json()
        if not data:
            raise ValueError("JSON requerido")

        templates = data.get('templates')
        context = data.get('context', {})
        api_filename = data.get('output', f"consolidado_{uuid.uuid4().hex}.pdf")

        if not templates or not isinstance(templates, list):
            raise ValueError("Campo 'templates' requerido y debe ser una lista")

        if not isinstance(context, dict):
            raise ValueError("Campo 'context' debe ser un objeto JSON")

        normalized_templates = []
        for t in templates:
            if not isinstance(t, str) or not t.strip():
                raise ValueError("Cada item de 'templates' debe ser un string no vacío")
            normalized_templates.append(t.strip())

        project_dir = Path(__file__).parent
        output_dir = project_dir / "temp_output" / "enlinea"
        output_dir.mkdir(parents=True, exist_ok=True)

        writer = PdfWriter()
        generated_files = []

        for template in normalized_templates:
            template_name = f"{template}.j2"
            logger.info(f"Generando PDF con template: {template}")
            individual_path = output_dir / f"{Path(template).stem}_{uuid.uuid4().hex}.pdf"
            pdf_service.generate_pdf(template_name, context, str(individual_path))
            generated_files.append(individual_path)

            reader = PdfReader(str(individual_path))
            for page in reader.pages:
                writer.add_page(page)

        out = io.BytesIO()
        writer.write(out)
        merged_bytes = out.getvalue()

        
        api_path = output_dir / api_filename
        with open(api_path, 'wb') as merged_file:
            merged_file.write(merged_bytes)

        api_content = base64.b64encode(merged_bytes).decode('utf-8')

        return jsonify({
            "success": True,
            "message": "PDF generado exitosamente",
            "data": {
                "api_content": api_content,
                "api_path": str(api_path),
                "api_filename": api_filename,
                "generated_files": [str(path) for path in generated_files]
            }
        })

    except ValueError as e:
        logger.error(f"Error de validación: {e}")
        return jsonify({"success": False, "error": str(e)}), 400
    except RuntimeError as e:
        logger.error(f"Error de runtime: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return jsonify({"success": False, "error": f"Error inesperado: {e}"}), 500


@app.route('/api/styles/<path:filename>')
@swag_from(str(SWAGGER_DIR / 'paths' / 'styles.yml'))
def serve_styles(filename):
    styles_dir = Path(__file__).parent / 'templates' / 'styles'
    return send_from_directory(styles_dir, filename)


@app.route('/api/img/<path:filename>')
@swag_from(str(SWAGGER_DIR / 'paths' / 'img.yml'))
def serve_images(filename):
    img_dir = Path(__file__).parent / 'templates' / 'img'
    return send_from_directory(img_dir, filename)


@app.route('/api/fonts/<path:filename>')
@swag_from(str(SWAGGER_DIR / 'paths' / 'fonts.yml'))
def serve_fonts(filename):
    fonts_dir = Path(__file__).parent / 'templates' / 'fonts'
    return send_from_directory(fonts_dir, filename)


@app.route('/api/render-template', methods=['GET'])
@swag_from(str(SWAGGER_DIR / 'paths' / 'render_template.yml'))
def render_template_endpoint():
    try:
        config_name = request.args.get('config', 'render_config.json')
        if not config_name:
            return jsonify({"error": "Nombre de archivo JSON requerido"}), 400

        safe_name = Path(config_name).name
        if safe_name != config_name:
            return jsonify({"error": "Nombre de archivo JSON inválido"}), 400

        json_path = PUBLIC_DIR / safe_name
        if not json_path.exists():
            return jsonify({"error": f"Archivo JSON no encontrado en public/: {config_name}"}), 404

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        template = data.get('template')
        context = data.get('context', {})
        output_path = data.get('output_path') or data.get('output')

        if not template:
            return jsonify({"error": "Campo 'template' requerido en el archivo JSON"}), 400

        if not isinstance(context, dict):
            return jsonify({"error": "Campo 'context' debe ser un objeto JSON"}), 400

        rendered_html = pdf_service.render_template("{}.j2".format(template), context)
        return rendered_html
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": f"Error inesperado: {e}"}), 500

@app.route('/api/health', methods=['GET'])
@swag_from(str(SWAGGER_DIR / 'paths' / 'health.yml'))
def health_check():
    """Endpoint de verificación de salud."""
    return jsonify({"status": "healthy", "service": "pdf-generator"})


@app.route('/api/download-pdf', methods=['GET'])
@swag_from(str(SWAGGER_DIR / 'paths' / 'download_pdf.yml'))
def download_pdf():
    """Endpoint para descargar PDF en base64."""
    try:
        # Obtener filepath del query parameter
        filepath = request.args.get('filepath')
        if not filepath:
            return jsonify({"error": "Parámetro 'filepath' requerido"}), 400
        
        # Validar que el filepath sea seguro (no path traversal)
        safe_filepath = Path(filepath).name
        if safe_filepath != filepath or '/' in filepath or '\\' in filepath:
            return jsonify({"error": "Path inválido: solo se permiten nombres de archivo"}), 400
        
        # Construir ruta completa en temp_output
        temp_output = Path(__file__).parent / 'temp_output'
        full_path = temp_output / safe_filepath
        
        # Verificar que el archivo existe
        if not full_path.exists():
            return jsonify({"error": f"Archivo no encontrado: {filepath}"}), 404
        
        # Verificar que sea un archivo PDF
        if not safe_filepath.lower().endswith('.pdf'):
            return jsonify({"error": "El archivo debe ser un PDF"}), 400
        
        # Leer archivo y convertir a base64
        with open(full_path, 'rb') as pdf_file:
            pdf_content = pdf_file.read()
            pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        
        # Retornar respuesta con el PDF en base64
        return jsonify({
            "success": True,
            "filename": safe_filepath,
            "size_bytes": len(pdf_content),
            "base64_content": pdf_base64
        })
        
    except Exception as e:
        app.logger.error(f"Error al descargar PDF: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@app.route('/api/creditos/generate-pdf', methods=['POST'])
@swag_from(str(SWAGGER_DIR / 'paths' / 'creditos_v1_generate.yml'))
def generate_pdf_creditos():
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        if not request.is_json:
            raise ValueError("Content-Type debe ser application/json")
        data = request.get_json()
       
        pdf_service_creditos = CreditosGeneratorService()
        resultado = pdf_service_creditos.generar_pdf(data)
                
        return jsonify({
            "success": True,
            "message": "PDF generado exitosamente y solicitud enviada para validación",
            "data": resultado
        })
        
    except ValueError as e:
        logger.error(f"Error de validación: {e}")
        return jsonify({"success": False, "error": str(e)}), 400
    except RuntimeError as e:
        logger.error(f"Error de runtime: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return jsonify({"success": False, "error": f"Error inesperado: {e}"}), 500


@app.route('/api/creditos/v2/generate-pdf', methods=['POST'])
@swag_from(str(SWAGGER_DIR / 'paths' / 'creditos_v2_generate.yml'))
def generate_pdf_creditos_v2():
    """Genera PDF de solicitud de crédito con el formato v2 (templates_creditos_v2)."""
    import logging
    logger = logging.getLogger(__name__)

    try:
        if not request.is_json:
            raise ValueError("Content-Type debe ser application/json")
        data = request.get_json()

        pdf_service_creditos_v2 = CreditosV2GeneratorService()
        resultado = pdf_service_creditos_v2.generar_pdf(data)

        return jsonify({
            "success": True,
            "message": "PDF v2 generado exitosamente",
            "data": resultado
        })

    except ValueError as e:
        logger.error(f"Error de validación (créditos v2): {e}")
        return jsonify({"success": False, "error": str(e)}), 400
    except RuntimeError as e:
        logger.error(f"Error de runtime (créditos v2): {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    except Exception as e:
        logger.error(f"Error inesperado (créditos v2): {e}")
        return jsonify({"success": False, "error": f"Error inesperado: {e}"}), 500


@app.route('/api/creditos/v2/render-template', methods=['POST', 'GET'])
@swag_from(str(SWAGGER_DIR / 'paths' / 'creditos_v2_render_get.yml'), methods=['GET'])
@swag_from(str(SWAGGER_DIR / 'paths' / 'creditos_v2_render_post.yml'), methods=['POST'])
def render_template_creditos_v2():
    """
    Renderiza el HTML del formato créditos v2 para previsualización.

    POST: body JSON con el mismo contrato que /api/creditos/v2/generate-pdf
    GET:  ?config=archivo.json  (archivo en public/ con el mismo JSON)
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        if request.method == 'GET':
            config_name = request.args.get('config', 'render_config_creditos_v2.json')
            safe_name = Path(config_name).name
            if safe_name != config_name:
                raise ValueError("Nombre de archivo JSON inválido")

            json_path = PUBLIC_DIR / safe_name
            if not json_path.exists():
                return jsonify({
                    "success": False,
                    "error": f"Archivo JSON no encontrado en public/: {config_name}",
                }), 404

            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            if not request.is_json:
                raise ValueError("Content-Type debe ser application/json")
            data = request.get_json()
            if not data:
                raise ValueError("JSON requerido")

        # Aceptar payload directo o envuelto en { "context": {...} }
        if isinstance(data.get('context'), dict) and 'solicitud' not in data:
            data = data['context']

        pdf_service_creditos_v2 = CreditosV2GeneratorService()
        rendered_html = pdf_service_creditos_v2.renderizar_html(
            data,
            assets_base_url='/api/creditos/v2/assets',
        )
        return Response(rendered_html, mimetype='text/html')

    except ValueError as e:
        logger.error(f"Error de validación (render créditos v2): {e}")
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error inesperado (render créditos v2): {e}")
        return jsonify({"success": False, "error": f"Error inesperado: {e}"}), 500


@app.route('/api/creditos/v2/assets/<path:filename>', methods=['GET'])
@swag_from(str(SWAGGER_DIR / 'paths' / 'creditos_v2_assets.yml'))
def serve_creditos_v2_assets(filename):
    """Sirve CSS y estáticos de templates_creditos_v2 para la previsualización HTML."""
    assets_dir = Path(__file__).parent / 'templates_creditos_v2'
    return send_from_directory(assets_dir, filename)


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint no encontrado"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Error interno del servidor"}), 500

if __name__ == '__main__':
    host = os.getenv('BASE_URL', 'localhost')
    print(f"Host: {host}")
    print(f"Port: {os.getenv('BASE_PORT', 5000)}")

    # Remover http:// o https:// si están presentes
    if host.startswith('http://'):
        host = host[7:]
    elif host.startswith('https://'):
        host = host[8:]
    
    port = int(os.getenv('BASE_PORT', 5000))
    app.run(debug=False, host=host, port=port)