import sys
import os
import logging
from dotenv import load_dotenv

# ============================================================
# 🔧 PATH FIXES (for nested folder setup on your machine)
# ============================================================

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))

# Add LiveKit agent core
sys.path.append(os.path.join(BASE_DIR, "livekit_agents"))

# Add Silero plugin path
sys.path.append(os.path.join(BASE_DIR, "livekit_plugins/livekit-plugins-silero/livekit/plugins"))

# Add Turn Detector plugin path
sys.path.append(os.path.join(BASE_DIR, "livekit_plugins/livekit-plugins-turn-detector/livekit/plugins"))

# ============================================================

from livekit_plugins.livekit_interrupt_handler import InterruptHandler

from livekit_agents.livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    RoomOutputOptions,
    RunContext,
    WorkerOptions,
    cli,
    metrics,
)

from livekit_agents.livekit.agents.llm import function_tool
from silero import VAD
from turn_detector.multilingual import MultilingualModel

# uncomment to enable Krisp background voice/noise cancellation
# from livekit.plugins import noise_cancellation

logger = logging.getLogger("basic-agent")

load_dotenv()


class MyAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "Your name is Kelly. You would interact with users via voice. "
                "Keep your responses concise and to the point. "
                "Do not use emojis, asterisks, markdown, or other special characters in your responses. "
                "You are curious, friendly, and have a sense of humor. "
                "You will speak English to the user."
            )
        )

    async def on_enter(self):
        # when the agent is added to the session, it'll generate a reply
        self.session.generate_reply()

    @function_tool
    async def lookup_weather(
        self, context: RunContext, location: str, latitude: str, longitude: str
    ):
        """Called when the user asks for weather-related information."""
        logger.info(f"Looking up weather for {location}")
        return "sunny with a temperature of 70 degrees."


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = VAD.load()


async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt="assemblyai/universal-streaming:en",
        llm="openai/gpt-4.1-mini",
        tts="cartesia/sonic-2:9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
        resume_false_interruption=True,
        false_interruption_timeout=1.0,
    )

    # Initialize the filler-word interruption handler
    interrupt_handler = InterruptHandler()

    # Handle user speech interruptions intelligently
    @session.on("transcription")
    async def _on_user_transcription(ev):
        text = getattr(ev, "text", "").strip()
        confidence = getattr(ev, "confidence", 1.0)
        decision = await interrupt_handler.handle_interruption(text, confidence)

        if decision == "ignored":
            logger.info(f"Ignored filler during agent speech: {text}")
        elif decision == "stop":
            logger.info(f"Real interruption detected: {text}")
            await session.stop_tts()
        else:
            logger.info(f"Processing valid user input: {text}")
            await session.generate_reply(text)

    # Collect metrics
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    await session.start(
        agent=MyAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(),
        room_output_options=RoomOutputOptions(transcription_enabled=True),
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
