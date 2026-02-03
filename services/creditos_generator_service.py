from __future__ import annotations

import logging
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
    nombres_apellidos: str
    tipo_identificacion: str
    numero_identificacion: str
    cedula: str  # Alias para numero_identificacion
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
        numero_identificacion = solicitante.get("numero_identificacion", "")
        
        return cls(
            nombres_apellidos=solicitante.get("nombres_apellidos", ""),
            tipo_identificacion=solicitante.get("tipo_identificacion", ""),
            numero_identificacion=numero_identificacion,
            cedula=numero_identificacion,  # Alias
            nit=info_laboral.get("empresa_nit", ""),  # NIT de empresa como respaldo
            fecha_nacimiento=solicitante.get("fecha_nacimiento", ""),
            email=solicitante.get("email", ""),
            telefono_movil=solicitante.get("telefono_movil", ""),
            direccion=solicitante.get("barrio_residencia", ""),
            ciudad_residencia=solicitante.get("ciudad_residencia", ""),
            profesion_ocupacion=solicitante.get("profesion_ocupacion", ""),
            salario=float(solicitante.get("salario", 0))
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
    def from_payload(cls, payload: Dict[str, Any]) -> 'SolicitudData':
        return cls(
            encabezado=EncabezadoData.from_payload(payload),
            solicitud=SolicitudDetalleData.from_payload(payload),
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
    def from_payload(cls, payload: Dict[str, Any]) -> 'SolicitudDetalleData':
        solicitud = payload.get("solicitud", {})
        linea = payload.get("linea_credito", {})
        
        return cls(
            numero_solicitud=solicitud.get("numero_solicitud", ""),
            numero_comprobante=solicitud.get("numero_comprobante", ""),
            valor_solicitud=int(solicitud.get("valor_solicitud", 0)),
            valor_solicitado=int(solicitud.get("valor_solicitado", 0)),
            categoria=solicitud.get("categoria", ""),
            rol_en_solicitud=solicitud.get("rol_en_solicitud", ""),
            plazo_meses=int(solicitud.get("plazo_meses", 0)),
            foto_documento=solicitud.get("foto_documento", {"url": ""}),
            moneda=solicitud.get("moneda", "COP"),
            tipcre=solicitud.get("tipcre", ""),
            modxml4=int(solicitud.get("modxml4", 0)),
            detalle_modalidad=linea.get("detalle_modalidad", ""),
            cuota_mensual=int(solicitud.get("cuota_mensual", 0))
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
    
    @classmethod
    def from_mongodb_data(
        cls, 
        mongodb_data: Dict[str, Any],
        trabajador: Dict[str, Any],
        convenio: Optional[Dict[str, Any]],
        firmantes: List[Dict[str, Any]]
    ) -> 'TemplateContext':
        """Crea TemplateContext desde datos de MongoDB."""
        payload = mongodb_data.get("payload", {})
        
        return cls(
            solicitante=SolicitanteData.from_payload(payload),
            solicitud=SolicitudData.from_payload(payload),
            trabajador=trabajador,
            convenio=convenio,
            firmantes=firmantes,
            tiene_convenio=convenio is not None,
            fecha_generacion=datetime.now(),
            metadata={
                "sistema": "Comfaca Crédito",
                "version": "2.0"
            }
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
            except:
                return str(value)
        
        def format_document(value):
            """Formatea número de documento."""
            if not value:
                return ''
            try:
                return "{:,.0f}".format(float(value)).replace(',', '.')
            except:
                return str(value)
        
        self.env.filters['currency'] = format_currency
        self.env.filters['format_date'] = format_date
        self.env.filters['format_document'] = format_document

    def generar_pdf(
        self, 
        data: Dict[str, Any],
   ) -> Dict[str, Any]:
        """
        Genera el PDF de una solicitud de crédito.
        
        Args:
            solicitud_id: ID de la solicitud
            incluir_convenio: Si debe incluir datos del convenio
            incluir_firmantes: Si debe incluir lista de firmantes
            
        Returns:
            Dict con información del PDF generado
            
        Raises:
            NotFoundError: Si no se encuentra la solicitud
            ValidationError: Si faltan datos requeridos
        """       
        try:
            solicitud_id = str(data.get("solicitud_id") or "").strip()
            if not solicitud_id:
                raise ValidationError(
                    "Campo requerido faltante: solicitud_id",
                    details={"field": "solicitud_id"},
                )

            # 1. Obtener datos de la solicitud
            solicitud_data = data.get("solicitud_data", {})
            if not isinstance(solicitud_data, dict) or not solicitud_data:
                raise ValidationError(
                    "Campo requerido faltante: solicitud_data",
                    details={"field": "solicitud_data"},
                )
            
            # 2. Enriquecer con datos de convenio si aplica
            convenio_data = None
            if data.get("incluir_convenio", True):
                convenio_data = data.get("convenio_data", {})
            
            # 3. Preparar lista de firmantes
            firmantes_data = []
            if data.get("incluir_firmantes", True):
                firmantes_data = data.get("firmantes_data", [])
            
            # 4. Obtener datos del trabajador desde API externa
            trabajador_data = data.get("trabajador_data", {})
            
            # 5. Preparar contexto completo para el template
            context = self._preparar_contexto_template(
                solicitud=solicitud_data,
                trabajador=trabajador_data,
                convenio=convenio_data,
                firmantes=firmantes_data
            )
            
            # 6. Renderizar HTML desde template
            html_content = self._renderizar_template(context)
            
            # 7. Generar PDF desde HTML
            pdf_path = self._generar_pdf_desde_html(
                html_content=html_content,
                solicitud_id=solicitud_id
            )
            # 8. Sin BD: no se actualiza ninguna fuente externa.
            
            return {
                "success": True,
                "pdf_path": pdf_path,
                "pdf_filename": Path(pdf_path).name,
            }
            
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError("Error al generar el PDF de la solicitud", details={"error": str(e)})

    def _construir_nombre_completo(self, datos: Dict[str, Any]) -> str:
        """Construye nombre completo desde diferentes formatos de datos."""
        # Formato API externa (prinom, priape)
        if datos.get("prinom") or datos.get("priape"):
            nombres = [
                datos.get("prinom", ""),
                datos.get("segnom", ""),
                datos.get("priape", ""),
                datos.get("segape", "")
            ]
        # Formato interno (primer_nombre, primer_apellido)
        elif datos.get("primer_nombre") or datos.get("primer_apellido"):
            nombres = [
                datos.get("primer_nombre", ""),
                datos.get("segundo_nombre", ""),
                datos.get("primer_apellido", ""),
                datos.get("segundo_apellido", "")
            ]
        # Formato simple (nombres, apellidos)
        else:
            nombres = [
                datos.get("nombres", ""),
                datos.get("apellidos", "")
            ]
        
        return " ".join([n.strip() for n in nombres if n and n.strip()])

    def _preparar_contexto_template(
        self,
        solicitud: Dict[str, Any],
        trabajador: Dict[str, Any],
        convenio: Optional[Dict[str, Any]],
        firmantes: List[Dict[str, Any]]
    ) -> TemplateContext:
        """Prepara el contexto completo para renderizar el template."""
        
        # Validar datos requeridos antes de crear el contexto
        payload = solicitud.get("payload", {})
        solicitante_data = payload.get("solicitante", {})
        
        # Verificar datos críticos para el template
        if not solicitante_data.get("numero_identificacion"):
            logger.warning(
                "No se puede validar convenio - faltan datos",
                extra={
                    "tiene_nit": bool(payload.get("informacion_laboral", {}).get("empresa_nit")),
                    "tiene_cedula": bool(solicitante_data.get("numero_identificacion")),
                },
            )
        
        # Crear contexto usando las clases de datos
        return TemplateContext.from_mongodb_data(
            mongodb_data=solicitud,
            trabajador=trabajador,
            convenio=convenio,
            firmantes=firmantes
        )

    def _renderizar_template(self, context: TemplateContext) -> str:
        """Renderiza el template HTML con el contexto."""
        try:
            template = self.env.get_template('formato-credito-front.html.j2')
            return template.render(**context.__dict__)
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
    ) -> str:
        """Genera archivo PDF desde contenido HTML."""
        try:
            # Crear directorio para el solicitante si no existe
            solicitud_dir = self.storage_dir / "solicitudes" / solicitud_id
            solicitud_dir.mkdir(parents=True, exist_ok=True)
            
            # Nombre del archivo PDF
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_filename = f"solicitud_{solicitud_id}_{timestamp}.pdf"
            pdf_path = solicitud_dir / pdf_filename
            
            # Generar PDF con WeasyPrint
            HTML(string=html_content, base_url=str(self.template_dir)).write_pdf(
                str(pdf_path)
            )
            
            return str(pdf_path)
            
        except Exception as e:
            logger.exception("Error generando archivo PDF")
            raise ValidationError(
                "Error al generar el archivo PDF",
                details={"error": str(e)}
            )
