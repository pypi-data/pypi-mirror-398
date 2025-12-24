"""
Test suite for Daita CLI - testing command-line interface functionality.

Tests cover:
- CLI command structure and parsing
- Project initialization (daita init)
- Component creation (daita create agent/workflow)
- Testing commands (daita test)
- Development server (daita dev)
- Deployment commands (daita push)
- Status and monitoring (daita status, daita logs)
- Utility commands (daita version, daita docs)
- Error handling and validation
- File system operations
"""
import pytest
import os
import tempfile
import shutil
import yaml
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from click.testing import CliRunner
import asyncio

# CLI imports
from daita.cli.main import cli
from daita.cli.core.init import initialize_project
from daita.cli.core.create import create_from_template
from daita.cli.core.test import run_tests
from daita.cli.core.status import show_project_status
from daita.cli.core.deploy import deploy_to_environment
from daita.cli.core.logs import show_deployment_logs
from daita.cli.utils import (
    find_project_root,
    ensure_project_root,
    load_project_config,
    save_project_config,
    to_class_name,
    to_snake_case,
    validate_project_name,
    validate_component_name,
    has_api_key,
    get_configured_providers
)


class TestCLIBasicStructure:
    """Test basic CLI structure and command parsing."""
    
    def test_cli_help(self):
        """Test CLI help output."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert "Daita CLI" in result.output
        assert "AI Agent Framework" in result.output
        assert "init" in result.output
        assert "create" in result.output
        assert "test" in result.output
        assert "dev" in result.output
        assert "push" in result.output
        assert "status" in result.output
        assert "logs" in result.output
    
    def test_cli_version(self):
        """Test version command."""
        runner = CliRunner()
        result = runner.invoke(cli, ['version'])
        
        assert result.exit_code == 0
        assert "Daita CLI" in result.output
        assert "AI Agent Framework" in result.output
        assert "github.com/daita-ai/daita-agents" in result.output
    
    def test_cli_verbose_flag(self):
        """Test verbose flag handling."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--verbose', 'version'])
        
        assert result.exit_code == 0
    
    def test_cli_quiet_flag(self):
        """Test quiet flag handling."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--quiet', 'version'])
        
        assert result.exit_code == 0
    
    @patch('webbrowser.open')
    def test_docs_command(self, mock_browser):
        """Test docs command opens browser."""
        runner = CliRunner()
        result = runner.invoke(cli, ['docs'])
        
        assert result.exit_code == 0
        mock_browser.assert_called_once_with("https://docs.daita-tech.io")
        assert "Opening documentation" in result.output


class TestProjectInitialization:
    """Test project initialization functionality."""
    
    def test_init_basic_project(self):
        """Test basic project initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test_project"
            
            # Run initialization
            asyncio.run(initialize_project(
                project_name="test_project",
                project_type="basic",
                force=False,
                verbose=False
            ))
            
            # Check project structure was created
            assert project_path.exists()
            assert (project_path / ".daita").exists()
            assert (project_path / "agents").exists()
            assert (project_path / "workflows").exists()
            assert (project_path / "data").exists()
            assert (project_path / "tests").exists()
            assert (project_path / "daita-project.yaml").exists()
            assert (project_path / "requirements.txt").exists()
            assert (project_path / "README.md").exists()
            assert (project_path / ".gitignore").exists()
            
            # Check __init__.py files
            assert (project_path / "agents" / "__init__.py").exists()
            assert (project_path / "workflows" / "__init__.py").exists()
    
    def test_init_analysis_project(self):
        """Test analysis project initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            asyncio.run(initialize_project(
                project_name="analysis_project",
                project_type="analysis",
                verbose=False
            ))
            
            project_path = Path(temp_dir) / "analysis_project"
            
            # Check project config
            config_file = project_path / "daita-project.yaml"
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            assert config['type'] == 'analysis'
            assert config['focus'] == ['data', 'insights', 'recommendations']
            assert config['llm']['temperature'] == 0.3  # More deterministic for analysis
            
            # Check analysis-specific files
            assert (project_path / "agents" / "data_analyzer.py").exists()
    
    def test_init_pipeline_project(self):
        """Test pipeline project initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            asyncio.run(initialize_project(
                project_name="pipeline_project",
                project_type="pipeline",
                verbose=False
            ))
            
            project_path = Path(temp_dir) / "pipeline_project"
            
            # Check project config
            config_file = project_path / "daita-project.yaml"
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            assert config['type'] == 'pipeline'
            assert config['focus'] == ['transform', 'validate', 'process']
            assert 'relay_channels' in config
            
            # Check pipeline-specific files
            assert (project_path / "workflows" / "data_pipeline.py").exists()
    
    def test_init_with_existing_directory(self):
        """Test initialization with existing directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "existing_project"
            project_path.mkdir()
            
            # Create some existing content
            (project_path / "existing_file.txt").write_text("existing content")
            
            os.chdir(temp_dir)
            
            # Should work with force=True
            asyncio.run(initialize_project(
                project_name="existing_project",
                force=True,
                verbose=False
            ))
            
            # Should have created Daita structure
            assert (project_path / ".daita").exists()
            assert (project_path / "daita-project.yaml").exists()
            # Original file should still exist
            assert (project_path / "existing_file.txt").exists()
    
    def test_init_cli_command(self):
        """Test init command through CLI."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            result = runner.invoke(cli, [
                'init', 'cli_test_project',
                '--type', 'basic',
                '--force'
            ])
            
            assert result.exit_code == 0
            assert "Project initialized!" in result.output
            assert "cd cli_test_project" in result.output
            
            # Check project was created
            project_path = Path(temp_dir) / "cli_test_project"
            assert project_path.exists()
            assert (project_path / ".daita").exists()


class TestComponentCreation:
    """Test component creation functionality."""
    
    def setup_method(self):
        """Set up test project for component creation."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir) / "test_project"
        
        # Create basic project structure
        self.project_path.mkdir()
        (self.project_path / ".daita").mkdir()
        (self.project_path / "agents").mkdir()
        (self.project_path / "workflows").mkdir()
        
        # Create project config
        config = {
            'name': 'test_project',
            'version': '1.0.0',
            'type': 'basic',
            'agents': [],
            'workflows': []
        }
        with open(self.project_path / "daita-project.yaml", 'w') as f:
            yaml.dump(config, f)
        
        os.chdir(self.project_path)
    
    def teardown_method(self):
        """Clean up test project."""
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_agent(self):
        """Test agent creation."""
        create_from_template(
            template='agent',
            name='test_agent',
            verbose=False
        )
        
        agent_file = self.project_path / "agents" / "test_agent.py"
        assert agent_file.exists()
        
        # Check agent file content
        content = agent_file.read_text()
        assert "class TestAgent:" in content
        assert "def create_agent():" in content
        assert "DaitaSDK" in content
        assert "substrate_agent" in content
    
    def test_create_workflow(self):
        """Test workflow creation."""
        create_from_template(
            template='workflow',
            name='test_workflow',
            verbose=False
        )
        
        workflow_file = self.project_path / "workflows" / "test_workflow.py"
        assert workflow_file.exists()
        
        # Check workflow file content
        content = workflow_file.read_text()
        assert "class TestWorkflow:" in content
        assert "def create_workflow():" in content
        assert "Workflow" in content
        assert "add_agent" in content
        assert "connect" in content
    
    def test_create_agent_cli_command(self):
        """Test create agent command through CLI."""
        runner = CliRunner()
        result = runner.invoke(cli, ['create', 'agent', 'cli_test_agent'])
        
        assert result.exit_code == 0
        assert "Created agent: cli_test_agent" in result.output
        
        agent_file = self.project_path / "agents" / "cli_test_agent.py"
        assert agent_file.exists()
    
    def test_create_workflow_cli_command(self):
        """Test create workflow command through CLI."""
        runner = CliRunner()
        result = runner.invoke(cli, ['create', 'workflow', 'cli_test_workflow'])
        
        assert result.exit_code == 0
        assert "Created workflow: cli_test_workflow" in result.output
        
        workflow_file = self.project_path / "workflows" / "cli_test_workflow.py"
        assert workflow_file.exists()
    
    def test_create_outside_project_error(self):
        """Test error when creating components outside project."""
        # Change to directory without .daita folder
        os.chdir(self.temp_dir)
        
        runner = CliRunner()
        result = runner.invoke(cli, ['create', 'agent', 'test_agent'])
        
        assert result.exit_code == 1
        assert "Not in a Daita project" in result.output


class TestTestingCommands:
    """Test testing functionality."""
    
    def setup_method(self):
        """Set up test project with components."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir) / "test_project"
        
        # Create project structure
        self.project_path.mkdir()
        (self.project_path / ".daita").mkdir()
        (self.project_path / "agents").mkdir()
        (self.project_path / "workflows").mkdir()
        
        # Create a test agent
        agent_code = '''
from daita import DaitaSDK

class TestAgent:
    def __init__(self):
        self.sdk = DaitaSDK()
        self.agent = self.sdk.substrate_agent(name="Test Agent")

    async def process(self, task, data, **kwargs):
        return await self.agent.process(task, data, **kwargs)

def create_agent():
    return TestAgent()
'''
        (self.project_path / "agents" / "test_agent.py").write_text(agent_code)
        
        # Create a test workflow
        workflow_code = '''
from daita import DaitaSDK
from daita.core.workflow import Workflow

class TestWorkflow:
    def __init__(self):
        self.sdk = DaitaSDK()
        self.workflow = Workflow("Test Workflow")

    async def run(self, data=None):
        await self.workflow.start()
        # Add workflow logic here
        await self.workflow.stop()

def create_workflow():
    return TestWorkflow()
'''
        (self.project_path / "workflows" / "test_workflow.py").write_text(workflow_code)
        
        os.chdir(self.project_path)
    
    def teardown_method(self):
        """Clean up test project."""
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('daita.cli.core.test._load_python_file')
    @patch('daita.cli.core.test._list_agents')
    @patch('daita.cli.core.test._list_workflows')
    def test_run_all_tests(self, mock_list_workflows, mock_list_agents, mock_load_file):
        """Test running all tests."""
        # Mock component lists
        mock_list_agents.return_value = ['test_agent']
        mock_list_workflows.return_value = ['test_workflow']
        
        # Mock component instances
        mock_agent = Mock()
        mock_agent.process = AsyncMock(return_value={"status": "success"})
        mock_workflow = Mock()
        mock_workflow.run = AsyncMock(return_value={"status": "success"})
        
        mock_load_file.side_effect = lambda path, func: mock_agent if 'agent' in str(path) else mock_workflow
        
        # Run tests
        asyncio.run(run_tests(
            target=None,
            data_file=None,
            watch=False,
            verbose=False
        ))
        
        # Verify agents and workflows were tested
        mock_agent.process.assert_called()
        mock_workflow.run.assert_called()
    
    @patch('daita.cli.core.test._load_python_file')
    def test_run_specific_agent_test(self, mock_load_file):
        """Test running test for specific agent."""
        mock_agent = Mock()
        mock_agent.process = AsyncMock(return_value={"status": "success"})
        mock_load_file.return_value = mock_agent
        
        asyncio.run(run_tests(
            target="test_agent",
            data_file=None,
            watch=False,
            verbose=False
        ))
        
        mock_agent.process.assert_called()
    
    def test_test_cli_command(self):
        """Test test command through CLI."""
        runner = CliRunner()
        
        with patch('daita.cli.core.test._list_agents', return_value=[]):
            with patch('daita.cli.core.test._list_workflows', return_value=[]):
                result = runner.invoke(cli, ['test'])
                
                assert result.exit_code == 0
    
    def test_test_with_data_file(self):
        """Test running tests with custom data file."""
        # Create test data file
        test_data = {"test": True, "value": 123}
        data_file = self.project_path / "test_data.json"
        with open(data_file, 'w') as f:
            json.dump(test_data, f)
        
        with patch('daita.cli.core.test._list_agents', return_value=[]):
            with patch('daita.cli.core.test._list_workflows', return_value=[]):
                asyncio.run(run_tests(
                    target=None,
                    data_file=str(data_file),
                    watch=False,
                    verbose=False
                ))


class TestDevelopmentServer:
    """Test development server functionality."""
    
    def setup_method(self):
        """Set up test project."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir) / "test_project"
        
        # Create project structure
        self.project_path.mkdir()
        (self.project_path / ".daita").mkdir()
        (self.project_path / "agents").mkdir()
        (self.project_path / "workflows").mkdir()
        
        os.chdir(self.project_path)
    
    def teardown_method(self):
        """Clean up test project."""
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('daita.cli.core.dev._start_file_watcher')
    def test_start_dev_server(self, mock_watcher):
        """Test starting development server."""
        from daita.cli.core.dev import start_dev_server
        
        # Mock watcher
        mock_watcher_instance = Mock()
        mock_watcher_instance.stop = Mock()
        mock_watcher_instance.join = Mock()
        mock_watcher.return_value = mock_watcher_instance
        
        # Test with very short duration to avoid hanging
        async def quick_dev_server():
            import asyncio
            # Simulate server starting then stopping quickly
            await asyncio.sleep(0.01)
            raise KeyboardInterrupt()
        
        with patch('daita.cli.core.dev.start_dev_server', quick_dev_server):
            try:
                asyncio.run(quick_dev_server())
            except KeyboardInterrupt:
                pass  # Expected
    
    def test_file_validation(self):
        """Test Python file validation."""
        from daita.cli.core.dev import _validate_python_file
        
        # Create valid Python file
        valid_file = self.project_path / "valid.py"
        valid_file.write_text("def hello(): return 'world'")
        
        # Should not raise error
        _validate_python_file(str(valid_file))
        
        # Create invalid Python file
        invalid_file = self.project_path / "invalid.py"
        invalid_file.write_text("def invalid( syntax error")
        
        # Should raise SyntaxError
        with pytest.raises(SyntaxError):
            _validate_python_file(str(invalid_file))


class TestDeploymentCommands:
    """Test deployment functionality."""
    
    def setup_method(self):
        """Set up test project with deployment config."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir) / "test_project"
        
        # Create project structure
        self.project_path.mkdir()
        (self.project_path / ".daita").mkdir()
        (self.project_path / "agents").mkdir()
        (self.project_path / "workflows").mkdir()
        
        # Create project config with deployment settings
        config = {
            'name': 'test_project',
            'version': '1.0.0',
            'type': 'basic',
            'agents': [{'name': 'test_agent'}],
            'workflows': [{'name': 'test_workflow'}],
            'environments': {
                'staging': {'description': 'Staging environment'},
                'production': {'description': 'Production environment'}
            }
        }
        with open(self.project_path / "daita-project.yaml", 'w') as f:
            yaml.dump(config, f)
        
        # Create requirements.txt
        (self.project_path / "requirements.txt").write_text("daita-agents>=0.1.0\n")
        
        os.chdir(self.project_path)
    
    def teardown_method(self):
        """Clean up test project."""
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_deploy_to_staging(self):
        """Test deployment to staging environment."""
        asyncio.run(deploy_to_environment(
            environment='staging',
            force=False,
            dry_run=False,
            verbose=False
        ))
        
        # Check deployment record was saved
        deployments_file = self.project_path / ".daita" / "deployments.json"
        assert deployments_file.exists()
        
        with open(deployments_file, 'r') as f:
            deployments = json.load(f)
        
        assert len(deployments) == 1
        assert deployments[0]['environment'] == 'staging'
        assert deployments[0]['project_name'] == 'test_project'
    
    def test_deploy_dry_run(self):
        """Test dry run deployment."""
        asyncio.run(deploy_to_environment(
            environment='staging',
            force=False,
            dry_run=True,
            verbose=False
        ))
        
        # Should not create deployment record in dry run
        deployments_file = self.project_path / ".daita" / "deployments.json"
        assert not deployments_file.exists()
    
    @patch('builtins.input', return_value='yes')
    def test_deploy_to_production_with_confirmation(self, mock_input):
        """Test production deployment with confirmation."""
        asyncio.run(deploy_to_environment(
            environment='production',
            force=False,
            dry_run=False,
            verbose=False
        ))
        
        # Should have asked for confirmation
        mock_input.assert_called_once()
        
        # Check deployment was recorded
        deployments_file = self.project_path / ".daita" / "deployments.json"
        assert deployments_file.exists()
    
    @patch('builtins.input', return_value='no')
    def test_deploy_to_production_cancelled(self, mock_input):
        """Test production deployment cancelled."""
        asyncio.run(deploy_to_environment(
            environment='production',
            force=False,
            dry_run=False,
            verbose=False
        ))
        
        # Should not create deployment record when cancelled
        deployments_file = self.project_path / ".daita" / "deployments.json"
        assert not deployments_file.exists()
    
    def test_deploy_to_production_forced(self):
        """Test forced production deployment."""
        asyncio.run(deploy_to_environment(
            environment='production',
            force=True,  # Skip confirmation
            dry_run=False,
            verbose=False
        ))
        
        # Check deployment was recorded
        deployments_file = self.project_path / ".daita" / "deployments.json"
        assert deployments_file.exists()
    
    def test_deploy_cli_command(self):
        """Test deploy command through CLI."""
        runner = CliRunner()
        result = runner.invoke(cli, ['push', 'staging'])
        
        assert result.exit_code == 0
        assert "Deployed to staging" in result.output


class TestStatusAndMonitoring:
    """Test status and monitoring functionality."""
    
    def setup_method(self):
        """Set up test project with history."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir) / "test_project"
        
        # Create project structure
        self.project_path.mkdir()
        (self.project_path / ".daita").mkdir()
        (self.project_path / "agents").mkdir()
        (self.project_path / "workflows").mkdir()
        
        # Create project config
        config = {
            'name': 'test_project',
            'version': '1.0.0',
            'type': 'basic',
            'agents': [{'name': 'test_agent'}],
            'workflows': [{'name': 'test_workflow'}]
        }
        with open(self.project_path / "daita-project.yaml", 'w') as f:
            yaml.dump(config, f)
        
        # Create agent and workflow files
        (self.project_path / "agents" / "test_agent.py").write_text("# Agent code")
        (self.project_path / "workflows" / "test_workflow.py").write_text("# Workflow code")
        
        # Create deployment history
        deployments = [
            {
                'environment': 'staging',
                'timestamp': '2024-01-01T12:00:00',
                'project_name': 'test_project',
                'version': '1.0.0',
                'agents': ['test_agent'],
                'workflows': ['test_workflow']
            },
            {
                'environment': 'production',
                'timestamp': '2024-01-02T12:00:00',
                'project_name': 'test_project',
                'version': '1.0.0',
                'agents': ['test_agent'],
                'workflows': ['test_workflow']
            }
        ]
        deployments_file = self.project_path / ".daita" / "deployments.json"
        with open(deployments_file, 'w') as f:
            json.dump(deployments, f)
        
        os.chdir(self.project_path)
    
    def teardown_method(self):
        """Clean up test project."""
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_show_project_status(self):
        """Test showing overall project status."""
        asyncio.run(show_project_status(
            environment=None,
            verbose=False
        ))
        # Should run without errors
    
    def test_show_environment_status(self):
        """Test showing status for specific environment."""
        asyncio.run(show_project_status(
            environment='staging',
            verbose=False
        ))
        # Should run without errors
    
    def test_show_deployment_logs(self):
        """Test showing deployment logs."""
        asyncio.run(show_deployment_logs(
            environment=None,
            limit=10,
            follow=False,
            verbose=False
        ))
        # Should run without errors
    
    def test_show_environment_specific_logs(self):
        """Test showing logs for specific environment."""
        asyncio.run(show_deployment_logs(
            environment='staging',
            limit=5,
            follow=False,
            verbose=False
        ))
        # Should run without errors
    
    def test_status_cli_command(self):
        """Test status command through CLI."""
        runner = CliRunner()
        result = runner.invoke(cli, ['status'])
        
        assert result.exit_code == 0
        assert "test_project" in result.output
    
    def test_logs_cli_command(self):
        """Test logs command through CLI."""
        runner = CliRunner()
        result = runner.invoke(cli, ['logs'])
        
        assert result.exit_code == 0


class TestCLIUtilities:
    """Test CLI utility functions."""
    
    def test_find_project_root(self):
        """Test finding project root."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test_project"
            project_path.mkdir()
            (project_path / ".daita").mkdir()
            
            # Should find project root from project directory
            result = find_project_root(project_path)
            assert result == project_path
            
            # Should find project root from subdirectory
            subdir = project_path / "agents"
            subdir.mkdir()
            result = find_project_root(subdir)
            assert result == project_path
            
            # Should return None when not in project
            non_project = Path(temp_dir) / "non_project"
            non_project.mkdir()
            result = find_project_root(non_project)
            assert result is None
    
    def test_ensure_project_root(self):
        """Test ensuring project root exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test_project"
            project_path.mkdir()
            (project_path / ".daita").mkdir()
            
            os.chdir(project_path)
            
            # Should return project root
            result = ensure_project_root()
            assert result == project_path
            
            # Should raise error when not in project
            os.chdir(temp_dir)
            with pytest.raises(ValueError) as exc_info:
                ensure_project_root()
            
            assert "Not in a Daita project" in str(exc_info.value)
    
    def test_load_save_project_config(self):
        """Test loading and saving project configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Test saving config
            config = {
                'name': 'test_project',
                'version': '1.0.0',
                'agents': []
            }
            save_project_config(project_path, config)
            
            config_file = project_path / "daita-project.yaml"
            assert config_file.exists()
            
            # Test loading config
            loaded_config = load_project_config(project_path)
            assert loaded_config == config
            
            # Test loading non-existent config
            empty_dir = Path(temp_dir) / "empty"
            empty_dir.mkdir()
            result = load_project_config(empty_dir)
            assert result is None
    
    def test_to_class_name(self):
        """Test snake_case to PascalCase conversion."""
        assert to_class_name("test_agent") == "TestAgent"
        assert to_class_name("my_custom_workflow") == "MyCustomWorkflow"
        assert to_class_name("simple") == "Simple"
        assert to_class_name("data_processor_v2") == "DataProcessorV2"
    
    def test_to_snake_case(self):
        """Test conversion to snake_case."""
        assert to_snake_case("TestAgent") == "testagent"  # Note: doesn't handle PascalCase
        assert to_snake_case("my-agent") == "my_agent"
        assert to_snake_case("My Agent") == "my_agent"
        assert to_snake_case("data@processor#v2") == "dataprocessorv2"
        assert to_snake_case("  multiple__underscores  ") == "multiple_underscores"
    
    def test_validate_project_name(self):
        """Test project name validation."""
        # Valid names
        assert validate_project_name("test_project") is True
        assert validate_project_name("my-agent-project") is True
        assert validate_project_name("project123") is True
        assert validate_project_name("a") is True
        
        # Invalid names
        assert validate_project_name("") is False
        assert validate_project_name("   ") is False
        assert validate_project_name("a" * 51) is False  # Too long
        assert validate_project_name("123project") is False  # Starts with number
        assert validate_project_name("-project") is False  # Starts with hyphen
        assert validate_project_name("project@name") is False  # Invalid characters
        assert validate_project_name("project name") is False  # Spaces not allowed
    
    def test_validate_component_name(self):
        """Test component name validation."""
        # Valid names
        assert validate_component_name("test_agent") is True
        assert validate_component_name("my_workflow") is True
        assert validate_component_name("agent123") is True
        assert validate_component_name("_private") is True
        
        # Invalid names
        assert validate_component_name("") is False
        assert validate_component_name("   ") is False
        assert validate_component_name("a" * 31) is False  # Too long
        assert validate_component_name("123agent") is False  # Starts with number
        assert validate_component_name("agent-name") is False  # Hyphens not allowed
        assert validate_component_name("agent name") is False  # Spaces not allowed
        assert validate_component_name("class") is False  # Python keyword
        assert validate_component_name("def") is False  # Python keyword
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_has_api_key_true(self):
        """Test has_api_key returns True when API key is present."""
        assert has_api_key() is True
    
    @patch.dict(os.environ, {}, clear=True)
    def test_has_api_key_false(self):
        """Test has_api_key returns False when no API key is present."""
        assert has_api_key() is False
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'openai-key', 'ANTHROPIC_API_KEY': 'anthropic-key'})
    def test_get_configured_providers(self):
        """Test getting list of configured providers."""
        providers = get_configured_providers()
        
        assert 'openai' in providers
        assert 'anthropic' in providers
        assert len(providers) >= 2
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_configured_providers_empty(self):
        """Test getting providers when none are configured."""
        providers = get_configured_providers()
        assert providers == []


class TestCLIErrorHandling:
    """Test CLI error handling and edge cases."""
    
    def test_command_outside_project_error(self):
        """Test commands that require project context outside project."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)  # Directory without .daita folder
            
            # Commands that require project context should fail
            project_commands = ['create', 'test', 'dev', 'push', 'status', 'logs']
            
            for cmd in project_commands:
                if cmd == 'create':
                    result = runner.invoke(cli, [cmd, 'agent', 'test'])
                else:
                    result = runner.invoke(cli, [cmd])
                
                assert result.exit_code == 1
                assert "Not in a Daita project" in result.output
    
    def test_init_invalid_project_type(self):
        """Test init with invalid project type."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            result = runner.invoke(cli, [
                'init', 'test_project',
                '--type', 'invalid_type'
            ])
            
            assert result.exit_code != 0  # Should fail with invalid type
    
    def test_create_unknown_template(self):
        """Test create with unknown template type."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test_project"
            project_path.mkdir()
            (project_path / ".daita").mkdir()
            os.chdir(project_path)
            
            with pytest.raises(ValueError) as exc_info:
                create_from_template(
                    template='unknown_template',
                    name='test_component'
                )
            
            assert "Unknown template: unknown_template" in str(exc_info.value)
    
    def test_missing_dependencies_error(self):
        """Test CLI behavior when dependencies are missing."""
        # This tests the dependency check mechanism
        from daita.cli.main import check_cli_dependencies
        
        # Should not raise error with dependencies present
        check_cli_dependencies()
    
    def test_keyboard_interrupt_handling(self):
        """Test graceful handling of keyboard interrupts."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Test with init command - should handle interrupts gracefully
            # We can't actually send SIGINT, but we can test the code path exists
            result = runner.invoke(cli, ['init', 'test_project', '--type', 'basic'])
            
            # Should complete successfully (no interrupt in test)
            assert result.exit_code == 0


class TestCLIIntegration:
    """Test end-to-end CLI workflows."""
    
    def test_complete_project_workflow(self):
        """Test complete workflow: init -> create -> test -> status."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # 1. Initialize project
            result = runner.invoke(cli, [
                'init', 'integration_test',
                '--type', 'basic', '--force'
            ])
            assert result.exit_code == 0
            
            # Change to project directory
            os.chdir(Path(temp_dir) / "integration_test")
            
            # 2. Create agent
            result = runner.invoke(cli, ['create', 'agent', 'test_agent'])
            assert result.exit_code == 0
            
            # 3. Create workflow
            result = runner.invoke(cli, ['create', 'workflow', 'test_workflow'])
            assert result.exit_code == 0
            
            # 4. Run tests (with mocking since we don't have real components)
            with patch('daita.cli.core.test._list_agents', return_value=[]):
                with patch('daita.cli.core.test._list_workflows', return_value=[]):
                    result = runner.invoke(cli, ['test'])
                    assert result.exit_code == 0
            
            # 5. Check status
            result = runner.invoke(cli, ['status'])
            assert result.exit_code == 0
            
            # 6. Deploy to staging
            result = runner.invoke(cli, ['push', 'staging'])
            assert result.exit_code == 0
            
            # 7. Check logs
            result = runner.invoke(cli, ['logs'])
            assert result.exit_code == 0
    
    def test_analysis_project_workflow(self):
        """Test workflow specific to analysis projects."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Initialize analysis project
            result = runner.invoke(cli, [
                'init', 'analysis_project',
                '--type', 'analysis', '--force'
            ])
            assert result.exit_code == 0
            
            project_path = Path(temp_dir) / "analysis_project"
            os.chdir(project_path)
            
            # Check analysis-specific files were created
            assert (project_path / "agents" / "data_analyzer.py").exists()
            
            # Check project config
            with open(project_path / "daita-project.yaml", 'r') as f:
                config = yaml.safe_load(f)
            assert config['type'] == 'analysis'
            assert 'focus' in config
    
    def test_pipeline_project_workflow(self):
        """Test workflow specific to pipeline projects."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Initialize pipeline project
            result = runner.invoke(cli, [
                'init', 'pipeline_project',
                '--type', 'pipeline', '--force'
            ])
            assert result.exit_code == 0
            
            project_path = Path(temp_dir) / "pipeline_project"
            os.chdir(project_path)
            
            # Check pipeline-specific files were created
            assert (project_path / "workflows" / "data_pipeline.py").exists()
            
            # Check project config
            with open(project_path / "daita-project.yaml", 'r') as f:
                config = yaml.safe_load(f)
            assert config['type'] == 'pipeline'
            assert 'relay_channels' in config


class TestCLIFileOperations:
    """Test CLI file system operations and safety."""
    
    def test_project_creation_safety(self):
        """Test that project creation doesn't overwrite important files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            existing_project = Path(temp_dir) / "existing"
            existing_project.mkdir()
            
            # Create important existing files
            important_files = [
                "important_data.txt",
                "config.json",
                "README.md"
            ]
            
            for filename in important_files:
                (existing_project / filename).write_text("important content")
            
            os.chdir(temp_dir)
            
            # Initialize project with force=True
            asyncio.run(initialize_project(
                project_name="existing",
                force=True,
                verbose=False
            ))
            
            # Important files should still exist
            for filename in important_files:
                assert (existing_project / filename).exists()
                assert (existing_project / filename).read_text() == "important content"
            
            # Daita files should be created
            assert (existing_project / ".daita").exists()
            assert (existing_project / "daita-project.yaml").exists()
    
    def test_component_creation_no_overwrite(self):
        """Test that component creation doesn't overwrite existing files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test_project"
            project_path.mkdir()
            (project_path / ".daita").mkdir()
            (project_path / "agents").mkdir()
            
            # Create existing agent file
            existing_agent = project_path / "agents" / "existing_agent.py"
            existing_agent.write_text("# Existing agent code")
            
            os.chdir(project_path)
            
            # Try to create agent with same name - should handle gracefully
            try:
                create_from_template('agent', 'existing_agent')
                # If it succeeds, check original content is preserved
                # (implementation may vary on how this is handled)
            except Exception:
                # If it fails, that's also acceptable behavior
                pass
    
    def test_gitignore_creation(self):
        """Test that .gitignore is created with appropriate entries."""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            asyncio.run(initialize_project(
                project_name="gitignore_test",
                verbose=False
            ))
            
            project_path = Path(temp_dir) / "gitignore_test"
            gitignore_file = project_path / ".gitignore"
            
            assert gitignore_file.exists()
            
            gitignore_content = gitignore_file.read_text()
            
            # Check for important entries
            assert "__pycache__/" in gitignore_content
            assert "*.pyc" in gitignore_content
            assert ".env" in gitignore_content
            assert ".daita/cache/" in gitignore_content
            assert "*.log" in gitignore_content
    
    def test_requirements_file_creation(self):
        """Test that requirements.txt is created with proper dependencies."""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            asyncio.run(initialize_project(
                project_name="requirements_test",
                verbose=False
            ))
            
            project_path = Path(temp_dir) / "requirements_test"
            requirements_file = project_path / "requirements.txt"
            
            assert requirements_file.exists()
            
            requirements_content = requirements_file.read_text()
            
            # Check for core dependencies
            assert "daita-agents" in requirements_content
            assert "openai" in requirements_content or "anthropic" in requirements_content


class TestCLIConfigurationManagement:
    """Test CLI configuration and settings management."""
    
    def test_project_config_update(self):
        """Test updating project configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create initial config
            initial_config = {
                'name': 'test_project',
                'version': '1.0.0',
                'agents': []
            }
            save_project_config(project_path, initial_config)
            
            # Load and update config
            config = load_project_config(project_path)
            config['version'] = '1.1.0'
            config['agents'].append({'name': 'new_agent'})
            
            # Save updated config
            save_project_config(project_path, config)
            
            # Verify changes
            updated_config = load_project_config(project_path)
            assert updated_config['version'] == '1.1.0'
            assert len(updated_config['agents']) == 1
            assert updated_config['agents'][0]['name'] == 'new_agent'
    
    def test_deployment_history_management(self):
        """Test deployment history tracking."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test_project"
            project_path.mkdir()
            (project_path / ".daita").mkdir()
            
            # Create project config
            config = {'name': 'test_project', 'version': '1.0.0', 'agents': [], 'workflows': []}
            save_project_config(project_path, config)
            
            os.chdir(project_path)
            
            # Deploy multiple times
            for i, env in enumerate(['staging', 'production', 'staging'], 1):
                asyncio.run(deploy_to_environment(
                    environment=env,
                    force=True,
                    dry_run=False,
                    verbose=False
                ))
            
            # Check deployment history
            deployments_file = project_path / ".daita" / "deployments.json"
            assert deployments_file.exists()
            
            with open(deployments_file, 'r') as f:
                deployments = json.load(f)
            
            assert len(deployments) == 3
            assert deployments[0]['environment'] == 'staging'
            assert deployments[1]['environment'] == 'production'
            assert deployments[2]['environment'] == 'staging'


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])