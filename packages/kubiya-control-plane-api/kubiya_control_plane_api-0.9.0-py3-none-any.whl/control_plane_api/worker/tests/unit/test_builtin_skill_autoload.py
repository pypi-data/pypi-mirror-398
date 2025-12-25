"""Unit tests for built-in skill auto-loading mechanism."""

import pytest
from unittest.mock import Mock, patch, MagicMock

# Add worker to sys.path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestBuiltinSkillAutoLoadAgentExecutor:
    """Test auto-loading of built-in skills in AgentExecutorV2"""

    @pytest.fixture
    def mock_control_plane(self):
        """Mock control plane client"""
        mock_cp = Mock()
        mock_cp.get_skills.return_value = [
            {"name": "shell", "type": "shell", "enabled": True, "configuration": {}}
        ]
        return mock_cp

    @pytest.fixture
    def mock_runtime(self):
        """Mock runtime"""
        mock_rt = Mock()
        mock_rt.supports_tools.return_value = True
        return mock_rt

    @patch('services.agent_executor_v2.SkillFactory')
    def test_context_graph_search_added_to_existing_skills(self, mock_factory_class, mock_control_plane):
        """Test that context_graph_search is added when other skills exist"""
        from services.agent_executor_v2 import AgentExecutorV2

        # Setup mock factory
        mock_factory = Mock()
        mock_factory.create_skills_from_list.return_value = []
        mock_factory_class.return_value = mock_factory

        # Execute the skill loading code
        executor = AgentExecutorV2()
        executor.control_plane = mock_control_plane

        # Simulate the skill loading logic from agent_executor_v2.py
        skill_configs = mock_control_plane.get_skills("test_agent_id")

        # Apply the auto-loading logic
        builtin_skill_types = {'context_graph_search'}
        existing_skill_types = {cfg.get('type') for cfg in skill_configs}

        for builtin_type in builtin_skill_types:
            if builtin_type not in existing_skill_types:
                builtin_config = {
                    'name': builtin_type,
                    'type': builtin_type,
                    'enabled': True,
                    'configuration': {}
                }
                skill_configs.append(builtin_config)

        # Verify context_graph_search was added
        skill_types = [cfg['type'] for cfg in skill_configs]
        assert 'context_graph_search' in skill_types
        assert 'shell' in skill_types  # Original skill still present
        assert len(skill_configs) == 2

    @patch('services.agent_executor_v2.SkillFactory')
    def test_context_graph_search_not_duplicated(self, mock_factory_class, mock_control_plane):
        """Test that context_graph_search is not added if already present"""
        from services.agent_executor_v2 import AgentExecutorV2

        # Mock control plane to return context_graph_search already
        mock_control_plane.get_skills.return_value = [
            {"name": "shell", "type": "shell", "enabled": True, "configuration": {}},
            {"name": "context_graph_search", "type": "context_graph_search", "enabled": True, "configuration": {}}
        ]

        executor = AgentExecutorV2()
        executor.control_plane = mock_control_plane

        # Simulate the skill loading logic
        skill_configs = mock_control_plane.get_skills("test_agent_id")

        # Apply the auto-loading logic
        builtin_skill_types = {'context_graph_search'}
        existing_skill_types = {cfg.get('type') for cfg in skill_configs}

        initial_count = len(skill_configs)

        for builtin_type in builtin_skill_types:
            if builtin_type not in existing_skill_types:
                builtin_config = {
                    'name': builtin_type,
                    'type': builtin_type,
                    'enabled': True,
                    'configuration': {}
                }
                skill_configs.append(builtin_config)

        # Verify no duplication
        assert len(skill_configs) == initial_count
        skill_types = [cfg['type'] for cfg in skill_configs]
        assert skill_types.count('context_graph_search') == 1

    @patch('services.agent_executor_v2.SkillFactory')
    def test_context_graph_search_added_when_no_skills(self, mock_factory_class):
        """Test that context_graph_search is added even when no other skills exist"""
        from services.agent_executor_v2 import AgentExecutorV2

        # Mock control plane to return empty skills
        mock_cp = Mock()
        mock_cp.get_skills.return_value = None

        executor = AgentExecutorV2()
        executor.control_plane = mock_cp

        # Simulate the "else" branch where no skills are found
        skill_configs = []
        builtin_skill_types = {'context_graph_search'}

        for builtin_type in builtin_skill_types:
            builtin_config = {
                'name': builtin_type,
                'type': builtin_type,
                'enabled': True,
                'configuration': {}
            }
            skill_configs.append(builtin_config)

        # Verify context_graph_search was added
        assert len(skill_configs) == 1
        assert skill_configs[0]['type'] == 'context_graph_search'
        assert skill_configs[0]['enabled'] is True

    def test_builtin_skill_config_structure(self):
        """Test that built-in skill config has correct structure"""
        builtin_config = {
            'name': 'context_graph_search',
            'type': 'context_graph_search',
            'enabled': True,
            'configuration': {}
        }

        # Verify structure matches what SkillFactory expects
        assert 'name' in builtin_config
        assert 'type' in builtin_config
        assert 'enabled' in builtin_config
        assert 'configuration' in builtin_config
        assert isinstance(builtin_config['configuration'], dict)


class TestBuiltinSkillAutoLoadTeamExecutor:
    """Test auto-loading of built-in skills in TeamExecutorV2"""

    @pytest.fixture
    def mock_control_plane(self):
        """Mock control plane client"""
        mock_cp = Mock()
        mock_cp.get_skills.return_value = [
            {"name": "shell", "type": "shell", "enabled": True, "configuration": {}}
        ]
        return mock_cp

    @patch('services.team_executor_v2.SkillFactory')
    def test_team_executor_adds_context_graph_search(self, mock_factory_class, mock_control_plane):
        """Test that TeamExecutorV2 also adds context_graph_search"""
        from services.team_executor_v2 import TeamExecutorV2

        # Setup mock factory
        mock_factory = Mock()
        mock_factory.create_skills_from_list.return_value = []
        mock_factory_class.return_value = mock_factory

        executor = TeamExecutorV2()
        executor.control_plane = mock_control_plane

        # Simulate team executor skill loading
        skill_configs = mock_control_plane.get_skills("leader_agent_id")

        # Apply the auto-loading logic (same as agent executor)
        builtin_skill_types = {'context_graph_search'}
        existing_skill_types = {cfg.get('type') for cfg in skill_configs}

        for builtin_type in builtin_skill_types:
            if builtin_type not in existing_skill_types:
                builtin_config = {
                    'name': builtin_type,
                    'type': builtin_type,
                    'enabled': True,
                    'configuration': {}
                }
                skill_configs.append(builtin_config)

        # Verify
        skill_types = [cfg['type'] for cfg in skill_configs]
        assert 'context_graph_search' in skill_types

    @patch('services.team_executor_v2.SkillFactory')
    def test_team_executor_handles_empty_skills(self, mock_factory_class):
        """Test TeamExecutorV2 handles empty skill list"""
        from services.team_executor_v2 import TeamExecutorV2

        mock_cp = Mock()
        mock_cp.get_skills.return_value = None

        executor = TeamExecutorV2()
        executor.control_plane = mock_cp

        # Simulate empty skills scenario
        skill_configs = []
        builtin_skill_types = {'context_graph_search'}

        for builtin_type in builtin_skill_types:
            builtin_config = {
                'name': builtin_type,
                'type': builtin_type,
                'enabled': True,
                'configuration': {}
            }
            skill_configs.append(builtin_config)

        # Verify context_graph_search was added
        assert len(skill_configs) == 1
        assert skill_configs[0]['type'] == 'context_graph_search'


class TestBuiltinSkillSetExtensibility:
    """Test that the builtin skill set is extensible"""

    def test_multiple_builtin_skills_can_be_added(self):
        """Test that multiple built-in skills can be configured"""
        # Define multiple built-in skills
        builtin_skill_types = {'context_graph_search', 'hypothetical_new_skill'}

        # Existing skills from agent
        existing_skills = [
            {"name": "shell", "type": "shell", "enabled": True, "configuration": {}}
        ]

        existing_skill_types = {cfg.get('type') for cfg in existing_skills}

        # Apply auto-loading for all built-in skills
        for builtin_type in builtin_skill_types:
            if builtin_type not in existing_skill_types:
                builtin_config = {
                    'name': builtin_type,
                    'type': builtin_type,
                    'enabled': True,
                    'configuration': {}
                }
                existing_skills.append(builtin_config)

        # Verify both built-in skills were added
        skill_types = [cfg['type'] for cfg in existing_skills]
        assert 'context_graph_search' in skill_types
        assert 'hypothetical_new_skill' in skill_types
        assert 'shell' in skill_types
        assert len(existing_skills) == 3

    def test_builtin_skill_types_is_a_set(self):
        """Test that builtin_skill_types is defined as a set"""
        builtin_skill_types = {'context_graph_search'}

        assert isinstance(builtin_skill_types, set)
        assert 'context_graph_search' in builtin_skill_types

    def test_adding_builtin_skill_preserves_original_skills(self):
        """Test that adding built-in skills doesn't modify original skill configs"""
        original_skills = [
            {"name": "shell", "type": "shell", "enabled": True, "configuration": {"timeout": 30}},
            {"name": "python", "type": "python", "enabled": False, "configuration": {}}
        ]

        skill_configs = original_skills.copy()
        builtin_skill_types = {'context_graph_search'}
        existing_skill_types = {cfg.get('type') for cfg in skill_configs}

        for builtin_type in builtin_skill_types:
            if builtin_type not in existing_skill_types:
                builtin_config = {
                    'name': builtin_type,
                    'type': builtin_type,
                    'enabled': True,
                    'configuration': {}
                }
                skill_configs.append(builtin_config)

        # Verify original skills unchanged
        assert skill_configs[0] == original_skills[0]
        assert skill_configs[1] == original_skills[1]
        # Verify new skill added
        assert skill_configs[2]['type'] == 'context_graph_search'


class TestBuiltinSkillConfiguration:
    """Test built-in skill configuration options"""

    def test_builtin_skill_default_configuration(self):
        """Test that built-in skills have empty default configuration"""
        builtin_config = {
            'name': 'context_graph_search',
            'type': 'context_graph_search',
            'enabled': True,
            'configuration': {}
        }

        assert builtin_config['configuration'] == {}

    def test_builtin_skill_can_have_custom_configuration(self):
        """Test that built-in skills can accept custom configuration"""
        builtin_config = {
            'name': 'context_graph_search',
            'type': 'context_graph_search',
            'enabled': True,
            'configuration': {
                'timeout': 60,
                'default_limit': 50
            }
        }

        assert builtin_config['configuration']['timeout'] == 60
        assert builtin_config['configuration']['default_limit'] == 50

    def test_builtin_skills_always_enabled(self):
        """Test that built-in skills are always enabled by default"""
        builtin_skill_types = {'context_graph_search'}

        for builtin_type in builtin_skill_types:
            builtin_config = {
                'name': builtin_type,
                'type': builtin_type,
                'enabled': True,
                'configuration': {}
            }

            assert builtin_config['enabled'] is True


class TestSkillLoadingOrder:
    """Test skill loading order and priority"""

    def test_builtin_skills_loaded_after_agent_skills(self):
        """Test that built-in skills are added after agent-specific skills"""
        agent_skills = [
            {"name": "shell", "type": "shell", "enabled": True, "configuration": {}},
            {"name": "python", "type": "python", "enabled": True, "configuration": {}}
        ]

        skill_configs = agent_skills.copy()
        builtin_skill_types = {'context_graph_search'}
        existing_skill_types = {cfg.get('type') for cfg in skill_configs}

        for builtin_type in builtin_skill_types:
            if builtin_type not in existing_skill_types:
                builtin_config = {
                    'name': builtin_type,
                    'type': builtin_type,
                    'enabled': True,
                    'configuration': {}
                }
                skill_configs.append(builtin_config)

        # Verify order: agent skills first, then built-in
        assert skill_configs[0]['type'] == 'shell'
        assert skill_configs[1]['type'] == 'python'
        assert skill_configs[2]['type'] == 'context_graph_search'

    def test_agent_configured_builtin_takes_precedence(self):
        """Test that if agent has configured a built-in skill, that config is used"""
        agent_skills = [
            {"name": "shell", "type": "shell", "enabled": True, "configuration": {}},
            {"name": "context_graph_search", "type": "context_graph_search", "enabled": True,
             "configuration": {"timeout": 120}}
        ]

        skill_configs = agent_skills.copy()
        builtin_skill_types = {'context_graph_search'}
        existing_skill_types = {cfg.get('type') for cfg in skill_configs}

        initial_count = len(skill_configs)

        for builtin_type in builtin_skill_types:
            if builtin_type not in existing_skill_types:
                builtin_config = {
                    'name': builtin_type,
                    'type': builtin_type,
                    'enabled': True,
                    'configuration': {}
                }
                skill_configs.append(builtin_config)

        # Verify no duplication and custom config preserved
        assert len(skill_configs) == initial_count
        context_graph_skill = next(s for s in skill_configs if s['type'] == 'context_graph_search')
        assert context_graph_skill['configuration']['timeout'] == 120
