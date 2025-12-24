"""
speech.py - Speech-to-text plugin interface
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class SpeechExtractor:
    """Interface for speech-to-text extraction"""

    def __init__(self):
        self.plugins = []

    async def extract(self, response) -> Dict[str, Any]:
        """Extract text from audio using available plugins"""
        result = {"text": "", "transcription": None}

        # Try plugins in order
        for plugin in self.plugins:
            try:
                transcription = await plugin.transcribe(response.content)
                if transcription:
                    result["transcription"] = transcription
                    result["text"] = transcription.get("text", "")
                    break
            except Exception as e:
                logger.error(f"Error in speech plugin {plugin}: {e}")

        return result
