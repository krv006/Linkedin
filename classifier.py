import difflib
import re
from typing import List, Iterable, Dict, Set

# ---------- Config ----------
VALID_TITLES = ['data engineer', 'android developer', 'data scientist',
                'ai engineer', 'game developer', 'ios developer',
                'devops engineer', 'cybersecurity analyst',
                'network engineer', 'cloud architect', 'full stack developer',
                'data analyst', 'frontend developer', 'backend developer', 'it project manager', "qa engineer"]
# Weights & thresholds
W_ALIAS = 14
W_TITLE_EXACT = 10
W_TOOL_EXACT = 8
W_TOOL_FUZZY_MAX = 5  # scaled by similarity (0..1)
W_PAIR_BONUS = 6  # co-occurrence bonus inside a role
NEG_PENALTY = 7
UNKNOWN_THR = 16
FULLSTACK_THR = 20  # both FE and BE scores ≥ this → full stack

_ws = re.compile(r"\s+")
_punct = re.compile(r"[^\w#+./-]+")


def norm_text(x: str) -> str:
    if x is None: return ""
    return _ws.sub(" ", _punct.sub(" ", x.lower())).strip()


def canon(x: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (x or "").lower())


def contains_word(text: str, term: str) -> bool:
    term = norm_text(term)
    return (term in text) if " " in term else re.search(rf"\b{re.escape(term)}\b", text) is not None


def tokenize_skills(sk: Iterable[str] | str) -> Set[str]:
    if sk is None: return set()
    parts = re.split(r"[,\|;/\n]+", sk) if isinstance(sk, str) else [str(s) for s in sk]
    return {p.strip() for p in parts if p and p.strip()}


def fuzzy_sim(a: str, b: str) -> float:
    # 0..1 similarity using difflib ratio
    return difflib.SequenceMatcher(a=canon(a), b=canon(b)).ratio()


# ---------- Knowledge ----------
FAMILIES = {
    "software": {
        "members": {"backend developer", "frontend developer", "full stack developer",
                    "android developer", "ios developer", "game developer", "qa engineer"},
    },
    "data": {
        "members": {"data analyst", "data engineer", "data scientist", "ai engineer"},
    },
    "infra": {
        "members": {"devops engineer", "cloud architect", "network engineer", "cybersecurity analyst"},
    },
    "management": {
        "members": {"it project manager"},
    }
}

TITLE_ALIASES = {
    "backend developer": {"backend developer", "back end", "server-side", "api developer"},
    "frontend developer": {"frontend developer", "front end", "ui developer", "web developer"},
    "full stack developer": {"full stack", "full-stack", "mern", "mean"},
    "data analyst": {"data analyst", "bi analyst", "business intelligence analyst"},
    "data engineer": {"data engineer", "etl developer", "data pipeline engineer"},
    "data scientist": {"data scientist", "ml scientist", "ml researcher"},
    "ai engineer": {"ai engineer", "llm engineer", "generative ai engineer"},
    "android developer": {"android developer", "android engineer"},
    "ios developer": {"ios developer", "ios engineer"},
    "game developer": {"game developer", "game engineer"},
    "devops engineer": {"devops", "sre"},
    "it project manager": {"project manager", "it pm", "scrum master"},
    "network engineer": {"network engineer", "network specialist"},
    "cybersecurity analyst": {"security analyst", "soc analyst"},
    "cloud architect": {"cloud architect", "solutions architect"},
    "qa engineer": {"qa engineer", "sdet", "test automation engineer"},
}

TITLE_KW = {
    "backend developer": {"backend", "server", "api", "microservice", ".net", "spring", "django", "fastapi", "node"},
    "frontend developer": {"frontend", "react", "angular", "vue", "typescript", "javascript", "ui"},
    "full stack developer": {"full stack", "full-stack"},
    "data analyst": {"analyst", "analytics", "bi"},
    "data engineer": {"data engineer", "etl", "elt", "pipeline"},
    "data scientist": {"scientist", "ml", "machine learning"},
    "ai engineer": {"ai", "llm", "generative"},
    "android developer": {"android"},
    "ios developer": {"ios"},
    "game developer": {"game", "unity", "unreal"},
    "devops engineer": {"devops", "sre"},
    "it project manager": {"project manager", "pm", "scrum"},
    "network engineer": {"network"},
    "cybersecurity analyst": {"security", "soc"},
    "cloud architect": {"architect", "cloud"},
    "qa engineer": {"qa", "test", "sdet"},
}

ROLE_TOOLS = {
    "backend developer": {"java", "spring", ".net", "asp.net", "c#", "node.js", "express", "django", "flask", "fastapi",
                          "golang", "gin", "php", "laravel", "ruby on rails", "postgresql", "mysql", "oracle", "sqlite",
                          "redis", "nginx", "grpc", "swagger", "hibernate"},
    "frontend developer": {"react", "next.js", "angular", "vue.js", "typescript", "javascript", "html", "css",
                           "tailwind css",
                           "bootstrap", "figma", "storybook", "vercel", "netlify", "blazor"},
    "full stack developer": {"react", "angular", "vue.js", "typescript", "javascript", "node.js", "express", "django",
                             "spring", ".net", "asp.net", "laravel", "sql", "postgresql", "mysql"},
    "data analyst": {"excel", "power bi", "tableau", "tableau prep", "qlik sense", "qlikview", "looker", "lookml",
                     "mode analytics", "google data studio", "ssrs", "sql", "dax"},
    "data engineer": {"apache airflow", "airflow", "dbt (data build tool)", "dbt", "spark", "pyspark", "kafka",
                      "apache kafka",
                      "kafka connect", "databricks", "glue", "snowflake", "bigquery", "redshift", "hadoop", "hive",
                      "presto",
                      "athena", "azure data factory (adf)", "ssis", "talend", "informatica", "informatica cloud", "gcp",
                      "aws",
                      "azure", "kubernetes", "docker", "terraform", "git", "gitlab ci/cd", "jenkins", "circleci",
                      "argo", "helm"},
    "data scientist": {"python", "pandas", "numpy", "scikit-learn", "scipy", "matlab", "r", "jupyter",
                       "jupyter notebook",
                       "pytorch", "tensorflow", "keras", "xgboost", "h2o.ai"},
    "ai engineer": {"hugging face", "transformer", "onnx", "aws sagemaker", "sagemaker", "openai", "rag", "vector db",
                    "langchain", "azure ml", "google ai platform"},
    "android developer": {"android sdk", "kotlin", "java", "retrofit", "rxjava", "gradle"},
    "ios developer": {"ios sdk", "swift", "swiftui", "objective-c", "combine", "xcode", "cocoa"},
    "game developer": {"unity", "unreal engine", "c#", "c++", "shader"},
    "devops engineer": {"docker", "kubernetes", "helm", "terraform", "ansible", "chef", "puppet", "jenkins",
                        "github actions",
                        "gitlab ci/cd", "travis ci", "circleci", "argo", "prometheus", "grafana", "graylog",
                        "elasticsearch",
                        "logstash", "kibana", "cloudformation", "cloudwatch", "nginx", "iis", "fargate", "openshift",
                        "openstack",
                        "rancher", "podman"},
    "it project manager": {"jira", "asana", "trello", "microsoft project", "confluence", "notion", "azure devops"},
    "network engineer": {"cisco asa", "wireshark", "routing", "switching", "bgp", "ospf", "ssh", "windows server",
                         "nginx", "apache", "cisco packet tracer"},
    "cybersecurity analyst": {"kali linux", "metasploit", "splunk", "snyk", "palo alto networks", "iam", "siem"},
    "cloud architect": {"aws", "azure", "gcp", "cloudformation", "terraform", "helm", "eks", "aks", "gke", "cloudwatch",
                        "prometheus", "grafana", "kubernetes"},
    "qa engineer": {"selenium", "cypress", "playwright", "pytest", "jmeter", "postman", "insomnia"},
}

NEGATIVE_HINTS = {
    "backend developer": {"react", "angular", "vue", "tailwind", "css", "html", "figma", "swift", "kotlin", "ios",
                          "android", "swiftui"},
    "frontend developer": {"spring", "django", "flask", "fastapi", ".net", "asp.net", "java", "c#", "kafka", "airflow",
                           "spark", "docker",
                           "kubernetes", "helm", "terraform", "nginx", "grpc"},
    "full stack developer": {"pytorch", "tensorflow", "keras", "langchain", "hugging face", "tableau", "power bi",
                             "qlik", "looker"},
    "data analyst": {"airflow", "spark", "kafka", "kubernetes", "docker", "dbt", "pytorch", "tensorflow", "keras",
                     "langchain",
                     "kafka connect", "terraform", "helm"},
    "data engineer": {"power bi", "tableau", "qlik", "looker", "dax", "react", "angular", "vue", "swift", "kotlin",
                      "swiftui"},
    "data scientist": {"power bi", "tableau", "qlik", "looker", "dax", "terraform", "helm", "ansible"},
    "ai engineer": {"power bi", "tableau", "qlik", "looker", "dax", "swift", "kotlin", "ios", "android"},
    "android developer": {"swift", "ios", "objective-c", "swiftui"},
    "ios developer": {"kotlin", "android", "rxjava"},
    "game developer": {"tableau", "power bi", "qlik", "looker"},
    "devops engineer": {"power bi", "tableau", "qlik", "looker", "figma", "storybook", "pytorch", "tensorflow", "keras",
                        "langchain"},
    "it project manager": {"pytorch", "tensorflow", "kotlin", "swift", "react", "angular", "django", "spring", "spark",
                           "airflow",
                           "kubernetes", "terraform"},
    "network engineer": {"react", "angular", "tableau", "power bi", "scikit-learn", "pytorch", "tensorflow", "django",
                         "spring"},
    "cybersecurity analyst": {"tableau", "power bi", "react", "angular", "figma"},
    "cloud architect": {"power bi", "tableau", "qlik", "looker", "swift", "kotlin", "ios", "android"},
    "qa engineer": {"power bi", "tableau", "qlik", "looker", "airflow", "spark", "dbt"},
}

# Strong precision constraints
MUST_HAVE = {
    "android developer": [{"android sdk", "kotlin", "java"}],  # any token from set suffices
    "ios developer": [{"ios sdk", "swift", "objective-c"}],
    "network engineer": [{"cisco", "cisco asa", "wireshark", "routing", "switching"}],
}
MUST_NOT = {
    "it project manager": [{"hands-on dev only"}],  # placeholder example for future use
}

# Pairwise bonuses (co-occurrence boosts inside a role)
PAIR_BONUS = {
    "backend developer": [("api", "swagger"), ("spring", ".net"), ("django", "postgresql"), ("node.js", "express")],
    "frontend developer": [("react", "typescript"), ("angular", "rxjs"), ("vue.js", "vuex")],
    "data engineer": [("airflow", "spark"), ("kafka", "spark"), ("dbt", "snowflake"), ("databricks", "spark")],
    "devops engineer": [("kubernetes", "helm"), ("terraform", "aws"), ("prometheus", "grafana")],
    "qa engineer": [("selenium", "pytest"), ("cypress", "typescript")],
}


# ---------- Scoring ----------
def score_alias(title_txt: str, role: str) -> float:
    if not role or role not in TITLE_ALIASES:
        return 0.0
    return max(
        (W_ALIAS * fuzzy_sim(title_txt, a))
        for a in TITLE_ALIASES[role]
    ) if TITLE_ALIASES[role] else 0.0


def score_title_kw(title_txt: str, role: str) -> float:
    return sum(W_TITLE_EXACT for k in TITLE_KW[role] if contains_word(title_txt, k))


def score_tools(skills: Set[str], role: str) -> float:
    if not skills: return 0.0
    exact, fuzzy = 0.0, 0.0
    for s in skills:
        for tool in ROLE_TOOLS[role]:
            if canon(s) == canon(tool):
                exact += W_TOOL_EXACT
            else:
                sim = fuzzy_sim(s, tool)
                if sim >= 0.86:  # high-confidence fuzzy
                    fuzzy += W_TOOL_FUZZY_MAX * sim
    return exact + fuzzy


def score_negatives(text: str, skills: Set[str], role: str) -> float:
    if role not in NEGATIVE_HINTS: return 0.0
    negs = NEGATIVE_HINTS[role]
    hits = 0
    hits += sum(1 for k in negs if contains_word(text, k))
    skill_canon = {canon(x) for x in skills}
    neg_canon = {canon(k) for k in negs}
    hits += sum(1 for c in skill_canon if c in neg_canon)
    return -NEG_PENALTY * hits


def score_pairs(skills: Set[str], role: str) -> float:
    if role not in PAIR_BONUS: return 0.0
    toks = {canon(x) for x in skills}
    bonus = 0.0
    for a, b in PAIR_BONUS[role]:
        if canon(a) in toks and canon(b) in toks:
            bonus += W_PAIR_BONUS
    return bonus


def pass_must_have(skills: Set[str], role: str) -> bool:
    reqs = MUST_HAVE.get(role, [])
    if not reqs: return True
    toks = {canon(x) for x in skills}
    return any(any(canon(opt) in toks for opt in group) for group in reqs)


# ---------- Hierarchical selection ----------
def family_gate(title_txt: str) -> Set[str]:
    """Gate roles by coarse family using title cues (soft—fallback to all if empty)."""
    t = set()
    if re.search(r"\b(project manager|scrum|pmp|roadmap)\b", title_txt): t.add("management")
    if re.search(r"\b(data|analyst|analytics|ml|ai|scientist)\b", title_txt): t.add("data")
    if re.search(r"\b(devops|sre|cloud|network|security)\b", title_txt): t.add("infra")
    if re.search(r"\b(front|back|full|android|ios|game|qa|developer|engineer)\b", title_txt): t.add("software")
    return t or set(FAMILIES.keys())


def candidate_roles(title_txt: str) -> Set[str]:
    fams = family_gate(title_txt)
    cand = set()
    for f in fams:
        cand |= FAMILIES[f]["members"]
    return cand


# ---------- Main ----------
def identify_title_rule_based_advanced(titles: List[str], skills: List[Iterable[str] | str]) -> List[str]:
    out = []
    for title, skill in zip(titles, skills):
        title_txt = norm_text(str(title))
        skill_set = tokenize_skills(skill)

        cands = list(candidate_roles(title_txt))
        scores: Dict[str, float] = {}
        for r in cands:
            if not pass_must_have(skill_set, r):
                scores[r] = -1e9  # hard fail
                continue
            s = 0.0
            s += score_alias(title_txt, r)
            s += score_title_kw(title_txt, r)
            s += score_tools(skill_set, r)
            s += score_pairs(skill_set, r)
            s += score_negatives(title_txt, skill_set, r)
            scores[r] = s

        # full stack resolver
        if scores.get("backend developer", 0) >= FULLSTACK_THR and scores.get("frontend developer", 0) >= FULLSTACK_THR:
            out.append("full stack developer")
            continue

        # select best with deterministic tie-break: alias > title_kw > tools
        best = None
        best_score = -1e9
        for r in VALID_TITLES:

            if r not in scores:  # gated out
                continue
            if scores[r] > best_score:
                best, best_score = r, scores[r]
            elif scores[r] == best_score and best is not None and r is not None:
                a1 = score_alias(title_txt, r)
                a2 = score_alias(title_txt, best)

                if a1 != a2:
                    if a1 > a2: best, best_score = r, scores[r]
                    continue
                t1 = score_title_kw(title_txt, r)
                t2 = score_title_kw(title_txt, best)
                if t1 > t2:
                    best, best_score = r, scores[r]

        out.append(best if (best is not None and best_score >= UNKNOWN_THR) else "unknown")

    return out


# Convenience wrapper for DataFrame
def identify_titles_for_df_advanced(df, title_col="Job Title", skills_col="Skills"):
    return identify_title_rule_based_advanced(
        df[title_col].astype(str).tolist(),
        df[skills_col].tolist()
    )
