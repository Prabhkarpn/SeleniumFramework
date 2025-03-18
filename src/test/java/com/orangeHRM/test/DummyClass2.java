package com.orangeHRM.test;

import org.testng.Assert;
import org.testng.annotations.Test;

import com.orangehrm.base.BaseClass;
import com.orangehrm.utilities.ExtentManager;

public class DummyClass2 extends BaseClass{
	
	@Test
	public void dummyTest2() throws InterruptedException {
		
		//ExtentManager.startTest("DummyTest2 Test");  -- This has been implemented in TestListener
		System.out.println("The Browser lauched");
		//Thread.sleep(20000);
		String title = getDriver().getTitle();
		ExtentManager.logStep("verifying the Title");
		Assert.assertEquals(title, "OrangeHRM","TestFailed : Title is not matched");
		
	}


}
