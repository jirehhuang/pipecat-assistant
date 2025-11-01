"""Flexible frame processor for handling hard-coded command patterns."""

import re
from enum import Enum
from typing import Awaitable, Callable

from loguru import logger
from pipecat.frames.frames import TranscriptionFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor


class MatchType(Enum):
    """Types of phrase matching strategies."""

    EXACT = "exact"  # Entire prompt must match exactly
    STARTS_WITH = "starts_with"  # Prompt starts with the phrase
    ENDS_WITH = "ends_with"  # Prompt ends with the phrase
    CONTAINS = "contains"  # Prompt contains the phrase (default)


# pylint: disable=too-few-public-methods
class CommandAction:
    """Represent a command with its phrases, match type, and action.

    Parameters
    ----------
    phrases
        List of phrases that trigger this action.
    action
        Async function to execute when a phrase matches.
    match_type
        How to match the phrase (exact, starts_with, ends_with, contains).
    name
        Optional name for the action (for logging).
    """

    def __init__(
        self,
        phrases: list[str],
        action: Callable[[TranscriptionFrame], Awaitable[None]],
        match_type: MatchType = MatchType.CONTAINS,
        name: str | None = None,
    ):
        self.phrases = phrases
        self.action = action
        self.match_type = match_type
        self.name = name or action.__name__
        self._patterns = self._compile_patterns()

    def _compile_patterns(self) -> list[re.Pattern]:
        """Compile regex patterns based on match type."""
        patterns = []
        for phrase in self.phrases:
            words = phrase.split()
            escaped_words = [re.escape(word) for word in words]
            word_pattern = r"\s*".join(escaped_words)

            if self.match_type == MatchType.EXACT:
                # Match only if entire text is the phrase
                pattern_str = rf"^\s*{word_pattern}\s*$"
            elif self.match_type == MatchType.STARTS_WITH:
                # Match if text starts with the phrase
                pattern_str = rf"^\s*{word_pattern}\b"
            elif self.match_type == MatchType.ENDS_WITH:
                # Match if text ends with the phrase
                pattern_str = rf"\b{word_pattern}\s*$"
            else:  # CONTAINS
                # Match if phrase appears anywhere in text
                pattern_str = rf"\b{word_pattern}\b"

            pattern = re.compile(pattern_str, re.IGNORECASE)
            patterns.append(pattern)
        return patterns

    def matches(self, text: str) -> bool:
        """Check if the text matches any of the command patterns."""
        return any(pattern.search(text) for pattern in self._patterns)


class CustomFrameProcessor(FrameProcessor):
    """Processor for flexibly handling hard-coded command patterns.

    This processor allows you to register multiple command actions, each with
    their own phrases and matching strategies. When a transcription matches a
    command, the associated action is executed and the frame is optionally
    blocked from proceeding through the pipeline.

    Parameters
    ----------
    actions
        List of command actions to register.
    block_on_match
        If True, matched frames won't be passed through the pipeline.
    """

    def __init__(
        self,
        actions: list[CommandAction] | None = None,
        block_on_match: bool = True,
    ):
        super().__init__()
        self._actions = actions or []
        self._block_on_match = block_on_match

    def add_action(self, action: CommandAction):
        """Add a command action to the processor.

        Parameters
        ----------
        action
            The command action to add.
        """
        self._actions.append(action)

    async def process_frame(self, frame, direction: FrameDirection):
        """Process frames and check for command matches."""
        await super().process_frame(frame, direction)

        if isinstance(frame, TranscriptionFrame):
            # Check each registered action
            for action in self._actions:
                if action.matches(frame.text):
                    logger.info(
                        f"Command '{action.name}' matched: '{frame.text}'"
                    )
                    # Execute the action
                    await action.action(frame)

                    # Optionally block the frame from proceeding
                    if self._block_on_match:
                        return

        await self.push_frame(frame, direction)
