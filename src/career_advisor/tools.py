import os
import re
from typing import Any, Dict, List
import requests
from ddgs import DDGS
from .observability import observer
from .registry import registry

def search_web(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    max_results = max(1, min(int(max_results), 8))

    try:
        results = []

        with DDGS() as ddgs:
            search_results = ddgs.text(
                query,
                max_results=max_results,
            )

            for item in search_results:
                results.append(
                    {
                        "title": item.get("title", ""),
                        "url": item.get("href", ""),
                        "snippet": item.get("body", ""),
                    }
                )

        return results

    except Exception as exc:
        observer.log(
            "search_web_warning",
            "search_web",
            query=query,
            error=str(exc),
        )

        return []



registry.register(
    name="search_web",
    description=(
        "Search the public web for current career roles, skill requirements, "
        "technology trends, and labor-market information."
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "max_results": {
                "type": "integer",
                "minimum": 1,
                "maximum": 8,
                "default": 5,
            },
        },
        "required": ["query"],
    },
    function=search_web,
)

def calculate_match_score(
    user_skills: List[str],
    required_skills: List[str],
) -> Dict[str, Any]:
    normalize = lambda values: {
        re.sub(r"[^a-z0-9+#. ]", "", value.lower()).strip()
        for value in values
        if value and value.strip()
    }

    user = normalize(user_skills)
    required = normalize(required_skills)

    if not required:
        return {
            "score": 0.0,
            "matched_skills": [],
            "missing_skills": [],
        }

    matched = sorted(user.intersection(required))
    missing = sorted(required.difference(user))
    score = round((len(matched) / len(required)) * 100, 1)

    return {
        "score": score,
        "matched_skills": matched,
        "missing_skills": missing,
    }

registry.register(
    name="calculate_match_score",
    description="Calculate a deterministic skill-match score for a career role.",
    parameters={
        "type": "object",
        "properties": {
            "user_skills": {
                "type": "array",
                "items": {"type": "string"},
            },
            "required_skills": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": ["user_skills", "required_skills"],
    },
    function=calculate_match_score,
)

def prioritize_skill_gaps(
    missing_skills: List[str],
    high_priority_skills: List[str],
) -> Dict[str, List[str]]:
    missing = [skill.strip() for skill in missing_skills if skill.strip()]
    priority_set = {skill.lower().strip() for skill in high_priority_skills}

    high = [skill for skill in missing if skill.lower() in priority_set]
    standard = [skill for skill in missing if skill.lower() not in priority_set]

    return {
        "high_priority": high,
        "standard_priority": standard,
    }

registry.register(
    name="prioritize_skill_gaps",
    description="Prioritize missing career skills using a supplied high-priority skill list.",
    parameters={
        "type": "object",
        "properties": {
            "missing_skills": {
                "type": "array",
                "items": {"type": "string"},
            },
            "high_priority_skills": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": ["missing_skills", "high_priority_skills"],
    },
    function=prioritize_skill_gaps,
)


latest_job_results = []

def _get_jooble_key():
    key = os.getenv("JOOBLE_API_KEY")
    if not key:
        raise ValueError("JOOBLE_API_KEY was not found. Set it as an environment variable.")
    return key

def search_jobs_external(query: str, location: str, limit: int = 10) -> Dict[str, Any]:
    global latest_job_results
    url = f"https://sa.jooble.org/api/{_get_jooble_key()}"
    response = requests.post(url, json={"keywords": query, "location": location, "page": 1}, timeout=20)
    response.raise_for_status()
    data = response.json()
    jobs = data.get("jobs", [])[:limit]
    cleaned_jobs = [{
        "title": job.get("title", ""),
        "company": job.get("company", "").strip() if len(job.get("company", "").strip()) > 1 else "Not specified",
        "location": job.get("location", ""), "snippet": job.get("snippet", ""),
        "salary": job.get("salary", ""), "source": job.get("source", ""),
        "link": job.get("link", ""), "updated": job.get("updated", ""),
    } for job in jobs]
    latest_job_results = cleaned_jobs.copy()
    return {"status":"success","query":query,"location":location,"total_available":data.get("totalCount",0),"returned_jobs":len(cleaned_jobs),"jobs":cleaned_jobs}

registry.register(
    name="search_jobs_external",
    description="Search current job vacancies using the Jooble Saudi Arabia Jobs API. Use this tool when real job-market evidence is needed for a career recommendation.",
    parameters={"type":"object","properties":{"query":{"type":"string"},"location":{"type":"string"},"limit":{"type":"integer","minimum":1,"maximum":25,"default":10}},"required":["query","location"]},
    function=search_jobs_external,
)
