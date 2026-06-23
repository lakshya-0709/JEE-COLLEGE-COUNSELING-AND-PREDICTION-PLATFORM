"""
Preference list generation service.
Generates an optimized JoSAA choice-filling order.
"""

from app.services.prediction import prediction_service


class PreferenceService:
    """Service for generating optimized preference/choice-filling lists."""

    def generate_preference_list(self, student_rank: int, exam_type: str,
                                  category: str, gender: str, home_state: str | None,
                                  preferred_branches: list[str],
                                  institute_types: list[str],
                                  branch_priority: str = "balanced",
                                  risk_tolerance: str = "balanced") -> dict:
        """
        Generate an optimized preference list for JoSAA choice filling.

        Strategy:
        - safe: 60% safe, 30% moderate, 10% dream
        - balanced: 30% dream, 40% moderate, 30% safe
        - aggressive: 50% dream, 35% moderate, 15% safe

        Ordering:
        - branch_first: Group by branch, then by college quality
        - college_first: Group by college tier, then by branch
        - balanced: Interleave based on overall score
        """
        # Get all predictions
        predictions = prediction_service.predict_colleges(
            student_rank, exam_type, category, gender,
            home_state, preferred_branches, institute_types
        )

        all_colleges = []
        for chance_cat in ["dream", "moderate", "safe"]:
            for p in predictions.get(chance_cat, []):
                all_colleges.append(p)

        if not all_colleges:
            return {
                "your_rank": student_rank,
                "total_choices": 0,
                "strategy": f"{risk_tolerance} / {branch_priority}",
                "preference_list": [],
            }

        # Score each college based on strategy
        scored = []
        for college in all_colleges:
            score = self._calculate_score(
                college, branch_priority, risk_tolerance, preferred_branches
            )
            scored.append((score, college))

        # Sort by score (higher is better position in list)
        scored.sort(key=lambda x: -x[0])

        # Apply risk tolerance limits
        max_choices = min(len(scored), 50)  # Cap at 50 choices
        final_list = scored[:max_choices]

        # Build preference list
        preference_list = []
        for idx, (score, college) in enumerate(final_list, 1):
            reason = self._get_reason(college, student_rank)
            preference_list.append({
                "rank_order": idx,
                "institute": college["institute"],
                "institute_short": college["institute_short"],
                "institute_type": college["institute_type"],
                "state": college["state"],
                "program": college["program"],
                "branch_short": college["branch_short"],
                "chance_category": college["chance_category"],
                "closing_rank_latest": college.get("closing_rank_2024") or college.get("closing_rank_2023"),
                "your_rank": student_rank,
                "reason": reason,
            })

        # Strategy description
        strategy_desc = {
            "safe": "Conservative — prioritizing high-chance colleges",
            "balanced": "Balanced — mix of dream, moderate, and safe picks",
            "aggressive": "Aggressive — prioritizing top colleges with lower chances",
        }

        return {
            "your_rank": student_rank,
            "total_choices": len(preference_list),
            "strategy": strategy_desc.get(risk_tolerance, risk_tolerance),
            "preference_list": preference_list,
        }

    def _calculate_score(self, college: dict, branch_priority: str,
                         risk_tolerance: str, preferred_branches: list[str]) -> float:
        """Calculate a ranking score for a college in the preference list."""
        score = 0.0
        chance = college["chance_category"]

        # Risk tolerance scoring
        risk_scores = {
            "safe": {"Dream": 1, "Moderate": 3, "Safe": 5},
            "balanced": {"Dream": 4, "Moderate": 5, "Safe": 3},
            "aggressive": {"Dream": 5, "Moderate": 3, "Safe": 1},
        }
        score += risk_scores.get(risk_tolerance, risk_scores["balanced"]).get(chance, 3) * 10

        # Branch preference bonus
        if preferred_branches and college["branch_short"] in preferred_branches:
            branch_idx = preferred_branches.index(college["branch_short"])
            score += (len(preferred_branches) - branch_idx) * 5

        # Branch priority adjustment
        if branch_priority == "branch_first" and preferred_branches:
            if college["branch_short"] in preferred_branches:
                score += 50
        elif branch_priority == "college_first":
            # Bonus for better institute types
            type_score = {"IIT": 40, "NIT": 30, "IIIT": 25, "GFTI": 15}
            score += type_score.get(college["institute_type"], 10)

        # Confidence score bonus
        score += college.get("confidence_score", 0) * 10

        # Rank difference bonus (higher difference = safer)
        rank_diff = college.get("rank_difference", 0)
        if rank_diff > 0:
            score += min(10, rank_diff / 1000)

        return score

    def _get_reason(self, college: dict, student_rank: int) -> str:
        """Generate a human-readable reason for the recommendation."""
        chance = college["chance_category"]
        closing = college.get("closing_rank_2024") or college.get("predicted_closing_2026")
        inst = college["institute_short"]
        branch = college["branch_short"]

        if not closing:
            return f"{inst} - {branch}"

        diff = closing - student_rank

        if chance == "Safe":
            return f"Your rank ({student_rank:,}) is {diff:,} better than last cutoff ({closing:,})"
        elif chance == "Moderate":
            if diff > 0:
                return f"Your rank is close to cutoff ({closing:,}), good chance"
            else:
                return f"Cutoff ({closing:,}) is slightly better than your rank, possible"
        else:
            return f"Cutoff ({closing:,}) is above your rank, aspirational pick"


# Global singleton
preference_service = PreferenceService()
