"""
Audio notification component for agent turn completion.

Provides cross-platform WAV audio playback functionality.
"""

import platform
import subprocess
from pathlib import Path
from typing import Optional


class AudioNotifier:
    """Handles audio notifications for agent events."""

    def __init__(self, enabled: bool = True, sound_file: Optional[str] = None):
        """
        Initialize audio notifier.

        Args:
            enabled: Whether audio notifications are enabled
            sound_file: Path to WAV file (uses default if None)
        """
        self.enabled = enabled
        self.system = platform.system()

        # Set default sound file to bundled notification.wav
        if sound_file is None:
            module_dir = Path(__file__).parent.parent
            self.sound_file = module_dir / "notification.wav"
        else:
            self.sound_file = Path(sound_file)

        # Verify sound file exists
        if not self.sound_file.exists():
            self.enabled = False
            print(f"Warning: Audio file not found: {self.sound_file}")

    def play(self) -> bool:
        """
        Play the notification sound.

        Returns:
            True if sound played successfully, False otherwise
        """
        if not self.enabled:
            return False

        try:
            if self.system == "Darwin":  # macOS
                subprocess.run(
                    ["afplay", str(self.sound_file)],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return True

            elif self.system == "Linux":
                # Try aplay first, then paplay as fallback
                for cmd in ["aplay", "paplay"]:
                    try:
                        subprocess.run(
                            [cmd, str(self.sound_file)],
                            check=False,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                        return True
                    except FileNotFoundError:
                        continue
                return False

            elif self.system == "Windows":
                import winsound  # type: ignore[import-untyped]

                winsound.PlaySound(  # type: ignore[attr-defined]
                    str(self.sound_file),
                    winsound.SND_FILENAME | winsound.SND_ASYNC,  # type: ignore[attr-defined]
                )
                return True

            else:
                # Unsupported platform
                return False

        except Exception:
            # Silently fail - audio is non-critical
            return False
