from pathlib import Path

import pytest
from pushikoo_interface import (
    Processer,
    get_adapter_test_env,
    Struct,
)
from pushikoo_interface.structure import StructText, StructTitle

from pushikoo_processer_re.config import InstanceConfig


def test_replace_rule():
    """Test replace rule processing."""
    ProcesserClass, CtxClass = get_adapter_test_env(
        Path(__file__).parents[1] / "pyproject.toml",
        adapter_instance_config=InstanceConfig.model_validate(
            {
                "rules": [
                    {"find": r"foo", "process": {"type": "replace", "replace": "bar"}}
                ]
            }
        ),
    )
    ProcesserClass: type[Processer]
    processer = ProcesserClass.create(identifier="test", ctx=CtxClass())
    processed = processer.process(
        content=Struct(content=[StructText(text="hello foo world")])
    )
    assert processed.content[0].text == "hello bar world"


def test_multiple_replace_rules():
    """Test multiple replace rules applied in order."""
    ProcesserClass, CtxClass = get_adapter_test_env(
        Path(__file__).parents[1] / "pyproject.toml",
        adapter_instance_config=InstanceConfig.model_validate(
            {
                "rules": [
                    {
                        "find": r"foo",
                        "process": {"type": "replace", "replace": "bar"},
                    },
                    {
                        "find": r"hello",
                        "process": {"type": "replace", "replace": "hi"},
                    },
                ]
            }
        ),
    )
    ProcesserClass: type[Processer]
    processer = ProcesserClass.create(identifier="test", ctx=CtxClass())
    processed = processer.process(
        content=Struct(content=[StructText(text="hello foo world")])
    )
    assert processed.content[0].text == "hi bar world"


def test_terminate_rule():
    """Test terminate rule raises exception."""
    from pushikoo_interface import TerminateFlowException

    ProcesserClass, CtxClass = get_adapter_test_env(
        Path(__file__).parents[1] / "pyproject.toml",
        adapter_instance_config=InstanceConfig.model_validate(
            {"rules": [{"find": r"STOP", "process": {"type": "terminate"}}]}
        ),
    )
    ProcesserClass: type[Processer]

    processer = ProcesserClass.create(identifier="test", ctx=CtxClass())
    with pytest.raises(TerminateFlowException):
        processer.process(
            content=Struct(content=[StructText(text="This should STOP here")]),
        )


def test_invalid_regex_pattern_raises_value_error():
    """Ensure invalid regex patterns propagate a ValueError."""
    ProcesserClass, CtxClass = get_adapter_test_env(
        Path(__file__).parents[1] / "pyproject.toml",
        adapter_instance_config=InstanceConfig.model_validate(
            {"rules": [{"find": "[", "process": {"type": "replace", "replace": "x"}}]}
        ),
    )
    ProcesserClass: type[Processer]
    processer = ProcesserClass.create(identifier="test", ctx=CtxClass())
    with pytest.raises(ValueError, match="Invalid regex pattern"):
        processer.process(
            content=Struct(content=[StructText(text="trigger invalid regex")])
        )


def test_regex_word_boundary():
    """Test regex with word boundary."""
    ProcesserClass, CtxClass = get_adapter_test_env(
        Path(__file__).parents[1] / "pyproject.toml",
        adapter_instance_config=InstanceConfig.model_validate(
            {
                "rules": [
                    {
                        "find": r"\bcat\b",
                        "process": {"type": "replace", "replace": "dog"},
                    }
                ]
            }
        ),
    )
    ProcesserClass: type[Processer]
    processer = ProcesserClass.create(identifier="test", ctx=CtxClass())
    processed = processer.process(
        content=Struct(content=[StructText(text="cat category concatenate")])
    )
    # Only standalone "cat" should be replaced, not "category" or "concatenate"
    assert processed.content[0].text == "dog category concatenate"


def test_title_processing():
    """Test that StructTitle is also processed."""
    ProcesserClass, CtxClass = get_adapter_test_env(
        Path(__file__).parents[1] / "pyproject.toml",
        adapter_instance_config=InstanceConfig.model_validate(
            {
                "rules": [
                    {
                        "find": r"old",
                        "process": {"type": "replace", "replace": "new"},
                    }
                ]
            }
        ),
    )
    ProcesserClass: type[Processer]
    processer = ProcesserClass.create(identifier="test", ctx=CtxClass())
    processed = processer.process(
        content=Struct(content=[StructTitle(text="old title")])
    )
    assert processed.content[0].text == "new title"


def test_complex_lookaround_matching():
    """Test lookahead/lookbehind replacements across multiple struct entries."""
    ProcesserClass, CtxClass = get_adapter_test_env(
        Path(__file__).parents[1] / "pyproject.toml",
        adapter_instance_config=InstanceConfig.model_validate(
            {
                "rules": [
                    {
                        "find": r"(?<=foo)bar",
                        "process": {"type": "replace", "replace": "BAZ"},
                    },
                    {
                        "find": r"cat(?=dog)",
                        "process": {"type": "replace", "replace": "cat-"},
                    },
                ]
            }
        ),
    )
    ProcesserClass: type[Processer]
    processer = ProcesserClass.create(identifier="test", ctx=CtxClass())
    processed = processer.process(
        content=Struct(
            content=[
                StructText(text="foobar123 catdog"),
                StructTitle(text="catdogfoobar"),
            ]
        )
    )
    assert processed.content[0].text == "fooBAZ123 cat-dog"
    assert processed.content[1].text == "cat-dogfooBAZ"
