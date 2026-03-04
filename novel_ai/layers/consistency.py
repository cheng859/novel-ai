from __future__ import annotations

from typing import List

from novel_ai.core.interfaces import ConsistencyEngine
from novel_ai.core.models import ConsistencyIssue, ConsistencyReport, StageContext, StageId, StageResult


class RuleBasedConsistencyEngine(ConsistencyEngine):
    def review(self, context: StageContext, stage_result: StageResult) -> ConsistencyReport:
        issues: List[ConsistencyIssue] = []

        # OOC: forbidden behavior surfaced in chapter text.
        chapter_text = stage_result.outputs.get("chapter_text", "")
        for c in context.global_characters.values():
            for forbidden in c.forbidden_behaviors:
                if forbidden and forbidden in chapter_text:
                    issues.append(
                        ConsistencyIssue(
                            code="OOC_FORBIDDEN_BEHAVIOR",
                            message=f"{c.name} violated forbidden behavior: {forbidden}",
                            stage_hint=StageId.STAGE5_CHAPTER_WRITING,
                        )
                    )

        # Timeline/world checks kept lightweight for scaffold.
        if stage_result.stage == StageId.STAGE5_CHAPTER_WRITING and not stage_result.outputs.get("chapter_id"):
            issues.append(
                ConsistencyIssue(
                    code="TIMELINE_MISSING_CHAPTER_ID",
                    message="Chapter generation missing chapter_id, timeline may break.",
                    stage_hint=StageId.STAGE4_CHAPTER_PLANNING,
                )
            )

        score = max(0.0, 1.0 - 0.2 * len(issues))
        rollback_stage = issues[0].stage_hint if issues else None
        return ConsistencyReport(score=score, issues=issues, rollback_stage=rollback_stage)
