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
from flask import Flask, request, jsonify, send_file
from dotenv import dotenv_values
import io
import importlib

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
# Cargar variables de entorno lo antes posible para que el middleware pueda leerlas
config = dotenv_values(".env")

app = Flask(__name__)

# Registrar middleware de autenticación Basic (excluir /health)
from services.auth_middleware import register_basic_auth

register_basic_auth(app, config, exempt_paths=['/health', '/favicon.ico'])

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
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type debe ser application/json"}), 415
        data = request.get_json()

        if not data:
            return jsonify({"error": "JSON requerido"}), 400

        template = data.get('template')
        context = data.get('context', {})
        output_path = "/app/output/" + data.get('output')

        if not template:
            return jsonify({"error": "Campo 'template' requerido"}), 400

        if not isinstance(context, dict):
            return jsonify({"error": "Campo 'context' debe ser un objeto JSON"}), 400

        # Generar PDF via service
        result = pdf_service.generate_pdf(template, context, output_path)

        if output_path:
            # Retornar confirmación de guardado
            return jsonify({
                "success": True,
                "message": "PDF generado exitosamente",
                "path": result
            })
        else:
            # Retornar PDF como archivo
            pdf_buffer = io.BytesIO(result)
            pdf_buffer.seek(0)
            return send_file(
                pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"{Path(template).stem}.pdf"
            )

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

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint no encontrado"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Error interno del servidor"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
