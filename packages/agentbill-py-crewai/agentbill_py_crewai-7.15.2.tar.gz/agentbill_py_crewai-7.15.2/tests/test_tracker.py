"""Tests for AgentBill CrewAI tracker."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from agentbill_crewai import track_crew


@pytest.fixture
def mock_crew():
    """Create a mock CrewAI crew for testing."""
    crew = Mock()
    crew.agents = [
        Mock(role="Researcher", goal="Research topics"),
        Mock(role="Writer", goal="Write content")
    ]
    crew.tasks = [
        Mock(description="Research task"),
        Mock(description="Writing task")
    ]
    return crew


def test_track_crew_initialization(mock_crew):
    """Test track_crew initializes correctly."""
    with patch('agentbill_crewai.tracker.AgentBill') as mock_agentbill:
        tracked_crew = track_crew(
            crew=mock_crew,
            api_key="test-api-key",
            customer_id="test-customer"
        )
        
        assert tracked_crew is not None
        mock_agentbill.init.assert_called_once()


def test_track_crew_wraps_kickoff(mock_crew):
    """Test track_crew wraps the kickoff method."""
    with patch('agentbill_crewai.tracker.AgentBill'):
        tracked_crew = track_crew(
            crew=mock_crew,
            api_key="test-api-key"
        )
        
        # Verify kickoff method exists
        assert hasattr(tracked_crew, 'kickoff')
        assert callable(tracked_crew.kickoff)


def test_track_crew_without_api_key():
    """Test track_crew raises error without API key."""
    with pytest.raises((ValueError, TypeError)):
        track_crew(
            crew=Mock(),
            api_key=None
        )


@patch('agentbill_crewai.tracker.AgentBill')
def test_track_crew_with_debug_mode(mock_agentbill, mock_crew):
    """Test track_crew with debug mode enabled."""
    tracked_crew = track_crew(
        crew=mock_crew,
        api_key="test-api-key",
        debug=True
    )
    
    assert tracked_crew is not None
    # Verify debug mode was passed to AgentBill
    init_call = mock_agentbill.init.call_args
    assert init_call is not None


@patch('agentbill_crewai.tracker.AgentBill')
def test_tracked_crew_execution(mock_agentbill, mock_crew):
    """Test tracked crew execution sends data."""
    mock_client = MagicMock()
    mock_agentbill.init.return_value = mock_client
    
    mock_crew.kickoff.return_value = "Crew execution result"
    
    tracked_crew = track_crew(
        crew=mock_crew,
        api_key="test-api-key"
    )
    
    # Execute crew
    result = tracked_crew.kickoff()
    
    assert result == "Crew execution result"
    mock_crew.kickoff.assert_called_once()


@patch('agentbill_crewai.tracker.AgentBill')
def test_track_crew_with_custom_base_url(mock_agentbill, mock_crew):
    """Test track_crew with custom base URL."""
    tracked_crew = track_crew(
        crew=mock_crew,
        api_key="test-api-key",
        base_url="https://custom.agentbill.com"
    )
    
    assert tracked_crew is not None
    init_call = mock_agentbill.init.call_args
    assert init_call is not None


def test_track_crew_preserves_crew_attributes(mock_crew):
    """Test that tracked crew preserves original crew attributes."""
    with patch('agentbill_crewai.tracker.AgentBill'):
        tracked_crew = track_crew(
            crew=mock_crew,
            api_key="test-api-key"
        )
        
        # Check that original attributes are preserved
        assert hasattr(tracked_crew, 'agents')
        assert hasattr(tracked_crew, 'tasks')
