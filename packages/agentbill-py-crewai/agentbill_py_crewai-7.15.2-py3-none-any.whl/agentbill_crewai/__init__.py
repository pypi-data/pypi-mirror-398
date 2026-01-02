"""AgentBill CrewAI Integration

Zero-config crew tracking for CrewAI agents in AgentBill.
"""

from .tracker import track_crew
from .orders import OrdersResource

__version__ = "7.15.2"
__all__ = ["track_crew", "OrdersResource"]
