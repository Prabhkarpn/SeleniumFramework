# Selenium Interview & Real‑Time Notes

These notes are written for **real interview answers** and **real automation scenarios**
(OrangeHRM, Salesforce Lightning, ServiceNow, custom Angular/React UIs etc.).
Each topic has:

1. **What it is**
2. **Why it is needed**
3. **All possible variations / locator strategies**
4. **Production‑grade code samples** (aligned to this framework: `BaseClass.getDriver()`, `ActionDriver`, `WebDriverWait`)
5. **Real problems faced + solutions**
6. **Best practices**

## Index

| # | Topic | File |
|---|-------|------|
| 1 | Handling Dropdowns (Select tag, custom `div` comboboxes, Salesforce Lightning, auto‑suggest, multi‑select) | [01-Handling-Dropdowns.md](./01-Handling-Dropdowns.md) |
| 2 | Handling Web Tables & Dynamic Web Tables (pagination, search, sort, lazy load) | [02-Handling-Web-Tables.md](./02-Handling-Web-Tables.md) |
| 3 | Handling Frames / iFrames (static, nested, dynamic) | [03-Handling-Frames.md](./03-Handling-Frames.md) |
| 4 | Waits in Selenium (Implicit, Explicit, Fluent, PageLoad, custom) | [04-About-Waits.md](./04-About-Waits.md) |
| 5 | JavaScriptExecutor (clicks, scroll, highlight, set value, alerts, shadow DOM) | [05-JavaScript-Executor.md](./05-JavaScript-Executor.md) |

## How to use these notes

- Read top‑to‑bottom for first time learning.
- For interviews → memorize the **"Real problems faced"** section in each file – that is what
  most interviewers actually test, not the syntax.
- Code snippets reference this framework's patterns:
  - `BaseClass.getDriver()` → returns a `ThreadLocal<WebDriver>`
  - `BaseClass.getActionDriver()` → wraps common Selenium actions with logging + Extent reporting
  - `WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(explicitWait));`
