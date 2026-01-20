import random
import time

from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def sleep(min_time=0.5, max_time=2.0):
    sleeptime = random.uniform(min_time, max_time)
    time.sleep(sleeptime)


def slow_scroll_all(driver, steps=50, distance=300):
    for i in range(steps):
        # Scroll the main window a bit
        driver.execute_script("window.scrollBy(0, arguments[0]);", distance)

        # Scroll all scrollable elements
        driver.execute_script("""
            const elems = document.querySelectorAll('*');
            elems.forEach(el => {
                if (el.scrollHeight > el.clientHeight + 50) {
                    el.scrollTop += arguments[0];
                }
            });
        """, distance)

        time.sleep(0.3)


def deep_scroll_page(driver, max_scrolls=12, pause=1.0):
    """
    Scrolls the whole window down step by step to trigger lazy loading
    of all job cards on the current result page.
    """
    last_height = 0
    for i in range(max_scrolls):
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        except WebDriverException:
            break
        time.sleep(pause)
        # Small scroll up to help LinkedIn load stuff sometimes
        try:
            driver.execute_script("window.scrollBy(0, -200);")
        except WebDriverException:
            pass

        new_height = driver.execute_script("return window.pageYOffset;")
        if new_height == last_height:
            # nothing new loaded
            break
        last_height = new_height


def applytimerange(driver):
    timerangeID = 'searchFilter_timePostedRange'
    try:
        timerange = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, timerangeID))
        )
        timerange.click()
    except:
        pass
    pastmonthlabel = 'timePostedRange-r2592000'  # keep
    past24hourslabel = 'timePostedRange-r86400'
    pastweeklabel = 'timePostedRange-r604800'  # keep
    try:
        timerangevalueLabel = driver.find_element(By.CSS_SELECTOR, f"label[for='{past24hourslabel}']")

        timerangevalueLabel.click()
    except:
        pass
    try:

        button = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((
                By.XPATH, "//button[contains(@aria-label, 'Apply')]"
            ))
        )

        #
        button.click()
        print("Time filter applied")

    except Exception as e:
        print(f"Error apply button: {e}")
        pass
