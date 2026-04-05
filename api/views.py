"""Shared API endpoints."""

from __future__ import annotations

from rest_framework.decorators import api_view, permission_classes  # type: ignore[import]
from rest_framework.permissions import IsAuthenticated  # type: ignore[import]
from rest_framework.response import Response  # type: ignore[import]


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def task_status(request, task_id):
    """Return async task status when Celery result backend is available."""

    try:
        from celery.result import AsyncResult  # type: ignore[import]
    except ModuleNotFoundError:
        return Response(
            {
                "task_id": task_id,
                "status": "unavailable",
                "detail": "Celery is not installed in this environment.",
            }
        )

    result = AsyncResult(task_id)
    payload = {
        "task_id": task_id,
        "status": result.state.lower(),
        "result": result.result if result.successful() else None,
    }
    if result.failed():
        payload["error"] = str(result.result)
    return Response(payload)
