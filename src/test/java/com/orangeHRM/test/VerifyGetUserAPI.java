package com.orangeHRM.test;

import org.testng.annotations.Test;
import org.testng.asserts.SoftAssert;

import com.orangehrm.utilities.ApiUtility;
import com.orangehrm.utilities.ExtentManager;
import com.orangehrm.utilities.RetryAnalyzer;

import io.restassured.response.Response;

public class VerifyGetUserAPI {
	
	@Test
	public void verifyGetUserAPI() {
		
		SoftAssert softAssert = new SoftAssert();
		//step1 : Define API endpoint
		String endPoint = " ";
		ExtentManager.logStep("API EndPoint: "+endPoint);
		
		//step2 : send GET request
		ExtentManager.logStep("Sending GET request to the API");
		Response response = ApiUtility.sendGetRequest(endPoint);
		
		//step3 : validate state code
		ExtentManager.logStep("Validating API response status code");
		boolean isStatuscodeValid = ApiUtility.validateStatusCode(response, 200);
		
		softAssert.assertTrue(isStatuscodeValid,"status code is not as expected");
		
		if(isStatuscodeValid) {
			ExtentManager.logStepValidationForAPI("Status code validation Passed!");
		}else {
			ExtentManager.logFailureAPI("Status code validation Failed!");
		}
		
		//Step 4 : Validate user name
		ExtentManager.logStep("Validating response body for username");
		String username = ApiUtility.getJsonValue(response, "username");
		boolean isUserNameValid = "Bret".equals(username);
		softAssert.assertTrue(isUserNameValid,"Username is not valid");
		if(isUserNameValid) {
			ExtentManager.logStepValidationForAPI("Username Validation Passed!");
		}else {
			ExtentManager.logFailureAPI("Username validation Fail!");
		}
		

		//Step 4 : Validate email
		ExtentManager.logStep("Validating response body for UserEmail");
		String userEmail = ApiUtility.getJsonValue(response, "email");
		boolean isEmailValid = "Bret".equals(userEmail);
		softAssert.assertTrue(isEmailValid,"UserEmail is not valid");
		if(isEmailValid) {
			ExtentManager.logStepValidationForAPI("UserEmail Validation Passed!");
		}else {
			ExtentManager.logFailureAPI("UserEmail validation Fail!");
		}
		
	}
	
	
	
	

}
