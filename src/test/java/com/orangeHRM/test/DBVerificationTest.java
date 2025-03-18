package com.orangeHRM.test;

import java.util.Map;

import org.testng.Assert;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Test;

import com.orangehrm.base.BaseClass;
import com.orangehrm.pages.HomePage;
import com.orangehrm.pages.LoginPage;
import com.orangehrm.utilities.DBConnection;
import com.orangehrm.utilities.ExtentManager;



public class DBVerificationTest extends BaseClass {
	
	private LoginPage loginPage;
	private HomePage homePage;
	
	@BeforeMethod
	public void setupPages() {
		
		loginPage=new LoginPage(getDriver());  //here getDriver() method we are calling it inside BaseClass
		homePage = new HomePage(getDriver());
		
	}
	
	@Test
	public void verifyEmployeeNameVerificationFromDB() {
		ExtentManager.logStep("logging with the admin credentials");
		loginPage.login(prop.getProperty("username"), prop.getProperty("password"));
		
		ExtentManager.logStep("Clicking on PIM tab");
		homePage.clickOnPIMTab();
		
		ExtentManager.logStep("Search for Employee");
		homePage.employeeSearch("prabhakar","0002");
		
		ExtentManager.logStep("Get the employee name from DB");
		String employee_id="2";
		
		//fetch data into a Map
		Map<String,String> employeeDetails = DBConnection.getEmployeeDetails(employee_id);
		
		String emplFirstName = employeeDetails.get("firstName");
		String emplMiddleName = employeeDetails.get("middleName");
		String emplLastName = employeeDetails.get("lastName");
		
		String emplFirstAndMiddleName = (emplFirstName+" "+emplMiddleName).trim();
		System.out.println("emp first name "+emplFirstName+" middle name "+emplMiddleName);
		
		ExtentManager.logStep("verify the employee first and middle name");
		Assert.assertTrue(homePage.verifyEmployeeFirstAndMiddleName(emplFirstAndMiddleName),"First and Middle names are not same");
		
		Assert.assertTrue(homePage.verifyEmployeeLastName(emplLastName),"Last name is not matched");
		
		
	}

}
