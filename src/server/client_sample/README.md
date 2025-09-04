# Server Build
```bash
docker build . --tag mahjong-cpp
docker run -it -p 50000:50000 mahjong-cpp
```

# Client
```bash
uv run client.py
```
