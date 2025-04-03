import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from datetime import datetime, timedelta

# Helper function from your existing tests
def click_element_safely(driver, element):
    try:
        # Scroll element into view
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.5)  # Give time for any animations
        
        # Click the element
        element.click()
    except Exception as e:
        print(f"Error clicking element: {str(e)}")
        # Try JavaScript click as fallback
        try:
            driver.execute_script("arguments[0].click();", element)
        except Exception as js_error:
            print(f"JavaScript click also failed: {str(js_error)}")
            raise

# Setup driver function
def setup_driver():
    chrome_options = Options()
    # Uncomment the following line for headless testing
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    return driver

# Test for generating sales reports between date ranges
def test_generate_sales_report():
    driver = setup_driver()
    try:
        print("Starting PDF report generation test...")
        time.sleep(5)  # Add a 5-second delay
        driver.get("http://127.0.0.1:8000/Login/")
        
        # Login as a seller
        email_field = driver.find_element(By.NAME, "your_email")
        email_field.send_keys("amalantoney123@gmail.com")

        password_field = driver.find_element(By.NAME, "your_password")
        password_field.send_keys("Amal@123")

        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        click_element_safely(driver, login_button)

        WebDriverWait(driver, 10).until(EC.url_changes("http://127.0.0.1:8000/Login/"))
        print(f"Logged in. Current URL: {driver.current_url}")

        # Navigate to seller dashboard using the correct URL
        try:
            # Try to find the dashboard link
            dashboard_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'seller_dashboard') or contains(@href, 'dashboard')]"))
            )
            click_element_safely(driver, dashboard_link)
            print("Clicked on Dashboard link")
        except (TimeoutException, NoSuchElementException):
            # Direct navigation as fallback - use the correct URL
            driver.get("http://127.0.0.1:8000/orders/seller_dashboard/")
            print("Navigated directly to seller dashboard")
        
        print(f"Dashboard URL: {driver.current_url}")
        
        # PDF REPORT TEST
        try:
            # Scroll down to the report generation section at bottom of page
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            print("Scrolled to bottom of page")
            
            # Find the card with "Generate Sales Report" title
            report_card = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'card-header')]/h5[contains(text(), 'Generate Sales Report')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", report_card)
            print("Found Generate Sales Report section")
            
            # Set start date using JavaScript directly to avoid input issues
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            end_date = datetime.now().strftime("%Y-%m-%d")
            
            # Make sure the elements exist before trying to set values
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "start_date"))
            )
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "end_date"))
            )
            
            # Use JavaScript to set the input values directly
            driver.execute_script("document.getElementById('start_date').value = arguments[0]", start_date)
            print(f"Set start date to: {start_date}")
            
            driver.execute_script("document.getElementById('end_date').value = arguments[0]", end_date)
            print(f"Set end date to: {end_date}")
            
            # Take a screenshot to verify the date inputs
            driver.save_screenshot("date_inputs_set.png")
            print("Screenshot saved of date inputs")
            
            # Find the report type dropdown and select PDF
            try:
                # First try to find the dropdown
                report_type_select = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "report_type"))
                )
                
                # Use JavaScript to select the PDF option
                driver.execute_script("arguments[0].value = 'pdf'", report_type_select)
                print("Selected PDF report type")
                
                # Take a screenshot to verify the form is filled
                driver.save_screenshot("form_filled.png")
                print("Screenshot saved of filled form")
                
                # Click generate button using JavaScript to ensure it works
                generate_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Generate Report')]"))
                )
                driver.execute_script("arguments[0].click();", generate_button)
                print("Clicked Generate Report button with JavaScript")
                
                # Wait for a moment to allow the report to generate
                time.sleep(5)
                print("Waited for report generation")
                
                # Take a screenshot
                driver.save_screenshot("after_generate_report.png")
                print("Screenshot saved after generating report")
                
                print("PDF report test completed successfully")
                
            except Exception as e:
                print(f"Error with PDF report options: {str(e)}")
                driver.save_screenshot("pdf_report_options_error.png")
                print("Error screenshot saved as pdf_report_options_error.png")
            
        except Exception as e:
            print(f"Error generating PDF report: {str(e)}")
            driver.save_screenshot("pdf_report_generation_error.png")
            print("Error screenshot saved as pdf_report_generation_error.png")
        
        # CSV REPORT TEST - Start a new browser session for this test
        print("\nStarting CSV report generation test in a new session...")
        driver.quit()
        driver = setup_driver()
        
        # Login again
        driver.get("http://127.0.0.1:8000/Login/")
        email_field = driver.find_element(By.NAME, "your_email")
        email_field.send_keys("amalantoney123@gmail.com")
        password_field = driver.find_element(By.NAME, "your_password")
        password_field.send_keys("Amal@123")
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        click_element_safely(driver, login_button)
        WebDriverWait(driver, 10).until(EC.url_changes("http://127.0.0.1:8000/Login/"))
        print("Logged in again for CSV test")
        
        # Navigate directly to seller dashboard
        driver.get("http://127.0.0.1:8000/orders/seller_dashboard/")
        print("Navigated to seller dashboard for CSV test")
        
        try:
            # Scroll to report section
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            
            # Find the card with "Generate Sales Report" title
            report_card = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'card-header')]/h5[contains(text(), 'Generate Sales Report')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", report_card)
            print("Found Generate Sales Report section")
            
            # Set start date using JavaScript directly
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            end_date = datetime.now().strftime("%Y-%m-%d")
            
            # Make sure the elements exist before trying to set values
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "start_date"))
            )
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "end_date"))
            )
            
            # Use JavaScript to set the input values
            driver.execute_script("document.getElementById('start_date').value = arguments[0]", start_date)
            print(f"Set start date to: {start_date}")
            
            driver.execute_script("document.getElementById('end_date').value = arguments[0]", end_date)
            print(f"Set end date to: {end_date}")
            
            # Find report type dropdown
            report_type_select = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "report_type"))
            )
            
            # Select CSV option
            driver.execute_script("arguments[0].value = 'csv'", report_type_select)
            print("Selected CSV report type")
            
            # Take a screenshot
            driver.save_screenshot("csv_form_filled.png")
            print("Screenshot saved of CSV form")
            
            # Click generate button
            generate_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Generate Report')]"))
            )
            driver.execute_script("arguments[0].click();", generate_button)
            print("Clicked Generate Report button for CSV")
            
            # Wait for download
            time.sleep(5)
            print("Waited for CSV report generation")
            
            # Take final screenshot
            driver.save_screenshot("csv_report_generated.png")
            print("CSV report test completed successfully")
            
        except Exception as e:
            print(f"Error with CSV report: {str(e)}")
            driver.save_screenshot("csv_report_error.png")
            print("Error screenshot saved as csv_report_error.png")
            
    except Exception as e:
        print(f"An error occurred in the main test flow: {str(e)}")
        driver.save_screenshot("main_test_error.png")
        print("Error screenshot saved as main_test_error.png")
        
    finally:
        driver.quit()
        print("All test sessions closed")

# Main function to run the tests
if __name__ == "__main__":
    print("Starting Report Generation Selenium Tests...")
    test_generate_sales_report()
    print("\nAll report generation tests completed!") 