"""Middleware para validación HTTP Basic usando variables en .env.

Exige que las variables BASIC_USER y BASIC_PASS estén presentes en el entorno
cuando se registra el middleware. Si faltan, lanza RuntimeError para forzar
la configuración.
"""
from typing import Iterable, Optional
import os
import base64
import hmac
from flask import request, Response


def _unauthorized_response() -> Response:
    return Response('Unauthorized', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})


def register_basic_auth(app, config, exempt_paths: Optional[Iterable[str]] = None):
    """Registra un before_request que valida Basic Auth contra variables en el entorno.

    - Requiere BASIC_USER y BASIC_PASS en el entorno (cargadas desde .env).
    - exempt_paths: lista opcional de rutas que no requieren autenticación.
    """
    if exempt_paths is None:
        exempt_paths = set()
    else:
        exempt_paths = set(exempt_paths)

    user = config['BASIC_USER']
    pwd = config['BASIC_PASSWORD']
    if not user or not pwd:
        raise RuntimeError('BASIC_USER and BASIC_PASS must be set in environment for Basic Auth')

    def _check_basic_auth():
        # Allow CORS preflight and exempt paths
        if request.method == 'OPTIONS':
            return None
        path = request.path or ''
        if path in exempt_paths:
            return None

        # Use custom header name 'Authorization' per requirements
        auth = request.headers.get('Authorization')
        if not auth or not auth.lower().startswith('basic '):
            return _unauthorized_response()

        try:
            token = auth.split(None, 1)[1]
            decoded = base64.b64decode(token, validate=True).decode('utf-8')
            incoming_user, incoming_pwd = decoded.split(':', 1)
        except Exception:
            return _unauthorized_response()

        # Use compare_digest to avoid timing attacks
        if not (hmac.compare_digest(incoming_user, user) and hmac.compare_digest(incoming_pwd, pwd)):
            return _unauthorized_response()

        return None

    app.before_request(_check_basic_auth)
