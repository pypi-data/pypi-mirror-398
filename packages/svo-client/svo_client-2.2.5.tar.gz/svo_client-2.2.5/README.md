# svo-client

Асинхронный Python-клиент для SVO Semantic Chunker microservice.

## Установка

```bash
pip install svo-client
```

## Пример использования

```python
from svo_client.chunker_client import ChunkerClient
import asyncio

async def main():
    async with ChunkerClient(timeout=60) as client:
        chunks = await client.chunk_text("Your text here.")
        print(client.reconstruct_text(chunks))

asyncio.run(main())
```

## Документация
- [OpenAPI schema](docs/openapi.json)
- [Примеры и тесты](tests/test_chunker_client.py)

## API клиента

### Класс `ChunkerClient`

**Инициализация:**
```python
client = ChunkerClient(url="http://localhost", port=8009, timeout=60)
```
- `url` — адрес сервиса (по умолчанию http://localhost)
- `port` — порт (по умолчанию 8009)
- `timeout` — таймаут HTTP-запросов в секундах (по умолчанию 60)
