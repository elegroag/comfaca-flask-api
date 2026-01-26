#!/bin/bash
# Script para reconstruir y probar el servicio Flask API con las optimizaciones aplicadas

echo "🔧 Reconstruyendo el contenedor con las optimizaciones..."

# Detener y eliminar contenedor existente
docker compose down

# Limpiar imágenes antiguas
docker compose build --no-cache

# Iniciar el servicio
echo "🚀 Iniciando el servicio..."
docker compose up -d

# Esperar a que el servicio esté listo
echo "⏳ Esperando a que el servicio esté listo..."
sleep 15

# Verificar health check
echo "🏥 Verificando salud del servicio..."
docker compose exec flask-api curl -fsS http://0.0.0.0:80/api/health

echo ""
echo "📊 Mostrando logs recientes..."
docker compose logs --tail=20 flask-api

echo ""
echo "🧪 Realizando prueba de generación de PDF..."
# Prueba simple de generación de PDF
curl -X POST http://localhost:5000/api/generate-pdf \
  -H "Content-Type: application/json" \
  -u admin:$(grep BASIC_AUTH_PASSWORD .env | cut -d'=' -f2) \
  -d '{
    "template": "test",
    "context": {"title": "Prueba", "content": "Contenido de prueba"},
    "output": "test_output.pdf"
  }'

echo ""
echo "✅ Script completado. Revisa los logs para ver el rendimiento."
