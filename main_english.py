import os
import time

import pandas as pd
from selenium import webdriver

from allfilter import open_all_filters_modal, select_all_title_filters_containing_keyword, submit_filters, \
    select_date_posted_past_month
from classifier import identify_titles_for_df_advanced
from cookies import save_cookies, load_cookies, login_and_save, COOKIE_FILE
from datasearching_english import searchingbykeywords
from pagination_english import pagination
from savetodatabase_english import save_to_csv, save_to_postgres
from utils_english import sleep

tools_list = list(set([
    ".NET", "Adobe XD", "Airflow", "Alamofire", "Alexa Skills Kit", "Amplify", "Ansible",
    "Apache", "Apache Kafka", "Apache Airflow", "Apache Nifi", "Apache NiFi", "Apache Storm",
    "AppDynamics", "Argo", "Asana", "Athena", "AWS", "AWS SageMaker", "Azure", "Azure DevOps",
    "Azure ML", "Bash", "BigQuery", "Bizagi", "Bitbucket", "Blender", "Bootstrap", "C++",
    "Caffe", "Cassandra", "Chef", "Cisco ASA", "Cisco Packet Tracer", "CircleCI", "ClickHouse",
    "CloudFormation", "CloudWatch", "Combine", "Confluence", "CoreData", "CSS", "Dagger",
    "DataRobot", "Databricks", "Datadog", "dbt (data build tool)", "Django", "Docker",
    "Docker Swarm", "Domo", "Draw.io", "Dynatrace", "Eclipse", "ElasticSearch", "Excel",
    "Fargate", "FastAPI", "Firebase", "Figma", "Flask", "GCP", "Git", "GitHub",
    "GitLab CI/CD", "Glide", "Golang", "Google AI Platform", "Google Analytics",
    "Google Tag Manager", "Gradle", "Grafana", "Graylog", "H2O.ai", "Hadoop", "Helm",
    "Heroku", "HubSpot", "Hugging Face", "IIS", "Informatica", "Informatica Cloud",
    "Insomnia", "IntelliJ IDEA", "iOS SDK", "Jenkins", "Jenkins X", "JIRA", "JMeter",
    "Jupyter", "Jupyter Notebook", "JUnit", "Kali Linux", "Keras", "Kibana", "KNIME",
    "Kotlin", "Kubernetes", "Lambda", "Linux", "Logstash", "Looker", "LookML",
    "Lucidchart", "MATLAB", "Marketo", "Maven", "Metasploit", "Microsoft Cognitive Services",
    "Microsoft Project", "Minitab", "MongoDB", "MongoDB Atlas", "Mocha", "Mulesoft",
    "Nagios", "Netlify", "New Relic", "Nexus", "Nginx", "Node.js", "Notion",
    "NumPy", "Objective-C", "OpenCV", "OpenShift", "OpenStack", "Oracle", "Oracle Cloud",
    "Oracle EBS", "Pandas", "Palo Alto Networks", "PeopleSoft", "Podman", "PostgreSQL",
    "Power BI", "Power Automate", "PowerApps", "PowerShell", "Presto", "Prometheus",
    "Puppet", "PyCharm", "Python", "Pytest", "PyTorch", "QlikView",
    "Qlik Sense", "R", "R Programming", "R Studio", "Rancher", "RapidMiner", "React",
    "Red Hat Enterprise Linux", "Redshift", "Retrofit", "Ruby", "RxJava", "Salesforce",
    "SAP", "SAP Analytics Cloud", "Scala", "Scikit-learn", "SciPy", "Selenium",
    "Snyk", "Snowflake", "Spark", "Splunk", "Spyder", "SQLite", "SSH", "SQL",
    "SSL", "Stata", "Superset", "Swagger", "Swift", "Tableau", "Tableau Prep",
    "Tailwind CSS", "Talend", "TensorFlow", "Terraform", "Trello", "Travis CI",
    "Unity", "Unreal Engine", "Vercel", "Visual Studio", "VS Code", "Vue.js",
    "Wireshark", "Windows Server", "Xcode", "C#", "ASP.NET", "Java", "Spring",
    "JavaScript", "Angular", "Ruby on Rails", "PHP", "Laravel", "Gin", "Qt",
    "SwiftUI", "Kotlin", "Android SDK", "TypeScript", "NestJS", "Shiny", "Scala",
    "Play", "Elixir", "Phoenix", "Clojure", "Compojure", "Rust", "Rocket",
    "Dart", "Flutter", "Haskell", "Yesod", "Julia", "HTTP.jl", "Lua", "LÖVE",
    "Shell", "PowerShell", "Cocoa", "Simulink", "Assembly", "NASM", "COBOL",
    "OpenCOBOL", "Pascal", "Free Pascal", "F#", "ASP.NET Core", "Blazor",
    "Visual Basic .NET", "Windows Forms", "Delphi", "Lazarus", "ActionScript",
    "Flex", "Groovy", "Grails", "VBScript", "ASP Classic", "Smalltalk", "Pharo",
    "Scheme", "Racket", "Prolog", "SWI-Prolog", "Ada", "GNAT", "Nim",
    "Nimble", "Crystal", "Lucky", "Solidity", "Truffle", "V", "Vlang",
    "Hibernate", "Sinatra", "Echo", "Vapor", "Ktor", "Symfony", "Actix",
    "Aqueduct", "Nerves", "Play Framework", "Giraffe", "SSRS", "Google Data Studio",
    "Mode Analytics", "IBM Cognos Analytics", "Azure Data Factory (ADF)", "SSIS",
    "Matillion", "Kafka Connect", "PowerBI", "VBA"
]))

options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

driver = webdriver.Chrome(options=options)
driver.maximize_window()

email = 'hp7070a@gmail.com'
password = 'J5gcdE5ysU_ub7R'
jobsURL = 'https://www.linkedin.com/jobs/'

if not load_cookies(driver):
    print("Cookie topilmadi – birinchi marta login qilinmoqda...")
    login_and_save(driver, email, password)

driver.get(jobsURL)
time.sleep(5)

keywordlist = [
    'Animation',
    '3D Modeling',
    'Game Developer',
    'VFX Artist',
    'Digital Art Artist',
    "AI Art",
    "Unreal engineer",
    "FX Simulation",
    "VR/AR",
    "Cinema 4D"
]

final_df = pd.DataFrame()
countrylist = ["UK", 'US', 'Uzbekistan']

# ─────────────── SCRAPING LOOP ───────────────
for country in ["UK"]:
    for keyword in ['3D Modeling']:
        try:
            searchingbykeywords(driver, keyword, country)
            sleep(4, 7)
            print('opeing all filters modal...')
            open_all_filters_modal(driver)
            print('opened all filters modal.')
            select_date_posted_past_month(driver)
            sleep(2, 4)
            select_all_title_filters_containing_keyword(driver, keyword)
            time.sleep(3)
            submit_filters(driver)
            time.sleep(4)
            df = pagination(driver, keyword, country, tools_list)

            if df is not None and not df.empty:
                final_df = pd.concat([final_df, df], ignore_index=True)

            sleep(1.0, 3)

        except Exception as e:
            print("Xato yuz berdi (session o‘chgan bo‘lishi mumkin):", e)

            if os.path.exists(COOKIE_FILE):
                os.remove(COOKIE_FILE)

            driver.quit()
            driver = webdriver.Chrome(options=options)
            driver.maximize_window()
            login_and_save(driver, email, password)
            driver.get(jobsURL)
            time.sleep(5)
            continue

    sleep(2.2, 5.0)

save_cookies(driver)
driver.quit()

print("Before datetime convert:", final_df[['Posted_date']].head(10))
save_to_csv(final_df, "nodate.csv")

# ─────────────── DATETIME FIX (WARNING YUQ) ───────────────
final_df['Posted_date'] = pd.to_datetime(final_df['Posted_date'], errors='coerce')
final_df['Posted_date'] = final_df['Posted_date'].dt.strftime('%Y-%m-%d %H:%M:%S')
final_df.index = range(1, len(final_df) + 1)
save_to_csv(final_df, "date.csv")
save_to_postgres(final_df)


# ─────────────── ILLEGAL CHAR FIX (applymap WARNING YUQ) ───────────────
def remove_illegal_characters(text):
    return "".join(c for c in text if ord(c) >= 32)


for col in final_df.columns:
    final_df[col] = final_df[col].astype(str).apply(remove_illegal_characters)

print(final_df.shape)
print(final_df.head())

final_df['Job Title from List new'] = identify_titles_for_df_advanced(final_df, title_col="Job Title",
                                                                      skills_col="Skills")
result = final_df[[
    'Posted_date',
    'Job Title from List new',
    'Job Title',
    'Company',
    'Company Logo URL',
    'Country',
    'Location',
    'Skills',
    'Salary Info',
    'Source'
]].copy()

result = result.rename(columns={
    'Posted_date': 'Posted_date',
    'Job Title from List new': 'Job Title from List',
    'Job Title': 'Job Title',
    'Company Logo URL': 'Company Logo URL',
    'Salary Info': 'Salary Info'
})

keywordlist = [
    'Animation',
    '3D Modeling',
    'Game Developer',
    'VFX Artist',
    'Digital Art Artist',
    "AI Art",
    "Unreal engineer",
    "FX Simulation",
    "VR/AR",
    "Cinema 4D"
]


def normalize_job_title(title, mapping):
    if pd.isna(title):
        return title
    title_lower = str(title).lower().strip()
    return mapping.get(title_lower, title)


title_mapping = {}
for official in keywordlist:
    title_mapping[official.lower()] = official

result['Job Title from List'] = result['Job Title from List'].apply(
    lambda x: normalize_job_title(x, title_mapping))

result = result[
    result['Job Title from List'].isin(keywordlist)
].copy()
result = result.reset_index(drop=True).rename_axis('ID').reset_index()

save_to_csv(result, "result.csv")

print("Finished")
