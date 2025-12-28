"""
Harmony processor for OpenAI Harmony format handling.

Provides detection and specialized processing for agents using OpenAI Harmony
response formatting (openai-harmony package for gpt-oss models).

Note: openai-harmony is a core dependency and should always be available
when the package is properly installed.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Import openai-harmony components
# This is a core dependency and should always be available when installed via pip
try:
    from openai_harmony import (  # type: ignore[import-untyped]
        HarmonyEncodingName,
        load_harmony_encoding,
    )

    HARMONY_AVAILABLE = True
except ImportError:
    # This should only happen in development/testing environments
    # where dependencies haven't been installed yet
    HARMONY_AVAILABLE = False
    logger.warning(
        "openai-harmony not found - this is a core dependency. "
        "Install with: pip install basic-agent-chat-loop"
    )


class HarmonyProcessor:
    """
    Processor for agents using OpenAI Harmony format.

    Detects and processes responses using the Harmony encoding format,
    which provides structured conversation handling for gpt-oss models.
    """

    def __init__(self, show_detailed_thinking: bool = False):
        """
        Initialize Harmony processor.

        Args:
            show_detailed_thinking: Whether to show reasoning/analysis/commentary
                channels with prefixes (default: False, only show final response)
        """
        self.show_detailed_thinking = show_detailed_thinking

        if not HARMONY_AVAILABLE:
            logger.error(
                "Cannot initialize HarmonyProcessor: openai-harmony not installed. "
                "This is a core dependency - please install via: "
                "pip install basic-agent-chat-loop"
            )
            self.encoding = None
            return

        try:
            self.encoding = load_harmony_encoding(HarmonyEncodingName.HARMONY_GPT_OSS)
            logger.info("Harmony encoding initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Harmony encoding: {e}")
            self.encoding = None

    @staticmethod
    def detect_harmony_agent(agent: Any, model_id: Optional[str] = None) -> bool:
        """
        Detect if an agent uses Harmony format.

        Detection strategies:
        1. Check for harmony-specific attributes
        2. Check provided model_id parameter
        3. Check agent model attributes for gpt-oss references

        Args:
            agent: Agent instance to check
            model_id: Optional pre-extracted model ID (recommended)

        Returns:
            True if agent appears to use Harmony format
        """
        if not HARMONY_AVAILABLE:
            # In dev/test environments without openai-harmony installed,
            # still detect agents but they won't be processed
            logger.debug(
                "Harmony detection available but processing will be disabled "
                "without openai-harmony"
            )

        # Strategy 1: Check for explicit harmony attribute
        if hasattr(agent, "uses_harmony") and agent.uses_harmony:
            logger.info("✓ Harmony: Agent has explicit uses_harmony=True")
            return True

        # Strategy 2: Check for harmony encoding attribute
        if hasattr(agent, "harmony_encoding"):
            logger.info("✓ Harmony: Agent has harmony_encoding attribute")
            return True

        # Strategy 3: Check provided model_id (preferred method)
        if model_id:
            model_lower = model_id.lower()
            if "gpt-oss" in model_lower or "harmony" in model_lower:
                logger.info(f"✓ Harmony: Model ID contains indicator: {model_id}")
                return True
            else:
                logger.debug(f"Model ID does not indicate harmony: {model_id}")

        # Strategy 4: Check model attributes on agent as fallback
        model_indicators = []

        # Check direct string attributes on agent
        for attr in ["model", "model_id", "model_name"]:
            if hasattr(agent, attr):
                model_value = getattr(agent, attr)
                if model_value and isinstance(model_value, str):
                    model_indicators.append(model_value.lower())
                    logger.debug(f"Found model string on agent.{attr}: {model_value}")

        # Check nested attributes on agent.model object
        if hasattr(agent, "model"):
            model = agent.model
            # If model itself is a string, we already captured it above
            if not isinstance(model, str):
                for attr in ["model_id", "model", "model_name", "name", "id"]:
                    if hasattr(model, attr):
                        model_value = getattr(model, attr)
                        if model_value:
                            model_indicators.append(str(model_value).lower())
                            logger.debug(
                                f"Found model on agent.model.{attr}: {model_value}"
                            )

        # Check if any indicator contains gpt-oss or harmony
        for indicator in model_indicators:
            if "gpt-oss" in indicator or "harmony" in indicator:
                logger.info(
                    f"✓ Harmony: Model attribute contains indicator: {indicator}"
                )
                return True

        # Strategy 4: Check agent class name
        class_name = agent.__class__.__name__.lower()
        if "harmony" in class_name:
            logger.info(f"Agent class name contains 'harmony': {class_name}")
            return True

        # Strategy 5: Check for harmony-specific methods
        harmony_methods = ["render_conversation", "parse_messages"]
        if any(hasattr(agent, method) for method in harmony_methods):
            logger.info("Agent has harmony-specific methods")
            return True

        # No harmony indicators found
        logger.debug(
            f"No harmony indicators found. Checked: "
            f"attributes (uses_harmony, harmony_encoding), "
            f"model indicators: {model_indicators}, "
            f"class: {agent.__class__.__name__}"
        )
        return False

    def process_response(
        self, response_text: str, metadata: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        Process a response that may contain Harmony-formatted content.

        Args:
            response_text: Raw response text from agent
            metadata: Optional metadata from response object (for token access)

        Returns:
            Dict with processed response data including:
            - text: Processed/formatted text
            - has_reasoning: Whether reasoning output was detected
            - has_tools: Whether tool calls were detected
            - channels: Dict of detected output channels
        """
        result = {
            "text": response_text,
            "has_reasoning": False,
            "has_tools": False,
            "channels": {},
        }

        if not HARMONY_AVAILABLE or not self.encoding:
            logger.debug("Harmony not available, skipping processing")
            return result

        try:
            # Try to extract tokens from metadata (OpenAI-compatible response)
            tokens = self._extract_tokens_from_metadata(metadata)

            if tokens:
                logger.debug(f"Extracted {len(tokens)} tokens from response")
                logger.debug(f"Token sample (first 20): {tokens[:20]}")

                # Parse messages from tokens using Harmony encoding
                try:
                    messages = self.encoding.parse_messages_from_completion_tokens(
                        tokens
                    )
                    logger.info(f"Parsed {len(messages)} harmony messages")

                    # Group messages by channel
                    channels = self._group_messages_by_channel(messages)
                    if channels:
                        result["channels"] = channels
                        result["has_reasoning"] = any(
                            ch in channels
                            for ch in ["reasoning", "analysis", "thinking"]
                        )

                        # Use final channel as primary text if available
                        if "final" in channels:
                            result["text"] = channels["final"]
                        elif "response" in channels:
                            result["text"] = channels["response"]

                        logger.info(f"Found channels: {list(channels.keys())}")
                    else:
                        logger.debug("No harmony channels found in messages")

                except Exception as e:
                    error_msg = str(e)
                    logger.error("=" * 60)
                    logger.error("HARMONY PARSING ERROR")
                    logger.error("=" * 60)
                    logger.error(f"Error type: {type(e).__name__}")
                    logger.error(f"Error message: {error_msg}")
                    logger.error(f"Number of tokens: {len(tokens)}")
                    logger.error(f"First 50 tokens: {tokens[:50]}")
                    logger.error(
                        "This error often occurs when the model outputs harmony "
                        "tokens in an unexpected format or sequence."
                    )
                    logger.error(
                        "The chat will continue using text-based fallback parsing."
                    )
                    logger.error("=" * 60)
                    logger.warning(
                        f"Failed to parse harmony tokens: {error_msg}. "
                        "Falling back to text-based extraction"
                    )
                    # Fall back to text-based parsing
                    channels = self._extract_channels(response_text)
                    if channels:
                        result["channels"] = channels
            else:
                logger.debug("No tokens found, using text-based parsing")
                # Fallback: Look for text-based markers
                channels = self._extract_channels(response_text)
                if channels:
                    result["channels"] = channels

            # Check for tool call indicators
            if any(
                marker in response_text.lower()
                for marker in ["<tool_call>", "<function>", "tool_use"]
            ):
                result["has_tools"] = True

        except Exception as e:
            logger.warning(f"Error processing Harmony response: {e}", exc_info=True)
            # Return original text on error

        return result

    def _extract_tokens_from_metadata(
        self, metadata: Optional[Any]
    ) -> Optional[list[int]]:
        """
        Extract raw tokens from response metadata.

        Looks for tokens in OpenAI-compatible response structures:
        - response.choices[0].logprobs.tokens (OpenAI style)
        - response.choices[0].logprobs.content[].token_ids
        - response.logprobs (direct access)

        Args:
            metadata: Response object from model

        Returns:
            List of token IDs or None if not found
        """
        if not metadata:
            logger.debug("No metadata provided for token extraction")
            return None

        try:
            # Log basic response structure
            logger.debug(f"Extracting tokens from {type(metadata).__name__}")

            # Strategy 1: OpenAI style - choices[0].logprobs
            if hasattr(metadata, "choices") and metadata.choices:
                choice = metadata.choices[0]
                if hasattr(choice, "logprobs"):
                    logprobs = choice.logprobs
                    if logprobs is None:
                        logger.warning(
                            "logprobs is None - enable logprobs=True in your API call"
                        )
                    else:
                        # Check for direct tokens list
                        if hasattr(logprobs, "tokens") and logprobs.tokens:
                            logger.debug(
                                f"Extracted {len(logprobs.tokens)} tokens from logprobs"
                            )
                            return logprobs.tokens

                        # Check for content array with token_ids
                        if hasattr(logprobs, "content") and logprobs.content:
                            token_ids = [
                                item.token_id
                                for item in logprobs.content
                                if hasattr(item, "token_id")
                            ]
                            if token_ids:
                                logger.debug(
                                    f"Extracted {len(token_ids)} token IDs from content"
                                )
                                return token_ids

            # Strategy 2: Direct logprobs attribute
            if (
                hasattr(metadata, "logprobs")
                and metadata.logprobs
                and hasattr(metadata.logprobs, "tokens")
            ):
                logger.debug("Found tokens in metadata.logprobs")
                return metadata.logprobs.tokens

            # Strategy 3: Check if metadata itself is a list of tokens
            if isinstance(metadata, list) and all(
                isinstance(x, int) for x in metadata[:10]
            ):
                logger.debug(f"Metadata is token list ({len(metadata)} tokens)")
                return metadata

            logger.warning(
                "No tokens found - ensure your API call includes logprobs=True"
            )
            return None

        except Exception as e:
            logger.error(f"Error extracting tokens: {e}")
            return None

    def _group_messages_by_channel(self, messages: list[Any]) -> dict[str, str]:
        """
        Group Harmony messages by their channel attribute.

        Args:
            messages: List of Harmony Message objects

        Returns:
            Dict mapping channel names to combined content
        """
        logger.debug(f"Grouping {len(messages)} harmony messages by channel")

        channels: dict[str, list[str]] = {}

        for i, msg in enumerate(messages):
            try:
                # Get channel name (default to 'default' if not specified)
                channel = "default"
                if hasattr(msg, "channel") and msg.channel:
                    channel = str(msg.channel).lower()

                # Get content
                content = ""
                if hasattr(msg, "content"):
                    content_val = msg.content
                    content = (
                        content_val
                        if isinstance(content_val, str)
                        else str(content_val)
                    )

                # Add to channel group
                if channel not in channels:
                    channels[channel] = []

                if content.strip():
                    channels[channel].append(content)

            except Exception as e:
                logger.warning(f"Error processing message {i + 1}: {e}")
                continue

        # Combine content for each channel
        result = {
            channel: "\n".join(content_list)
            for channel, content_list in channels.items()
        }

        if result:
            logger.info(f"Found harmony channels: {list(result.keys())}")
        else:
            logger.warning("No harmony channels found in messages")

        return result

    def _extract_channels(self, text: str) -> dict[str, str]:
        """
        Extract output channels from Harmony-formatted text.

        NOTE: This is a simple text-based fallback for when token parsing fails.
        It uses basic regex patterns and will NOT properly parse real harmony output.
        Proper harmony parsing requires token-level processing via
        parse_messages_from_completion_tokens().

        This fallback is kept as a last resort but should not be relied upon.

        Harmony supports multiple output channels like:
        - analysis: Internal reasoning/analysis
        - commentary: Meta-commentary about the response
        - final: Final output to user

        Args:
            text: Response text to parse

        Returns:
            Dict mapping channel names to content (likely empty for real harmony output)
        """
        channels = {}

        import re

        # Simple XML-style tag extraction (won't match real harmony format)
        channel_pattern = r"<(\w+)>(.*?)</\1>"
        matches = re.findall(channel_pattern, text, re.DOTALL)

        for channel_name, content in matches:
            channels[channel_name.lower()] = content.strip()

        return channels

    def format_for_display(self, processed_response: dict[str, Any]) -> str:
        """
        Format processed Harmony response for terminal display.

        Behavior depends on show_detailed_thinking setting:
        - False (default): Only show final response
        - True: Show all channels (reasoning, analysis, commentary, final) with prefixes

        Args:
            processed_response: Response dict from process_response()

        Returns:
            Formatted text for display
        """
        channels = processed_response.get("channels", {})

        # If detailed thinking is disabled, only show final response or main text
        if not self.show_detailed_thinking:
            # Return final channel if available, otherwise return main text
            return channels.get("final", processed_response["text"])

        # Detailed thinking mode: show all channels with labeled prefixes
        lines = []

        # Show reasoning/thinking/analysis if present
        reasoning = (
            channels.get("reasoning")
            or channels.get("thinking")
            or channels.get("analysis")
        )
        if reasoning:
            lines.append("💭 [REASONING]")
            lines.append(reasoning)
            lines.append("")  # Blank line separator

        # Show analysis if it's separate from reasoning
        if "analysis" in channels and "reasoning" in channels:
            lines.append("📊 [ANALYSIS]")
            lines.append(channels["analysis"])
            lines.append("")

        # Show commentary
        if "commentary" in channels:
            lines.append("📝 [COMMENTARY]")
            lines.append(channels["commentary"])
            lines.append("")

        # Show tool calls if detected
        if processed_response.get("has_tools") and "tool_call" in channels:
            lines.append("🔧 [TOOL CALL]")
            lines.append(channels["tool_call"])
            lines.append("")

        # Show final response
        final_response = channels.get("final", processed_response["text"])
        if final_response:
            lines.append("💬 [RESPONSE]")
            lines.append(final_response)

        return "\n".join(lines)
