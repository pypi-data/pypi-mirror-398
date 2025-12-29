"""
Omium Chat - AI-assisted workflow building and debugging.

This module provides an interactive chat interface for building workflows
with AI assistance and getting help with debugging.
"""

import asyncio
import json
import os
import httpx
from typing import Optional, Dict, Any, List
from pathlib import Path

from omium.output import (
    console, print_success, print_error, print_warning, print_info,
    print_header, print_panel, print_json, print_divider, OmiumSpinner
)
from omium.config import get_config

# Omium-specific system prompt for AI assistant
OMIUM_SYSTEM_PROMPT = """You are the Omium AI Assistant, an expert on the Omium platform - a fault-tolerant operating system for multi-agent AI workflows.

Your knowledge includes:
1. **Omium CLI Commands:**
   - `omium init` - Initialize SDK configuration
   - `omium run <workflow.json>` - Execute a workflow
   - `omium list` - List recent executions
   - `omium show <execution-id>` - Show execution details
   - `omium logs <execution-id>` - Stream live logs
   - `omium status <execution-id>` - Watch execution status
   - `omium replay <execution-id>` - Replay from checkpoint
   - `omium rollback <execution-id> <checkpoint-id>` - Rollback to checkpoint
   - `omium new` - Create workflow from template
   - `omium tui` - Launch interactive dashboard

2. **Workflow Types:**
   - CrewAI workflows: Define agents with roles, goals, backstory, and tasks
   - LangGraph workflows: State machines with nodes and edges
   - Multi-agent workflows: Teams of agents working together

3. **Fault Tolerance:**
   - Automatic checkpointing during execution
   - Rollback to any checkpoint on failure
   - Replay from checkpoints for debugging
   - Consensus-based coordination for distributed execution

4. **Best Practices:**
   - Use descriptive workflow IDs
   - Set appropriate checkpoint intervals
   - Monitor executions with `omium logs` and `omium status`
   - Use the TUI dashboard for visual monitoring

Be concise, helpful, and provide code examples when relevant. Format responses with markdown."""


# Workflow templates for quick scaffolding
WORKFLOW_TEMPLATES = {
    "crewai": {
        "type": "crewai",
        "workflow_id": "my-crewai-workflow",
        "agent_id": "agent-1",
        "inputs": {},
        "definition": {
            "agents": [{"name": "researcher", "role": "Research Specialist", "goal": "Find relevant information", "backstory": "Expert researcher", "tools": []}],
            "tasks": [{"description": "Research the given topic", "agent": "researcher", "expected_output": "Comprehensive research report"}]
        }
    },
    "langgraph": {
        "type": "langgraph",
        "workflow_id": "my-langgraph-workflow",
        "agent_id": "agent-1",
        "inputs": {},
        "definition": {
            "nodes": ["start", "process", "end"],
            "edges": [{"from": "start", "to": "process"}, {"from": "process", "to": "end"}],
            "state_schema": {"messages": "list", "context": "dict"}
        }
    },
    "multi-agent": {
        "type": "crewai",
        "workflow_id": "multi-agent-workflow",
        "agent_id": "orchestrator",
        "inputs": {},
        "definition": {
            "agents": [
                {"name": "researcher", "role": "Research Specialist", "goal": "Gather information", "backstory": "Expert at finding data", "tools": []},
                {"name": "analyst", "role": "Data Analyst", "goal": "Analyze information", "backstory": "Expert at insights", "tools": []},
                {"name": "writer", "role": "Content Writer", "goal": "Create content", "backstory": "Expert communicator", "tools": []}
            ],
            "tasks": [
                {"description": "Research the topic", "agent": "researcher", "expected_output": "Research findings"},
                {"description": "Analyze the research", "agent": "analyst", "expected_output": "Analysis report"},
                {"description": "Write the final report", "agent": "writer", "expected_output": "Final document"}
            ]
        }
    }
}


def get_available_templates() -> List[str]:
    """Get list of available workflow templates."""
    return list(WORKFLOW_TEMPLATES.keys())


def get_template(name: str) -> Optional[Dict[str, Any]]:
    """Get a workflow template by name."""
    return WORKFLOW_TEMPLATES.get(name)


def create_workflow_from_template(template_name: str, workflow_id: str, output_path: Optional[str] = None) -> Optional[str]:
    """Create a workflow file from a template."""
    import copy
    template = get_template(template_name)
    if not template:
        print_error(f"Unknown template: {template_name}")
        return None
    
    workflow = copy.deepcopy(template)
    workflow["workflow_id"] = workflow_id
    
    if not output_path:
        output_path = f"{workflow_id}.json"
    
    try:
        with open(output_path, "w") as f:
            json.dump(workflow, f, indent=2)
        print_success(f"Created workflow: {output_path}")
        return output_path
    except Exception as e:
        print_error(f"Failed to create workflow: {e}")
        return None


class ChatSession:
    """Interactive chat session for workflow assistance with real LLM."""
    
    def __init__(self):
        self.history: List[Dict[str, str]] = []
        self.context: Dict[str, Any] = {}
        
        # Get LLM credentials from environment
        self.api_key = os.getenv("DO_MODEL_ACCESS_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("DO_INFERENCE_BASE_URL") or os.getenv("OPENAI_BASE_URL") or "https://inference.do-ai.run/v1"
        self.model = os.getenv("OMIUM_CHAT_MODEL") or "llama3.3-70b-instruct"
        
        # Check if LLM is available
        self.llm_available = bool(self.api_key and self.base_url)
        
        if not self.llm_available:
            console.print("[yellow]⚠ LLM not configured. Using offline mode.[/yellow]")
            console.print("[dim]Set DO_MODEL_ACCESS_KEY or OPENAI_API_KEY for AI responses.[/dim]")
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the chat history."""
        self.history.append({"role": role, "content": content})
    
    def get_response(self, user_input: str) -> str:
        """Get a response to user input using LLM or fallback."""
        self.add_message("user", user_input)
        
        if self.llm_available:
            try:
                response = asyncio.run(self._get_llm_response(user_input))
            except Exception as e:
                console.print(f"[dim]LLM error: {e}. Using offline mode.[/dim]")
                response = self._get_fallback_response(user_input)
        else:
            response = self._get_fallback_response(user_input)
        
        self.add_message("assistant", response)
        return response
    
    async def _get_llm_response(self, user_input: str) -> str:
        """Get response from DigitalOcean LLM API."""
        # Build messages with system prompt and history
        messages = [{"role": "system", "content": OMIUM_SYSTEM_PROMPT}]
        
        # Add recent history (last 10 messages for context)
        for msg in self.history[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # base_url is https://inference.do-ai.run/v1, append /chat/completions
            api_url = f"{self.base_url.rstrip('/')}/chat/completions"
            response = await client.post(
                api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    def _get_fallback_response(self, user_input: str) -> str:
        """Fallback to rule-based response when LLM unavailable."""
        input_lower = user_input.lower().strip()
        
        if any(word in input_lower for word in ["help", "what can you do", "commands"]):
            return self._help_response()
        elif any(word in input_lower for word in ["create", "new", "workflow"]):
            return self._create_workflow_response(input_lower)
        elif any(word in input_lower for word in ["list", "show", "templates"]):
            return self._list_templates_response()
        elif any(word in input_lower for word in ["run", "execute"]):
            return self._run_response()
        elif any(word in input_lower for word in ["error", "debug", "fix", "issue"]):
            return self._debug_response()
        elif any(word in input_lower for word in ["checkpoint", "rollback", "recover"]):
            return self._checkpoint_response()
        elif "bye" in input_lower or "exit" in input_lower or "quit" in input_lower:
            return "Goodbye! Happy building with Omium. 🚀"
        else:
            return self._default_response()
    
    def _help_response(self) -> str:
        return """I can help you with:

📝 **Creating Workflows**
   - "Create a new CrewAI workflow"
   - "Make a multi-agent research workflow"

📋 **Templates**
   - "Show me available templates"
   - "List workflow templates"

🚀 **Running**
   - "How do I run a workflow?"
   - "Execute my workflow"

🔍 **Debugging**
   - "My workflow failed, help me debug"
   - "How do I rollback to a checkpoint?"

What would you like to do?"""
    
    def _create_workflow_response(self, input_text: str) -> str:
        if "crewai" in input_text:
            return """Great! I'll help you create a CrewAI workflow.

Run this command to create one:
```
omium init-workflow --type crewai --name my-crew -o workflow.json
```

Or use the template directly:
```python
omium new --template crewai
```

Would you like me to explain the CrewAI workflow structure?"""
        elif "langgraph" in input_text:
            return """I'll help you create a LangGraph workflow.

Run this command:
```
omium init-workflow --type langgraph --name my-graph -o workflow.json
```

LangGraph workflows use nodes and edges to define state transitions.
Would you like more details on the structure?"""
        elif "multi" in input_text or "research" in input_text:
            return """For a multi-agent workflow, I recommend the multi-agent template:

```
omium new --template multi-agent
```

This creates a workflow with:
- 🔍 Researcher agent
- 📊 Analyst agent  
- ✍️ Writer agent

They work together in a pipeline. Want me to explain how to customize it?"""
        else:
            return """What type of workflow would you like to create?

1. **CrewAI** - AI agents with roles, goals, and tasks
2. **LangGraph** - State machines with nodes and edges
3. **Multi-Agent** - Pre-configured team of agents

Just say "create a crewai workflow" or "new langgraph workflow"."""
    
    def _list_templates_response(self) -> str:
        templates = get_available_templates()
        template_list = "\n".join(f"  • {t}" for t in templates)
        return f"""Available workflow templates:

{template_list}

Use `omium new --template <name>` to create from a template.
Or ask me "create a <template> workflow" for guidance."""
    
    def _run_response(self) -> str:
        return """To run a workflow:

```bash
omium run workflow.json
```

Options:
- `--execution-id` - Custom execution ID
- `--checkpoint-manager` - Checkpoint service URL

Monitor with:
```bash
omium logs <execution-id>
omium status <execution-id>
```

Would you like to see an example workflow file?"""
    
    def _debug_response(self) -> str:
        return """Let me help you debug! Here are some common steps:

1️⃣ **Check execution status**
   ```
   omium show <execution-id>
   ```

2️⃣ **View logs**
   ```
   omium logs <execution-id>
   ```

3️⃣ **List checkpoints**
   ```
   omium checkpoints list <execution-id>
   ```

4️⃣ **Rollback to checkpoint**
   ```
   omium rollback <execution-id> <checkpoint-id>
   ```

What error are you seeing? I can provide more specific help."""
    
    def _checkpoint_response(self) -> str:
        return """Omium provides fault-tolerance through checkpoints.

**List checkpoints:**
```
omium checkpoints list <execution-id>
```

**Rollback to a checkpoint:**
```
omium rollback <execution-id> <checkpoint-id>
```

**Replay from checkpoint:**
```
omium replay <execution-id> --checkpoint-id <id>
```

Checkpoints save agent state automatically during execution.
Want to learn more about the checkpoint system?"""
    
    def _default_response(self) -> str:
        return """I'm here to help with Omium workflows! 

Try asking:
- "Help me create a workflow"
- "Show me templates"
- "How do I debug my workflow?"

Or type 'help' for full list of topics."""


def run_chat_session():
    """Run an interactive chat session."""
    print_header("Omium Chat", "AI-assisted workflow building")
    
    console.print("[dim]Type 'help' for available commands, 'exit' to quit[/dim]")
    console.print()
    
    session = ChatSession()
    
    # Initial greeting
    greeting = session.get_response("help")
    print_panel(greeting, title="🤖 Omium Assistant", style="cyan")
    
    while True:
        try:
            console.print()
            user_input = console.input("[bold cyan]You:[/bold cyan] ")
            
            if not user_input.strip():
                continue
            
            if user_input.lower().strip() in ["exit", "quit", "bye", "q"]:
                console.print("[dim]Goodbye! 👋[/dim]")
                break
            
            response = session.get_response(user_input)
            console.print()
            print_panel(response, title="🤖 Assistant", style="blue")
            
        except KeyboardInterrupt:
            console.print("\n[dim]Chat session ended.[/dim]")
            break
        except EOFError:
            break


def run_new_workflow_wizard():
    """Run interactive workflow creation wizard."""
    print_header("New Workflow", "Create a workflow from template")
    
    console.print("[bold]Available templates:[/bold]")
    for i, name in enumerate(get_available_templates(), 1):
        console.print(f"  {i}. {name}")
    
    console.print()
    
    try:
        # Get template choice
        choice = console.input("[bold]Select template (1-3) or name:[/bold] ")
        
        templates = get_available_templates()
        if choice.isdigit() and 1 <= int(choice) <= len(templates):
            template_name = templates[int(choice) - 1]
        elif choice in templates:
            template_name = choice
        else:
            print_error("Invalid template selection")
            return
        
        # Get workflow name
        workflow_id = console.input("[bold]Workflow ID:[/bold] ") or "my-workflow"
        
        # Get output path
        output = console.input(f"[bold]Output file ({workflow_id}.json):[/bold] ") or f"{workflow_id}.json"
        
        # Create workflow
        console.print()
        result = create_workflow_from_template(template_name, workflow_id, output)
        
        if result:
            console.print()
            console.print(f"[dim]Edit the workflow file and run with:[/dim]")
            console.print(f"[bold]omium run {result}[/bold]")
            
    except KeyboardInterrupt:
        console.print("\n[dim]Wizard cancelled.[/dim]")
    except EOFError:
        pass
