<div align="center">
  <img src="ui/static/assets/tak-logo.png" alt="Topaz Agent Kit Logo" width="200"/>
</div>

# Topaz Agent Kit - Basic Project

Welcome to your Topaz Agent Kit project! This is a minimal, functional setup that includes an example pipeline and several independent agents ready to use.

## 🎯 What is Topaz Agent Kit?

**Topaz Agent Kit** is a powerful, config-driven multi-agent orchestration framework that enables you to build sophisticated AI agent workflows quickly and easily. Instead of writing complex code from scratch, you define your agents and pipelines using simple YAML configuration files.

### Key Features

- **🔄 Multi-Framework Support**: Build agents using LangGraph, CrewAI, Agno, ADK, OAK, Semantic Kernel, or MAF — all in one unified system
- **🧰 Rich Tool Ecosystem**: Access 75+ pre-built tools via MCP (Model Context Protocol) for document processing, web search, email, travel, and more
- **🔄 Flexible Execution Patterns**: Use sequential, parallel, conditional, switch, loop, repeat, and nested patterns to orchestrate complex workflows
- **🎛️ Modern Web UI**: Interactive web interface with real-time agent visualization, file uploads, and session management
- **📄 Document Intelligence**: Built-in RAG (Retrieval-Augmented Generation) with document upload, analysis, and semantic search
- **🚪 Human-in-the-Loop**: Approval gates, input prompts, and selection gates for interactive workflows
- **⚡ Rapid Development**: Go from idea to working demo in hours, not weeks

### What This Basic Project Includes

This basic template provides:

- ✅ **Example Pipeline**: A simple `hello_agent` pipeline to get you started
- ✅ **Independent Agents**: Five ready-to-use agents (content_analyzer, rag_query, content_extractor, image_extractor, web_search)
- ✅ **MCP Integration**: Pre-configured MCP server for tool access
- ✅ **Web UI**: Full-featured web interface for interacting with your agents
- ✅ **Project Structure**: Organized configuration files and auto-generated code

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Environment Setup](#environment-setup)
- [Project Structure](#project-structure)
- [Adding a New Pipeline](#adding-a-new-pipeline)
- [Pipeline Patterns](#pipeline-patterns)
- [Running Your Project](#running-your-project)
- [Next Steps](#next-steps)

## 🚀 Quick Start

1. **Set up your environment variables** (see [Environment Setup](#environment-setup))
2. **Start the services**:
   ```bash
   topaz-agent-kit serve fastapi --project .
   ```
3. **Open your browser** to `http://127.0.0.1:8090`

## 🔧 Environment Setup

### Step 1: Create Your `.env` File

Copy the example environment file:

```bash
cp .env.example .env
```

### Step 2: Configure Required Variables

Open `.env` and fill in the required values. The basic template uses **Azure OpenAI** by default, so you need:

```bash
# Azure OpenAI Configuration (Required)
AZURE_OPENAI_API_BASE=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
AZURE_OPENAI_MODEL=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

**Note**: If you want to use a different model provider (Google AI, Ollama), you'll need to:
1. Update the `model` field in your agent YAML files
2. Add the corresponding environment variables (see `.env.example` for all options)

### Optional: Other Model Providers

If you want to use other providers, uncomment and configure the relevant sections in `.env`:

- **Google AI**: `GOOGLE_API_KEY` (for Gemini models)
- **Ollama**: `OLLAMA_BASE_URL` (defaults to `http://localhost:11434` for local models)

### Optional: MCP Toolkits

If you plan to use MCP toolkits, you'll need to configure the corresponding API keys:

- **Web Search**: `SERPER_API_KEY` (for Serper API) or `TAVILY_API_KEY` (for Tavily)
- **SEC API**: `SEC_API_KEY` (for SEC filings search)
- **Amadeus Travel**: `AMADEUS_CLIENT_ID` and `AMADEUS_CLIENT_SECRET` (for flights, hotels, activities)
- **Gmail**: `GMAIL_CREDENTIALS_PATH` (path to `client_secret.json` for email operations)
- **Browser Automation**: `BROWSERLESS_API_KEY` (for browser automation tools)

See `.env.example` for all available options.

## 📁 Project Structure

```
.
├── config/
│   ├── pipeline.yml              # Main pipeline configuration
│   ├── ui_manifest.yml           # Global UI configuration
│   ├── agents/                   # Agent configurations
│   │   ├── hello_agent.yml       # Example agent
│   │   ├── content_analyzer.yml  # Independent agents
│   │   ├── rag_query.yml
│   │   └── ...
│   ├── pipelines/                # Individual pipeline definitions
│   │   └── example.yml           # Example pipeline
│   ├── prompts/                  # Jinja2 prompt templates
│   │   ├── hello_agent.jinja
│   │   └── ...
│   └── ui_manifests/             # Pipeline-specific UI configs
│       ├── example.yml
│       └── independent_agents.yml
├── agents/                       # Generated agent code (auto-generated)
├── services/                     # Generated service code (auto-generated)
├── ui/                          # UI assets
│   └── static/
│       └── assets/              # Logos, icons, workflow diagrams
├── data/                        # Runtime data (created automatically)
│   ├── chat.db                 # Chat history
│   ├── chroma_db/              # Vector database
│   ├── rag_files/              # RAG document storage
│   └── user_files/             # User-uploaded files
├── .env                         # Your environment variables (create from .env.example)
└── README.md                    # This file
```

## ➕ Adding a New Pipeline

### Step 1: Create the Pipeline Configuration

Create a new file in `config/pipelines/` (e.g., `config/pipelines/my_pipeline.yml`):

```yaml
name: "My Pipeline"
description: "Description of what this pipeline does"

nodes:
  - id: my_agent
    config_file: agents/my_agent.yml

pattern:
  type: sequential
  steps:
    - node: my_agent
```

### Step 2: Create Agent Configuration

Create `config/agents/my_agent.yml`:

```yaml
id: my_agent
type: agno
model: "azure_openai"
run_mode: "local"

prompt:
  instruction:
    jinja: prompts/my_agent.jinja
  inputs:
    inline: |
      - User Query: {{user_text}}

outputs:
  final:
    selectors:
      - response
    selector_mode: "first"
    transform: |
      {{ value.response }}
```

### Step 3: Create Prompt Template

Create `config/prompts/my_agent.jinja`:

```jinja
You are a helpful assistant. Respond to user queries.

## Guidelines:
- Be clear and concise
- Provide accurate information

## Response:
Provide a helpful response to the user's query.
```

### Step 4: Register the Pipeline

Add your pipeline to `config/pipeline.yml`:

```yaml
pipelines:
  - id: example
    config_file: pipelines/example.yml
  - id: my_pipeline
    config_file: pipelines/my_pipeline.yml  # Add this line
```

### Step 5: Create UI Manifest (Optional)

Create `config/ui_manifests/my_pipeline.yml`:

```yaml
title: "My Pipeline"
subtitle: "Description of what this pipeline does"

agents:
  - id: my_agent
    title: "My Agent"
    subtitle: "Agent description"
    icon: "assets/my_agent.svg"

interaction_diagram: "assets/my_pipeline_workflow.svg"
```

And add it to `config/ui_manifest.yml`:

```yaml
pipelines:
  - id: "example"
    title: "Example Pipeline"
    ui_manifest: "ui_manifests/example.yml"
  - id: "my_pipeline"
    title: "My Pipeline"
    ui_manifest: "ui_manifests/my_pipeline.yml"  # Add this
```

### Step 6: Generate Code

After creating your configuration files, regenerate the agent and service code:

```bash
topaz-agent-kit generate agents --project .
topaz-agent-kit generate services --project .
topaz-agent-kit generate diagrams --project .
```

## 🔀 Pipeline Patterns

Topaz Agent Kit supports multiple execution patterns. Here are the most common ones:

### 1. Sequential Pattern

Execute agents one after another in order:

```yaml
pattern:
  type: sequential
  steps:
    - node: agent1
    - node: agent2
    - node: agent3
```

**Use when**: Each agent depends on the output of the previous agent.

### 2. Parallel Pattern

Execute multiple agents simultaneously:

```yaml
pattern:
  type: sequential
  steps:
    - node: coordinator
    - type: parallel
      steps:
        - node: agent1
        - node: agent2
        - node: agent3
    - node: aggregator
```

**Use when**: Agents are independent and can run concurrently to save time.

### 3. Conditional Pattern

Execute steps based on conditions:

```yaml
pattern:
  type: sequential
  steps:
    - node: analyzer
    - type: sequential
      condition: "analyzer.needs_review == true"
      steps:
        - node: reviewer
        - gate: approve_review
    - node: finalizer
```

**Use when**: You need to conditionally execute parts of the pipeline based on previous results.

### 4. Switch Pattern

Route to different branches based on a condition:

```yaml
pattern:
  type: sequential
  steps:
    - node: classifier
    - type: switch(classifier.complexity > 5)
      cases:
        true:
          - node: complex_processor
          - node: validator
        false:
          - node: simple_processor
    - node: finalizer
```

**Use when**: You need to choose between different execution paths.

### 5. Loop Pattern

Repeat a step or pattern multiple times. There are two ways to control loops:

#### 5a. Numeric Loop (with max_iterations)

Iterate a fixed number of times or until a termination condition is met:

```yaml
pattern:
  type: sequential
  steps:
    - node: initializer
    - type: loop
      body:
        type: sequential
        steps:
          - node: processor
          - gate: continue_loop
            condition: "processor.has_more == true"
      termination:
        max_iterations: 10
        condition: "processor.has_more == false"  # Optional: early exit condition
    - node: finalizer
```

**Use when**: You need to iterate until a condition is met or a maximum number of iterations is reached.

#### 5b. List Iteration (with iterate_over)

Iterate over a list/array from a previous agent's output:

```yaml
pattern:
  type: sequential
  steps:
    - node: scanner
    - type: loop
      condition: "scanner.total_count > 0"  # Optional: skip loop if list is empty
      iterate_over: "scanner.items_list"   # Path to the list/array
      loop_item_key: "current_item"         # Context key for current item (default: "loop_item")
      termination:
        max_iterations: 100  # Optional: safety limit to prevent infinite loops
      body:
        type: sequential
        steps:
          - node: processor  # current_item is automatically available in context
          - node: validator
          - node: recorder
    - node: finalizer
```

**Key Features**:
- **`iterate_over`**: Path to the list/array to iterate over (e.g., `"scanner.pending_items"`)
- **`loop_item_key`**: Context key where the current item is injected (default: `"loop_item"`)
- **`max_iterations`**: Optional safety limit (recommended for large lists)
- **`condition`**: Optional pattern-level condition to skip the loop entirely if the list is empty

**Accessing the Current Item**:
- In agent prompts: Use `{{current_item.field_name}}` or `{{loop_item.field_name}}` (depending on `loop_item_key`)
- In agent inputs: Use `{{current_item.field_name}}` in the YAML input mapping
- The loop automatically terminates when all items in the list are processed

**Accessing Accumulated Results** (when `accumulate_results=true`, default):
- After the loop completes, downstream agents can access all loop iteration results using `{agent_id}_instances`
- Example: If `validator` runs inside a loop, use `{{validator_instances}}` in downstream agents
- The `*_instances` dictionary contains keys like `validator_0`, `validator_1`, etc., with each iteration's result
- This allows summary/aggregation agents to process all loop results, not just the last one

**Example from ECI Claims Vetter**:
```yaml
- type: loop
  condition: "eci_pending_claims_scanner.total_pending_count > 0"
  iterate_over: "eci_pending_claims_scanner.pending_claims_list"
  loop_item_key: "current_claim"
  termination:
    max_iterations: 100  # Safety limit
  body:
    type: sequential
    steps:
      - node: eci_claims_extractor  # Accesses current_claim.claim_id, current_claim.claim_form_path, etc.
      - node: eci_claim_validator    # Accesses current_claim.claim_id
```

**Use when**: You have a list of items to process (e.g., pending claims, files, emails, orders) and want to process each item through the same sequence of steps.

### 6. Repeat Pattern

Run the same agent multiple times in parallel with different inputs:

```yaml
pattern:
  type: sequential
  steps:
    - node: file_scanner
    - type: parallel
      repeat:
        node: processor
        instances: "file_scanner.file_count"
        instance_id_template: "processor_{{index}}"
        input_mapping:
          user_text: "{{file_scanner.file_paths[index]}}"
    - node: aggregator
```

**Use when**: You need to process multiple items in parallel (e.g., multiple files, multiple problems).

### 7. Nested Patterns

Combine patterns for complex workflows:

```yaml
pattern:
  type: sequential
  steps:
    - node: coordinator
    - type: parallel
      steps:
        - type: sequential
          condition: "coordinator.needs_flights == true"
          steps:
            - node: flights_expert
            - gate: select_flights
        - type: sequential
          condition: "coordinator.needs_hotels == true"
          steps:
            - node: hotels_expert
            - gate: select_hotels
    - node: aggregator
```

**Use when**: You need complex workflows with conditional parallel execution.

## 🎯 Accessing Agent Outputs

In your patterns, you can access outputs from previous agents using Jinja2 expressions:

```yaml
pattern:
  type: sequential
  steps:
    - node: agent1
    - node: agent2
      # agent2 can access agent1's output
      # In agent2's prompt, use: {{agent1.field_name}}
```

**Example**: If `agent1` returns `{"summary": "..."}`, you can access it in `agent2`'s prompt as `{{agent1.summary}}`.

## 🚀 Running Your Project

### Start All Services

```bash
topaz-agent-kit serve all --project .
```

This starts:
- FastAPI server (UI) on `http://127.0.0.1:8090`
- MCP server on `http://127.0.0.1:8050`

### Start Individual Services

```bash
# UI only
topaz-agent-kit serve fastapi --project .

# CLI only
topaz-agent-kit serve cli --project .

# MCP server only
topaz-agent-kit serve mcp --project .
```

### Validate Configuration

```bash
topaz-agent-kit validate .
```

## 📚 Next Steps

1. **Customize the example pipeline**: Edit `config/pipelines/example.yml` and `config/agents/hello_agent.yml`
2. **Add your own agents**: Follow the [Adding a New Pipeline](#adding-a-new-pipeline) guide
3. **Explore patterns**: Try different execution patterns for your use case
4. **Use independent agents**: The project includes several independent agents (content_analyzer, rag_query, etc.) that can be used directly
5. **Check the documentation**: Visit the [Topaz Agent Kit documentation](https://docs.topaz-agent-kit.com) for advanced features

## 🆘 Troubleshooting

### Environment Variables Not Loading

- Make sure `.env` exists (copy from `.env.example`)
- Check that variable names match exactly (case-sensitive)
- Restart the services after changing `.env`

### Agents Not Generating

- Run `topaz-agent-kit generate agents --project .` after creating agent configs
- Check that agent YAML files are valid
- Verify `config/pipeline.yml` references your agents correctly

### Pipeline Not Appearing in UI

- Make sure the pipeline is registered in `config/pipeline.yml`
- Create a UI manifest in `config/ui_manifests/`
- Add the pipeline to `config/ui_manifest.yml`
- Regenerate diagrams: `topaz-agent-kit generate diagrams --project .`

---

**Happy Building! 🎉**

