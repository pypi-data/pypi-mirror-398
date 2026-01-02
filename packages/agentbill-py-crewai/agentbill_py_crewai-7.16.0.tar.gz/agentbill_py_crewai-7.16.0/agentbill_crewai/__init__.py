"""AgentBill CrewAI Integration

Zero-config crew tracking for CrewAI agents in AgentBill.
v7.16.0: Added OpenAI native prompt prefix cache tracking (cached_input_tokens)
"""

from .tracker import track_crew
from .orders import OrdersResource

__version__ = "7.16.0"
__all__ = ["track_crew", "OrdersResource"]
