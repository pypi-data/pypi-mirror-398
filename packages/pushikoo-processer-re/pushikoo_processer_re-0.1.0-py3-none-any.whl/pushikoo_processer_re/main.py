import re

from loguru import logger
from pushikoo_interface import (
    Processer,
    Struct,
    TerminateFlowException,
)
from pushikoo_interface.structure import StructText

from pushikoo_processer_re.config import (
    AdapterConfig,
    InstanceConfig,
    Rule,
    Terminate,
    Replace,
)


class RegexProcesser(
    Processer[
        AdapterConfig,
        InstanceConfig,
    ]
):
    """
    A regex-based text processer.

    This processer applies a list of regex rules to text content in order.
    Each rule can either:
    - Terminate: Terminate the flow when the pattern is found
    - Replace: Replace all matches with a specified string
    """

    def __init__(self) -> None:
        logger.debug(f"{self.adapter_name}.{self.identifier} initialized")

    def _get_compiled_rules(self) -> list[tuple[re.Pattern[str], Rule]]:
        """
        Get compiled regex patterns, recompiling if config has changed.
        Supports hot-reloading of configuration.
        """
        current_rules = self.instance_config.rules
        _compiled_rules = []

        for rule in current_rules:
            try:
                pattern = re.compile(rule.find)
                _compiled_rules.append((pattern, rule))
                logger.debug(f"Compiled regex pattern: {rule.find}")
            except re.error as e:
                logger.error(f"Invalid regex pattern '{rule.find}': {e}")
                raise ValueError(f"Invalid regex pattern '{rule.find}': {e}")

        return _compiled_rules

    def _process_text(self, text: str) -> str:
        """
        Apply all rules to a text string.

        Args:
            text: The input text to process

        Returns:
            The processed text after applying all replacement rules

        Raises:
            TerminateFlowException: If a Terminate rule matches
        """
        compiled_rules = self._get_compiled_rules()

        for pattern, rule in compiled_rules:
            if pattern.search(text):
                if isinstance(rule.process, Terminate):
                    logger.debug(f"Terminate rule matched: {rule.find}")
                    raise TerminateFlowException(
                        f"Matched terminate pattern: {rule.find}"
                    )
                elif isinstance(rule.process, Replace):
                    text = pattern.sub(rule.process.replace, text)
                    logger.debug(
                        f"Replaced pattern '{rule.find}' with '{rule.process.replace}'"
                    )
        return text

    def process(self, content: Struct) -> Struct:
        """
        Process the content by applying regex rules to all text elements.

        Only StructText and StructTitle elements are processed.
        Image and URL elements are passed through unchanged.

        Args:
            content: The input Struct containing content blocks

        Returns:
            The modified Struct with processed text content
        """
        for item in content.content:
            if isinstance(item, StructText):
                item.text = self._process_text(item.text)
            # StructImage and StructURL are not text-based, skip them

        return content
