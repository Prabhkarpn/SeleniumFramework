# 5. JavaScriptExecutor in Selenium

> `JavascriptExecutor` lets you run **arbitrary JavaScript** inside the browser
> through Selenium. It is the ultimate "fallback weapon" when normal Selenium
> actions fail — and a great helper for scrolling, highlighting, and reading
> page state.

---

## 5.1  What it is

`org.openqa.selenium.JavascriptExecutor` is an **interface implemented by every
`WebDriver`**. So you simply cast:

```java
JavascriptExecutor js = (JavascriptExecutor) driver;
js.executeScript("alert('hi');");
```

Two methods:

| Method | Use it for |
|--------|-----------|
| `executeScript(script, args…)` | synchronous JS — return value or `null` |
| `executeAsyncScript(script, args…)` | async JS — must call `arguments[arguments.length-1](result)` to signal done |

When you pass `args`, they show up inside the script as `arguments[0]`, `arguments[1]`,
…  Most often you pass a `WebElement` and use `arguments[0]` as the DOM node.

---

## 5.2  When SHOULD we use JS executor (and when should we NOT)

### Use it when:
- A normal click is being intercepted by overlays you can't easily dismiss.
- You need to **scroll** to/around an element.
- You need to **highlight** elements during demos / debugging.
- You need to read non‑standard properties (`scrollHeight`, `offsetTop`, custom
  attributes).
- You need to **set values directly** in inputs that misbehave with `sendKeys`
  (date pickers, masked inputs).
- The element is technically not interactable but functionally is (e.g. zero‑size
  hidden labels).
- Working with **shadow DOM** (Selenium 4 has `getShadowRoot()` natively, but for
  older versions JS is the only way).

### Do NOT use it when:
- A normal `click()` / `sendKeys()` would work — JS bypasses many real‑user checks
  and your test will pass even when a real user can't click the element. **Test
  what users do.**
- You're tempted to "JS away" a flaky test instead of fixing the wait.

> **Rule:** prefer real Selenium actions, fall back to JS only if necessary.

---

## 5.3  Common recipes

### a) Click via JS (bypasses overlays)
```java
WebElement el = driver.findElement(By.id("save"));
((JavascriptExecutor) driver).executeScript("arguments[0].click();", el);
```

### b) Scroll into view
```java
js.executeScript("arguments[0].scrollIntoView({block:'center'});", el);
```

This framework already exposes a helper:
```java
// ActionDriver#scrollToElement(By by)
js.executeScript("arguments[0].scrollIntoView(true)", element);
```

### c) Scroll the window
```java
js.executeScript("window.scrollBy(0, 800);");                    // by 800px
js.executeScript("window.scrollTo(0, document.body.scrollHeight);"); // to bottom
js.executeScript("window.scrollTo(0, 0);");                       // to top
```

### d) Set value directly (date pickers, masked inputs)
```java
js.executeScript(
    "arguments[0].value=arguments[1];" +
    "arguments[0].dispatchEvent(new Event('input', {bubbles:true}));" +
    "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
    dateInput, "2026-05-26");
```

> Why dispatch `input`/`change`? React/Angular don't notice raw `value=` writes.
> Firing the events makes the framework re‑render correctly.

### e) Highlight an element (debug / demos)
This framework already has `applyBorder(by, "green")` in `ActionDriver`. The implementation:

```java
String script = "arguments[0].style.border='3px solid " + color + "'";
((JavascriptExecutor) driver).executeScript(script, element);
```

Pretty handy for screenshots — every passing/failing element in your Extent report
gets a green/red border.

### f) Get / set text
```java
String txt = (String) js.executeScript("return arguments[0].innerText;", el);
js.executeScript("arguments[0].innerText='Updated by Automation';", el);
```

### g) Read browser & page info
```java
String title    = (String) js.executeScript("return document.title;");
String ua       = (String) js.executeScript("return navigator.userAgent;");
Long winHeight  = (Long)   js.executeScript("return window.innerHeight;");
String urlNow   = (String) js.executeScript("return window.location.href;");
```

### h) Wait until JS condition is true
```java
new WebDriverWait(driver, Duration.ofSeconds(15))
   .until(d -> Boolean.TRUE.equals(
       ((JavascriptExecutor) d).executeScript("return document.readyState === 'complete';")));
```

### i) Wait for jQuery / Angular to be idle
```java
// jQuery
js.executeScript("return typeof jQuery !== 'undefined' && jQuery.active === 0;");

// Angular (older)
js.executeScript("return window.getAllAngularTestabilities().every(t => t.isStable());");
```

### j) Open a new tab
```java
js.executeScript("window.open('https://example.com','_blank');");
```

### k) Refresh / navigate
```java
js.executeScript("window.location.reload();");
js.executeScript("history.back();");
```

### l) Zoom in/out (occasional CI fix for overlapping elements)
```java
js.executeScript("document.body.style.zoom='90%';");
```

### m) Drag using JS (when native Actions API misbehaves on HTML5 DnD)
You usually need a custom JS DnD helper script — search "html5DnD selenium" — but the
shape is:
```java
js.executeScript("arguments[0].dispatchEvent(new DragEvent('dragstart'));", source);
```

### n) Take full‑page screenshot via JS (legacy browsers)
Selenium 4 `getFullPageScreenshotAs(...)` works only in Firefox; for Chrome you
either use Chrome DevTools Protocol or scroll + stitch. JS helps you collect
heights:
```java
Long h = (Long) js.executeScript("return document.body.scrollHeight;");
```

### o) Shadow DOM (pre Selenium 4)
```java
WebElement host = driver.findElement(By.cssSelector("my-app"));
WebElement insideShadow = (WebElement) ((JavascriptExecutor) driver)
   .executeScript("return arguments[0].shadowRoot.querySelector('input.search');", host);
insideShadow.sendKeys("hello");
```

In Selenium 4 you can use the native API:
```java
SearchContext shadow = host.getShadowRoot();
shadow.findElement(By.cssSelector("input.search")).sendKeys("hello");
```

### p) Async script — wait for a callback‑driven API
```java
String script =
    "var cb = arguments[arguments.length - 1];" +
    "fetch('/api/health').then(r => r.json()).then(j => cb(j.status));";
String status = (String) js.executeAsyncScript(script);
```

---

## 5.4  Examples that fit THIS framework

You already have `JavascriptExecutor` used in `ActionDriver` for `applyBorder`,
`scrollToElement` and `waitForPageLoad`. Below are 3 more methods that pair well:

```java
/** JS-click as a fallback when normal click is intercepted. */
public void jsClick(By by) {
    try {
        WebElement el = driver.findElement(by);
        applyBorder(by, "green");
        ((JavascriptExecutor) driver).executeScript("arguments[0].click();", el);
        ExtentManager.logStep("JS-clicked " + getElementDescription(by));
        logger.info("JS-clicked " + getElementDescription(by));
    } catch (Exception e) {
        applyBorder(by, "red");
        logger.error("JS click failed: " + e.getMessage());
    }
}

/** Set value on date/masked inputs and trigger input/change events. */
public void jsSetValue(By by, String value) {
    try {
        WebElement el = driver.findElement(by);
        ((JavascriptExecutor) driver).executeScript(
            "arguments[0].value=arguments[1];" +
            "arguments[0].dispatchEvent(new Event('input', {bubbles:true}));" +
            "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
            el, value);
        logger.info("JS-set value '" + value + "' on " + getElementDescription(by));
    } catch (Exception e) {
        logger.error("JS set value failed: " + e.getMessage());
    }
}

/** Scroll a child element to the bottom — useful for AG-Grid / virtualized tables. */
public void jsScrollContainerToBottom(By container) {
    WebElement c = driver.findElement(container);
    ((JavascriptExecutor) driver).executeScript(
        "arguments[0].scrollTop = arguments[0].scrollHeight;", c);
}
```

---

## 5.5  Real problems faced & solutions

| # | Problem | Solution |
|---|---------|----------|
| 1 | `ElementClickInterceptedException` because of cookie banner | Either dismiss banner properly OR `jsClick` |
| 2 | Date picker rejects `sendKeys` | Use `jsSetValue(...)` so React updates state |
| 3 | Element is below the fold; `click()` fails in headless | `scrollIntoView({block:'center'})` first |
| 4 | Test passes but user actually can't click button (overlay) | DON'T fall back to JS click silently — assert overlay is gone first |
| 5 | `executeAsyncScript` hangs forever | Forgot to invoke the callback `arguments[arguments.length-1]` |
| 6 | `WebElement` returned by JS is stale | Re‑locate via `By` inside a wait |
| 7 | "JavaScript error: Cannot read properties of null" | Element not in DOM when JS ran — wrap in `WebDriverWait` first |
| 8 | Need Shadow DOM in Chrome 95 | `arguments[0].shadowRoot.querySelector(...)` (or upgrade Selenium to 4) |
| 9 | Animation makes click miss target | `await new Promise(r=>setTimeout(r,300))` inside async script, or wait for animation class to be removed |

---

## 5.6  Performance & safety tips

- **Pass elements as args** (`arguments[0]`) instead of re‑querying inside the
  script — faster and avoids race conditions.
- **Cast return values carefully** — JS numbers come back as `Long` or `Double`,
  booleans as `Boolean`, lists as `ArrayList<Object>`, elements as `WebElement`.
- **Always log what you JS‑executed** so the Extent report tells reviewers it was a
  JS interaction, not a real click.
- **Don't pile up huge scripts.** If you find yourself writing 50 lines of JS,
  store it in a `.js` resource file and load it at runtime.

---

## 5.7  Quick interview answer

> *"JavascriptExecutor is the Selenium interface that runs JS in the browser. I use
> it for scrolling (`scrollIntoView`), highlighting elements (already wired into
> our framework's `applyBorder`), waiting for `document.readyState`, and as a
> fallback for clicks that get intercepted or for date/masked inputs where
> `sendKeys` doesn't trigger React state updates. I avoid using JS click as a
> default because it bypasses real‑user checks and can hide actual UI bugs. For
> async stuff I use `executeAsyncScript` and remember to invoke the callback at
> `arguments[arguments.length - 1]`."*
