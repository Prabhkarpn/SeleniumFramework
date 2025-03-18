package com.orangehrm.pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;

import com.orangehrm.actiondriver.ActionDriver;
import com.orangehrm.base.BaseClass;

public class HomePage {

	public ActionDriver actionDriver;

	// Define locators using BY class
	private By adminTab = By.xpath("//span[text()='Admin']");
	private By userIDButton = By.xpath("//p[@class='oxd-userdropdown-name']");
	private By logoutButton = By.xpath("//a[text()='Logout']");
	private By orangeHRMLogo = By.xpath("//div[@class='oxd-brand-banner']/img");
	
	private By pimTab = By.xpath("//span[text()='PIM']");
	private By employeeName = By.xpath("(//input[@placeholder='Type for hints...'])[1]");
	private By searchButton = By.xpath("//button[@type='submit']");
	private By empFirstAndMiddleName = By.xpath("(//div[@class='oxd-table-card'])[1]/div/div[3]");
	private By empLastName = By.xpath("(//div[@class='oxd-table-card'])[1]/div/div[4]");
	private By empId = By.xpath("//label[text()='Employee Id']/parent::div/following-sibling::div/input");

	// initialize ActionDriver object by passing WebDriver Instance
	/*
	public HomePage(WebDriver driver) {
		this.actionDriver = new ActionDriver(driver);
	}  */
	
	public HomePage(WebDriver driver) {
		this.actionDriver = BaseClass.getActionDriver();
	}
	
	//Method to verify if Admin tab is visible
	public boolean isAdminTabVisible() {
		return actionDriver.isDisplayed(adminTab);
	}
	
	public boolean verifyOrangeHRMLogo() {
		return actionDriver.isDisplayed(orangeHRMLogo);
	}
	
	//method to navigate PIM Tab
	public void clickOnPIMTab() {
		actionDriver.click(pimTab);
	}
	
	//Empolyee search
	public void employeeSearch(String empName,String empID) {
		actionDriver.enterText(employeeName, empName);
		actionDriver.enterText(empId, empID);
		actionDriver.click(searchButton);
		actionDriver.scrollToElement(empFirstAndMiddleName);
	}
	
	//verify employee first and middle name
	public boolean verifyEmployeeFirstAndMiddleName(String employeeFirstAndMiddleNameDB) {
		return actionDriver.compareText(empFirstAndMiddleName, employeeFirstAndMiddleNameDB);
	}
	
	//Verify Employee Last Name
	
	public  boolean verifyEmployeeLastName(String employeeLastNameDB) {
		return actionDriver.compareText(empLastName, employeeLastNameDB);
	}
	
	
	//Method to perform Logout operation
	public void logout() {
		actionDriver.click(userIDButton);
		actionDriver.click(logoutButton);
		
	}

}
