package com.orangeHRM.test;

import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Test;

import com.orangehrm.base.BaseClass;
import com.orangehrm.pages.HomePage;
import com.orangehrm.pages.LoginPage;
import com.orangehrm.utilities.DataProviders;
import com.orangehrm.utilities.ExtentManager;

import junit.framework.Assert;

public class HomePageTest extends BaseClass{
	
	private LoginPage loginPage;
	private HomePage homePage;
	
	@BeforeMethod
	public void setupPages() {
		
		loginPage=new LoginPage(getDriver());  //here getDriver() method we are calling it inside BaseClass
		homePage = new HomePage(getDriver());
		
	}
	
	@Test(dataProvider="validLoginData", dataProviderClass = DataProviders.class)
	public void verifyOrangeHRMLogo(String username, String password) {
		//ExtentManager.startTest("Home Page verify Logo Test"); -- This has been implemented in TestListener
		System.out.println("Running testMethod2 on Thread: "+Thread.currentThread().getId());
		loginPage.login(username, password);
		ExtentManager.logStep("Verifying Logo is visible or not");
		staticWait(10);
		Assert.assertTrue("Logo is not Visible",homePage.verifyOrangeHRMLogo());
		ExtentManager.logStep("Validation is Successful");
		ExtentManager.logStep("Looged out successfully!");
		
		
	}

}
