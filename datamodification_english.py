import pandas as pd


def changedatetype(date_element):
    words = date_element.split()
    difference = 0
    changed_date = None

    for word in words:
        if word.isdigit():
            difference = int(word)

    if "day" in date_element:
        changed_date = pd.Timestamp.now() - pd.Timedelta(days=difference)
    elif "minute" in date_element:
        changed_date = pd.Timestamp.now() - pd.Timedelta(minutes=difference)
    elif "second" in date_element:
        changed_date = pd.Timestamp.now() - pd.Timedelta(seconds=difference)
    elif "hour" in date_element:
        changed_date = pd.Timestamp.now() - pd.Timedelta(hours=difference)
    elif "week" in date_element:
        changed_date = pd.Timestamp.now() - pd.Timedelta(weeks=difference)
    elif 'month' in date_element:
        changed_date = pd.Timestamp.now() - pd.DateOffset(months=difference)

    if changed_date is None:
        return 'error'

    return changed_date.strftime('%Y-%m-%d %H:%M:%S')


def process_job_data(job_data):
    df = pd.DataFrame(job_data)
    if 'Skills' not in df.columns:
        df['Skills'] = ''
    df['Skills'] = df['Skills'].apply(
        lambda x: ', '.join([str(skill) for skill in x if skill]) if isinstance(x, list) else ''
    )

    dfclean = df.drop_duplicates(subset='JobID', keep='first')[[
        'Posted_date', 'Job Title from List', 'Job Title', 'Company',
        'Company Logo URL', 'Country', 'Location', 'Skills', 'Salary Info', 'Source'
        # , 'Description'
    ]]

    return dfclean
