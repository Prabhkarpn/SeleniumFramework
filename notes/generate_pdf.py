#!/usr/bin/env python3
"""
Pure-Python PDF generator (no external dependencies).
Generates a formatted PDF from structured content using raw PDF commands.
"""
import zlib
import datetime

class SimplePDF:
    def __init__(self):
        self.objects = []
        self.pages = []
        self.current_page_content = []
        self.page_height = 842  # A4
        self.page_width = 595
        self.margin_left = 50
        self.margin_right = 50
        self.margin_top = 60
        self.margin_bottom = 60
        self.y = self.page_height - self.margin_top
        self.line_height = 14
        self.font_size = 10
        self.current_font = "F1"  # Helvetica


    def _escape(self, text):
        return text.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')

    def _usable_width(self):
        return self.page_width - self.margin_left - self.margin_right

    def _check_page_break(self, needed=20):
        if self.y < self.margin_bottom + needed:
            self._end_page()
            self._start_page()

    def _start_page(self):
        self.current_page_content = []
        self.y = self.page_height - self.margin_top
        # Set default font
        self.current_page_content.append(f"BT /F1 {self.font_size} Tf ET")

    def _end_page(self):
        self.pages.append("\n".join(self.current_page_content))

    def set_font(self, font_key, size):
        self.current_font = font_key
        self.font_size = size
        self.line_height = size + 4
        self.current_page_content.append(f"BT /{font_key} {size} Tf ET")


    def write_text(self, text, x=None, bold=False, size=None):
        if size:
            self.set_font("F2" if bold else "F1", size)
        elif bold:
            self.set_font("F2", self.font_size)
        if x is None:
            x = self.margin_left
        self._check_page_break()
        escaped = self._escape(text)
        self.current_page_content.append(
            f"BT /{self.current_font} {self.font_size} Tf "
            f"{x} {self.y} Td ({escaped}) Tj ET"
        )
        self.y -= self.line_height

    def write_line(self):
        self._check_page_break()
        self.current_page_content.append(
            f"0.7 0.7 0.7 RG 0.5 w "
            f"{self.margin_left} {self.y} m "
            f"{self.page_width - self.margin_right} {self.y} l S"
        )
        self.y -= 8

    def blank_line(self):
        self.y -= self.line_height


    def write_wrapped(self, text, x=None, bold=False, indent=0):
        if x is None:
            x = self.margin_left + indent
        max_chars = int((self._usable_width() - indent) / (self.font_size * 0.5))
        words = text.split()
        line = ""
        for word in words:
            test = line + " " + word if line else word
            if len(test) > max_chars:
                if line:
                    self.write_text(line, x, bold)
                line = word
            else:
                line = test
        if line:
            self.write_text(line, x, bold)

    def title(self, text):
        self.blank_line()
        self.set_font("F2", 18)
        self.write_wrapped(text, bold=True)
        self.set_font("F1", 10)
        self.write_line()
        self.blank_line()

    def heading2(self, text):
        self._check_page_break(30)
        self.blank_line()
        self.set_font("F2", 13)
        self.write_text(text, bold=True)
        self.set_font("F1", 10)


    def heading3(self, text):
        self._check_page_break(25)
        self.blank_line()
        self.set_font("F2", 11)
        self.write_text(text, bold=True)
        self.set_font("F1", 10)

    def bullet(self, text):
        self._check_page_break()
        self.write_text("*", self.margin_left)
        self.y += self.line_height  # go back up
        self.write_wrapped(text, indent=15)

    def code_block(self, lines):
        self._check_page_break(len(lines) * 10 + 10)
        # background
        h = len(lines) * 10 + 8
        if self.y - h < self.margin_bottom:
            self._end_page()
            self._start_page()
            h = min(h, self.y - self.margin_bottom)
        self.current_page_content.append(
            f"0.93 0.93 0.93 rg "
            f"{self.margin_left - 5} {self.y - h + 5} "
            f"{self._usable_width() + 10} {h} re f"
        )
        self.current_page_content.append("0 0 0 rg")
        self.set_font("F3", 8)
        for line in lines:
            self._check_page_break()
            escaped = self._escape(line[:100])  # truncate long lines
            self.current_page_content.append(
                f"BT /F3 8 Tf {self.margin_left} {self.y} Td ({escaped}) Tj ET"
            )
            self.y -= 10
        self.set_font("F1", 10)
        self.blank_line()


    def build(self, filename):
        # Finalize last page
        self._end_page()

        # Build PDF structure
        pdf_objects = []

        # Object 1: Catalog
        pdf_objects.append("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj")

        # Object 2: Pages (will reference page objects)
        page_obj_nums = list(range(4, 4 + len(self.pages)))
        kids = " ".join(f"{n} 0 R" for n in page_obj_nums)
        pdf_objects.append(
            f"2 0 obj\n<< /Type /Pages /Kids [{kids}] "
            f"/Count {len(self.pages)} >>\nendobj"
        )

        # Object 3: Font resources
        pdf_objects.append(
            "3 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj"
        )
        next_obj = 4 + len(self.pages)

        # Font bold
        font_bold_num = next_obj
        pdf_objects.append(
            f"{font_bold_num} 0 obj\n<< /Type /Font /Subtype /Type1 "
            f"/BaseFont /Helvetica-Bold >>\nendobj"
        )
        next_obj += 1

        # Font courier
        font_courier_num = next_obj
        pdf_objects.append(
            f"{font_courier_num} 0 obj\n<< /Type /Font /Subtype /Type1 "
            f"/BaseFont /Courier >>\nendobj"
        )
        next_obj += 1


        # Resources dict string
        resources = (
            f"<< /Font << /F1 3 0 R /F2 {font_bold_num} 0 R "
            f"/F3 {font_courier_num} 0 R >> >>"
        )

        # Page objects and their content streams
        content_obj_start = next_obj
        for i, page_content in enumerate(self.pages):
            page_num = 4 + i
            content_num = content_obj_start + i
            pdf_objects.insert(
                page_num - 1,
                f"{page_num} 0 obj\n<< /Type /Page /Parent 2 0 R "
                f"/MediaBox [0 0 {self.page_width} {self.page_height}] "
                f"/Resources {resources} "
                f"/Contents {content_num} 0 R >>\nendobj"
            )
            stream_data = page_content.encode('latin-1', errors='replace')
            pdf_objects.append(
                f"{content_num} 0 obj\n<< /Length {len(stream_data)} >>\n"
                f"stream\n{page_content}\nendstream\nendobj"
            )

        # Write PDF file
        with open(filename, 'wb') as f:
            f.write(b"%PDF-1.4\n")
            offsets = []
            for obj in pdf_objects:
                offsets.append(f.tell())
                f.write(obj.encode('latin-1', errors='replace'))
                f.write(b"\n")

            xref_pos = f.tell()
            f.write(b"xref\n")
            f.write(f"0 {len(pdf_objects) + 1}\n".encode())
            f.write(b"0000000000 65535 f \n")
            for off in offsets:
                f.write(f"{off:010d} 00000 n \n".encode())

            f.write(b"trailer\n")
            f.write(f"<< /Size {len(pdf_objects) + 1} /Root 1 0 R >>\n".encode())
            f.write(b"startxref\n")
            f.write(f"{xref_pos}\n".encode())
            f.write(b"%%EOF\n")



def generate_notes_pdf():
    pdf = SimplePDF()
    pdf._start_page()

    # ===== COVER PAGE =====
    pdf.set_font("F2", 22)
    pdf.y = 600
    pdf.write_text("Selenium WebDriver", pdf.margin_left + 100, bold=True, size=22)
    pdf.write_text("Complete Deep-Dive Notes", pdf.margin_left + 80, bold=True, size=20)
    pdf.blank_line()
    pdf.set_font("F1", 12)
    pdf.write_text("Topics: Dropdowns | Web Tables | Frames | Waits | JS Executor")
    pdf.write_text("With Real Demo Site URLs & Production Code Examples")
    pdf.blank_line()
    pdf.write_text("Author: Prabhakar | Framework: OrangeHRM Selenium Framework")
    pdf.write_text(f"Generated: {datetime.date.today().strftime('%B %d, %Y')}")
    pdf.blank_line()
    pdf.blank_line()
    pdf.write_line()
    pdf.blank_line()
    pdf.set_font("F2", 14)
    pdf.write_text("Table of Contents", bold=True)
    pdf.set_font("F1", 11)
    pdf.blank_line()
    pdf.write_text("1. Handling Dropdowns (Select, Custom div, Salesforce Lightning, Auto-suggest)")
    pdf.write_text("2. Handling Web Tables & Dynamic Tables (Pagination, Search, Infinite Scroll)")
    pdf.write_text("3. Handling Frames / iFrames (Static, Nested, Dynamic)")
    pdf.write_text("4. Waits in Selenium (Implicit, Explicit, Fluent, Custom)")
    pdf.write_text("5. JavaScriptExecutor (Click, Scroll, Set Value, Shadow DOM)")

    # ===== TOPIC 1: DROPDOWNS =====
    pdf._end_page()
    pdf._start_page()
    pdf.title("1. HANDLING DROPDOWNS IN SELENIUM")


    pdf.write_wrapped("Most modern UIs (Salesforce Lightning, ServiceNow, Angular/React Material) do NOT use the HTML <select> tag. They render dropdowns as <div>, <ul><li> or <input role='combobox'>. The classic Select class will NOT work on them.")
    pdf.blank_line()

    pdf.heading2("Demo Sites for Practicing Dropdowns")
    pdf.write_text("* https://the-internet.herokuapp.com/dropdown  (Native <select>)")
    pdf.write_text("* https://demoqa.com/select-menu  (React-select, multi-select)")
    pdf.write_text("* https://demoqa.com/auto-complete  (Auto-suggest typeahead)")
    pdf.write_text("* https://practice.expandtesting.com/dropdown  (Standard practice)")
    pdf.write_text("* https://ultimateqa.com/filling-out-forms/  (Cascading dropdowns)")
    pdf.write_text("* https://opensource-demo.orangehrmlive.com/  (Custom div, Login: Admin/admin123)")
    pdf.blank_line()

    pdf.heading2("1.1 Native <select> - The Easy Case")
    pdf.write_wrapped("Use Select class from org.openqa.selenium.support.ui.Select. Works ONLY when tag is literally <select>.")
    pdf.blank_line()

    pdf.heading3("Example: https://the-internet.herokuapp.com/dropdown")
    pdf.code_block([
        'driver.get("https://the-internet.herokuapp.com/dropdown");',
        '',
        'WebElement dropdownEl = driver.findElement(By.id("dropdown"));',
        'Select dropdown = new Select(dropdownEl);',
        '',
        '// 3 ways to select:',
        'dropdown.selectByVisibleText("Option 1");',
        'dropdown.selectByValue("2");',
        'dropdown.selectByIndex(1);',
        '',
        '// Useful APIs:',
        'dropdown.isMultiple();',
        'dropdown.getFirstSelectedOption().getText();',
        'dropdown.getOptions();  // all options',
    ])


    pdf.heading2("1.2 Custom div/ul/li Dropdowns (Real-World)")
    pdf.write_wrapped("Recipe is ALWAYS 2 steps: (1) Click to open (2) Wait for options & select.")
    pdf.blank_line()
    pdf.heading3("Example: https://demoqa.com/select-menu")
    pdf.code_block([
        'driver.get("https://demoqa.com/select-menu");',
        '// Click the react-select container to open',
        'driver.findElement(By.id("withOptGroup")).click();',
        '// Wait for option and click',
        'By option = By.xpath("//div[contains(@class,\'option\') and text()=\'Group 1, option 1\']");',
        'new WebDriverWait(driver, Duration.ofSeconds(10))',
        '    .until(ExpectedConditions.elementToBeClickable(option)).click();',
    ])

    pdf.heading3("Generic Reusable Method:")
    pdf.code_block([
        'public void selectFromCustomDropdown(By toggle, By optionsBy, String value) {',
        '    WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(15));',
        '    wait.until(ExpectedConditions.elementToBeClickable(toggle)).click();',
        '    List<WebElement> options = wait.until(',
        '        ExpectedConditions.visibilityOfAllElementsLocatedBy(optionsBy));',
        '    for (WebElement opt : options) {',
        '        if (opt.getText().trim().equalsIgnoreCase(value)) {',
        '            opt.click(); return;',
        '        }',
        '    }',
        '    throw new NoSuchElementException("Option not found: " + value);',
        '}',
    ])

    pdf.heading2("1.3 Salesforce Lightning Combobox")
    pdf.write_wrapped("Lightning uses <input role='combobox'> + <div role='listbox'>. The input is READ-ONLY (must click). Wait for aria-expanded='true' before selecting option.")
    pdf.blank_line()
    pdf.code_block([
        'public void selectLightningCombobox(String label, String optionText) {',
        '    By combo = By.xpath("//lightning-combobox[.//label[normalize-space()=\'" ',
        '        + label + "\']]//input[@role=\'combobox\']");',
        '    WebElement el = wait.until(ExpectedConditions.elementToBeClickable(combo));',
        '    el.click();',
        '    wait.until(ExpectedConditions.attributeToBe(el, "aria-expanded", "true"));',
        '    By opt = By.xpath("//lightning-base-combobox-item[.//span[normalize-space()=\'"',
        '        + optionText + "\']]");',
        '    wait.until(ExpectedConditions.elementToBeClickable(opt)).click();',
        '}',
    ])


    pdf.heading2("1.4 Auto-suggest / Typeahead")
    pdf.write_wrapped("You must TYPE first, then AJAX returns suggestions dynamically.")
    pdf.heading3("Example: https://demoqa.com/auto-complete")
    pdf.code_block([
        'driver.get("https://demoqa.com/auto-complete");',
        'WebElement input = driver.findElement(By.id("autoCompleteMultipleInput"));',
        'input.sendKeys("re");',
        'By sugg = By.xpath("//div[contains(@class,\'option\') and contains(text(),\'Red\')]");',
        'wait.until(ExpectedConditions.elementToBeClickable(sugg)).click();',
    ])

    pdf.heading2("1.5 Common Problems & Solutions")
    pdf.write_text("* ElementNotInteractableException -> Wait for elementToBeClickable + scroll")
    pdf.write_text("* StaleElementReferenceException -> Re-locate using By, never cache WebElement")
    pdf.write_text("* Option not found (whitespace) -> Use normalize-space() in XPath")
    pdf.write_text("* UnexpectedTagNameException -> It's NOT <select>; use custom approach")
    pdf.write_text("* Dropdown closes before click -> Re-open inside loop for each pick")
    pdf.blank_line()

    # ===== TOPIC 2: WEB TABLES =====
    pdf._end_page()
    pdf._start_page()
    pdf.title("2. HANDLING WEB TABLES & DYNAMIC TABLES")
    pdf.write_wrapped("Real challenge: pagination, sorting, filtering, lazy loading. Not the static table itself.")
    pdf.blank_line()

    pdf.heading2("Demo Sites for Practicing Tables")
    pdf.write_text("* https://the-internet.herokuapp.com/tables  (Sortable + edit/delete)")
    pdf.write_text("* https://demoqa.com/webtables  (Dynamic add/edit/delete + pagination)")
    pdf.write_text("* https://datatables.net/examples/basic_init/zero_configuration.html")
    pdf.write_text("  (jQuery DataTables: search, sort, pagination)")
    pdf.write_text("* https://demo.guru99.com/test/web-table-element.php  (Nested tables)")
    pdf.write_text("* https://www.ag-grid.com/example/  (AG-Grid virtualized enterprise)")
    pdf.blank_line()


    pdf.heading2("2.1 Read All Data from Static Table")
    pdf.heading3("Example: https://the-internet.herokuapp.com/tables")
    pdf.code_block([
        'driver.get("https://the-internet.herokuapp.com/tables");',
        'List<WebElement> rows = driver.findElements(By.cssSelector("#table1 tbody tr"));',
        'List<WebElement> headers = driver.findElements(By.cssSelector("#table1 thead th"));',
        'System.out.println("Rows: " + rows.size() + ", Cols: " + headers.size());',
        '',
        '// Read specific cell (row 2, col 3)',
        'String cell = driver.findElement(',
        '    By.cssSelector("#table1 tbody tr:nth-child(2) td:nth-child(3)")).getText();',
    ])

    pdf.heading2("2.2 Find Row by Value & Click Action (Classic Interview Q)")
    pdf.write_wrapped("Question: Find the row where Last Name='Bach' and click Edit.")
    pdf.code_block([
        '// Direct XPath approach:',
        'By editLink = By.xpath(',
        '    "//table[@id=\'table1\']//tbody//tr[td[1][normalize-space()=\'Bach\']]//a[text()=\'edit\']");',
        'driver.findElement(editLink).click();',
        '',
        '// Production approach: dynamic column index from header name',
        '// (See full method in HTML version)',
    ])

    pdf.heading2("2.3 Dynamic Tables with PAGINATION (Page 2/3 Problem)")
    pdf.write_wrapped("Real scenario: The data is NOT on page 1. It appears only when you click page 2 or 3.")
    pdf.blank_line()
    pdf.heading3("Example: https://datatables.net/examples/basic_init/zero_configuration.html")
    pdf.code_block([
        'public boolean findAcrossPages(String searchName) {',
        '    WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));',
        '    while (true) {',
        '        List<WebElement> rows = driver.findElements(By.cssSelector("#example tbody tr"));',
        '        for (WebElement row : rows) {',
        '            if (row.findElements(By.tagName("td")).get(0).getText().equals(searchName))',
        '                return true;  // Found!',
        '        }',
        '        WebElement next = driver.findElement(By.id("example_next"));',
        '        if (next.getAttribute("class").contains("disabled")) return false;',
        '        String firstRow = rows.get(0).getText();',
        '        next.click();',
        '        // CRITICAL: Wait for page to actually change!',
        '        wait.until(ExpectedConditions.not(',
        '            ExpectedConditions.textToBe(',
        '                By.cssSelector("#example tbody tr:first-child"), firstRow)));',
        '    }',
        '}',
    ])


    pdf.heading3("KEY INSIGHTS for Pagination:")
    pdf.write_text("1. NEVER cache WebElement across pages (DOM rebuilt = StaleElement)")
    pdf.write_text("2. ALWAYS wait for 'first row text changed' after clicking Next")
    pdf.write_text("3. Check if Next button is disabled to stop the loop")
    pdf.blank_line()

    pdf.heading2("2.4 Using Table Search (Best Practice)")
    pdf.code_block([
        '// ALWAYS prefer search over walking pages when available!',
        'driver.findElement(By.cssSelector("input[type=\'search\']")).sendKeys("Tiger Nixon");',
        'wait.until(d -> d.findElements(By.cssSelector("#example tbody tr")).size() == 1);',
    ])

    pdf.heading2("2.5 AG-Grid / Virtualized Tables")
    pdf.write_wrapped("AG-Grid only renders VISIBLE rows. Rows below fold don't exist in DOM. Scroll the grid body via JS to load them.")
    pdf.code_block([
        '// Scroll AG-Grid body:',
        'js.executeScript("document.querySelector(\'.ag-body-viewport\').scrollTop += 400;");',
        '// Then re-query rows (new ones now exist in DOM)',
    ])

    pdf.heading2("2.6 Common Problems")
    pdf.write_text("* StaleElement after Next -> Re-locate inside loop")
    pdf.write_text("* XPath td[3] breaks -> Compute index from header dynamically")
    pdf.write_text("* AG-Grid row not found -> Scroll body via JS")
    pdf.write_text("* Pagination never ends -> Compare current to previous page text")
    pdf.write_text("* getText() returns '' -> Use getAttribute('value') for inputs")
    pdf.blank_line()

    # ===== TOPIC 3: FRAMES =====
    pdf._end_page()
    pdf._start_page()
    pdf.title("3. HANDLING FRAMES / IFRAMES IN SELENIUM")
    pdf.write_wrapped("A frame/iframe is 'a page inside a page'. Selenium only sees the top-level document. You must explicitly switch context to interact with frame elements.")
    pdf.blank_line()

    pdf.heading2("Demo Sites for Practicing Frames")
    pdf.write_text("* https://the-internet.herokuapp.com/iframe  (TinyMCE editor in iframe)")
    pdf.write_text("* https://the-internet.herokuapp.com/nested_frames  (Nested frames)")
    pdf.write_text("* https://demoqa.com/frames  (Multiple iframes)")
    pdf.write_text("* https://demoqa.com/nestedframes  (Parent/child frames)")
    pdf.write_text("* https://practice.expandtesting.com/iframe  (Simple iframe)")
    pdf.blank_line()


    pdf.heading2("3.1 All Ways to Switch INTO a Frame")
    pdf.write_text("a) By index: driver.switchTo().frame(0);  // least preferred")
    pdf.write_text("b) By name/id: driver.switchTo().frame('paymentFrame');")
    pdf.write_text("c) By WebElement: driver.switchTo().frame(element);  // most reliable")
    pdf.write_text("d) Wait+Switch (RECOMMENDED):")
    pdf.code_block([
        'new WebDriverWait(driver, Duration.ofSeconds(15))',
        '    .until(ExpectedConditions.frameToBeAvailableAndSwitchTo(By.id("mce_0_ifr")));',
    ])

    pdf.heading2("3.2 Switching OUT of a Frame")
    pdf.code_block([
        'driver.switchTo().parentFrame();    // 1 level up',
        'driver.switchTo().defaultContent(); // all the way to top (ALWAYS USE THIS)',
    ])

    pdf.heading2("3.3 Complete Working Example - TinyMCE Editor")
    pdf.heading3("URL: https://the-internet.herokuapp.com/iframe")
    pdf.code_block([
        'driver.get("https://the-internet.herokuapp.com/iframe");',
        'WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));',
        '',
        '// Switch to editor iframe',
        'wait.until(ExpectedConditions.frameToBeAvailableAndSwitchTo(By.id("mce_0_ifr")));',
        '',
        '// Type in the editor',
        'WebElement body = driver.findElement(By.tagName("body"));',
        'body.clear();',
        'body.sendKeys("Hello from Selenium!");',
        '',
        '// ALWAYS come back to main page',
        'driver.switchTo().defaultContent();',
    ])

    pdf.heading2("3.4 Nested Frames Example")
    pdf.heading3("URL: https://the-internet.herokuapp.com/nested_frames")
    pdf.code_block([
        'driver.get("https://the-internet.herokuapp.com/nested_frames");',
        'driver.switchTo().frame("frame-top");     // first level',
        'driver.switchTo().frame("frame-middle");  // second level',
        'String text = driver.findElement(By.id("content")).getText(); // "MIDDLE"',
        'driver.switchTo().defaultContent();       // back to root',
        'driver.switchTo().frame("frame-bottom");  // switch to sibling',
    ])

    pdf.heading2("3.5 Golden Rules")
    pdf.write_text("* Cannot jump from one frame to sibling directly - go to defaultContent first")
    pdf.write_text("* ALWAYS call defaultContent() after frame work (use try/finally)")
    pdf.write_text("* If NoSuchElement but locator is correct -> probably inside an iframe!")
    pdf.blank_line()

    pdf.heading2("3.6 Common Problems")
    pdf.write_text("* NoSuchFrameException -> Frame not in DOM yet; use frameToBeAvailableAndSwitchTo")
    pdf.write_text("* Can't click main page after frame -> Forgot defaultContent()")
    pdf.write_text("* Iframe has no id/name -> Locate by src, title, pass WebElement")
    pdf.write_text("* TinyMCE not accepting text -> switchTo frame first, sendKeys to body")
    pdf.blank_line()


    # ===== TOPIC 4: WAITS =====
    pdf._end_page()
    pdf._start_page()
    pdf.title("4. WAITS IN SELENIUM")
    pdf.write_wrapped("Most flaky tests are caused by a missing or wrong wait. Selenium runs at JVM speed while web apps load asynchronously (AJAX, animations, SPA routing).")
    pdf.blank_line()

    pdf.heading2("Demo Sites for Practicing Waits")
    pdf.write_text("* https://the-internet.herokuapp.com/dynamic_loading/1  (Hidden element)")
    pdf.write_text("* https://the-internet.herokuapp.com/dynamic_loading/2  (Not yet rendered)")
    pdf.write_text("* https://the-internet.herokuapp.com/dynamic_controls  (Appear/disappear)")
    pdf.write_text("* https://demoqa.com/dynamic-properties  (Button enabled after delay)")
    pdf.write_text("* https://practice.expandtesting.com/dynamic-loading  (Loading spinner)")
    pdf.blank_line()

    pdf.heading2("4.1 Implicit Wait")
    pdf.code_block([
        'driver.manage().timeouts().implicitlyWait(Duration.ofSeconds(10));',
        '// Applies to EVERY findElement. Only checks DOM presence.',
        '// Does NOT wait for visibility/clickability!',
    ])
    pdf.write_wrapped("CONS: Only handles 'element not in DOM'. Selenium warns against mixing with explicit waits (timeouts compound).")
    pdf.blank_line()

    pdf.heading2("4.2 Explicit Wait - THE WORKHORSE")
    pdf.heading3("Example: https://the-internet.herokuapp.com/dynamic_loading/1")
    pdf.code_block([
        'driver.get("https://the-internet.herokuapp.com/dynamic_loading/1");',
        'driver.findElement(By.cssSelector("#start button")).click();',
        'WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(15));',
        '',
        '// Wait for spinner to disappear',
        'wait.until(ExpectedConditions.invisibilityOfElementLocated(By.id("loading")));',
        '',
        '// Wait for result to be visible',
        'WebElement result = wait.until(',
        '    ExpectedConditions.visibilityOfElementLocated(By.cssSelector("#finish h4")));',
        'System.out.println(result.getText());  // "Hello World!"',
    ])


    pdf.heading3("ExpectedConditions You Use 90% of the Time:")
    pdf.write_text("* presenceOfElementLocated(by) - exists in DOM (might be hidden)")
    pdf.write_text("* visibilityOfElementLocated(by) - exists AND visible")
    pdf.write_text("* elementToBeClickable(by) - visible AND enabled (use before click)")
    pdf.write_text("* invisibilityOfElementLocated(by) - spinner/modal disappears")
    pdf.write_text("* textToBe(by, 'Done') - wait until text matches")
    pdf.write_text("* attributeToBe(el, 'aria-expanded', 'true') - combobox open")
    pdf.write_text("* frameToBeAvailableAndSwitchTo(by) - iframes")
    pdf.write_text("* numberOfElementsToBeMoreThan(by, 0) - table rows loaded")
    pdf.write_text("* stalenessOf(element) - old element gone (page transition)")
    pdf.blank_line()

    pdf.heading2("4.3 Fluent Wait")
    pdf.code_block([
        'Wait<WebDriver> fluent = new FluentWait<>(driver)',
        '    .withTimeout(Duration.ofSeconds(30))',
        '    .pollingEvery(Duration.ofMillis(250))         // faster polling',
        '    .ignoring(NoSuchElementException.class)',
        '    .ignoring(StaleElementReferenceException.class) // key!',
        '    .withMessage("Element never loaded");',
        'WebElement el = fluent.until(d -> d.findElement(By.id("target")));',
    ])
    pdf.write_wrapped("Use FluentWait when: shorter polling needed, must ignore StaleElement, need custom error message.")
    pdf.blank_line()

    pdf.heading2("4.4 Dynamic Controls Example")
    pdf.heading3("URL: https://the-internet.herokuapp.com/dynamic_controls")
    pdf.code_block([
        'driver.get("https://the-internet.herokuapp.com/dynamic_controls");',
        'driver.findElement(By.cssSelector("#checkbox-example button")).click();',
        'wait.until(ExpectedConditions.invisibilityOfElementLocated(By.id("checkbox")));',
        'wait.until(ExpectedConditions.textToBe(By.id("message"), "It\'s gone!"));',
        '',
        'driver.findElement(By.cssSelector("#input-example button")).click();',
        'WebElement input = wait.until(',
        '    ExpectedConditions.elementToBeClickable(By.cssSelector("#input-example input")));',
        'input.sendKeys("Now I can type!");',
    ])

    pdf.heading2("4.5 THE TRAP: Implicit + Explicit Together")
    pdf.write_wrapped("NEVER MIX! When explicit wait polls findElement, implicit wait ALSO triggers for EACH poll. WebDriverWait(10s) + implicit(10s) = up to 100s timeout!")
    pdf.write_text("FIX: Set implicit wait to 0, rely fully on explicit waits.")
    pdf.blank_line()

    pdf.heading2("4.6 Common Problems")
    pdf.write_text("* ElementClickInterceptedException -> Wait for overlay to disappear first")
    pdf.write_text("* StaleElement repeatedly -> FluentWait with .ignoring(StaleElement)")
    pdf.write_text("* Test super slow on CI -> Remove implicit wait, use explicit only")
    pdf.write_text("* presenceOf works but click fails -> Element display:none; use elementToBeClickable")
    pdf.blank_line()


    # ===== TOPIC 5: JAVASCRIPT EXECUTOR =====
    pdf._end_page()
    pdf._start_page()
    pdf.title("5. JAVASCRIPT EXECUTOR IN SELENIUM")
    pdf.write_wrapped("JavascriptExecutor lets you run arbitrary JS inside the browser. The ultimate fallback when normal Selenium actions fail, and great for scrolling/highlighting.")
    pdf.blank_line()

    pdf.heading2("Demo Sites for Practicing JS Executor")
    pdf.write_text("* https://the-internet.herokuapp.com/infinite_scroll  (Scroll via JS)")
    pdf.write_text("* https://the-internet.herokuapp.com/shadowdom  (Shadow DOM access)")
    pdf.write_text("* https://demoqa.com/buttons  (JS click when intercepted)")
    pdf.write_text("* https://demoqa.com/date-picker  (Set date value via JS)")
    pdf.write_text("* https://the-internet.herokuapp.com/drag_and_drop  (HTML5 DnD via JS)")
    pdf.blank_line()

    pdf.heading2("5.1 Basic Setup")
    pdf.code_block([
        'JavascriptExecutor js = (JavascriptExecutor) driver;',
        'js.executeScript("alert(\'Hello!\');");',
        '',
        '// executeScript(script, args...)       - synchronous',
        '// executeAsyncScript(script, args...)  - async (must call callback)',
    ])

    pdf.heading2("5.2 JS Click (Bypass Overlays)")
    pdf.heading3("Example: https://demoqa.com/buttons")
    pdf.code_block([
        'driver.get("https://demoqa.com/buttons");',
        'WebElement btn = driver.findElement(By.xpath("//button[text()=\'Click Me\']"));',
        '// Normal click fails due to overlay:',
        '// btn.click(); // ElementClickInterceptedException!',
        '// JS click bypasses:',
        '((JavascriptExecutor) driver).executeScript("arguments[0].click();", btn);',
    ])

    pdf.heading2("5.3 Scroll Into View")
    pdf.heading3("Example: https://the-internet.herokuapp.com/infinite_scroll")
    pdf.code_block([
        'driver.get("https://the-internet.herokuapp.com/infinite_scroll");',
        'JavascriptExecutor js = (JavascriptExecutor) driver;',
        '// Scroll to bottom to trigger lazy-load:',
        'js.executeScript("window.scrollTo(0, document.body.scrollHeight);");',
        '',
        '// Scroll specific element into view:',
        'js.executeScript("arguments[0].scrollIntoView({block:\'center\'});", element);',
    ])


    pdf.heading2("5.4 Set Value on Date Pickers (sendKeys won't work)")
    pdf.heading3("Example: https://demoqa.com/date-picker")
    pdf.code_block([
        'driver.get("https://demoqa.com/date-picker");',
        'WebElement dateInput = driver.findElement(By.id("datePickerMonthYearInput"));',
        '// JS set value + trigger React events:',
        'js.executeScript(',
        '    "arguments[0].value = arguments[1];"',
        '    + "arguments[0].dispatchEvent(new Event(\'input\', {bubbles:true}));"',
        '    + "arguments[0].dispatchEvent(new Event(\'change\', {bubbles:true}));",',
        '    dateInput, "05/26/2026");',
    ])
    pdf.write_wrapped("WHY dispatch events? React/Angular don't notice raw value= writes. Firing input/change events makes the framework re-render correctly.")
    pdf.blank_line()

    pdf.heading2("5.5 Shadow DOM Access")
    pdf.heading3("Example: https://the-internet.herokuapp.com/shadowdom")
    pdf.code_block([
        'driver.get("https://the-internet.herokuapp.com/shadowdom");',
        'WebElement host = driver.findElement(By.cssSelector("my-paragraph:nth-child(1)"));',
        '',
        '// Pre-Selenium 4: JS only way',
        'WebElement inner = (WebElement) js.executeScript(',
        '    "return arguments[0].shadowRoot.querySelector(\'slot\')", host);',
        '',
        '// Selenium 4 native:',
        'SearchContext shadow = host.getShadowRoot();',
        'WebElement slot = shadow.findElement(By.cssSelector("slot"));',
    ])

    pdf.heading2("5.6 Other Useful JS Recipes")
    pdf.write_text("* Highlight: js.executeScript('arguments[0].style.border=\"3px solid green\"', el)")
    pdf.write_text("* Page title: (String) js.executeScript('return document.title;')")
    pdf.write_text("* Page ready: js.executeScript('return document.readyState === \"complete\";')")
    pdf.write_text("* Open tab: js.executeScript('window.open(url, \"_blank\");')")
    pdf.write_text("* Zoom: js.executeScript('document.body.style.zoom=\"80%\";')")
    pdf.write_text("* Remove element: js.executeScript('arguments[0].remove();', banner)")
    pdf.blank_line()

    pdf.heading2("5.7 Common Problems")
    pdf.write_text("* ElementClickIntercepted (cookie banner) -> Dismiss OR jsClick")
    pdf.write_text("* Date picker rejects sendKeys -> jsSetValue with dispatchEvent")
    pdf.write_text("* Element below fold, fails headless -> scrollIntoView first")
    pdf.write_text("* executeAsyncScript hangs -> Forgot to call callback argument")
    pdf.write_text("* 'Cannot read properties of null' -> Element not in DOM yet; add wait")
    pdf.blank_line()

    pdf.write_line()
    pdf.blank_line()
    pdf.set_font("F2", 12)
    pdf.write_text("=== END OF NOTES ===", pdf.margin_left + 180, bold=True)
    pdf.set_font("F1", 9)
    pdf.write_text("Generated for SeleniumFramework | Prabhakar | May 2026")
    pdf.write_text("For full HTML version with tables/formatting: see Selenium-Deep-Dive-Notes.html")

    # Build the PDF
    pdf.build("/projects/sandbox/SeleniumFramework/notes/Selenium-Deep-Dive-Notes.pdf")
    print("PDF generated successfully!")

if __name__ == "__main__":
    generate_notes_pdf()
