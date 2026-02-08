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
    solicitud_id: str
    
    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> 'EncabezadoData':
        encabezado = payload.get("encabezado", {})
        return cls(
            fecha_radicado=encabezado.get("fecha_radicado", ""),
            solicitud_id=encabezado.get("solicitud_id", "")
        )


@dataclass
class SolicitanteData:
    """Datos del solicitante para el template."""
    fecha_vinculacion: str
    tipo_documento: str
    numero_documento: str
    fecha_nacimiento: str
    pais_nacimiento: str
    nombre_completo: str
    fecha_expedicion_documento: str
    profesion_ocupacion: str
    sexo: str
    nivel_educativo: str
    barrio_residencia: str
    ciudad_residencia: str
    pais_residencia: str
    telefono_fijo: str
    telefono_movil: str
    email: str
    tipo_vivienda: str
    vive_con_nucleo_familiar: bool
    personas_a_cargo: int
    direccion_residencia: str
    
    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> 'SolicitanteData':
        solicitante = payload.get("solicitante", {})
        
        return cls(
            fecha_vinculacion=solicitante.get("fecha_vinculacion", ""),
            tipo_documento=solicitante.get("tipo_documento", ""),
            numero_documento=solicitante.get("numero_documento", ""),
            fecha_nacimiento=solicitante.get("fecha_nacimiento", ""),
            pais_nacimiento=solicitante.get("pais_nacimiento", ""),
            nombre_completo=solicitante.get("nombre_completo", ""),
            fecha_expedicion_documento=solicitante.get("fecha_expedicion_documento", ""),
            profesion_ocupacion=solicitante.get("profesion_ocupacion", ""),
            sexo=solicitante.get("sexo", ""),
            nivel_educativo=solicitante.get("nivel_educativo", ""),
            barrio_residencia=solicitante.get("barrio_residencia", ""),
            ciudad_residencia=solicitante.get("ciudad_residencia", ""),
            pais_residencia=solicitante.get("pais_residencia", ""),
            telefono_fijo=solicitante.get("telefono_fijo", ""),
            telefono_movil=solicitante.get("telefono_movil", ""),
            email=solicitante.get("email", ""),
            tipo_vivienda=solicitante.get("tipo_vivienda", ""),
            vive_con_nucleo_familiar=solicitante.get("vive_con_nucleo_familiar", False),
            personas_a_cargo=solicitante.get("personas_a_cargo", 0),
            direccion_residencia=solicitante.get("direccion_residencia", "")
        )


@dataclass
class SolicitudData:
    """Datos de la solicitud para el template."""
    numero_solicitud: str
    numero_comprobante: str
    valor_solicitud: int
    categoria: str
    rol_en_solicitud: str
    plazo_meses: int
    producto_tipo: str
    ha_tenido_credito_comfaca: bool
    
    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> 'SolicitudData':
        solicitud = payload.get("solicitud", {})
        
        # Función helper para conversión segura a int
        def safe_int(value, default=0):
            try:
                return int(value) if value else default
            except (ValueError, TypeError) as e:
                logger.warning(f"Error convirtiendo a int: {e}", extra={"value": str(value)})
                return default
        
        return cls(
            numero_solicitud=solicitud.get("numero_solicitud", ""),
            numero_comprobante=solicitud.get("numero_comprobante", ""),
            valor_solicitud=safe_int(solicitud.get("valor_solicitud")),
            categoria=solicitud.get("categoria", ""),
            rol_en_solicitud=solicitud.get("rol_en_solicitud", ""),
            plazo_meses=safe_int(solicitud.get("plazo_meses")),
            producto_tipo=solicitud.get("producto_tipo", ""),
            ha_tenido_credito_comfaca=solicitud.get("ha_tenido_credito_comfaca", False)
        )


@dataclass
class LaboralData:
    """Datos laborales para el template."""
    empresa_razon_social: str
    empresa_nit: str
    empresa_telefono: str
    empresa_direccion: str
    empresa_ciudad: str
    cargo: str
    fecha_ingreso: str
    tipo_contrato: str
    nombramiento_o_pagador: str
    tiempo_servicio: int
    tiempo_servicio_unidad: str
    
    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> 'LaboralData':
        laboral = payload.get("laboral", {})
        
        def safe_int(value, default=0):
            try:
                return int(value) if value else default
            except (ValueError, TypeError):
                return default
        
        return cls(
            empresa_razon_social=laboral.get("empresa_razon_social", ""),
            empresa_nit=laboral.get("empresa_nit", ""),
            empresa_telefono=laboral.get("empresa_telefono", ""),
            empresa_direccion=laboral.get("empresa_direccion", ""),
            empresa_ciudad=laboral.get("empresa_ciudad", ""),
            cargo=laboral.get("cargo", ""),
            fecha_ingreso=laboral.get("fecha_ingreso", ""),
            tipo_contrato=laboral.get("tipo_contrato", ""),
            nombramiento_o_pagador=laboral.get("nombramiento_o_pagador", ""),
            tiempo_servicio=safe_int(laboral.get("tiempo_servicio")),
            tiempo_servicio_unidad=laboral.get("tiempo_servicio_unidad", "")
        )


@dataclass
class EconomicaData:
    """Datos económicos para el template."""
    arrendamientos: float
    otros_ingresos: float
    descripcion_ingresos: str
    total_gastos: float
    descripcion_gastos: str
    total_activos: float
    total_pasivos: float
    
    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> 'EconomicaData':
        economica = payload.get("economica", {})
        
        def safe_float(value, default=0):
            try:
                return float(value) if value else default
            except (ValueError, TypeError):
                return default
        
        return cls(
            arrendamientos=safe_float(economica.get("arrendamientos")),
            otros_ingresos=safe_float(economica.get("otros_ingresos")),
            descripcion_ingresos=economica.get("descripcion_ingresos", ""),
            total_gastos=safe_float(economica.get("total_gastos")),
            descripcion_gastos=economica.get("descripcion_gastos", ""),
            total_activos=safe_float(economica.get("total_activos")),
            total_pasivos=safe_float(economica.get("total_pasivos"))
        )


@dataclass
class IngresosData:
    """Datos de ingresos para el template."""
    salario_basico_mensual: float
    subsidio_transporte: float
    horas_extras: float
    comisiones: float
    otros_ingresos: float
    total_ingresos: float
    total_neto: float
    
    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> 'IngresosData':
        ingresos = payload.get("ingresos", {})
        
        def safe_float(value, default=0):
            try:
                return float(value) if value else default
            except (ValueError, TypeError):
                return default
        
        return cls(
            salario_basico_mensual=safe_float(ingresos.get("salario_basico_mensual")),
            subsidio_transporte=safe_float(ingresos.get("subsidio_transporte")),
            horas_extras=safe_float(ingresos.get("horas_extras")),
            comisiones=safe_float(ingresos.get("comisiones")),
            otros_ingresos=safe_float(ingresos.get("otros_ingresos")),
            total_ingresos=safe_float(ingresos.get("total_ingresos")),
            total_neto=safe_float(ingresos.get("total_neto"))
        )


@dataclass
class DescuentosData:
    """Datos de descuentos para el template."""
    salud_pension: float
    libranzas_comfaca: float
    otras_libranzas: float
    judiciales: float
    otras_deducciones: float
    total_gastos: float
    
    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> 'DescuentosData':
        descuentos = payload.get("descuentos", {})
        
        def safe_float(value, default=0):
            try:
                return float(value) if value else default
            except (ValueError, TypeError):
                return default
        
        return cls(
            salud_pension=safe_float(descuentos.get("salud_pension")),
            libranzas_comfaca=safe_float(descuentos.get("libranzas_comfaca")),
            otras_libranzas=safe_float(descuentos.get("otras_libranzas")),
            judiciales=safe_float(descuentos.get("judiciales")),
            otras_deducciones=safe_float(descuentos.get("otras_deducciones")),
            total_gastos=safe_float(descuentos.get("total_gastos"))
        )


@dataclass
class ConyugeData:
    """Datos del cónyuge para el template."""
    numero_identificacion: str
    nombres_apellidos: str
    ingresos_laborales: float
    trabaja: bool
    empresa_nombre: str
    empresa_direccion: str
    email: str
    empresa_telefono: str
    telefono_movil: str
    
    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> 'ConyugeData':
        conyuge = payload.get("conyuge", {})
        
        def safe_float(value, default=0):
            try:
                return float(value) if value else default
            except (ValueError, TypeError):
                return default
        
        return cls(
            numero_identificacion=conyuge.get("numero_identificacion", ""),
            nombres_apellidos=conyuge.get("nombres_apellidos", ""),
            ingresos_laborales=safe_float(conyuge.get("ingresos_laborales")),
            trabaja=conyuge.get("trabaja", False),
            empresa_nombre=conyuge.get("empresa_nombre", ""),
            empresa_direccion=conyuge.get("empresa_direccion", ""),
            email=conyuge.get("email", ""),
            empresa_telefono=conyuge.get("empresa_telefono", ""),
            telefono_movil=conyuge.get("telefono_movil", "")
        )


@dataclass
class TemplateContext:
    """Estructura completa de datos para el template."""
    solicitud: SolicitudData
    solicitante: SolicitanteData
    laboral: LaboralData
    economica: EconomicaData
    ingresos: IngresosData
    descuentos: DescuentosData
    conyuge: Optional[ConyugeData]
    referencias: List[Dict[str, Any]]
    deudas: List[Dict[str, Any]]
    propiedades: List[Dict[str, Any]]
    firmantes: List[Dict[str, Any]]
    convenio: Optional[Dict[str, Any]]
    proceso_firmado: Dict[str, Any]
    encabezado: EncabezadoData
    pdf_metadata: Dict[str, Any]
    trabajador: Dict[str, Any]
    
    @classmethod
    def from_data(
        cls, 
        data: Dict[str, Any],
        trabajador: Dict[str, Any]
    ) -> 'TemplateContext':
        """Crea TemplateContext desde datos."""
        
        return cls(
            solicitud=SolicitudData.from_payload(data),
            solicitante=SolicitanteData.from_payload(data),
            laboral=LaboralData.from_payload(data),
            economica=EconomicaData.from_payload(data),
            ingresos=IngresosData.from_payload(data),
            descuentos=DescuentosData.from_payload(data),
            conyuge=ConyugeData.from_payload(data) if data.get("conyuge") else None,
            referencias=data.get("referencias", []),
            deudas=data.get("deudas", []),
            propiedades=data.get("propiedades", []),
            firmantes=data.get("firmantes", []),
            convenio=data.get("convenio"),
            proceso_firmado=data.get("proceso_firmado", {}),
            encabezado=EncabezadoData.from_payload(data),
            pdf_metadata=data.get("pdf_metadata", {}),
            trabajador=trabajador
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
        try:
            # Validar y extraer datos de entrada
            solicitud_id = str(data.get("solicitud_id") or "").strip()
            if not solicitud_id:
                logger.error("Solicitud ID faltante en datos de entrada")
                raise ValidationError(
                    "Campo requerido faltante: solicitud_id",
                    details={"field": "solicitud_id"},
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
            
            # Crear TemplateContext usando las clases de datos estructuradas
            context = TemplateContext.from_data(
                data=data,
                trabajador=trabajador_data
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

    def _validar_estructura_solicitud(self, data: Dict[str, Any]) -> None:
        """Valida la estructura básica de los datos de la solicitud."""
        if not isinstance(data, dict):
            raise ValidationError(
                "Estructura inválida: los datos deben ser un diccionario",
                details={"expected": "dict", "received": type(data).__name__}
            )
        
        # Validar campos requeridos
        campos_requeridos = ["solicitud", "solicitante"]
        for campo in campos_requeridos:
            if campo not in data or not data[campo]:
                raise ValidationError(
                    f"Campo requerido faltante: {campo}",
                    details={"missing_field": campo}
                )
        
        # Validar estructura de solicitud
        solicitud_info = data["solicitud"]
        if not isinstance(solicitud_info, dict):
            raise ValidationError(
                "Estructura inválida: solicitud debe ser un diccionario",
                details={"expected": "dict", "received": type(solicitud_info).__name__}
            )
        
        # Validar campos críticos de solicitud
        if not solicitud_info.get("numero_solicitud"):
            logger.error(
                "Campo crítico faltante: numero_solicitud",
                extra={"solicitud": solicitud_info}
            )
            raise ValidationError(
                "Campo requerido faltante: numero_solicitud",
                details={"field": "solicitud.numero_solicitud"}
            )
    
    def _validar_contexto_template(self, context: TemplateContext) -> None:
        """Valida que el contexto del template tenga todos los datos necesarios."""
        # Validar datos del solicitante
        if not context.solicitante.numero_documento:
            logger.warning("Contexto sin número de identificación del solicitante")
        
        if not context.solicitante.nombre_completo:
            logger.warning("Contexto sin nombre del solicitante")
        
        # Validar datos de la solicitud
        if not context.solicitud.numero_solicitud:
            logger.error(
                "Contexto inválido: falta numero_solicitud",
                extra={"solicitud": context.solicitud.numero_solicitud}
            )
            raise ValidationError(
                "Contexto inválido: falta numero_solicitud en los datos de solicitud",
                details={"field": "context.solicitud.numero_solicitud"}
            )
        
        # Validar estructura de firmantes
        if context.firmantes and not isinstance(context.firmantes, list):
            raise ValidationError(
                "Estructura inválida: firmantes debe ser una lista",
                details={"expected": "list", "received": type(context.firmantes).__name__}
            )
        
        logger.info(
            "Contexto validado exitosamente",
            extra={
                "numero_solicitud": context.solicitud.numero_solicitud,
                "solicitante": context.solicitante.nombre_completo,
                "tiene_convenio": context.convenio is not None,
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
