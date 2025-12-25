"""AI-powered workflow automation for content management commands"""

import click

from praisonaiwp.ai import AI_AVAILABLE
from praisonaiwp.core.config import Config
from praisonaiwp.core.ssh_manager import SSHManager
from praisonaiwp.core.wp_client import WPClient
from praisonaiwp.utils.ai_formatter import AIFormatter


@click.group()
def workflow():
    """AI-powered workflow automation for content management"""
    pass


@workflow.command()
@click.argument('name')
@click.option('--description', help='Workflow description')
@click.option('--trigger', help='Trigger type (manual, schedule, event)')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def create(name, description, trigger, server, json_output, verbose):
    """Create a new AI workflow"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"workflow create {name}",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"workflow create {name}",
            error_code="CONFIG_NOT_FOUND"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    try:
        # Get server config
        server_config = config.get_server(server)
        
        # Create SSH manager and WP client
        ssh_manager = SSHManager(
            hostname=server_config.get('hostname') or server_config.get('ssh_host'),
            username=server_config.get('username') or server_config.get('ssh_user'),
            key_file=server_config.get('key_file') or server_config.get('ssh_key'),
            port=server_config.get('port', 22)
        )
        
        wp_client = WPClient(
            ssh=ssh_manager,
            wp_path=server_config.get('wp_path', '/var/www/html'),
            php_bin=server_config.get('php_bin', 'php'),
            wp_cli=server_config.get('wp_cli', '/usr/local/bin/wp'),
            verify_installation=False
        )
        
        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)
        
        # Create workflow
        if verbose:
            click.echo(f"Creating workflow: {name}")
        
        workflow_result = integration.create_workflow(
            name=name,
            description=description or f"AI workflow: {name}",
            trigger=trigger or 'manual'
        )
        
        # Format output
        success_msg = AIFormatter.success_response(
            workflow_result,
            f"Created workflow: {name}",
            command=f"workflow create {name}"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n🔧 Workflow Created: {name}")
            click.echo("=" * 40)
            click.echo(f"ID: {workflow_result.get('workflow_id', 'N/A')}")
            click.echo(f"Description: {workflow_result.get('description', 'N/A')}")
            click.echo(f"Trigger: {workflow_result.get('trigger', 'N/A')}")
            click.echo(f"Status: {workflow_result.get('status', 'draft')}")
            
            # Next steps
            instructions = workflow_result.get('next_steps', [])
            if instructions:
                click.echo(f"\n📋 Next Steps:")
                for i, instruction in enumerate(instructions, 1):
                    click.echo(f"  {i}. {instruction}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"workflow create {name}",
            error_code="WORKFLOW_CREATION_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@workflow.command()
@click.argument('workflow_id')
@click.option('--action', help='Action to add (generate, optimize, translate, schedule)')
@click.option('--params', help='Action parameters (JSON format)')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def add_step(workflow_id, action, params, server, json_output, verbose):
    """Add a step to an existing workflow"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"workflow add-step {workflow_id}",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"workflow add-step {workflow_id}",
            error_code="CONFIG_NOT_FOUND"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    try:
        # Parse parameters
        action_params = {}
        if params:
            try:
                action_params = json.loads(params)
            except json.JSONDecodeError:
                error_msg = AIFormatter.error_response(
                    "Invalid JSON format for parameters",
                    command=f"workflow add-step {workflow_id}",
                    error_code="INVALID_PARAMS"
                )
                click.echo(AIFormatter.format_output(error_msg, json_output))
                return
        
        # Get server config
        server_config = config.get_server(server)
        
        # Create SSH manager and WP client
        ssh_manager = SSHManager(
            hostname=server_config.get('hostname') or server_config.get('ssh_host'),
            username=server_config.get('username') or server_config.get('ssh_user'),
            key_file=server_config.get('key_file') or server_config.get('ssh_key'),
            port=server_config.get('port', 22)
        )
        
        wp_client = WPClient(
            ssh=ssh_manager,
            wp_path=server_config.get('wp_path', '/var/www/html'),
            php_bin=server_config.get('php_bin', 'php'),
            wp_cli=server_config.get('wp_cli', '/usr/local/bin/wp'),
            verify_installation=False
        )
        
        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)
        
        # Add step to workflow
        if verbose:
            click.echo(f"Adding step '{action}' to workflow {workflow_id}")
        
        step_result = integration.add_workflow_step(
            workflow_id=workflow_id,
            action=action,
            params=action_params
        )
        
        # Format output
        success_msg = AIFormatter.success_response(
            step_result,
            f"Added step '{action}' to workflow {workflow_id}",
            command=f"workflow add-step {workflow_id}"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n➕ Step Added to Workflow {workflow_id}")
            click.echo("=" * 40)
            click.echo(f"Action: {action}")
            click.echo(f"Step ID: {step_result.get('step_id', 'N/A')}")
            click.echo(f"Order: {step_result.get('order', 'N/A')}")
            
            # Parameters
            if action_params:
                click.echo(f"Parameters:")
                for key, value in action_params.items():
                    click.echo(f"  {key}: {value}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"workflow add-step {workflow_id}",
            error_code="STEP_ADDITION_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@workflow.command()
@click.argument('workflow_id')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def run(workflow_id, server, json_output, verbose):
    """Execute a workflow"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"workflow run {workflow_id}",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"workflow run {workflow_id}",
            error_code="CONFIG_NOT_FOUND"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    try:
        # Get server config
        server_config = config.get_server(server)
        
        # Create SSH manager and WP client
        ssh_manager = SSHManager(
            hostname=server_config.get('hostname') or server_config.get('ssh_host'),
            username=server_config.get('username') or server_config.get('ssh_user'),
            key_file=server_config.get('key_file') or server_config.get('ssh_key'),
            port=server_config.get('port', 22)
        )
        
        wp_client = WPClient(
            ssh=ssh_manager,
            wp_path=server_config.get('wp_path', '/var/www/html'),
            php_bin=server_config.get('php_bin', 'php'),
            wp_cli=server_config.get('wp_cli', '/usr/local/bin/wp'),
            verify_installation=False
        )
        
        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)
        
        # Run workflow
        if verbose:
            click.echo(f"Running workflow {workflow_id}...")
        
        execution_result = integration.run_workflow(workflow_id)
        
        # Format output
        success_msg = AIFormatter.success_response(
            execution_result,
            f"Workflow {workflow_id} execution complete",
            command=f"workflow run {workflow_id}"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n🚀 Workflow Execution Complete")
            click.echo("=" * 40)
            click.echo(f"Workflow ID: {workflow_id}")
            click.echo(f"Execution ID: {execution_result.get('execution_id', 'N/A')}")
            click.echo(f"Status: {execution_result.get('status', 'Unknown')}")
            click.echo(f"Duration: {execution_result.get('duration', 'N/A')}")
            
            # Steps executed
            steps = execution_result.get('steps', [])
            if steps:
                click.echo(f"\n📋 Steps Executed:")
                for i, step in enumerate(steps, 1):
                    status = "✅" if step.get('status') == 'success' else "❌"
                    click.echo(f"  {status} {i}. {step.get('action', 'Unknown')}")
                    if step.get('result'):
                        click.echo(f"     Result: {step['result']}")
            
            # Results
            results = execution_result.get('results', {})
            if results:
                click.echo(f"\n📊 Results:")
                for key, value in results.items():
                    click.echo(f"  {key}: {value}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"workflow run {workflow_id}",
            error_code="WORKFLOW_EXECUTION_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@workflow.command()
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def list(server, json_output, verbose):
    """List all workflows"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command="workflow list",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command="workflow list",
            error_code="CONFIG_NOT_FOUND"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    try:
        # Get server config
        server_config = config.get_server(server)
        
        # Create SSH manager and WP client
        ssh_manager = SSHManager(
            hostname=server_config.get('hostname') or server_config.get('ssh_host'),
            username=server_config.get('username') or server_config.get('ssh_user'),
            key_file=server_config.get('key_file') or server_config.get('ssh_key'),
            port=server_config.get('port', 22)
        )
        
        wp_client = WPClient(
            ssh=ssh_manager,
            wp_path=server_config.get('wp_path', '/var/www/html'),
            php_bin=server_config.get('php_bin', 'php'),
            wp_cli=server_config.get('wp_cli', '/usr/local/bin/wp'),
            verify_installation=False
        )
        
        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)
        
        # List workflows
        if verbose:
            click.echo("Fetching workflows...")
        
        workflows_result = integration.list_workflows()
        
        # Format output
        success_msg = AIFormatter.success_response(
            workflows_result,
            f"Found {len(workflows_result.get('workflows', []))} workflows",
            command="workflow list"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n📋 Workflows")
            click.echo("=" * 30)
            
            workflows = workflows_result.get('workflows', [])
            if not workflows:
                click.echo("No workflows found.")
                return
            
            for workflow in workflows:
                click.echo(f"\n🔧 {workflow.get('name', 'Unknown')} (ID: {workflow.get('id', 'N/A')})")
                click.echo(f"   Description: {workflow.get('description', 'N/A')}")
                click.echo(f"   Status: {workflow.get('status', 'Unknown')}")
                click.echo(f"   Trigger: {workflow.get('trigger', 'Unknown')}")
                click.echo(f"   Steps: {workflow.get('step_count', 0)}")
                if workflow.get('last_run'):
                    click.echo(f"   Last run: {workflow['last_run']}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command="workflow list",
            error_code="WORKFLOW_LIST_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@workflow.command()
@click.argument('workflow_id')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def status(workflow_id, server, json_output, verbose):
    """Get workflow status and details"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"workflow status {workflow_id}",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"workflow status {workflow_id}",
            error_code="CONFIG_NOT_FOUND"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    try:
        # Get server config
        server_config = config.get_server(server)
        
        # Create SSH manager and WP client
        ssh_manager = SSHManager(
            hostname=server_config.get('hostname') or server_config.get('ssh_host'),
            username=server_config.get('username') or server_config.get('ssh_user'),
            key_file=server_config.get('key_file') or server_config.get('ssh_key'),
            port=server_config.get('port', 22)
        )
        
        wp_client = WPClient(
            ssh=ssh_manager,
            wp_path=server_config.get('wp_path', '/var/www/html'),
            php_bin=server_config.get('php_bin', 'php'),
            wp_cli=server_config.get('wp_cli', '/usr/local/bin/wp'),
            verify_installation=False
        )
        
        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)
        
        # Get workflow status
        if verbose:
            click.echo(f"Getting status for workflow {workflow_id}...")
        
        status_result = integration.get_workflow_status(workflow_id)
        
        # Format output
        success_msg = AIFormatter.success_response(
            status_result,
            f"Status retrieved for workflow {workflow_id}",
            command=f"workflow status {workflow_id}"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n📊 Workflow Status: {workflow_id}")
            click.echo("=" * 40)
            
            workflow = status_result.get('workflow', {})
            if workflow:
                click.echo(f"Name: {workflow.get('name', 'Unknown')}")
                click.echo(f"Status: {workflow.get('status', 'Unknown')}")
                click.echo(f"Trigger: {workflow.get('trigger', 'Unknown')}")
                click.echo(f"Created: {workflow.get('created_at', 'N/A')}")
                click.echo(f"Updated: {workflow.get('updated_at', 'N/A')}")
            
            # Steps
            steps = status_result.get('steps', [])
            if steps:
                click.echo(f"\n📋 Steps:")
                for i, step in enumerate(steps, 1):
                    status_icon = {
                        'pending': '⏸️',
                        'running': '🔄',
                        'completed': '✅',
                        'failed': '❌'
                    }.get(step.get('status', 'pending'), '❓')
                    
                    click.echo(f"  {i}. {status_icon} {step.get('action', 'Unknown')}")
                    click.echo(f"     Order: {step.get('order', 'N/A')}")
                    if step.get('last_run'):
                        click.echo(f"     Last run: {step['last_run']}")
            
            # Recent executions
            executions = status_result.get('recent_executions', [])
            if executions:
                click.echo(f"\n🚀 Recent Executions:")
                for execution in executions[:5]:
                    status_icon = "✅" if execution.get('status') == 'success' else "❌"
                    click.echo(f"  {status_icon} {execution.get('execution_id', 'Unknown')} - {execution.get('status', 'Unknown')}")
                    if execution.get('duration'):
                        click.echo(f"     Duration: {execution['duration']}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"workflow status {workflow_id}",
            error_code="WORKFLOW_STATUS_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))


@workflow.command()
@click.argument('workflow_id')
@click.confirmation_option(prompt='Are you sure you want to delete this workflow?')
@click.option('--server', help='Server name from config')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.option('--verbose', is_flag=True, help='Verbose output')
def delete(workflow_id, server, json_output, verbose):
    """Delete a workflow"""
    
    # Check if AI is available
    if not AI_AVAILABLE:
        error_msg = AIFormatter.error_response(
            "AI features not available. Install with: pip install 'praisonaiwp[ai]'",
            command=f"workflow delete {workflow_id}",
            error_code="AI_NOT_AVAILABLE"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    # Load config
    config = Config()
    if not config.exists():
        error_msg = AIFormatter.error_response(
            "Configuration not found. Run 'praisonaiwp init' first.",
            command=f"workflow delete {workflow_id}",
            error_code="CONFIG_NOT_FOUND"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
        return
    
    try:
        # Get server config
        server_config = config.get_server(server)
        
        # Create SSH manager and WP client
        ssh_manager = SSHManager(
            hostname=server_config.get('hostname') or server_config.get('ssh_host'),
            username=server_config.get('username') or server_config.get('ssh_user'),
            key_file=server_config.get('key_file') or server_config.get('ssh_key'),
            port=server_config.get('port', 22)
        )
        
        wp_client = WPClient(
            ssh=ssh_manager,
            wp_path=server_config.get('wp_path', '/var/www/html'),
            php_bin=server_config.get('php_bin', 'php'),
            wp_cli=server_config.get('wp_cli', '/usr/local/bin/wp'),
            verify_installation=False
        )
        
        # Import AI integration
        from praisonaiwp.ai.integration import PraisonAIWPIntegration
        integration = PraisonAIWPIntegration(wp_client, verbose=1 if verbose else 0)
        
        # Delete workflow
        if verbose:
            click.echo(f"Deleting workflow {workflow_id}...")
        
        delete_result = integration.delete_workflow(workflow_id)
        
        # Format output
        success_msg = AIFormatter.success_response(
            delete_result,
            f"Workflow {workflow_id} deleted successfully",
            command=f"workflow delete {workflow_id}"
        )
        
        if json_output:
            click.echo(AIFormatter.format_output(success_msg))
        else:
            click.echo(f"\n🗑️  Workflow Deleted")
            click.echo("=" * 30)
            click.echo(f"Workflow ID: {workflow_id}")
            click.echo(f"Status: {delete_result.get('status', 'Deleted')}")
        
    except Exception as e:
        error_msg = AIFormatter.error_response(
            str(e),
            command=f"workflow delete {workflow_id}",
            error_code="WORKFLOW_DELETION_ERROR"
        )
        click.echo(AIFormatter.format_output(error_msg, json_output))
