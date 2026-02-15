# Evolution API - WhatsApp Business Integration
# Official image from Evolution API project
FROM atendai/evolution-api:latest

# The Evolution API image already includes everything needed
# Environment variables are configured via render.yaml

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8080}/ || exit 1

# Port is set via environment variable
EXPOSE 8080

# Start the Evolution API
CMD ["node", "./dist/src/main.js"]
