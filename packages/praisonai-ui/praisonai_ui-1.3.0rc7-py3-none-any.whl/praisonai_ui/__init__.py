"""
PraisonAI UI - Modern AI Agent Chat Interface

This module re-exports all chainlit functionality under the praisonai_ui namespace.
Upstream Chainlit updates are automatically available through this module.

Usage:
    import praisonai_ui as ui

    @ui.on_message
    async def main(message: ui.Message):
        await ui.Message(content="Hello!").send()
"""

# Re-export everything from chainlit
from chainlit import *
from chainlit import __version__

# Also expose chainlit module for advanced usage
import chainlit
