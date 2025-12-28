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
    from openai_harmony import (
        Conversation,
        DeveloperContent,
        HarmonyEncodingName,
        Message,
        Role,
        SystemContent,
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
    def detect_harmony_agent(agent: Any) -> bool:
        """
        Detect if an agent uses Harmony format.

        Detection strategies:
        1. Check for harmony-specific attributes
        2. Check agent metadata for harmony indicators
        3. Check agent model name for gpt-oss references

        Args:
            agent: Agent instance to check

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
            logger.info("Agent has explicit uses_harmony=True")
            return True

        # Strategy 2: Check for harmony encoding attribute
        if hasattr(agent, "harmony_encoding"):
            logger.info("Agent has harmony_encoding attribute")
            return True

        # Strategy 3: Check model name/id for gpt-oss or harmony
        model_indicators = []
        if hasattr(agent, "model"):
            model = agent.model
            for attr in ["model_id", "model", "model_name", "name"]:
                if hasattr(model, attr):
                    model_value = getattr(model, attr)
                    if model_value:
                        model_indicators.append(str(model_value).lower())

        for indicator in model_indicators:
            if "gpt-oss" in indicator or "harmony" in indicator:
                logger.info(f"Agent model contains harmony indicator: {indicator}")
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
                    logger.warning(
                        f"Failed to parse harmony tokens: {e}. "
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
            # Log detailed response structure for debugging
            logger.info("=" * 60)
            logger.info("HARMONY DEBUG: Response Structure Analysis")
            logger.info("=" * 60)
            logger.info(f"Response type: {type(metadata).__name__}")
            logger.info(
                f"Response module: {type(metadata).__module__}"
            )

            # Log all non-private attributes
            attrs = [a for a in dir(metadata) if not a.startswith("_")]
            logger.info(f"Available attributes: {attrs[:30]}")

            # Strategy 1: OpenAI style - choices[0].logprobs
            if hasattr(metadata, "choices"):
                logger.info("✓ Has 'choices' attribute")
                if metadata.choices:
                    logger.info(f"  Choices count: {len(metadata.choices)}")
                    choice = metadata.choices[0]
                    logger.info(f"  Choice[0] type: {type(choice).__name__}")

                    choice_attrs = [a for a in dir(choice) if not a.startswith("_")]
                    logger.info(f"  Choice[0] attributes: {choice_attrs[:20]}")

                    # Check for logprobs attribute
                    if hasattr(choice, "logprobs"):
                        logger.info("  ✓ Choice has 'logprobs' attribute")
                        logprobs = choice.logprobs

                        if logprobs is None:
                            logger.warning(
                                "  ✗ logprobs is None - you need to enable "
                                "logprobs in your API call!"
                            )
                            logger.warning(
                                "  Add 'logprobs=True' to your completion request"
                            )
                        else:
                            logger.info(f"  Logprobs type: {type(logprobs).__name__}")
                            logprobs_attrs = [
                                a for a in dir(logprobs) if not a.startswith("_")
                            ]
                            logger.info(
                                f"  Logprobs attributes: {logprobs_attrs[:20]}"
                            )

                            # Check for direct tokens list
                            if hasattr(logprobs, "tokens"):
                                tokens = logprobs.tokens
                                logger.info(
                                    f"  ✓ Found tokens in logprobs.tokens: "
                                    f"{len(tokens) if tokens else 0} tokens"
                                )
                                if tokens:
                                    logger.info(
                                        f"  First 5 tokens: {tokens[:5]}"
                                    )
                                    logger.info("=" * 60)
                                    return tokens

                            # Check for content array with token_ids
                            if hasattr(logprobs, "content"):
                                logger.info("  ✓ Has 'content' attribute")
                                if logprobs.content:
                                    logger.info(
                                        f"  Content items: {len(logprobs.content)}"
                                    )
                                    if logprobs.content:
                                        first_item = logprobs.content[0]
                                        logger.info(
                                            f"  First item type: "
                                            f"{type(first_item).__name__}"
                                        )
                                        item_attrs = [
                                            a
                                            for a in dir(first_item)
                                            if not a.startswith("_")
                                        ]
                                        logger.info(
                                            f"  First item attrs: {item_attrs[:20]}"
                                        )

                                    token_ids = []
                                    for item in logprobs.content:
                                        if hasattr(item, "token_id"):
                                            token_ids.append(item.token_id)
                                        elif hasattr(item, "token"):
                                            # Log token text for debugging
                                            logger.debug(
                                                f"  Found token text: "
                                                f"{getattr(item, 'token', '')[:20]}"
                                            )
                                    if token_ids:
                                        logger.info(
                                            f"  ✓ Extracted {len(token_ids)} "
                                            f"token IDs from content"
                                        )
                                        logger.info(
                                            f"  First 5 token IDs: {token_ids[:5]}"
                                        )
                                        logger.info("=" * 60)
                                        return token_ids
                    else:
                        logger.warning("  ✗ Choice has no 'logprobs' attribute")
                else:
                    logger.warning("  ✗ Choices list is empty")
            else:
                logger.info("✗ No 'choices' attribute")

            # Strategy 2: Direct logprobs attribute
            if hasattr(metadata, "logprobs"):
                logger.info("✓ Has direct 'logprobs' attribute")
                if metadata.logprobs and hasattr(metadata.logprobs, "tokens"):
                    logger.info("  ✓ Found tokens in metadata.logprobs.tokens")
                    logger.info("=" * 60)
                    return metadata.logprobs.tokens

            # Strategy 3: Check if metadata itself is a list of tokens
            if isinstance(metadata, list):
                logger.info(f"✓ Metadata is a list with {len(metadata)} items")
                if all(isinstance(x, int) for x in metadata[:10]):
                    logger.info("  ✓ Items appear to be integers (tokens)")
                    logger.info("=" * 60)
                    return metadata

            logger.warning("✗ No tokens found in any expected location")
            logger.warning(
                "Make sure your API call includes 'logprobs=True' parameter"
            )
            logger.info("=" * 60)
            return None

        except Exception as e:
            logger.error(f"Error extracting tokens from metadata: {e}", exc_info=True)
            logger.info("=" * 60)
            return None

    def _group_messages_by_channel(
        self, messages: list[Any]
    ) -> dict[str, str]:
        """
        Group Harmony messages by their channel attribute.

        Args:
            messages: List of Harmony Message objects

        Returns:
            Dict mapping channel names to combined content
        """
        logger.info("=" * 60)
        logger.info("HARMONY DEBUG: Grouping Messages by Channel")
        logger.info("=" * 60)
        logger.info(f"Total messages to process: {len(messages)}")

        channels: dict[str, list[str]] = {}

        for i, msg in enumerate(messages):
            try:
                logger.info(f"\nMessage {i + 1}:")
                logger.info(f"  Type: {type(msg).__name__}")

                # Get channel name (default to 'default' if not specified)
                channel = "default"
                if hasattr(msg, "channel"):
                    channel_val = msg.channel
                    logger.info(f"  Has 'channel' attribute: {channel_val}")
                    if channel_val:
                        channel = str(channel_val).lower()
                else:
                    logger.info("  No 'channel' attribute")

                logger.info(f"  Using channel: '{channel}'")

                # Get content
                content = ""
                if hasattr(msg, "content"):
                    content_val = msg.content
                    logger.info(
                        f"  Content type: {type(content_val).__name__}"
                    )
                    if isinstance(content_val, str):
                        content = content_val
                        logger.info(
                            f"  Content length: {len(content)} chars"
                        )
                        logger.info(
                            f"  Content preview: {content[:100]}..."
                        )
                    else:
                        content = str(content_val)
                        logger.info(
                            f"  Content (stringified): {content[:100]}..."
                        )
                else:
                    logger.warning("  No 'content' attribute!")

                # Add to channel group
                if channel not in channels:
                    channels[channel] = []
                    logger.info(f"  Created new channel group: '{channel}'")

                if content.strip():
                    channels[channel].append(content)
                    logger.info(f"  Added content to '{channel}' channel")
                else:
                    logger.warning("  Content was empty, skipping")

            except Exception as e:
                logger.error(
                    f"Error processing message {i + 1}: {e}", exc_info=True
                )
                continue

        # Combine content for each channel
        logger.info("\n" + "=" * 60)
        logger.info("Channel Summary:")
        logger.info("=" * 60)

        result = {}
        for channel, content_list in channels.items():
            combined = "\n".join(content_list)
            result[channel] = combined
            logger.info(
                f"  '{channel}': {len(content_list)} messages, "
                f"{len(combined)} total chars"
            )

        logger.info(f"\nTotal channels found: {list(result.keys())}")
        logger.info("=" * 60)

        return result

    def _extract_channels(self, text: str) -> dict[str, str]:
        """
        Extract output channels from Harmony-formatted text.

        Harmony supports multiple output channels like:
        - analysis: Internal reasoning/analysis
        - commentary: Meta-commentary about the response
        - final: Final output to user

        Args:
            text: Response text to parse

        Returns:
            Dict mapping channel names to content
        """
        channels = {}

        # Simple channel extraction based on common patterns
        # More sophisticated parsing could use the Harmony encoding directly
        import re

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

    def create_conversation(self, messages: list) -> Optional[Any]:
        """
        Create a Harmony Conversation object from message history.

        Args:
            messages: List of message dicts with 'role' and 'content'

        Returns:
            Harmony Conversation object or None if not available or on error
        """
        if not HARMONY_AVAILABLE:
            logger.warning(
                "Cannot create Harmony conversation: openai-harmony not installed"
            )
            return None

        try:
            harmony_messages = []
            for msg in messages:
                role_str = msg.get("role", "user").upper()
                content = msg.get("content", "")

                # Map role strings to Harmony Role enum
                if role_str == "SYSTEM":
                    role = Role.SYSTEM
                    msg_content = SystemContent.new()
                elif role_str == "DEVELOPER":
                    role = Role.DEVELOPER
                    msg_content = DeveloperContent.new().with_instructions(content)
                elif role_str == "ASSISTANT":
                    role = Role.ASSISTANT
                    msg_content = content
                else:  # USER
                    role = Role.USER
                    msg_content = content

                harmony_messages.append(
                    Message.from_role_and_content(role, msg_content)
                )

            return Conversation.from_messages(harmony_messages)

        except Exception as e:
            logger.error(f"Failed to create Harmony conversation: {e}")
            return None
