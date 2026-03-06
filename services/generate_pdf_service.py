"""GeneratePdfService: encapsulates HTML -> PDF generation logic.

This is a port of the former top-level `generate_pdf` function into a
service class following a simple layered pattern.
"""
from pathlib import Path
import logging
import time
import base64
from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeneratePdfService:
    """Service responsible for rendering an HTML template and producing a PDF.

    Methods
    -------
    generate_pdf(template_name, context, output_path=None)
        Renders the specified template with context and returns PDF bytes or writes
        to a file and returns the output path.
    """

    def __init__(self, templates_dir=None):
        # Allow overriding templates directory for tests or different layouts
        if templates_dir:
            self.templates_dir = Path(templates_dir)
        else:
            # Default to the `templates` folder next to this service file's parent
            self.templates_dir = Path(__file__).parent.parent / "templates"

        self.env = Environment(loader=FileSystemLoader(str(self.templates_dir)))

    def generate_pdf(self, template_name: str, context: dict, output_path: str = None):
        """Generate a PDF from a Jinja2 HTML template.

        Parameters
        ----------
        template_name : str
            Filename of the template inside the templates directory.
        context : dict
            Context used to render the template.
        output_path : str, optional
            If provided, the PDF will be written to this path and the path is
            returned. Otherwise the PDF in base64 is returned.

        Returns
        -------
        dict
            Dictionary with api_content, api_path, api_filename.
        """
        start_time = time.time()
        logger.info(f"Iniciando generación de PDF para template: {template_name}")
        
        # Prevent path traversal by using only the name
        safe_name = Path(template_name).name
        if safe_name != template_name:
            raise ValueError("Nombre de template inválido")

        template_path = self.templates_dir / safe_name
        if not template_path.exists():
            raise ValueError(f"Template no encontrado: {template_name}")

        # Medir tiempo de renderizado
        render_start = time.time()
        template = self.env.get_template(safe_name)
        
        rendered_html = template.render(**context)
        render_time = time.time() - render_start
        logger.info(f"Template renderizado en {render_time:.2f} segundos")

        # Medir tiempo de generación de PDF
        pdf_start = time.time()
        base_url = template_path.parent
        pdf_bytes = HTML(string=rendered_html, base_url=str(base_url)).write_pdf()
        pdf_time = time.time() - pdf_start
        logger.info(f"PDF generado en {pdf_time:.2f} segundos")

        total_time = time.time() - start_time
        logger.info(f"Tiempo total de generación: {total_time:.2f} segundos")

        if output_path:
            # Guardar PDF en disco
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)
            logger.info(f"PDF guardado en: {output_path}")
        
            # Extraer nombre de archivo desde output_path
            pdf_filename = Path(output_path).name
            
            # Convertir PDF a base64
            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
            logger.info(f"PDF convertido a base64, longitud: {len(pdf_base64)} caracteres")
            return {
                "api_content": pdf_base64,
                "api_path": output_path,
                "api_filename": pdf_filename
            }
        else:
            raise ValueError("El path de salida es requerido para guardar el PDF")
       

    def render_template(self, template_name: str, context: dict) -> str:
        safe_name = Path(template_name).name
        if safe_name != template_name:
            raise ValueError("Nombre de template inválido")

        template_path = self.templates_dir / safe_name
        if not template_path.exists():
            raise ValueError(f"Template no encontrado: {template_name}")

        template = self.env.get_template(safe_name)
        rendered_html = template.render(**context)
        return rendered_html