# Intelligent Help Desk System

An AI-powered help desk system that automatically classifies user requests, retrieves relevant information from a knowledge base, generates contextual responses using LLMs, and determines when human escalation is needed.

## 🚀 Features

- **Request Classification**: Automatically categorizes IT support requests into predefined types
- **Knowledge Retrieval**: Semantic search through documentation using vector embeddings
- **Response Generation**: Context-aware responses using Large Language Models
- **Escalation Logic**: Smart routing for complex issues requiring human intervention
- **REST API**: Clean API interface for integration with existing systems

## 📁 Project Structure

```bash
Help-Desk-Automation-System/
│   README.md
├── .github/workflows/workflows
└───Project/
    │   app.py  # Flask API
    │   classifier.py  # Request categorization
    │   data_models.py # Pydantic schemas
    │   escalation.py
    │   main.py
    │   pyproject.toml
    │   requirements.txt
    │   response.py
    │   retrieval.py
    │   test.py #series of users requests
    │
    ├───templates/
    │       index.html
    │
    ├───tests/
    │   │   __init__.py
    │   │   test_classifier.py
    │   │   test_escalation.py
    │   │   test_response.py
    │   │   test_retrieval.py
    │   │                              # Unit/integration tests
    │   └───integration/
    │           __init__.py
    │           test_classify_and_escalate.py
    │           test_full_workflow.py
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Flask API     │    │   Classification │    │   Knowledge     │
│   (app.py)      │───▶│   System         │───▶│   Retrieval    │
│                 │    │   (classifier.py)│    │   (retrieval.py)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Response      │    │   Escalation     │    │   Vector DB     │
│   Generation    │    │   Engine         │    │   (ChromaDB)    │
│   (response.py) │    │   (escalation.py)│    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🛠️ Technology Stack

- **Backend**: Python, Flask
- **AI/ML**: Cohere API (embeddings & generation), ChromaDB (vector storage)
- **Code Quality**: Black (formatting), Ruff (linting)
- **Testing**: pytest (unit & integration tests)
- **Deployment**: Render
- **CI/CD**: GitHub Actions

## 📦 Installation

### Prerequisites

- Python 3.9+
- Cohere API key

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Taciturny/Help-Desk-Automation-System.git
   cd help-desk-automation-system
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment configuration**
   ```bash
   export COHERE_API_KEY="your-cohere-api-key"
   export FLASK_ENV="development"  # or "production"
   ```

4. **Initialize knowledge base**
   ```bash
   python -m retrieval
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

The API will be available at `http://localhost:5000`

## 🔧 API Usage

### Classify Request
```bash
POST /api/classify
Content-Type: application/json

{
    "request": "I forgot my password and can't log in"
}
```

**Response:**
```json
{
    "category": "password_reset",
    "confidence": 0.92,
    "keywords_matched": ["password", "forgot", "can't", "log", "in"],
    "reasoning": "Matched 5 indicators for password_reset"
}
```

### Get Knowledge Response
```bash
POST /api/knowledge
Content-Type: application/json

{
    "query": "How do I install Slack?",
    "template_type": "installation"
}
```

**Response:**
```json
{
    "query": "How do I install Slack?",
    "answer": "To install Slack:\n1. Visit the company software portal...",
    "confidence": 0.87,
    "sources": ["installation#slack", "software_guides"]
}
```

### Check Escalation
```bash
POST /api/escalate
Content-Type: application/json

{
    "request": "Security breach detected on server",
    "category": "security_incident",
    "confidence": 0.95
}
```

**Response:**
```json
{
    "should_escalate": true,
    "escalation_level": "security_team",
    "priority": "high",
    "contact_info": "security-team@company.com",
    "response_time_sla": 15
}
```

## 🧪 Testing

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=. --cov-report=html
```

### Run specific test types
```bash
# Run all unit tests individually
pytest tests/test_classifier.py
pytest tests/test_escalation.py
pytest tests/test_response.py
pytest tests/test_retrieval.py

# OR run all unit tests at once
pytest tests/

# Run only integration tests
pytest tests/integration/
```

## 🔍 Code Quality

### Format code
```bash
black .
```

### Lint code
```bash
ruff check .
```

### Run all quality checks
```bash
black . && ruff check . && pytest
```

## 🚀 Deployment

### Render Deployment

1. **Connect repository** to Render
2. **Set environment variables**:
   - `COHERE_API_KEY`: Your Cohere API key
   - `FLASK_ENV`: `production`
3. **Deploy** using the provided `render.yaml` configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `COHERE_API_KEY` | Cohere API key for embeddings and generation | Yes |
| `FLASK_ENV` | Flask environment (development/production) | No |
| `PORT` | Application port (default: 5000) | No |

## 📊 Performance Metrics

The system tracks several key metrics:

- **Classification Accuracy**: >90% on test dataset
- **Response Confidence**: Average >0.75 for actionable responses
- **Retrieval Relevance**: Top-3 results typically >0.8 relevance score
- **Response Time**: <2 seconds for standard queries

## 🔄 CI/CD Pipeline

GitHub Actions workflow includes:

1. **Code Quality**: Black formatting, Ruff linting
2. **Testing**: Unit and integration tests with coverage
3. **Security**: Dependency vulnerability scanning
4. **Deployment**: Automatic deployment to Render on main branch

## 🚀 Deployment

The application is deployed on **Streamlit Cloud** and can be accessed here:
👉 [Help Desk Assistant App](https://app-desk-automation-system-6qhqg4mcyfwxgubbzpjfaq.streamlit.app/)


## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run quality checks (`black . && ruff check . && pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📝 Configuration Files

### Knowledge Base Files
- `categories.json`: Category definitions and metadata
- `installation_guides.json`: Software installation procedures
- `troubleshooting_database.json`: Common issues and solutions
- `company_it_policies.md`: IT policies and guidelines
- `knowledge_base.md`: General help documentation

### Test Data
- `test_requests.json`: Evaluation dataset with expected classifications

## 🔧 Customization

### Adding New Categories
1. Update `RequestCategory` enum in `data_models.py`
2. Add classification patterns in `classifier.py`
3. Create escalation rules in `escalation.py`
4. Update knowledge base documents

### Adjusting Confidence Thresholds
Modify confidence calculations in:
- `classifier.py`: Classification confidence
- `response.py`: Response generation confidence
- `escalation.py`: Escalation trigger thresholds

## 🐛 Troubleshooting

### Common Issues

**Low Classification Confidence**
- Add more keywords to category patterns
- Update regex patterns for better matching
- Expand knowledge base with relevant documents

**Poor Retrieval Results**
- Check Cohere API key configuration
- Verify knowledge base loading
- Review document chunking and embeddings

**API Errors**
- Validate JSON request format
- Check required fields are present
- Review error logs for specific issues

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Built with ❤️ for intelligent IT support**
