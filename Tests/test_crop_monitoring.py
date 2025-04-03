import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options

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

# Test soil analysis functionality
def test_soil_analysis():
    driver = setup_driver()
    try:
        time.sleep(5)  # Add a 5-second delay
        driver.get("http://127.0.0.1:8000/Login/")
        
        # Login process
        email_field = driver.find_element(By.NAME, "your_email")
        email_field.send_keys("amalantoney123@gmail.com")  # Replace with a valid test email

        password_field = driver.find_element(By.NAME, "your_password")
        password_field.send_keys("Amal@123")  # Replace with a valid test password

        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        click_element_safely(driver, login_button)

        WebDriverWait(driver, 10).until(EC.url_changes("http://127.0.0.1:8000/Login/"))
        print(f"Logged in. Current URL: {driver.current_url}")

        # Wait for the page to load completely
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        print("Page body loaded")
        
        # Navigate to product list page (adjust URL as needed)
        driver.get("http://127.0.0.1:8000/products/sellerproductlist/")
        print("Navigated to products page")
        
        # Wait for soil analysis card and click on it
        try:
            soil_card = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "label[for='c2']"))
            )
            click_element_safely(driver, soil_card)
            print("Clicked on soil analysis card")
            
            # Get test soil image path
            test_dir = os.path.dirname(os.path.abspath(__file__))
            test_image_path = os.path.join(test_dir, "test_images", "test_soil.jpg")
            
            # Ensure test image exists
            if not os.path.exists(test_image_path):
                print(f"Test image not found at {test_image_path}")
                # Use any image from the system for testing
                import glob
                test_images = glob.glob(os.path.join(test_dir, "*.jpg")) + glob.glob(os.path.join(test_dir, "*.png"))
                if test_images:
                    test_image_path = test_images[0]
                    print(f"Using alternative test image: {test_image_path}")
                else:
                    raise FileNotFoundError("No test images found!")
            
            # Find file input and upload test image
            file_input = driver.find_element(By.NAME, "soil_image")
            file_input.send_keys(test_image_path)
            print(f"Uploaded test soil image: {test_image_path}")
            
            # Click analyze button
            analyze_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Analyze Soil')]"))
            )
            click_element_safely(driver, analyze_button)
            print("Clicked analyze button")
            
            # Wait for results
            try:
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".soil-analysis"))
                )
                print("Soil analysis results displayed successfully")
                
                # Check if soil type is displayed
                soil_type = driver.find_element(By.XPATH, "//strong[contains(text(), 'Soil Type')]")
                print(f"Found soil type element: {soil_type.text}")
                
                # Check if characteristics are displayed
                try:
                    characteristics = driver.find_element(By.XPATH, "//h6[contains(text(), 'Soil Characteristics')]")
                    print("Soil characteristics displayed")
                    
                    # Take screenshot of results
                    driver.save_screenshot("soil_analysis_results.png")
                    print("Screenshot saved as soil_analysis_results.png")
                    
                except NoSuchElementException:
                    print("Soil characteristics section not found")
            
            except TimeoutException:
                print("Soil analysis results not displayed in expected time")
                driver.save_screenshot("soil_analysis_error.png")
                print("Error screenshot saved as soil_analysis_error.png")
        
        except (TimeoutException, NoSuchElementException) as e:
            print(f"Error accessing soil analysis: {str(e)}")
            driver.save_screenshot("soil_card_error.png")
            print("Error screenshot saved as soil_card_error.png")
            
    except Exception as e:
        print(f"An error occurred during soil analysis test: {str(e)}")
        driver.save_screenshot("soil_test_error.png")
        print("Error screenshot saved as soil_test_error.png")
        
    finally:
        driver.quit()
        print("Test completed and browser closed")


# Test crop health monitoring functionality
def test_crop_health_monitoring():
    driver = setup_driver()
    try:
        time.sleep(5)  # Add a 5-second delay
        driver.get("http://127.0.0.1:8000/Login/")
        
        # Login process
        email_field = driver.find_element(By.NAME, "your_email")
        email_field.send_keys("tomjosebiju@gmail.com")  # Replace with a valid test email

        password_field = driver.find_element(By.NAME, "your_password")
        password_field.send_keys("Tom@345")  # Replace with a valid test password

        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        click_element_safely(driver, login_button)

        WebDriverWait(driver, 10).until(EC.url_changes("http://127.0.0.1:8000/Login/"))
        print(f"Logged in. Current URL: {driver.current_url}")

        # Wait for the page to load completely
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        print("Page body loaded")
        
        # Navigate to product list page
        driver.get("http://127.0.0.1:8000/products/sellerproductlist/")
        print("Navigated to products page")
        
        # Wait for crop health monitoring card and click on it
        try:
            crop_card = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "label[for='c3']"))
            )
            click_element_safely(driver, crop_card)
            print("Clicked on crop health monitor card")
            
            # Get test crop image path
            test_dir = os.path.dirname(os.path.abspath(__file__))
            test_image_path = os.path.join(test_dir, "test_images", "test_crop.jpg")
            
            # Ensure test image exists
            if not os.path.exists(test_image_path):
                print(f"Test image not found at {test_image_path}")
                # Use any image from the system for testing
                import glob
                test_images = glob.glob(os.path.join(test_dir, "*.jpg")) + glob.glob(os.path.join(test_dir, "*.png"))
                if test_images:
                    test_image_path = test_images[0]
                    print(f"Using alternative test image: {test_image_path}")
                else:
                    raise FileNotFoundError("No test images found!")
            
            # Find file input and upload test image
            file_input = driver.find_element(By.NAME, "crop_image")
            file_input.send_keys(test_image_path)
            print(f"Uploaded test crop image: {test_image_path}")
            
            # Enter area value
            area_input = driver.find_element(By.ID, "area")
            area_input.clear()
            area_input.send_keys("2.5")
            print("Entered cultivation area: 2.5 hectares")
            
            # Click analyze button
            analyze_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Analyze Crop')]"))
            )
            click_element_safely(driver, analyze_button)
            print("Clicked analyze button")
            
            # Wait for results
            try:
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".health-analysis"))
                )
                print("Crop health analysis results displayed successfully")
                
                # Check if crop details are displayed
                crop_type = driver.find_element(By.XPATH, "//strong[contains(text(), 'Crop Type')]")
                print(f"Found crop type element: {crop_type.text}")
                
                disease = driver.find_element(By.XPATH, "//strong[contains(text(), 'Disease')]")
                print(f"Found disease element: {disease.text}")
                
                # Take screenshot of results
                driver.save_screenshot("crop_analysis_results.png")
                print("Screenshot saved as crop_analysis_results.png")
                
            except TimeoutException:
                print("Crop analysis results not displayed in expected time")
                driver.save_screenshot("crop_analysis_error.png")
                print("Error screenshot saved as crop_analysis_error.png")
        
        except (TimeoutException, NoSuchElementException) as e:
            print(f"Error accessing crop health monitoring: {str(e)}")
            driver.save_screenshot("crop_card_error.png")
            print("Error screenshot saved as crop_card_error.png")
            
    except Exception as e:
        print(f"An error occurred during crop monitoring test: {str(e)}")
        driver.save_screenshot("crop_test_error.png")
        print("Error screenshot saved as crop_test_error.png")
        
    finally:
        driver.quit()
        print("Test completed and browser closed")


# Test fruit disease detection functionality
def test_fruit_disease_detection():
    driver = setup_driver()
    try:
        time.sleep(5)  # Add a 5-second delay
        driver.get("http://127.0.0.1:8000/Login/")
        
        # Login process
        email_field = driver.find_element(By.NAME, "your_email")
        email_field.send_keys("tomjosebiju@gmail.com")
        
        password_field = driver.find_element(By.NAME, "your_password")
        password_field.send_keys("Tom@345")
        
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        click_element_safely(driver, login_button)
        
        WebDriverWait(driver, 10).until(EC.url_changes("http://127.0.0.1:8000/Login/"))
        print(f"Logged in. Current URL: {driver.current_url}")
        
        # Wait for the page to load completely
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        print("Page body loaded")
        
        # Navigate to product list page
        driver.get("http://127.0.0.1:8000/products/sellerproductlist/")
        print("Navigated to products page")
        
        # Fruit disease detection card is selected by default (c1)
        try:
            # Get test fruit image path
            test_dir = os.path.dirname(os.path.abspath(__file__))
            test_image_path = os.path.join(test_dir, "test_images", "test_fruit.jpg")
            
            # Ensure test image exists
            if not os.path.exists(test_image_path):
                print(f"Test image not found at {test_image_path}")
                # Use any image from the system for testing
                import glob
                test_images = glob.glob(os.path.join(test_dir, "*.jpg")) + glob.glob(os.path.join(test_dir, "*.png"))
                if test_images:
                    test_image_path = test_images[0]
                    print(f"Using alternative test image: {test_image_path}")
                else:
                    raise FileNotFoundError("No test images found!")
            
            # Find file input and upload test image
            file_input = driver.find_element(By.NAME, "image")
            file_input.send_keys(test_image_path)
            print(f"Uploaded test fruit image: {test_image_path}")
            
            # Click analyze button
            analyze_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//form[@action='{}']//button[contains(text(), 'Analyze')]".format(
                    "/products/process_image/"
                )))
            )
            click_element_safely(driver, analyze_button)
            print("Clicked analyze button")
            
            # Wait for results
            try:
                # Wait for either success message or prediction result
                result_element = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, "//h4[contains(@class, 'alert-heading') and contains(text(), 'Prediction Result')]"))
                )
                print("Fruit disease detection results displayed successfully")
                
                # Take screenshot of results
                driver.save_screenshot("fruit_analysis_results.png")
                print("Screenshot saved as fruit_analysis_results.png")
                
            except TimeoutException:
                print("Fruit disease detection results not displayed in expected time")
                driver.save_screenshot("fruit_analysis_error.png")
                print("Error screenshot saved as fruit_analysis_error.png")
            
        except Exception as e:
            print(f"Error processing fruit image: {str(e)}")
            driver.save_screenshot("fruit_processing_error.png")
            print("Error screenshot saved as fruit_processing_error.png")
        
    except Exception as e:
        print(f"An error occurred during fruit disease detection test: {str(e)}")
        driver.save_screenshot("fruit_test_error.png")
        print("Error screenshot saved as fruit_test_error.png")
        
    finally:
        driver.quit()
        print("Test completed and browser closed")


# Main function to run the tests
if __name__ == "__main__":
    print("Starting Crop Monitoring Selenium Tests...")
    
    print("\n--- Testing Soil Analysis ---")
    test_soil_analysis()
    
    print("\n--- Testing Crop Health Monitoring ---")
    test_crop_health_monitoring()
    
    print("\n--- Testing Fruit Disease Detection ---")
    test_fruit_disease_detection()
    
    print("\nAll tests completed!")
