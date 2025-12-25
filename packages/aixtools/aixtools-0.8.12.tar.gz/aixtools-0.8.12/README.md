# AIXtools

AIXtools is a comprehensive Python library for AI agent development, debugging, and deployment. It provides a complete toolkit for building, testing, and monitoring AI agents with support for multiple model providers, advanced logging, and agent-to-agent communication.

## Capabilities

- **[Installation](#installation)**
- **[Environment Configuration](#environment-configuration)**
- **[Agents](#agents)** - Core agent functionality
  - Basic Agent Usage
  - Agent Development & Management
  - Agent Batch Processing
  - Node Debugging and Visualization
- **[Context Engineering](#context-engineering)** - Transform files into agent-readable content
  - File Type Processors
  - Configuration
  - Processing Examples
- **[Agent-to-Agent Communication](#a2a-agent-to-agent-communication)** - Inter-agent communication framework
  - Core Features
  - Google SDK Integration
  - Remote Agent Connections
- **[Testing & Tools](#testing--tools)** - Comprehensive testing utilities
  - Running Tests
  - Testing Utilities
  - Mock Tool System
  - Model Patch Caching
  - Agent Mock
  - FaultyMCP Testing Server
  - MCP Tool Doctor
  - Tool Doctor
  - Evaluations
- **[Logging & Debugging](#logging--debugging)** - Advanced logging and debugging
  - Basic Logging
  - Log Viewing Application
  - Object Logging
  - MCP Logging
- **[Databases](#databases)** - Traditional and vector database support
- **[Chainlit & HTTP Server](#chainlit--http-server)** - Web interfaces and server framework
  - Chainlit Integration
  - HTTP Server Framework
- **[Programming Utilities](#programming-utilities)** - Essential utilities
  - Persisted Dictionary
  - Enum with Description
  - Context Management
  - Configuration Management
  - File Utilities
  - Chainlit Utilities
  - Truncation Utilities

## Installation

```bash
uv add aixtools
```

**Updating**

```bash
uv add --upgrade aixtools
```

## Environment Configuration

AIXtools requires environment variables for model providers.

**IMPORTANT:** Create a `.env` file based on `.env_template`:

Here is an example configuration:

```bash
# Model family (azure, openai, or ollama)
MODEL_FAMILY=azure
MODEL_TIMEOUT=120

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your_endpoint.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-06-01
AZURE_OPENAI_API_KEY=your_secret_key
AZURE_MODEL_NAME=gpt-4o

# OpenAI
OPENAI_MODEL_NAME=gpt-4.5-preview
OPENAI_API_KEY=openai_api_key

# Ollama
OLLAMA_MODEL_NAME=llama3.2:3b-instruct-fp16
OLLAMA_LOCAL_URL=http://localhost:11434/v1
```

## Agents

### Basic Agent Usage

```python
from aixtools.agents.agent import get_agent, run_agent

async def main():
    agent = get_agent(system_prompt="You are a helpful assistant.")
    result, nodes = await run_agent(agent, "Explain quantum computing")
    print(result)
```

### Agent Development & Management

The agent system provides a unified interface for creating and managing AI agents across different model providers.

```python
from aixtools.agents.agent import get_agent, run_agent

# Create an agent with default model
agent = get_agent(system_prompt="You are a helpful assistant.")

# Run the agent
result, nodes = await run_agent(agent, "Tell me about AI")
```

### Node Debugging and Visualization

The `print_nodes` module provides a clean, indented output for easy reading of the node from agent execution.

```python
from aixtools.agents.print_nodes import print_nodes, print_node
from aixtools.agents.agent import get_agent, run_agent

agent = get_agent(system_prompt="You are a helpful assistant.")
result, nodes = await run_agent(agent, "Explain quantum computing")
# Print all execution nodes for debugging
print_nodes(nodes)
```

**Features:**
- Node Type Detection: Automatically handles different node types (`UserPromptNode`, `CallToolsNode`, `ModelRequestNode`, `End`)
- Formatted Output: Provides clean, indented output for easy reading
- Tool Call Visualization: Shows tool names and arguments for tool calls
- Text Content Display: Formats text parts with proper indentation
- Model Request Summary: Shows character count for model requests to avoid verbose output

**Node Types Supported:**
- `UserPromptNode` - Displays user prompts with indentation
- `CallToolsNode` - Shows tool calls with names and arguments
- `ModelRequestNode` - Summarizes model requests with character count
- `End` - Marks the end of execution (output suppressed by default)

### Agent Batch Processing

Process multiple agent queries simultaneously with built-in concurrency control and result aggregation.

```python
from aixtools.agents.agent_batch import agent_batch, AgentQueryParams

# Create query parameters
query_parameters = [
    AgentQueryParams(prompt="What is the meaning of life"),
    AgentQueryParams(prompt="Who is the prime minister of Canada")
]

# Run queries in batches
async for result in agent_batch(query_parameters):
    print(result)
```

## Context Engineering

Transform file formats into agent-readable content with enforced size limits to prevent context overflow. The main entry point is the `read_file()` function in `aixtools/agents/context/reader.py`, which provides automatic file type detection and delegates to specialized processors for each file type.

### Basic Usage

The `read_file()` function in `reader.py` is the main interface for processing files. It automatically detects file types and applies appropriate truncation strategies.

```python
from aixtools.agents.context.reader import read_file
from pathlib import Path

# Read a file with automatic type detection and truncation
result = read_file(Path("data.csv"))

if result.success:
    print(f"File type: {result.file_type}")
    print(f"Content length: {len(result.content)}")
    print(f"Truncation info: {result.truncation_info}")
    print(result.content)

# Optionally specify custom tokenizer and limits
result = read_file(
    Path("large_file.json"),
    max_tokens_per_file=10000,
    max_total_output=100000
)
```

### Architecture

The context engineering system is organized with `reader.py` as the main interface:
- `reader.py` - Main `read_file()` function with file type detection and processing coordination
- `config.py` - Configurable size limits and thresholds
- `processors/` - Specialized processors for each file type (text, code, JSON, CSV, PDF, etc.)
- `data_models.py` - Data classes for results and metadata

### Supported File Types

- Text files (`.txt`, `.log`, `.md`)
- Code files (Python, JavaScript, etc.)
- Structured data (`JSON`, `YAML`, `XML`)
- Tabular data (`CSV`, `TSV`)
- Documents (`PDF`, `DOCX`)
- Spreadsheets (`.xlsx`, `.xls`, `.ods`)
- Images (`PNG`, `JPEG`, `GIF`, `WEBP`)
- Audio files

### Key Features

- Automatic file type detection based on MIME types and extensions
- Token-based truncation with configurable limits per file
- Intelligent content sampling (head + tail rows for tabular data)
- Structure-aware truncation for `JSON`, `YAML`, and `XML`
- Markdown conversion for documents using `markitdown`
- Binary content support for images with metadata extraction
- Comprehensive error handling with partial results when possible

### Configuration

All limits are configurable via environment variables:

```bash
# Output limits
MAX_TOKENS_PER_FILE=5000
MAX_TOTAL_OUTPUT=50000

# Text truncation
MAX_LINES=200
MAX_LINE_LENGTH=1000

# Tabular truncation
MAX_COLUMNS=50
DEFAULT_ROWS_HEAD=20
DEFAULT_ROWS_MIDDLE=10
DEFAULT_ROWS_TAIL=10
MAX_CELL_LENGTH=500

# Images
MAX_IMAGE_ATTACHMENT_SIZE=2097152  # 2MB
```

### Processing Examples

The recommended approach is to use the `read_file()` function which automatically handles file type detection and processing. However, you can also use individual processors directly for specific file types.

#### Using read_file() (Recommended)

```python
from aixtools.agents.context.reader import read_file
from pathlib import Path

# Process any file type automatically
result = read_file(Path("data.csv"))
if result.success:
    print(result.content)

# Works with all supported types
pdf_result = read_file(Path("report.pdf"))
excel_result = read_file(Path("workbook.xlsx"))
json_result = read_file(Path("config.json"))
```

#### Processing Tabular Data Directly

```python
from aixtools.agents.context.processors.tabular import process_tabular
from pathlib import Path

# Process specific row range from large CSV
result = process_tabular(
    file_path=Path("large_data.csv"),
    start_row=100,
    end_row=200,
    max_columns=20,
    max_cell_length=500
)

print(f"Rows shown: {result.truncation_info.rows_shown}")
print(f"Columns shown: {result.truncation_info.columns_shown}")
```

#### Processing Spreadsheets Directly

```python
from aixtools.agents.context.processors.spreadsheet import process_spreadsheet
from pathlib import Path

# Process Excel file with multiple sheets
result = process_spreadsheet(
    file_path=Path("workbook.xlsx"),
    max_sheets=3,
    max_rows_per_sheet_head=20,
    max_rows_per_sheet_tail=10
)

# Content includes all processed sheets with truncation info
print(result.content)
```

#### Processing Documents Directly

```python
from aixtools.agents.context.processors.document import process_document
from pathlib import Path

# Convert PDF to markdown and truncate
result = process_document(
    file_path=Path("report.pdf"),
    max_lines=200,
    max_line_length=1000
)

if result.was_extracted:
    print("Document successfully converted to markdown")
    print(result.content)
```

### Output Format

All processors return consistent output with metadata:

```
File: data.csv
Columns: 8 (of 20000 total)
Rows: 20 (of 1000000 total)

col1,col2,...,col8
value1,value2,...
...

Truncated: columns: 8 of 20000, rows: 20 of 1000000, 45 cells
```

The context engineering system ensures agents receive properly formatted, size-limited content that fits within token budgets while preserving the most relevant information from each file type.

## A2A (Agent-to-Agent Communication)

The `A2A` module provides a comprehensive framework for enabling sophisticated communication between AI agents across different environments and platforms. It includes Google SDK integration, `PydanticAI` adapters, and `FastA2A` application conversion capabilities.

### Core Features

**Agent Application Conversion**
- Convert `PydanticAI` agents into `FastA2A` applications (deprecated)
- Support for session metadata extraction and context management
- Custom worker classes with enhanced data part support
- Automatic handling of user and session identification

**Remote Agent Connections**
- Establish connections between agents across different environments
- Asynchronous message sending with task polling capabilities
- Terminal state detection and error handling
- Support for various message types including text, files, and data

**Google SDK Integration**
- Native integration with Google's A2A SDK
- Card-based agent representation and discovery
- `PydanticAI` adapter for seamless Google SDK compatibility
- Storage and execution management for agent interactions

### Basic Usage

Enable sophisticated agent interactions with Google SDK integration and `PydanticAI` adapters.

```python
from aixtools.a2a.google_sdk.remote_agent_connection import RemoteAgentConnection
from aixtools.a2a.app import agent_to_a2a

# Convert a PydanticAI agent to FastA2A application
a2a_app = agent_to_a2a(
    agent=my_agent,
    name="MyAgent",
    description="A helpful AI assistant",
    skills=[{"name": "chat", "description": "General conversation"}]
)

# Connect agents across different environments
connection = RemoteAgentConnection(card=agent_card, client=a2a_client)
response = await connection.send_message_with_polling(message)
```

### Postgres DB Store for A2A agent

See implementation: `aixtools/a2a/google_sdk/store`

#### Alembic

In order to take full control of the database schema management Alembic is used for handling database migrations.
Thus make sure, that google-sdk Store objects are being created with parameter create_table=False
```python
from a2a.server.tasks import DatabaseTaskStore

...

task_store=DatabaseTaskStore(engine=db_engine, create_table=False)
```

#### Setup of database and applying migrations (manual if needed):

configure POSTGRES_URL env variable
```.dotenv
POSTGRES_URL=postgresql+asyncpg://user:password@localhost:5432/a2a_magic_db
```


```shell
# from scope of your a2a service

#activate your virtual environment
kzwk877@degfqx35d621DD a2a_magic_service % source .venv/bin/activate
# set the PATH_TO_ALEMBIC_CONFIG environment variable to point to the alembic configuration directory
(a2a_magic_service) kzwk877@degfqx35d621DD a2a_magic_service % export PATH_TO_ALEMBIC_CONFIG="$(pwd)/.venv/lib/python3.12/site-packages/aixtools/a2a/google_sdk/store"
# Make sure that database is existed
(a2a_magic_service) kzwk877@degfqx35d621DD a2a_magic_service % uv run "${PATH_TO_ALEMBIC_CONFIG}/ensure_database.py"
2025-11-11 10:08:51.501 WARNING  [root] Looking for '.env' file in default directory
2025-11-11 10:08:52.750 INFO     [root] Using .env file at '/PATH_TO_A2A_SERVICE/a2a_magic_service/.env'
2025-11-11 10:08:52.751 INFO     [root] Using MAIN_PROJECT_DIR='/PATH_TO_A2A_SERVICE/a2a_magic_service'
2025-11-11 10:08:52.752 WARNING  [root] Using         DATA_DIR='/app/data'
2025-11-11 10:08:52.757 INFO     [__main__] Starting database creation script...
...
2025-11-11 10:08:52.821 INFO     [__main__] Creating database 'a2a_magic_db'...
2025-11-11 10:08:52.904 INFO     [__main__] Database 'a2a_magic_db' created successfully
...
2025-11-11 10:08:52.921 INFO     [__main__] Database creation script completed successfully!
# Apply alembic migrations
(a2a_magic_service) kzwk877@degfqx35d621DD a2a_magic_service % alembic --config "${PATH_TO_ALEMBIC_CONFIG}/alembic.ini" upgrade head
2025-11-11 10:11:34.185 WARNING  [root] Looking for '.env' file in default directory
2025-11-11 10:11:35.046 WARNING  [root] Looking for '.env' file at '/PATH_TO_A2A_SERVICE/a2a_magic_service'
2025-11-11 10:11:35.047 INFO     [root] Using .env file at '/PATH_TO_A2A_SERVICE/a2a_magic_service/.env'
2025-11-11 10:11:35.048 INFO     [root] Using MAIN_PROJECT_DIR='/PATH_TO_A2A_SERVICE/a2a_magic_service'
2025-11-11 10:11:35.049 WARNING  [root] Using         DATA_DIR='/app/data'
2025-11-11 10:11:35.054 INFO     [env_py] Using database URL for migrations: postgresql://user:password@localhost:5432/a2a_magic_db
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 68c6975ed20b, Added a2a-sdk Task table
```

#### Schema modifications

if new schema modifications has been introduced with new versions of a2a sdk suggested way 
to create new alembic migrations would be:

- launch a2a service with passed parameter to `DatabaseStore` `create_table=True`
- make sure that all new tables/columns are created in 
the database (possibly an new request to a2a server needs to be made)
- create new alembic migration script
```shell
(a2a_magic_service) kzwk877@degfqx35d621DD % alembic --config "${PATH_TO_ALEMBIC_CONFIG}/alembic.ini" revision --autogenerate -m "New table introduced"
```
- review the generated migration script
- apply and test

## Databases

### Database Integration

Support for both traditional and vector databases with seamless integration.

```python
from aixtools.db.database import Database
from aixtools.db.vector_db import VectorDB

# Traditional database
db = Database("sqlite:///app.db")

# Vector database for embeddings
vector_db = VectorDB()
vector_db.add_documents(documents)
```

## Logging & Debugging

AixTools provides functionality for logging and debugging.

### Basic Logging and Debugging

```python
from aixtools.agents.agent import get_agent, run_agent

async def main():
    # Create an agent
    agent = get_agent(system_prompt="You are a helpful assistant.")

    # Run agent - logging is automatic via ObjectLogger
    result, nodes = await run_agent(
        agent,
        "Explain quantum computing",
        debug=True,  # Enable debug logging
        log_model_requests=True  # Log model requests/responses
    )

    print(f"Result: {result}")
    print(f"Logged {len(nodes)} nodes")
```

### Log Viewing Application

Interactive `Streamlit` application for analyzing logged objects and debugging agent behavior.

**Features:**
- Log file selection and filtering
- Node visualization with expand/collapse
- Export capabilities to `JSON`
- Regex pattern matching
- Real-time log monitoring

```bash
# Run the log viewer
log_view

# Or specify custom log directory
log_view /path/to/logs
```

### Object Logging & Debugging

Advanced logging system with object serialization and visual debugging tools.

```python
from aixtools.logging.log_objects import ObjectLogger

# Log any pickleable object
with ObjectLogger() as logger:
    logger.log({"message": "Hello, world!"})
    logger.log(agent_response)
```

### MCP Logging

AIXtools provides MCP support for both client and server implementations with easier logging for debugging purposes.

**Example:**

Let's assume we have an MCP server that runs an agent tool.

Note that the `ctx: Context` parameter is passed to `run_agent()`, this will enable logging to the MCP client.

```python
@mcp.tool
async def my_tool_with_agent(query: str, ctx: Context) -> str:
    """ A tool that uses an gents to process the query """
    agent = get_agent()
    async with get_qb_agent() as agent:
        ret, nodes = await run_agent(agent=agent, prompt=query, ctx=ctx)    # Enable MCP logging
        return str(ret)
```

On the client side, you can create an agent connected to the MCP server, the nodes from the MCP server will show on the `STDOUT` so you can see what's going on the MCP server's agent loop.

```python
mcp = get_mcp_client("http://localhost:8000")   # Get an MCP client with a default log handler that prints to STDOUT
agent = get_agent(toolsets=[mcp])
async with agent:
    # The messages from the MCP server will be printed to the STDOUT
    ret, nodes = await run_agent(agent, prompt="...")
```

#### MCP Server Logging

Create MCP servers with built-in logging capabilities.

```python
from aixtools.mcp.fast_mcp_log import FastMcpLog

# Use FastMCP server with logging
mcp = FastMcpLog("Demo")
```

## Testing & Tools

AIXtools provides comprehensive testing utilities and diagnostic tools for AI agent development and debugging.

### Running Tests

Execute the test suite using the provided scripts:

```bash
# Run all tests
./scripts/test.sh

# Run unit tests only
./scripts/test_unit.sh

# Run integration tests only
./scripts/test_integration.sh
```

### Testing Utilities

The testing module provides mock tools, model patching, and test utilities for comprehensive agent testing.

```python
from aixtools.testing.mock_tool import MockTool
from aixtools.testing.model_patch_cache import ModelPatchCache
from aixtools.testing.aix_test_model import AixTestModel

# Create mock tools for testing
mock_tool = MockTool(name="test_tool", response="mock response")

# Use model patch caching for consistent test results
cache = ModelPatchCache()
cached_response = cache.get_cached_response("test_prompt")

# Test model for controlled testing scenarios
test_model = AixTestModel()
```

### Mock Tool System

Create and manage mock tools for testing agent behavior without external dependencies.

```python
from aixtools.testing.mock_tool import MockTool

# Create a mock tool with predefined responses
mock_calculator = MockTool(
    name="calculator",
    description="Performs mathematical calculations",
    response_map={
        "2+2": "4",
        "10*5": "50"
    }
)

# Use in agent testing
agent = get_agent(tools=[mock_calculator])
result = await run_agent(agent, "What is 2+2?")
```

### Model Patch Caching

Cache model responses for consistent testing and development workflows.

```python
from aixtools.testing.model_patch_cache import ModelPatchCache

# Initialize cache
cache = ModelPatchCache(cache_dir="./test_cache")

# Cache responses for specific prompts
cache.cache_response("test prompt", "cached response")

# Retrieve cached responses
response = cache.get_cached_response("test prompt")
```

### Model Patching System

Dynamic model behavior modification for testing and debugging.

```python
from aixtools.model_patch.model_patch import ModelPatch

# Apply patches to models for testing
with ModelPatch() as patch:
    patch.apply_response_override("test response")
    result = await agent.run("test prompt")
```

### Agent Mock

Replay previously recorded agent runs without executing the actual agent. Useful for testing, debugging, and creating reproducible test cases.

```python
from aixtools.testing.agent_mock import AgentMock
from aixtools.agents.agent import get_agent, run_agent

# Run an agent and capture its execution
agent = get_agent(system_prompt="You are a helpful assistant.")
result, nodes = await run_agent(agent, "Explain quantum computing")

# Create a mock agent from the recorded nodes
agent_mock = AgentMock(nodes=nodes, result_output=result)

# Save the mock for later use
agent_mock.save(Path("test_data/quantum_mock.pkl"))

# Load and replay the mock agent
loaded_mock = AgentMock.load(Path("test_data/quantum_mock.pkl"))
result, nodes = await run_agent(loaded_mock, "any prompt")  # Returns recorded nodes
```

### FaultyMCP Testing Server

A specialized MCP server designed for testing error handling and resilience in MCP client implementations. `FaultyMCP` simulates various failure scenarios including network errors, server crashes, and random exceptions.

**Features:**
- Configurable error probabilities for different request types
- HTTP 404 error injection for `POST`/`DELETE` requests
- Server crash simulation on `GET` requests
- Random exception throwing in tool operations
- MCP-specific error simulation (`ValidationError`, `ResourceError`, etc.)
- Safe mode for controlled testing

```python
from aixtools.mcp.faulty_mcp import run_server_on_port, config

# Configure error probabilities
config.prob_on_post_404 = 0.3      # 30% chance of 404 on POST
config.prob_on_get_crash = 0.1     # 10% chance of crash on GET
config.prob_in_list_tools_throw = 0.2  # 20% chance of exception in tools/list

# Run the faulty server
run_server_on_port()
```

**Command Line Usage:**

```bash
# Run with default error probabilities
python -m aixtools.mcp.faulty_mcp

# Run in safe mode (no errors by default)
python -m aixtools.mcp.faulty_mcp --safe-mode

# Custom configuration
python -m aixtools.mcp.faulty_mcp \
    --port 8888 \
    --prob-on-post-404 0.2 \
    --prob-on-get-crash 0.1 \
    --prob-in-list-tools-throw 0.3
```

**Available Test Tools:**
- `add(a, b)` - Reliable addition operation
- `multiply(a, b)` - Reliable multiplication operation
- `always_error()` - Always throws an exception
- `random_throw_exception(a, b, prob)` - Randomly throws exceptions
- `freeze_server(seconds)` - Simulates server freeze
- `throw_404_exception()` - Throws HTTP 404 error

### MCP Tool Doctor

Analyze tools from MCP (Model Context Protocol) servers and receive AI-powered recommendations for improvement.

```python
from aixtools.tools.doctor.mcp_tool_doctor import tool_doctor_mcp
from pydantic_ai.mcp import MCPServerStreamableHTTP, MCPServerStdio

# Analyze HTTP MCP server
recommendations = await tool_doctor_mcp(mcp_url='http://127.0.0.1:8000/mcp')
for rec in recommendations:
    print(rec)

# Analyze STDIO MCP server
server = MCPServerStdio(command='fastmcp', args=['run', 'my_server.py'])
recommendations = await tool_doctor_mcp(mcp_server=server, verbose=True)
```

**Command Line Usage:**

```bash
# Analyze HTTP MCP server (default)
tool_doctor_mcp

# Analyze specific HTTP MCP server
tool_doctor_mcp --mcp-url http://localhost:9000/mcp --verbose

# Analyze STDIO MCP server
tool_doctor_mcp --stdio-command fastmcp --stdio-args run my_server.py --debug
```

**Available options:**
- `--mcp-url URL` - URL of HTTP MCP server (default: `http://127.0.0.1:8000/mcp`)
- `--stdio-command CMD` - Command to run STDIO MCP server
- `--stdio-args ARGS` - Arguments for STDIO MCP server command
- `--verbose` - Enable verbose output
- `--debug` - Enable debug output

### Tool Doctor

Analyze tool usage patterns from agent logs and get optimization recommendations.

```python
from aixtools.tools.doctor.tool_doctor import ToolDoctor
from aixtools.tools.doctor.tool_recommendation import ToolRecommendation

# Analyze tool usage patterns
doctor = ToolDoctor()
analysis = doctor.analyze_tools(agent_logs)

# Get tool recommendations
recommendation = ToolRecommendation()
suggestions = recommendation.recommend_tools(agent_context)
```

### Evaluations

Run comprehensive Agent/LLM evaluations using the built-in evaluation discovery based on `Pydantic-AI` framework with AIXtools enhancements.

```bash
# Run all evaluations
python -m aixtools.evals

# Run evaluations with filtering
python -m aixtools.evals --filter "specific_test"

# Run with verbose output and detailed reporting
python -m aixtools.evals --verbose --include-input --include-output --include-reasons

# Specify custom evaluations directory
python -m aixtools.evals --evals-dir /path/to/evals

# Set minimum assertions threshold
python -m aixtools.evals --min-assertions 0.8
```

**Command Line Options:**
- `--evals-dir` - Directory containing `eval_*.py` files (default: `evals`)
- `--filter` - Filter to run only matching evaluations
- `--include-input` - Include input in report output (default: `True`)
- `--include-output` - Include output in report output (default: `True`)
- `--include-evaluator-failures` - Include evaluator failures in report
- `--include-reasons` - Include reasons in report output
- `--min-assertions` - Minimum assertions average required for success (default: `1.0`)
- `--verbose` - Print detailed information about discovery and processing

The evaluation system discovers and runs all `Dataset` objects from `eval_*.py` files in the specified directory, similar to test runners but specifically designed for LLM evaluations using `pydantic_evals`.

**Discovery Mechanism**

The evaluation framework uses an automatic discovery system:

1. **File Discovery**: Scans the specified directory for files matching the pattern `eval_*.py`
2. **Dataset Discovery**: Within each file, looks for variables named `dataset_*` that are instances of `pydantic_evals.Dataset`
3. **Target Function Discovery**: Within the same file looks for function or async function named `target_*`. There must be 1 target function per file.
4. **Function Discovery**: Looks for functions with specific prefixes:
   - Functions prefixed with `scorer_*`, `evaluator_*` for custom scorer and evaluator functions that will be used for each dataset in that file
5. **Filtering**: Supports filtering by module name, file name, dataset name, or fully qualified name

**Example Evaluation File Structure:**

```python
# eval_math_operations.py
from pydantic_evals import Dataset, Case

# This dataset will be discovered automatically
dataset_addition = Dataset(
    name="Addition Tests",
    cases=[
        Case(input="What is 2 + 2?", expected="4"),
        Case(input="What is 10 + 5?", expected="15"),
    ],
    evaluators=[...]
)

# This function will be used as the evaluation target
async def target_math_agent(input_text: str) -> str:
    # Your agent run logic here
    agent = get_agent(system_prompt="You are a math assistant.")
    result, _ = await run_agent(agent, input_text)
    return result

# This function will be used as evaluator for all datasets (optional)
def evaluator_check_output(ctx: EvaluatorContext) -> bool:
    # Your result evaluation logic here
    return ctx.output == ctx.expected_output
```

The discovery system will:
- Find `eval_math_operations.py` in the `evals` directory
- Discover `dataset_addition` as an evaluation dataset
- Use `evaluate_math_agent` as the target function for evaluation
- Run each case through the target function and evaluate results

#### Name-Based Discovery

The evaluation system uses name-based discovery for all components:

**Target Functions** (exactly one required per eval file):
- Purpose: The main function being evaluated - processes inputs and returns outputs
- Naming: Functions named `target_*` (e.g., `target_my_function`)
- Signature: `def target_name(inputs: InputType) -> OutputType` or `async def target_name(inputs: InputType) -> OutputType`
- Example: `async def target_math_agent(input_text: str) -> str`

**Scoring Functions** (optional):
- Purpose: Determine if evaluation results meet success criteria
- Naming: Functions named `scorer_*` (e.g., `scorer_custom`)
- Signature: `def scorer_name(report: EvaluationReport, dataset: AixDataset, min_score: float = 1.0, verbose: bool = False) -> bool`
- Example: `def scorer_accuracy_threshold(report, dataset, min_score=0.8, verbose=False) -> bool`

**Evaluator Functions** (optional):
- Purpose: Custom evaluation logic for comparing outputs with expected results
- Naming: Functions named `evaluator_*` (e.g., `evaluator_check_output`)
- Signature: `def evaluator_name(ctx: EvaluatorContext) -> EvaluatorOutput` or `async def evaluator_name(ctx: EvaluatorContext) -> EvaluatorOutput`
- Example: `def evaluator_exact_match(ctx) -> EvaluatorOutput`

This name-based approach works seamlessly with both synchronous and asynchronous functions.

#### Scoring System

The framework includes a custom scoring system with `average_assertions` as the default scorer. This scorer checks if the average assertion score meets a minimum threshold and provides detailed pass/fail reporting.

## Chainlit & HTTP Server

### Chainlit Integration

Ready-to-use `Chainlit` application for interactive agent interfaces.

```python
# Run the Chainlit app
# Configuration in aixtools/chainlit.md
# Main app in aixtools/app.py
```

### HTTP Server Framework

AIXtools provides an HTTP server framework for deploying agents and tools as web services.

```python
from aixtools.server.app_mounter import mount_app
from aixtools.server import create_server

# Create and configure server
server = create_server()

# Mount applications and endpoints
mount_app(server, "/agent", agent_app)
mount_app(server, "/tools", tools_app)

# Run server
server.run(host="0.0.0.0", port=8000)
```

**Features:**
- Application mounting system for modular service composition
- Integration with `Chainlit` for agent interfaces
- RESTful API support
- Middleware support for authentication and logging

## Programming Utilities

AIXtools provides essential programming utilities for configuration management, data persistence, file operations, and context handling.

### Persisted Dictionary

Persistent key-value storage with automatic serialization and file-based persistence.

```python
from aixtools.utils.persisted_dict import PersistedDict

# Create a persistent dictionary
cache = PersistedDict("cache.json")

# Store and retrieve data
cache["user_preferences"] = {"theme": "dark", "language": "en"}
cache["session_data"] = {"last_login": "2024-01-01"}

# Data is automatically saved to file
print(cache["user_preferences"])  # Persists across program restarts
```

### Enum with Description

Enhanced `Enum` classes with built-in descriptions for better documentation and user interfaces.

```python
from aixtools.utils.enum_with_description import EnumWithDescription

class ModelType(EnumWithDescription):
    GPT4 = ("gpt-4", "OpenAI GPT-4 model")
    CLAUDE = ("claude-3", "Anthropic Claude-3 model")
    LLAMA = ("llama-2", "Meta LLaMA-2 model")

# Access enum values and descriptions
print(ModelType.GPT4.value)        # "gpt-4"
print(ModelType.GPT4.description)  # "OpenAI GPT-4 model"

# Get all descriptions
for model in ModelType:
    print(f"{model.value}: {model.description}")
```

### Context Management

Centralized context management for sharing state across components.

```python
from aixtools.context import Context

# Create and use context
context = Context()
context.set("user_id", "12345")
context.set("session_data", {"preferences": {"theme": "dark"}})

# Retrieve context data
user_id = context.get("user_id")
session_data = context.get("session_data")

# Context can be passed between components
def process_request(ctx: Context):
    user_id = ctx.get("user_id")
    # Process with user context
```

### Configuration Management

Robust configuration handling with environment variable support and validation.

```python
from aixtools.utils.config import Config
from aixtools.utils.config_util import load_config

# Load configuration from environment and files
config = load_config()

# Access configuration values
model_name = config.get("MODEL_NAME", "gpt-4")
api_key = config.get("API_KEY")
timeout = config.get("TIMEOUT", 30, int)

# Configuration with validation
class AppConfig(Config):
    model_name: str = "gpt-4"
    max_tokens: int = 1000
    temperature: float = 0.7

app_config = AppConfig()
```

### File Utilities

Enhanced file operations with `Path` support and utility functions.

```python
from aixtools.utils.files import read_file, write_file, ensure_directory
from pathlib import Path

# Read and write files with automatic encoding handling
content = read_file("data.txt")
write_file("output.txt", "Hello, world!")

# Ensure directories exist
data_dir = Path("data/logs")
ensure_directory(data_dir)

# Work with file paths
config_path = Path("config") / "settings.json"
if config_path.exists():
    config_data = read_file(config_path)
```

### Chainlit Utilities

Specialized utilities for `Chainlit` integration and agent display.

```python
from aixtools.utils.chainlit.cl_agent_show import show_agent_response
from aixtools.utils.chainlit.cl_utils import format_message

# Display agent responses in Chainlit
await show_agent_response(
    response="Hello, how can I help you?",
    metadata={"model": "gpt-4", "tokens": 150}
)

# Format messages for Chainlit display
formatted_msg = format_message(
    content="Processing your request...",
    message_type="info"
)
```

### Truncation Utilities

Smart truncation utilities for handling large data structures and preventing context overflow in LLM applications.

```python
from aixtools.utils import (
    truncate_recursive_obj,
    truncate_df_to_csv,
    truncate_text_head_tail,
    truncate_text_middle,
    format_truncation_message,
    TruncationMetadata
)

# Truncate nested JSON/dict structures while preserving structure
data = {"items": [f"item_{i}" for i in range(1000)], "description": "A" * 10000}
truncated = truncate_recursive_obj(data, max_string_len=100, max_list_len=10)

# Get truncation metadata
result, metadata = truncate_recursive_obj(
    data,
    target_size=1000,
    ensure_size=True,
    return_metadata=True
)
print(f"Truncated: {metadata.was_truncated}")
print(f"Size: {metadata.original_size} → {metadata.truncated_size}")

# Truncate DataFrames to CSV with head+tail preview
import pandas as pd
df = pd.DataFrame({"col1": range(10000), "col2": ["x" * 200] * 10000})
csv_output = truncate_df_to_csv(
    df,
    max_rows=20,              # Show first 10 and last 10 rows
    max_columns=10,           # Show first 5 and last 5 columns
    max_cell_chars=80,        # Truncate cell contents
    max_row_chars=2000        # Truncate CSV lines
)

# Truncate text preserving head and tail
text = "A" * 10000
truncated, chars_removed = truncate_text_head_tail(text, head_chars=100, tail_chars=100)

# Truncate text in the middle
truncated, chars_removed = truncate_text_middle(text, max_chars=500)

# Format truncation messages
message = format_truncation_message(
    original_size=10000,
    truncated_size=500,
    unit="chars",
    recommendation="Consider processing in smaller chunks"
)
```

**Key Features:**
- **Structure-preserving truncation** - `truncate_recursive_obj()` maintains dict/list structure while truncating
- **DataFrame to CSV truncation** - `truncate_df_to_csv()` shows head+tail rows and left+right columns
- **Text truncation strategies** - Head+tail or middle truncation for different use cases
- **Type-safe metadata** - `TruncationMetadata` Pydantic model with full type hints
- **Size enforcement** - `ensure_size=True` guarantees output fits within target size
- **Informative messages** - Automatic generation of user-friendly truncation messages

**Truncation Metadata:**

All truncation functions support `return_metadata=True` to get detailed information:

```python
result, meta = truncate_recursive_obj(data, target_size=1000, return_metadata=True)

# TruncationMetadata attributes
meta.original_size    # Original size in characters
meta.truncated_size   # Final size after truncation
meta.was_truncated    # Whether truncation occurred
meta.strategy         # Strategy used: "none", "smart", "middle", "str"
```

### General Utilities

Common utility functions for everyday programming tasks.

```python
from aixtools.utils.utils import safe_json_loads, timestamp_now, hash_string

# Safe JSON parsing
data = safe_json_loads('{"key": "value"}', default={})

# Get current timestamp
now = timestamp_now()

# Generate hash for strings
file_hash = hash_string("content to hash")
```

