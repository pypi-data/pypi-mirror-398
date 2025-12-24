# OpenBlog

**Open-source AI-powered blog generation system** — 12-stage pipeline for producing high-quality, AEO-optimized articles.

## ✨ Features

- 🔄 **12-Stage Pipeline** — Modular, testable stages from data fetch to HTML output
- 🎯 **AEO Optimization** — Built-in Answer Engine Optimization scoring (70-85+ scores)
- 🔍 **Smart Citations** — Automatic source validation and formatting
- 📝 **Rich Content** — FAQ/PAA extraction, internal links, ToC generation
- 🖼️ **Image Generation** — AI-powered featured images via OpenRouter
- 🌐 **Multi-language** — Supports multiple languages with auto-detection
- ⚡ **Fast** — 60-90 second generation time

## 📋 Pipeline Stages

```
Stage 0: Data Fetch & Company Detection
Stage 1: Prompt Construction
Stage 2: AI Content Generation (Gemini + tools)
Stage 3: Structured Data Extraction
Stage 4: Citation Validation ─┐
Stage 5: Internal Links      │ (parallel)
Stage 6: Table of Contents   │
Stage 7: Metadata            │
Stage 8: FAQ/PAA Enhancement │
Stage 9: Image Generation   ─┘
Stage 10: Cleanup & Validation
Stage 11: HTML Generation & Storage
```

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/federicodeponte/openblog.git
cd openblog
pip install -r requirements.txt
```

### Environment Variables

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key

# Optional - DataForSEO fallback (when Google Search quota exhausted)
# Cost: $0.50 per 1,000 queries - Standard mode (async task-based)
# Automatically activates when Google Search returns 429/quota errors
DATAFORSEO_LOGIN=your_dataforseo_email
DATAFORSEO_PASSWORD=your_dataforseo_password

# Optional - for Google Drive integration
GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'
GOOGLE_DELEGATION_SUBJECT=user@domain.com
```

### API Usage

```bash
# Start the server
uvicorn service.api:app --reload

# Generate a blog
curl -X POST http://localhost:8000/blog/write \
  -H "Content-Type: application/json" \
  -d '{
    "primary_keyword": "AI in customer service",
    "company_url": "https://example.com"
  }'
```

### Python Usage

```python
from pipeline.core.workflow_engine import WorkflowEngine
from pipeline.core.execution_context import ExecutionContext

engine = WorkflowEngine()
context = ExecutionContext(
    job_id="test-123",
    job_config={
        "primary_keyword": "AI adoption in customer service",
        "company_url": "https://example.com",
    },
)

result = await engine.execute(context)
print(result.final_article["Headline"])
```

## 🏗️ Project Structure

```
openblog/
├── pipeline/
│   ├── blog_generation/    # 12 stages (stage_00 to stage_11)
│   ├── core/               # Workflow engine, execution context
│   ├── models/             # Data models, AI clients
│   ├── processors/         # HTML, citations, sitemap
│   ├── prompts/            # Prompt templates
│   └── utils/              # AEO scorer, helpers
├── service/
│   ├── api.py              # FastAPI endpoints
│   └── image_generator.py  # Image generation
├── tests/                  # Test suite
├── docs/                   # Documentation
├── modal_deploy.py         # Modal deployment
└── requirements.txt
```

## 📊 Output Quality

- **AEO Score**: 70-85+ / 100
- **Generation Time**: 60-90 seconds
- **Citation Validation**: Automatic URL checking
- **HTML Output**: Clean, semantic markup

## 🔧 Deployment

### Modal (Recommended)

```bash
pip install modal
modal deploy modal_deploy.py
```

### Docker

```bash
docker build -t openblog .
docker run -p 8000:8000 openblog
```

## 📖 Documentation

- [Architecture Overview](ARCHITECTURE_OVERVIEW.md)
- [Detailed Architecture](docs/ARCHITECTURE.md)
- [Input Requirements](docs/INPUT_REQUIREMENTS.md)
- [Async Architecture](docs/ASYNC_ARCHITECTURE.md)

## 🧪 Testing

```bash
pytest tests/ -v
pytest tests/stages/test_stage_00.py -v  # Test specific stage
```

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions welcome! Please read the contributing guidelines before submitting PRs.

---

Built with ❤️ by [SCAILE](https://scaile.tech)
