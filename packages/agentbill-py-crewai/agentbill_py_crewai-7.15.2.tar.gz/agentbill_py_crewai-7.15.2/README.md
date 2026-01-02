# AgentBill CrewAI Integration

OpenTelemetry-based crew tracker for automatically tracking and billing CrewAI agent usage.

## Installation

```bash
pip install agentbill-crewai
```

This will automatically install the required dependencies:
- `crewai`
- `agentbill-langchain` (CrewAI uses LangChain callbacks under the hood)

## Quick Start

```python
from agentbill_crewai import track_crew
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI

# 1. Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini")

# 2. Create agents
researcher = Agent(
    role="Research Analyst",
    goal="Find and analyze data",
    backstory="Expert researcher with attention to detail",
    llm=llm
)

writer = Agent(
    role="Content Writer",
    goal="Write engaging content",
    backstory="Creative writer with storytelling skills",
    llm=llm
)

# 3. Create tasks
research_task = Task(
    description="Research the topic: {topic}",
    agent=researcher,
    expected_output="Comprehensive research findings"
)

writing_task = Task(
    description="Write an article based on the research",
    agent=writer,
    expected_output="Well-written article"
)

# 4. Create crew
crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, writing_task]
)

# 5. Run with AgentBill tracking!
result = track_crew(
    crew=crew,
    inputs={"topic": "AI in healthcare"},
    agentbill_config={
        "api_key": "agb_your_api_key_here",
        "base_url": "https://bgwyprqxtdreuutzpbgw.supabase.co",
        "customer_id": "customer-123",
        "debug": True
    }
)

print(result)

# ✅ Automatically captured:
# - All agent LLM calls
# - Token usage per agent
# - Task execution times
# - Total crew cost
# - Agent-level profitability
```

## Features

- ✅ **Zero-config instrumentation** - Just wrap with `track_crew()`
- ✅ **Agent-level tracking** - Track each agent's LLM usage
- ✅ **Task-level metrics** - Measure task execution time
- ✅ **Multi-agent support** - Track complex multi-agent workflows
- ✅ **Cost calculation** - Auto-calculates costs per agent
- ✅ **Crew profitability** - Compare crew costs vs revenue
- ✅ **OpenTelemetry compatible** - Standard observability

## Advanced Usage

### Track Revenue Per Crew

```python
result = track_crew(
    crew=crew,
    inputs={"topic": "AI trends"},
    agentbill_config={
        "api_key": "agb_...",
        "base_url": "https://...",
        "customer_id": "customer-123"
    },
    revenue=5.00,  # What you charged for this crew execution
    revenue_metadata={
        "subscription": "enterprise",
        "feature": "research_crew"
    }
)
```

### Use with Custom LLMs

```python
from langchain_anthropic import ChatAnthropic

# Works with any LangChain-compatible LLM
anthropic_llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")

agent = Agent(
    role="Analyst",
    goal="Analyze data",
    backstory="Expert analyst",
    llm=anthropic_llm  # CrewAI auto-tracks this!
)
```

### Sequential vs Parallel Crews

```python
# Sequential crew (default)
sequential_crew = Crew(
    agents=[agent1, agent2],
    tasks=[task1, task2],
    process=Process.sequential  # Tasks run one after another
)

# Parallel crew
from crewai import Process

parallel_crew = Crew(
    agents=[agent1, agent2],
    tasks=[task1, task2],
    process=Process.parallel  # Tasks run concurrently
)

# Both tracked automatically!
track_crew(sequential_crew, {...})
track_crew(parallel_crew, {...})
```

### Hierarchical Crews

```python
# Manager agent delegates to worker agents
manager = Agent(
    role="Project Manager",
    goal="Coordinate the team",
    backstory="Experienced manager",
    llm=llm
)

crew = Crew(
    agents=[manager, worker1, worker2],
    tasks=[task1, task2],
    process=Process.hierarchical,  # Manager delegates
    manager_llm=llm
)

# All agent interactions tracked!
result = track_crew(crew, inputs={...}, agentbill_config={...})
```

## Configuration

```python
agentbill_config = {
    "api_key": "agb_...",           # Required - get from dashboard
    "base_url": "https://...",      # Required - your AgentBill instance
    "customer_id": "customer-123",  # Optional - for multi-tenant apps
    "account_id": "account-456",    # Optional - for account-level tracking
    "debug": True,                  # Optional - enable debug logging
    "batch_size": 10,               # Optional - batch signals before sending
    "flush_interval": 5.0           # Optional - flush interval in seconds
}
```

## How It Works

The crew tracker wraps CrewAI execution:

1. **Inject Callback** - Adds AgentBill callback to all agents' LLMs
2. **Track Agents** - Monitors each agent's LLM calls
3. **Track Tasks** - Measures task execution time
4. **Calculate Costs** - Sums up all agent costs
5. **Send Signals** - Sends data to AgentBill via `record-signals` API

All agent interactions are automatically captured without code changes.

## Real-World Example: Research Crew

```python
from agentbill_crewai import track_crew
from crewai import Agent, Task, Crew
from crewai_tools import SerperDevTool
from langchain_openai import ChatOpenAI

# Tools
search_tool = SerperDevTool()
llm = ChatOpenAI(model="gpt-4o-mini")

# Agents
researcher = Agent(
    role="Senior Research Analyst",
    goal="Discover cutting-edge developments in {topic}",
    backstory="Veteran researcher with 10+ years experience",
    tools=[search_tool],
    llm=llm
)

analyst = Agent(
    role="Data Analyst",
    goal="Analyze research findings and extract insights",
    backstory="Expert at data analysis and pattern recognition",
    llm=llm
)

writer = Agent(
    role="Content Writer",
    goal="Create compelling content from insights",
    backstory="Award-winning writer with storytelling expertise",
    llm=llm
)

# Tasks
research_task = Task(
    description="Research {topic} and compile findings",
    agent=researcher,
    expected_output="Comprehensive research report"
)

analysis_task = Task(
    description="Analyze research and identify key insights",
    agent=analyst,
    expected_output="Detailed analysis with insights"
)

writing_task = Task(
    description="Write engaging article from analysis",
    agent=writer,
    expected_output="Publication-ready article"
)

# Crew
research_crew = Crew(
    agents=[researcher, analyst, writer],
    tasks=[research_task, analysis_task, writing_task],
    verbose=True
)

# Execute with tracking
result = track_crew(
    crew=research_crew,
    inputs={"topic": "Quantum Computing in Drug Discovery"},
    agentbill_config={
        "api_key": "agb_your_key",
        "base_url": "https://xxx.supabase.co",
        "customer_id": "pharma-corp-123"
    },
    revenue=50.00,  # What you charged for this research
    revenue_metadata={
        "client": "PharmaCorp",
        "project": "drug_discovery_research"
    }
)

print("Article:", result)

# ✅ Dashboard shows:
# - Cost per agent (researcher, analyst, writer)
# - Total crew cost
# - Revenue ($50)
# - Net margin (revenue - cost)
# - Agent efficiency metrics
```

## Troubleshooting

### Not seeing agent data?

1. Ensure CrewAI agents have LLMs assigned
2. Check API key is correct
3. Enable `debug: True` to see logs
4. Verify crew is actually running (not just created)

### Missing token counts?

- Some LLMs don't return usage data
- OpenAI and Anthropic provide accurate counts
- Local models may need manual instrumentation

### Multiple crews running?

Each `track_crew()` call is independent - perfect for parallel crew execution!

## License

MIT
