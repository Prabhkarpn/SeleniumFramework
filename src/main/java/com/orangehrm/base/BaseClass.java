package com.orangehrm.base;

import java.io.FileInputStream;
import java.io.IOException;
import java.time.Duration;
import java.util.Properties;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.locks.LockSupport;

import org.apache.logging.log4j.Logger;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.edge.EdgeDriver;
import org.openqa.selenium.firefox.FirefoxDriver;
import org.testng.annotations.AfterMethod;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.BeforeSuite;

import com.orangehrm.actiondriver.ActionDriver;
import com.orangehrm.utilities.ExtentManager;
import com.orangehrm.utilities.LoggerManager;

public class BaseClass {

	protected static Properties prop;
	//protected static WebDriver driver;
	//private static ActionDriver actionDriver;
	
	protected static ThreadLocal<WebDriver>driver = new ThreadLocal<>();
	private static ThreadLocal<ActionDriver>actionDriver = new ThreadLocal<>();
	
	
	public static final Logger logger = LoggerManager.getLogger(BaseClass.class);
	
	@BeforeSuite
	public void loadConfig() throws Exception {
		// Load the configuration file
		prop = new Properties();
		// for reading the file we need to create FileInputStream object
		FileInputStream fis = new FileInputStream("src\\main\\resources\\config.properties");
		prop.load(fis);
		logger.info("config.properties file is loaded");
		
		//Start the Extent Report
		//ExtentManager.getReporter();  -- This has been implemented in TestListener
	}

	@BeforeMethod
	public synchronized void setup() {
		System.out.println("Setting up WebDriver for : "+this.getClass().getSimpleName());
		launchBrowser();
		configureBrowser();
		staticWait(10);
		
		logger.info("WebDriver initialized and Browser Maximized");
		logger.trace("This is a trace Message");
		logger.error("This is a Error Message");
		logger.debug("This is a debug message");
		logger.fatal("This is a fatal message");
		logger.warn("This is a warn meaage");
		
		//Initialize the ActionDriver only  once
		/*
		if(actionDriver == null) {
			actionDriver = new ActionDriver(driver);
			System.out.println("ActionDriver instance is created"+Thread.currentThread().getId());
		} */
		
		//initialize ActionDriver for the current Thread
		actionDriver.set(new ActionDriver(getDriver()));
		logger.info("ActionDriver initialized for thread : "+Thread.currentThread().getId());

	}

	// initialize the webDriver based on browser defined in config.properties file
	private void launchBrowser() {
		String browser = prop.getProperty("browser");

		if (browser.equalsIgnoreCase("chrome")) {
			//driver = new ChromeDriver();
			driver.set(new ChromeDriver());		//new changes as per Thread
			ExtentManager.registerDriver(getDriver());
			logger.info("ChromeDriver instance is created");
		} else if (browser.equalsIgnoreCase("edge")) {
			//driver = new EdgeDriver();
			driver.set(new EdgeDriver());		//new changes as per Thread
			ExtentManager.registerDriver(getDriver());
			logger.info("EdgeDriver instance is created");
		} else if (browser.equalsIgnoreCase("firefox")) {
			//driver = new FirefoxDriver();
			driver.set(new FirefoxDriver());	//new changes as per Thread
			ExtentManager.registerDriver(getDriver());
			logger.info("FirefoxDriver instance is created");
		} else {
			throw new IllegalArgumentException("Browser not supported : " + browser);
		}

	}
	
	
	/*Configure Browser Settings such as PageLoad timeout, 
	 * implicit wait,maximize the browser and Launch the url
	 */
	private void configureBrowser() {
		
		getDriver().manage().window().maximize();
		
		// PageLoad timeouts
		getDriver().manage().timeouts().pageLoadTimeout(Duration.ofSeconds(60));
		
		// Implicit wait
		int implicitWait = Integer.parseInt(prop.getProperty("implicitWait"));
		getDriver().manage().timeouts().implicitlyWait(Duration.ofSeconds(implicitWait));

		// navigate to URL
		try {
			getDriver().get(prop.getProperty("url"));
		} catch (Exception e) {
			System.out.println("Failed to Navigate to the URL"+e.getMessage());
		}
		
	}
	
	

	@AfterMethod
	public synchronized void tearDown() {
		if (getDriver() != null) {

			try {
				getDriver().quit();
			} catch (Exception e) {
				System.out.println("Unable to quit the browser : " + e.getMessage());

			}
		}
		logger.info("WebDriver instance is closed");
		driver.remove();
		actionDriver.remove();
		//getDriver()`=null;
		//actionDriver=null;
		//ExtentManager.endTest();  -- This has been implemented in TestListener
	}
	
	//getter method for prop
	public static Properties getProp() {
		return prop;
	}
	
	/*
	//driver getter method
	public WebDriver getDriver()
	{
		return driver;
	}
	
	//driver setter method
	public void setDriver(WebDriver driver) {
		this.driver = driver;
	}
	*/
	//Getter method for WebDriver
	public static WebDriver getDriver() {
		if(driver.get() == null) {
			System.out.println("WebDriver is not initiated");
			throw new IllegalStateException("WebDriver is not initiated");
		}
		return driver.get();
	}
	
	//Getter method for ActionDriver
	public static ActionDriver getActionDriver() {
		if(actionDriver.get() == null) {
			System.out.println("Action Driver is not initialized");
			throw new IllegalStateException("Action Driver is not initialized");
		}
		return actionDriver.get();
	}
	
	public void staticWait(int seconds) {
		LockSupport.parkNanos(TimeUnit.SECONDS.toNanos(seconds));
	}

}
