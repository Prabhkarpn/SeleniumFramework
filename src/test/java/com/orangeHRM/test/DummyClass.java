package com.orangeHRM.test;

import org.testng.Assert;
import org.testng.SkipException;
import org.testng.annotations.Test;

import com.orangehrm.base.BaseClass;
import com.orangehrm.utilities.ExtentManager;







public class DummyClass extends BaseClass{
	
	@Test
	public void dummyTest() throws InterruptedException {
		
		//ExtentManager.startTest("DummyTest1 Test");
		System.out.println("The Browser lauched");
		//Thread.sleep(20000);
		String title = getDriver().getTitle();
		ExtentManager.logStep("verifying the Title");
		Assert.assertEquals(title, "OrangeHRM","TestFailed : Title is not matched");
		ExtentManager.logSkip("This case is skipped");
		throw new SkipException("Skipping the test as part of testing");
		
	}

}
