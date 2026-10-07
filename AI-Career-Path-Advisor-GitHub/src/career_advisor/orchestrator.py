import json
from typing import Any
from .agents import profile_agent, career_research_agent, skill_gap_agent, roadmap_agent, reviewer_agent, writer_agent
from .observability import observer
from .tools import latest_job_results

class CareerAdvisorOrchestrator:
    def __init__(self, rag):
        self.max_revision_rounds = 1
        self.rag = rag

    @staticmethod
    def _pack(title: str, value: Any) -> str:
        return f"\n\n===== {title} =====\n{value}"

    @staticmethod
    def _get_review_decision(review: str) -> str:
        match = re.search(r"\b(PASS|REVISE)\b", review.upper())

        if match:
            return match.group(1)

        return "PASS"

    def run(self, user_request: str) -> Dict[str, Any]:
        observer.log(
            "orchestrator_start",
            "Orchestrator",
            request=user_request,
        )

        # Clear job results from any previous run
        latest_job_results.clear()

        # Analyze the user profile
        profile = profile_agent.run(user_request)["answer"]

        # Retrieve relevant career knowledge from the PDF RAG layer
        rag_results = self.rag.retrieve(
            user_request,
            top_k=3,
        )

        # Format retrieved PDF knowledge for the agents
        rag_context = "\n\n".join(
            [
                f"Source: {item['source']}\n"
                f"Page: {item['page']}\n"
                f"Knowledge: {item['content']}\n"
                f"Retrieval Score: {item['retrieval_score']:.3f}"
                for item in rag_results
            ]
        )

        observer.log(
            "rag_retrieval",
            "Orchestrator",
            retrieved_documents=len(rag_results),
            sources=[
                f"{item['source']} - Page {item['page']}"
                for item in rag_results
            ],
        )

        research_task = (
            "Analyze the following user profile and research suitable career paths. "
            "Use the retrieved career knowledge as additional grounded context."
            + self._pack("USER PROFILE", profile)
            + self._pack("RETRIEVED CAREER KNOWLEDGE", rag_context)
        )

        research = career_research_agent.run(research_task)["answer"]

        gap_task = (
            "Perform a skill-gap analysis using the profile and career research."
            + self._pack("USER PROFILE", profile)
            + self._pack("CAREER RESEARCH", research)
        )

        gaps = skill_gap_agent.run(gap_task)["answer"]

        roadmap_task = (
            "Create a development roadmap using the following evidence."
            + self._pack("USER PROFILE", profile)
            + self._pack("CAREER RESEARCH", research)
            + self._pack("SKILL GAP ANALYSIS", gaps)
        )

        roadmap = roadmap_agent.run(roadmap_task)["answer"]

        review_task = (
            "Review the complete analysis for quality and evidence."
            + self._pack("USER PROFILE", profile)
            + self._pack("CAREER RESEARCH", research)
            + self._pack("SKILL GAP ANALYSIS", gaps)
            + self._pack("ROADMAP", roadmap)
        )

        review = reviewer_agent.run(review_task)["answer"]

        review_decision = self._get_review_decision(review)

        observer.log(
            "review_decision",
            "Orchestrator",
            decision=review_decision,
        )

        if review_decision == "REVISE":
            revision_task = (
                "Revise the roadmap using the review feedback. "
                "Preserve supported content and correct only identified weaknesses."
                + self._pack("USER PROFILE", profile)
                + self._pack("CAREER RESEARCH", research)
                + self._pack("SKILL GAP ANALYSIS", gaps)
                + self._pack("CURRENT ROADMAP", roadmap)
                + self._pack("REVIEW FEEDBACK", review)
            )

            roadmap = roadmap_agent.run(revision_task)["answer"]

        job_opportunities = json.dumps(
            latest_job_results,
            ensure_ascii=False,
            indent=2,
        )

        final_task = (
            "Create the final career advisory report from the validated material."
            + self._pack("ORIGINAL USER REQUEST", user_request)
            + self._pack("USER PROFILE", profile)
            + self._pack("CAREER RESEARCH", research)
            + self._pack("SKILL GAP ANALYSIS", gaps)
            + self._pack("ROADMAP", roadmap)
            + self._pack("QUALITY REVIEW", review)
            + self._pack("RETRIEVED CAREER KNOWLEDGE", rag_context)
            + self._pack(
                "CURRENT JOB OPPORTUNITIES FROM JOOBLE",
                job_opportunities,
            )
            + """

IMPORTANT JOB OPPORTUNITY INSTRUCTIONS:
- Add a section titled "Current Job Opportunities".
- Select only the most relevant jobs for the user's profile and experience level.
- Use only jobs provided in CURRENT JOB OPPORTUNITIES FROM JOOBLE.
- Do not invent job titles, companies, locations, or links.
- For each selected job, show:
  Job Title
  Company
  Location
  Source
  Apply Link
- Exclude clearly unsuitable senior or unrelated positions.
- If no suitable jobs are available, state that no suitable current opportunities were found.
"""
        )

        final_report = writer_agent.run(final_task)["answer"]

        observer.log(
            "orchestrator_finish",
            "Orchestrator",
            review_decision=review_decision,
        )

        return {
            "answer": final_report,
            "metadata": {
                "profile": profile,
                "rag_results": rag_results,
                "research": research,
                "skill_gap_analysis": gaps,
                "roadmap": roadmap,
                "review": review,
                "review_decision": review_decision,
                "job_opportunities": latest_job_results.copy(),
                "metrics": observer.summary(),
            },
        }

