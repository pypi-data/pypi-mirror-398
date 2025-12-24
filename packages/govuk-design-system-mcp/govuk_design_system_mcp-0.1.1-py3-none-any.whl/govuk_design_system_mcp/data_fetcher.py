import httpx
from functools import lru_cache

DESIGN_SYSTEM_BASE = "https://raw.githubusercontent.com/alphagov/govuk-design-system/main/src"

@lru_cache(maxsize=100)
def fetch_text(url: str) -> str | None:
    """Fetch text content from a URL."""
    try:
        resp = httpx.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.text
    except Exception:
        pass
    return None

def get_component_list() -> list[str]:
    """Get list of all components from govuk-frontend."""
    return [
        "accordion", "back-link", "breadcrumbs", "button", "character-count",
        "checkboxes", "cookie-banner", "date-input", "details", "error-message",
        "error-summary", "exit-this-page", "fieldset", "file-upload", "footer",
        "header", "inset-text", "notification-banner", "pagination", "panel",
        "password-input", "phase-banner", "radios", "select", "service-navigation",
        "skip-link", "summary-list", "table", "tabs", "tag", "task-list",
        "text-input", "textarea", "warning-text"
    ]

def get_pattern_list() -> list[str]:
    """Get list of all patterns from GOV.UK Design System."""
    return [
        "addresses", "bank-details", "check-a-service-is-suitable", "check-answers",
        "complete-multiple-tasks", "confirm-a-phone-number", "confirm-an-email-address",
        "confirmation-pages", "contact-a-department-or-service-team", "cookies-page",
        "create-a-username", "create-accounts", "dates", "email-addresses",
        "equality-information", "ethnic-group", "exit-a-page-quickly", "gender-or-sex",
        "names", "national-insurance-numbers", "navigate-a-service", "page-not-found-pages",
        "passwords", "payment-card-details", "phone-numbers", "problem-with-the-service-pages",
        "question-pages", "service-unavailable-pages", "start-pages", "start-using-a-service",
        "step-by-step-navigation", "task-list-pages", "validation"
    ]

def get_style_list() -> list[str]:
    """Get list of all styles from GOV.UK Design System."""
    return [
        "colour", "font-override-classes", "headings", "images", "layout",
        "links", "lists", "page-template", "paragraphs", "section-break",
        "spacing", "type-scale", "typeface"
    ]

def get_component_docs(component: str) -> str | None:
    """Fetch documentation markdown for a component."""
    url = f"{DESIGN_SYSTEM_BASE}/components/{component}/index.md"
    return fetch_text(url)

def get_pattern_docs(pattern: str) -> str | None:
    """Fetch documentation markdown for a pattern."""
    url = f"{DESIGN_SYSTEM_BASE}/patterns/{pattern}/index.md"
    return fetch_text(url)

def get_style_docs(style: str) -> str | None:
    """Fetch documentation markdown for a style."""
    url = f"{DESIGN_SYSTEM_BASE}/styles/{style}/index.md"
    return fetch_text(url)