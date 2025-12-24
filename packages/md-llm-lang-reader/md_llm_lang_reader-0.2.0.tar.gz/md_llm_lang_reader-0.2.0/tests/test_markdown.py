from md_llm_lang_reader.generator import is_fence_line, fence_delim


def test_fence_detection():
    assert is_fence_line("```")
    assert is_fence_line("```python")
    assert is_fence_line("~~~")
    assert is_fence_line("~~~js")

    assert fence_delim("```python") == "```"
    assert fence_delim("~~~js") == "~~~"
