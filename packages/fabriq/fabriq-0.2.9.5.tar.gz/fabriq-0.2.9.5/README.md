# Fabriq

Fabriq is a Python SDK for building quick, low-code Generative AI solutions.

It provides a modular framework for building and deploying conversational AI Agents with minimal effort.

`NOTICE:` This package is currently under active development. The API and functionality are subject to significant changes.

## Installation

```bash
pip install fabriq[all]
```

For ChatBot only:
```bash
pip install fabriq[chat]
```


## Chatbot only Entry Points

- `fabriq-chat-cli`: Terminal-based chat interface with default configuration
- `fabriq-chat-ui`: Streamlit-based web chat interface with default configuration

## Chatbot CLI Usage

- **Commands**:
  - `/help`: Show help
  - `/clear`: Clear conversation history
  - `/history`: Show conversation history
  - `/upload`: Upload documents from a directory path
  - `/exit` or `/quit`: Exit chatbot


## Requirements

- Python 3.12, 3.11, 3.10
- See requirements.txt and packages for dependencies.

## License

MIT License

## Author

Aaryan Verma  
[LinkedIn](https://linkedin.com/in/aaryanverma)

---

For more details, see the documentation and example notebooks in the config folder.