from __future__ import annotations

import logging
import base64
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from jinja2 import Environment, FileSystemLoader, Undefined
from weasyprint import HTML

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    def __init__(self, message: str, *, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.details = details or {}

class CreditosGeneratorService:
    """
    Servicio para generar PDFs de solicitudes de crédito con soporte para
    convenios empresariales y firmantes.
    """

    def __init__(self):
        project_root = Path(__file__).resolve().parents[1]
        self.template_dir = project_root / 'templates_creditos'
        self.storage_dir = project_root / 'temp_output'
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Configurar Jinja2 con Undefined silencioso
        class SilentUndefined(Undefined):
            def __str__(self) -> str:
                return ''
            def __getitem__(self, key: str) -> 'SilentUndefined':
                return SilentUndefined(key)
            def __call__(self, *args: Any, **kwargs: Any) -> str:
                return ''
            def __iter__(self) -> Any:
                return iter([])

        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            undefined=SilentUndefined
        )

        # Registrar filtros personalizados
        self._registrar_filtros()

    def _registrar_filtros(self) -> None:
        """Registra filtros personalizados para Jinja2."""

        def format_currency(value: Any) -> str:
            """Formatea valor como moneda colombiana."""
            if value is None or value == '':
                return '$ 0'
            try:
                return "${:,.0f}".format(float(value)).replace(',', '.')
            except (ValueError, TypeError):
                return '$ 0'

        def format_date(value: Any, format_str: str = '%d/%m/%Y') -> str:
            """Formatea fecha."""
            if not value:
                return ''
            try:
                if isinstance(value, str):
                    date_obj = datetime.fromisoformat(value.replace('Z', '+00:00'))
                elif isinstance(value, datetime):
                    date_obj = value
                else:
                    return ''
                return date_obj.strftime(format_str)
            except (ValueError, TypeError) as e:
                logger.warning(f"Error formateando fecha: {e}", extra={"value": str(value)})
                return str(value)

        def format_document(value: Any) -> str:
            """Formatea número de documento."""
            if not value:
                return ''
            try:
                return "{:,.0f}".format(float(value)).replace(',', '.')
            except (ValueError, TypeError) as e:
                logger.warning(f"Error formateando documento: {e}", extra={"value": str(value)})
                return str(value)

        self.env.filters['currency'] = format_currency
        self.env.filters['format_date'] = format_date
        self.env.filters['format_document'] = format_document

    def generar_pdf(
        self, 
        data: Dict[str, Any],
   ) -> Dict[str, Any]:
        """
        Genera el PDF de una solicitud de crédito y retorna el contenido en base64.
        
        Args:
            data: Diccionario con todos los datos necesarios para generar el PDF:
                - solicitud_id: ID de la solicitud (requerido)
                - solicitud: Datos de la solicitud
                - solicitante: Datos del solicitante
                - laboral: Datos laborales
                - economica: Datos económicos
                - ingresos: Datos de ingresos
                - descuentos: Datos de descuentos
                - conyuge: Datos del cónyuge (opcional)
                - referencias: Lista de referencias
                - deudas: Lista de deudas
                - propiedades: Lista de propiedades
                - firmantes: Lista de firmantes
                - convenio: Datos del convenio (opcional)
                - proceso_firmado: Datos del proceso de firmado
                - encabezado: Datos del encabezado
                - pdf_metadata: Metadatos del PDF
                - trabajador: Datos del trabajador (opcional)
            
        Returns:
            Dict con el contenido del PDF generado:
                - content: String con el contenido del PDF en base64
                - pdf_path: Ruta completa del archivo PDF generado
                - pdf_filename: Nombre del archivo PDF
            
        Raises:
            ValidationError: Si faltan datos requeridos o hay errores en el proceso
        """       
        # Validar y extraer datos de entrada
        solicitud_id = str(data.get("solicitud_id") or "").strip()
        if not solicitud_id:
            logger.error("Solicitud ID faltante en datos de entrada")
            raise ValueError(
                "Campo requerido faltante: solicitud_id"
            )

        # Extraer datos opcionales con valores por defecto
        trabajador_data = data.get("trabajador", {})

        logger.info(
            "Iniciando generación de PDF",
            extra={
                "solicitud_id": solicitud_id,
                "tiene_convenio": data.get("convenio") is not None,
                "cantidad_firmantes": len(data.get("firmantes", []))
            }
        )
        
        # Validar estructura básica de los datos
        self._validar_estructura_solicitud(data)

        # Normalizar datos del JSON al formato esperado por los templates
        contexto = self._preparar_contexto(data)

        # Validar contexto normalizado
        self._validar_contexto_template(contexto)

        # Renderizar HTML desde template
        html_content = self._renderizar_template(contexto)
        
        # Generar PDF desde HTML
        api_content, api_path, api_filename = self._generar_pdf_desde_html(
            html_content=html_content,
            solicitud_id=solicitud_id
        )
        
        logger.info(
            "PDF generado exitosamente",
            extra={
                "api_path": api_path,
                "api_filename": api_filename,
            }
        )
        return {
            "api_content": api_content,
            "api_path": api_path,
            "api_filename": api_filename
        }

    def _validar_estructura_solicitud(self, data: Dict[str, Any]) -> None:
        """Valida la estructura básica de los datos de la solicitud."""
        # Validar campos requeridos
        campos_requeridos = ["solicitud", "solicitante"]
        for campo in campos_requeridos:
            if campo not in data or not data[campo]:
                raise ValueError(
                    f"Campo requerido faltante: {campo}"
                )
        
        # Validar estructura de solicitud
        solicitud_info = data["solicitud"]
        if not isinstance(solicitud_info, dict):
            raise ValueError(
                "Estructura inválida: solicitud debe ser un diccionario"
            )
        
        # Validar campos críticos de solicitud
        if not solicitud_info.get("numero_solicitud"):
            logger.error(
                "Campo crítico faltante: numero_solicitud",
                extra={"solicitud": solicitud_info}
            )
            raise ValueError(
                "Campo requerido faltante: numero_solicitud"
            )
    
    def _preparar_contexto(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normaliza los datos del JSON de entrada al formato esperado por los templates."""
        ctx = deepcopy(data)

        # --- economica: renombrar campos ---
        economica = ctx.get("economica", {})
        if "otros" in economica and "otros_ingresos" not in economica:
            economica["otros_ingresos"] = economica.pop("otros")
        if "descripcion" in economica and "descripcion_ingresos" not in economica:
            economica["descripcion_ingresos"] = economica.pop("descripcion")
        if "gastos_descripcion" in economica and "descripcion_gastos" not in economica:
            economica["descripcion_gastos"] = economica.pop("gastos_descripcion")
        ctx["economica"] = economica

        # --- ingresos: mover subsidio_transporte desde descuentos si falta ---
        ingresos = ctx.get("ingresos", {})
        descuentos = ctx.get("descuentos", {})
        if "subsidio_transporte" not in ingresos and "subsidio_transporte" in descuentos:
            ingresos["subsidio_transporte"] = descuentos.pop("subsidio_transporte")
        if "total_neto_recibido" in ingresos and "total_neto" not in ingresos:
            ingresos["total_neto"] = ingresos.pop("total_neto_recibido")
        ctx["ingresos"] = ingresos

        # --- descuentos: renombrar total_descuentos → total_gastos ---
        if "total_descuentos" in descuentos and "total_gastos" not in descuentos:
            descuentos["total_gastos"] = descuentos.pop("total_descuentos")
        ctx["descuentos"] = descuentos

        # --- referencias: dict {familiares:[], personales:[]} → lista plana con campo tipo ---
        referencias_raw = ctx.get("referencias", [])
        if isinstance(referencias_raw, dict):
            lista_refs: List[Dict[str, Any]] = []
            for ref in referencias_raw.get("familiares", []):
                ref_copy = dict(ref)
                ref_copy["tipo"] = "familiar"
                lista_refs.append(ref_copy)
            for ref in referencias_raw.get("personales", []):
                ref_copy = dict(ref)
                ref_copy["tipo"] = "personal"
                lista_refs.append(ref_copy)
            ctx["referencias"] = lista_refs

        # --- conyuge: array [] → dict o None ---
        conyuge_raw = ctx.get("conyuge")
        if isinstance(conyuge_raw, list):
            ctx["conyuge"] = conyuge_raw[0] if conyuge_raw else None

        return ctx

    def _validar_contexto_template(self, context: Dict[str, Any]) -> None:
        """Valida que el contexto del template tenga todos los datos necesarios."""
        solicitante = context.get("solicitante", {})
        solicitud = context.get("solicitud", {})

        # Validar datos del solicitante
        if not solicitante.get("numero_documento"):
            logger.warning("Contexto sin número de identificación del solicitante")

        if not solicitante.get("nombre_completo"):
            logger.warning("Contexto sin nombre del solicitante")

        # Validar datos de la solicitud
        if not solicitud.get("numero_solicitud"):
            logger.error(
                "Contexto inválido: falta numero_solicitud",
                extra={"solicitud": solicitud}
            )
            raise ValidationError(
                "Contexto inválido: falta numero_solicitud en los datos de solicitud",
                details={"field": "solicitud.numero_solicitud"}
            )

        # Validar estructura de firmantes
        firmantes = context.get("firmantes", [])
        if firmantes and not isinstance(firmantes, list):
            raise ValidationError(
                "Estructura inválida: firmantes debe ser una lista",
                details={"expected": "list", "received": type(firmantes).__name__}
            )

        logger.info(
            "Contexto validado exitosamente",
            extra={
                "numero_solicitud": solicitud.get("numero_solicitud"),
                "solicitante": solicitante.get("nombre_completo"),
                "tiene_convenio": context.get("convenio") is not None,
                "cantidad_firmantes": len(firmantes)
            }
        )

    def _renderizar_template(self, context: Dict[str, Any]) -> str:
        """Renderiza el template HTML con el contexto."""
        try:
            template = self.env.get_template('formato-credito-front.html.j2')
            # Agregar template_dir al contexto para las rutas CSS
            template_context = dict(context)
            template_context['template_dir'] = str(self.template_dir)
            return template.render(**template_context)
        except Exception as e:
            logger.exception("Error renderizando template")
            raise ValueError(
                f"Error al generar el documento HTML: {str(e)}"
            )

    def _generar_pdf_desde_html(
        self, 
        html_content: str, 
        solicitud_id: str
    ) -> tuple[str, str, str]:
        """Genera PDF desde contenido HTML y retorna el contenido en base64, ruta y nombre de archivo."""
        try:
            # Crear directorio para el solicitante si no existe
            solicitud_dir = self.storage_dir / "solicitudes" / solicitud_id
            solicitud_dir.mkdir(parents=True, exist_ok=True)
            
            # Nombre del archivo PDF
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_filename = f"solicitud_{solicitud_id}_{timestamp}.pdf"
            pdf_path = solicitud_dir / pdf_filename
            
            # Generar PDF con WeasyPrint
            pdf_bytes = HTML(string=html_content, base_url=str(self.template_dir)).write_pdf()
            
            # Guardar PDF en disco
            with open(pdf_path, 'wb') as f:
                f.write(pdf_bytes)
            
            # Convertir a base64
            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
            
            logger.info(
                "PDF generado exitosamente",
                extra={
                    "solicitud_id": solicitud_id,
                    "pdf_path": str(pdf_path),
                    "pdf_size_bytes": len(pdf_bytes),
                    "base64_length": len(pdf_base64)
                }
            )
            
            return pdf_base64, str(pdf_path), pdf_filename
            
        except Exception as e:
            logger.exception("Error generando PDF")
            raise ValueError(
                f"Error al generar el archivo PDF: {str(e)}"
            )