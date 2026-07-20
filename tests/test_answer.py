import pytest
from unittest.mock import patch, MagicMock
from core.answer import answer, NO_DOCS_RESPONSE

CHUNKS = [
    {"id": 1, "doc_id": 1, "page_num": 5, "text": "(d) Total 93200840.00", "filename": "form16.pdf", "score": 2.5},
    {"id": 2, "doc_id": 1, "page_num": 8, "text": "Tax Deducted from Salary of Employee u/s 192(1) 3,57,73,078.00", "filename": "form16.pdf", "score": 1.8},
]

def _mock_grok_response(content: str):
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp

def test_answer_returns_string(monkeypatch):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_grok_response(
        "Answer: Your gross salary is 93,20,084.\nConfidence: HIGH\nSources:\n- Document: form16.pdf, Page 5: \"(d) Total 93200840.00\""
    )
    with patch("core.answer.OpenAI", return_value=mock_client):
        result = answer("What is my gross salary?", CHUNKS, "fake-key")
    assert isinstance(result, str)
    assert "Answer:" in result

def test_answer_empty_chunks_returns_no_docs_response():
    result = answer("What is my salary?", [], "fake-key")
    assert result == NO_DOCS_RESPONSE

def test_answer_passes_api_key():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_grok_response("Answer: x\nConfidence: LOW\nSources:")
    with patch("core.answer.OpenAI", return_value=mock_client) as mock_cls:
        answer("test", CHUNKS, "my-grok-key")
        mock_cls.assert_called_once_with(api_key="my-grok-key", base_url="https://api.x.ai/v1")

def test_answer_prompt_includes_chunk_text():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_grok_response("Answer: ok\nConfidence: LOW\nSources:")
    with patch("core.answer.OpenAI", return_value=mock_client):
        answer("salary?", CHUNKS, "key")
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"] if call_args.kwargs else call_args[1]["messages"]
        user_content = next(m["content"] for m in messages if m["role"] == "user")
        assert "(d) Total 93200840.00" in user_content
        assert "form16.pdf" in user_content
