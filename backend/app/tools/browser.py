"""Headless browser automation backed by Playwright."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.config import get_settings
from app.tools.base import Tool, ToolError

try:
    from playwright.async_api import async_playwright
except ImportError:  # pragma: no cover - import guarded for environments w/o playwright
    async_playwright = None  # type: ignore[assignment]


class BrowserArgs(BaseModel):
    url: str = Field(description="Fully-qualified URL to open, including the scheme.")
    action: Literal["extract_text", "screenshot", "title"] = Field(
        default="extract_text",
        description=(
            "What to do after navigating. 'extract_text' returns visible page text, "
            "'title' returns the document title, 'screenshot' returns a base64 PNG."
        ),
    )
    wait_for: str | None = Field(
        default=None,
        description="Optional CSS selector to wait for before performing the action.",
    )
    max_chars: int = Field(
        default=4000,
        ge=200,
        le=20000,
        description="Maximum number of characters of extracted text to return.",
    )


class BrowserTool(Tool):
    """Open a URL in a headless browser and extract information."""

    name = "browse_web"
    description = (
        "Navigate to a URL in a headless browser and return the page title, "
        "visible text, or a screenshot. Use this for live web lookups, "
        "JavaScript-heavy pages, or when you need the rendered DOM."
    )
    parameters_model = BrowserArgs

    async def run(
        self,
        url: str,
        action: str,
        wait_for: str | None,
        max_chars: int,
    ) -> dict[str, Any]:
        if async_playwright is None:
            raise ToolError(
                "playwright is not installed in this environment. "
                "Run `pip install playwright && playwright install chromium`."
            )

        settings = get_settings()
        engine = settings.browser_engine.lower()
        if engine not in {"chromium", "firefox", "webkit"}:
            raise ToolError(f"unsupported browser engine: {engine}")

        async with async_playwright() as p:
            browser_type = getattr(p, engine)
            try:
                browser = await browser_type.launch(headless=settings.browser_headless)
            except Exception as exc:
                raise ToolError(
                    f"failed to launch {engine}: {exc}. "
                    "Ensure browser binaries are installed via `playwright install`."
                ) from exc

            try:
                context = await browser.new_context()
                page = await context.new_page()
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                except Exception as exc:
                    raise ToolError(f"navigation to {url} failed: {exc}") from exc

                if wait_for:
                    try:
                        await page.wait_for_selector(wait_for, timeout=15_000)
                    except Exception as exc:
                        raise ToolError(f"selector {wait_for!r} never appeared: {exc}") from exc

                if action == "title":
                    return {"url": url, "title": await page.title()}

                if action == "screenshot":
                    import base64

                    raw = await page.screenshot(full_page=False, type="png")
                    return {
                        "url": url,
                        "screenshot_base64": base64.b64encode(raw).decode("ascii"),
                        "mime": "image/png",
                    }

                # extract_text
                text = await page.evaluate("() => document.body ? document.body.innerText : ''")
                cleaned = " ".join(text.split())
                return {
                    "url": url,
                    "title": await page.title(),
                    "text": cleaned[:max_chars],
                    "truncated": len(cleaned) > max_chars,
                }
            finally:
                await browser.close()
