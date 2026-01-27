import os
import re
import time

import pandas as pd
from dotenv import load_dotenv
from selenium import webdriver

from allfilter import (
    open_all_filters_modal,
    select_all_title_filters_containing_keyword,
    submit_filters,
    select_date_posted_past_month,
)
from classifier import identify_titles_for_df_advanced
from cookies import save_cookies, load_cookies, login_and_save, COOKIE_FILE
from datasearching_english import searchingbykeywords
from pagination_english import pagination
from savetodatabase_english import save_to_csv, save_to_postgres
from utils_english import sleep

# =========================
# ENV
# =========================
load_dotenv()
LI_EMAIL = os.getenv("LI_EMAIL", "").strip()
LI_PASSWORD = os.getenv("LI_PASSWORD", "").strip()

if not LI_EMAIL or not LI_PASSWORD:
    raise RuntimeError("❌ .env ichida LI_EMAIL va LI_PASSWORD bo‘lishi shart")


# =========================
# SALARY NORMALIZER (K -> 000)
# =========================
def expand_k_in_salary(text: str) -> str:
    """
    "??70K/yr - ??75K/yr" -> "70 000/yr - 75 000/yr"
    "£40K/yr" -> "£40 000/yr"
    """
    if text is None:
        return text

    s = str(text).strip()
    if not s:
        return s

    # LinkedIn ba’zan £/€ ni "??" qilib yuboradi
    s = s.replace("??", "")

    def repl(m):
        num = float(m.group(1))
        expanded = int(round(num * 1000))
        return f"{expanded:,}".replace(",", " ")  # 70000 -> "70 000"

    s = re.sub(r"(\d+(?:\.\d+)?)\s*[Kk]\b", repl, s)
    return s


# =========================
# ILLEGAL CHAR FIX
# =========================
def remove_illegal_characters(x):
    s = "" if x is None else str(x)
    return "".join(c for c in s if ord(c) >= 32).strip()


# =========================
# TOOL LIST
# =========================
tools_list = list(set([
    # Animation
    "Autodesk Maya", "Blender", "Cinema 4D", "Houdini", "Toon Boom Harmony",
    "Adobe After Effects", "Adobe Animate", "ZBrush", "Substance Painter", "Marvelous Designer",

    # 3D Modeling
    "Blender", "Autodesk Maya", "3ds Max", "ZBrush", "Cinema 4D",
    "Substance Painter", "Substance Designer", "Quixel Mixer", "Quixel Megascans",
    "RealityCapture", "Metashape",

    # Game Developer
    "Unreal Engine", "Unity", "Godot", "C++", "C#", "Python", "Blender", "Maya",
    "Substance Painter", "Quixel Megascans", "Git", "Perforce",

    # VFX Artist
    "Houdini", "Autodesk Maya", "Nuke", "Adobe After Effects", "Cinema 4D",
    "RealFlow", "Embergen", "PFTrack", "Mocha Pro", "SynthEyes",

    # Digital Art Artist
    "Adobe Photoshop", "Procreate", "Clip Studio Paint", "Krita", "PureRef",
    "Blender", "Wacom", "XP-Pen", "Huion",

    # AI Art
    "Midjourney", "Stable Diffusion", "DALL·E", "Leonardo AI", "Adobe Firefly",
    "Runway", "Pika Labs", "Topaz AI", "Magnific AI", "Upscayl",

    # Unreal Engineer
    "Unreal Engine 5", "Blueprints", "C++", "Quixel Megascans", "World Creator",
    "Gaea", "Lumen", "Nanite", "Movie Render Queue",

    # FX Simulation
    "Houdini", "Embergen", "RealFlow", "Blender Mantaflow", "Phoenix FD",

    # VR / AR
    "Unity", "Unreal Engine", "ARKit", "ARCore", "OpenXR", "Meta Quest SDK",
    "Apple Vision Pro SDK", "HTC Vive SDK", "Blender", "Maya",

    # Cinema 4D
    "Cinema 4D", "Redshift", "Octane Render", "Adobe After Effects",
    "Adobe Illustrator", "X-Particles", "RealFlow",
]))

# =========================
# DRIVER
# =========================
options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

driver = webdriver.Chrome(options=options)
driver.maximize_window()

jobsURL = "https://www.linkedin.com/jobs/"

# =========================
# LOGIN via cookies
# =========================
if not load_cookies(driver):
    print("Cookie topilmadi – login qilinmoqda...")
    login_and_save(driver, LI_EMAIL, LI_PASSWORD)

driver.get(jobsURL)
time.sleep(5)

# =========================
# CONFIG
# =========================
keywordlist = [
    "Animation",
    "3D Modeling",
    "Game Developer",
    "VFX Artist",
    "Digital Art Artist",
    "AI Art",
    "Unreal engineer",
    "FX Simulation",
    "VR/AR",
    "Cinema 4D",
]

final_df = pd.DataFrame()

COUNTRY_LIST = [
    "Japan",
    "UK",
    "Germany",
    "Poland",
    "France",
    "Switzerland",
    "London",
    "Philippines",
    "United States",
    "China",
    "Dubai",
    "Abu Dhabi",
    "Uzbekistan",
    "Kazakhstan",
]

for country in ["UK"]:  # <-- filter country
    for keyword in ["3D Modeling"]:  # <-- filter keyword
        try:
            searchingbykeywords(driver, keyword, country)
            sleep(4, 7)

            print("opening all filters modal...")
            open_all_filters_modal(driver)
            print("opened all filters modal.")

            select_date_posted_past_month(driver)
            sleep(2, 4)

            select_all_title_filters_containing_keyword(driver, keyword)
            time.sleep(3)

            submit_filters(driver)
            time.sleep(4)

            df = pagination(driver, keyword, country, tools_list)

            if df is not None and not df.empty:
                # ✅ Salary K -> 000
                if "Salary Info" in df.columns:
                    df["Salary Info"] = df["Salary Info"].apply(expand_k_in_salary)

                # ✅ Illegal chars clean
                for col in df.columns:
                    df[col] = df[col].apply(remove_illegal_characters)

                final_df = pd.concat([final_df, df], ignore_index=True)

            sleep(1.0, 3)

        except Exception as e:
            print("Xato (session o‘chgan bo‘lishi mumkin):", e)

            if os.path.exists(COOKIE_FILE):
                os.remove(COOKIE_FILE)

            try:
                driver.quit()
            except Exception:
                pass

            driver = webdriver.Chrome(options=options)
            driver.maximize_window()

            login_and_save(driver, LI_EMAIL, LI_PASSWORD)
            driver.get(jobsURL)
            time.sleep(5)
            continue

    sleep(2.2, 5.0)

save_cookies(driver)
driver.quit()

if final_df.empty:
    print("Hech narsa topilmadi (final_df empty).")
    raise SystemExit(0)

save_to_csv(final_df, "nodate.csv")

if "Posted_date" in final_df.columns:
    final_df["Posted_date"] = pd.to_datetime(final_df["Posted_date"], errors="coerce")
    final_df["Posted_date"] = final_df["Posted_date"].dt.strftime("%Y-%m-%d %H:%M:%S")

final_df.index = range(1, len(final_df) + 1)
save_to_csv(final_df, "date.csv")
save_to_postgres(final_df)

final_df["Job Title from List new"] = identify_titles_for_df_advanced(
    final_df,
    title_col="Job Title",
    skills_col="Skills",
)

result = final_df[
    [
        "Posted_date",
        "Job Title from List new",
        "Job Title",
        "Company",
        "Company Logo URL",
        "Country",
        "Location",
        "Skills",
        "Salary Info",
        "Source",
    ]
].copy()

result = result.rename(columns={"Job Title from List new": "Job Title from List"})
result = result.reset_index(drop=True).rename_axis("ID").reset_index()

save_to_csv(result, "result.csv")

print("Finished ✅")
