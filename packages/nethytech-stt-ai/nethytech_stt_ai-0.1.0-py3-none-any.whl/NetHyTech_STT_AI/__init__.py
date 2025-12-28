from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from os import getcwd
import time


chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--use-fake-ui-for-media-stream")
chrome_options.add_argument("--headless=new")


driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)


website = "https://allorizenproject1.netlify.app/"
driver.get(website)

rec_file = f"{getcwd()}\\input.txt"

def listen():
    try:
        # Click start button
        start_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "startButton"))
        )
        start_button.click()
        print("Listening...")

        last_text = ""

        # Run for 60 seconds only
        end_time = time.time() + 60

        while time.time() < end_time:
            output_element = driver.find_element(By.ID, "output")
            current_text = output_element.text.strip()

            if current_text and current_text != last_text:
                last_text = current_text

                with open(rec_file, "w", encoding="utf-8") as file:
                    file.write(current_text.lower())

                print("USER:", current_text)

            time.sleep(1)

    except KeyboardInterrupt:
        print("Stopped by user")
    except Exception as e:
        print("Error:", e)
    finally:
        driver.quit()
        print("Browser closed")

listen()
