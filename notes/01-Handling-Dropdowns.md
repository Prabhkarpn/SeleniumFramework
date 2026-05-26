# 1. Handling Dropdowns in Selenium

> Most modern UIs (Salesforce Lightning, ServiceNow, Angular/React Material UI, Ant
> Design, PrimeNG, AG‑Grid filters, etc.) **do not use the HTML `<select>` tag anymore**.
> They render dropdowns as `<div>`, `<ul><li>` or `<input role="combobox">` for styling
> flexibility. The classic `Select` class **will not work** there. This is the single
> most common interview question on this topic.

---

## 1.1  Types of dropdowns you will face in real projects

| Type | HTML Pattern | Example Apps |
|------|--------------|--------------|
| **Standard / native** | `<select><option>…</option></select>` | OrangeHRM old screens, simple PHP/JSP apps |
| **Custom div dropdown** | `<div class="dropdown"><ul><li>…</li></ul></div>` | Most React/Angular admin panels |
| **Combobox (typeable)** | `<input role="combobox"> + <ul role="listbox">` | Salesforce Lightning, ServiceNow |
| **Auto‑suggest / search** | input fires AJAX, options appear after typing | Google search, Amazon, Flipkart |
| **Multi‑select with chips** | each selected value shown as a removable chip | Jira labels, Salesforce multi‑picklist |
| **Hidden select (Bootstrap‑select)** | real `<select>` is hidden, fake UI shown | Older Bootstrap apps |
| **Cascading dropdown** | second dropdown depends on first | Country → State → City |

---

## 1.2  Native `<select>` — the easy case

Use the **`Select`** class from `org.openqa.selenium.support.ui.Select`.

```java
import org.openqa.selenium.support.ui.Select;

WebElement countryEl = driver.findElement(By.id("country"));
Select country = new Select(countryEl);

// 3 ways to choose
country.selectByVisibleText("India");
country.selectByValue("IN");
country.selectByIndex(2);

// helpful APIs
country.isMultiple();                       // true / false
List<WebElement> all = country.getOptions();
WebElement first    = country.getFirstSelectedOption();
country.deselectAll();                      // only multi-select
```

**How to confirm it is a native `<select>`:**
Inspect element → if the **tag name is literally `select`**, use `Select`. If it is
`div`, `ul`, `input` or anything else → it is a **custom dropdown** (next section).

---

## 1.3  Custom `div / ul / li` dropdowns (the real‑world case)

Pattern in HTML:

```html
<div class="dropdown" id="country-dd">
   <button class="dropdown-toggle">Select Country</button>
   <ul class="dropdown-menu" style="display:none">
       <li>India</li>
       <li>USA</li>
       <li>UK</li>
   </ul>
</div>
```

The `<ul>` is hidden until you click the toggle. So the recipe is **always 2 steps**:

```java
public void selectFromCustomDropdown(By dropdownToggle, By optionsLocator, String value) {
    WebDriver driver = BaseClass.getDriver();
    WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(15));

    // Step 1: open the dropdown
    wait.until(ExpectedConditions.elementToBeClickable(dropdownToggle)).click();

    // Step 2: wait for ALL options to render, then iterate
    List<WebElement> options =
        wait.until(ExpectedConditions.visibilityOfAllElementsLocatedBy(optionsLocator));

    for (WebElement option : options) {
        if (option.getText().trim().equalsIgnoreCase(value)) {
            option.click();
            return;
        }
    }
    throw new NoSuchElementException("Option [" + value + "] not found in dropdown");
}
```

Usage:

```java
selectFromCustomDropdown(
    By.cssSelector("#country-dd .dropdown-toggle"),
    By.cssSelector("#country-dd ul.dropdown-menu li"),
    "India");
```

### Smarter version – click the option directly via XPath text match
Iterating is fine, but a **single XPath** is faster and more readable.

```java
driver.findElement(By.cssSelector("#country-dd .dropdown-toggle")).click();
By option = By.xpath("//ul[contains(@class,'dropdown-menu')]//li[normalize-space(text())='India']");
new WebDriverWait(driver, Duration.ofSeconds(10))
    .until(ExpectedConditions.elementToBeClickable(option))
    .click();
```

Why `normalize-space(text())='India'`?
Real DOM often has hidden whitespace / `&nbsp;` around the label. `normalize-space`
trims them so the match is reliable.

---

## 1.4  Salesforce Lightning combobox – the famous one

In Salesforce Lightning the dropdown looks like:

```html
<lightning-combobox>
   <input role="combobox"
          aria-controls="dropdown-element-7"
          aria-expanded="false"
          placeholder="--None--"/>
   <div id="dropdown-element-7" role="listbox" style="display:none">
       <lightning-base-combobox-item data-value="hot">  Hot </lightning-base-combobox-item>
       <lightning-base-combobox-item data-value="warm"> Warm </lightning-base-combobox-item>
       <lightning-base-combobox-item data-value="cold"> Cold </lightning-base-combobox-item>
   </div>
</lightning-combobox>
```

Things that are different from a normal dropdown:

- The `<input>` is **read‑only**, you cannot `sendKeys`. You **must click** it to open.
- The listbox uses `role="listbox"` / `role="option"` (great locator hints).
- Options are not direct children of input – they are rendered in a sibling/portal node.
- `aria-expanded` flips `false → true` when the dropdown opens. **Use that as your wait
  condition.**

### Production code:

```java
public void selectLightningCombobox(String labelOrPlaceholder, String optionText) {
    WebDriver driver = BaseClass.getDriver();
    WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(20));

    // 1. Locate the combobox via its label/placeholder (most stable in SF)
    By combo = By.xpath(
        "//lightning-combobox[.//label[normalize-space()='" + labelOrPlaceholder + "']]" +
        "//input[@role='combobox']");

    WebElement comboEl = wait.until(ExpectedConditions.elementToBeClickable(combo));
    comboEl.click();

    // 2. Wait for aria-expanded='true' → guarantees listbox is open
    wait.until(ExpectedConditions.attributeToBe(comboEl, "aria-expanded", "true"));

    // 3. Click the option using role=option
    By option = By.xpath(
        "//lightning-base-combobox-item[.//span[normalize-space()='" + optionText + "']]");
    wait.until(ExpectedConditions.elementToBeClickable(option)).click();

    // 4. Verify
    wait.until(ExpectedConditions.attributeContains(comboEl, "value", optionText));
}
```

> **Interview tip:** When asked "How do you handle Salesforce dropdowns?" → say:
> *"Lightning components don't expose a real `<select>`, they render a `div` with
> `role="combobox"` and a portal `listbox`. I click the combobox, wait for
> `aria-expanded='true'`, then click the option using `role='option'` or
> `lightning-base-combobox-item`. I never use `Select` for Lightning."*

---

## 1.5  Auto‑suggest / typeahead dropdowns (Google, Flipkart, Amazon)

Behaviour:
- You **must type** something first → an AJAX call returns the suggestions.
- The suggestion list is created **dynamically** in the DOM after each keystroke.

```java
public void selectFromAutoSuggest(By inputBox, String partialText, String fullText) {
    WebDriver driver = BaseClass.getDriver();
    WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(15));

    WebElement input = wait.until(ExpectedConditions.elementToBeClickable(inputBox));
    input.clear();
    input.sendKeys(partialText);                       // triggers AJAX

    // wait for at least one suggestion to render
    By suggestion = By.xpath(
        "//ul[contains(@class,'suggestions')]//li[contains(normalize-space(),'" + fullText + "')]");
    wait.until(ExpectedConditions.elementToBeClickable(suggestion)).click();
}
```

### Problem faced #1 – stale element after typing
The DOM list is **destroyed and re‑created on every keystroke**. If you typed slowly
or the test sleeps in the middle, the previously located `<li>` becomes stale.
**Fix:** locate the option `By` reference, not a cached `WebElement`. The wait above
already does that correctly.

### Problem faced #2 – the suggestion never appears in headless mode
Some sites debounce input — they fire the AJAX only after **300 ms of no typing**.
If you `sendKeys` too fast, the request is cancelled.
**Fix:** type character by character with a tiny pause:
```java
for (char c : partialText.toCharArray()) {
    input.sendKeys(String.valueOf(c));
    Thread.sleep(80);    // OR Actions#pause(Duration.ofMillis(80))
}
```

---

## 1.6  Multi‑select dropdowns

### a) Native `<select multiple>`
```java
Select skills = new Select(driver.findElement(By.id("skills")));
skills.selectByVisibleText("Java");
skills.selectByVisibleText("Selenium");
skills.selectByVisibleText("TestNG");
// later
skills.deselectByVisibleText("TestNG");
skills.deselectAll();
```

### b) Custom multi‑select (Jira labels, Salesforce multi‑picklist, react‑select)

Each selection becomes a chip. You usually have to:

```java
public void selectMultipleValues(By openBtn, By optionXPathTemplate, List<String> values) {
    WebDriver driver = BaseClass.getDriver();
    WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(15));

    for (String v : values) {
        // open dropdown each time (some UIs close after 1 selection)
        wait.until(ExpectedConditions.elementToBeClickable(openBtn)).click();

        By option = By.xpath(String.format(optionXPathTemplate.toString(), v));
        wait.until(ExpectedConditions.elementToBeClickable(option)).click();
    }
}
```

### Problem faced – dropdown closes after first selection
Some libraries (`react-select` default) close the menu after every choice.
**Fix:** either re‑open the dropdown for each value (above) **or** hold down the
modifier the library expects, **or** pass a `closeMenuOnSelect={false}` prop in dev –
but as testers we control only the first option.

---

## 1.7  Hidden / Bootstrap‑select dropdowns

These look custom but the **real `<select>` is in DOM with `style="display:none"`**.
`Select` class **fails** because Selenium refuses to interact with hidden elements.

**Fix using JavaScriptExecutor:**

```java
WebElement hiddenSelect = driver.findElement(By.id("country"));
JavascriptExecutor js = (JavascriptExecutor) driver;
js.executeScript("arguments[0].style.display='block';", hiddenSelect);
new Select(hiddenSelect).selectByVisibleText("India");
```

Or simply ignore the hidden select and click the **fake UI** like a custom dropdown
(section 1.3).

---

## 1.8  Cascading dropdowns (Country → State → City)

The trick is **wait for the second dropdown to be enabled / populated** before
selecting:

```java
selectFromCustomDropdown(countryToggle, countryOpts, "India");

// State dropdown will be re-rendered. Wait until it has more than 1 option.
wait.until(driver -> driver.findElements(stateOpts).size() > 1);

selectFromCustomDropdown(stateToggle, stateOpts, "Karnataka");
```

---

## 1.9  How to integrate into THIS framework (`ActionDriver`)

Add a generic helper in `ActionDriver.java`:

```java
/** Generic custom-dropdown helper for div/ul/li widgets */
public void selectCustomDropdown(By toggle, By optionsLocator, String value) {
    try {
        applyBorder(toggle, "green");
        waitForElementToBeClickable(toggle);
        driver.findElement(toggle).click();

        List<WebElement> options =
            wait.until(ExpectedConditions.visibilityOfAllElementsLocatedBy(optionsLocator));

        for (WebElement opt : options) {
            if (opt.getText().trim().equalsIgnoreCase(value)) {
                opt.click();
                ExtentManager.logStep("Selected '" + value + "' from custom dropdown");
                logger.info("Selected '" + value + "' from custom dropdown");
                return;
            }
        }
        throw new NoSuchElementException("Option not found: " + value);
    } catch (Exception e) {
        applyBorder(toggle, "red");
        ExtentManager.logFailure(BaseClass.getDriver(),
            "Custom dropdown failed", e.getMessage());
        logger.error("Custom dropdown failed: " + e.getMessage());
    }
}
```

---

## 1.10  Summary — interview cheat‑sheet

| Scenario | Tool / Approach |
|----------|-----------------|
| `<select>` tag | `Select` class |
| `<div>` / `<ul><li>` | click toggle → wait for options → iterate / XPath text match |
| `role="combobox"` / Lightning | click input → wait `aria-expanded='true'` → click `role="option"` |
| Auto‑suggest | `sendKeys` partial → wait → click suggestion |
| Multi‑select (custom) | loop, possibly re‑open between picks |
| Hidden `<select>` | JS `display='block'` then `Select`, **or** automate the fake UI |
| Cascading | wait until child dropdown is populated/enabled |

---

## 1.11  Most common problems & fixes (quick reference)

| Problem | Root cause | Fix |
|---------|-----------|-----|
| `ElementNotInteractableException` | Element is hidden / behind overlay | Wait for `elementToBeClickable`, scroll into view via JS |
| `StaleElementReferenceException` | DOM re‑rendered (especially auto‑suggest) | Re‑locate using `By`, never cache `WebElement` |
| Option not found although visible | Whitespace / `&nbsp;` in text | Use `normalize-space()` in XPath |
| `Select` class throws `UnexpectedTagNameException` | Element is not `<select>` | It's a custom dropdown – use section 1.3 / 1.4 |
| Dropdown closes before option click | React‑select style auto‑close | Re‑open inside loop, or click option **inside the listbox region** quickly |
| Works locally, fails in headless | UI not fully painted | Use explicit waits, NOT `Thread.sleep`; set window size |
