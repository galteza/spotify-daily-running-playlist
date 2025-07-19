from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

'''
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode
driver = webdriver.Chrome(options=chrome_options)]
'''

# Set up the WebDriver (replace with your path to chromedriver)

def scrapeBPM(query, driver):
    

    # Find the search input field and enter the search query
    search_box = driver.find_element(By.NAME, "query")
    search_box.send_keys(query)
    search_box.send_keys(Keys.RETURN)  # Press Enter to search

    # Wait for the page to load (you may need to adjust this time)
    # WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "a.flex.flex-col")))

    time.sleep(2)

    # Find the first search result link
    first_result = driver.find_element(By.CSS_SELECTOR, "a.flex.flex-col")
    first_result_url = first_result.get_attribute("href")  # Get the URL of the first result

    # Visit the first result URL
    driver.get(first_result_url)

    # Wait for the result page to load completely
    # WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.CLASS_NAME, "mt-1 text-3xl font-semibold text-card-foreground")))

    time.sleep(1)

    # Get the page source after the page is loaded
    page_source = driver.page_source

    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(page_source, "html.parser")

    # Find the BPM value by targeting the appropriate class
    bpm_element = soup.find_all("dd", class_="mt-1 text-3xl font-semibold text-card-foreground")[2]

    # Extract the BPM value (if found)
    if bpm_element:
        bpm_value = bpm_element.get_text(strip=True)
        return bpm_value
    else:
        return "BPM not found"

'''
# Example Usage
bpm = scrapeBPM("Ariana Grande Positions")  # Replace with the song or artist name you want to search for
print(f"BPM: {bpm}")

# Close the browser when done
driver.quit()

'''
