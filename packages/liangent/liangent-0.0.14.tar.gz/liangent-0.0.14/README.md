# Lagent: Minimalist Lightweight Agent

> **Slogan**: Minimalist lightweight agent, your first usable agent.

[English](README.md) | [中文](README_CN.md)

---

**Lagent** is a lightweight, extensible, and memory-aware agent framework designed for building LLM-based applications. It is designed to be a **teaching prototype** and a practical solution for **simple tasks**.

Unlike complex frameworks that rely on heavy planning steps, Lagent focuses on solving problems through **forced tool usage constraints** and **dynamic prompt injection**. This approach significantly reduces hallucinations and improves usability for everyday tasks.

### ✨ Key Highlights

1.  **🛡️ Local Code Sandbox**: 
    *   Safely execute **Python** and **Shell** scripts locally.
    *   **Double Security Guarantee**: Configurable whitelists/blacklists for dependencies and commands.
    *   Prevents dangerous operations while allowing powerful automation.

2.  **📉 Hallucination Reduction via Dynamic Constraints**:
    *   **Minimum Tool Usage**: Define `MIN_TOOL_USE` (e.g., must use at least 1 tool). 
    *   **Dynamic Prompt Injection**: If the agent attempts to answer without meeting the quota, the system intercepts it and injects a prompt forcing it to "reflect" and use tools.

3.  **🔧 Simple Tool Registration**:
    *   Register tools using a simple `@tool` decorator.
    *   **Universal Compatibility**: Does *not* rely on specific "Function Calling" APIs. Parses JSON-like actions from text, allowing use with smaller models.

4.  **💾 Minimalist SQLite Storage**:
    *   Zero-config persistent storage for sessions and logs.

5.  **🔍 High Observability**:
    *   **Full Traceability**: Every step is recorded.
    *   **Console Debugging**: See the agent's full thought process, including the **complete prompts** sent to the LLM (System + History) using `show_prompts=True`.

6.  **☁️ Serverless Ready**:
    *   Built-in `fc_handler.py` for deployment on AWS Lambda, Google Cloud Functions, or Aliyun FC.

---

### 🚀 Getting Started

#### 1. Installation
```bash
pip install liangent
```

#### 2. Initialize Project
Go to your project directory and run:
```bash
lagent init
```
This generates two essential files:
*   `.env`: Configuration file (API Keys, etc.)
*   `AGENTS.md`: Agent identity and guidelines

Edit `.env` to set your API Key:
```env
OPENAI_API_KEY=sk-your-key-here
MODEL_NAME=gpt-3.5-turbo
```

#### 3. Write Code (main.py)
```python
from lagent import Lagent

# Initialize agent (loads .env automatically)
# show_prompts=True: Prints full prompts to console for debugging
client = Lagent(show_prompts=True)

query = "List files in current directory and calculate 123 * 456"
print(f"User: {query}")

# Stream response
print("Agent: ", end="", flush=True)
for event in client.stream(query):
    if event.get("event") == "thought":
        print(f"\n[Thinking] {event.get('content')}", end="", flush=True)
    elif event.get("event") == "final_answer":
        print(f"\n\n{event.get('content')}\n")
```

#### 4. Use CLI
Lagent comes with a handy CLI:

**Quick Chat in Terminal:**
```bash
lagent chat
```

**Start API Server:**
```bash
lagent start --port 8000
```
API Documentation: `http://localhost:8000/docs`

---

### 📝 Customizing Agent Behavior

The `AGENTS.md` file is the soul of your agent. Modify it to define its persona and rules.

```markdown
# Agent Guidelines

## Identity
You are a senior Python engineer.

## Behavior Rules
- Be concise.
- Always verify code logic using the python tool.
```
This content is automatically injected into the System Prompt.

### 🔧 Custom Tools

Register tools using the `@tool` decorator. **Google-style docstrings are mandatory** as they are used to generate the tool schema for the LLM.

```python
from lagent import tool

@tool
def calculate_bmi(weight: float, height: float) -> float:
    """
    Calculate Body Mass Index (BMI).
    
    Args:
        weight: Weight in kilograms (kg).
        height: Height in meters (m).
    """
    return weight / (height * height)
```