from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entities import (
    AIModel,
    EvaluationDataset,
    EvaluationResult,
    EvaluationRun,
    EvaluationRunStatus,
)
from app.modules.evaluations.scoring import score_case
from app.modules.providers.registry import get_provider_adapter
from app.modules.validation.response import ResponseValidator


class EvaluationService:
    def __init__(self) -> None:
        self.validator = ResponseValidator()

    async def list_datasets(self, session: AsyncSession) -> list[EvaluationDataset]:
        result = await session.execute(select(EvaluationDataset).order_by(EvaluationDataset.id))
        return list(result.scalars().all())

    async def get_dataset(self, session: AsyncSession, dataset_id: str) -> EvaluationDataset:
        result = await session.execute(
            select(EvaluationDataset)
            .options(selectinload(EvaluationDataset.cases))
            .where(EvaluationDataset.id == dataset_id)
        )
        dataset = result.scalar_one_or_none()
        if dataset is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
        return dataset

    async def run_evaluation(
        self,
        session: AsyncSession,
        *,
        dataset_id: str,
        model_ids: list[str] | None = None,
        update_model_quality: bool = True,
    ) -> EvaluationRun:
        dataset = await self.get_dataset(session, dataset_id)
        models = await self._resolve_models(session, model_ids)
        if not models:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No enabled models available for evaluation",
            )
        if not dataset.cases:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dataset has no cases",
            )

        run_id = f"eval_{uuid.uuid4().hex[:12]}"
        run = EvaluationRun(
            id=run_id,
            dataset_id=dataset.id,
            status=EvaluationRunStatus.running,
            model_ids=[m.id for m in models],
            update_model_quality=update_model_quality,
            summary={},
        )
        session.add(run)
        await session.flush()

        try:
            for model in models:
                adapter = get_provider_adapter(model.provider_id)
                for case in dataset.cases:
                    provider_result = await adapter.complete(
                        model_id=model.id,
                        prompt=case.input_text,
                        task_type=dataset.task_type,
                        output_format="json",
                        language=case.language,
                    )
                    cost = self._cost(
                        model, provider_result.input_tokens, provider_result.output_tokens
                    )

                    if not provider_result.ok:
                        session.add(
                            EvaluationResult(
                                run_id=run_id,
                                case_id=case.id,
                                model_id=model.id,
                                score=0.0,
                                correct=False,
                                valid_output=False,
                                latency_ms=provider_result.latency_ms,
                                input_tokens=provider_result.input_tokens,
                                output_tokens=provider_result.output_tokens,
                                estimated_cost_usd=cost,
                                obtained_output=None,
                                error_type=provider_result.error_type,
                                error_message=provider_result.error_message,
                            )
                        )
                        continue

                    validation = self.validator.validate(
                        provider_result.content,
                        output_format="json",
                        task_type=dataset.task_type,
                    )
                    obtained = validation.normalized if validation.ok else None
                    if isinstance(provider_result.content, dict) and obtained is None:
                        obtained = provider_result.content

                    score, correct = score_case(
                        expected=case.expected_output,
                        obtained=obtained if validation.ok else None,
                        valid_output=validation.ok,
                    )
                    session.add(
                        EvaluationResult(
                            run_id=run_id,
                            case_id=case.id,
                            model_id=model.id,
                            score=score,
                            correct=correct,
                            valid_output=validation.ok,
                            latency_ms=provider_result.latency_ms,
                            input_tokens=provider_result.input_tokens,
                            output_tokens=provider_result.output_tokens,
                            estimated_cost_usd=cost,
                            obtained_output=obtained
                            if isinstance(obtained, dict)
                            else {"raw": str(provider_result.content)},
                            error_type=None if validation.ok else "invalid_response",
                            error_message=None
                            if validation.ok
                            else ";".join(validation.errors),
                        )
                    )

            await session.flush()
            summary = await self._build_summary(session, run_id, dataset.task_type)
            run.summary = summary
            run.status = EvaluationRunStatus.completed
            run.completed_at = datetime.now(UTC)

            if update_model_quality:
                await self._apply_quality_update(session, summary, dataset.task_type)

            await session.commit()
            await session.refresh(run)
            return run
        except Exception as exc:
            run.status = EvaluationRunStatus.failed
            run.error_message = str(exc)
            run.completed_at = datetime.now(UTC)
            await session.commit()
            raise

    async def get_run(self, session: AsyncSession, evaluation_id: str) -> EvaluationRun:
        result = await session.execute(
            select(EvaluationRun)
            .options(selectinload(EvaluationRun.results).selectinload(EvaluationResult.case))
            .where(EvaluationRun.id == evaluation_id)
        )
        run = result.scalar_one_or_none()
        if run is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation run not found"
            )
        return run

    async def list_runs(
        self, session: AsyncSession, dataset_id: str | None = None, limit: int = 20
    ) -> list[EvaluationRun]:
        stmt = select(EvaluationRun).order_by(EvaluationRun.started_at.desc()).limit(limit)
        if dataset_id:
            stmt = stmt.where(EvaluationRun.dataset_id == dataset_id)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def _resolve_models(
        self, session: AsyncSession, model_ids: list[str] | None
    ) -> list[AIModel]:
        stmt = select(AIModel).where(AIModel.enabled.is_(True))
        if model_ids:
            stmt = stmt.where(AIModel.id.in_(model_ids))
        result = await session.execute(stmt.order_by(AIModel.id))
        return list(result.scalars().all())

    def _cost(self, model: AIModel, input_tokens: int, output_tokens: int) -> float:
        in_cost = (input_tokens / 1_000_000) * model.input_cost_per_million_tokens
        out_cost = (output_tokens / 1_000_000) * model.output_cost_per_million_tokens
        return round(in_cost + out_cost, 8)

    async def _build_summary(
        self, session: AsyncSession, run_id: str, task_type: str
    ) -> dict[str, Any]:
        result = await session.execute(
            select(EvaluationResult)
            .options(selectinload(EvaluationResult.case))
            .where(EvaluationResult.run_id == run_id)
        )
        rows = list(result.scalars().all())

        by_model: dict[str, list[EvaluationResult]] = defaultdict(list)
        for row in rows:
            by_model[row.model_id].append(row)

        models_summary: dict[str, Any] = {}
        for model_id, items in by_model.items():
            n = len(items) or 1
            by_difficulty: dict[str, list[float]] = defaultdict(list)
            by_language: dict[str, list[float]] = defaultdict(list)
            for item in items:
                by_difficulty[item.case.difficulty].append(item.score)
                by_language[item.case.language].append(item.score)

            avg = sum(i.score for i in items) / n
            models_summary[model_id] = {
                "task_type": task_type,
                "cases": len(items),
                "accuracy": round(sum(1 for i in items if i.correct) / n, 4),
                "average_score": round(avg, 4),
                "valid_json_rate": round(sum(1 for i in items if i.valid_output) / n, 4),
                "error_rate": round(sum(1 for i in items if i.error_type) / n, 4),
                "average_latency_ms": round(sum(i.latency_ms for i in items) / n, 2),
                "average_cost_usd": round(sum(i.estimated_cost_usd for i in items) / n, 8),
                "total_cost_usd": round(sum(i.estimated_cost_usd for i in items), 8),
                "quality_by_difficulty": {
                    k: round(sum(v) / len(v), 4) for k, v in by_difficulty.items()
                },
                "quality_by_language": {
                    k: round(sum(v) / len(v), 4) for k, v in by_language.items()
                },
            }

        return {
            "task_type": task_type,
            "total_results": len(rows),
            "models": models_summary,
        }

    async def _apply_quality_update(
        self, session: AsyncSession, summary: dict[str, Any], task_type: str
    ) -> None:
        models_summary = summary.get("models") or {}
        for model_id, metrics in models_summary.items():
            model = await session.get(AIModel, model_id)
            if model is None:
                continue
            quality = dict(model.quality_by_task or {})
            # Blend new evaluation into stored quality used by the router
            measured = float(metrics.get("average_score") or 0.0)
            previous = float(quality.get(task_type, measured))
            quality[task_type] = round((previous * 0.3) + (measured * 0.7), 4)
            quality[f"{task_type}__by_difficulty"] = metrics.get("quality_by_difficulty", {})
            quality[f"{task_type}__by_language"] = metrics.get("quality_by_language", {})
            quality[f"{task_type}__last_eval_accuracy"] = metrics.get("accuracy")
            model.quality_by_task = quality
