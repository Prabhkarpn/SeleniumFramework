# Handling Dropdowns in Selenium WebDriver — Complete Notes

> A single, in-depth reference covering every type of dropdown you will face in
> real automation projects: Select dropdowns, Bootstrap/Lightbox dropdowns,
> Div-based dropdowns, Auto-suggest, Multi-select, and Cascading dropdowns.
> Includes real public URLs to practice on, common issues, root causes,
> solutions, best practices, and interview questions.

---

## Table of Contents

1. [What is a Dropdown?](#1-what-is-a-dropdown)
2. [How to Identify the Type of Dropdown](#2-how-to-identify-the-type-of-dropdown)
3. [Type 1 — Select Dropdown (HTML `<select>`)](#3-type-1--select-dropdown-html-select)
4. [Type 2 — Bootstrap / Lightbox Dropdown](#4-type-2--bootstrap--lightbox-dropdown)
5. [Type 3 — Div-Based / Custom Dropdown](#5-type-3--div-based--custom-dropdown)
6. [Type 4 — Auto-Suggest Dropdown](#6-type-4--auto-suggest-dropdown)
7. [Type 5 — Multi-Select Dropdown](#7-type-5--multi-select-dropdown)
8. [Type 6 — Cascading / Dependent Dropdown](#8-type-6--cascading--dependent-dropdown)
9. [Type 7 — Hidden Dropdown (Display:none)](#9-type-7--hidden-dropdown-displaynone)
10. [Common Issues & Root-Cause Solutions](#10-common-issues--root-cause-solutions)
11. [Best Practices for Dropdown Automation](#11-best-practices-for-dropdown-automation)
12. [Reusable Utility Methods](#12-reusable-utility-methods)
13. [Interview Questions on Dropdowns](#13-interview-questions-on-dropdowns)

---

## 1. What is a Dropdown?

### Definition
A **dropdown** is a UI control that lets the user pick one (or many) values
from a list that "drops down" when the control is clicked. From a developer's
point of view it is just a way to save screen space and constrain user input.

### Why automation testers care
Dropdowns are one of the most common controls in any web app:
- Country / State / City selectors
- Date pickers (Day / Month / Year)
- Filters (Price, Rating, Category)
- Settings (Language, Currency, Theme)

Each dropdown can be **built differently** in HTML, and Selenium's behaviour
changes depending on how it is built. Picking the wrong strategy is the #1
reason automation scripts become flaky on dropdowns.

### How it works under the hood
Browsers do not have a single "dropdown widget". A dropdown is one of:
| Implementation | HTML signature | Selenium approach |
|---|---|---|
| Native HTML | `<select><option>` | `org.openqa.selenium.support.ui.Select` |
| Bootstrap / jQuery | `<button data-toggle="dropdown">` + `<ul>` | Click + WebElement list |
| Custom Div | `<div role="combobox">` + `<div role="listbox">` | JS / Actions / explicit waits |
| Auto-suggest | `<input>` + dynamic `<ul>` | sendKeys + wait + click |

---

## 2. How to Identify the Type of Dropdown

Right-click → Inspect on the dropdown and look at the **outer tag**:

| You see... | It is a... | Use... |
|---|---|---|
| `<select>` … `<option>` | Native Select | `Select` class |
| `<button>` / `<a>` with `data-toggle="dropdown"` and a sibling `<ul>` | Bootstrap | Click + List of `<li>` |
| `<div>` / `<span>` with `role="combobox"` or arbitrary classes | Custom Div | Click + List of children + waits |
| `<input>` whose suggestions appear as you type | Auto-suggest | sendKeys + wait + click |

> **Golden Rule:** Only use the `Select` class when the outer tag is literally
> `<select>`. Using it on anything else throws
> `UnexpectedTagNameException: Element should have been "select" but was ...`

---

## 3. Type 1 — Select Dropdown (HTML `<select>`)

### 3.1 Definition
The native HTML `<select>` element with `<option>` children. Fully supported
by Selenium through the helper class
`org.openqa.selenium.support.ui.Select`.

### 3.2 HTML structure
```html
<select id="country">
    <option value="in">India</option>
    <option value="us">United States</option>
    <option value="uk">United Kingdom</option>
</select>
```

### 3.3 Practice URLs (real, public)
| Site | What to try |
|---|---|
| https://www.lambdatest.com/selenium-playground/select-dropdown-demo | Single + multi `<select>` |
| https://demoqa.com/select-menu | "Old Style Select Menu" section |
| https://www.facebook.com/ (signup) | Day / Month / Year birthday selects |
| https://www.orangehrm.com/  → demo OrangeHRM → PIM module | Job Title, Employment Status |

### 3.4 The `Select` class — full API

```java
import org.openqa.selenium.support.ui.Select;

WebElement dd = driver.findElement(By.id("country"));
Select select = new Select(dd);

// --- Selecting ---
select.selectByVisibleText("India");
select.selectByValue("us");          // matches <option value="us">
select.selectByIndex(2);             // 0-based

// --- De-selecting (multi-select only) ---
select.deselectByVisibleText("India");
select.deselectByValue("us");
select.deselectByIndex(2);
select.deselectAll();

// --- Reading ---
List<WebElement> all = select.getOptions();
List<WebElement> selected = select.getAllSelectedOptions();
WebElement first = select.getFirstSelectedOption();
boolean isMulti = select.isMultiple();
```

### 3.5 Working example — Facebook DOB
```java
driver.get("https://www.facebook.com/r.php");

// Day
Select day = new Select(driver.findElement(By.id("day")));
day.selectByVisibleText("15");

// Month
Select month = new Select(driver.findElement(By.id("month")));
month.selectByValue("8");            // August

// Year
Select year = new Select(driver.findElement(By.id("year")));
year.selectByIndex(25);              // 25 years back from today's listing
```

### 3.6 Iterating to pick a dynamic value
Sometimes the value to pick is decided at runtime (e.g. from a data file).
Iterate through `getOptions()`:

```java
Select s = new Select(driver.findElement(By.id("country")));
String wanted = "United Kingdom";

for (WebElement opt : s.getOptions()) {
    if (opt.getText().trim().equalsIgnoreCase(wanted)) {
        opt.click();
        break;
    }
}
```

### 3.7 Issues you will hit & solutions

| Issue | Root cause | Solution |
|---|---|---|
| `UnexpectedTagNameException: Element should have been "select"` | The element looks like a dropdown but is actually a `<div>` / `<ul>` | Don't use `Select`; use the Div approach (Section 5) |
| `NoSuchElementException` while finding the `<select>` | Page not fully loaded / inside an iframe | Add `WebDriverWait` for `presenceOfElementLocated`, switch into iframe if needed |
| `selectByVisibleText` fails with whitespace | Option text has leading/trailing spaces or non-breaking spaces (`&nbsp;`) | Read `getText()`, `trim()`, compare manually and click |
| `ElementNotInteractableException` | `<select>` is `display:none` or covered by overlay | Scroll into view via JS, close overlay, or use JS `arguments[0].value=...` then dispatch `change` event |
| Selected value not reflected on UI but reflected in DOM | Page uses framework (React/Angular) that ignores native change | Trigger event: `var e=new Event('change',{bubbles:true}); el.dispatchEvent(e);` |

---

## 4. Type 2 — Bootstrap / Lightbox Dropdown

### 4.1 Definition
A **Bootstrap dropdown** is built using a `<button>` (or `<a>`) toggle and a
sibling `<ul>` / `<div>` panel. It looks like a dropdown but is **not** a
`<select>`. The "lightbox" name comes from the panel that visually pops over
the page.

### 4.2 HTML structure
```html
<div class="dropdown">
  <button class="btn dropdown-toggle"
          data-bs-toggle="dropdown" aria-expanded="false">
    Select country
  </button>
  <ul class="dropdown-menu">
    <li><a class="dropdown-item" href="#">India</a></li>
    <li><a class="dropdown-item" href="#">USA</a></li>
    <li><a class="dropdown-item" href="#">UK</a></li>
  </ul>
</div>
```

### 4.3 Practice URLs
| Site | What to try |
|---|---|
| https://www.lambdatest.com/selenium-playground/bootstrap-dropdown-demo | Single, split, nested Bootstrap dropdowns |
| https://getbootstrap.com/docs/5.3/components/dropdowns/ | Official live demos |
| https://demo.guru99.com/test/newtours/register.php | Country dropdown (still a real `<select>` here, but the layout is similar) |

### 4.4 Working example — LambdaTest playground
```java
driver.get("https://www.lambdatest.com/selenium-playground/bootstrap-dropdown-demo");

// 1. Click toggle to open the panel
driver.findElement(By.id("single-button")).click();

// 2. Wait for menu to appear
WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));
wait.until(ExpectedConditions.visibilityOfElementLocated(
        By.cssSelector("ul.dropdown-menu")));

// 3. Click the desired option
List<WebElement> options =
        driver.findElements(By.cssSelector("ul.dropdown-menu li a"));

for (WebElement opt : options) {
    if (opt.getText().trim().equals("Action")) {
        opt.click();
        break;
    }
}
```

### 4.5 The "lightbox" twist
Sometimes the dropdown panel is rendered inside a **modal/lightbox** that is
appended to `<body>` (not inside the parent div). XPath relative to the
trigger will fail. Locate the panel from the document root:

```java
// Wrong - assumes panel is a sibling of the trigger
By.xpath(".//ul[@class='dropdown-menu']/li[text()='India']");

// Right - locate from root
By.xpath("//ul[contains(@class,'dropdown-menu') and not(contains(@style,'display: none'))]" +
         "//a[normalize-space()='India']");
```

### 4.6 Issues & solutions

| Issue | Root cause | Solution |
|---|---|---|
| Click on toggle does nothing | Bootstrap JS not yet attached | Add explicit wait for the toggle to be `elementToBeClickable` |
| Option click happens but value not selected | The visible "selected" element is actually a separate label | After click, also assert/read the label, and `.click()` on the toggle to close the panel if needed |
| `StaleElementReferenceException` while iterating options | Panel re-renders on open/close | Re-locate the list inside the loop, or capture all texts first then click by index |
| Panel is hidden behind another panel | Two dropdowns opened together | Click `body` to close stray panels before opening the next |

---

## 5. Type 3 — Div-Based / Custom Dropdown

### 5.1 Definition
A fully custom dropdown built with `<div>`, `<span>`, `<ul>` and CSS. It can
behave just like a native one but Selenium has **no helper class** for it.
You drive it the way a real user would: click to open, click to choose.

### 5.2 HTML structure (typical)
```html
<div class="custom-select" id="lang">
   <div class="selected">English</div>
   <div class="options" style="display:none">
       <div class="option" data-val="en">English</div>
       <div class="option" data-val="hi">Hindi</div>
       <div class="option" data-val="fr">French</div>
   </div>
</div>
```

### 5.3 Practice URLs
| Site | What to try |
|---|---|
| https://www.makemytrip.com/ | "From" / "To" city pickers (div-based) |
| https://www.spicejet.com/ | Source / Destination |
| https://demoqa.com/select-menu | "Select Value" and "Select One" (React-Select widgets) |
| https://www.jqueryscript.net/demo/Multi-Functional-Select-Box-jQuery-Selectator/ | Pure div select |

### 5.4 Working example — DemoQA "Select Value"
```java
driver.get("https://demoqa.com/select-menu");

// 1. Click the React-Select container to open the panel
WebElement combo = driver.findElement(By.id("withOptGroup"));
combo.click();

// 2. Wait for the list of options to appear
WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));
wait.until(ExpectedConditions.visibilityOfElementLocated(
        By.cssSelector("div[id^='react-select'][id$='-listbox']")));

// 3. Pick the option whose text matches
String want = "Group 1, option 2";
List<WebElement> options =
        driver.findElements(By.cssSelector("div[id^='react-select'] div[id*='option']"));

for (WebElement o : options) {
    if (o.getText().trim().equals(want)) {
        o.click();
        break;
    }
}
```

### 5.5 Working example — MakeMyTrip "From" city
```java
driver.get("https://www.makemytrip.com/");

// Some popups appear; close them first
driver.findElement(By.xpath("//span[@data-cy='closeModal']")).click();

// Click the "From" field (it's a span/label, not an <input>)
driver.findElement(By.xpath("//span[text()='From']")).click();

// A search input now appears inside the popup
WebElement search = driver.findElement(By.id("fromCity"));
search.sendKeys("Delhi");

// Wait for the suggestion list and pick the right one
WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));
wait.until(ExpectedConditions.visibilityOfElementLocated(
        By.cssSelector("ul.react-autosuggest__suggestions-list")));

driver.findElement(By.xpath(
   "//li[contains(@class,'suggestion')]//p[contains(text(),'Delhi')]")).click();
```

### 5.6 Issues & solutions

| Issue | Root cause | Solution |
|---|---|---|
| Click on the "container" doesn't open the panel | The clickable element is a child `<span>` or `<i>` (the arrow) | Locate the actual clickable child, or use `Actions.moveToElement().click()` |
| Options appear, then disappear before click | Animation; using `findElement` too early returns the still-collapsing copy | Wait for `visibilityOfElementLocated` with a longer timeout, then click |
| Option not in DOM until you scroll | Virtualised list (React-Window) loads only visible rows | Type into the search box to filter, or scroll inside the list with JS until the option is rendered |
| Clicking the option does nothing | Real handler is on a parent element | `o.findElement(By.xpath("./..")).click();` or use JS click |

---

## 6. Type 4 — Auto-Suggest Dropdown

### 6.1 Definition
An `<input>` whose suggestion list is generated **dynamically** as the user
types. Examples: Google search, Bing, MakeMyTrip city, Amazon search.

### 6.2 Practice URLs
| Site | What to try |
|---|---|
| https://www.google.com | Search "selenium" → suggestion list |
| https://www.amazon.in | Header search bar |
| https://jqueryui.com/autocomplete/ | The classic learning demo (inside an iframe) |

### 6.3 Working example — Google
```java
driver.get("https://www.google.com");

WebElement box = driver.findElement(By.name("q"));
box.sendKeys("selenium");

// Wait until at least one suggestion is rendered
WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));
wait.until(ExpectedConditions.visibilityOfElementLocated(
        By.xpath("//ul[@role='listbox']//li")));

// Print all suggestions, then click the right one
List<WebElement> suggestions =
        driver.findElements(By.xpath("//ul[@role='listbox']//li"));

for (WebElement s : suggestions) {
    System.out.println(s.getText());
    if (s.getText().contains("selenium webdriver")) {
        s.click();
        break;
    }
}
```

### 6.4 Working example — jQuery UI autocomplete (inside iframe)
```java
driver.get("https://jqueryui.com/autocomplete/");
driver.switchTo().frame(0);                          // critical step

WebElement tag = driver.findElement(By.id("tags"));
tag.sendKeys("ja");

WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));
wait.until(ExpectedConditions.visibilityOfElementLocated(
        By.xpath("//ul[contains(@class,'ui-autocomplete')]/li")));

driver.findElement(By.xpath(
        "//ul[contains(@class,'ui-autocomplete')]/li/div[text()='Java']"))
      .click();
driver.switchTo().defaultContent();
```

### 6.5 Issues & solutions

| Issue | Root cause | Solution |
|---|---|---|
| Suggestions not appearing | App debounces typing; `sendKeys` sent too fast | Type one char at a time with a small wait, or call `sendKeys` then `Thread.sleep(500)` for the API call (better: explicit wait for `visibilityOfElementLocated`) |
| Suggestions disappear when iterating | List re-renders on every keystroke or on focus loss | Capture the list once, copy texts to a `List<String>`, then click by re-locating |
| Wrong suggestion clicked | `contains()` matches multiple items | Use `normalize-space(text())='Exact'` or pick by index after asserting the list |
| Pressed `ENTER` and went to results page | Default form submit | Click the suggestion `<li>` instead of pressing Enter, or use `Keys.ARROW_DOWN` until selected then Enter |

---

## 7. Type 5 — Multi-Select Dropdown

### 7.1 Two flavours

**A. Native `<select multiple>`**
Use the same `Select` class — `isMultiple()` returns `true`.
```java
Select multi = new Select(driver.findElement(By.id("multi-select")));
multi.selectByVisibleText("Apple");
multi.selectByVisibleText("Mango");
multi.deselectByVisibleText("Apple");
multi.deselectAll();
```
Practice URL: https://www.lambdatest.com/selenium-playground/select-dropdown-demo
(scroll to "Multi Select List Demo").

**B. Custom multi-select (chips/tags)**
Built with div + checkboxes (e.g. Select2, react-select multi).
There is no `Select` helper. You click the input → click each option → each
becomes a "chip". You may need to click the `x` on each chip to deselect.

```java
driver.get("https://demoqa.com/select-menu");

// Open the multi-select
WebElement input = driver.findElement(
        By.cssSelector("#selectMenuContainer input"));
input.click();

// Pick "Green"
driver.findElement(By.xpath("//div[text()='Green']")).click();
// Pick "Black"
driver.findElement(By.xpath("//div[text()='Black']")).click();

// Remove "Green" chip
driver.findElement(By.xpath(
   "//div[contains(@class,'multi-value__label') and text()='Green']" +
   "/following-sibling::div")).click();
```

### 7.2 Issues & solutions
| Issue | Root cause | Solution |
|---|---|---|
| `Ctrl+Click` not selecting multiple in Mac | Mac uses `Cmd` not `Ctrl` | Use `Keys.chord` and detect OS, or directly use `Select` API which handles it |
| Selected values lost on form submit | Hidden field not updated | After every click, also `Tab` away to commit, or fire `change` event via JS |

---

## 8. Type 6 — Cascading / Dependent Dropdown

### 8.1 Definition
The options of dropdown B depend on what was selected in dropdown A
(Country → State → City).

### 8.2 Practice URLs
- https://www.spicejet.com/ — From / To (selecting From filters To)
- https://www.redbus.in/ — Source / Destination
- https://www.geeksforgeeks.org/ → Search "country state city dropdown" demos

### 8.3 Key automation rule
**Always wait for the second dropdown to be re-populated before interacting**.
Frameworks usually clear and re-build the second list, so the old options are
stale.

```java
// 1. Pick country
new Select(driver.findElement(By.id("country"))).selectByVisibleText("India");

// 2. Wait until states are loaded (e.g. > 1 option)
WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));
wait.until(d -> new Select(d.findElement(By.id("state")))
                .getOptions().size() > 1);

// 3. Pick state
new Select(driver.findElement(By.id("state"))).selectByVisibleText("Karnataka");
```

### 8.4 Issues & solutions
| Issue | Root cause | Solution |
|---|---|---|
| `StaleElementReferenceException` on second select | The second `<select>` was rebuilt | Re-locate it after the first selection |
| Second list still has old options | AJAX call still in flight | Wait for a known new option to appear, or wait for the spinner to disappear |
| Wrong option chosen | Identical text in both lists | Scope the locator by parent ID |

---

## 9. Type 7 — Hidden Dropdown (display:none)

Some apps style the original `<select>` as `display:none` and render a custom
UI on top. Selenium will throw `ElementNotInteractableException` because the
element is technically not visible.

### Solutions
1. Interact with the **visible custom UI** (Section 5) — preferred.
2. Force-set value with **JavaScriptExecutor**:
```java
WebElement hidden = driver.findElement(By.id("country"));
((JavascriptExecutor) driver).executeScript(
    "arguments[0].style.display='block'; arguments[0].value='in';" +
    "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
    hidden);
```
3. Use the `Select` class **after** un-hiding via JS.

---

## 10. Common Issues & Root-Cause Solutions

| Issue | Root cause | Fix |
|---|---|---|
| `UnexpectedTagNameException: Element should have been "select" but was div` | Used `Select` on a non-`<select>` element | Switch to Div-based handling (Section 5) |
| `ElementNotInteractableException` | Hidden, off-screen, or covered by overlay | `JS scrollIntoView`, close overlay, or JS click |
| `StaleElementReferenceException` | DOM re-rendered after locate | Re-locate inside the loop / use `ExpectedConditions.refreshed(...)` |
| `NoSuchElementException` after dropdown opens | Panel rendered at end of `<body>` | Locate from root `//`, not relative to trigger |
| Click happens but value not picked up | Framework needs `change`/`input` event | Dispatch the event via JS |
| Dropdown opens, then immediately closes | Mouse moved away during animation | Use `Actions.moveToElement(option).click()`; avoid extra `findElement` between hover and click |
| Option text has `\u00A0` (non-breaking space) | Designer used `&nbsp;` | Compare with `text.replace('\u00A0',' ').trim()` |
| Slow dropdown causes flaky tests | Hard `Thread.sleep` | Replace with `WebDriverWait` and a custom condition |
| Inside iframe, nothing is found | You forgot to switch frames | `driver.switchTo().frame(...)` then `defaultContent()` after |

---

## 11. Best Practices for Dropdown Automation

1. **Always inspect first.** Decide between Select / Bootstrap / Div before
   writing code.
2. **Never use `Thread.sleep`.** Replace with `WebDriverWait` + an
   `ExpectedCondition` that proves the dropdown is in the state you need.
3. **Wrap dropdown logic in a Page Object method** —
   `selectCountry(String name)` — and let the page object hide whether it is
   `Select` or div-based.
4. **Centralize utility methods** for div-based dropdowns (see Section 12) so
   every page object reuses one tested implementation.
5. **Validate after selection.** Read back the selected text and assert it.
   This catches "click happened but selection didn't" silently.
6. **For multi-selects, deselect everything first** so tests are independent.
7. **Handle stale elements with `ExpectedConditions.refreshed(...)`** when
   cascading dropdowns rebuild the list.
8. **Never auto-fail** on the first dropdown failure — log the option list so
   the failure tells you what *was* available.

---

## 12. Reusable Utility Methods

Add these to `com.orangehrm.actiondriver.ActionDriver` (or a new
`DropdownUtility` class) so every test/page object reuses them.

```java
public class DropdownUtility {

    private final WebDriver driver;
    private final WebDriverWait wait;

    public DropdownUtility(WebDriver driver, Duration timeout) {
        this.driver = driver;
        this.wait = new WebDriverWait(driver, timeout);
    }

    /** Native <select> by visible text. */
    public void selectByText(By locator, String text) {
        WebElement el = wait.until(
                ExpectedConditions.elementToBeClickable(locator));
        new Select(el).selectByVisibleText(text);
    }

    /** Bootstrap / div-based dropdown. */
    public void selectFromCustomDropdown(By trigger, By optionsLocator,
                                         String wantedText) {
        wait.until(ExpectedConditions.elementToBeClickable(trigger)).click();
        wait.until(ExpectedConditions.visibilityOfElementLocated(optionsLocator));

        List<WebElement> options = driver.findElements(optionsLocator);
        for (WebElement o : options) {
            if (o.getText().trim().equalsIgnoreCase(wantedText)) {
                wait.until(ExpectedConditions.elementToBeClickable(o)).click();
                return;
            }
        }
        throw new NoSuchElementException(
                "Option '" + wantedText + "' not found. Available: " +
                options.stream().map(WebElement::getText).toList());
    }

    /** Auto-suggest: type, wait, click. */
    public void selectFromAutoSuggest(By inputLocator, By suggestionLocator,
                                      String typeText, String wantedText) {
        WebElement input = wait.until(
                ExpectedConditions.elementToBeClickable(inputLocator));
        input.clear();
        input.sendKeys(typeText);
        wait.until(ExpectedConditions.visibilityOfElementLocated(suggestionLocator));

        for (WebElement s : driver.findElements(suggestionLocator)) {
            if (s.getText().trim().equalsIgnoreCase(wantedText)) {
                s.click();
                return;
            }
        }
        throw new NoSuchElementException(
                "Suggestion '" + wantedText + "' not found");
    }

    /** JS fallback — last resort for hidden / problematic <select>. */
    public void selectByValueJS(By locator, String value) {
        WebElement el = driver.findElement(locator);
        ((JavascriptExecutor) driver).executeScript(
            "arguments[0].value=arguments[1];" +
            "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
            el, value);
    }
}
```

---

## 13. Interview Questions on Dropdowns

### A. Conceptual / Beginner
1. What is the `Select` class in Selenium? Which package is it from?
2. Why can't `Select` handle Bootstrap / custom dropdowns?
3. List all methods of `Select` and explain when to use each.
4. What is the difference between `selectByVisibleText`, `selectByValue`, and
   `selectByIndex`?
5. How do you find the currently selected option?
6. What does `isMultiple()` return for a normal `<select>`?
7. How do you get all options of a dropdown?
8. Difference between `getOptions()` and `getAllSelectedOptions()`.

### B. Practical / Mid-level
9.  How would you select an option from a Bootstrap dropdown?
10. How do you handle a dropdown that does not use the `<select>` tag?
11. How do you handle an auto-suggest dropdown like Google?
12. How do you handle dependent (cascading) dropdowns?
13. How will you handle a multi-select where the UI uses checkboxes inside a div?
14. What is `UnexpectedTagNameException`? When does it appear and how to fix?
15. What is `StaleElementReferenceException` and why does it happen with
    cascading dropdowns? How will you fix it?
16. How would you select an option whose value comes from an Excel sheet?
17. How will you verify that a dropdown is sorted alphabetically?
18. How do you handle a dropdown inside an iframe?

### C. Scenario / Senior-level
19. A dropdown is hidden via `display:none` — how will you select a value?
20. Your dropdown list is virtualised (only visible rows in DOM). How do you
    select a value at the bottom?
21. Click on the option works locally but fails on Jenkins — possible reasons?
22. How would you design a generic, reusable utility to handle every type of
    dropdown? Walk me through the API.
23. Same option text appears in two cascading dropdowns — how do you avoid
    XPath ambiguity?
24. The dropdown opens, but `Select` cannot find the option — how do you
    debug?
25. After selecting a value via Selenium, the form submit still says "field
    required". Why and how do you fix it?
26. How do you select a dropdown value when the options are loaded only when
    you scroll inside the list?
27. How would you assert that all 50 US states are present in a dropdown?
28. The same dropdown is built with `<select>` on desktop and a div on mobile
    web — how do you write a single test that works on both?

### D. Coding tasks frequently asked
- Write code to print all options of a `<select>` dropdown.
- Write code to count total options.
- Select the **last** option of a dropdown without knowing its text.
- Select a **random** option, then verify it is selected.
- Select all options of a multi-select, deselect the second one, print
  remaining selected.
- Select "India" from MakeMyTrip "From" city using only XPath.
- Sort the options of a `<select>` and verify they are already sorted.

---

### Quick "type → strategy" cheat-sheet

```
<select>                  -> Select class
<button data-toggle…>+<ul>-> click + list
<div role="combobox">     -> click + waits + click
<input> + dynamic <ul>    -> sendKeys + wait + click
<select multiple>         -> Select class (multi methods)
custom multi w/ chips     -> click each option, click x to deselect
display:none <select>     -> JS executor or interact with custom UI
inside iframe             -> switchTo().frame(...) first
```

---

> **Tip for daily practice:** Bookmark these three links and rotate between
> them every week — they cover 90% of dropdown patterns you'll meet at work.
> 1. https://www.lambdatest.com/selenium-playground/select-dropdown-demo
> 2. https://demoqa.com/select-menu
> 3. https://www.makemytrip.com/
