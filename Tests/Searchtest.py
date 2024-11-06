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
def test_successful_search_and_filter(driver):
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

    try:
        # Find and click the search button
        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "btn-search"))
        )
        click_element_safely(driver, search_button)
        print("Clicked search button")

        # Wait for search modal to appear
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "searchModal"))
        )
        print("Search modal opened")

        # Find and fill the search input
        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "q"))
        )
        search_input.clear()
        search_input.send_keys("a")
        print("Entered search term: 'a'")

        # Find and click the search icon button
        search_icon = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#searchForm .btn-primary"))
        )
        click_element_safely(driver, search_icon)
        print("Clicked search icon")

        WebDriverWait(driver, 10).until(
            EC.url_contains("search_results")
        )
        print("Search results page loaded")

        category_dropdown = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "category"))
        )
        print("Found category dropdown")

  
        driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", category_dropdown)
        time.sleep(1)

 
        click_element_safely(driver, category_dropdown)
        print("Clicked category dropdown")


        first_option = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#category option:nth-child(2)"))
        )
        first_option.click()
        print("Selected first category option")


        apply_filters_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#filter-form button[type='submit']"))
        )
        driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", apply_filters_button)
        time.sleep(1)

        click_element_safely(driver, apply_filters_button)
        print("Clicked Apply Filters button")

        time.sleep(2)

    
        total_height = driver.execute_script("return document.body.scrollHeight")
        for i in range(0, total_height, 200):
            driver.execute_script(f"window.scrollTo(0, {i});")
            time.sleep(0.5)
        print("Scrolled through filtered results")

    except TimeoutException as e:
        print("Search and filter operation failed")
        print(f"Error: {str(e)}")
        driver.save_screenshot("search_filter_error.png")
        raise

    print("Search and filter test completed successfully")

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
        test_successful_search_and_filter(driver)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()