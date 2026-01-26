#!/usr/bin/env python3
"""
Configuración de Gunicorn con parámetros optimizados para generación de PDFs.
"""

# Configuración de workers y timeouts optimizados
bind = "0.0.0.0:80"
workers = 2  # Reducido para evitar sobrecarga en generación de PDFs
worker_class = "sync"  # Sync es más estable para WeasyPrint
worker_connections = 1000
timeout = 120  # 2 minutos para generación de PDFs complejos
keepalive = 30
max_requests = 1000  # Reiniciar workers después de 1000 peticiones
max_requests_jitter = 50  # Variación aleatoria para evitar reinicios simultáneos
preload_app = True
daemon = False
user = "app"
group = "app"
tmp_upload_dir = "/tmp"

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Optimización de memoria
worker_tmp_dir = "/dev/shm"

# Límites de recursos
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
