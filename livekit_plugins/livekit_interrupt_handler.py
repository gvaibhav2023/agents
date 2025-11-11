"""
LiveKit Voice Interruption Handler
Author: Vaibhav
Description: Filters out filler words during agent TTS playback to prevent false VAD interruptions.
"""

import asyncio
from typing import List

# Configurable list of ignored filler words
IGNORED_WORDS = ["uh", "umm", "hmm", "haan"]

class InterruptHandler:
    def __init__(self, ignored_words: List[str] = None):
        self.ignored_words = ignored_words or IGNORED_WORDS
        self.agent_speaking = False  # This changes when TTS starts/stops

    def set_agent_state(self, speaking: bool):
        """Call this when the agent starts/stops speaking."""
        self.agent_speaking = speaking

    def is_filler(self, text: str) -> bool:
        """Return True if input text contains only filler words."""
        clean_text = text.lower().strip()
        if not clean_text:
            return False
        return all(word in self.ignored_words for word in clean_text.split())

    async def handle_interruption(self, text: str, confidence: float = 1.0):
        """
        Handle incoming speech and decide if it's a real interruption.
        Returns: 'ignored', 'stop', or 'process'
        """
        if self.agent_speaking:
            # Case 1: Agent currently speaking
            if confidence < 0.6:
                print(f"[LOW CONFIDENCE IGNORED] '{text}'")
                return "ignored"

            if self.is_filler(text):
                print(f"[IGNORED FILLER] '{text}' while agent speaking")
                return "ignored"

            print(f"[VALID INTERRUPTION] '{text}' while agent speaking → STOP agent")
            return "stop"

        else:
            # Case 2: Agent quiet
            print(f"[USER SPEECH] '{text}' registered normally")
            return "process"
