"""
Mode loader for Self-Contained Bundle Architecture.

This module provides ModeLoader class for loading mode configurations
from directory-based bundles. Each mode bundle contains:
- mode.yaml: configuration
- system_prompt.md: LLM system prompt
- faq.md: FAQ content for RAG
- examples.yaml: few-shot examples (optional)
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

logger = logging.getLogger(__name__)


class ModeLoader:
    """Load mode configurations from Self-Contained Bundles.

    Each mode is stored in a directory with the following structure:
    config/modes/
    └── mode_name/
        ├── mode.yaml          (required)
        ├── system_prompt.md   (required)
        ├── faq.md             (required)
        └── examples.yaml      (optional)

    Attributes:
        modes_dir: Path to directory containing mode bundles
    """

    def __init__(self, modes_dir: Path) -> None:
        """Initialize ModeLoader.

        Args:
            modes_dir: Path to directory containing mode bundles

        Raises:
            FileNotFoundError: If modes_dir doesn't exist
        """
        self.modes_dir = Path(modes_dir)
        if not self.modes_dir.exists():
            raise FileNotFoundError(f"Modes directory not found: {self.modes_dir}")
        logger.info(f"Initialized ModeLoader with directory: {self.modes_dir}")

    def load_all_modes(self) -> Dict[str, Dict[str, Any]]:
        """Load all modes from directory.

        Iterates through all subdirectories in modes_dir and loads
        mode configurations. Skips directories without mode.yaml
        or with disabled modes.

        Returns:
            Dictionary mapping mode names to mode configurations

        Example:
            >>> loader = ModeLoader(Path("config/modes"))
            >>> modes = loader.load_all_modes()
            >>> print(modes["it_support"]["display_name"])
            '🛠️ IT Support'
        """
        modes: Dict[str, Dict[str, Any]] = {}

        if not self.modes_dir.exists():
            logger.warning(f"Modes directory does not exist: {self.modes_dir}")
            return modes

        # Iterate through all subdirectories
        for mode_dir in self.modes_dir.iterdir():
            if not mode_dir.is_dir():
                continue  # Skip files

            try:
                mode = self._load_mode(mode_dir)
                if mode is None:
                    continue  # Mode was skipped (disabled or error)

                mode_name = mode.get("name")
                if not mode_name:
                    logger.warning(f"Mode in {mode_dir} has no 'name' field, skipping")
                    continue

                # Check if mode is enabled
                if not mode.get("enabled", True):
                    logger.info(f"Skipped disabled mode: {mode_name}")
                    continue

                modes[mode_name] = mode
                logger.info(f"✅ Loaded mode: {mode_name}")

            except Exception as e:
                logger.error(f"Failed to load mode from {mode_dir}: {e}", exc_info=True)
                # Continue loading other modes even if one fails
                continue

        logger.info(f"✅ Loaded {len(modes)} mode(s) from {self.modes_dir}")
        return modes

    def _load_mode(self, mode_dir: Path) -> Optional[Dict[str, Any]]:
        """Load mode configuration from directory.

        Loads mode.yaml, system_prompt.md, faq.md, and optionally examples.yaml.
        Validates that required files exist.

        Args:
            mode_dir: Path to mode directory containing mode.yaml

        Returns:
            Dictionary with mode configuration or None if mode disabled/error

        Raises:
            FileNotFoundError: If system_prompt.md or faq.md missing
            yaml.YAMLError: If mode.yaml has syntax errors
        """
        mode_yaml_path = mode_dir / "mode.yaml"

        # Check if mode.yaml exists
        if not mode_yaml_path.exists():
            logger.warning(f"⏭️ Skipped mode: mode.yaml not found in {mode_dir}")
            return None

        # Load mode.yaml
        try:
            mode = yaml.safe_load(mode_yaml_path.read_text(encoding="utf-8"))
            if mode is None:
                logger.error(f"mode.yaml is empty in {mode_dir}")
                return None
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in {mode_dir}/mode.yaml: {e}")
            return None

        # Validate required fields
        files = mode.get("files", {})
        if not isinstance(files, dict):
            logger.error(f"Invalid 'files' section in {mode_dir}/mode.yaml")
            return None

        # 1. Load system_prompt.md (required)
        system_prompt_file = files.get("system_prompt")
        if not system_prompt_file:
            logger.error(f"Missing 'files.system_prompt' in {mode_dir}/mode.yaml")
            return None

        system_prompt_path = mode_dir / system_prompt_file
        if not system_prompt_path.exists():
            raise FileNotFoundError(f"Missing required file: {system_prompt_path}")

        # Load system_prompt as string
        mode["system_prompt"] = system_prompt_path.read_text(encoding="utf-8").strip()

        # 2. Load faq.md (required)
        faq_file = files.get("faq")
        if not faq_file:
            logger.error(f"Missing 'files.faq' in {mode_dir}/mode.yaml")
            return None

        faq_path = mode_dir / faq_file
        if not faq_path.exists():
            raise FileNotFoundError(f"Missing required file: {faq_path}")

        # ВАЖНО: Не загружаем содержимое faq.md, только путь
        # handlers.py и rag_chains.py используют faq_file для rebuild_index
        mode["faq_file"] = str(faq_path.absolute())

        # 3. Load examples.yaml (optional)
        examples_file = files.get("examples")
        if examples_file:
            examples_path = mode_dir / examples_file
            if examples_path.exists():
                try:
                    examples_content = yaml.safe_load(
                        examples_path.read_text(encoding="utf-8")
                    )
                    mode["few_shot_examples"] = examples_content
                    logger.debug(f"Loaded examples.yaml for mode {mode.get('name')}")
                except yaml.YAMLError as e:
                    logger.warning(
                        f"Invalid YAML in {examples_path}: {e}, skipping examples"
                    )
            else:
                logger.info(f"No examples.yaml for mode {mode.get('name')}, skipping")

        return mode

    def get_mode(self, mode_name: str) -> Optional[Dict[str, Any]]:
        """Get mode configuration by name.

        Args:
            mode_name: Name of the mode to retrieve

        Returns:
            Mode configuration dictionary or None if not found

        Example:
            >>> loader = ModeLoader(Path("config/modes"))
            >>> mode = loader.get_mode("it_support")
            >>> print(mode["display_name"])
            '🛠️ IT Support'
        """
        modes = self.load_all_modes()
        return modes.get(mode_name)
