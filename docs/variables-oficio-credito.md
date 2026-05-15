# Variables para el Oficio de Crédito — Referencia Completa

## Estructura raíz del JSON de entrada

`CreditosGeneratorService.generar_pdf(data)` espera un diccionario con la siguiente estructura:

| Variable | Tipo | Requerido | Descripción |
|---|---|---|---|
| `solicitud_id` | `str` | **Sí** | ID único de la solicitud. Se usa para crear el directorio de salida en `temp_output/solicitudes/{solicitud_id}/` |
| `solicitud` | `dict` | **Sí** | Datos principales de la solicitud |
| `solicitante` | `dict` | **Sí** | Datos personales del solicitante |
| `laboral` | `dict` | No | Información laboral del solicitante |
| `economica` | `dict` | No | Información económica (activos, pasivos, gastos) |
| `ingresos` | `dict` | No | Ingresos laborales del solicitante |
| `descuentos` | `dict` | No | Descuentos por nómina |
| `conyuge` | `dict`/`list` | No | Datos del cónyuge. Si es `list`, se toma el primer elemento |
| `referencias` | `dict`/`list` | No | Referencias. Si es `dict` con claves `familiares`/`personales`, se normaliza a lista con campo `tipo` |
| `deudas` | `list` | No | Deudas del solicitante |
| `propiedades` | `list` | No | Propiedades del solicitante |
| `firmantes` | `list` | No | Firmantes del documento |
| `convenio` | `dict` | No | Datos del convenio empresarial. Requiere `representante_nombre` para mostrar bloque de firma |
| `proceso_firmado` | `dict` | No | Información de firma digital |
| `encabezado` | `dict` | No | Datos del encabezado (fecha radicado) |
| `pdf_metadata` | `dict` | No | Metadatos del PDF generado |
| `trabajador` | `dict` | No | Datos del trabajador (normalizado pero no usado en templates) |

---

## `solicitud` (Requerido — `numero_solicitud` obligatorio)

| Campo | Tipo | Descripción |
|---|---|---|
| `numero_solicitud` | `str` | **Requerido.** Número de la solicitud |
| `numero_comprobante` | `str` | Número de comprobante |
| `valor_solicitud` | `int/float/str` | Monto solicitado (filtro `\|currency`) |
| `categoria` | `str` | Categoría del crédito |
| `rol_en_solicitud` | `str` | `'solicitante'` o `'codeudor'` (checkboxes) |
| `plazo_meses` | `int/str` | Plazo en meses |
| `producto_tipo` | `str` | Código: `'04'`=Educación, `'05'`=Salud, `'02'`=Vivienda, `'07'`=Electrodomésticos, `'06'`=Hogar, `'08'`=Vestuario, `'03'`=Recreación |
| `ha_tenido_credito_comfaca` | `bool` | ¿Ha tenido crédito con Comfaca? |

---

## `solicitante` (Requerido)

| Campo | Tipo | Descripción |
|---|---|---|
| `fecha_vinculacion` | `str` (ISO date) | Fecha de vinculación a Comfaca |
| `tipo_documento` | `str` | `'CC'` o `'CE'` |
| `numero_documento` | `str` | Número de identificación |
| `fecha_nacimiento` | `str` (ISO date) | Fecha de nacimiento |
| `pais_nacimiento` | `str` | País de nacimiento (default: `'Colombia'`) |
| `nombre_completo` | `str` | Nombres y apellidos completos |
| `fecha_expedicion_documento` | `str` (ISO date) | Fecha de expedición del documento |
| `profesion_ocupacion` | `str` | Profesión u ocupación |
| `sexo` | `str` | `'M'` o `'F'` |
| `nivel_educativo` | `str` | `'primaria'`, `'bachillerato'`, `'tecnico'`, `'universitario'`, `'posgrado'`, `'ninguno'` |
| `barrio_residencia` | `str` | Barrio de residencia |
| `ciudad_residencia` | `str` | Ciudad de residencia |
| `pais_residencia` | `str` | País de residencia (default: `'Colombia'`) |
| `telefono_fijo` | `str` | Teléfono fijo |
| `telefono_movil` | `str` | Teléfono móvil |
| `email` | `str` | Correo electrónico |
| `tipo_vivienda` | `str` | `'propia'`, `'familiar'`, `'arrendada'` |
| `vive_con_nucleo_familiar` | `bool` | ¿Vive con núcleo familiar? |
| `personas_a_cargo` | `int` | Número de personas a cargo |

---

## `laboral`

| Campo | Tipo | Descripción |
|---|---|---|
| `empresa_razon_social` | `str` | Razón social de la empresa |
| `empresa_nit` | `str` | NIT de la empresa |
| `empresa_telefono` | `str` | Teléfono de la empresa |
| `empresa_direccion` | `str` | Dirección de la empresa |
| `empresa_ciudad` | `str` | Ciudad de la empresa |
| `cargo` | `str` | Cargo en la empresa |
| `fecha_ingreso` | `str` (ISO date) | Fecha de ingreso |
| `tipo_contrato` | `str` | Tipo de contrato |
| `nombramiento_o_pagador` | `str` | Nombramiento o nombre del pagador |
| `tiempo_servicio` | `int/str` | Tiempo de servicio |
| `tiempo_servicio_unidad` | `str` | Unidad (default: `'meses'`) |

---

## `convenio` (opcional)

| Campo | Tipo | Descripción |
|---|---|---|
| `representante_nombre` | `str` | Nombre del representante legal. **Requiere este campo para mostrar el bloque de firma en `informacion_laboral.html.j2`** |

---

## `ingresos`

| Campo | Tipo | Descripción |
|---|---|---|
| `salario_basico_mensual` | `int/float/str` | Salario básico mensual |
| `subsidio_transporte` | `int/float/str` | Subsidio de transporte (también puede venir de `descuentos.subsidio_transporte`) |
| `horas_extras` | `int/float/str` | Horas extras |
| `comisiones` | `int/float/str` | Comisiones |
| `otros_ingresos` | `int/float/str` | Otros ingresos laborales |
| `total_ingresos` | `int/float/str` | Total de ingresos |
| `total_neto` | `int/float/str` | Total neto recibido (también puede venir como `total_neto_recibido`) |

---

## `descuentos`

| Campo | Tipo | Descripción |
|---|---|---|
| `salud_pension` | `int/float/str` | Salud y pensión |
| `libranzas_comfaca` | `int/float/str` | Libranzas con Comfaca |
| `otras_libranzas` | `int/float/str` | Otras libranzas |
| `judiciales` | `int/float/str` | Descuentos judiciales |
| `otras_deducciones` | `int/float/str` | Otras deducciones de nómina |
| `total_gastos` | `int/float/str` | Total de gastos (también puede venir como `total_descuentos`) |

---

## `economica`

| Campo | Tipo | Descripción |
|---|---|---|
| `arrendamientos` | `int/float/str` | Ingresos por arrendamientos |
| `otros_ingresos` | `int/float/str` | Otros ingresos (también puede venir como `otros`) |
| `descripcion_ingresos` | `str` | Descripción de ingresos (también puede venir como `descripcion`) |
| `total_gastos` | `int/float/str` | Total gastos (también puede venir como `gastos_descripcion`) |
| `descripcion_gastos` | `str` | Descripción de gastos |
| `total_activos` | `int/float/str` | Total de activos |
| `total_pasivos` | `int/float/str` | Total de pasivos |

---

## `conyuge` (opcional)

| Campo | Tipo | Descripción |
|---|---|---|
| `numero_identificacion` | `str` | Número de identificación |
| `nombres_apellidos` | `str` | Nombre y apellidos |
| `ingresos_laborales` | `int/float/str` | Ingresos laborales |
| `trabaja` | `bool` | ¿Trabaja? (Si/No) |
| `empresa_nombre` | `str` | Nombre de la empresa |
| `empresa_direccion` | `str` | Dirección de la empresa |
| `email` | `str` | Correo electrónico |
| `empresa_telefono` | `str` | Teléfono de la empresa |
| `telefono_movil` | `str` | Teléfono móvil |

---

## `referencias` (lista de elementos)

Cada elemento debe tener:

| Campo | Tipo | Descripción |
|---|---|---|
| `tipo` | `str` | `'familiar'` o `'personal'` (añadido por el normalizador si se pasa como dict) |
| `nombre_apellidos` | `str` | Nombre y apellidos |
| `celular` | `str` | Número de celular |

**Nota:** Si se pasa como `dict` con claves `familiares` y `personales` (formato antiguo), el servicio lo normaliza automáticamente a lista plana con campo `tipo`.

---

## `deudas` (lista de elementos)

| Campo | Tipo | Descripción |
|---|---|---|
| `nombre_acreedor` | `str` | Nombre del acreedor |
| `concepto` | `str` | Concepto de la deuda |
| `valor_cuota` | `int/float/str` | Valor de la cuota mensual |
| `saldo_obligacion` | `int/float/str` | Saldo total de la obligación |

---

## `propiedades` (lista de elementos)

| Campo | Tipo | Descripción |
|---|---|---|
| `tipo_bien` | `str` | Tipo de bien (e.g. `'Vivienda'`, `'Vehículo'`) |
| `direccion_marca_placa` | `str` | Dirección, marca o placa |
| `ciudad` | `str` | Ciudad |
| `matricula_modelo` | `str` | Matrícula inmobiliaria o modelo |
| `valor_comercial` | `int/float/str` | Valor comercial |

---

## `firmantes` (lista de elementos, opcional)

| Campo | Tipo | Descripción |
|---|---|---|
| `tipo` | `str` | Tipo de firmante |
| `rol` | `str` | Rol del firmante |
| `nombre_completo` | `str` | Nombre completo |
| `numero_documento` | `str/int` | Número de documento (filtro `\|format_document`) |
| `email` | `str` | Correo electrónico |
| `orden` | `int/str` | Orden de firma |

---

## `encabezado`

| Campo | Tipo | Descripción |
|---|---|---|
| `fecha_radicado` | `str` (ISO date) | Fecha de radicado (filtro `\|format_date`) |

---

## `pdf_metadata` (opcional)

| Campo | Tipo | Descripción |
|---|---|---|
| `fecha_generacion` | `str` (ISO date) | Fecha de generación del documento |
| `solicitud_id` | `str` | ID de la solicitud |
| `version` | `str` | Versión del sistema (default: `'1.0'`) |

---

## Renombrado automático de campos (normalización)

El servicio aplica los siguientes renombrados si los campos originales existen:

| Campo original | Campo normalizado | Ubicación |
|---|---|---|
| `economica.otros` | `economica.otros_ingresos` | `creditos_generator_service.py:212-213` |
| `economica.descripcion` | `economica.descripcion_ingresos` | `creditos_generator_service.py:214-215` |
| `economica.gastos_descripcion` | `economica.descripcion_gastos` | `creditos_generator_service.py:216-217` |
| `descuentos.subsidio_transporte` | `ingresos.subsidio_transporte` | `creditos_generator_service.py:223-224` |
| `ingresos.total_neto_recibido` | `ingresos.total_neto` | `creditos_generator_service.py:225-226` |
| `descuentos.total_descuentos` | `descuentos.total_gastos` | `creditos_generator_service.py:230-231` |
| `referencias` dict con `familiares`/`personales` | Lista plana con `tipo` | `creditos_generator_service.py:234-246` |
| `conyuge` como `list` | `dict` (primer elemento) | `creditos_generator_service.py:249-251` |

---

## Filtros Jinja2 personalizados

El `CreditosGeneratorService` registra los siguientes filtros:

| Filtro | Función | Descripción |
|---|---|---|
| `\|currency` | `format_currency` | Formatea como moneda colombiana: `$ 1.500.000` |
| `\|format_date` | `format_date` | Formatea fecha ISO (acepta formato opcional) |
| `\|format_document` | `format_document` | Formatea número de documento con puntos: `1.234.567` |

---

## Ejemplo de payload completo

```json
{
  "solicitud_id": "000001-20260206",
  "solicitud": {
    "numero_solicitud": "000001-20260206",
    "numero_comprobante": "COMP-2026-001",
    "valor_solicitud": 5000000,
    "categoria": "Crédito Ordinario",
    "rol_en_solicitud": "solicitante",
    "plazo_meses": 12,
    "producto_tipo": "04",
    "ha_tenido_credito_comfaca": false
  },
  "solicitante": {
    "fecha_vinculacion": "2020-01-15",
    "tipo_documento": "CC",
    "numero_documento": "12345678",
    "fecha_nacimiento": "1990-05-15",
    "pais_nacimiento": "Colombia",
    "nombre_completo": "Juan Pérez García",
    "fecha_expedicion_documento": "2015-03-20",
    "profesion_ocupacion": "Ingeniero de Sistemas",
    "sexo": "M",
    "nivel_educativo": "universitario",
    "barrio_residencia": "San José",
    "ciudad_residencia": "Florencia",
    "pais_residencia": "Colombia",
    "telefono_fijo": "6081234567",
    "telefono_movil": "3201234567",
    "email": "juan.perez@email.com",
    "tipo_vivienda": "propia",
    "vive_con_nucleo_familiar": true,
    "personas_a_cargo": 2
  },
  "laboral": {
    "empresa_razon_social": "Empresa XYZ S.A.S",
    "empresa_nit": "1234567890",
    "empresa_telefono": "6087654321",
    "empresa_direccion": "Carrera 10 # 20-30",
    "empresa_ciudad": "Florencia",
    "cargo": "Desarrollador Senior",
    "fecha_ingreso": "2021-06-01",
    "tipo_contrato": "Término Indefinido",
    "nombramiento_o_pagador": "Recursos Humanos",
    "tiempo_servicio": 48,
    "tiempo_servicio_unidad": "meses"
  },
  "ingresos": {
    "salario_basico_mensual": 3500000,
    "subsidio_transporte": 140000,
    "horas_extras": 250000,
    "comisiones": 150000,
    "otros_ingresos": 100000,
    "total_ingresos": 4140000,
    "total_neto": 2900000
  },
  "descuentos": {
    "salud_pension": 560000,
    "libranzas_comfaca": 0,
    "otras_libranzas": 200000,
    "judiciales": 0,
    "otras_deducciones": 480000,
    "total_gastos": 1240000
  },
  "economica": {
    "arrendamientos": 0,
    "otros_ingresos": 0,
    "descripcion_ingresos": "Ingresos adicionales por freelance",
    "total_gastos": 800000,
    "descripcion_gastos": "Gastos familiares mensuales",
    "total_activos": 45000000,
    "total_pasivos": 15000000
  },
  "conyuge": {
    "numero_identificacion": "87654321",
    "nombres_apellidos": "María López Rodríguez",
    "ingresos_laborales": 2000000,
    "trabaja": true,
    "empresa_nombre": "Comercial ABC",
    "empresa_direccion": "Calle 5 # 10-15",
    "email": "maria.lopez@email.com",
    "empresa_telefono": "6081112233",
    "telefono_movil": "3101234567"
  },
  "referencias": [
    {
      "tipo": "familiar",
      "nombre_apellidos": "Pedro Pérez López",
      "celular": "3123456789"
    },
    {
      "tipo": "familiar",
      "nombre_apellidos": "Ana Pérez López",
      "celular": "3156789012"
    },
    {
      "tipo": "personal",
      "nombre_apellidos": "Carlos Martínez",
      "celular": "3209876543"
    }
  ],
  "deudas": [
    {
      "nombre_acreedor": "Banco de Bogotá",
      "concepto": "Tarjeta de Crédito",
      "valor_cuota": 150000,
      "saldo_obligacion": 3500000
    },
    {
      "nombre_acreedor": "Coopechocó",
      "concepto": "Crédito de Consumo",
      "valor_cuota": 200000,
      "saldo_obligacion": 5000000
    }
  ],
  "propiedades": [
    {
      "tipo_bien": "Vivienda",
      "direccion_marca_placa": "Carrera 15 # 25-40, Florencia",
      "ciudad": "Florencia",
      "matricula_modelo": "NO APLICA",
      "valor_comercial": 65000000
    }
  ],
  "firmantes": [
    {
      "tipo": "solicitante",
      "rol": "deudor",
      "nombre_completo": "Juan Pérez García",
      "numero_documento": "12345678",
      "email": "juan.perez@email.com",
      "orden": 1
    }
  ],
  "convenio": {
    "representante_nombre": "Luis Fernando Gómez"
  },
  "proceso_firmado": {
    "proveedor": "Certifico",
    "estado": "completado",
    "transaccion_id": "TXN-2026-001234",
    "fecha_inicio": "2026-02-06T10:30:00"
  },
  "encabezado": {
    "fecha_radicado": "2026-02-06"
  },
  "pdf_metadata": {
    "fecha_generacion": "2026-02-06",
    "solicitud_id": "000001-20260206",
    "version": "1.0"
  }
}
```

---

## Ejemplo de payload mínimo

```json
{
  "solicitud_id": "000001-20260206",
  "solicitud": {
    "numero_solicitud": "000001-20260206",
    "valor_solicitud": 5000000,
    "plazo_meses": 12,
    "producto_tipo": "04"
  },
  "solicitante": {
    "tipo_documento": "CC",
    "numero_documento": "12345678",
    "nombre_completo": "Juan Pérez García",
    "fecha_nacimiento": "1990-05-15"
  }
}
```