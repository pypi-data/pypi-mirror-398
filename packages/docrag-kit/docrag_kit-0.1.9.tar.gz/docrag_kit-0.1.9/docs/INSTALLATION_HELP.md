# Quick Installation Help

If you're experiencing installation issues with DocRAG Kit, try these solutions:

## Solution 1: Use Python 3.11 (Recommended)

```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install --upgrade pip
pip install docrag-kit
```

## Solution 2: Install from requirements.txt

```bash
git clone https://github.com/dexiusprime-oss/docrag-kit.git
cd docrag-kit
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

## Solution 3: For Apple Silicon (M1/M2/M3)

```bash
# Create environment with Python 3.11
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Install with specific architecture
arch -arm64 pip install docrag-kit
```

## Solution 4: Manual dependency installation

```bash
pip install click pyyaml python-dotenv chardet tiktoken mcp
pip install langchain langchain-openai langchain-google-genai
pip install chromadb==0.4.22
pip install langchain-chroma
pip install docrag-kit --no-deps
```

## Still Having Issues?

1. Check full troubleshooting guide: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
2. Open an issue: https://github.com/dexiusprime-oss/docrag-kit/issues/new/choose
3. Include:
   - Your OS and architecture
   - Python version (`python --version`)
   - Full error output
   - What you've already tried

## Common Error: onnxruntime or pulsar-client

If you see errors about `onnxruntime` or `pulsar-client`, this is a known issue with ChromaDB on some platforms.

**Quick fix:**
```bash
# Use Python 3.11 in a fresh environment
python3.11 -m venv fresh_env
source fresh_env/bin/activate
pip install --upgrade pip setuptools wheel
pip install docrag-kit
```

For more details: [docs/TROUBLESHOOTING.md#dependency-conflict-with-onnxruntime-or-pulsar-client](docs/TROUBLESHOOTING.md#dependency-conflict-with-onnxruntime-or-pulsar-client)
