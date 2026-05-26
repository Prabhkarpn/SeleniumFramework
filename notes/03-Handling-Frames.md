# 3. Handling Frames / iFrames in Selenium

> A **frame / iframe** is essentially "a page inside a page". Selenium's driver, by
> default, only sees the **top‑level** document. To interact with elements inside a
> frame you must explicitly **switch context** into it.

---

## 3.1  What is an iframe and why it exists

```html
<html>
  <body>
     <h1>Main page</h1>
     <iframe id="paymentFrame" src="https://payments.example.com"></iframe>
  </body>
</html>
```

iFrames are used for:
- Embedding 3rd‑party widgets (Stripe / PayPal payment forms, reCAPTCHA, YouTube,
  Google Maps).
- Sandboxing legacy/cross‑origin content (Outlook Web, JIRA editors, Salesforce
  Visualforce pages, ServiceNow forms, TinyMCE / CKEditor editors).
- Module isolation in old enterprise apps.

**Browser sees the outer page and the inner page as two completely separate DOMs.**
That's the whole reason Selenium needs `switchTo().frame(...)`.

---

## 3.2  How to identify a frame

Right‑click the suspicious area → "View frame source" / "Inspect". If you see an
`<iframe …>` ancestor wrapping your target element, it's a frame.

Quick check in dev tools console:
```js
document.getElementsByTagName('iframe').length        // count of iframes
```

In Selenium:
```java
int frameCount = driver.findElements(By.tagName("iframe")).size();
System.out.println("iframes on the page = " + frameCount);
```

> **Symptom that screams "frame!":**
> Your locator is correct (works in the browser console), but Selenium throws
> `NoSuchElementException`. 9 times out of 10 the element is inside an iframe.

---

## 3.3  All ways to switch INTO a frame

### a) By index (least preferred — order can change)
```java
driver.switchTo().frame(0);          // first iframe on the page
driver.switchTo().frame(2);          // third iframe
```

### b) By name or id attribute
```html
<iframe id="paymentFrame" name="payments">…</iframe>
```
```java
driver.switchTo().frame("paymentFrame");      // matches id OR name
```

### c) By WebElement (most reliable)
Best when the iframe has neither id nor name — locate it by any locator and pass it in:

```java
WebElement frameEl = driver.findElement(By.cssSelector("iframe[src*='payments']"));
driver.switchTo().frame(frameEl);
```

### d) Wait + switch (recommended in real frameworks)
The iframe is often added to the DOM **after** an AJAX call. Use the built‑in
expected condition:

```java
new WebDriverWait(driver, Duration.ofSeconds(15))
   .until(ExpectedConditions.frameToBeAvailableAndSwitchTo(
        By.cssSelector("iframe[src*='payments']")));
```

This single line **waits until the frame exists *and* switches into it**.

---

## 3.4  Switching OUT of a frame

```java
driver.switchTo().parentFrame();    // goes 1 level up
driver.switchTo().defaultContent(); // jumps all the way to top-level page
```

> **Rule of thumb:** Whenever you finish work inside a frame, immediately call
> `defaultContent()`. This avoids "I'm still inside the iframe and can't find the
> sidebar button" bugs.

---

## 3.5  Nested frames (frame inside a frame)

```html
<iframe id="outer">
   <iframe id="inner">…</iframe>
</iframe>
```

```java
driver.switchTo().frame("outer");
driver.switchTo().frame("inner");      // now inside inner

// do work …

driver.switchTo().parentFrame();       // back to outer
driver.switchTo().defaultContent();    // back to root
```

You **cannot** jump directly from `outer/inner` to a sibling iframe. You must go up
to default content first, then down again.

---

## 3.6  Reusable wrapper for THIS framework

Add to `ActionDriver.java`:

```java
/** Switch into a frame located by <by> with explicit wait. */
public void switchToFrame(By by) {
    try {
        wait.until(ExpectedConditions.frameToBeAvailableAndSwitchTo(by));
        logger.info("Switched to frame: " + getElementDescription(by));
    } catch (Exception e) {
        logger.error("Unable to switch to frame: " + e.getMessage());
        ExtentManager.logFailure(BaseClass.getDriver(),
            "Unable to switch to frame", e.getMessage());
    }
}

/** Always pair switchToFrame() with this in a finally block. */
public void switchToDefaultContent() {
    try {
        driver.switchTo().defaultContent();
        logger.info("Switched back to default content");
    } catch (Exception e) {
        logger.error("Unable to switch to default content: " + e.getMessage());
    }
}
```

Usage pattern (always in try/finally so we never leak frame context):

```java
try {
    BaseClass.getActionDriver().switchToFrame(By.id("paymentFrame"));
    BaseClass.getActionDriver().enterText(By.id("cardNumber"), "4111111111111111");
    BaseClass.getActionDriver().click(By.id("payNow"));
} finally {
    BaseClass.getActionDriver().switchToDefaultContent();
}
```

---

## 3.7  Frames vs framesets (legacy)

`<frameset>` is HTML4 and deprecated, but you may meet it on **internal banking /
mainframe apps**. Selenium handles them with the same `switchTo().frame()` API.
Just be aware that `frameset` pages don't have a `<body>` element — locating by
relative XPath from `body` will fail at the top level.

---

## 3.8  Real problems faced & solutions

| # | Problem | Cause | Fix |
|---|---------|-------|-----|
| 1 | `NoSuchFrameException` | Iframe not yet in DOM | Use `frameToBeAvailableAndSwitchTo` (waits up to timeout) |
| 2 | After interacting with frame, can't click main page button | Still inside iframe context | Always call `defaultContent()` when done |
| 3 | Iframe has no id/name, only random generated id | Angular generates ids | Locate iframe by `src`, `title`, or relative position; pass `WebElement` |
| 4 | Switched to frame but element still not found | Multiple iframes have same id; switched to wrong one | Use a more specific locator (`src*=`, `title=`) |
| 5 | TinyMCE / CKEditor editor not accepting text | The editable area is inside its own iframe (`tinymce_ifr`) | `switchTo().frame("tinymce_ifr")` then `sendKeys` to `body` |
| 6 | Test fails on Salesforce classic but works in Lightning | Classic uses Visualforce iframes heavily | Inspect carefully; sometimes 2 nested frames |
| 7 | reCAPTCHA cannot be clicked | Always inside an iframe + cross‑origin | Switch to the recaptcha iframe; for tests, ask devs to disable it in QA env |
| 8 | "ScriptTimeout" when running inside frame | `executeAsyncScript` called against wrong context | Switch to required frame first, *then* run JS |

---

## 3.9  Worked example — TinyMCE rich‑text editor

TinyMCE's editable surface is a literal iframe with id `…_ifr`. To type into it:

```java
WebDriver driver = BaseClass.getDriver();
WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));

wait.until(ExpectedConditions.frameToBeAvailableAndSwitchTo(
    By.cssSelector("iframe[id$='_ifr']")));

driver.findElement(By.tagName("body")).sendKeys("Hello from automation!");

driver.switchTo().defaultContent();        // ALWAYS come back
driver.findElement(By.id("submitPost")).click();
```

---

## 3.10  Worked example — Stripe payment iframe

```java
// Stripe wraps card input in nested iframes
driver.switchTo().frame(driver.findElement(
    By.cssSelector("iframe[name^='__privateStripeFrame']")));
driver.findElement(By.cssSelector("input[name='cardnumber']"))
      .sendKeys("4242424242424242");
driver.switchTo().defaultContent();
```

---

## 3.11  Quick interview answer

> *"Selenium operates at one DOM at a time. If the element is inside an `<iframe>`,
> I switch context using `driver.switchTo().frame(...)`. I prefer
> `frameToBeAvailableAndSwitchTo` because it waits until the frame is present.
> Once the work in the frame is done, I always call
> `driver.switchTo().defaultContent()` to come back, otherwise the next click on the
> main page will fail. For nested frames I switch level by level; for siblings I go
> back to default content first. The most common mistakes I've seen: forgetting to
> exit the frame, hardcoding `frame(0)` when the order changes, and not using a
> wait — the iframe may load after the page."*
