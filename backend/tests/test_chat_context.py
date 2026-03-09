from routers.chat import summarize_context_on_server, build_page_context_message


def test_summarize_context_prioritizes_relevant_elements():
    ctx = {
        "url": "http://localhost:5173/dashboard",
        "title": "Dashboard",
        "headings": [{"tag": "h1", "text": "Welcome"}],
        "elements": [
            {"tag": "button", "text": "Open settings"},
            {"tag": "a", "text": "Pricing"},
            {"tag": "div", "text": "Random content"},
        ],
    }

    summary = summarize_context_on_server(ctx)

    assert summary["url"] == ctx["url"]
    assert summary["title"] == "Dashboard"
    assert any(el["text"] == "Pricing" for el in summary["elements"])


def test_build_page_context_message_formats_system_message():
    msg = build_page_context_message({"url": "http://x", "title": "T", "elements": []})
    assert msg is not None
    assert msg["role"] == "system"
    assert msg["content"].startswith("PAGE_CONTEXT:\n")
