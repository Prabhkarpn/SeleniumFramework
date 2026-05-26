# 4. Waits in Selenium

> Most flaky tests are caused by a missing or wrong wait. This file covers every
> kind of wait, when to use which, and the typical "works locally / fails on CI"
> traps.

---

## 4.1  Why waits exist

Modern web apps are **asynchronous**:
- AJAX calls populate dropdowns / tables / charts after the page is "loaded".
- Animations (modals fading in, accordions sliding) happen after a click.
- SPAs (React/Angular) only mount components when a route is navigated.

Selenium runs at the speed of the JVM — way faster than human pace — so without
waits it tries to interact with elements that **don't exist yet** or aren't
**interactable yet**. Result: `NoSuchElementException`, `ElementNotInteractableException`,
`StaleElementReferenceException`.

There are **3 kinds of wait** in Selenium + a few helpers:

1. Implicit wait
2. Explicit wait (`WebDriverWait`)
3. Fluent wait (`FluentWait`)
4. Page‑load timeout / Script timeout
5. Hard wait (`Thread.sleep`) — **avoid in production**

---

## 4.2  Implicit wait

Set once on the driver. Selenium will poll the DOM every ~500 ms until the element
is found, up to the timeout, **for every `findElement` call**.

```java
driver.manage().timeouts().implicitlyWait(Duration.ofSeconds(10));
```

Already done in this framework's `BaseClass.configureBrowser()`:
```java
int implicitWait = Integer.parseInt(prop.getProperty("implicitWait"));
getDriver().manage().timeouts().implicitlyWait(Duration.ofSeconds(implicitWait));
```

### Pros
- One‑liner setup.
- Applies globally.

### Cons (important)
- **Only handles "element not in DOM yet"**. Does **not** wait for visibility,
  clickability, text, attribute, etc.
- Selenium 4 docs **explicitly warn against mixing implicit + explicit waits**
  → behaviour becomes unpredictable (the timeouts can compound).

> **Best practice:** keep implicit wait **small (0–5 s)** or **disable it (set 0)**
> and rely on explicit waits everywhere. Many teams set it to 0.

---

## 4.3  Explicit wait — `WebDriverWait` + `ExpectedConditions`

The workhorse of any solid framework. Already used in `ActionDriver`:

```java
WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(explicitWait));
wait.until(ExpectedConditions.elementToBeClickable(by));
```

### The conditions you actually use 90 % of the time

| ExpectedCondition | When to use |
|---|---|
| `presenceOfElementLocated(by)` | Element exists in DOM (might be hidden) |
| `visibilityOfElementLocated(by)` | Exists **and** is visible (display, opacity, size) |
| `visibilityOfAllElementsLocatedBy(by)` | All matched elements are visible (good for option lists) |
| `elementToBeClickable(by)` | Visible **and** enabled — use before `click()` |
| `invisibilityOfElementLocated(by)` | Wait until a spinner / modal disappears |
| `textToBe(by, "Done")` / `textToBePresentInElement…` | Wait until text matches |
| `attributeToBe(el, "aria-expanded", "true")` | Lightning combobox / accordion open |
| `frameToBeAvailableAndSwitchTo(by)` | iframes |
| `numberOfElementsToBe(by, n)` / `numberOfElementsToBeMoreThan(by, n)` | Tables loaded |
| `urlContains("dashboard")` / `titleIs("Home")` | After navigation |
| `alertIsPresent()` | Native JS alerts |
| `stalenessOf(element)` | Wait until old DOM dies (great between page transitions) |

### Real pattern – wait for spinner to disappear, then act
```java
By spinner = By.cssSelector(".loader, .spinner-overlay");
wait.until(ExpectedConditions.invisibilityOfElementLocated(spinner));
wait.until(ExpectedConditions.elementToBeClickable(saveBtn)).click();
```

### Combining conditions (Selenium 4)
```java
wait.until(ExpectedConditions.and(
    ExpectedConditions.visibilityOfElementLocated(saveBtn),
    ExpectedConditions.elementToBeClickable(saveBtn)
));
```

### Custom condition — lambda (very powerful)
```java
wait.until(d -> d.findElements(By.cssSelector("table tbody tr")).size() > 5);
```

---

## 4.4  Fluent wait

Same idea as explicit wait, but you can configure:
- The **polling interval**
- The exceptions to **ignore** while polling
- A custom message

```java
Wait<WebDriver> fluent = new FluentWait<>(driver)
    .withTimeout(Duration.ofSeconds(30))
    .pollingEvery(Duration.ofMillis(250))
    .ignoring(NoSuchElementException.class)
    .ignoring(StaleElementReferenceException.class)
    .withMessage("Dashboard tile never loaded");

WebElement tile = fluent.until(d -> d.findElement(By.id("kpi-tile")));
```

> `WebDriverWait` is actually a subclass of `FluentWait` with sensible defaults
> (poll every 500 ms, ignore `NoSuchElementException`). Use **FluentWait** when:
> - you want **shorter polling** (e.g. 100–250 ms)
> - you want to **ignore additional exceptions** (most common: `StaleElementReferenceException`)
> - you want a **custom failure message**

---

## 4.5  Page Load Timeout & Script Timeout

```java
driver.manage().timeouts()
      .pageLoadTimeout(Duration.ofSeconds(60))
      .scriptTimeout(Duration.ofSeconds(30));
```

- **pageLoadTimeout** → max time `driver.get(url)` or a navigation can take. Throws
  `TimeoutException` if exceeded.
- **scriptTimeout** → max time `executeAsyncScript` can run.

This framework already does it in `configureBrowser()`:
```java
getDriver().manage().timeouts().pageLoadTimeout(Duration.ofSeconds(60));
```

### Wait until `document.readyState === 'complete'`
This framework already exposes a helper in `ActionDriver`:

```java
public void waitForPageLoad(int timeOutInSec) {
    wait.withTimeout(Duration.ofSeconds(timeOutInSec)).until(
        WebDriver -> ((JavascriptExecutor) WebDriver)
                       .executeScript("return document.readyState").equals("complete"));
}
```

> Caveat: `readyState='complete'` only means the **HTML document** finished parsing.
> SPA frameworks (Angular/React) often keep loading data **after** that. For SPAs,
> wait on a **business marker** instead — e.g. "the user avatar is visible" or
> "the spinner is gone".

---

## 4.6  Hard wait (`Thread.sleep`) — when (rarely) to use

```java
Thread.sleep(2000);   // BLOCKS the thread for 2 s no matter what
```

- **Pros:** trivially simple.
- **Cons:** wastes time on fast machines, not enough on slow ones. **Top cause of
  flaky/slow suites.**
- **Acceptable use cases:**
  - 100–300 ms pause between keystrokes for debounced auto‑suggest.
  - Throwaway debugging.
  - When the only "ready" signal is a CSS animation finishing and there is no DOM
    change to wait on.

This framework's `BaseClass.staticWait()` uses `LockSupport.parkNanos` which is
basically a `Thread.sleep`. Treat it as a last resort.

---

## 4.7  Implicit + Explicit together — the trap

Selenium 4 documentation:
> "Do not mix implicit and explicit waits. Doing so can cause unpredictable wait
> times."

What actually happens: when an explicit wait polls and hits `findElement`, the
implicit wait ALSO kicks in for **each** poll — so a `WebDriverWait` of 10 s with
an implicit wait of 10 s can take up to 100 s before timing out.

**Fix:** in CI, set implicit wait to `0` and rely fully on explicit waits.

---

## 4.8  Common interview / real‑world questions

### Q1. "Difference between implicit and explicit wait?"
- Implicit: global, applies to every `findElement`, only checks presence.
- Explicit: targeted, applies to a specific condition, supports any condition
  (visible, clickable, attribute, text, …).

### Q2. "When do we use FluentWait?"
- When we need custom polling, custom ignore‑list, or custom message.
- Most often used to ignore `StaleElementReferenceException` while waiting for a
  table to stabilize.

### Q3. "How do you wait for an Ajax call to finish?"
Several options, in order of preference:
1. Wait for the **business marker** (the actual element you need).
2. Wait for the **spinner / loader to disappear**.
3. JS hook: `wait.until(d -> ((JsExec)d).executeScript("return jQuery.active==0"));`
   (only if jQuery exists).
4. Last resort: poll `document.readyState` for `complete`.

### Q4. "How to wait for page to fully load in Angular/React?"
- `readyState='complete'` is necessary but not sufficient.
- Wait for an element you know is rendered last (e.g. avatar, footer).
- For Angular specifically, you can poll
  `window.getAllAngularTestabilities()[0].isStable()` via JS.

---

## 4.9  Real problems faced & fixes

| # | Problem | Fix |
|---|---------|-----|
| 1 | `ElementClickInterceptedException` | Wait for overlay/spinner to disappear before click |
| 2 | `StaleElementReferenceException` repeatedly | Use FluentWait with `.ignoring(StaleElementReferenceException.class)` and re‑locate inside |
| 3 | Test super slow because of huge implicit wait + explicit wait combined | Set implicit wait to 0 |
| 4 | Page seems loaded but data not ready | Wait on business element / spinner gone, not on `readyState` |
| 5 | Random `TimeoutException` only on Jenkins | Headless renders slower; bump explicit wait via property file, not code |
| 6 | Click works once, fails next time | Animation in flight → use `elementToBeClickable` not just `visibilityOf` |
| 7 | `presenceOfElementLocated` finds it but click fails | Element in DOM but `display:none`. Use `visibilityOf…` |

---

## 4.10  Best‑practice summary

1. **Default to explicit waits.** Use the most specific `ExpectedCondition`
   (`elementToBeClickable` for clicks, `visibilityOf…` for reading text).
2. **Disable or minimize implicit wait** to avoid the compounding bug.
3. **Centralize timeouts in `config.properties`** — this framework already does this
   via `explicitWait`, `implicitWait`. Different envs can override.
4. **Avoid `Thread.sleep`.** If you "really need" it, leave a comment why.
5. **Wait on a business marker, not on `readyState`**, for SPAs.
6. **Always pair "switchTo().frame()" with a wait** — `frameToBeAvailableAndSwitchTo`.
7. **For data‑heavy widgets** (tables, charts) wait on
   `numberOfElementsToBeMoreThan(rows, 0)` or `invisibilityOf(spinner)`.
