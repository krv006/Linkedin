# aititlefilter_english.py
# DeepSeek API bilan ishlaydigan versiya (2025-noyabr)

import time

import requests

# <<<--- O‘z kalitingni shu yerga yoz --->>>
DEEPSEEK_API_KEY = ""  # https://platform.deepseek.com/api_keys


def identify_title(titles, skills):
    """
    DeepSeek-chat modeliga so‘rov yuboradi va faqat kerakli ro‘yxatni qaytaradi.
    """
    url = "https://api.deepseek.com/v1/chat/completions"

    prompt = f"""
You are an expert in job title matching. Return ONLY a comma-separated list of matched job titles from this exact list (no extra text, no markdown, no numbering):

Backend developer, Frontend developer, Data analyst, Data engineer, Data scientist, AI engineer, Android developer, IOS developer, Game developer, DevOps engineer, IT project manager, Network engineer, Cybersecurity Analyst, Cloud Architect, Full stack developer, QA engineer

Input titles: {titles}
Skills: {skills}

Rules:
- Match using both the job title and the skills.
- If no good match → return "unknown"
- Exactly {len(titles)} items, comma-separated only.
Example output: Backend developer, AI engineer, unknown

Return ONLY the list:
"""

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek-chat",  # DeepSeek uchun to‘g‘ri model
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 512,
        "stream": False
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()

        result = response.json()["choices"][0]["message"]["content"].strip()
        cleaned = [item.strip() for item in result.split(",")]

        # Uzunlikni to‘g‘rilash (DeepSeek ba’zan qo‘shimcha gap qo‘shib yuboradi)
        if len(cleaned) < len(titles):
            cleaned += ["unknown"] * (len(titles) - len(cleaned))
        cleaned = cleaned[:len(titles)]

        print(f"DeepSeek → {cleaned}")
        return cleaned

    except requests.exceptions.HTTPError as err:
        if response.status_code == 401:
            print("DeepSeek: API kalit noto‘g‘ri yoki muddati tugagan!")
        elif response.status_code == 404:
            print("DeepSeek: Model topilmadi → 'deepseek-chat' ishlatilishi kerak.")
        else:
            print(f"DeepSeek HTTP xatosi: {response.status_code} → {response.text}")
        return ["unknown"] * len(titles)
    except Exception as e:
        print(f"DeepSeek ulanish xatosi: {e}")
        return ["unknown"] * len(titles)


def processdf(df, chunk_size=10):
    results = []
    for i in range(0, len(df), chunk_size):
        chunk = df.iloc[i:i + chunk_size]
        titles = chunk["Job Title"].tolist()
        skills = chunk["Skills"].tolist()
        matched_titles = identify_title(titles, skills)

        # Uzunlikni yana bir marta tekshirish (xavfsizlik uchun)
        if len(matched_titles) != len(chunk):
            if len(matched_titles) > len(chunk):
                matched_titles = matched_titles[:len(chunk)]
            else:
                matched_titles.extend(["unknown"] * (len(chunk) - len(matched_titles)))

        results.extend(matched_titles)
        time.sleep(1)  # DeepSeek uchun oddiy delay

    # Yakuniy uzunlikni tekshirish
    if len(results) != len(df):
        diff = len(df) - len(results)
        if diff > 0:
            results.extend(["unknown"] * diff)
        else:
            results = results[:len(df)]

    return results


def filtercolumns(df, keywordlist):
    try:
        results = processdf(df, 10)
        df["Job Title from List"] = results

        # NaN va boshqa tozalash (avvalgidek)
        df['Salary Info'] = df['Salary Info'].fillna(0)
        df = df.fillna('Unknown')

        filtered_df = df[
            df["Job Title from List"].isin(keywordlist) &
            (df["Job Title from List"] != "unknown")
            ]

        print(f"Filtered to {len(filtered_df)} jobs matching keywords.")
        return filtered_df

    except Exception as e:
        print(f"Error while filtering columns: {e}")
        print("Returning original DF without filtering.")
        return df
