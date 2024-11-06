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


def test_login():
    driver = setup_driver()  # Setup the driver
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

    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        driver.quit()

# Update main function to call the new test function
def main():
    test_login()

if __name__ == "__main__":
    main()