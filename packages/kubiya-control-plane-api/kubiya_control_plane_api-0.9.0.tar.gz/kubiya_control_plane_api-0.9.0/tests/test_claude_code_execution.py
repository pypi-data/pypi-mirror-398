#!/usr/bin/env python3
"""
Test Claude Code runtime execution end-to-end.
This script creates an agent with claude_code runtime and executes a task.
"""
import requests
import json
import time
import sys

API_BASE = "http://localhost:8000"
TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6Imt1Yml5YS5haSIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6InNoYWtlZEBrdWJpeWEuYWkiLCJleHAiOjE3OTI0MTYwNzAsImlhdCI6MTc2MDk2NjQ3MCwibmJmIjoxNzYwOTY2NDcwLCJvcmdhbml6YXRpb24iOiJrdWJpeWEtYWkiLCJ0b2tlbl9pZCI6IjkwYjk4Zjk5LTRmYzctNDA0Mi1iMmRiLTNjMDJiNTVlNTk2OSIsInRva2VuX25hbWUiOnsidHlwZSI6IiIsIm5hbWUiOiJ3b3JrZXIiLCJkZXNjcmlwdGlvbiI6IkFQSSBrZXkgZm9yIHdvcmtlciBxdWV1ZTogRGVmYXVsdCBRdWV1ZSIsImVtYWlsIjoic2hha2VkQGt1Yml5YS5haSIsInRva2VuX2lkIjoiOTBiOThmOTktNGZjNy00MDQyLWIyZGItM2MwMmI1NWU1OTY5IiwidHRsIjoiMzY0ZCJ9fQ.VNws3BYLtgR5W9rEGdxpgVSgEIsgIcdTGv5rhCLbyeY"
QUEUE_ID = "e1ee3d20-c609-453f-9ee5-4a8138e36cf9"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def list_agents():
    """List all agents and their runtimes"""
    print("=" * 80)
    print("LISTING AGENTS")
    print("=" * 80)

    response = requests.get(f"{API_BASE}/api/v1/agents", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to list agents: {response.status_code}")
        print(response.text)
        return None

    agents = response.json()
    print(f"\nFound {len(agents)} agents:")
    for agent in agents:
        print(f"  • {agent['name']}")
        print(f"    ID: {agent['id']}")
        print(f"    Runtime: {agent.get('runtime', 'default')}")
        print()

    return agents

def create_claude_code_agent():
    """Create a new agent with claude_code runtime"""
    print("=" * 80)
    print("CREATING CLAUDE CODE AGENT")
    print("=" * 80)

    agent_data = {
        "name": "Claude Code Test Agent",
        "description": "Testing Claude Code runtime with streaming",
        "system_prompt": "You are a helpful AI assistant powered by Claude Code SDK.",
        "runtime": "claude_code",
        "configuration": {
            "model": "claude-sonnet-4"
        }
    }

    response = requests.post(
        f"{API_BASE}/api/v1/agents",
        headers=headers,
        json=agent_data
    )

    if response.status_code not in [200, 201]:
        print(f"❌ Failed to create agent: {response.status_code}")
        print(response.text)
        return None

    agent = response.json()
    print(f"✅ Created agent: {agent['name']}")
    print(f"   ID: {agent['id']}")
    print(f"   Runtime: {agent.get('runtime', 'N/A')}")
    print()

    return agent

def execute_agent(agent_id, prompt, stream=False):
    """Execute agent with given prompt"""
    print("=" * 80)
    print(f"EXECUTING AGENT ({'STREAMING' if stream else 'NON-STREAMING'})")
    print("=" * 80)
    print(f"Agent ID: {agent_id}")
    print(f"Prompt: {prompt}")
    print()

    execution_data = {
        "prompt": prompt,
        "worker_queue_id": QUEUE_ID,
        "stream": stream
    }

    response = requests.post(
        f"{API_BASE}/api/v1/agents/{agent_id}/execute",
        headers=headers,
        json=execution_data,
        stream=stream
    )

    if response.status_code != 200:
        print(f"❌ Failed to execute agent: {response.status_code}")
        print(response.text)
        return None

    if stream:
        print("📡 Streaming response:")
        print("-" * 80)
        for line in response.iter_lines():
            if line:
                print(line.decode('utf-8'))
        print("-" * 80)
    else:
        result = response.json()
        print(f"✅ Execution submitted:")
        print(f"   Execution ID: {result.get('execution_id')}")
        print(f"   Workflow ID: {result.get('workflow_id')}")
        print(f"   Status: {result.get('status')}")
        print()
        return result

def list_teams():
    """List all teams"""
    print("=" * 80)
    print("LISTING TEAMS")
    print("=" * 80)

    response = requests.get(f"{API_BASE}/api/v1/teams", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to list teams: {response.status_code}")
        print(response.text)
        return None

    teams = response.json()
    print(f"\nFound {len(teams)} teams:")
    for team in teams:
        print(f"  • {team['name']}")
        print(f"    ID: {team['id']}")
        print(f"    Runtime: {team.get('runtime', 'default')}")
        print()

    return teams

def main():
    print("\n" + "=" * 80)
    print("CLAUDE CODE RUNTIME END-TO-END TEST")
    print("=" * 80)
    print()

    # Step 1: List existing agents
    agents = list_agents()
    if agents is None:
        sys.exit(1)

    # Step 2: Check if we have any claude_code agents
    claude_agents = [a for a in agents if a.get('runtime') == 'claude_code']

    if claude_agents:
        print(f"✅ Found {len(claude_agents)} existing Claude Code agent(s)")
        agent = claude_agents[0]
    else:
        print("⚠️  No Claude Code agents found, creating one...")
        agent = create_claude_code_agent()
        if agent is None:
            sys.exit(1)

    # Step 3: Execute with non-streaming
    print("\n🧪 Test 1: Non-streaming execution")
    result = execute_agent(
        agent['id'],
        "Hello! What is 2+2? Please explain your calculation.",
        stream=False
    )

    if result:
        print("✅ Non-streaming execution submitted successfully\n")

    # Step 4: Execute with streaming
    print("\n🧪 Test 2: Streaming execution")
    execute_agent(
        agent['id'],
        "Count from 1 to 5 and explain each number.",
        stream=True
    )

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  Agent ID: {agent['id']}")
    print(f"  Agent Name: {agent['name']}")
    print(f"  Runtime: {agent.get('runtime', 'N/A')}")
    print()
    print("Check worker logs for execution details:")
    print("  tail -f worker.log")
    print()

if __name__ == "__main__":
    main()
