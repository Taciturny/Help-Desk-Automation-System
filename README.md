# Help-Desk-Automation-System
A comprehensive AI-powered help desk automation system that classifies user requests, retrieves relevant knowledge, generates intelligent responses, and handles escalations automatically.

## 🚀 Features

- **Intelligent Request Classification**: Automatically categorizes support requests using keyword-based pattern matching
- **Knowledge Retrieval**: Searches through documentation and knowledge base using semantic similarity
- **Response Generation**: Creates contextual responses using Cohere's language models
- **Escalation Management**: Automatically escalates complex or high-priority issues
- **Interactive CLI**: User-friendly command-line interface for real-time support
- **Comprehensive Logging**: Detailed logging for monitoring and debugging

## 📋 Supported Request Categories

- **Password Reset**: Account lockouts, forgotten passwords, authentication issues
- **Software Installation**: Application setup, installation failures, configuration
- **Hardware Failure**: Device malfunctions, screen issues, equipment problems
- **Network Connectivity**: WiFi problems, VPN issues, internet connectivity
- **Email Configuration**: Outlook setup, email sync issues, distribution lists
- **Security Incidents**: Suspicious activities, malware, phishing attempts
- **Policy Questions**: Company policies, approval processes, guidelines

## 🛠 Installation

### Prerequisites

- Python 3.9 or higher
- Cohere API key (sign up at [cohere.ai](https://cohere.ai))

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Taciturny/Help-Desk-Automation-System.git
   cd help-desk-automation-system
   ```

2. **Create virtual environment**
   ```bash
   python -m venv helpdesk_env
   source helpdesk_env/bin/activate  # On Windows: helpdesk_env\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Option 1: Export directly
   export COHERE_API_KEY="your-cohere-api-key-here"

   # Option 2: Create .env file
   echo "COHERE_API_KEY=your-cohere-api-key-here" > .env
   ```
## 🚀 Usage

### Interactive Mode

Run the system in interactive mode for real-time support:

```bash
python main.py
```

This launches an interactive CLI where users can type their support requests and receive immediate responses.

### Batch Mode

Process a single query programmatically:

```bash
python main.py --batch --query "I forgot my password and can't log in"
```

### Command Line Options

```bash
python main.py [OPTIONS]

Options:
  --log-level {DEBUG,INFO,WARNING,ERROR}  Set logging level (default: INFO)
  --batch                                 Run in batch mode (non-interactive)
  --query TEXT                           Single query to process (for batch mode)
  --help                                 Show help message
```

## 🏗 System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Input    │───▶│   Classifier     │───▶│  Knowledge      │
│                 │    │                  │    │  Retrieval      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Final         │◀───│   Escalation     │◀───│   Response      │
│   Response      │    │   Engine         │    │   Generation    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Core Components

1. **Request Classifier** (`classifier.py`)
   - Keyword-based pattern matching
   - Confidence scoring
   - Extensible for ML-based classification

2. **Knowledge Retriever** (`retrieval.py`)
   - ChromaDB vector database
   - Cohere embeddings
   - Multi-method confidence scoring

3. **Response Generator** (`response.py`)
   - Template-based responses
   - Context-aware generation
   - Multiple response formats

4. **Data Models** (`data_models.py`)
   - Type-safe data structures
   - Escalation management
   - Request/response schemas

3. **Escalation Engine** (`escalation_engine.py`)
   - Rule-based ticket evaluation
   - Priority-sorted escalation matching
   - Business hours and SLA management


6. **Escalation Rules Manager** (`escalation_rules.py`)
   - JSON-based rule configuration
   - CRUD operations for rules
   - Default escalation rule templates

## 🎯 Example Usage

### Interactive Session

```
============================================================
   HELP DESK AUTOMATION SYSTEM
============================================================
Type 'quit', 'exit', or 'help' for special commands
Enter your IT support request below:

👤 Your request: I can't install Slack on my computer

🔄 Processing your request...

🎯 CATEGORY: Software Installation

💡 SOLUTION:
   1. Download Slack from the company software portal
   2. Right-click the installer and select "Run as administrator"
   3. Follow the installation wizard
   4. Restart your computer if prompted

🔗 ADDITIONAL RESOURCES:
   • Software Catalog: https://company.com/software
   • Installation Guidelines: https://company.com/installation-guide

------------------------------------------------------------
```

### Batch Processing

```bash
$ python main.py --batch --query "My laptop screen is flickering"

🎯 CATEGORY: Hardware Failure

💡 SOLUTION:
   1. Check display cable connections
   2. Update graphics drivers
   3. Test with external monitor

⚠️  ESCALATION REQUIRED
   Reason: Hardware issues require physical inspection
   Contact: hardware-support@company.com
```

## 📊 Monitoring & Logging

The system provides comprehensive logging and statistics:

### View System Statistics
```bash
# In interactive mode, type:
stats

📊 SYSTEM STATISTICS:
  Knowledge Base: 156 documents
  Total Requests: 42
  Avg Confidence: 0.847
  System Status: operational
```

### Log Files

- `helpdesk.log` - Complete system logs
- Console output - Real-time feedback
- Configurable log levels (DEBUG, INFO, WARNING, ERROR)

## 🔒 Security & Privacy

- No sensitive data stored in logs
- API keys managed through environment variables
- Request data processed in memory only
- Escalation triggers for security incidents

## 🛡 Error Handling

The system includes robust error handling:

- **API Failures**: Graceful fallback responses
- **Missing Knowledge**: Automatic escalation
- **Classification Errors**: Default to human review
- **Network Issues**: Retry mechanisms

## 🚀 Extending the System

### Adding New Classifications
1. Extend `RequestCategory` enum in `data_models.py`
2. Add patterns to `KeywordBasedClassifier`
3. Update template mapping in main system

### Custom Response Templates
1. Add new template method in `ResponseGenerator`
2. Update `_get_template_type()` mapping
3. Configure category-specific responses

### Integration APIs
The system can be easily integrated into:
- Slack bots
- Microsoft Teams apps
- Web applications
- Ticketing systems

## 📈 Performance Metrics

- **Classification Accuracy**: ~85-90% for well-defined categories
- **Response Time**: < 2 seconds for most queries
- **Knowledge Retrieval**: Semantic search with 0.3+ relevance threshold
- **Escalation Rate**: ~15-20% of requests (configurable)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push to branch (`git push origin feature/new-feature`)
5. Create Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support
For questions or issues:

1. Check the [Issues](https://github.com/yourusername/helpdesk-automation/issues) page
2. Review the logs in `helpdesk.log`
3. Ensure your Cohere API key is valid
4. Verify all dependencies are installed

## 🙏 Acknowledgments

- [Cohere](https://cohere.ai) for language model APIs
- [ChromaDB](https://www.trychroma.com/) for vector database
- [scikit-learn](https://scikit-learn.org/) for ML utilities

---
**Built with ❤️ for better IT support automation**
