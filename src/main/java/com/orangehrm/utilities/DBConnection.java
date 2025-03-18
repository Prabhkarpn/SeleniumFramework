package com.orangehrm.utilities;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.HashMap;
import java.util.Map;

public class DBConnection {
	
	private static final String DB_URL="jdbc:mysql://localhost:3306/orangehrm";
	private static final String DB_USERNAME = "root";
	private static final String DB_PASSWORD = "";
	
	public static Connection getConnection() {
		try {
			System.out.println("Starting DB Connection...");
			Connection conn = DriverManager.getConnection(DB_URL,DB_USERNAME,DB_PASSWORD);
			System.out.println("DB Connection Successfull");
			return conn;
		} catch (SQLException e) {
			System.out.println("Error while establishing the DB connection");
			e.printStackTrace();
			return null;
		}
	}
	
	
	//Get the employee details from DB and store in a map
	public static Map<String, String> getEmployeeDetails(String employee_id){
		String query="SELECT emp_firstname,emp_middle_name,emp_lastname FROM hs_hr_employee WHERE employee_id="+employee_id;
		
		Map<String, String>employeeDetails = new HashMap<String,String>();
		
		try(Connection conn = getConnection();
				Statement stmt = conn.createStatement();
				ResultSet rs = stmt.executeQuery(query)){
			System.out.println("Executing query : "+query);
			if(rs.next()) {
				
				String firstName = rs.getString("emp_firstname");
				String middleName = rs.getString("emp_middle_name");
				String lastName = rs.getString("emp_lastname");
				
				//store in a map
				employeeDetails.put("firstName", firstName);
				employeeDetails.put("middleName", middleName!=null? middleName:"");
				employeeDetails.put("lastName", lastName);
				
				System.out.println("Query exceuted successfully");
				System.out.println("Employee data fetched"+employeeDetails);
			}
			else {
				System.out.println("Employee not found");
		}
		}
		catch (Exception e) {
			System.out.println("Error while executing query");
			e.printStackTrace();
		}
		
		return employeeDetails;
	}

}
