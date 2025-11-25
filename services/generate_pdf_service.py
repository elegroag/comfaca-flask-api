"""GeneratePdfService: encapsulates HTML -> PDF generation logic.

This is a port of the former top-level `generate_pdf` function into a
service class following a simple layered pattern.
"""
from pathlib import Path
from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader

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
            returned. Otherwise the PDF bytes are returned.

        Returns
        -------
        bytes or str
            PDF bytes when `output_path` is None, otherwise the output path.

        Raises
        ------
        FileNotFoundError
            If the template file does not exist.
        RuntimeError
            For other unexpected errors during generation.
        """
        try:
            # Prevent path traversal by using only the name
            safe_name = Path(template_name).name
            if safe_name != template_name:
                raise ValueError("Nombre de template inválido")

            template_path = self.templates_dir / safe_name
            if not template_path.exists():
                raise FileNotFoundError(f"Template no encontrado: {template_name}")

            template = self.env.get_template(safe_name)
            rendered_html = template.render(**context)

            # Generate PDF
            base_url = template_path.parent
            pdf_bytes = HTML(string=rendered_html, base_url=str(base_url)).write_pdf()

            if output_path:
                output_dir = Path(output_path).parent
                output_dir.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'wb') as f:
                    f.write(pdf_bytes)
                return output_path
            else:
                return pdf_bytes

        except FileNotFoundError:
            # Let callers handle 404 semantics
            raise
        except Exception as e:
            raise RuntimeError(f"Error al generar PDF: {e}")

    def render_template(self, template_name: str, context: dict) -> str:
        try:
            safe_name = Path(template_name).name
            if safe_name != template_name:
                raise ValueError("Nombre de template inválido")

            template_path = self.templates_dir / safe_name
            if not template_path.exists():
                raise FileNotFoundError(f"Template no encontrado: {template_name}")

            template = self.env.get_template(safe_name)
            rendered_html = template.render(**context)
            return rendered_html
        except FileNotFoundError:
            raise
        except Exception as e:
            raise RuntimeError(f"Error al renderizar template: {e}")
