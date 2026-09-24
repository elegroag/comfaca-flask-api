from __future__ import annotations

import base64
import logging
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, Undefined
from weasyprint import HTML

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    def __init__(self, message: str, *, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.details = details or {}


class CreditosV2GeneratorService:
    """
    Genera PDFs del formulario de crédito formato v2 (templates_creditos_v2).
    Reutiliza el mismo contrato JSON de CreditosGeneratorService.
    """

    def __init__(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        self.template_dir = project_root / "templates_creditos_v2"
        self.storage_dir = project_root / "temp_output"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        class SilentUndefined(Undefined):
            def __str__(self) -> str:
                return ""

            def __getitem__(self, key: str) -> "SilentUndefined":
                return SilentUndefined(key)

            def __call__(self, *args: Any, **kwargs: Any) -> str:
                return ""

            def __iter__(self) -> Any:
                return iter([])

        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            undefined=SilentUndefined,
        )
        self._registrar_filtros()

    def _registrar_filtros(self) -> None:
        def format_currency(value: Any) -> str:
            if value is None or value == "":
                return "$ 0"
            try:
                return "${:,.0f}".format(float(value)).replace(",", ".")
            except (ValueError, TypeError):
                return "$ 0"

        def format_date(value: Any, format_str: str = "%d/%m/%Y") -> str:
            if not value:
                return ""
            try:
                if isinstance(value, str):
                    date_obj = datetime.fromisoformat(value.replace("Z", "+00:00"))
                elif isinstance(value, datetime):
                    date_obj = value
                else:
                    return ""
                return date_obj.strftime(format_str)
            except (ValueError, TypeError) as e:
                logger.warning("Error formateando fecha: %s", e, extra={"value": str(value)})
                return str(value)

        def format_document(value: Any) -> str:
            if not value:
                return ""
            try:
                return "{:,.0f}".format(float(value)).replace(",", ".")
            except (ValueError, TypeError) as e:
                logger.warning("Error formateando documento: %s", e, extra={"value": str(value)})
                return str(value)

        def date_parts(value: Any) -> Dict[str, str]:
            empty = {"day": "", "month": "", "year": ""}
            if not value:
                return empty
            # Ya viene separado desde el cliente Nuxt (day/month/year o dia/mes/anio)
            if isinstance(value, dict):
                day = str(value.get("day") or value.get("dia") or "").strip()
                month = str(value.get("month") or value.get("mes") or "").strip()
                year = str(value.get("year") or value.get("anio") or "").strip()
                if day or month or year:
                    return {
                        "day": day.zfill(2) if day.isdigit() else day,
                        "month": month.zfill(2) if month.isdigit() else month,
                        "year": year,
                    }
                return empty
            try:
                if isinstance(value, str):
                    date_obj = datetime.fromisoformat(value.replace("Z", "+00:00"))
                elif isinstance(value, datetime):
                    date_obj = value
                else:
                    return empty
                return {
                    "day": f"{date_obj.day:02d}",
                    "month": f"{date_obj.month:02d}",
                    "year": str(date_obj.year),
                }
            except (ValueError, TypeError):
                return empty

        self.env.filters["currency"] = format_currency
        self.env.filters["format_date"] = format_date
        self.env.filters["format_document"] = format_document
        self.env.filters["date_parts"] = date_parts

    def renderizar_html(
        self,
        data: Dict[str, Any],
        *,
        assets_base_url: Optional[str] = None,
    ) -> str:
        """
        Renderiza el HTML del formato v2 para previsualización/pruebas.

        Usa el mismo contrato JSON que generar_pdf. Si se pasa assets_base_url
        (p. ej. '/api/creditos/v2/assets'), las hojas de estilo se resuelven
        vía HTTP para vista en navegador.
        """
        self._validar_estructura_solicitud(data)
        contexto = self._preparar_contexto(data)
        self._validar_contexto_template(contexto)
        return self._renderizar_template(contexto, assets_base_url=assets_base_url)

    def generar_pdf(self, data: Dict[str, Any]) -> Dict[str, Any]:
        solicitud_id = str(data.get("solicitud_id") or "").strip()
        if not solicitud_id:
            raise ValueError("Campo requerido faltante: solicitud_id")

        logger.info(
            "Iniciando generación de PDF créditos v2",
            extra={
                "solicitud_id": solicitud_id,
                "tiene_convenio": data.get("convenio") is not None,
                "cantidad_firmantes": len(data.get("firmantes", [])),
            },
        )

        html_content = self.renderizar_html(data)
        api_content, api_path, api_filename = self._generar_pdf_desde_html(
            html_content=html_content,
            solicitud_id=solicitud_id,
        )

        return {
            "api_content": api_content,
            "api_path": api_path,
            "api_filename": api_filename,
        }

    def _validar_estructura_solicitud(self, data: Dict[str, Any]) -> None:
        for campo in ("solicitud", "solicitante"):
            if campo not in data or not data[campo]:
                raise ValueError(f"Campo requerido faltante: {campo}")

        solicitud_info = data["solicitud"]
        if not isinstance(solicitud_info, dict):
            raise ValueError("Estructura inválida: solicitud debe ser un diccionario")

        if not solicitud_info.get("numero_solicitud"):
            raise ValueError("Campo requerido faltante: numero_solicitud")

    def _preparar_contexto(self, data: Dict[str, Any]) -> Dict[str, Any]:
        ctx = deepcopy(data)

        economica = ctx.get("economica", {}) or {}
        if "otros" in economica and "otros_ingresos" not in economica:
            economica["otros_ingresos"] = economica.pop("otros")
        if "descripcion" in economica and "descripcion_ingresos" not in economica:
            economica["descripcion_ingresos"] = economica.pop("descripcion")
        if "gastos_descripcion" in economica and "descripcion_gastos" not in economica:
            economica["descripcion_gastos"] = economica.pop("gastos_descripcion")
        ctx["economica"] = economica

        ingresos = ctx.get("ingresos", {}) or {}
        descuentos = ctx.get("descuentos", {}) or {}
        if "subsidio_transporte" not in ingresos and "subsidio_transporte" in descuentos:
            ingresos["subsidio_transporte"] = descuentos.pop("subsidio_transporte")
        if "total_neto_recibido" in ingresos and "total_neto" not in ingresos:
            ingresos["total_neto"] = ingresos.pop("total_neto_recibido")
        ctx["ingresos"] = ingresos

        if "total_descuentos" in descuentos and "total_gastos" not in descuentos:
            descuentos["total_gastos"] = descuentos.pop("total_descuentos")
        ctx["descuentos"] = descuentos

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

        conyuge_raw = ctx.get("conyuge")
        if isinstance(conyuge_raw, list):
            ctx["conyuge"] = conyuge_raw[0] if conyuge_raw else None

        laboral = ctx.get("laboral", {}) or {}
        if not laboral.get("mes") and laboral.get("fecha_ingreso"):
            try:
                fecha = datetime.fromisoformat(
                    str(laboral["fecha_ingreso"]).replace("Z", "+00:00")
                )
                laboral.setdefault("mes", f"{fecha.month:02d}")
                laboral.setdefault("anio", str(fecha.year))
            except (ValueError, TypeError):
                pass
        ctx["laboral"] = laboral

        ctx.setdefault("encabezado", {})
        ctx.setdefault("ingresos", {})
        ctx.setdefault("descuentos", {})
        ctx.setdefault("economica", {})
        ctx.setdefault("propiedades", [])
        ctx.setdefault("deudas", [])
        ctx.setdefault("referencias", [])

        ctx["propiedades_por_tipo"] = self._agrupar_propiedades(ctx.get("propiedades") or [])
        ctx["referencia_familiar"] = self._primera_referencia(ctx.get("referencias") or [], "familiar")
        ctx["referencia_personal"] = self._primera_referencia(ctx.get("referencias") or [], "personal")
        ctx["documentos_entregados_codigos"] = self._codigos_documentos_entregados(
            ctx.get("documentos_entregados")
        )

        return ctx

    def _codigos_documentos_entregados(self, documentos: Any) -> List[str]:
        """Códigos tipdoc de SISU normalizados a 2 dígitos ('5' -> '05')."""
        if not isinstance(documentos, list):
            return []
        codigos: List[str] = []
        for doc in documentos:
            if not isinstance(doc, dict):
                continue
            codigo = str(doc.get("documento_requerido_id") or "").strip()
            if codigo:
                codigos.append(codigo.zfill(2))
        return codigos

    def _agrupar_propiedades(self, propiedades: List[Dict[str, Any]]) -> Dict[str, Optional[Dict[str, Any]]]:
        result: Dict[str, Optional[Dict[str, Any]]] = {
            "vivienda": None,
            "vehiculo": None,
            "otros": None,
        }
        for prop in propiedades:
            if not isinstance(prop, dict):
                continue
            tipo = str(prop.get("tipo_bien") or "").lower()
            if "vivienda" in tipo and result["vivienda"] is None:
                result["vivienda"] = prop
            elif "vehic" in tipo and result["vehiculo"] is None:
                result["vehiculo"] = prop
            elif result["otros"] is None and "vivienda" not in tipo and "vehic" not in tipo:
                result["otros"] = prop
        return result

    def _primera_referencia(
        self,
        referencias: List[Dict[str, Any]],
        tipo: str,
    ) -> Optional[Dict[str, Any]]:
        for ref in referencias:
            if isinstance(ref, dict) and ref.get("tipo") == tipo:
                return ref
        return None

    def _validar_contexto_template(self, context: Dict[str, Any]) -> None:
        solicitante = context.get("solicitante", {})
        solicitud = context.get("solicitud", {})

        if not solicitante.get("numero_documento"):
            logger.warning("Contexto v2 sin número de identificación del solicitante")
        if not solicitante.get("nombre_completo"):
            logger.warning("Contexto v2 sin nombre del solicitante")

        if not solicitud.get("numero_solicitud"):
            raise ValidationError(
                "Contexto inválido: falta numero_solicitud en los datos de solicitud",
                details={"field": "solicitud.numero_solicitud"},
            )

        firmantes = context.get("firmantes", [])
        if firmantes and not isinstance(firmantes, list):
            raise ValidationError(
                "Estructura inválida: firmantes debe ser una lista",
                details={"expected": "list", "received": type(firmantes).__name__},
            )

    def _renderizar_template(
        self,
        context: Dict[str, Any],
        *,
        assets_base_url: Optional[str] = None,
    ) -> str:
        try:
            template = self.env.get_template("formato-credito.html.j2")
            template_context = dict(context)
            template_context["template_dir"] = (
                assets_base_url.rstrip("/")
                if assets_base_url
                else str(self.template_dir)
            )
            return template.render(**template_context)
        except Exception as e:
            logger.exception("Error renderizando template créditos v2")
            raise ValueError(f"Error al generar el documento HTML: {str(e)}") from e

    def _generar_pdf_desde_html(
        self,
        html_content: str,
        solicitud_id: str,
    ) -> tuple[str, str, str]:
        try:
            solicitud_dir = self.storage_dir / "solicitudes_v2" / solicitud_id
            solicitud_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_filename = f"solicitud_v2_{solicitud_id}_{timestamp}.pdf"
            pdf_path = solicitud_dir / pdf_filename

            pdf_bytes = HTML(
                string=html_content,
                base_url=str(self.template_dir),
            ).write_pdf()

            with open(pdf_path, "wb") as f:
                f.write(pdf_bytes)

            pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

            logger.info(
                "PDF créditos v2 generado exitosamente",
                extra={
                    "solicitud_id": solicitud_id,
                    "pdf_path": str(pdf_path),
                    "pdf_size_bytes": len(pdf_bytes),
                },
            )

            return pdf_base64, str(pdf_path), pdf_filename
        except Exception as e:
            logger.exception("Error generando PDF créditos v2")
            raise ValueError(f"Error al generar el archivo PDF: {str(e)}") from e
