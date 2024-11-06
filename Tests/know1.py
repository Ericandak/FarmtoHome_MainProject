from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import requests
from selenium.common.exceptions import WebDriverException
import time

def setup_driver():
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    return driver

def wait_for_overlay_to_disappear(driver, timeout=10):
    try:
        WebDriverWait(driver, timeout).until_not(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".overlay, .modal, .loading"))
        )
    except TimeoutException:
        print("No overlay found or it didn't disappear")

def click_element_safely(driver, element):
    try:
        element.click()
    except ElementClickInterceptedException:
        wait_for_overlay_to_disappear(driver)
        try:
            element.click()
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", element)
def test_successful_product_and_seller_navigation(driver):
    time.sleep(5)  # Add a 5-second delay
    driver.get("http://127.0.0.1:8000/Login/")
    
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

    # Wait for product cards to be visible
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "product-card")))
        print("Product cards found")
    except TimeoutException:
        print("Product cards not found")
        raise

    # Find and click the first product card
    try:
        product_card = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "product-card"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", product_card)
        time.sleep(1) 
        

        product_name = product_card.find_element(By.CSS_SELECTOR, ".card-title").text
        print(f"Found product: {product_name}")

        click_element_safely(driver, product_card)
        print("Clicked on product card")
    except (TimeoutException, NoSuchElementException) as e:
        print("Product card not found or not clickable")
        print(f"Error: {str(e)}")
        raise

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "product-image"))
        )
        print("Product detail page loaded")

        for i in range(0, 1000, 550):  
            driver.execute_script(f"window.scrollTo(0, {i});")
            time.sleep(0.5)
        print("Scrolled through product details")

        try:
    
            seller_button = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.LINK_TEXT, "Know Your Seller"))
            )
        except TimeoutException:
            try:
             
                seller_button = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "Know Your"))
                )
            except TimeoutException:
                try:
            
                    seller_button = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, "//a[contains(., 'Know Your Seller')]"))
                    )
                except TimeoutException:

                    print("Page source:", driver.page_source)
                    raise Exception("Could not find 'Know Your Seller' button using any method")
        print(f"Found button with text: {seller_button.text}")
        print(f"Button HTML: {seller_button.get_attribute('outerHTML')}")


        driver.execute_script("arguments[0].scrollIntoView(true);", seller_button)
        time.sleep(2)  
        try:
            click_element_safely(driver, seller_button)
            print("Clicked 'Know Your Seller' button")
        except Exception as e:
            print(f"Failed to click button: {str(e)}")
            driver.execute_script("arguments[0].click();", seller_button)
            print("Clicked button using JavaScript")


        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "seller-profile"))
        )
        print("Seller profile page loaded successfully")

    
        for i in range(0, 1000, 550):
            driver.execute_script(f"window.scrollTo(0, {i});")
            time.sleep(0.5)
        print("Scrolled through seller profile")

        # Wait a moment at the bottom of the page
        time.sleep(2)
    except TimeoutException:
        print("Failed to navigate to seller profile")
        raise

    print("Product and seller navigation test completed")

def check_server_running():
    try:
        response = requests.get("http://127.0.0.1:8000/")
        return response.status_code == 200
    except requests.ConnectionError:
        return False

def main():
    driver = setup_driver()
    try:
        if not check_server_running():
            print("Server is not running. Please start the server first.")
            return
        test_successful_product_and_seller_navigation(driver)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
