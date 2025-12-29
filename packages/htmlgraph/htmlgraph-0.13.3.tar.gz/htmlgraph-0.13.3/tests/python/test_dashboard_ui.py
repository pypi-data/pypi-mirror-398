"""
Playwright tests for HtmlGraph dashboard UI.

Run with: uv run pytest tests/python/test_dashboard_ui.py --headed
"""
import os
import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.skipif(
    os.environ.get("HTMLGRAPH_UI_TESTS") != "1",
    reason="UI tests require Playwright browsers + a running server; set HTMLGRAPH_UI_TESTS=1 to enable.",
)


@pytest.fixture(scope="session")
def base_url():
    """Base URL for the dashboard (assumes server is running)."""
    return "http://localhost:8080"


def test_dashboard_loads(page: Page, base_url):
    """Test that the dashboard loads successfully."""
    page.goto(base_url)

    # Check page title
    expect(page).to_have_title("HtmlGraph Dashboard")

    # Check main heading
    heading = page.get_by_role("heading", name="<> HtmlGraph", level=1)
    expect(heading).to_be_visible()

    # Check tagline
    expect(page.get_by_text("HTML is All You Need")).to_be_visible()


def test_dashboard_stats_visible(page: Page, base_url):
    """Test that dashboard statistics are displayed."""
    page.goto(base_url)

    # Check stats boxes
    expect(page.get_by_text("Total")).to_be_visible()
    expect(page.get_by_text("Done")).to_be_visible()
    expect(page.get_by_text("Active")).to_be_visible()
    expect(page.get_by_text("Blocked")).to_be_visible()


def test_view_navigation_buttons(page: Page, base_url):
    """Test navigation between different views."""
    page.goto(base_url)

    # Check all view buttons exist
    kanban_btn = page.get_by_role("button", name="Kanban")
    graph_btn = page.get_by_role("button", name="Graph")
    analytics_btn = page.get_by_role("button", name="Analytics")
    sessions_btn = page.get_by_role("button", name="Sessions")

    expect(kanban_btn).to_be_visible()
    expect(graph_btn).to_be_visible()
    expect(analytics_btn).to_be_visible()
    expect(sessions_btn).to_be_visible()

    # Test switching to Sessions view
    sessions_btn.click()
    expect(page.get_by_role("heading", name="Sessions")).to_be_visible()


def test_kanban_columns_displayed(page: Page, base_url):
    """Test that Kanban columns are displayed."""
    page.goto(base_url)

    # Check for kanban columns
    expect(page.get_by_text("Todo")).to_be_visible()
    expect(page.get_by_text("In Progress")).to_be_visible()
    expect(page.get_by_text("Blocked")).to_be_visible()
    expect(page.get_by_text("Done")).to_be_visible()


def test_feature_card_interaction(page: Page, base_url):
    """Test clicking on a feature card opens detail panel."""
    page.goto(base_url)

    # Find any feature card in the kanban board
    # We look for elements with the feature card structure
    feature_cards = page.locator('[data-type="feature"]').first

    if feature_cards.count() > 0:
        # Click the first feature card
        feature_cards.click()

        # Detail panel should appear with Details heading
        expect(page.get_by_role("heading", name="Details")).to_be_visible()

        # Should have close button
        close_btn = page.get_by_role("button", name="×")
        expect(close_btn).to_be_visible()

        # Close the panel
        close_btn.click()


def test_sessions_view_loads(page: Page, base_url):
    """Test that sessions view loads and displays data."""
    page.goto(base_url)

    # Navigate to sessions
    page.get_by_role("button", name="Sessions").click()

    # Check heading
    expect(page.get_by_role("heading", name="Sessions")).to_be_visible()

    # Check filters exist
    expect(page.get_by_text("Status:")).to_be_visible()
    expect(page.get_by_text("Agent:")).to_be_visible()

    # Check table headers
    expect(page.get_by_text("Session ID")).to_be_visible()
    expect(page.get_by_text("Events")).to_be_visible()


def test_theme_toggle(page: Page, base_url):
    """Test theme toggle button functionality."""
    page.goto(base_url)

    # Find theme toggle button
    theme_btn = page.get_by_role("button", name="Toggle theme")
    expect(theme_btn).to_be_visible()

    # Click to toggle theme
    theme_btn.click()

    # Theme should toggle (we can check by inspecting computed styles or data attributes)
    # This is a basic test that the button works
    expect(theme_btn).to_be_visible()


@pytest.mark.skip(reason="Requires specific test data")
def test_session_comparison(page: Page, base_url):
    """Test session comparison functionality."""
    page.goto(base_url)

    # Navigate to sessions
    page.get_by_role("button", name="Sessions").click()

    # Select two sessions (requires test data)
    checkboxes = page.get_by_role("checkbox").all()
    if len(checkboxes) >= 2:
        checkboxes[0].check()
        checkboxes[1].check()

        # Click compare button
        compare_btn = page.get_by_role("button", name="Compare Sessions")
        if compare_btn.is_visible():
            compare_btn.click()

            # Comparison modal should appear
            expect(page.get_by_text("Session Comparison")).to_be_visible()
