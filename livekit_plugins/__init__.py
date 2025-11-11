import sys, os

# Dynamically include plugin folders in sys.path so imports like
# `from livekit_plugins.turn_detector.multilingual import MultilingualModel`
# work properly

BASE_DIR = os.path.dirname(__file__)

# Add paths for internal plugin packages
plugin_paths = [
    os.path.join(BASE_DIR, "livekit-plugins-silero"),
    os.path.join(BASE_DIR, "livekit-plugins-turn-detector"),
]

for path in plugin_paths:
    if path not in sys.path:
        sys.path.append(path)

# (Optional but helpful)
__all__ = ["silero", "turn_detector"]
