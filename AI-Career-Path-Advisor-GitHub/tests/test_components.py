from career_advisor.exceptions import LoopDetectedError
from career_advisor.loop_detection import LoopDetector
from career_advisor.registry import registry
import career_advisor.tools  # registers tools
from career_advisor.tools import calculate_match_score, prioritize_skill_gaps

def test_registry_has_match_tool():
    assert any(x["function"]["name"] == "calculate_match_score" for x in registry.schemas())

def test_match_score():
    result=calculate_match_score(["Python","SQL","Machine Learning"],["Python","SQL","Docker","Machine Learning"])
    assert result["score"] == 75.0
    assert "docker" in result["missing_skills"]

def test_loop_detection():
    detector=LoopDetector(max_repeats=1)
    detector.check("search_web", {"query":"AI Engineer"})
    try:
        detector.check("search_web", {"query":"AI Engineer"})
        assert False
    except LoopDetectedError:
        pass

def test_skill_priority():
    result=prioritize_skill_gaps(["Docker","Cloud","Communication"],["Docker","Cloud"])
    assert set(result["high_priority"]) == {"Docker","Cloud"}
