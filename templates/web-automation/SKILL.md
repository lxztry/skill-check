---
name: {{SKILL_NAME}}
description: >
  Automates web browsing tasks including navigation, form filling, screenshot capture,
  and data extraction. Use when browsing websites, scraping web content, filling forms,
  taking screenshots, or automating web interactions. Trigger on: web browsing,
  web scraping, browser automation, form submission.
compatibility:
  - Python 3.8+
  - selenium / playwright
---

# {{SKILL_NAME}}

Automates web browsing tasks with [Selenium/Playwright].

## Prerequisites

1. Install browser driver:
   - Chrome: `selenium-manager` or download chromedriver
   - Firefox: geckodriver
2. Install dependencies:
   ```bash
   pip install selenium playwright
   playwright install
   ```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BROWSER` | No | Browser to use: chrome/firefox (default: chrome) |
| `HEADLESS` | No | Run headless: true/false (default: true) |
| `IMPLICIT_WAIT` | No | Implicit wait seconds (default: 10) |

## Usage

### Basic Browser Control

```python
from scripts.browser import Browser

browser = Browser(headless=True)
browser.navigate("https://example.com")
title = browser.get_title()
print(title)
browser.close()
```

### Common Tasks

| Task | Command |
|------|---------|
| Navigate | `python scripts/navigate.py --url https://example.com` |
| Screenshot | `python scripts/screenshot.py --url https://example.com --output screenshot.png` |
| Fill Form | `python scripts/fill_form.py --url https://example.com/form --data '{"username":"test"}'` |
| Scrape | `python scripts/scrape.py --url https://example.com --selector ".content"` |

## Browser Methods

| Method | Description |
|--------|-------------|
| `navigate(url)` | Go to URL |
| `screenshot(path)` | Save screenshot |
| `find_element(selector)` | Find element by CSS selector |
| `fill_form(data)` | Fill form with dict data |
| `click(selector)` | Click element |
| `wait_for(selector)` | Wait for element |

## Error Handling

| Error | Handling |
|-------|----------|
| Element not found | Wait and retry with explicit wait |
| Timeout | Increase implicit_wait |
| Browser crash | Restart browser |

## References

- `references/browser-api.md` - Detailed API reference
- `references/examples.md` - Usage examples
