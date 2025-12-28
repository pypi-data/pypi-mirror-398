# GNS3 Copilot

[![CI - QA & Testing](https://github.com/yueguobin/gns3-copilot/actions/workflows/ci.yaml/badge.svg)](https://github.com/yueguobin/gns3-copilot/actions/workflows/ci.yaml)
[![CD - Production Release](https://github.com/yueguobin/gns3-copilot/actions/workflows/cd.yaml/badge.svg)](https://github.com/yueguobin/gns3-copilot/actions/workflows/cd.yaml)
[![codecov](https://codecov.io/gh/yueguobin/gns3-copilot/branch/Development/graph/badge.svg?token=7FDUCM547W)](https://codecov.io/gh/yueguobin/gns3-copilot)
[![PyPI version](https://img.shields.io/pypi/v/gns3-copilot)](https://pypi.org/project/gns3-copilot/)
[![PyPI downloads](https://static.pepy.tech/badge/gns3-copilot)](https://pepy.tech/project/gns3-copilot)
![License](https://img.shields.io/badge/license-MIT-green.svg) 
[![platform](https://img.shields.io/badge/platform-linux%20%7C%20windows%20%7C%20macOS-lightgrey)](https://shields.io/)

An AI-powered network automation assistant designed specifically for GNS3 network simulator, providing intelligent network device management and automated operations.

## Project Overview

GNS3 Copilot is a powerful network automation tool that integrates multiple AI models and network automation frameworks. It can interact with users through natural language and perform tasks such as network device configuration, topology management, and fault diagnosis.

<img src="https://raw.githubusercontent.com/yueguobin/gns3-copilot/refs/heads/master/demo.gif" alt="GNS3 Copilot Function demonstration" width="1280"/>

### Core Features

- 🤖 **AI-Powered Chat Interface**: Supports natural language interaction, understands network automation requirements
- 🔧 **Device Configuration Management**: Batch configuration of network devices, supports multiple vendor devices (currently tested with Cisco IOSv image only)
- 📊 **Topology Management**: Automatically create, modify, and manage GNS3 network topologies
- 🔍 **Network Diagnostics**: Intelligent network troubleshooting and performance monitoring
- 🌐 **LLM Support**: Integrated DeepSeek AI model for natural language processing



## Technical Architecture

[GNS3-Copilot Architecture](Architecture/gns3_copilot_architecture.md)

[Core Framework Detailed Design](Architecture/Core%20Framework%20Detailed%20Design.md)


The Final Concept: Multi-Agent System Architecture and Dynamic Context Manager (Based on Current Understanding)

 **Multi-Agent Role Assignment**

This system employs distinct agents, each specializing in a specific function:

- **Planning Agent:** Responsible for **identifying user intent** and **formulating the detailed task plan**.
    
- **Execution Agent:** Responsible for **executing specific device operations** step-by-step according to the plan.
    
- **Supervision Agent:** Responsible for **continuous monitoring** and evaluation of the Execution Agent's results. If issues are found, it requests the Execution Agent to **retry** or notifies the **Expert Agent** to intervene.
    
- **Expert Agent:** Responsible for addressing complex problems discovered by the Supervision Agent, providing **guidance**, **correcting the plan**, or **proposing solutions**.
    

 **System Workflow**

The process operates in a closed-loop structure, ensuring reliability and self-correction:

1. **User Input Request**
    
    - The user initiates the system by submitting a task or request.
        
2. **Planning Agent: Intent Recognition & Plan Formulation**
    
    - The Planning Agent analyzes the request, understands the objective, and generates a sequence of execution steps.
        
3. **Execution Agent: Execute Plan Steps**
    
    - The Execution Agent takes the planned steps and performs the corresponding concrete operations.
        
4. **Supervision Agent: Real-time Monitoring & Evaluation**
    
    - The Supervision Agent continuously checks the outcome of each execution step.
        
    - **Issue Detected** $\rightarrow$ Requests the Execution Agent to **Retry** OR **Notifies the Expert Agent**.
        
5. **Expert Agent: Intervention & Guidance/Correction**
    
    - The Expert Agent intervenes when complex problems are reported.
        
    - It provides guidance $\rightarrow$ **Corrects the Plan** (loops back to Step 2) OR **Proposes a Solution** (loops back to Step 3).
        
6. **Return Final Work Result**
    
    - Once all steps are successfully completed and verified, the final result is delivered to the user.

## 🤝 Contributing

We welcome contributions from the community! To keep the project stable, please follow our branching strategy:

- **Target Branch**: Always submit your Pull Requests to the `Development` branch (not `master`).

- **Feature Branches**: Create a new branch for each feature or bug fix: `git checkout -b feature/your-feature-name Development`.

- **Workflow**: Fork -> Branch -> Commit -> Push -> Pull Request to `Development`.


## Installation Guide

### Environment Requirements

- Python 3.10+
- GNS3 Server (running on http://localhost:3080 or remote host)
- Supported operating systems: Windows, macOS, Linux

### Installation Steps

1. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows
```

1. **Install GNS3 Copilot**
```bash
pip install gns3-copilot
```
or
```bash
pip install git+https://github.com/yueguobin/gns3-copilot
```
1. **Start GNS3 Server**
Ensure GNS3 Server is running and can be accessed via its API interface: `http://x.x.x.x:3080`

1. **Launch the application**
```bash
gns3-copilot
```

## Usage Guide

### Startup

```bash
# Basic startup, default port 8501
gns3-copilot

# Specify custom port
gns3-copilot --server.port 8080

# Specify address and port
gns3-copilot --server.address 0.0.0.0 --server.port 8080

# Run in headless mode
gns3-copilot --server.headless true

# Get help
gns3-copilot --help

```

### Configure on Settings Page

GNS3 Copilot configuration is managed through a Streamlit interface, with all settings saved in the `.env` file in the project root directory. If the `.env` file doesn't exist on first run, the system will automatically create it.

#### 🔧 Main Configuration Content

##### 1. GNS3 Server Configuration
- **GNS3 Server Host**: GNS3 server host address (e.g., 127.0.0.1)
- **GNS3 Server URL**: Complete GNS3 server URL (e.g., http://127.0.0.1:3080)
- **API Version**: GNS3 API version (supports v2 and v3)
- **GNS3 Server Username**: GNS3 server username (required only for API v3)
- **GNS3 Server Password**: GNS3 server password (required only for API v3)

##### 2. LLM Model Configuration
- **Model Provider**: Model provider (supports: openai, anthropic, deepseek, xai, openrouter, etc.)
- **Model Name**: Specific model name (e.g., deepseek-chat, gpt-4o-mini, etc.)
- **Model API Key**: Model API key
- **Base URL**: Base URL for model service (required when using third-party platforms like OpenRouter)
- **Temperature**: Model temperature parameter (controls output randomness, range 0.0-1.0)

##### 3. Other Settings
- **Linux Console Username**: Linux console username (for Debian devices in GNS3)
- **Linux Console Password**: Linux console password

## Security Considerations

1. **API Key Protection**:
   - Do not commit `.env` file to version control
   - Regularly rotate API keys
   - Use principle of least privilege

## License

This project uses MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgements

Special thanks to the following resources for their inspiration and technical foundation:

* **Powered by 《网络工程师的 Python 之路》**
* **Powered by 《网络工程师的 AI 之路》**

## Contact

- Project Homepage: https://github.com/yueguobin/gns3-copilot
- Issue Reporting: https://github.com/yueguobin/gns3-copilot/issues

---
