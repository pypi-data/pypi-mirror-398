from md_llm_lang_reader.generator import extract_json_array


def test_extract_json_array_exact():
    raw = '[{"src":"a","tgt":"b"}]'
    assert extract_json_array(raw) == raw


def test_extract_json_array_embedded():
    raw = "Here you go:\n\n[ {\"src\": \"a\", \"tgt\": \"b\"} ]\nThanks!"
    assert extract_json_array(raw).strip().startswith("[")
    assert extract_json_array(raw).strip().endswith("]")
