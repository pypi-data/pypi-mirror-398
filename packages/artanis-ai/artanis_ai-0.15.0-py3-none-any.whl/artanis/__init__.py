"""
Artanis SDK for AI Application Observability.

Artanis helps you understand failures, build evaluation sets, and act on
user feedback through comprehensive tracing and state management.

Example:
    from artanis import Artanis

    # Initialize client
    artanis = Artanis(api_key="sk_...")

    # Create a trace
    trace = artanis.trace("answer-question")
    trace.input(question="What is AI?", model="gpt-4")
    trace.output("AI stands for Artificial Intelligence")

    # Record feedback
    artanis.feedback(trace.id, rating="positive")
"""

from artanis.client import Artanis
from artanis.trace import Trace

__version__ = "0.1.0"
__all__ = ["Artanis", "Trace"]
