# Docker Examples

Basic Docker setup for MQTT broker and Ollama.

```bash
# Start MQTT broker
docker-compose up -d mosquitto

# Optional: Ollama
docker-compose up -d ollama
docker exec ollama ollama pull gemma3n:4b
```

