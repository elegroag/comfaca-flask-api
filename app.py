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
from flask import Flask, request, jsonify, send_file, send_from_directory
from dotenv import dotenv_values, load_dotenv
import base64
import os
import uuid
import importlib
import json

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
# Cargar variables de entorno lo antes posible para que el middleware pueda leerlas
load_dotenv(".env")
config = dotenv_values(".env")

app = Flask(__name__)

# Registrar middleware de autenticación Basic (excluir /health)
from services.auth_middleware import register_basic_auth

register_basic_auth(app, config, exempt_paths=['/api/health', '/api/favicon.ico', '/api/creditos/generate-pdf', '/api/download-pdf'])

# Instantiate PDF service
pdf_service = GeneratePdfService()

@app.route('/api/generate-pdf', methods=['POST'])
def generate_pdf_endpoint():
    """
    Endpoint para generar PDFs.
    Request JSON:
    {
        "template": "empresa.html",
        "context": {"key": "value", ...},
        "output": "optional/path/to/output.pdf"
    }

    Response:
    - Si output especificado: JSON con {"status": "success", "path": "path/to/file"}
    - Si no output: PDF file como attachment
    """
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
        if output:
            output_path = "/app/temp_output/enlinea/" + output
        else:
            output_path = "/app/temp_output/enlinea/"+ uuid.uuid4().hex + ".pdf"

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


@app.route('/api/styles/<path:filename>')
def serve_styles(filename):
    styles_dir = Path(__file__).parent / 'templates' / 'styles'
    return send_from_directory(styles_dir, filename)


@app.route('/api/img/<path:filename>')
def serve_images(filename):
    img_dir = Path(__file__).parent / 'templates' / 'img'
    return send_from_directory(img_dir, filename)


@app.route('/api/fonts/<path:filename>')
def serve_fonts(filename):
    fonts_dir = Path(__file__).parent / 'templates' / 'fonts'
    return send_from_directory(fonts_dir, filename)


@app.route('/api/render-template', methods=['GET'])
def render_template_endpoint():
    try:
        config_name = request.args.get('config', 'render_config.json')
        if not config_name:
            return jsonify({"error": "Nombre de archivo JSON requerido"}), 400

        safe_name = Path(config_name).name
        if safe_name != config_name:
            return jsonify({"error": "Nombre de archivo JSON inválido"}), 400

        json_path = Path(__file__).parent / safe_name
        if not json_path.exists():
            return jsonify({"error": f"Archivo JSON no encontrado: {config_name}"}), 404

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
def health_check():
    """Endpoint de verificación de salud."""
    return jsonify({"status": "healthy", "service": "pdf-generator"})


@app.route('/api/download-pdf', methods=['GET'])
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