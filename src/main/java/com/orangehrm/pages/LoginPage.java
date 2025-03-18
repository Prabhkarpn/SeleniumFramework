package com.orangehrm.pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;

import com.orangehrm.actiondriver.ActionDriver;
import com.orangehrm.base.BaseClass;

public class LoginPage {

	private ActionDriver actionDriver;

	// Define Locators using By class
	private By userNameField = By.name("username");
	private By passwordField = By.name("password");
	private By loginButton = By.xpath("//button[@type='submit']");
	private By errorMessage = By.xpath("//p[text()='Invalid credentials']");
	
	//initialize ActionDriver object by passing WebDriver Instance
	/*
	public LoginPage(WebDriver driver) {
		this.actionDriver=new ActionDriver(driver);
	}  */
	
	public LoginPage(WebDriver driver) {
		this.actionDriver = BaseClass.getActionDriver();
	}
	
	
	//Method to Perform Login
	public void login(String userName, String password) {
		actionDriver.enterText(userNameField, userName);
		actionDriver.enterText(passwordField, password);
		actionDriver.click(loginButton);
		
	}
	
	//Method to check if error message is displayed 
	public boolean isErrorMessageDisplayed() {
		return actionDriver.isDisplayed(errorMessage);
	}
	
	//Method to get the Text from Error message
	public String getErrorMessageText() {
		return actionDriver.getText(errorMessage);
	}
	
	//Verify if Error Message correct or not
	public boolean verifyErrorMessage(String expectedError) {
		return actionDriver.compareText(errorMessage, expectedError);
	}
		
	}



