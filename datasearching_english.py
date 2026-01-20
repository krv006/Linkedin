import time


def searchingbykeywords(driver, keyword, location):
    """
    LinkedIn 2025-yil holatiga mos – URL orqali to‘g‘ridan-to‘g‘ri Past 24 hours bilan qidiruv.
    Bu usul selector o‘zgarishidan qat’iy nazar ishlaydi.
    """
    # Bo‘sh joylarni %20 ga almashtirish
    keyword_encoded = keyword.strip().replace(" ", "%20")
    location_encoded = location.strip().replace(" ", "%20")

    # f_TP=1 → Past 24 hours filtri avtomatik qo‘yiladi
    search_url = (
        f"https://www.linkedin.com/jobs/search/?keywords={keyword_encoded}"
        f"&location={location_encoded}&f_TP=1"
    )

    print(f"Qidiruv boshlandi → {keyword} | {location}")
    driver.get(search_url)
    # Qo‘shimcha kutish – LinkedIn sekin yuklanishi mumkin
    time.sleep(4)
