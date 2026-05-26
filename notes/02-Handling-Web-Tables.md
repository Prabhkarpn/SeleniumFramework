# 2. Handling Web Tables & Dynamic Web Tables

> A "web table" is any tabular data on a page. The challenge is rarely the *static* table.
> Real projects always have **pagination, sorting, filtering, lazy loading and dynamic
> column counts**. This file covers all of them with code.

---

## 2.1  Anatomy of an HTML table

```html
<table id="employees">
  <thead>
    <tr>
      <th>ID</th><th>Name</th><th>Dept</th><th>Action</th>
    </tr>
  </thead>
  <tbody>
    <tr><td>1</td><td>Prabhakar</td><td>QA</td><td><button>Edit</button></td></tr>
    <tr><td>2</td><td>John</td>     <td>Dev</td><td><button>Edit</button></td></tr>
    …
  </tbody>
</table>
```

Standard tag mapping you must memorize:

| HTML tag | Meaning | Typical XPath |
|----------|---------|---------------|
| `<table>` | the whole table | `//table[@id='employees']` |
| `<tr>` | a row | `//table//tbody/tr` |
| `<th>` | header cell | `//table//thead//th` |
| `<td>` | data cell | `//tr/td[2]` |

> **Note:** Modern apps (AG‑Grid, Material Table, Salesforce DataTable) often use
> `<div role="row">` / `<div role="cell">` instead of real `<tr>/<td>`. The same
> *strategies* below apply, just swap the locators. Use `role="row"` / `role="cell"`.

---

## 2.2  Static table – read all data

```java
public List<List<String>> readTable(By tableLocator) {
    WebDriver driver = BaseClass.getDriver();
    List<WebElement> rows = driver.findElements(
        new ByChained(tableLocator, By.cssSelector("tbody tr")));

    List<List<String>> data = new ArrayList<>();
    for (WebElement row : rows) {
        List<WebElement> cells = row.findElements(By.tagName("td"));
        List<String> rowData = new ArrayList<>();
        for (WebElement c : cells) rowData.add(c.getText().trim());
        data.add(rowData);
    }
    return data;
}
```

### Get total rows / columns
```java
int rowCount = driver.findElements(By.cssSelector("#employees tbody tr")).size();
int colCount = driver.findElements(By.cssSelector("#employees thead th")).size();
```

### Read a specific cell (row 3, column 2)
```java
String name = driver.findElement(
    By.cssSelector("#employees tbody tr:nth-child(3) td:nth-child(2)")).getText();
```

---

## 2.3  Find a row by value and click action button (THE classic interview question)

> Question: *"In a list of 100 employees, find the row where name is 'John' and click
> its Edit button."*

```java
public void clickActionForRow(String columnHeader, String value, String actionName) {
    WebDriver driver = BaseClass.getDriver();

    // 1. Find the column index dynamically (don't hardcode)
    By header = By.xpath(
        "//table[@id='employees']//thead//th[normalize-space()='" + columnHeader + "']");
    int colIndex = getElementIndex(header);    // 1-based

    // 2. Build XPath to the row whose td at that index = value
    By targetRow = By.xpath(
        "//table[@id='employees']//tbody//tr[td[" + colIndex + "][normalize-space()='" + value + "']]");

    // 3. Inside that row, click the action button by its label
    By actionBtn = By.xpath(
        "//table[@id='employees']//tbody//tr[td[" + colIndex + "][normalize-space()='" + value + "']]" +
        "//button[normalize-space()='" + actionName + "']");

    new WebDriverWait(driver, Duration.ofSeconds(10))
        .until(ExpectedConditions.elementToBeClickable(actionBtn))
        .click();
}

private int getElementIndex(By header) {
    WebDriver driver = BaseClass.getDriver();
    List<WebElement> headers = driver.findElements(
        By.xpath("//table[@id='employees']//thead//th"));
    for (int i = 0; i < headers.size(); i++) {
        if (headers.get(i).getText().trim().equalsIgnoreCase(
                driver.findElement(header).getText().trim())) {
            return i + 1;     // XPath is 1-based
        }
    }
    throw new NoSuchElementException("Header not found");
}
```

> **Why dynamic column index?** UI teams *love* to reorder columns. Hardcoding
> `td[3]` will break next sprint. Looking up the column by header name keeps the
> test stable.

---

## 2.4  Dynamic web tables with **PAGINATION**

> Real scenario: *the value you need is on page 3 of 12, you must search across all pages.*

There are typically **3 styles** of pagination you will face:

### Style A – numbered pages (1, 2, 3, …, Next)

```java
public boolean clickRowAcrossPages(String name, String action) {
    WebDriver driver = BaseClass.getDriver();
    WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));

    while (true) {
        // search current page
        List<WebElement> rows = driver.findElements(
            By.xpath("//table[@id='employees']//tbody//tr"));
        for (WebElement r : rows) {
            if (r.findElements(By.tagName("td")).get(1).getText().trim().equalsIgnoreCase(name)) {
                r.findElement(By.xpath(".//button[normalize-space()='" + action + "']")).click();
                return true;
            }
        }

        // go next, if possible
        WebElement next = driver.findElement(By.cssSelector(".pagination .next"));
        if ("true".equals(next.getDomAttribute("aria-disabled"))
                || next.getDomAttribute("class").contains("disabled")) {
            return false;        // exhausted all pages, name not found
        }

        // capture first row text to detect page change
        String firstBefore = rows.get(0).getText();
        next.click();
        wait.until(ExpectedConditions.not(
            ExpectedConditions.textToBe(
                By.cssSelector("#employees tbody tr:first-child"), firstBefore)));
    }
}
```

> **Important trick — *"Wait until the first row text changes"***. After clicking
> Next, the AJAX call takes time. If you don't wait, you re‑scan the same page and
> miss the value or get StaleElement. The cheapest reliable wait is "first row text
> changed" or "loader gone".

### Style B – Next / Previous only

Same as above, just remove the page‑number logic; loop until Next is disabled.

### Style C – Infinite scroll / "Load more"

The table grows as you scroll. Use JS to scroll the container or click "Load more"
until the search value appears:

```java
public boolean findInInfiniteScroll(String name) {
    WebDriver driver = BaseClass.getDriver();
    JavascriptExecutor js = (JavascriptExecutor) driver;

    int previousCount = -1;
    while (true) {
        List<WebElement> rows = driver.findElements(By.cssSelector("#employees tbody tr"));
        for (WebElement r : rows) {
            if (r.getText().contains(name)) {
                ((JavascriptExecutor) driver)
                    .executeScript("arguments[0].scrollIntoView({block:'center'});", r);
                r.findElement(By.tagName("button")).click();
                return true;
            }
        }
        if (rows.size() == previousCount) return false;   // stopped growing → end of list
        previousCount = rows.size();

        // scroll last row into view to trigger lazy load
        js.executeScript("arguments[0].scrollIntoView();", rows.get(rows.size() - 1));
        new WebDriverWait(driver, Duration.ofSeconds(5))
            .until(d -> d.findElements(By.cssSelector("#employees tbody tr")).size() > rows.size());
    }
}
```

### The exact scenario from the question
> "Sometimes the data is not on the first page; it appears only on page 2 or 3."

That is *exactly* Style A above. The two key insights:

1. **Don't `Thread.sleep`** between page clicks. Use the *"first row text changed"*
   wait — it's deterministic.
2. **Don't cache `WebElement` references** across pages. The DOM is replaced every time
   you click Next → all old `WebElement`s become **stale**. Re‑locate inside the loop.

---

## 2.5  Dynamic tables with **SEARCH / FILTER**

If the page has a search box, that is **always faster and more stable** than walking
pages:

```java
driver.findElement(By.id("tableSearch")).sendKeys("John");
By targetRow = By.xpath(
    "//table[@id='employees']//tbody//tr[td[normalize-space()='John']]");
new WebDriverWait(driver, Duration.ofSeconds(8))
    .until(ExpectedConditions.visibilityOfElementLocated(targetRow));
```

> **Best practice:** if the table has a search/filter feature, **always use it** in
> tests. It is one network call vs N pagination clicks.

---

## 2.6  Sorting – verify a column is sorted

```java
public boolean isColumnSortedAsc(String header) {
    int idx = getElementIndex(
        By.xpath("//thead//th[normalize-space()='" + header + "']"));
    List<WebElement> cells = BaseClass.getDriver().findElements(
        By.xpath("//tbody//tr/td[" + idx + "]"));

    List<String> actual = cells.stream()
        .map(c -> c.getText().trim())
        .collect(Collectors.toList());

    List<String> expected = new ArrayList<>(actual);
    Collections.sort(expected, String.CASE_INSENSITIVE_ORDER);

    return actual.equals(expected);
}
```

For numeric / date columns, parse before comparing:

```java
List<Integer> nums = actual.stream().map(Integer::parseInt).collect(Collectors.toList());
boolean asc = IntStream.range(0, nums.size() - 1).allMatch(i -> nums.get(i) <= nums.get(i + 1));
```

---

## 2.7  Tables built with `<div role="grid">` (AG‑Grid, Salesforce, Material)

Same logic — different locators:

```java
List<WebElement> rows = driver.findElements(By.cssSelector("[role='row']"));
for (WebElement r : rows) {
    List<WebElement> cells = r.findElements(By.cssSelector("[role='gridcell'], [role='cell']"));
    …
}
```

For AG‑Grid specifically:
- The grid only renders **visible rows** (virtualization) — rows below the fold
  literally do not exist in DOM.
- To reach them, scroll the **grid body** (`.ag-body-viewport`) using JS:

```java
js.executeScript(
    "document.querySelector('.ag-body-viewport').scrollTop += 400;");
```

Then re‑query rows. This is the common "row 200 doesn't exist" problem — it's not a
bug, the row was simply not rendered yet.

---

## 2.8  Real problems faced & solutions (interview gold)

| # | Problem | Why | Solution |
|---|---------|-----|----------|
| 1 | `StaleElementReferenceException` after clicking Next | DOM rebuilt | Re‑locate elements inside the loop, never cache rows |
| 2 | Search returns 0 results although visible | Search is debounced (300 ms) | Wait for spinner to disappear / row count > 0 |
| 3 | XPath `td[3]` breaks after column reorder | Hardcoded index | Compute index dynamically from header text |
| 4 | AG‑Grid: row index 100 not found | Virtualized rendering | Scroll body via JS until row appears |
| 5 | Pagination loop never ends | "Next" never gets a `disabled` attribute | Compare current page text to previous; if same → stop |
| 6 | Test passes locally, fails on Jenkins | Different page size / resolution | Set fixed `--window-size=1920,1080` in headless |
| 7 | `getText()` returns "" on a cell with `<input value="X">` | text is in `value`, not text node | Use `getDomAttribute("value")` or `getAttribute("value")` |
| 8 | Total rows shown wrongly | Counting hidden filtered rows | Filter only visible rows: `tr:not([hidden])` |

---

## 2.9  Helper to plug into THIS framework

Add to `ActionDriver.java`:

```java
/** Click an action button on the row whose <colHeader> column equals <cellValue>. */
public void clickRowAction(By tableRoot, String colHeader, String cellValue, String actionLabel) {
    WebDriver driver = BaseClass.getDriver();
    try {
        // Resolve column index from header name
        List<WebElement> headers = driver.findElements(
            new ByChained(tableRoot, By.cssSelector("thead th")));
        int colIdx = -1;
        for (int i = 0; i < headers.size(); i++) {
            if (headers.get(i).getText().trim().equalsIgnoreCase(colHeader)) {
                colIdx = i + 1; break;
            }
        }
        if (colIdx == -1) throw new NoSuchElementException("Header missing: " + colHeader);

        By btn = By.xpath(
            "(.//tbody/tr[td[" + colIdx + "][normalize-space()='" + cellValue + "']]" +
            "//button[normalize-space()='" + actionLabel + "'])[1]");

        wait.until(ExpectedConditions.elementToBeClickable(btn)).click();
        logger.info("Clicked '" + actionLabel + "' for " + colHeader + "=" + cellValue);
    } catch (Exception e) {
        logger.error("clickRowAction failed: " + e.getMessage());
        ExtentManager.logFailure(driver, "Row action failed", e.getMessage());
    }
}
```

---

## 2.10  Summary cheat‑sheet

- **Read row/column count** → `findElements().size()`
- **Specific cell** → `tr:nth-child(N) td:nth-child(M)`
- **Find row by value** → XPath with `[td[idx][normalize-space()='val']]`
- **Pagination** → loop, re‑locate, wait for first‑row text change
- **Infinite scroll** → JS scroll last row into view, wait for new rows
- **Always prefer** the table's own search box over walking pages
- **AG‑Grid / Material grid** → use `role` attributes and grid‑body scroll
