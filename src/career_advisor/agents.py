from .base_agent import BaseAgent
from .prompts import PROFILE_PROMPT, CAREER_RESEARCH_PROMPT, SKILL_GAP_PROMPT, ROADMAP_PROMPT, REVIEWER_PROMPT, WRITER_PROMPT

profile_agent = BaseAgent(
    name="ProfileAgent",
    system_prompt=PROFILE_PROMPT,
    max_steps=2,
)

career_research_agent = BaseAgent(
    name="CareerResearchAgent",
    system_prompt=CAREER_RESEARCH_PROMPT,
    allowed_tools=["search_web", "search_jobs_external"],
    max_steps=4,
    max_tool_calls=2,
)

skill_gap_agent = BaseAgent(
    name="SkillGapAgent",
    system_prompt=SKILL_GAP_PROMPT,
    allowed_tools=["calculate_match_score", "prioritize_skill_gaps"],
    max_steps=4,
    max_tool_calls=2,
)

roadmap_agent = BaseAgent(
    name="RoadmapAgent",
    system_prompt=ROADMAP_PROMPT,
    max_steps=2,
)

reviewer_agent = BaseAgent(
    name="ReviewerAgent",
    system_prompt=REVIEWER_PROMPT,
    max_steps=2,
)

writer_agent = BaseAgent(
    name="WriterAgent",
    system_prompt=WRITER_PROMPT,
    max_steps=2,
)
