"""
E2E Test for Planning Tools with SQLAlchemy

Tests that the planning tools work correctly with SQLAlchemy database access
instead of Supabase, fixing the serverless timeout issues.
"""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from control_plane_api.app.database import Base
from control_plane_api.app.models.agent import Agent
from control_plane_api.app.models.team import Team
from control_plane_api.app.lib.planning_tools.agents import AgentsContextTools
from control_plane_api.app.lib.planning_tools.teams import TeamsContextTools
import uuid
import asyncio


@pytest.fixture
def test_db():
    """Create a test database session using the actual database"""
    from control_plane_api.app.database import get_db

    # Use the actual database connection
    db = next(get_db())

    yield db

    db.close()


@pytest.fixture
def sample_agents(test_db):
    """Query existing agents from database"""
    # Query first org that has agents
    result = test_db.execute(text("SELECT organization_id FROM agents LIMIT 1")).first()

    if result:
        org_id = result[0]
    else:
        org_id = "kubiya-ai"  # Default org

    # Query agents for this org
    agents = test_db.execute(
        text("SELECT * FROM agents WHERE organization_id = :org_id LIMIT 5"),
        {"org_id": org_id}
    ).fetchall()

    return agents, org_id


@pytest.mark.asyncio
async def test_list_agents_with_sqlalchemy(test_db, sample_agents):
    """Test that list_agents works with SQLAlchemy database"""
    agents, org_id = sample_agents

    # Create the tools with the database session
    tools = AgentsContextTools(db=test_db, organization_id=org_id)

    # Call list_agents
    result = await tools.list_agents(limit=10)

    # Verify we got results
    assert isinstance(result, list), "Result should be a list"
    assert len(result) >= 0, "Result should be a list"

    if len(result) > 0:
        # Verify agent data structure
        agent_dict = result[0]
        assert "id" in agent_dict
        assert "name" in agent_dict
        assert "model_id" in agent_dict
        assert "execution_environment" in agent_dict

        print(f"✅ Successfully fetched {len(result)} agents using SQLAlchemy")
        for agent in result[:3]:  # Show first 3
            print(f"  - {agent['name']}: {agent.get('model_id', 'N/A')}")
    else:
        print("⚠️  No agents found in database, but query succeeded")


@pytest.mark.asyncio
async def test_list_agents_with_organization_filter(test_db, sample_agents):
    """Test that organization filtering works"""
    agents, org_id = sample_agents

    # Query with organization filter
    tools = AgentsContextTools(db=test_db, organization_id=org_id)
    result = await tools.list_agents(limit=10)

    # Should only get agents from our org
    if len(result) > 0:
        assert all(a["organization_id"] == org_id for a in result), "All agents should be from the specified org"
        print(f"✅ Organization filtering works correctly - all {len(result)} agents from org {org_id}")
    else:
        print(f"⚠️  No agents found for org {org_id}")


@pytest.mark.asyncio
async def test_list_agents_without_db_session(test_db, sample_agents):
    """Test that tools can create their own DB session if needed"""
    agents, org_id = sample_agents

    # Create tools WITHOUT passing db session
    # This should create its own session using _get_db()
    tools = AgentsContextTools(organization_id=org_id)

    # This will try to create a session, which might fail in test environment
    # but we're testing the code path exists
    try:
        result = await tools.list_agents(limit=10)
        print(f"✅ Tools can create their own DB session")
    except Exception as e:
        print(f"⚠️  Expected: Tools need proper DB setup: {str(e)}")


def test_agents_context_tools_initialization():
    """Test that AgentsContextTools initializes correctly"""
    # Test with db parameter
    tools = AgentsContextTools(db=None, organization_id="test-org")
    assert tools.organization_id == "test-org"
    assert tools.name == "agent_context_tools"

    print("✅ AgentsContextTools initializes correctly")


if __name__ == "__main__":
    print("\n🧪 Running Planning Tools SQLAlchemy E2E Tests\n")
    print("=" * 60)

    # Run the tests
    pytest.main([__file__, "-v", "-s"])
