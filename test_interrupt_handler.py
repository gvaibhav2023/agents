from livekit_plugins.livekit_interrupt_handler import InterruptHandler
import asyncio

# Create the handler instance
handler = InterruptHandler()

print("----- TEST START -----\n")

# Case 1: Agent speaking, user says filler
handler.set_agent_state(True)
asyncio.run(handler.handle_interruption("umm", 0.95))

# Case 2: Agent speaking, user says command
asyncio.run(handler.handle_interruption("stop", 0.95))

# Case 3: Agent quiet, user says filler
handler.set_agent_state(False)
asyncio.run(handler.handle_interruption("umm", 0.95))

# Case 4: Low confidence voice noise
handler.set_agent_state(True)
asyncio.run(handler.handle_interruption("hmm yeah", 0.4))

print("\n----- TEST END -----")
