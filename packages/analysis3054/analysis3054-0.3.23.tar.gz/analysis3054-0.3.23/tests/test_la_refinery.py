import importlib.util
import sys
import types
from pathlib import Path

import pytest

# Stub the Playwright module before loading la_refinery to avoid heavy optional installs
fake_async_api = types.ModuleType("playwright.async_api")


class DummyTimeoutError(Exception):
    """Minimal TimeoutError replacement for tests."""


class DummyPlaywright:
    def __init__(self):
        self.chromium = self
        self.webkit = self

    async def launch(self, *args, **kwargs):
        raise RuntimeError("chromium launch called in tests")


async def async_playwright():
    class _Context:
        async def __aenter__(self):
            return DummyPlaywright()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    return _Context()


fake_async_api.TimeoutError = DummyTimeoutError
fake_async_api.Page = object
fake_async_api.async_playwright = async_playwright

sys.modules.setdefault("playwright", types.ModuleType("playwright"))
sys.modules["playwright.async_api"] = fake_async_api

# Load the la_refinery module directly to avoid optional package imports from analysis3054.__init__
MODULE_PATH = Path(__file__).resolve().parents[1] / "analysis3054" / "la_refinery.py"
spec = importlib.util.spec_from_file_location("la_refinery", MODULE_PATH)
la_refinery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(la_refinery)

safe_click = la_refinery.safe_click
safe_fill = la_refinery.safe_fill
wait_for_apex_processing = la_refinery.wait_for_apex_processing


class DummyLocator:
    def __init__(self, *, should_click_fail=False, should_fill_fail=False):
        self.should_click_fail = should_click_fail
        self.should_fill_fail = should_fill_fail
        self.waits = []
        self.clicked = False
        self.filled_with = None
        self.pressed = []
        self.scrolled = False

    @property
    def first(self):
        return self

    async def wait_for(self, state="visible", timeout=0):
        self.waits.append((state, timeout))

    async def scroll_into_view_if_needed(self):
        self.scrolled = True

    async def click(self):
        if self.should_click_fail:
            raise RuntimeError("click failed")
        self.clicked = True

    async def fill(self, value):
        if self.should_fill_fail:
            raise RuntimeError("fill failed")
        self.filled_with = value

    async def press(self, key):
        self.pressed.append(key)


class DummyPage:
    def __init__(self, locator_map=None, selector_behaviors=None):
        self.locator_map = locator_map or {}
        self.selector_behaviors = selector_behaviors or {}
        self.load_states = []

    def locator(self, selector):
        if selector not in self.locator_map:
            raise KeyError(f"Unknown selector {selector}")
        return self.locator_map[selector]

    async def wait_for_selector(self, selector, state="visible", timeout=0):
        behavior = self.selector_behaviors.get((selector, state), "ok")
        if behavior == "timeout":
            # Import within the method to mirror la_refinery implementation
            from playwright.async_api import TimeoutError as PlaywrightTimeout

            raise PlaywrightTimeout("timeout")
        if behavior == "error":
            raise RuntimeError("selector error")

    async def wait_for_load_state(self, state):
        self.load_states.append(state)

    async def wait_for_timeout(self, timeout):
        # Included to match interface used by la_refinery helpers
        return timeout


@pytest.mark.anyio
async def test_safe_click_uses_fallback_selector():
    first_locator = DummyLocator(should_click_fail=True)
    second_locator = DummyLocator()
    page = DummyPage(locator_map={
        "first": first_locator,
        "second": second_locator,
    })

    result = await safe_click(page, ["first", "second"], "test")

    assert result is True
    assert first_locator.clicked is False
    assert second_locator.clicked is True
    # Both selectors should have been waited on
    assert len(first_locator.waits) == 1
    assert len(second_locator.waits) == 1


@pytest.mark.anyio
async def test_safe_click_returns_false_when_all_strategies_fail():
    locator = DummyLocator(should_click_fail=True)
    page = DummyPage(locator_map={"only": locator})

    result = await safe_click(page, ["only"], "test")

    assert result is False
    assert locator.clicked is False


@pytest.mark.anyio
async def test_safe_fill_successfully_sets_value_and_triggers_tab():
    failing_locator = DummyLocator(should_fill_fail=True)
    working_locator = DummyLocator()
    page = DummyPage(locator_map={
        "fail": failing_locator,
        "ok": working_locator,
    })

    result = await safe_fill(page, ["fail", "ok"], "01-JAN-2018", "date")

    assert result is True
    assert working_locator.filled_with == "01-JAN-2018"
    assert working_locator.pressed == ["Tab"]
    assert failing_locator.filled_with is None


@pytest.mark.anyio
async def test_safe_fill_returns_false_when_all_strategies_fail():
    locator = DummyLocator(should_fill_fail=True)
    page = DummyPage(locator_map={"only": locator})

    result = await safe_fill(page, ["only"], "value", "field")

    assert result is False
    assert locator.filled_with is None


@pytest.mark.anyio
async def test_wait_for_apex_processing_uses_spinner_and_completes():
    page = DummyPage(selector_behaviors={
        (".u-Processing", "visible"): "timeout",  # no spinner visible
        (".u-Processing", "detached"): "ok",
    })

    await wait_for_apex_processing(page)

    # Should not fall back to load_state when detach completes
    assert page.load_states == []


@pytest.mark.anyio
async def test_wait_for_apex_processing_falls_back_to_network_idle_on_error():
    page = DummyPage(selector_behaviors={
        (".u-Processing", "visible"): "ok",
        (".u-Processing", "detached"): "error",
    })

    await wait_for_apex_processing(page)

    assert page.load_states == ["networkidle"]
