from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_client
from app.db import get_db
from app.models.entities import Client, EvaluationRun
from app.modules.evaluations.service import EvaluationService
from app.schemas.evaluations import (
    EvaluationCaseResponse,
    EvaluationDatasetDetailResponse,
    EvaluationDatasetResponse,
    EvaluationResultItem,
    EvaluationRunRequest,
    EvaluationRunResponse,
)

router = APIRouter()
service = EvaluationService()


def _run_to_response(run: EvaluationRun) -> EvaluationRunResponse:
    return EvaluationRunResponse(
        evaluation_id=run.id,
        dataset_id=run.dataset_id,
        status=run.status.value if hasattr(run.status, "value") else str(run.status),
        model_ids=list(run.model_ids or []),
        update_model_quality=run.update_model_quality,
        summary=run.summary or {},
        started_at=run.started_at.isoformat() if run.started_at else None,
        completed_at=run.completed_at.isoformat() if run.completed_at else None,
        error_message=run.error_message,
        result_count=len(run.results) if run.results is not None else 0,
    )


@router.get("/evaluations/datasets", response_model=list[EvaluationDatasetResponse])
async def list_datasets(
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Client, Depends(get_current_client)],
) -> list[EvaluationDatasetResponse]:
    datasets = await service.list_datasets(session)
    out: list[EvaluationDatasetResponse] = []
    for ds in datasets:
        detail = await service.get_dataset(session, ds.id)
        out.append(
            EvaluationDatasetResponse(
                id=detail.id,
                name=detail.name,
                task_type=detail.task_type,
                version=detail.version,
                description=detail.description,
                case_count=len(detail.cases),
            )
        )
    return out


@router.get("/evaluations/datasets/{dataset_id}", response_model=EvaluationDatasetDetailResponse)
async def get_dataset(
    dataset_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Client, Depends(get_current_client)],
) -> EvaluationDatasetDetailResponse:
    dataset = await service.get_dataset(session, dataset_id)
    return EvaluationDatasetDetailResponse(
        id=dataset.id,
        name=dataset.name,
        task_type=dataset.task_type,
        version=dataset.version,
        description=dataset.description,
        case_count=len(dataset.cases),
        cases=[
            EvaluationCaseResponse(
                id=str(case.id),
                case_key=case.case_key,
                input=case.input_text,
                expected_output=case.expected_output,
                difficulty=case.difficulty,
                language=case.language,
                tags=case.tags or [],
            )
            for case in dataset.cases
        ],
    )


@router.post("/evaluations/run", response_model=EvaluationRunResponse)
async def run_evaluation(
    payload: EvaluationRunRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Client, Depends(get_current_client)],
) -> EvaluationRunResponse:
    run = await service.run_evaluation(
        session,
        dataset_id=payload.dataset_id,
        model_ids=payload.model_ids,
        update_model_quality=payload.update_model_quality,
    )
    # reload with results count
    run = await service.get_run(session, run.id)
    return _run_to_response(run)


@router.get("/evaluations/{evaluation_id}", response_model=EvaluationRunResponse)
async def get_evaluation(
    evaluation_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Client, Depends(get_current_client)],
) -> EvaluationRunResponse:
    run = await service.get_run(session, evaluation_id)
    return _run_to_response(run)


@router.get("/evaluations/{evaluation_id}/results", response_model=list[EvaluationResultItem])
async def get_evaluation_results(
    evaluation_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Client, Depends(get_current_client)],
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
) -> list[EvaluationResultItem]:
    run = await service.get_run(session, evaluation_id)
    items: list[EvaluationResultItem] = []
    for row in run.results[:limit]:
        obtained = row.obtained_output or {}
        expected = row.case.expected_output or {}
        items.append(
            EvaluationResultItem(
                case_key=row.case.case_key,
                model_id=row.model_id,
                score=row.score,
                correct=row.correct,
                valid_output=row.valid_output,
                difficulty=row.case.difficulty,
                language=row.case.language,
                latency_ms=row.latency_ms,
                estimated_cost_usd=row.estimated_cost_usd,
                obtained_category=obtained.get("category") if isinstance(obtained, dict) else None,
                expected_category=expected.get("category"),
                error_type=row.error_type,
            )
        )
    return items


@router.get("/evaluations", response_model=list[EvaluationRunResponse])
async def list_evaluations(
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Client, Depends(get_current_client)],
    dataset_id: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[EvaluationRunResponse]:
    runs = await service.list_runs(session, dataset_id=dataset_id, limit=limit)
    return [
        EvaluationRunResponse(
            evaluation_id=run.id,
            dataset_id=run.dataset_id,
            status=run.status.value if hasattr(run.status, "value") else str(run.status),
            model_ids=list(run.model_ids or []),
            update_model_quality=run.update_model_quality,
            summary=run.summary or {},
            started_at=run.started_at.isoformat() if run.started_at else None,
            completed_at=run.completed_at.isoformat() if run.completed_at else None,
            error_message=run.error_message,
            result_count=0,
        )
        for run in runs
    ]
