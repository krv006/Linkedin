from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def open_all_filters_modal(driver, timeout=15):
    wait = WebDriverWait(driver, timeout)

    try:
        btn = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[contains(@class,'search-reusables__all-filters-pill-button') "
                "and normalize-space()='All filters']"
            ))
        )

        driver.execute_script("arguments[0].click();", btn)
        return True

    except Exception as e:
        print(f"[All filters modal] open failed: {e}")
        return False


def select_all_title_filters_containing_keyword(driver, keyword, timeout=15):
    wait = WebDriverWait(driver, timeout)
    kw = keyword.lower().strip()

    try:
        # Title filter fieldset
        title_section = wait.until(
            EC.presence_of_element_located((
                By.XPATH,
                "//fieldset[.//h3[normalize-space()='Title']]"
            ))
        )

        options = title_section.find_elements(
            By.XPATH,
            ".//li[contains(@class,'search-reusables__filter-value-item')]"
        )

        matched_count = 0
        for opt in options:
            text = opt.text.lower()
            if kw in text:
                checkbox = opt.find_element(By.XPATH, ".//input[@type='checkbox']")
                if not checkbox.is_selected():
                    driver.execute_script("arguments[0].click();", checkbox)
                    matched_count += 1

        if matched_count == 0:
            print(f"[Title filter] no options matched '{keyword}'")
            return False

        return True

    except Exception as e:
        print(f"[Title filter] selection failed: {e}")
        return False


def submit_filters(driver, timeout=15):
    wait = WebDriverWait(driver, timeout)

    try:
        show_btn = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[.//span[contains(normalize-space(),'Show')]]"
            ))
        )
        driver.execute_script("arguments[0].click();", show_btn)
        return True

    except Exception as e:
        print(f"[Filters submit] failed: {e}")
        return False


def select_date_posted_past_month(driver, timeout=15):
    wait = WebDriverWait(driver, timeout)

    try:
        # Locate Date posted fieldset
        date_section = wait.until(
            EC.presence_of_element_located((
                By.XPATH,
                "//fieldset[.//h3[normalize-space()='Date posted']]"
            ))
        )

        # Locate "Past month" radio input (robust: by value OR label text)
        past_month_radio = date_section.find_element(
            By.XPATH,
            ".//input[@type='radio' and (@value='r2592000' "
            "or following-sibling::label//span[normalize-space()='Past month'])]"
        )

        if not past_month_radio.is_selected():
            driver.execute_script("arguments[0].click();", past_month_radio)

        return True

    except Exception as e:
        print(f"[Date posted] Past month selection failed: {e}")
        return False
