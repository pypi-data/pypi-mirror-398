"""AgentBill CrewAI Tracker"""

import time
from typing import Any, Dict, Optional

try:
    from crewai import Crew
except ImportError:
    raise ImportError(
        "crewai is not installed. Install with: pip install crewai"
    )

# Import AgentBill LangChain callback (CrewAI uses LangChain under the hood)
try:
    from agentbill_langchain import AgentBillCallback
except ImportError:
    raise ImportError(
        "agentbill-langchain is required. Install with: pip install agentbill-langchain"
    )


def track_crew(
    crew: Crew,
    inputs: Dict[str, Any],
    agentbill_config: Dict[str, Any],
    revenue: Optional[float] = None,
    revenue_metadata: Optional[Dict[str, Any]] = None
) -> Any:
    """Execute a CrewAI crew with AgentBill tracking.
    
    This function wraps crew execution and automatically tracks:
    - All agent LLM calls
    - Token usage per agent
    - Task execution times
    - Total crew cost
    
    Args:
        crew: CrewAI Crew instance to track
        inputs: Input dict for crew.kickoff()
        agentbill_config: AgentBill configuration dict:
            - api_key: AgentBill API key (required)
            - base_url: AgentBill base URL (required)
            - customer_id: Customer ID (optional)
            - account_id: Account ID (optional)
            - debug: Enable debug logging (optional)
        revenue: Optional revenue amount for profitability tracking
        revenue_metadata: Optional metadata for revenue tracking
    
    Returns:
        Crew execution result
    
    Example:
        result = track_crew(
            crew=my_crew,
            inputs={"topic": "AI trends"},
            agentbill_config={
                "api_key": "agb_...",
                "base_url": "https://...",
                "customer_id": "customer-123"
            },
            revenue=10.00
        )
    """
    # Create AgentBill callback with Cost Guard enabled
    callback = AgentBillCallback(
        api_key=agentbill_config["api_key"],
        base_url=agentbill_config["base_url"],
        customer_id=agentbill_config.get("customer_id"),
        account_id=agentbill_config.get("account_id"),
        agent_id=agentbill_config.get("agent_id"),
        event_name=agentbill_config.get("event_name", "crewai_crew_execution"),
        debug=agentbill_config.get("debug", False),
        batch_size=agentbill_config.get("batch_size", 10),
        flush_interval=agentbill_config.get("flush_interval", 5.0),
        # Enable Cost Guard validation (v6.5.0+)
        daily_budget=agentbill_config.get("daily_budget"),
        monthly_budget=agentbill_config.get("monthly_budget"),
        enable_cost_guard=agentbill_config.get("enable_cost_guard", True)
    )
    
    debug = agentbill_config.get("debug", False)
    
    if debug:
        print(f"[AgentBill] Starting crew tracking")
        print(f"[AgentBill] Crew has {len(crew.agents)} agents and {len(crew.tasks)} tasks")
    
    # Track start time
    start_time = time.time()
    
    # Inject callback into all agents' LLMs
    for agent in crew.agents:
        if hasattr(agent, 'llm') and agent.llm is not None:
            # CrewAI agents use LangChain LLMs under the hood
            # We need to add our callback to the LLM's callbacks list
            if hasattr(agent.llm, 'callbacks'):
                if agent.llm.callbacks is None:
                    agent.llm.callbacks = []
                agent.llm.callbacks.append(callback)
                
                if debug:
                    print(f"[AgentBill] Added callback to agent: {agent.role}")
    
    # Track crew execution
    try:
        # Execute crew with inputs
        result = crew.kickoff(inputs=inputs)
        
        # Calculate total execution time
        execution_time = time.time() - start_time
        
        if debug:
            print(f"[AgentBill] Crew completed in {execution_time:.2f}s")
        
        # Track crew-level metrics with UUID detection
        customer_id_value = agentbill_config.get("customer_id")
        crew_signal = {
            "event_name": agentbill_config.get("event_name", "crewai_crew_execution"),
            "data_source": "crewai",
            "account_id": agentbill_config.get("account_id"),
            "latency_ms": int(execution_time * 1000),
            "data": {
                "agent_count": len(crew.agents),
                "task_count": len(crew.tasks),
                "process": str(crew.process) if hasattr(crew, 'process') else "sequential",
                "crew_name": getattr(crew, 'name', 'unknown'),
            }
        }
        
        # Add customer with UUID detection
        if customer_id_value:
            import re
            uuid_regex = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
            is_uuid = bool(uuid_regex.match(customer_id_value))
            if is_uuid:
                crew_signal["customer_id"] = customer_id_value
            else:
                crew_signal["customer_external_id"] = customer_id_value
        
        callback._queue_signal(crew_signal)
        
        # Track revenue if provided
        if revenue is not None:
            callback.track_revenue(
                event_name="crewai_crew_revenue",
                revenue=revenue,
                metadata={
                    **(revenue_metadata or {}),
                    "agent_count": len(crew.agents),
                    "task_count": len(crew.tasks),
                    "execution_time_s": execution_time
                }
            )
            
            if debug:
                print(f"[AgentBill] Revenue tracked: ${revenue}")
        
        # Flush all queued signals
        callback.flush()
        
        if debug:
            print(f"[AgentBill] Tracking complete")
        
        return result
        
    except Exception as e:
        if debug:
            print(f"[AgentBill] Crew execution error: {e}")
        
        # Try to flush on error
        try:
            callback.flush()
        except:
            pass
        
        raise e
