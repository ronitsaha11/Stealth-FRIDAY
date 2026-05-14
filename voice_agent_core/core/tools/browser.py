"""
browser.py — Raptor Browser Intelligence Tools
================================================
Tool functions for browser tab awareness and control.
Uses the BrowserBridge singleton to communicate with the Chrome extension.

Tools:
  - browser_get_page()     → read current tab data
  - browser_click(selector) → click an element
  - browser_type(selector, text) → type into an input
  - browser_summarize()    → summarize page content via LLM
"""

from __future__ import annotations

import os

from core.browser_bridge import browser_bridge


def browser_get_page() -> dict:
    """
    Get structured data from the currently active browser tab.
    Returns title, URL, visible text, buttons, and inputs.
    """
    # First try the cached data (recent auto-report)
    data = browser_bridge.get_latest_page_data()

    # If stale or missing, request fresh data from extension
    if not data:
        data = browser_bridge.request_fresh_page_data(timeout=5.0)

    if not data:
        return {
            "status": "failed",
            "message": "No browser data available. Make sure the Raptor extension is installed and a tab is open.",
        }

    title = data.get("title", "Unknown")
    url = data.get("url", "")
    button_count = len(data.get("buttons", []))
    input_count = len(data.get("inputs", []))
    text_preview = (data.get("visible_text", "")[:200] + "...") if data.get("visible_text") else ""

    return {
        "status": "success",
        "message": (
            f"You are on: {title}. "
            f"URL is {url}. "
            f"The page has {button_count} clickable elements and {input_count} input fields. "
            f"Content preview: {text_preview}"
        ),
        "data": data,
    }


def browser_click(selector: str = "", text: str = "") -> dict:
    """
    Click a button or link on the active tab.
    Accepts either a CSS selector or visible button text for fuzzy matching.
    """
    if not selector and not text:
        return {"status": "failed", "message": "No selector or button text provided."}

    if text:
        result = browser_bridge.send_click_by_text(text)
    else:
        result = browser_bridge.send_click(selector)

    status = result.get("status", "error")
    message = result.get("message", "")

    if status == "blocked":
        return {"status": "failed", "message": "Action blocked: this is a restricted domain."}

    if status == "success":
        return {"status": "success", "message": message or f"Clicked successfully."}

    return {"status": "failed", "message": message or "Click failed."}


def browser_type(selector: str = "", field: str = "", text: str = "") -> dict:
    """
    Type text into an input field on the active tab.
    Accepts either a CSS selector or a field name/placeholder hint for fuzzy matching.
    """
    if not text:
        return {"status": "failed", "message": "No text provided to type."}

    if not selector and not field:
        return {"status": "failed", "message": "No selector or field hint provided."}

    if field:
        result = browser_bridge.send_type_by_hint(field, text)
    else:
        result = browser_bridge.send_type(selector, text)

    status = result.get("status", "error")
    message = result.get("message", "")

    if status == "blocked":
        return {"status": "failed", "message": "Action blocked: this is a restricted domain."}

    if status == "success":
        return {"status": "success", "message": message or f"Typed successfully."}

    return {"status": "failed", "message": message or "Type action failed."}


def browser_summarize() -> dict:
    """
    Summarize the content of the currently active browser tab using Groq LLM.
    """
    data = browser_bridge.get_latest_page_data()
    if not data:
        data = browser_bridge.request_fresh_page_data(timeout=5.0)

    if not data:
        return {
            "status": "failed",
            "message": "No browser data available. Make sure the Raptor extension is installed.",
        }

    title = data.get("title", "Unknown page")
    url = data.get("url", "")
    visible_text = data.get("visible_text", "")

    if not visible_text or len(visible_text.strip()) < 20:
        return {
            "status": "success",
            "message": f"The page '{title}' doesn't have enough readable content to summarize.",
        }

    # Truncate text for LLM context window
    text_for_llm = visible_text[:3000]

    try:
        from groq import Groq

        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            return {
                "status": "failed",
                "message": "Cannot summarize: Groq API key not configured.",
            }

        client = Groq()
        resp = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Raptor, a concise AI assistant. "
                        "Summarize the following web page content in 2-3 sentences. "
                        "Be direct and informative."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Page title: {title}\nURL: {url}\n\nContent:\n{text_for_llm}",
                },
            ],
            model="llama-3.1-8b-instant",
        )
        summary = resp.choices[0].message.content
        return {"status": "success", "message": summary}

    except Exception as e:
        return {"status": "failed", "message": f"Summarization failed: {e}"}


def browser_search(query: str) -> dict:
    """
    Open a new tab to search the web for a query, wait for the page to load,
    and then return a summary of the search results.
    """
    import webbrowser
    import time
    from urllib.parse import quote_plus

    if not query:
        return {"status": "failed", "message": "No search query provided."}

    search_url = f"https://www.google.com/search?q={quote_plus(query)}"
    
    # Open default browser
    webbrowser.open(search_url)

    # Wait for the browser to open, load the page, and the extension to send the new page data
    # Google searches are usually fast, give it 3.5 seconds
    time.sleep(3.5)

    # Automatically summarize the new active tab
    summary_result = browser_summarize()
    
    status = summary_result.get("status", "error")
    if status == "success":
        summary_msg = summary_result.get("message", "Could not summarize search results.")
        return {
            "status": "success", 
            "message": f"I searched for {query}. {summary_msg}"
        }
    else:
        return {
            "status": "success", 
            "message": f"I opened a search for {query}, but couldn't read the results automatically."
        }
