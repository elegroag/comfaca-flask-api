from __future__ import annotations

import logging
import base64
from dataclasses import dataclass
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


@dataclass
class EncabezadoData:
    """Datos del encabezado para el template."""
    fecha_radicado: str
    
    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> 'EncabezadoData':
        encabezado = payload.get("encabezado", {})
        return cls(
            fecha_radicado=encabezado.get("fecha_radicado", "")
        )


@dataclass
class SolicitanteData:
    """Datos del solicitante para el template."""
    nombres: str
    apellidos: str
    tipo_documento: str
    numero_documento: str
    cedula: str  # Alias para numero_documento
    nit: str     # NIT personal o de empresa
    fecha_nacimiento: str
    email: str
    telefono_movil: str
    direccion: str
    ciudad_residencia: str
    profesion_ocupacion: str
    salario: float
    
    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> 'SolicitanteData':
        solicitante = payload.get("solicitante", {})
        info_laboral = payload.get("informacion_laboral", {})
        
        # Mapear campos para compatibilidad con template
        numero_documento = solicitante.get("numero_documento", "")  # Corregido: numero_documento en lugar de numero_documento
        
        # Conversión segura de salario
        salario_value = 0
        try:
            salario_raw = solicitante.get("salario", 0)
            salario_value = float(salario_raw) if salario_raw else 0
        except (ValueError, TypeError) as e:
            logger.warning(f"Error convirtiendo salario: {e}", extra={"salario_raw": str(solicitante.get("salario"))})
        
        return cls(
            nombres=solicitante.get("nombres", ""),
            apellidos=solicitante.get("apellidos", ""),
            tipo_documento=solicitante.get("tipo_documento", ""),
            numero_documento=numero_documento,
            cedula=numero_documento,  # Alias
            nit=info_laboral.get("empresa_nit", ""),  # NIT de empresa como respaldo
            fecha_nacimiento=solicitante.get("fecha_nacimiento", ""),
            email=solicitante.get("email", ""),
            telefono_movil=solicitante.get("telefono", ""),  # Corregido: telefono en lugar de telefono_movil
            direccion=solicitante.get("barrio_residencia", ""),
            ciudad_residencia=solicitante.get("ciudad_residencia", ""),
            profesion_ocupacion=solicitante.get("profesion_ocupacion", ""),
            salario=salario_value
        )


@dataclass
class SolicitudData:
    """Datos de la solicitud para el template."""
    encabezado: EncabezadoData
    solicitud: 'SolicitudDetalleData'  # Datos anidados como espera el template
    solicitante: SolicitanteData  # Datos del solicitante como espera el template
    # Campos adicionales que el template espera como solicitud.campo
    producto_solicitado: Dict[str, Any]
    informacion_laboral: Dict[str, Any]
    ingresos_descuentos: Dict[str, Any]
    informacion_economica: Dict[str, Any]
    deudas: List[Dict[str, Any]]
    referencias: Dict[str, Any]
    
    @classmethod
    def from_payload(cls, payload: Dict[str, Any], numero_solicitud: str = "") -> 'SolicitudData':
        return cls(
            encabezado=EncabezadoData.from_payload(payload),
            solicitud=SolicitudDetalleData.from_payload(payload, numero_solicitud),
            solicitante=SolicitanteData.from_payload(payload),
            producto_solicitado=payload.get("producto_solicitado", {}),
            informacion_laboral=payload.get("informacion_laboral", {}),
            ingresos_descuentos=payload.get("ingresos_descuentos", {}),
            informacion_economica=payload.get("informacion_economica", {}),
            deudas=payload.get("deudas", []),
            referencias=payload.get("referencias", {})
        )


@dataclass
class SolicitudDetalleData:
    """Datos detallados de la solicitud (anidados)."""
    numero_solicitud: str
    numero_comprobante: str
    valor_solicitud: int
    valor_solicitado: int
    categoria: str
    rol_en_solicitud: str
    plazo_meses: int
    foto_documento: Dict[str, Any]
    moneda: str
    tipcre: str
    modxml4: int
    detalle_modalidad: str
    cuota_mensual: int
    
    @classmethod
    def from_payload(cls, payload: Dict[str, Any], numero_solicitud: str = "") -> 'SolicitudDetalleData':
        solicitud = payload.get("solicitud", {})
        linea = payload.get("linea_credito", {})
        
        # Función helper para conversión segura a int
        def safe_int(value, default=0):
            try:
                return int(value) if value else default
            except (ValueError, TypeError) as e:
                logger.warning(f"Error convirtiendo a int: {e}", extra={"value": str(value)})
                return default
        
        return cls(
            numero_solicitud=numero_solicitud,  # Usar el numero_solicitud pasado como parámetro
            numero_comprobante=solicitud.get("numero_comprobante", ""),
            valor_solicitud=safe_int(solicitud.get("valor_solicitud")),
            valor_solicitado=safe_int(solicitud.get("valor_solicitado")),
            categoria=solicitud.get("categoria", ""),
            rol_en_solicitud=solicitud.get("rol_en_solicitud", ""),
            plazo_meses=safe_int(solicitud.get("plazo_meses")),
            foto_documento=solicitud.get("foto_documento", {"url": ""}),
            moneda=solicitud.get("moneda", "COP"),
            tipcre=solicitud.get("tipcre", ""),
            modxml4=safe_int(solicitud.get("modxml4")),
            detalle_modalidad=linea.get("detalle_modalidad", ""),
            cuota_mensual=safe_int(solicitud.get("cuota_mensual"))
        )


@dataclass
class TemplateContext:
    """Estructura completa de datos para el template."""
    solicitante: SolicitanteData
    solicitud: SolicitudData
    trabajador: Dict[str, Any]
    convenio: Optional[Dict[str, Any]]
    firmantes: List[Dict[str, Any]]
    tiene_convenio: bool
    fecha_generacion: datetime
    metadata: Dict[str, Any]
    numero_solicitud: str  # Agregar numero_solicitud directamente
    
    @classmethod
    def from_data(
        cls, 
        data: Dict[str, Any],
        trabajador: Dict[str, Any],
        convenio: Optional[Dict[str, Any]],
        firmantes: List[Dict[str, Any]]
    ) -> 'TemplateContext':
        """Crea TemplateContext desde datos."""
        payload = data.get("payload", {})
        
        return cls(
            solicitante=SolicitanteData.from_payload(payload),
            solicitud=SolicitudData.from_payload(payload, data.get("numero_solicitud", "")),
            trabajador=trabajador,
            convenio=convenio,
            firmantes=firmantes,
            tiene_convenio=convenio is not None,
            fecha_generacion=datetime.now(),
            metadata={
                "sistema": "Comfaca Crédito",
                "version": "2.0"
            },
            numero_solicitud=data.get("numero_solicitud", "")  # Agregar numero_solicitud desde data
        )


class CreditosGeneratorService:
    """
    Servicio para generar PDFs de solicitudes de crédito con soporte para
    convenios empresariales y firmantes.
    """

    def __init__(self):
        project_root = Path(__file__).resolve().parents[1]
        self.template_dir = project_root / 'templates_creditos'
        self.storage_dir = project_root / 'temp_output'
            
        # Crear directorio de storage si no existe
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar Jinja2 con Undefined silencioso
        class SilentUndefined(Undefined):
            def __str__(self):
                return ''
            def __getitem__(self, key):
                return SilentUndefined(key)
            def __call__(self, *args, **kwargs):
                return ''
            def __iter__(self):
                return iter([])
        
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            undefined=SilentUndefined
        )
        
        # Registrar filtros personalizados
        self._registrar_filtros()

    def _registrar_filtros(self):
        """Registra filtros personalizados para Jinja2."""
        
        def format_currency(value):
            """Formatea valor como moneda colombiana."""
            if value is None or value == '':
                return '$ 0'
            try:
                return "${:,.0f}".format(float(value)).replace(',', '.')
            except (ValueError, TypeError):
                return '$ 0'
        
        def format_date(value, format_str='%d/%m/%Y'):
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
        
        def format_document(value):
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
                - solicitud_data: Datos completos de la solicitud desde MongoDB (requerido)
                - trabajador_data: Datos del trabajador desde API externa (opcional)
                - convenio_data: Datos del convenio (requerido)
                - firmantes_data: Lista de firmantes (opcional)
                - incluir_firmantes: Booleano para incluir firmantes (default: True)
            
        Returns:
            Dict con el contenido del PDF generado:
                - content: String con el contenido del PDF en base64
                - pdf_path: Ruta completa del archivo PDF generado
                - pdf_filename: Nombre del archivo PDF
            
        Raises:
            ValidationError: Si faltan datos requeridos o hay errores en el proceso
        """       
        try:
            # Validar y extraer datos de entrada
            solicitud_id = str(data.get("solicitud_id") or "").strip()
            if not solicitud_id:
                logger.error("Solicitud ID faltante en datos de entrada")
                raise ValidationError(
                    "Campo requerido faltante: solicitud_id",
                    details={"field": "solicitud_id"},
                )

            # Obtener y validar datos de la solicitud
            solicitud_data = data.get("solicitud_data", {})
    
            # Extraer datos opcionales con valores por defecto
            trabajador_data = data.get("trabajador_data", {})
            
            incluir_firmantes = data.get("incluir_firmantes", True)
            
            # Obtener datos de convenio (requerido)
            convenio_data = data.get("convenio_data")

            logger.info(
                "Iniciando generación de PDF",
                extra={
                    "solicitud_id": solicitud_id,
                    "incluir_firmantes": data.get("incluir_firmantes", True),
                    "tiene_convenio": convenio_data is not None
                }
            )
            
            # Preparar datos de firmantes según flag
            firmantes_data = data.get("firmantes_data", []) if incluir_firmantes else []
            
            # Validar estructura básica del payload
            self._validar_estructura_solicitud(solicitud_data)
            
            # Crear TemplateContext usando las clases de datos estructuradas
            context = TemplateContext.from_data(
                data=solicitud_data,
                trabajador=trabajador_data,
                convenio=convenio_data,
                firmantes=firmantes_data
            )
            
            # Validar contexto creado
            self._validar_contexto_template(context)
            
            # Renderizar HTML desde template usando el contexto estructurado
            html_content = self._renderizar_template(context)
            
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
            
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            logger.exception("Error inesperado generando PDF")
            raise ValidationError(
                "Error al generar el PDF de la solicitud", 
                details={"error": str(e)}
            )

    def _validar_estructura_solicitud(self, solicitud_data: Dict[str, Any]) -> None:
        """Valida la estructura básica de los datos de la solicitud."""
        payload = solicitud_data.get("payload", {})
        if not isinstance(payload, dict):
            raise ValidationError(
                "Estructura inválida: falta payload en solicitud_data",
                details={"expected": "payload", "received": type(payload).__name__}
            )
        
        # Validar campos requeridos en el payload
        campos_requeridos = ["solicitud", "solicitante"]
        for campo in campos_requeridos:
            if campo not in payload or not payload[campo]:
                raise ValidationError(
                    f"Campo requerido faltante en payload: {campo}",
                    details={"missing_field": campo}
                )
        
        # Validar estructura de solicitud
        solicitud_info = payload["solicitud"]
        if not isinstance(solicitud_info, dict):
            raise ValidationError(
                "Estructura inválida: solicitud debe ser un diccionario",
                details={"expected": "dict", "received": type(solicitud_info).__name__}
            )
        
        # Validar campos críticos de solicitud - numero_solicitud está en solicitud_data, no en payload
        if not solicitud_data.get("numero_solicitud"):
            logger.error(
                "Campo crítico faltante: numero_solicitud",
                extra={"solicitud_data": solicitud_data}
            )
            raise ValidationError(
                "Campo requerido faltante: numero_solicitud",
                details={"field": "solicitud_data.numero_solicitud"}
            )
    
    def _validar_contexto_template(self, context: TemplateContext) -> None:
        """Valida que el contexto del template tenga todos los datos necesarios."""
        # Validar datos del solicitante
        if not context.solicitante.numero_documento:
            logger.warning("Contexto sin número de identificación del solicitante")
        
        if not context.solicitante.nombres:
            logger.warning("Contexto sin nombre del solicitante")

        if not context.solicitante.apellidos:
            logger.warning("Contexto sin apellido del solicitante")
        
        # Validar datos de la solicitud - numero_solicitud está directamente en el contexto
        if not context.numero_solicitud:
            logger.error(
                "Contexto inválido: falta numero_solicitud",
                extra={"context": {"numero_solicitud": context.numero_solicitud}}
            )
            raise ValidationError(
                "Contexto inválido: falta numero_solicitud en los datos de solicitud",
                details={"field": "context.numero_solicitud"}
            )
        
        # Validar convenio si debería tenerlo
        if context.tiene_convenio and not context.convenio:
            logger.warning("Contexto indica tener convenio pero no hay datos de convenio")
        
        # Validar estructura de firmantes
        if context.firmantes and not isinstance(context.firmantes, list):
            raise ValidationError(
                "Estructura inválida: firmantes debe ser una lista",
                details={"expected": "list", "received": type(context.firmantes).__name__}
            )
        
        logger.info(
            "Contexto validado exitosamente",
            extra={
                "numero_solicitud": context.numero_solicitud,
                "solicitante": context.solicitante.nombres,
                "tiene_convenio": context.tiene_convenio,
                "cantidad_firmantes": len(context.firmantes)
            }
        )

    def _renderizar_template(self, context: TemplateContext) -> str:
        """Renderiza el template HTML con el contexto."""
        try:
            template = self.env.get_template('formato-credito-front.html.j2')
            # Agregar template_dir al contexto para las rutas CSS
            template_context = context.__dict__.copy()
            template_context['template_dir'] = str(self.template_dir)
            return template.render(**template_context)
        except Exception as e:
            logger.exception("Error renderizando template")
            raise ValidationError(
                "Error al generar el documento HTML",
                details={"error": str(e)}
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
            raise ValidationError(
                "Error al generar el archivo PDF",
                details={"error": str(e)}
            )
