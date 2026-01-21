import re
import time
from typing import List, Dict, Optional

import pandas as pd
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, \
    ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Agar senda datamodification_english.changedatetype bo'lsa ishlaydi
try:
    from datamodification_english import changedatetype as external_changedatetype
except Exception:
    external_changedatetype = None

from utils_english import slow_scroll_all, deep_scroll_page, sleep


# ---------------------------
# ✅ Date converter (fallback)
# ---------------------------
def changedatetype(date_element: str) -> str:
    """
    Fallback converter. LinkedIn date strings -> 'YYYY-mm-dd HH:MM:SS'
    Examples: '2 days ago', 'today', 'yesterday', 'just now'
    """
    if external_changedatetype:
        # Sening tashqi funksiyang bo'lsa o'shani ishlatamiz
        try:
            return external_changedatetype(date_element)
        except Exception:
            pass

    if not date_element:
        return "error"

    date_element = str(date_element).lower().strip()

    if "just now" in date_element:
        return pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
    if date_element == "today":
        return pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
    if date_element == "yesterday":
        ts = pd.Timestamp.now() - pd.Timedelta(days=1)
        return ts.strftime('%Y-%m-%d %H:%M:%S')

    words = date_element.split()
    difference = None
    for w in words:
        if w.isdigit():
            difference = int(w)
            break
        # ba'zan "a day ago" kabi bo'ladi
        if w == "a":
            difference = 1

    if difference is None:
        return "error"

    now = pd.Timestamp.now()

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


# -------------------------------------------------------
# ✅ Get date from RIGHT-side details (absolute xpath old)
# -------------------------------------------------------
def get_date_from_job_details(driver) -> str:
    """
    Old absolute XPath variant. Kechikib qolsa 'Date not found' qaytaradi.
    """
    try:
        ago_element = driver.find_element(
            By.XPATH,
            "/html/body/div[6]/div[3]/div[4]/div/div/main/div/div[2]/div[2]/div/div[2]/div/div[2]/div[1]/div/div[1]/div/div[1]/div/div[3]/div/span"
        )
        raw_date = (ago_element.text or "").strip()
        if raw_date:
            return changedatetype(raw_date)
    except Exception:
        pass
    return "Date not found"


# ----------------------------------------------
# ✅ Date from card (before click) - stable
# ----------------------------------------------
def extract_posting_date_from_card(card) -> str:
    """
    Extract posting date from job card itself.
    Returns converted timestamp if 'ago'/'today' etc.
    """
    try:
        time_el = card.find_element(By.XPATH, ".//time")
        txt = (time_el.get_attribute("datetime") or time_el.text or "").strip()
        if not txt:
            return "Date not found"

        low = txt.lower()
        if any(k in low for k in
               ["ago", "today", "yesterday", "minute", "hour", "day", "week", "month", "year", "second", "just now"]):
            return changedatetype(txt)

        return txt
    except Exception:
        return "Date not found"


# ------------------------------------------------------
# ✅ Date from details (NO BLOCK, retries, fallbacks)
# ------------------------------------------------------
def extract_posting_date_from_details(driver, timeout: int = 4, retries: int = 2) -> str:
    """
    NEVER blocks. Never uses input().
    Tries multiple selectors on details pane.
    """
    selectors = [
        # Job top card time inside details
        (By.XPATH, "//div[contains(@class,'jobs-unified-top-card')]//time"),
        # Any time element
        (By.XPATH, "//time"),
        # spans containing "ago"
        (By.XPATH, "//span[contains(translate(., 'AGO', 'ago'), 'ago')]"),
        # spans containing "posted"
        (By.XPATH, "//span[contains(translate(., 'POSTED', 'posted'), 'posted')]"),
    ]

    for _ in range(retries + 1):
        for by, xp in selectors:
            try:
                el = WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((by, xp))
                )
                txt = (el.get_attribute("datetime") or el.text or "").strip()
                if not txt:
                    continue

                low = txt.lower()
                if any(k in low for k in
                       ["ago", "today", "yesterday", "minute", "hour", "day", "week", "month", "year", "second",
                        "just now"]):
                    converted = changedatetype(txt)
                    if converted != "error":
                        return converted
                    return "Date not found"

                return txt

            except (TimeoutException, StaleElementReferenceException):
                pass
            except Exception:
                pass

        sleep(0.5, 1.0)

    return "Date not found"


# ------------------------------------------------------
# ✅ Main extraction
# ------------------------------------------------------
def extractinfo(driver, keyword: str, country: str, job_data: Optional[List[Dict]], tools_list: List[str]):
    # Scroll + lazy loading
    slow_scroll_all(driver)
    deep_scroll_page(driver)
    time.sleep(2.5)

    # Results exists?
    try:
        results_element = WebDriverWait(driver, 8).until(
            EC.presence_of_element_located((By.XPATH, "//small//span"))
        )
        results_text = (results_element.text or "").strip()
        if not results_text:
            print("No results found.")
            return job_data
    except Exception as e:
        print("No results element found:", e)
        return job_data

    # Get cards
    try:
        job_cards = driver.find_elements(By.CLASS_NAME, "job-card-container")
        print(f"Number of job cards loaded: {len(job_cards)}")
        if job_data is None:
            job_data = []

        # 1) first pass: capture card + date from card
        initial_data = []
        for card in job_cards:
            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", card)
            except Exception:
                pass
            sleep(0.4, 0.9)

            date_posted = extract_posting_date_from_card(card)
            initial_data.append({
                "card_element": card,
                "date_posted": date_posted
            })

        # 2) second pass: click each and collect details
        for idx, data in enumerate(initial_data):
            card = data["card_element"]

            # scroll into view
            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", card)
            except Exception:
                pass
            sleep(0.4, 0.9)

            # click
            try:
                card.click()
            except ElementClickInterceptedException:
                try:
                    driver.execute_script("arguments[0].click();", card)
                except Exception:
                    print("card click failed (skip)")
                    continue
            except Exception:
                print("card click failed (skip)")
                continue

            # wait job title panel load a bit
            sleep(0.6, 1.2)

            # Job title
            try:
                title_element = WebDriverWait(driver, 6).until(
                    EC.presence_of_element_located((
                        By.CSS_SELECTOR,
                        "div.t-24.job-details-jobs-unified-top-card__job-title h1.t-24.t-bold.inline a"
                    ))
                )
                job_title = (title_element.text or "").strip()
            except Exception:
                job_title = None

            # Date from card -> fallback to details
            date_posted = data.get("date_posted", None)
            if not date_posted or date_posted in ["Date not found", "error", "None", None]:
                date_posted = extract_posting_date_from_details(driver, timeout=4, retries=2)

            # Optional: last resort absolute xpath
            if not date_posted or date_posted in ["Date not found", "error", "None", None]:
                date_posted = get_date_from_job_details(driver)

            print("Final date_posted used:", date_posted)

            # ✅ SEN AYTGAN TALAB:
            # date topilmasa -> shu jobni SKIP qilib ketadi
            if not date_posted or date_posted in ["Date not found", "error", "None", None]:
                print("⚠️ Date not found -> skipping this job")
                continue

            # Job link + ID
            try:
                job_link = card.find_element(By.CLASS_NAME, "job-card-list__title--link").get_attribute("href")
                match = re.search(r'view/(\d+)', job_link or "")
                job_id = match.group(1) if match else 'Not available'
            except Exception:
                job_link = None
                job_id = 'Not available'

            # Company name
            try:
                company_name_element = WebDriverWait(driver, 8).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__company-name a")
                    )
                )
                company_name = (company_name_element.text or "").strip()
            except Exception:
                company_name = "Unknown"

            # Company logo (from card)
            try:
                img_element = card.find_element(By.XPATH, ".//div[contains(@class, 'ivm-view-attr__img-wrapper')]//img")
                img_url = img_element.get_attribute("src")
            except Exception:
                img_url = None

            # Location
            try:
                location_element = WebDriverWait(driver, 6).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR,
                         ".job-details-jobs-unified-top-card__primary-description-container span > span.tvm__text--low-emphasis:first-child")
                    )
                )
                location = (location_element.text or "").strip()
            except Exception:
                location = None

            # Salary + skills modal
            skillslist = []
            try:
                salary_element = card.find_element(
                    By.XPATH,
                    ".//div[contains(@class, 'artdeco-entity-lockup__metadata')]//span"
                )
                salarytext = (salary_element.text or "").strip()
            except Exception:
                salarytext = '0'

            # Skills modal open
            try:
                expandlist = driver.find_element(By.CLASS_NAME, 'job-details-preferences-and-skills')
                expandlist.click()
                time.sleep(2.0)

                elements = driver.find_elements(
                    By.CLASS_NAME,
                    'job-details-preferences-and-skills__modal-section-insights-list-item'
                )

                for element in elements:
                    element_text = (element.text or "").strip()
                    if not element_text:
                        continue
                    if salarytext and salarytext in element_text:
                        continue
                    if any(x in element_text for x in
                           ['Remote', 'Full-time', 'Intern', 'On-site', 'Hybrid', 'Temporary', 'Contract']):
                        continue
                    skillslist.append(element_text)

                if not skillslist:
                    skillslist.append(None)

                closeexpandlist = WebDriverWait(driver, 6).until(
                    EC.presence_of_element_located((By.XPATH, "//button[@aria-label='Dismiss']"))
                )
                closeexpandlist.click()
            except Exception:
                skillslist = []

            # Description
            try:
                description_element = driver.find_element(By.CSS_SELECTOR, '#job-details')
                description = (description_element.text or "").replace('\n', ' ')
            except Exception:
                description = ''

            # Match tools_list
            try:
                for skill in tools_list:
                    if re.search(rf'\b{re.escape(skill)}\b', description, re.IGNORECASE) and skill not in skillslist:
                        skillslist.append(skill)
            except Exception:
                pass

            # ✅ Append (BUG FIX: data["date_posted"] emas, date_posted!)
            job_data.append({
                "Posted_date": date_posted,
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

            sleep(0.4, 0.9)

    except Exception as e:
        print(f'Error in extraction loop: {e}')

    return job_data
