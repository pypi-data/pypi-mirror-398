"""
Omium CLI tool for local testing and workflow management.
"""

import asyncio
import click
import json
import sys
import httpx
import logging
import getpass
import platform
from typing import Optional, Dict, Any

from omium import OmiumClient
from omium.client import CheckpointError
from omium.config import get_config_manager, get_config, ConfigManager, OmiumConfig
from omium.remote_client import RemoteOmiumClient
from omium.output import (
    console, print_success, print_error, print_warning, print_info,
    print_header, print_panel, print_json, print_table, print_tree,
    print_welcome, print_step, print_divider, OmiumSpinner,
    create_progress_bar, progress_spinner
)
from omium.streaming import (
    stream_execution_logs, print_log_entry, watch_execution,
    get_execution_status
)
from omium.tui import OmiumApp
from omium.chat import run_chat_session, run_new_workflow_wizard, get_available_templates
from omium.project import OmiumProject, init_project, get_current_project

logger = logging.getLogger(__name__)


def _get_secure_input(prompt: str, default: str = "", allow_visible: bool = False) -> str:
    """
    Get input that works reliably on all platforms (Linux, macOS, Windows).
    
    On Windows/PowerShell, getpass doesn't show any feedback which confuses users.
    This function uses visible input with clear messaging for better UX.
    
    Args:
        prompt: Prompt text to display
        default: Default value if user presses Enter without input
        allow_visible: If True, always use visible input (recommended for API keys)
        
    Returns:
        User input or default value
    """
    is_windows = platform.system() == "Windows"
    
    # For API keys, use visible input on Windows since getpass provides no feedback
    # Users can't tell if paste worked or if they're typing
    if is_windows or allow_visible:
        try:
            if default:
                masked_default = f"{default[:8]}...{default[-4:]}" if len(default) > 12 else default[:4] + "..."
                value = click.prompt(
                    prompt,
                    default="",
                    show_default=False,
                    prompt_suffix=f" (current: {masked_default}, press Enter to keep): "
                )
                if not value or not value.strip():
                    return default
                return value.strip()
            else:
                # Show input normally - API keys aren't that sensitive in terminal
                # And users need to see that paste worked
                value = click.prompt(prompt, default="", show_default=False)
                return value.strip() if value else ""
        except (KeyboardInterrupt, EOFError):
            raise
    
    # On macOS/Linux, getpass works well
    try:
        if default:
            click.echo(f"{prompt} [{default[:20]}...] (press Enter to use default, or paste new): ", nl=False)
        else:
            click.echo(f"{prompt}: ", nl=False)
        
        value = getpass.getpass("")
        
        if not value or not value.strip():
            if default:
                return default
            return ""
        
        return value.strip()
        
    except (KeyboardInterrupt, EOFError):
        raise
    except Exception as e:
        logger.warning(f"Error with getpass, falling back to visible input: {e}")
        try:
            click.echo()
            return click.prompt(prompt, default=default, show_default=bool(default))
        except (KeyboardInterrupt, EOFError):
            raise


@click.group()
@click.version_option(version="0.2.0")
def cli():
    """Omium CLI - Fault-tolerant agent operating system."""
    pass


@cli.command("configure")
@click.option("--api-key", help="API key for authentication")
@click.option("--api-url", help="Omium API base URL")
@click.option("--region", help="AWS region")
@click.option("--interactive", "-i", is_flag=True, help="Interactive configuration")
def configure(api_key: Optional[str], api_url: Optional[str], region: Optional[str], interactive: bool):
    """
    Configure Omium SDK settings.
    
    This command sets up your API key, region, and other SDK settings.
    Configuration is saved to ~/.omium/config.json
    """
    config_manager = get_config_manager()
    current_config = config_manager.load()
    
    if interactive:
        click.echo("🔧 Omium SDK Configuration")
        click.echo("=" * 50)
        
        # API Key
        if not api_key:
            system = platform.system()
            if system == "Windows":
                paste_hint = "Paste with Ctrl+V or right-click"
            elif system == "Darwin":  # macOS
                paste_hint = "Paste with Cmd+V"
            else:  # Linux and others
                paste_hint = "Paste with Ctrl+Shift+V or right-click"
            
            click.echo(f"Enter your API key ({paste_hint}):")
            api_key = _get_secure_input(
                "API Key",
                current_config.api_key or "",
            )
            if not api_key:
                click.echo("⚠️  Warning: No API key provided. Set OMIUM_API_KEY environment variable.", err=True)
        
        # API URL
        if not api_url:
            api_url = click.prompt(
                "API URL",
                default=current_config.api_url or "https://api.omium.ai",
            )
        
        # Region
        if not region:
            region = click.prompt(
                "Region",
                default=current_config.region or "us-east-1",
            )
        
        # Validate API key if provided
        if api_key:
            try:
                test_client = RemoteOmiumClient(api_key=api_key, api_url=api_url or current_config.api_url)
                click.echo("✓ API key format is valid")
            except Exception as e:
                click.echo(f"⚠️  Warning: {e}", err=True)
    
    # Update configuration
    updates = {}
    if api_key:
        updates["api_key"] = api_key
    if api_url:
        updates["api_url"] = api_url
    if region:
        updates["region"] = region
    
    if updates:
        config_manager.update(**updates)
        config_manager.save()
        click.echo(f"✓ Configuration saved to {config_manager.config_file}")
    else:
        click.echo("No changes to save. Use --interactive or provide options.")


@cli.command("init")
@click.option("--api-key", help="Omium API key (will prompt if not provided)")
@click.option("--api-url", help="Omium API base URL (defaults to https://api.omium.ai)")
@click.option("--skip-verify", is_flag=True, help="Skip API key verification (not recommended)")
def init(api_key: Optional[str], api_url: Optional[str], skip_verify: bool):
    """
    Initialize Omium SDK configuration.
    
    This command sets up your local Omium environment by:
    1. Asking for your API key (or using --api-key)
    2. Verifying the key with Omium API
    3. Fetching your tenant info and credit balance
    4. Saving configuration to ~/.omium/config.json
    
    After initialization, you can use omium commands without specifying API keys.
    
    Examples:
        # Interactive mode (will prompt for API key)
        omium init
        
        # Non-interactive mode (recommended for Windows/PowerShell)
        omium init --api-key omium_xxxxx --api-url https://api.omium.ai
        
        # Skip verification (not recommended)
        omium init --api-key omium_xxxxx --skip-verify
    
    Note: On Windows/PowerShell, use --api-key flag for best compatibility.
    """
    config_manager = get_config_manager()
    current_config = config_manager.load()
    
    # Beautiful welcome banner
    print_welcome()
    print_header("SDK Initialization", "Let's set up your Omium environment")
    
    # Get API key
    if not api_key:
        print_info("To get started, you'll need an API key from your Omium account.")
        console.print("[dim]Get one at:[/dim] [link=https://app.omium.ai/api-keys]https://app.omium.ai/api-keys[/link]")
        console.print()
        
        # Cross-platform paste instructions
        system = platform.system()
        if system == "Windows":
            paste_hint = "Paste with Ctrl+V or right-click"
        elif system == "Darwin":  # macOS
            paste_hint = "Paste with Cmd+V"
        else:  # Linux and others
            paste_hint = "Paste with Ctrl+Shift+V or right-click"
        
        click.echo(f"💡 Tip: You can paste your API key ({paste_hint})")
        click.echo("   Or use --api-key flag: omium init --api-key YOUR_KEY")
        click.echo()
        
        default_key = current_config.api_key or ""
        if default_key:
            click.echo(f"Found existing API key: {default_key[:20]}...")
            use_existing = click.confirm("Use existing API key?", default=True)
            if use_existing:
                api_key = default_key
            else:
                try:
                    click.echo()
                    click.echo(f"Enter your API key ({paste_hint}):")
                    api_key = _get_secure_input("API Key", "", allow_visible=True)
                except (KeyboardInterrupt, EOFError):
                    click.echo("\n\n❌ Input cancelled.", err=True)
                    click.echo("\nTip: Use --api-key flag to avoid interactive prompts:", err=True)
                    click.echo("   omium init --api-key omium_xxxxx --api-url https://api.omium.ai", err=True)
                    sys.exit(1)
        else:
            try:
                click.echo(f"Enter your API key ({paste_hint}):")
                api_key = _get_secure_input("API Key", "", allow_visible=True)
            except (KeyboardInterrupt, EOFError):
                click.echo("\n\n❌ Input cancelled.", err=True)
                click.echo("\nTip: Use --api-key flag to avoid interactive prompts:", err=True)
                click.echo("   omium init --api-key omium_xxxxx --api-url https://api.omium.ai", err=True)
                sys.exit(1)
    
    if not api_key or not api_key.strip():
        click.echo("❌ API key is required. Exiting.", err=True)
        click.echo("\nGet your API key from: https://app.omium.ai/api-keys", err=True)
        click.echo("\nTip: Use --api-key flag:", err=True)
        click.echo("   omium init --api-key omium_xxxxx --api-url https://api.omium.ai", err=True)
        sys.exit(1)
    
    # Validate API key format
    if not api_key.startswith("omium_"):
        click.echo("⚠️  Warning: API key should start with 'omium_'. Continuing anyway...", err=True)
    
    # Get API URL
    if not api_url:
        default_url = current_config.api_url or "https://api.omium.ai"
        click.echo()
        try:
            api_url = click.prompt(
                "Omium API URL",
                default=default_url,
                show_default=True,
            )
            # Handle empty input
            if not api_url or api_url.strip() == "":
                api_url = default_url
        except (KeyboardInterrupt, EOFError):
            click.echo("\n\nUsing default API URL: https://api.omium.ai")
            api_url = default_url
    
    # Verify API key with Omium API
    if not skip_verify:
        console.print()
        
        with OmiumSpinner("Verifying API key with Omium..."):
            try:
                tenant_info = asyncio.run(_verify_api_key_and_get_info(api_key, api_url))
            except Exception as e:
                tenant_info = None
                error_msg = str(e)
        
        if tenant_info:
            print_success("API key verified successfully!")
            console.print()
            
            # Determine plan display based on subscription info from auth-service
            plan_display = "✓ Verified"  # Default when no subscription data
            
            # Check for subscription tier from auth-service response
            subscription_tier = tenant_info.get('subscription_tier')
            subscription_status = tenant_info.get('subscription_status')
            
            if subscription_tier and subscription_status in ('active', 'trial', 'trialing'):
                # Format tier nicely (e.g., 'pro' -> 'Pro Plan', 'enterprise' -> 'Enterprise Plan')
                tier_display = subscription_tier.replace('_', ' ').title()
                plan_display = f"✓ {tier_display} Plan"
            elif tenant_info.get('has_subscription'):
                plan_display = f"✓ {tenant_info.get('subscription_plan', 'Active')}"
            elif tenant_info.get('credits_balance', 0) > 0:
                plan_display = f"{tenant_info.get('credits_balance'):,} credits"
            
            tenant_data = [
                {"field": "Account", "value": tenant_info.get('tenant_name', 'N/A')},
                {"field": "Plan", "value": plan_display},
                {"field": "Environment", "value": tenant_info.get('environment', 'production')},
            ]
            print_table(tenant_data, columns=["field", "value"], title="Account Info")
            
            # Note: Don't show misleading warnings since we have proper subscription data now
        else:
            print_warning("Could not verify API key. Saving anyway...")
            console.print("[dim]The key may still work for API calls.[/dim]")
    
    # Save configuration
    try:
        config_manager.update(api_key=api_key, api_url=api_url)
        config_manager.save()
        
        console.print()
        print_success(f"Configuration saved to {config_manager.config_file}")
        console.print()
        
        # Next steps in a beautiful panel
        next_steps = """[bold]You're all set! Next steps:[/bold]

  [cyan]1.[/cyan] Create a workflow: [bold]omium init-workflow[/bold]
  [cyan]2.[/cyan] Run a workflow: [bold]omium run workflow.json[/bold]
  [cyan]3.[/cyan] View executions: [bold]omium list[/bold]

[dim]For more help, visit: https://docs.omium.ai[/dim]"""
        
        print_panel(next_steps, title="🚀 Ready!", style="green")
        
    except Exception as e:
        print_error(f"Error saving configuration: {e}")
        sys.exit(1)


async def _verify_api_key_and_get_info(api_key: str, api_url: str) -> Optional[Dict[str, Any]]:
    """
    Verify API key and get tenant information including subscription status.
    
    Returns:
        Dict with tenant_name, credits_balance, balance_usd, environment, subscription info, or None if verification fails
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Use public SDK verification endpoint
            verify_url = f"{api_url}/api/v1/api-keys/verify"
            logger.debug(f"Verifying API key at: {verify_url}")
            
            verify_response = await client.get(
                verify_url,
                headers={"X-API-Key": api_key},
            )
            
            if verify_response.status_code != 200:
                error_text = verify_response.text[:200] if verify_response.text else "Unknown error"
                error_detail = f"HTTP {verify_response.status_code}: {error_text}"
                logger.warning(f"API key verification failed: {error_detail}")
                raise Exception(error_detail)
            
            key_info = verify_response.json()
            tenant_id = key_info.get("tenant_id")
            
            # Get tenant info and credits
            tenant_info = {
                "tenant_id": tenant_id,
                "tenant_name": key_info.get("tenant_name", "My Account"),
                "environment": key_info.get("environment", "production"),
                "has_subscription": False,
                "subscription_plan": None,
                # Include subscription info from auth-service response
                "subscription_tier": key_info.get("subscription_tier"),
                "subscription_status": key_info.get("subscription_status"),
            }
            
            # Try to get subscription status first
            try:
                subscription_response = await client.get(
                    f"{api_url}/api/v1/billing/subscriptions/status",
                    headers={"X-API-Key": api_key},
                )
                if subscription_response.status_code == 200:
                    sub_data = subscription_response.json()
                    # Check for active subscription - billing service returns flat structure
                    status = sub_data.get("status")
                    if status in ("active", "trialing"):
                        tenant_info["has_subscription"] = True
                        tenant_info["subscription_plan"] = sub_data.get("plan_name") or sub_data.get("plan_id") or "Active Plan"
                        tenant_info["subscription_status"] = status
            except Exception as e:
                logger.debug(f"Could not fetch subscription (non-critical): {e}")
            
            # Get credit balance
            try:
                balance_response = await client.get(
                    f"{api_url}/api/v1/billing/balance",
                    headers={"X-API-Key": api_key},
                )
                if balance_response.status_code == 200:
                    balance_data = balance_response.json()
                    tenant_info["credits_balance"] = balance_data.get("credits_balance", 0)
                    tenant_info["balance_usd"] = balance_data.get("balance_usd", 0.0)
                else:
                    tenant_info["credits_balance"] = 0
                    tenant_info["balance_usd"] = 0.0
            except Exception as e:
                logger.debug(f"Could not fetch balance (non-critical): {e}")
                tenant_info["credits_balance"] = 0
                tenant_info["balance_usd"] = 0.0
            
            return tenant_info
            
    except httpx.RequestError as e:
        error_msg = f"Network error: {str(e)}"
        logger.warning(f"Network error verifying API key: {error_msg}")
        raise Exception(error_msg)
    except Exception as e:
        # Re-raise to preserve error details
        if "HTTP" in str(e) or "Network error" in str(e):
            raise
        error_msg = f"Verification error: {str(e)}"
        logger.warning(f"Error verifying API key: {error_msg}")
        raise Exception(error_msg)


@cli.command("init-workflow")
@click.option("--type", type=click.Choice(["crewai", "langgraph"], case_sensitive=False), default="crewai", help="Workflow type")
@click.option("--name", default="my-workflow", help="Workflow name")
@click.option("--output", default="workflow.json", help="Output file path")
def init_workflow(type: str, name: str, output: str):
    """
    Initialize a new workflow template.
    
    Creates a template workflow file that you can customize.
    """
    templates = {
        "crewai": {
            "type": "crewai",
            "workflow_id": name,
            "agent_id": f"{name}-agent",
            "inputs": {
                "topic": "Your input here"
            },
            "definition": {
                "name": name,
                "verbose": True,
                "llm": {
                    "provider": "openai",
                    "model": "gpt-3.5-turbo",
                    "temperature": 0.7
                },
                "agents": [
                    {
                        "role": "Agent",
                        "goal": "Your agent's goal",
                        "backstory": "Your agent's backstory",
                        "verbose": True,
                        "allow_delegation": False
                    }
                ],
                "tasks": [
                    {
                        "description": "Your task description: {topic}",
                        "agent_index": 0,
                        "expected_output": "Expected output description"
                    }
                ]
            }
        },
        "langgraph": {
            "type": "langgraph",
            "workflow_id": name,
            "agent_id": f"{name}-agent",
            "inputs": {
                "messages": [],
                "data": {
                    "input": "Your input here"
                }
            },
            "definition": {
                "name": name,
                "nodes": [
                    {
                        "name": "process",
                        "function": "default_process"
                    },
                    {
                        "name": "respond",
                        "function": "default_respond"
                    }
                ],
                "edges": [
                    {
                        "from": "START",
                        "to": "process"
                    },
                    {
                        "from": "process",
                        "to": "respond"
                    },
                    {
                        "from": "respond",
                        "to": "END"
                    }
                ]
            }
        }
    }
    
    template = templates.get(type.lower(), templates["crewai"])
    
    try:
        with open(output, "w") as f:
            json.dump(template, f, indent=2)
        
        click.echo(f"✓ Created {type} workflow template: {output}")
        click.echo(f"\nNext steps:")
        click.echo(f"  1. Edit {output} to customize your workflow")
        click.echo(f"  2. Set OPENAI_API_KEY environment variable (for CrewAI)")
        click.echo(f"  3. Run: omium run {output}")
        
    except Exception as e:
        click.echo(f"Error creating template: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("script_or_workflow", type=click.Path(exists=True))
@click.option("--project", "-p", help="Project name for organizing traces")
@click.option("--env", "-e", multiple=True, help="Environment variables (KEY=VALUE)")
@click.option("--no-trace", is_flag=True, help="Disable automatic tracing")
@click.option("--execution-id", help="Execution ID (auto-generated if not provided)")
@click.option("--execution-engine-url", default="http://localhost:8000", help="Execution Engine API URL")
@click.option("--checkpoint-manager", default="localhost:7001", help="Checkpoint Manager URL")
def run(
    script_or_workflow: str,
    project: Optional[str],
    env: tuple,
    no_trace: bool,
    execution_id: Optional[str],
    execution_engine_url: str,
    checkpoint_manager: str
):
    """
    Run a Python script or workflow with Omium instrumentation.
    
    This command supports two modes:
    
    1. Python scripts (.py) - Recommended
       Runs your Python script with automatic Omium tracing.
       LangGraph and CrewAI are automatically instrumented.
       
       Examples:
           omium run main.py
           omium run crew.py --project my-research
           omium run agent.py --env OPENAI_API_KEY=xxx
    
    2. JSON workflows (.json) - Legacy
       Runs a JSON workflow definition through the Execution Engine.
       
       Example:
           omium run workflow.json
    """
    import subprocess
    import os as os_module
    
    # Get current config
    from omium.config import get_config
    config = get_config()
    
    # Detect file type
    if script_or_workflow.endswith('.py'):
        # Python script mode - run with instrumentation
        _run_python_script(
            script_path=script_or_workflow,
            project=project,
            env_vars=env,
            no_trace=no_trace,
            config=config
        )
    elif script_or_workflow.endswith('.json'):
        # Legacy JSON workflow mode
        click.echo(print_warning_text("JSON workflows are deprecated. Consider using Python scripts instead."))
        click.echo(f"Running workflow: {script_or_workflow}")
        
        # Load workflow file
        try:
            with open(script_or_workflow, "r") as f:
                workflow_config = json.load(f)
        except json.JSONDecodeError as e:
            click.echo(f"Error: Invalid JSON in workflow file: {e}", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"Error loading workflow file: {e}", err=True)
            sys.exit(1)
        
        # Validate workflow config
        if "type" not in workflow_config and "definition" not in workflow_config:
            click.echo("Error: Workflow file must contain 'type' and 'definition' fields", err=True)
            sys.exit(1)
        
        # Store execution_engine_url in context for async function
        ctx = click.get_current_context()
        ctx.params['execution_engine_url'] = execution_engine_url
        
        # Auto-register workflow if not already registered
        asyncio.run(_ensure_workflow_registered(workflow_config))
        
        # Run workflow
        asyncio.run(_run_workflow(workflow_config, execution_id, checkpoint_manager))
    else:
        click.echo(f"Error: Unsupported file type: {script_or_workflow}", err=True)
        click.echo("Supported formats: .py (Python scripts), .json (workflows)", err=True)
        sys.exit(1)


def _run_python_script(
    script_path: str,
    project: Optional[str],
    env_vars: tuple,
    no_trace: bool,
    config
):
    """Run a Python script with Omium instrumentation."""
    import subprocess
    import os as os_module
    
    # Build environment
    run_env = os_module.environ.copy()
    
    # Add Omium environment variables
    if config and config.api_key:
        run_env["OMIUM_API_KEY"] = config.api_key
    
    if project:
        run_env["OMIUM_PROJECT"] = project
    
    if not no_trace:
        run_env["OMIUM_TRACING"] = "true"
    
    # Add user-provided environment variables
    for e in env_vars:
        if "=" in e:
            key, value = e.split("=", 1)
            run_env[key] = value
        else:
            click.echo(f"Warning: Invalid env format '{e}', expected KEY=VALUE", err=True)
    
    # Display info
    click.echo(print_info_text(f"🚀 Running {script_path} with Omium instrumentation"))
    
    if not no_trace:
        click.echo(print_dim_text("   Tracing: enabled"))
        if project:
            click.echo(print_dim_text(f"   Project: {project}"))
    else:
        click.echo(print_dim_text("   Tracing: disabled"))
    
    # Create wrapper script that initializes Omium before running user's script
    wrapper_code = f'''
import sys
import os

# Initialize Omium if tracing is enabled
if os.environ.get("OMIUM_TRACING", "").lower() in ("true", "1", "yes"):
    try:
        import omium
        omium.init()
        print("\\033[90m   Omium initialized successfully\\033[0m")
    except Exception as e:
        print(f"\\033[93m   Warning: Failed to initialize Omium: {{e}}\\033[0m")

# Execute the user's script
script_path = {repr(os_module.path.abspath(script_path))}
script_dir = os.path.dirname(script_path)

# Add script directory to path
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# Change to script directory
os.chdir(script_dir)

# Execute
with open(script_path, 'r') as f:
    code = compile(f.read(), script_path, 'exec')
    exec(code, {{'__name__': '__main__', '__file__': script_path}})
'''
    
    # Run the wrapper
    try:
        result = subprocess.run(
            [sys.executable, "-c", wrapper_code],
            env=run_env,
            cwd=os_module.path.dirname(os_module.path.abspath(script_path)) or ".",
        )
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        click.echo("\nExecution interrupted by user")
        sys.exit(130)
    except Exception as e:
        click.echo(f"Error running script: {e}", err=True)
        sys.exit(1)


def print_warning_text(text: str) -> str:
    """Format text as a warning."""
    return f"\033[93m⚠️  {text}\033[0m"


def print_info_text(text: str) -> str:
    """Format text as info."""
    return f"\033[94m{text}\033[0m"


def print_dim_text(text: str) -> str:
    """Format text as dim."""
    return f"\033[90m{text}\033[0m"




async def _run_workflow(workflow_config: dict, execution_id: Optional[str], checkpoint_manager: str):
    """Run workflow asynchronously."""
    # Get execution engine URL from environment or use default
    execution_engine_url = click.get_current_context().params.get(
        'execution_engine_url',
        'http://localhost:8000'
    )
    
    # Determine workflow type
    workflow_type = workflow_config.get("type", "crewai").lower()
    if workflow_type not in ["crewai", "langgraph"]:
        click.echo(f"Error: Unsupported workflow type '{workflow_type}'. Supported: 'crewai', 'langgraph'", err=True)
        sys.exit(1)
    
    workflow_definition = workflow_config.get("definition", workflow_config)
    inputs = workflow_config.get("inputs", {})
    
    try:
        # Create execution via Execution Engine API
        async with httpx.AsyncClient(timeout=300.0) as http_client:
            # Create execution
            create_response = await http_client.post(
                f"{execution_engine_url}/api/v1/executions",
                json={
                    "workflow_id": workflow_config.get("workflow_id", "cli-workflow"),
                    "agent_id": workflow_config.get("agent_id", "cli-agent"),
                    "input_data": inputs,
                    "metadata": {
                        "workflow_type": workflow_type,
                        "workflow_definition": workflow_definition,
                        "source": "cli"
                    }
                }
            )
            
            if create_response.status_code != 201:
                click.echo(f"Error creating execution: {create_response.text}", err=True)
                sys.exit(1)
            
            execution = create_response.json()
            execution_id = execution["id"]
            
            click.echo(f"✓ Execution created: {execution_id}")
            click.echo(f"✓ Workflow type: {workflow_type}")
            click.echo("Executing workflow...")
            
            # Poll for execution status
            max_wait = 300  # 5 minutes
            wait_time = 0
            poll_interval = 2  # seconds
            
            while wait_time < max_wait:
                await asyncio.sleep(poll_interval)
                wait_time += poll_interval
                
                status_response = await http_client.get(
                    f"{execution_engine_url}/api/v1/executions/{execution_id}"
                )
                
                if status_response.status_code != 200:
                    click.echo(f"Error checking execution status: {status_response.text}", err=True)
                    sys.exit(1)
                
                execution = status_response.json()
                status = execution["status"]
                
                if status == "completed":
                    click.echo("✓ Workflow completed successfully!")
                    click.echo(f"\nResult:\n{json.dumps(execution.get('output_data', {}), indent=2)}")
                    
                    # Show checkpoints if available
                    checkpoints = execution.get("metadata", {}).get("checkpoints", [])
                    if checkpoints:
                        click.echo(f"\n✓ Created {len(checkpoints)} checkpoints")
                        for cp in checkpoints[:5]:  # Show first 5
                            click.echo(f"  - {cp.get('name', 'unknown')}")
                        if len(checkpoints) > 5:
                            click.echo(f"  ... and {len(checkpoints) - 5} more")
                    
                    # Show validation status
                    validation_passed = execution.get("metadata", {}).get("validation_passed")
                    if validation_passed:
                        click.echo("\n✓ Post-condition validation passed")
                    
                    return
                elif status == "failed":
                    error_msg = execution.get("error_message", "Unknown error")
                    click.echo(f"\n✗ Workflow failed: {error_msg}", err=True)
                    
                    # Show failure details
                    metadata = execution.get("metadata", {})
                    failure = metadata.get("failure", {})
                    recovery = metadata.get("recovery", {})
                    suggested_fix = metadata.get("suggested_fix")
                    
                    if failure:
                        click.echo(f"\nFailure Details:")
                        click.echo(f"  Type: {failure.get('type', 'unknown')}")
                        click.echo(f"  Message: {failure.get('message', 'Unknown')}")
                        
                        validation_errors = failure.get("validation_errors", [])
                        if validation_errors:
                            click.echo(f"  Validation Errors:")
                            for err in validation_errors:
                                click.echo(f"    - {err}")
                    
                    if recovery:
                        rollback_performed = recovery.get("rollback_performed", False)
                        if rollback_performed:
                            checkpoint = recovery.get("rollback_checkpoint", {})
                            click.echo(f"\n✓ Automatic rollback performed")
                            click.echo(f"  Rolled back to checkpoint: {checkpoint.get('name', 'unknown')}")
                        else:
                            click.echo(f"\n⚠ No checkpoint available for rollback")
                    
                    if suggested_fix:
                        click.echo(f"\n💡 Suggested Fix:")
                        click.echo(f"  {suggested_fix}")
                        click.echo(f"\nTo retry with fix, update your workflow and run again.")
                    
                    sys.exit(1)
                elif status == "running":
                    click.echo(".", nl=False)  # Progress indicator
                    sys.stdout.flush()
            
            # Timeout
            click.echo(f"\n⚠ Execution timed out after {max_wait} seconds", err=True)
            click.echo(f"Execution ID: {execution_id}")
            click.echo(f"Check status: {execution_engine_url}/api/v1/executions/{execution_id}")
            sys.exit(1)
            
    except httpx.RequestError as e:
        click.echo(f"Error connecting to Execution Engine at {execution_engine_url}: {e}", err=True)
        click.echo("Make sure Execution Engine is running and accessible.", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error executing workflow: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("execution_id")
@click.option("--execution-engine-url", default="http://localhost:8000", help="Execution Engine API URL")
@click.option("--checkpoint-manager", default="localhost:7001", help="Checkpoint Manager URL")
@click.option("--checkpoint-id", help="Specific checkpoint ID to replay from (optional)")
def replay(execution_id: str, execution_engine_url: str, checkpoint_manager: str, checkpoint_id: Optional[str]):
    """
    Replay an execution from a checkpoint.
    
    This will recreate the execution state from a previous checkpoint and
    re-execute the workflow from that point.
    """
    click.echo(f"Replaying execution: {execution_id}")
    if checkpoint_id:
        click.echo(f"From checkpoint: {checkpoint_id}")
    asyncio.run(_replay_execution(execution_id, execution_engine_url, checkpoint_manager, checkpoint_id))


async def _replay_execution(
    execution_id: str,
    execution_engine_url: str,
    checkpoint_manager: str,
    checkpoint_id: Optional[str]
):
    """Replay execution from checkpoint."""
    try:
        async with httpx.AsyncClient(timeout=300.0) as http_client:
            # Get original execution
            execution_response = await http_client.get(
                f"{execution_engine_url}/api/v1/executions/{execution_id}"
            )
            
            if execution_response.status_code != 200:
                click.echo(f"Error: Execution {execution_id} not found", err=True)
                sys.exit(1)
            
            execution = execution_response.json()
            
            # Get checkpoints from execution metadata first (they might be stored locally)
            checkpoints = execution.get("metadata", {}).get("checkpoints", [])
            
            # If no checkpoints in metadata, try checkpoint manager
            if not checkpoints:
                click.echo("No checkpoints in execution metadata, trying checkpoint manager...")
                client = OmiumClient(checkpoint_manager_url=checkpoint_manager)
                try:
                    await client.connect()
                    checkpoints = await client.list_checkpoints(execution_id=execution_id)
                    await client.close()
                except Exception as e:
                    click.echo(f"⚠️  Could not get checkpoints from checkpoint manager: {e}", err=True)
                    click.echo("   Checkpoints may be stored locally in execution metadata.", err=True)
                    checkpoints = []
            
            if not checkpoints:
                click.echo("No checkpoints found for this execution", err=True)
                click.echo("Note: Checkpoints may not have been created, or checkpoint manager is unavailable.", err=True)
                sys.exit(1)
            
            click.echo(f"Found {len(checkpoints)} checkpoint(s):")
            for i, cp in enumerate(checkpoints):
                cp_name = cp.get("name") or cp.get("checkpoint_name", "unknown")
                cp_id = cp.get("id", "N/A")
                marker = " <-- Selected" if checkpoint_id and (cp_id == checkpoint_id or cp_id.startswith(checkpoint_id)) else ""
                click.echo(f"  {i+1}. {cp_name} ({cp_id[:16]}...){marker}")
            
            # Select checkpoint
            target_checkpoint = None
            if checkpoint_id:
                target_checkpoint = next(
                    (cp for cp in checkpoints 
                     if cp.get("id") == checkpoint_id or cp.get("id", "").startswith(checkpoint_id)),
                    None
                )
                if not target_checkpoint:
                    click.echo(f"Error: Checkpoint {checkpoint_id} not found", err=True)
                    sys.exit(1)
            else:
                # Use last checkpoint
                target_checkpoint = checkpoints[-1]
                click.echo(f"\nUsing last checkpoint: {target_checkpoint.get('name') or target_checkpoint.get('checkpoint_name', 'unknown')}")
            
            # Use the replay API endpoint (simpler and more reliable)
            click.echo("\nStarting replay via API...")
            replay_response = await http_client.post(
                f"{execution_engine_url}/api/v1/executions/{execution_id}/replay",
                json={"checkpoint_id": target_checkpoint.get("id")} if target_checkpoint.get("id") else {}
            )
            
            if replay_response.status_code == 200:
                result = replay_response.json()
                new_execution_id = result.get("replay_execution_id")
                
                click.echo("✓ Replay started successfully!")
                click.echo(f"\nReplay Execution ID: {new_execution_id}")
                click.echo(f"Original Execution: {execution_id}")
                click.echo(f"Replayed from checkpoint: {target_checkpoint.get('name') or target_checkpoint.get('checkpoint_name', 'unknown')}")
                click.echo(f"\nThe replay execution is running in the background.")
                click.echo(f"Check status: {execution_engine_url}/api/v1/executions/{new_execution_id}")
                click.echo(f"Or use: omium show {new_execution_id}")
            else:
                click.echo(f"Error starting replay: {replay_response.status_code} - {replay_response.text}", err=True)
                sys.exit(1)
                
    except httpx.RequestError as e:
        click.echo(f"Error connecting to services: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error replaying execution: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option("--execution-engine-url", default="http://localhost:8000", help="Execution Engine API URL")
@click.option("--status", help="Filter by status (completed, failed, running, pending)")
@click.option("--workflow-id", help="Filter by workflow ID")
@click.option("--limit", default=20, help="Number of executions to show")
def list(execution_engine_url: str, status: Optional[str], workflow_id: Optional[str], limit: int):
    """
    List recent executions.
    
    Shows a list of recent workflow executions with their status and basic info.
    """
    asyncio.run(_list_executions(execution_engine_url, status, workflow_id, limit))


async def _list_executions(execution_engine_url: str, status: Optional[str], workflow_id: Optional[str], limit: int):
    """List executions asynchronously."""
    try:
        async with httpx.AsyncClient() as client:
            params = {"page": 1, "page_size": limit}
            if status:
                params["status"] = status
            if workflow_id:
                params["workflow_id"] = workflow_id
            
            response = await client.get(
                f"{execution_engine_url}/api/v1/executions",
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                executions = data.get("executions", [])
                total = data.get("total", 0)
                
                if not executions:
                    print_info("No executions found.")
                    return
                
                print_header(f"Executions", f"Found {total} execution(s)")
                
                # Format executions for Rich table
                table_data = []
                for exec in executions:
                    exec_id = exec.get("id", "unknown")[:36]
                    exec_status = exec.get("status", "unknown")
                    workflow = exec.get("workflow_id", "unknown")[:28]
                    created = exec.get("created_at", "unknown")
                    if created != "unknown":
                        from datetime import datetime
                        try:
                            dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                            created = dt.strftime("%Y-%m-%d %H:%M")
                        except:
                            pass
                    
                    # Format status with color
                    if exec_status == "completed":
                        status_display = f"[green]✓ {exec_status}[/green]"
                    elif exec_status == "failed":
                        status_display = f"[red]✗ {exec_status}[/red]"
                    elif exec_status == "running":
                        status_display = f"[blue]⟳ {exec_status}[/blue]"
                    else:
                        status_display = exec_status
                    
                    table_data.append({
                        "id": exec_id,
                        "status": status_display,
                        "workflow_id": workflow,
                        "created_at": created
                    })
                
                print_table(table_data, columns=["id", "status", "workflow_id", "created_at"])
                console.print()
                console.print("[dim]Use[/dim] [bold]omium show <execution-id>[/bold] [dim]to view details[/dim]")
            else:
                print_error(f"Error: {response.status_code} - {response.text}")
                sys.exit(1)
                
    except httpx.RequestError as e:
        print_error(f"Error connecting to Execution Engine: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error listing executions: {e}")
        sys.exit(1)


@cli.command()
@click.argument("execution_id")
@click.option("--execution-engine-url", default="http://localhost:8000", help="Execution Engine API URL")
def show(execution_id: str, execution_engine_url: str):
    """
    Show detailed information about an execution.
    
    Displays full execution details including inputs, outputs, checkpoints, and metadata.
    """
    asyncio.run(_show_execution(execution_id, execution_engine_url))


async def _show_execution(execution_id: str, execution_engine_url: str):
    """Show execution details asynchronously."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{execution_engine_url}/api/v1/executions/{execution_id}"
            )
            
            if response.status_code == 200:
                execution = response.json()
                
                # Header
                print_header(f"Execution: {execution_id[:20]}...", "Detailed execution information")
                
                # Status with color
                status = execution.get('status', 'unknown')
                if status == "completed":
                    status_display = f"[green]✓ {status.upper()}[/green]"
                elif status == "failed":
                    status_display = f"[red]✗ {status.upper()}[/red]"
                elif status == "running":
                    status_display = f"[blue]⟳ {status.upper()}[/blue]"
                else:
                    status_display = status.upper()
                
                # Basic info table
                basic_info = [
                    {"field": "Status", "value": status_display},
                    {"field": "Workflow ID", "value": execution.get('workflow_id', 'unknown')},
                    {"field": "Agent ID", "value": execution.get('agent_id', 'unknown')},
                    {"field": "Created", "value": execution.get('created_at', 'unknown')},
                    {"field": "Started", "value": execution.get('started_at', 'N/A')},
                    {"field": "Completed", "value": execution.get('completed_at', 'N/A')},
                ]
                print_table(basic_info, columns=["field", "value"], title="Basic Info")
                
                # Input data
                if execution.get("input_data"):
                    console.print()
                    print_json(execution.get("input_data"), title="Input Data")
                
                # Output data
                if execution.get("output_data"):
                    console.print()
                    print_json(execution.get("output_data"), title="Output Data")
                
                # Error message
                if execution.get("error_message"):
                    console.print()
                    console.print("[bold red]Error:[/bold red]")
                    console.print(f"[red]{execution.get('error_message')}[/red]")
                
                # Checkpoints
                checkpoints = execution.get("metadata", {}).get("checkpoints", [])
                if checkpoints:
                    console.print()
                    console.print(f"[bold]Checkpoints ({len(checkpoints)}):[/bold]")
                    checkpoint_data = []
                    for i, cp in enumerate(checkpoints, 1):
                        checkpoint_data.append({
                            "#": str(i),
                            "name": cp.get('name', 'unknown'),
                            "id": cp.get('id', 'N/A')[:12] + "...",
                            "created": cp.get('created_at', 'N/A')
                        })
                    print_table(checkpoint_data, columns=["#", "name", "id", "created"])
                
                # Recovery details
                recovery = execution.get("metadata", {}).get("recovery_details")
                if recovery:
                    console.print()
                    console.print("[bold]Recovery Details:[/bold]")
                    recovery_data = [
                        {"field": "Action", "value": recovery.get('action', 'N/A')},
                        {"field": "Status", "value": recovery.get('status', 'N/A')},
                        {"field": "Message", "value": recovery.get('message', 'N/A')},
                    ]
                    print_table(recovery_data, columns=["field", "value"])
                
                console.print()
                print_divider()
                console.print(f"[dim]Use[/dim] [bold]omium replay {execution_id}[/bold] [dim]to replay this execution[/dim]")
                
            elif response.status_code == 404:
                print_error(f"Execution not found: {execution_id}")
                sys.exit(1)
            else:
                print_error(f"Error: {response.status_code} - {response.text}")
                sys.exit(1)
                
    except httpx.RequestError as e:
        print_error(f"Error connecting to Execution Engine: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error showing execution: {e}")
        sys.exit(1)


@cli.command()
@click.argument("execution_id")
@click.option("--follow", "-f", is_flag=True, default=True, help="Follow log output (stream new logs)")
@click.option("--tail", "-n", default=50, help="Number of recent logs to show")
@click.option("--execution-engine-url", default="http://localhost:8000", help="Execution Engine API URL")
def logs(execution_id: str, follow: bool, tail: int, execution_engine_url: str):
    """
    Stream logs from a running execution.
    
    Shows live log output from an execution. In follow mode (default), 
    new logs are streamed as they arrive.
    
    Examples:
        omium logs exec-123           # Stream logs with follow mode
        omium logs exec-123 --no-follow  # Show last 50 logs and exit
        omium logs exec-123 -n 100    # Show last 100 logs
    """
    print_header(f"Logs: {execution_id[:20]}...", "Live log streaming")
    
    async def _stream():
        async for log in stream_execution_logs(
            execution_id=execution_id,
            execution_engine_url=execution_engine_url,
            follow=follow,
            tail=tail,
            on_log=print_log_entry
        ):
            pass  # Logs are printed by callback
    
    try:
        asyncio.run(_stream())
    except KeyboardInterrupt:
        console.print("\n[dim]Log streaming stopped.[/dim]")


@cli.command()
@click.argument("execution_id")
@click.option("--execution-engine-url", default="http://localhost:8000", help="Execution Engine API URL")
def status(execution_id: str, execution_engine_url: str):
    """
    Watch execution status with live updates.
    
    Monitors an execution and shows status changes in real-time.
    Automatically exits when the execution completes.
    
    Examples:
        omium status exec-123         # Watch execution status
    """
    print_header(f"Watching: {execution_id[:20]}...", "Live status monitoring")
    
    def on_status_change(execution: dict):
        status = execution.get("status", "unknown")
        
        # Format status with color
        if status == "completed":
            status_display = f"[green]✓ {status.upper()}[/green]"
        elif status == "failed":
            status_display = f"[red]✗ {status.upper()}[/red]"
        elif status == "running":
            status_display = f"[blue]⟳ {status.upper()}[/blue]"
        else:
            status_display = status.upper()
        
        console.print(f"Status: {status_display}")
        
        # Show checkpoints count
        checkpoints = execution.get("metadata", {}).get("checkpoints", [])
        if checkpoints:
            console.print(f"[dim]Checkpoints: {len(checkpoints)}[/dim]")
        
        # Show error if failed
        if status == "failed" and execution.get("error_message"):
            console.print(f"[red]Error: {execution.get('error_message')}[/red]")
    
    try:
        asyncio.run(watch_execution(
            execution_id=execution_id,
            execution_engine_url=execution_engine_url,
            update_callback=on_status_change
        ))
        print_success("Execution monitoring complete.")
    except KeyboardInterrupt:
        console.print("\n[dim]Status monitoring stopped.[/dim]")


@cli.command()
@click.option("--execution-engine-url", default="http://localhost:8000", help="Execution Engine API URL")
def tui(execution_engine_url: str):
    """
    Launch interactive TUI dashboard.
    
    Opens a full-featured terminal user interface for managing
    Omium workflows and executions with keyboard navigation.
    
    Features:
        - Live executions table with status
        - Auto-refresh every 5 seconds
        - Keyboard navigation (↑/↓, Enter, q to quit)
        - Dark/light mode toggle (d)
    
    Examples:
        omium tui                    # Launch dashboard
        omium tui --execution-engine-url http://api:8000
    """
    print_info("Launching Omium TUI dashboard...")
    console.print("[dim]Press 'q' to quit, 'd' to toggle dark mode[/dim]")
    
    try:
        app = OmiumApp(execution_engine_url=execution_engine_url)
        app.run()
    except Exception as e:
        print_error(f"Failed to launch TUI: {e}")
        console.print("[dim]Make sure 'textual' is installed: pip install textual[/dim]")


@cli.command()
def chat():
    """
    Start interactive AI chat for workflow help.
    
    Chat with an AI assistant to get help with:
    - Creating workflows
    - Debugging issues  
    - Understanding checkpoints
    - Best practices
    
    Examples:
        omium chat                   # Start chat session
    """
    run_chat_session()


@cli.command("new")
@click.option("--template", "-t", type=click.Choice(get_available_templates()), help="Template to use")
@click.option("--name", "-n", help="Workflow name/ID")
@click.option("--output", "-o", help="Output file path")
def new_workflow(template: Optional[str], name: Optional[str], output: Optional[str]):
    """
    Create a new workflow from template.
    
    Interactive wizard to create a workflow file from predefined templates.
    
    Templates:
        crewai      - CrewAI workflow with agents and tasks
        langgraph   - LangGraph state machine workflow
        multi-agent - Multi-agent team workflow
    
    Examples:
        omium new                           # Interactive wizard
        omium new --template crewai         # Use specific template
        omium new -t multi-agent -n my-team -o workflow.json
    """
    if template and name:
        # Non-interactive mode
        from omium.chat import create_workflow_from_template
        output_path = output or f"{name}.json"
        create_workflow_from_template(template, name, output_path)
    else:
        # Interactive wizard
        run_new_workflow_wizard()


@cli.command()
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish", "powershell"]))
def completions(shell: str):
    """
    Generate shell completion script.
    
    Outputs a completion script for the specified shell that can be
    sourced or installed to enable tab completion for omium commands.
    
    Examples:
        # Bash - add to ~/.bashrc
        omium completions bash >> ~/.bashrc
        
        # Zsh - add to ~/.zshrc
        omium completions zsh >> ~/.zshrc
        
        # Fish
        omium completions fish > ~/.config/fish/completions/omium.fish
        
        # PowerShell - add to $PROFILE
        omium completions powershell >> $PROFILE
    """
    import subprocess
    
    if shell == "bash":
        script = '''
# Omium CLI bash completion
_omium_completion() {
    local IFS=$'\\n'
    COMPREPLY=( $(env COMP_WORDS="${COMP_WORDS[*]}" COMP_CWORD=$COMP_CWORD _OMIUM_COMPLETE=bash_complete $1) )
    return 0
}
complete -o default -F _omium_completion omium
'''
    elif shell == "zsh":
        script = '''
# Omium CLI zsh completion
#compdef omium

_omium() {
    eval $(env _OMIUM_COMPLETE=zsh_complete omium)
}
compdef _omium omium
'''
    elif shell == "fish":
        script = '''
# Omium CLI fish completion
function __fish_omium_complete
    set -lx _OMIUM_COMPLETE fish_complete
    set -lx COMP_WORDS (commandline -o)
    set -lx COMP_CWORD (count (commandline -oc))
    omium
end
complete -c omium -f -a "(__fish_omium_complete)"
'''
    elif shell == "powershell":
        script = '''
# Omium CLI PowerShell completion
$scriptblock = {
    param($wordToComplete, $commandAst, $cursorPosition)
    $env:_OMIUM_COMPLETE = "powershell_complete"
    $env:COMP_WORDS = $commandAst.ToString()
    omium | ForEach-Object {
        [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
    }
    Remove-Item env:_OMIUM_COMPLETE
    Remove-Item env:COMP_WORDS
}
Register-ArgumentCompleter -Native -CommandName omium -ScriptBlock $scriptblock
'''
    
    console.print(script.strip())
    console.print()
    console.print(f"[dim]# Add the above to your shell config file[/dim]")


@cli.group()
def project():
    """Project configuration commands (omium.toml)."""
    pass


@project.command("init")
@click.option("--name", "-n", help="Project name")
@click.option("--dir", "-d", "directory", help="Project directory (default: current)")
def project_init(name: Optional[str], directory: Optional[str]):
    """
    Initialize a new Omium project with omium.toml.
    
    Creates an omium.toml configuration file and workflows directory
    for config-as-code workflow management.
    
    Examples:
        omium project init                    # Initialize in current directory
        omium project init --name my-agent    # With custom name
        omium project init --dir ./my-project # In specific directory
    """
    success = init_project(project_dir=directory, project_name=name)
    if success:
        console.print()
        console.print("[dim]Created project structure:[/dim]")
        console.print("  📄 omium.toml      - Project configuration")
        console.print("  📁 workflows/      - Workflow definitions")
        console.print("  📄 .gitignore      - Git ignore file")


@project.command("info")
def project_info():
    """
    Show current project information.
    
    Displays configuration from omium.toml if present.
    """
    proj = get_current_project()
    if not proj:
        print_warning("No omium.toml found in current directory.")
        console.print("[dim]Run 'omium project init' to create one.[/dim]")
        return
    
    print_header(f"Project: {proj.name}", f"v{proj.version}")
    
    info = [
        {"setting": "Execution Engine", "value": proj.execution_engine_url},
        {"setting": "Checkpoint Manager", "value": proj.checkpoint_manager_url},
        {"setting": "LLM Provider", "value": proj.llm_provider},
        {"setting": "LLM Model", "value": proj.llm_model},
        {"setting": "Workflows Dir", "value": str(proj.workflows_dir)},
        {"setting": "Log Level", "value": proj.log_level},
    ]
    print_table(info, columns=["setting", "value"], title="Configuration")


@project.command("workflows")
def project_workflows():
    """
    List workflows in the current project.
    
    Shows all workflows defined in omium.toml and the workflows directory.
    """
    proj = get_current_project()
    if not proj:
        print_warning("No omium.toml found. Run 'omium project init' first.")
        return
    
    workflows = proj.list_workflows()
    
    if not workflows:
        print_info("No workflows found.")
        console.print("[dim]Create workflows in the 'workflows/' directory[/dim]")
        return
    
    print_header("Project Workflows", f"{len(workflows)} workflow(s)")
    print_table(workflows, columns=["id", "type", "file", "source"])


@cli.group()
def checkpoints():
    """Checkpoint management commands."""
    pass


@checkpoints.command("list")
@click.argument("execution_id")
@click.option("--checkpoint-manager", default="localhost:7001", help="Checkpoint Manager URL")
def list_checkpoints(execution_id: str, checkpoint_manager: str):
    """List checkpoints for an execution."""
    asyncio.run(_list_checkpoints(execution_id, checkpoint_manager))


async def _list_checkpoints(execution_id: str, checkpoint_manager: str):
    """List checkpoints asynchronously."""
    client = OmiumClient(checkpoint_manager_url=checkpoint_manager)
    
    try:
        await client.connect()
        
        checkpoints = await client.list_checkpoints(execution_id=execution_id)
        
        if not checkpoints:
            click.echo(f"No checkpoints found for execution {execution_id}")
            click.echo("Note: Checkpoints may be stored locally if checkpoint manager is unavailable.")
            return
        
        click.echo(f"Checkpoints for execution {execution_id}:")
        for cp in checkpoints:
            click.echo(f"  - {cp.get('checkpoint_name', 'unknown')} ({cp.get('id', 'unknown')})")
            if cp.get("created_at"):
                click.echo(f"    Created: {cp['created_at']}")
        
    except Exception as e:
        error_msg = str(e)
        if "connection" in error_msg.lower() or "unavailable" in error_msg.lower():
            click.echo(f"⚠️  Could not connect to checkpoint manager at {checkpoint_manager}", err=True)
            click.echo("   Checkpoints may be stored locally. Check execution metadata for checkpoint info.", err=True)
        else:
            click.echo(f"Error listing checkpoints: {error_msg}", err=True)
        # Don't exit with error code - this is informational
        return
    finally:
        await client.close()


@cli.command()
@click.argument("execution_id")
@click.argument("checkpoint_id")
@click.option("--checkpoint-manager", default="localhost:7001", help="Checkpoint Manager URL")
def rollback(execution_id: str, checkpoint_id: str, checkpoint_manager: str):
    """Rollback execution to a checkpoint."""
    click.echo(f"Rolling back execution {execution_id} to checkpoint {checkpoint_id}")
    asyncio.run(_rollback_execution(execution_id, checkpoint_id, checkpoint_manager))


async def _rollback_execution(execution_id: str, checkpoint_id: str, checkpoint_manager: str):
    """Rollback execution asynchronously."""
    client = OmiumClient(checkpoint_manager_url=checkpoint_manager)
    
    try:
        await client.connect()
        
        result = await client.rollback_to_checkpoint(
            checkpoint_id=checkpoint_id,
            execution_id=execution_id,
            trigger_reason="Manual rollback via CLI",
            trigger_type="manual",
        )
        
        click.echo(f"Rollback successful: {json.dumps(result, indent=2)}")
        
    except CheckpointError as e:
        click.echo(f"Rollback failed: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error during rollback: {e}", err=True)
        sys.exit(1)
    finally:
        await client.close()


@cli.command("export-crew")
@click.argument("source")
@click.option("--output", "-o", help="Output file path (defaults to stdout)")
@click.option("--workflow-name", help="Name for the workflow (defaults to crew name)")
@click.option("--workflow-id", help="ID for the workflow (defaults to workflow-name)")
@click.option("--register", is_flag=True, help="Register workflow with Omium backend after export")
def export_crew(source: str, output: Optional[str], workflow_name: Optional[str], workflow_id: Optional[str], register: bool):
    """
    Export a CrewAI Crew object to Omium workflow format.

    Args:
        source: Path to Python file and object name, e.g., 'path/to/file.py:crew_object'

    Example:
        omium export-crew my_workflow.py:my_crew > workflow.json
        omium export-crew my_workflow.py:my_crew -o workflow.json
    """
    try:
        from omium.adapters.crewai_adapter import export_crewai_workflow
        from omium.adapters.crewai_yaml_adapter import export_crewai_workflow_from_yaml
        
        # Parse source path and object name
        if ":" not in source:
            click.echo("Error: Source must be in format 'path/to/file.py:object_name'", err=True)
            sys.exit(1)
        
        file_path, object_name = source.rsplit(":", 1)
        
        # Check if this is a class-based workflow (has .crew() method call)
        # If so, try YAML-based export first (more reliable)
        use_yaml_export = False
        if "().crew()" in object_name or "().crew" in object_name:
            use_yaml_export = True
            click.echo("Detected class-based CrewAI workflow. Using YAML-based export...")
        
        # Change to file's directory to help CrewAI find config files
        import os
        original_cwd = os.getcwd()
        abs_file_path = os.path.abspath(file_path)
        file_dir = os.path.dirname(abs_file_path)
        
        # Change to project root (where pyproject.toml is) if it exists
        project_root = file_dir
        while project_root and project_root != os.path.dirname(project_root):
            if os.path.exists(os.path.join(project_root, "pyproject.toml")):
                os.chdir(project_root)
                break
            project_root = os.path.dirname(project_root)
        else:
            # If no pyproject.toml found, use file's directory
            if file_dir:
                os.chdir(file_dir)
        
        try:
            if use_yaml_export:
                # Use YAML-based export (doesn't require instantiating crew)
                workflow = export_crewai_workflow_from_yaml(
                    crew_file_path=abs_file_path,
                    workflow_name=workflow_name,
                    workflow_id=workflow_id
                )
            else:
                # Use standard export (requires crew object)
                logger.debug(f"Loading object '{object_name}' from '{abs_file_path}' (cwd: {os.getcwd()})")
                crew = _load_python_object(abs_file_path, object_name)
                
                if crew is None:
                    click.echo(f"Error: Could not find object '{object_name}' in {file_path}", err=True)
                    click.echo(f"Debug: Absolute path: {abs_file_path}, CWD: {os.getcwd()}", err=True)
                    sys.exit(1)
                
                # Export the workflow
                workflow = export_crewai_workflow(
                    crew=crew,
                    workflow_name=workflow_name,
                    workflow_id=workflow_id
                )
        finally:
            # Restore original directory
            os.chdir(original_cwd)
        
        # Output JSON
        json_output = json.dumps(workflow, indent=2)
        
        if output:
            with open(output, "w") as f:
                f.write(json_output)
            click.echo(f"✓ Exported workflow to {output}")
        else:
            click.echo(json_output)
        
        # Register with backend if requested
        if register:
            asyncio.run(_register_workflow(workflow))
            
    except ImportError as e:
        click.echo(f"Error: {e}", err=True)
        click.echo("Install CrewAI with: pip install crewai", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error exporting CrewAI workflow: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command("export-langgraph")
@click.argument("source")
@click.option("--output", "-o", help="Output file path (defaults to stdout)")
@click.option("--workflow-name", help="Name for the workflow (defaults to graph name)")
@click.option("--workflow-id", help="ID for the workflow (defaults to workflow-name)")
def export_langgraph(source: str, output: Optional[str], workflow_name: Optional[str], workflow_id: Optional[str]):
    """
    Export a LangGraph StateGraph to Omium workflow format.

    Args:
        source: Path to Python file and object name, e.g., 'path/to/file.py:graph_object'

    Note: The graph must be compiled (graph.compile()) before export.

    Example:
        omium export-langgraph my_workflow.py:compiled_graph > workflow.json
        omium export-langgraph my_workflow.py:compiled_graph -o workflow.json
    """
    try:
        from omium.adapters.langgraph_adapter import export_langgraph_workflow
        
        # Parse source path and object name
        if ":" not in source:
            click.echo("Error: Source must be in format 'path/to/file.py:object_name'", err=True)
            sys.exit(1)
        
        file_path, object_name = source.rsplit(":", 1)
        
        # Load the Python file and extract the graph object
        graph = _load_python_object(file_path, object_name)
        
        if graph is None:
            click.echo(f"Error: Could not find object '{object_name}' in {file_path}", err=True)
            sys.exit(1)
        
        # Export the workflow
        workflow = export_langgraph_workflow(
            graph=graph,
            workflow_name=workflow_name,
            workflow_id=workflow_id
        )
        
        # Output JSON
        json_output = json.dumps(workflow, indent=2)
        
        if output:
            with open(output, "w") as f:
                f.write(json_output)
            click.echo(f"✓ Exported workflow to {output}")
        else:
            click.echo(json_output)
            
    except ImportError as e:
        click.echo(f"Error: {e}", err=True)
        click.echo("Install LangGraph with: pip install langgraph", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error exporting LangGraph workflow: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def _load_python_object(file_path: str, object_name: str):
    """
    Load a Python object from a file.
    
    Supports:
    - Direct objects: 'file.py:my_object'
    - Method calls: 'file.py:MyClass().method()'
    - Method references: 'file.py:MyClass.method'
    - Nested attributes: 'file.py:MyClass().crew'
    
    Args:
        file_path: Path to Python file
        object_name: Name of the object to extract (can include method calls)
        
    Returns:
        The loaded object or None if not found
    """
    import importlib.util
    import os
    import re
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Load the module
    spec = importlib.util.spec_from_file_location("workflow_module", file_path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Could not load module from {file_path}")
    
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Check if object_name contains method calls or attribute access
    # Pattern: ClassName().method() or ClassName().attribute or ClassName().method
    # More flexible pattern to handle various formats
    method_call_pattern = r'^(\w+)\(\)(?:\.(\w+)(?:\(\))?)?$'
    match = re.match(method_call_pattern, object_name)
    
    if match:
        # Handle method calls like "CompetitorAnalysisWorkflowCrew().crew()"
        class_name = match.group(1)
        method_name = match.group(2) if match.group(2) else None
        
        if not hasattr(module, class_name):
            logger.debug(f"Class {class_name} not found in module")
            return None
        
        class_obj = getattr(module, class_name)
        
        # If it's a class, instantiate it
        if isinstance(class_obj, type):
            try:
                instance = class_obj()
            except Exception as e:
                # If instantiation fails (e.g., needs API key), try to get the method directly
                logger.warning(f"Could not instantiate {class_name}: {e}. Trying to get method directly.")
                if method_name:
                    if hasattr(class_obj, method_name):
                        method = getattr(class_obj, method_name)
                        # Return a wrapper that will try to call it when accessed
                        def method_wrapper():
                            try:
                                inst = class_obj()
                                return getattr(inst, method_name)()
                            except Exception as e2:
                                logger.error(f"Could not call {class_name}().{method_name}(): {e2}")
                                raise
                        return method_wrapper
                raise ValueError(f"Could not instantiate {class_name}: {e}")
            
            # If method name provided, call it
            if method_name:
                if hasattr(instance, method_name):
                    method = getattr(instance, method_name)
                    if callable(method):
                        try:
                            return method()
                        except Exception as e:
                            # If method call fails (e.g., needs API key), try to inspect the source
                            logger.warning(f"Could not call {class_name}().{method_name}(): {e}")
                            logger.warning("Attempting to extract workflow from class structure...")
                            # Try alternative approach: return a special object that can be handled by export
                            raise ValueError(f"Could not call {class_name}().{method_name}(): {e}. "
                                           f"Please ensure OPENAI_API_KEY is set or use a different export method.")
                    else:
                        return method
                else:
                    raise AttributeError(f"{class_name} instance has no attribute '{method_name}'")
            else:
                return instance
        else:
            # Not a class, return as-is
            return class_obj
    
    # Handle simple attribute access like "my_object" or "MyClass.attribute"
    if '.' in object_name and not object_name.endswith('()'):
        parts = object_name.split('.')
        obj = module
        for part in parts:
            if not hasattr(obj, part):
                return None
            obj = getattr(obj, part)
        return obj
    
    # Simple object access
    if not hasattr(module, object_name):
        return None
    
    return getattr(module, object_name)


async def _register_workflow(workflow: Dict[str, Any]) -> None:
    """Register workflow with Omium backend."""
    try:
        from omium.remote_client import RemoteOmiumClient
        
        config = get_config()
        if not config.api_key:
            click.echo("⚠️  Warning: API key not configured. Skipping registration.", err=True)
            click.echo("   Run 'omium init' to configure your API key.", err=True)
            return
        
        client = RemoteOmiumClient(
            api_url=config.api_url,
            api_key=config.api_key,
        )
        
        try:
            # Convert Omium workflow format to backend format
            workflow_type = workflow.get("type", "crewai")
            workflow_definition = workflow.get("definition", {})
            
            # Extract workflow name from definition or use workflow_id
            workflow_name = workflow_definition.get("name") or workflow.get("workflow_id", "untitled-workflow")
            
            registration_data = {
                "name": workflow_name,
                "description": f"Workflow exported from CLI: {workflow_name}",
                "workflow_type": workflow_type,
                "definition": workflow_definition,
                "config": {
                    "workflow_id": workflow.get("workflow_id"),
                    "agent_id": workflow.get("agent_id"),
                    "inputs": workflow.get("inputs", {}),
                },
                "tags": ["cli-exported"],
                "status": "draft",
            }
            
            result = await client.register_workflow(registration_data)
            click.echo(f"✓ Registered workflow: {result.get('id')} ({result.get('name')})")
            dashboard_url = config.api_url.replace('/api', '/app').replace('api.omium.ai', 'app.omium.ai')
            click.echo(f"  View in dashboard: {dashboard_url}/automation")
            
        finally:
            await client.close()
            
    except Exception as e:
        click.echo(f"⚠️  Warning: Failed to register workflow: {e}", err=True)
        click.echo("   Workflow exported locally but not registered with backend.", err=True)


async def _ensure_workflow_registered(workflow_config: Dict[str, Any]) -> None:
    """Ensure workflow is registered with backend before execution."""
    try:
        from omium.remote_client import RemoteOmiumClient
        
        config = get_config()
        if not config.api_key:
            # If no API key, skip registration (user might be running locally)
            return
        
        client = RemoteOmiumClient(
            api_url=config.api_url,
            api_key=config.api_key,
        )
        
        try:
            workflow_id = workflow_config.get("workflow_id")
            if not workflow_id:
                # No workflow_id, can't check if registered
                return
            
            # Check if workflow exists (by name, since backend uses UUIDs)
            workflow_type = workflow_config.get("type", "crewai")
            workflow_definition = workflow_config.get("definition", {})
            workflow_name = workflow_definition.get("name") or workflow_id
            
            # List workflows to see if one with this name exists
            workflows_result = await client.list_workflows(
                workflow_type=workflow_type,
                page=1,
                page_size=100
            )
            
            existing = None
            workflows = workflows_result.get("workflows", [])
            for wf in workflows:
                if wf.get("name") == workflow_name or wf.get("config", {}).get("workflow_id") == workflow_id:
                    existing = wf
                    break
            
            if not existing:
                # Workflow not registered, register it now
                click.echo(f"Workflow '{workflow_name}' not found in backend. Registering...")
                
                registration_data = {
                    "name": workflow_name,
                    "description": f"Workflow auto-registered from CLI execution",
                    "workflow_type": workflow_type,
                    "definition": workflow_definition,
                    "config": {
                        "workflow_id": workflow_id,
                        "agent_id": workflow_config.get("agent_id"),
                        "inputs": workflow_config.get("inputs", {}),
                    },
                    "tags": ["cli-executed"],
                    "status": "draft",
                }
                
                result = await client.register_workflow(registration_data)
                click.echo(f"✓ Auto-registered workflow: {result.get('id')} ({result.get('name')})")
            else:
                # Workflow exists
                logger.debug(f"Workflow {workflow_name} already registered (ID: {existing.get('id')})")
            
        finally:
            await client.close()
            
    except Exception as e:
        # Don't fail execution if registration fails
        logger.warning(f"Failed to ensure workflow registration: {e}")
        click.echo(f"⚠️  Warning: Could not verify workflow registration: {e}", err=True)
        click.echo("   Continuing with execution...", err=True)


if __name__ == "__main__":
    cli()
