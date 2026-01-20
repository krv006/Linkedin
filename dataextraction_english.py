import re
import time

import pandas as pd
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from datamodification_english import changedatetype
from utils_english import slow_scroll_all, deep_scroll_page, sleep


def get_date_from_job_details(driver):
    """
    Extract date (e.g., '2 hours ago') from the right-side job details panel.
    """
    try:
        ago_element = driver.find_element(
            By.XPATH,
            "/html/body/div[6]/div[3]/div[4]/div/div/main/div/div[2]/div[2]/div/div[2]/div/div[2]/div[1]/div/div[1]/div/div[1]/div/div[3]/div/span"
        )
        raw_date = ago_element.text.strip()
        if raw_date:
            return changedatetype(raw_date)
    except:
        pass

    return "Date not found"


# def extract_posting_date(card, driver):
#     """
#     Extract posting date from a LinkedIn job card.
#     Supports multiple formats used by LinkedIn.
#     """
#     # Scroll card into view
#     driver.execute_script("arguments[0].scrollIntoView(true);", card)
#     sleep()

#     date_posted = "Date not found"

#     try:
#         # 1) Look for <time> element (classic LinkedIn format)
#         try:
#             date_element = card.find_element(By.XPATH, ".//time")
#             date_posted = date_element.get_attribute("datetime") or date_element.text.strip()

#         except:
#             # 2) Look for spans that contain "ago", "posted", etc.
#             try:
#                 date_element = card.find_element(
#                     By.XPATH,
#                     ".//span[contains(text(),'ago') or contains(text(),'Posted') or contains(@class,'t-black--light')]"
#                 )
#                 date_posted = date_element.text.strip()

#             except:
#                 # 3) Look inside footer metadata
#                 try:
#                     date_element = card.find_element(
#                         By.XPATH,
#                         ".//li[contains(@class,'job-card-container__footer-item')]//span[contains(text(),'ago')]"
#                     )
#                     date_posted = date_element.text.strip()
#                 except:
#                     date_element = 
#         print("Extracted date_posted:", date_posted)
#         # Convert LinkedIn date string to real timestamp
#         if date_posted not in ["", None, "Date not found"]:
#             date_posted = changedatetype(date_posted)

#     except:
#         date_posted = "Date not found"

#     return date_posted

from selenium.webdriver.common.by import By


def extract_posting_date_from_card(card):
    """
    Extract posting date ONLY from job card (before click).
    """
    try:
        time_el = card.find_element(By.XPATH, ".//time")
        return time_el.get_attribute("datetime") or time_el.text.strip()
    except:
        return "Date not found"


def extract_posting_date_from_details(driver, timeout=5):
    try:
        el = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((
                By.XPATH,
                "//time | //span[contains(text(),'ago')]"
            ))
        )
        return el.get_attribute("datetime") or el.text.strip()
    except:
        x = 1

        while x == 1:
            x = input('error finding the date')
        return "Date not found"


# def extract_posting_date(card, driver):
#     """
#     Extract posting date from a LinkedIn job card.
#     Tries card-level selectors first, then falls back to details panel.
#     """
#     driver.execute_script("arguments[0].scrollIntoView(true);", card)
#     sleep()

#     date_posted = "Date not found"

#     try:
#         # 1) <time> element inside card
#         try:
#             el = card.find_element(By.XPATH, ".//time")
#             date_posted = el.get_attribute("datetime") or el.text.strip()

#         except:
#             # 2) span with 'ago' / 'Posted'
#             try:
#                 el = card.find_element(
#                     By.XPATH,
#                     ".//span[contains(text(),'ago') or contains(text(),'Posted')]"
#                 )
#                 date_posted = el.text.strip()

#             except:
#                 # 3) footer metadata
#                 try:
#                     el = card.find_element(
#                         By.XPATH,
#                         ".//li[contains(@class,'job-card-container__footer-item')]//span[contains(text(),'ago')]"
#                     )
#                     date_posted = el.text.strip()

#                 except:
#                     # 4) LAST RESORT: job details panel (absolute XPath)
#                     try:
#                         el = driver.find_element(
#                             By.XPATH,
#                             "/html/body/div[6]/div[3]/div[4]/div/div/main/div/div[2]/div[2]/div/div[2]/div/div[2]/div[1]/div/div[1]/div/div[1]/div/div[3]/div/span/span[3]/span[2]"
#                         )
#                         date_posted = el.text.strip()
#                     except Exception as e:
#                         date_posted = "Date not found"
#                         print('error here', e)
#                         time.sleep(60)

#         print("Extracted date_posted:", date_posted)

#         if date_posted not in ("", None, "Date not found"):
#             date_posted = changedatetype(date_posted)

#     except Exception as e:
#         print("Date extracti    on failed:", e)
#         date_posted = "Date not found"

#     return date_posted

def changedatetype(date_element):
    date_element = date_element.lower().strip()

    # Handle simple formats
    if "just now" in date_element:
        return pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')

    if date_element == "today":
        return pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')

    if date_element == "yesterday":
        ts = pd.Timestamp.now() - pd.Timedelta(days=1)
        return ts.strftime('%Y-%m-%d %H:%M:%S')

    # Extract number
    words = date_element.split()
    difference = None
    for word in words:
        if word.isdigit():
            difference = int(word)
            break

    if difference is None:
        return "error"

    now = pd.Timestamp.now()

    # Apply difference
    if "day" in date_element:
        changed_date = now - pd.Timedelta(days=difference)
    elif "minute" in date_element:
        changed_date = now - pd.Timedelta(minutes=difference)
    elif "second" in date_element:
        changed_date = now - pd.Timedelta(seconds=difference)
    elif "hour" in date_element:
        changed_date = now - pd.Timedelta(hours=difference)
    elif "week" in date_element:
        changed_date = now - pd.Timedelta(weeks=difference)
    elif "month" in date_element:
        changed_date = now - pd.DateOffset(months=difference)
    elif "year" in date_element:
        changed_date = now - pd.DateOffset(years=difference)
    else:
        return "error"

    return changed_date.strftime('%Y-%m-%d %H:%M:%S')


def extractinfo(driver, keyword, country, job_data, tools_list):
    # Scroll va lazy loading
    slow_scroll_all(driver)
    deep_scroll_page(driver)
    time.sleep(3)  # Allow all cards to load

    try:
        # Natijalar soni tekshirish
        results_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//small//span"))
        )
        results_text = results_element.text.strip()
        if not results_text:
            print("No results found.")
            return job_data
    except Exception as e:
        print("No results element found:", e)
        return job_data

    try:
        job_cards = driver.find_elements(By.CLASS_NAME, "job-card-container")
        print(f"Number of job cards loaded: {len(job_cards)}")
        if job_data is None:
            job_data = []

        # --- 🔹 Scroll paytida date_postedni yig‘ish
        initial_data = []
        for card in job_cards:
            driver.execute_script("arguments[0].scrollIntoView(true);", card)
            sleep()

            try:
                # date_posted = extract_posting_date(card, driver)
                date_posted = extract_posting_date_from_card(card)
            except:
                date_posted = "Date not found"

            initial_data.append({
                "card_element": card,
                "date_posted": date_posted
            })

        # --- 🔹 Har bir cardni ochib qolgan ma'lumotlarni yig‘ish
        for idx, data in enumerate(initial_data):
            card = data["card_element"]
            driver.execute_script("arguments[0].scrollIntoView(true);", card)
            sleep()

            try:
                card.click()
            except:
                print('card click failed')

            # Job title
            try:
                title_element = driver.find_element(
                    By.CSS_SELECTOR, "div.t-24.job-details-jobs-unified-top-card__job-title h1.t-24.t-bold.inline a"
                )
                job_title = title_element.text
            except:
                job_title = None
            try:
                date_posted = data.get("date_posted", None)
            except:
                date_posted = None

            # If date is missing or invalid → fetch from job details pane
            if not date_posted or date_posted == "Date not found" or date_posted == "error":
                # date_posted = get_date_from_job_details(driver)
                date_posted = extract_posting_date_from_details(driver)
            print("Final date_posted used:", date_posted)
            # Job link va ID
            try:
                job_link = card.find_element(By.CLASS_NAME, "job-card-list__title--link").get_attribute("href")
                match = re.search(r'view/(\d+)', job_link)
                job_id = match.group(1) if match else 'Not available'
            except:
                job_link = None
                job_id = 'Not available'

            # Company name
            try:
                company_name_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__company-name a")
                    )
                )
                company_name = company_name_element.text
            except:
                company_name = "Unknown"

            # Company logo
            try:
                img_element = card.find_element(By.XPATH, ".//div[contains(@class, 'ivm-view-attr__img-wrapper')]//img")
                img_url = img_element.get_attribute("src")
            except:
                img_url = None

            # Location
            try:
                location_element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR,
                         ".job-details-jobs-unified-top-card__primary-description-container span > span.tvm__text--low-emphasis:first-child")
                    )
                )
                location = location_element.text
            except:
                location = None

            # Salary va skills
            skillslist = []
            try:
                salary_element = card.find_element(By.XPATH,
                                                   ".//div[contains(@class, 'artdeco-entity-lockup__metadata')]//span")
                salarytext = salary_element.text
            except:
                salarytext = '0'

            try:
                expandlist = driver.find_element(By.CLASS_NAME, 'job-details-preferences-and-skills')
                expandlist.click()
                time.sleep(3)
                elements = driver.find_elements(By.CLASS_NAME,
                                                'job-details-preferences-and-skills__modal-section-insights-list-item')
                for element in elements:
                    element_text = element.text
                    if salarytext not in element_text and 'Remote' not in element_text and 'Full-time' not in element_text and \
                            'Intern' not in element_text and 'On-site' not in element_text and 'Hybrid' not in element_text and \
                            'Temporary' not in element_text and "Contract" not in element_text:
                        skillslist.append(element_text)
                if not skillslist:
                    skillslist.append(None)
                closeexpandlist = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//button[@aria-label='Dismiss']"))
                )
                closeexpandlist.click()
            except:
                skillslist = []

            # Description
            try:
                description_element = driver.find_element(By.CSS_SELECTOR, '#job-details')
                description = description_element.text.replace('\n', ' ')
            except:
                description = ''

            # Tools list bilan match qilish
            try:
                for skill in tools_list:
                    if re.search(rf'\b{re.escape(skill)}\b', description, re.IGNORECASE) and skill not in skillslist:
                        skillslist.append(skill)
            except:
                pass

            # Job data append
            job_data.append({
                "Posted_date": data["date_posted"],
                "Job Title from List": keyword,
                "Job Title": job_title,
                "Company": company_name,
                "Company Logo URL": img_url,
                "Country": country,
                "Location": location,
                "Skills": skillslist,
                "Salary Info": salarytext,
                "Extracted on": pd.Timestamp.now(),
                "Source": "linkedin.com",
                "JobID": job_id
            })

            sleep()

    except Exception as e:
        print(f'Error in extraction loop: {e}')

    return job_data
