import json
import os
import time

from selenium.webdriver.common.by import By

COOKIE_FILE = "linkedin.cookies.json"


def save_cookies(driver):
    cookies = driver.get_cookies()
    with open(COOKIE_FILE, "w") as f:
        json.dump(cookies, f)
    print(f"Cookie'lar saqlandi → {COOKIE_FILE}")


def load_cookies(driver):
    if not os.path.exists(COOKIE_FILE):
        return False
    try:
        driver.get("https://www.linkedin.com")
        time.sleep(3)
        with open(COOKIE_FILE, "r") as f:
            cookies = json.load(f)
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except:
                continue
        driver.get("https://www.linkedin.com/feed/")
        time.sleep(5)
        if "feed" in driver.current_url or "jobs" in driver.current_url:
            print("Cookie'lardan muvaffaqiyatli kirildi!")
            return True
        else:
            os.remove(COOKIE_FILE)
            return False
    except:
        if os.path.exists(COOKIE_FILE):
            os.remove(COOKIE_FILE)
        return False


def login_and_save(driver, email, password):
    driver.get("https://www.linkedin.com/login")
    time.sleep(3)
    driver.find_element(By.ID, "username").send_keys(email)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    time.sleep(12)
    save_cookies(driver)
