import random
import time

import pandas as pd
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from dataextraction_english import extractinfo
from datamodification_english import process_job_data


def pagination(driver, keyword, country, tools_list):
    job = []
    try:
        current_url = driver.current_url
        print(f"Initial search URL: {current_url}")

        # Extract from the first page
        print("Extracting from page 1...")
        WebDriverWait(driver, 20).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, ".job-card-container")) > 0
        )
        # Scroll for lazy load (top to bottom)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        extractinfo(driver=driver, keyword=keyword, job_data=job, country=country, tools_list=tools_list)
        print(f'Extracted from page 1: {len(job)} total jobs so far')

        page_num = 1  # Track for logging and delays

        while True:
            page_extracted = False
            max_page_retries = 2

            for retry in range(max_page_retries):
                try:
                    print(
                        f"Attempting to navigate to next page (page {page_num + 1}, retry {retry + 1}/{max_page_retries})")

                    # Scroll to bottom to ensure pagination is visible/loaded
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)

                    # Wait for pagination container
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-search-pagination"))
                    )

                    # Try to click "Next" button
                    next_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='View next page']"))
                    )
                    driver.execute_script("arguments[0].click();", next_button)
                    print(f"Clicked 'Next' button to reach page {page_num + 1}")

                    # Wait for new page load (check for refreshed job cards)
                    WebDriverWait(driver, 20).until(
                        lambda d: len(d.find_elements(By.CSS_SELECTOR, ".job-card-container")) > 0
                    )

                    # Scroll for lazy load (top to bottom)
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    driver.execute_script("window.scrollTo(0, 0);")

                    print(f"Page {page_num + 1} loaded, extracting...")
                    extractinfo(driver=driver, keyword=keyword, job_data=job, country=country, tools_list=tools_list)
                    print(f'Extracted from page {page_num + 1}: {len(job)} total jobs so far')

                    page_num += 1
                    page_extracted = True
                    break  # Success

                except TimeoutException:
                    print(f"No next page available or wait failed for page {page_num + 1} (retry {retry + 1})")
                    if retry < max_page_retries - 1:
                        time.sleep(5)
                    else:
                        # No next page, exit the loop
                        print("No more pages available. Stopping pagination.")
                        # Fall through to end the while loop
                        raise TimeoutException("No next page")  # To break out cleanly
                except WebDriverException as e:
                    print(f"Driver error on next page (retry {retry + 1}): {e}")
                    if retry < max_page_retries - 1:
                        time.sleep(5)
                        driver.refresh()  # Refresh as last resort
                    else:
                        print(f"Skipping next page after driver errors")
                        raise WebDriverException("Max retries exceeded")  # To break out
                except Exception as e:
                    print(f"Unexpected error on next page: {e}")
                    continue

            if not page_extracted:
                break

            # Progressive delay (longer for later pages)
            time.sleep(random.uniform(3 + (page_num * 0.5), 6 + (page_num * 0.5)))

    except (TimeoutException, WebDriverException) as e:
        # Expected: no more pages or max retries
        print(f"Pagination ended normally: {e}")
    except Exception as e:
        print(f"Critical pagination error: {e}")
        # Fallback: Extract current page if not already done
        try:
            extractinfo(driver=driver, keyword=keyword, job_data=job, country=country, tools_list=tools_list)
        except:
            pass
    try:
        df = process_job_data(job)
        print(f"Processed DataFrame with {len(df) if not df.empty else 0} unique jobs")
    except Exception as e:
        print(f"Error processing job data: {e}")
        df = pd.DataFrame()
    return df
