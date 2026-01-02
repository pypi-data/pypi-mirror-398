"""Basic CrewAI + AgentBill example"""

from agentbill_crewai import track_crew
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
import os

# Initialize LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

# Create agents
researcher = Agent(
    role="Research Analyst",
    goal="Find and analyze information about {topic}",
    backstory="You are an expert researcher with 10 years of experience in data analysis.",
    llm=llm,
    verbose=True
)

writer = Agent(
    role="Content Writer",
    goal="Write engaging content based on research",
    backstory="You are a creative writer skilled at transforming complex information into readable content.",
    llm=llm,
    verbose=True
)

# Create tasks
research_task = Task(
    description="Research the following topic thoroughly: {topic}",
    agent=researcher,
    expected_output="A comprehensive research report with key findings"
)

writing_task = Task(
    description="Write a blog post based on the research findings",
    agent=writer,
    expected_output="A well-structured 500-word blog post"
)

# Create crew
research_crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, writing_task],
    verbose=True
)

# Execute with AgentBill tracking
print("Starting crew execution with AgentBill tracking...")
print("=" * 60)

result = track_crew(
    crew=research_crew,
    inputs={"topic": "The impact of AI on software development"},
    agentbill_config={
        "api_key": "agb_your_api_key_here",  # Replace with your actual API key
        "base_url": "https://bgwyprqxtdreuutzpbgw.supabase.co",
        "customer_id": "customer-demo-123",
        "debug": True  # See what's being tracked
    },
    revenue=5.00,  # Track what you charged for this crew execution
    revenue_metadata={
        "client": "Demo Client",
        "project": "blog_generation",
        "subscription": "pro"
    }
)

print("\n" + "=" * 60)
print("Crew Result:")
print(result)

print("\n✅ Complete! Check your AgentBill dashboard for:")
print("  - Token usage per agent (researcher, writer)")
print("  - Model costs (auto-calculated)")
print("  - Task execution times")
print("  - Total crew cost")
print("  - Revenue ($5.00)")
print("  - Net margin (revenue - cost)")
print("  - Agent-level profitability")
