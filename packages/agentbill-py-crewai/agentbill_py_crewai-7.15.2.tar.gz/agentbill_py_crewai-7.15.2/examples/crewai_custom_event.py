"""
CrewAI with Custom Event Names Example

Shows how to use custom event names per crew execution
"""
import os
from agentbill_crewai import track_crew
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI

# Initialize LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY")
)

# Create research agent
researcher = Agent(
    role="Research Analyst",
    goal="Research and analyze information about {topic}",
    backstory="You are an expert researcher with deep analytical skills",
    llm=llm,
    verbose=True
)

# Create research task
research_task = Task(
    description="Research comprehensive information about {topic}",
    expected_output="A detailed research report",
    agent=researcher
)

# Create crew
research_crew = Crew(
    agents=[researcher],
    tasks=[research_task],
    verbose=True
)

# Example 1: Research event
print("Running research crew with 'research_analysis' event...")
result1 = track_crew(
    crew=research_crew,
    inputs={"topic": "AI Agent Frameworks"},
    agentbill_config={
        "api_key": os.getenv("AGENTBILL_API_KEY", "your-api-key"),
        "base_url": os.getenv("AGENTBILL_BASE_URL", "https://bgwyprqxtdreuutzpbgw.supabase.co"),
        "customer_id": "customer-123",
        "agent_id": "agent-456",
        "event_name": "research_analysis",  # Custom event name
        "debug": True
    },
    revenue=5.00
)

print(f"\nResult: {result1}")

# Example 2: Content generation event (different crew execution)
print("\n" + "="*60)
print("Running research crew with 'content_generation' event...")

result2 = track_crew(
    crew=research_crew,
    inputs={"topic": "Future of AI"},
    agentbill_config={
        "api_key": os.getenv("AGENTBILL_API_KEY", "your-api-key"),
        "base_url": os.getenv("AGENTBILL_BASE_URL", "https://bgwyprqxtdreuutzpbgw.supabase.co"),
        "customer_id": "customer-123",
        "agent_id": "agent-456",
        "event_name": "content_generation",  # Different event name
        "debug": True
    },
    revenue=10.00
)

print(f"\nResult: {result2}")

print("\n✅ Both crew executions tracked with different event names!")
