# Daita Agents

[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/daita-agents)](https://pypi.org/project/daita-agents/)

**Daita Agents** is a commercial AI agent framework designed for production environments. Build intelligent, scalable, data first agent systems with automatic tracing, reliability features, and enterprise-grade observability.

## Quick Start

```bash
# Install the SDK
pip install daita-agents

# Set up your first agent
daita init my-project
cd my-project

# Create and test an agent
daita create agent my-agent
daita test my-agent
```

## Key Features

### Free SDK Features
- **Production-Ready Agents**: BaseAgent and SubstrateAgent with automatic lifecycle management
- **Multi-LLM Support**: OpenAI, Anthropic, Google Gemini, and xAI Grok integrations
- **Automatic Tracing**: Zero-configuration observability for all operations
- **Plugin System**: Database (PostgreSQL, MySQL, MongoDB) and API integrations
- **Workflow Orchestration**: Multi-agent systems with relay communication
- **CLI Tools**: Development, testing, and deployment commands

### Premium Features
- **Enterprise Integrations**: Advanced database plugins and connectors
- **Horizontal Scaling**: Agent pools and load balancing
- **Advanced Reliability**: Circuit breakers, backpressure control, task management
- **Dashboard Analytics**: Real-time monitoring and performance insights
- **Priority Support**: Direct access to engineering team
- **Custom Integrations**: Tailored solutions for enterprise needs

## Installation

### Basic Installation

The base installation includes OpenAI and all CLI tools - everything you need to get started:

```bash
pip install daita-agents
```

This gives you:
- Full CLI (`daita init`, `daita create`, `daita test`, etc.)
- OpenAI integration (GPT-4, GPT-3.5, etc.)
- Core agent framework and workflow orchestration
- Automatic tracing and observability

### Recommended Installation

For most users, we recommend adding commonly-used features:

```bash
pip install daita-agents[recommended]
```

Adds: Claude (Anthropic), pandas, numpy, web scraping tools

### Installation by Use Case

**Data-focused agents** (analysis, ETL, reporting):
```bash
pip install daita-agents[data]
```

**Production deployment** (cloud + monitoring):
```bash
pip install daita-agents[production]
```

**Complete setup** (most common features):
```bash
pip install daita-agents[complete]
```

### Additional LLM Providers

Add support for specific LLM providers (OpenAI already included):

```bash
pip install daita-agents[anthropic]   # Claude models
pip install daita-agents[google]      # Gemini models
pip install daita-agents[llm-all]     # All LLM providers
```

### Database Integration

Install database connectors as needed:

```bash
pip install daita-agents[postgresql]  # PostgreSQL
pip install daita-agents[mysql]       # MySQL
pip install daita-agents[mongodb]     # MongoDB
pip install daita-agents[databases]   # All traditional databases
pip install daita-agents[vectordb]    # Vector databases (Chroma, Pinecone, Qdrant)
```

### Other Optional Features

```bash
pip install daita-agents[cloud]       # AWS and Slack integrations
pip install daita-agents[web]         # Web scraping and parsing
pip install daita-agents[api-server]  # FastAPI server for custom APIs
pip install daita-agents[all]         # Everything (large install)
```

### Development

```bash
pip install daita-agents[dev]
```

## Basic Usage

### Simple Agent
```python
from daita import SubstrateAgent

# Create agent with simple configuration
agent = SubstrateAgent(
    name="Data Analyst",
    model="gpt-4o-mini",
    prompt="You are a data analyst. Help users analyze and interpret data."
)

# Start and run agent
await agent.start()

# Simple execution - just get the answer
answer = await agent.run("Analyze sales trends from last quarter")
print(answer)

# Detailed execution - get full metadata
result = await agent.run_detailed("What are the key insights?")
print(f"Answer: {result['result']}")
print(f"Cost: ${result['cost']:.4f}")
print(f"Time: {result['processing_time_ms']}ms")
```

### Agent with Tools
```python
from daita import SubstrateAgent
from daita.core.tools import tool

# Define tools for your agent
@tool
async def query_database(sql: str) -> list:
    '''Execute SQL query and return results.'''
    return await db.execute(sql)

@tool
async def calculate_metrics(data: list) -> dict:
    '''Calculate statistical metrics for data.'''
    return {
        'mean': sum(data) / len(data),
        'max': max(data),
        'min': min(data)
    }

# Create agent and register tools
agent = SubstrateAgent(
    name="Data Analyst",
    model="gpt-4o-mini",
    prompt="You are a data analyst with database access."
)
agent.register_tool(query_database)
agent.register_tool(calculate_metrics)

await agent.start()

# Agent autonomously decides which tools to use
answer = await agent.run("What were total sales last month?")
print(answer)
```

### Multi-Agent Workflow
```python
from daita import Workflow, BaseAgent

# Create workflow with multiple agents
workflow = Workflow()
workflow.connect(data_agent, "processed_data", analysis_agent)
workflow.connect(analysis_agent, "insights", report_agent)

# Execute workflow
results = await workflow.run(input_data)
```

### CLI Commands
```bash
# Initialize new project
daita init my-project

# Create components
daita create agent my-agent
daita create workflow data-pipeline

# Test and deploy
daita test --watch
daita push production
```

## Architecture

### Core Components
- **Agents**: Intelligent processing units with LLM integration
- **Workflows**: Orchestrate multiple agents with communication channels
- **Plugins**: Extensible integrations for databases and APIs
- **Tracing**: Automatic observability for debugging and monitoring
- **Reliability**: Production-grade error handling and retry logic

### Automatic Tracing
All operations are automatically traced:
- Agent lifecycle and decisions
- LLM calls with token usage and costs
- Plugin/tool executions
- Workflow communication
- Error handling and retries

## Examples

### Database Integration
```python
from daita import SubstrateAgent
from daita.plugins import postgresql

# Create database plugin (provides query tool)
db = postgresql(
    host="localhost",
    database="mydb",
    user="user",
    password="pass"
)

# Create agent with database tools
agent = SubstrateAgent(
    name="Database Analyst",
    model="gpt-4o-mini",
    tools=[db]  # Automatically registers database query tools
)

await agent.start()

# Agent can autonomously query database
answer = await agent.run("Show me all active users from the database")
print(answer)
```

### Decision Tracing
```python
from daita import record_decision_point

async def make_decision(data):
    confidence = analyze_confidence(data)
    
    # Trace decision reasoning
    decision = record_decision_point(
        decision_type="classification",
        confidence=confidence,
        reasoning="Based on data patterns..."
    )
    
    return decision
```

## Authentication & Deployment

### API Key Setup
```bash
export DAITA_API_KEY="your-api-key"
export OPENAI_API_KEY="your-openai-key"
```

### Cloud Deployment
```bash
# Deploy to managed infrastructure
daita push production

# Monitor deployments
daita logs production
daita status
```

## Documentation

- **[Getting Started Guide](https://docs.daita-tech.io/getting-started)**
- **[API Reference](https://docs.daita-tech.io/api)**
- **[Plugin Development](https://docs.daita-tech.io/plugins)**
- **[Enterprise Features](https://docs.daita-tech.io/enterprise)**

## Commercial Licensing

Daita Agents is commercial software with a generous free tier:

- **Free**: Core SDK, basic plugins, community support
- **Premium**: Enterprise features, advanced scaling, priority support
- **Enterprise**: Custom integrations, dedicated support, SLA

[Contact Sales](https://daita-tech.io/contact/sales) for premium features and enterprise licensing.

## Support

- **Documentation**: [docs.daita-technologies.com](https://docs.daita-tech.io)
- **Commercial Support**: [support@daita-tech.io](mailto:support@daita-tech.io)

## Links

- **Homepage**: [daita-tech.io](https://daita-tech.io)
- **PyPI Package**: [pypi.org/project/daita-agents](https://pypi.org/project/daita-agents/)

---

*Built for production AI agent systems. Start free, scale with premium features.*