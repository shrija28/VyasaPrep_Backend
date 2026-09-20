"""Admin aggregate analytics endpoint.

Implements task 11.1 / REQ-12.1, REQ-12.2, REQ-12.3, REQ-12.6.

Provides ``GET /api/admin/analytics`` — an admin-only endpoint that
returns submission data across all students, reshaped to match the
``submissions`` array consumed by ``dashboard.js`` so the existing chart
code (radar, bar, doughnut) can be reused unchanged on the admin
analytics page.

Filters
-------

All filters are optional and combinable:

* ``subject`` — one of Biology / Physics / Chemistry / Mathematics.
* ``student`` — a KCET Student ID (e.g. ``KCET0001``).
* ``set`` — an ``exam_set_id`` (UUID).
* ``status`` — ``completed`` or ``in_progress``.

Pagination
----------

* ``limit`` — default 100, max 500.
* ``offset`` — default 0.

Empty-state
-----------

When the filtered subset is empty the response carries
``{empty: true, submissions: [], total: 0, filters: {...}}`` so the
frontend can render the empty-state message instead of empty charts
(REQ-12.6).
"""

from __future__ import annotations

import uuid
from typing import Any, Optional

from flask import Blueprint, request, g, jsonify
from sqlalchemy import func, select

from ..db.models import Exam, ExamSet, Submission, Subject, User
from ..middleware.rbac import require_admin

router = Blueprint("admin_analytics", __name__)

_DEFAULT_LIMIT = 100
_MAX_LIMIT = 500


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _validation_error(
    message: str,
    field: Optional[str] = None,
):
    """Return a 400 envelope identical in shape to other admin endpoints."""

    body: dict[str, Any] = {
        "error": "validation_error",
        "message": message,
    }

    if field is not None:
        body["field"] = field

    return jsonify(body), 400


def _normalise_subject(
    value: Optional[str],
) -> Optional[Subject]:
    """Return the matching :class:`Subject` enum or ``None`` for invalid input."""

    if not isinstance(value, str):
        return None

    stripped = value.strip()

    if not stripped:
        return None

    try:
        return Subject(stripped)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# GET /api/admin/analytics
# ---------------------------------------------------------------------------


@router.route("/analytics", methods=["GET"])
def get_analytics() -> Any:
    """Return aggregate analytics across all students with optional filters.

    The response shape matches the ``submissions`` array that
    ``dashboard.js`` already consumes, augmented with ``student_name``
    and ``kcet_student_id`` fields for the admin results table.

    Default sort: ``submitted_at DESC`` (REQ-12.3).

    Institution Integration (REQ-7.4, 9.7):
    - Platform admins see all submissions across all students.
    - Institution admins see only submissions from students linked to
      their institution.
    """

    # -----------------------------------------------------------------------
    # Require admin role
    # -----------------------------------------------------------------------

    _admin = require_admin()

    admin_role = _admin.get("role")

    if admin_role not in (
        "platform_admin",
        "institution_admin",
    ):
        return jsonify({
            "error": "forbidden",
            "message": "Admin access required",
        }), 403

    # -----------------------------------------------------------------------
    # Get database session
    # -----------------------------------------------------------------------

    session = getattr(g, "db", None)

    if session is None:
        return jsonify({
            "error": "database_error",
            "message": "Database session unavailable",
        }), 500

    # -----------------------------------------------------------------------
    # Read query parameters
    # -----------------------------------------------------------------------

    subject = request.args.get("subject")
    student = request.args.get("student")
    set_filter = request.args.get("set")
    status_filter = request.args.get("status")

    # -----------------------------------------------------------------------
    # Pagination parameters
    # -----------------------------------------------------------------------

    try:
        limit = int(
            request.args.get(
                "limit",
                _DEFAULT_LIMIT,
            )
        )

        offset = int(
            request.args.get(
                "offset",
                0,
            )
        )

    except (TypeError, ValueError):
        return _validation_error(
            "limit and offset must be integers"
        )

    if limit < 1:
        return _validation_error(
            "limit must be greater than 0",
            field="limit",
        )

    if offset < 0:
        return _validation_error(
            "offset must be greater than or equal to 0",
            field="offset",
        )

    # -----------------------------------------------------------------------
    # Validate subject filter
    # -----------------------------------------------------------------------

    selected_subject: Optional[Subject] = None

    if subject is not None:

        normalised = _normalise_subject(subject)

        if normalised is None:

            allowed = [
                s.value
                for s in Subject
            ]

            return _validation_error(
                f"subject must be one of {allowed}",
                field="subject",
            )

        selected_subject = normalised

    # -----------------------------------------------------------------------
    # Validate status filter
    # -----------------------------------------------------------------------

    valid_statuses = (
        "completed",
        "in_progress",
    )

    if (
        status_filter is not None
        and status_filter not in valid_statuses
    ):
        return _validation_error(
            f"status must be one of {list(valid_statuses)}",
            field="status",
        )

    # -----------------------------------------------------------------------
    # Validate exam-set UUID
    # -----------------------------------------------------------------------

    set_uuid: Optional[uuid.UUID] = None

    if set_filter is not None:

        try:
            set_uuid = uuid.UUID(set_filter)

        except (
            ValueError,
            AttributeError,
        ):
            return _validation_error(
                "set must be a valid UUID (exam_set_id)",
                field="set",
            )

    # -----------------------------------------------------------------------
    # Build pagination
    # -----------------------------------------------------------------------

    capped_limit = min(
        limit,
        _MAX_LIMIT,
    )

    # -----------------------------------------------------------------------
    # Build active filters response
    # -----------------------------------------------------------------------

    filters_response: dict[str, Any] = {
        "subject": (
            selected_subject.value
            if selected_subject is not None
            else None
        ),
        "student": (
            student
            if student
            else None
        ),
        "set": (
            set_filter
            if set_filter
            else None
        ),
        "status": (
            status_filter
            if status_filter
            else None
        ),
    }

    # -----------------------------------------------------------------------
    # Core query
    #
    # Submissions joined with:
    #   - exam_sets
    #   - exams
    #   - users
    # -----------------------------------------------------------------------

    stmt = (
        select(
            Submission,
            ExamSet,
            Exam,
            User,
        )
        .join(
            ExamSet,
            ExamSet.id == Submission.exam_set_id,
        )
        .join(
            Exam,
            Exam.id == ExamSet.exam_id,
        )
        .join(
            User,
            User.id == Submission.user_id,
        )
    )

    # -----------------------------------------------------------------------
    # Institution scoping
    #
    # Platform admins:
    #   See all submissions.
    #
    # Institution admins:
    #   See only submissions belonging to their institution.
    # -----------------------------------------------------------------------

    admin_institution_id = _admin.get(
        "institution_id"
    )

    if (
        admin_role == "institution_admin"
        and admin_institution_id is not None
    ):
        stmt = stmt.where(
            User.institution_id
            == admin_institution_id
        )

    # -----------------------------------------------------------------------
    # Apply filters
    # -----------------------------------------------------------------------

    if selected_subject is not None:
        stmt = stmt.where(
            Exam.subject
            == selected_subject.value
        )

    if student:
        stmt = stmt.where(
            User.kcet_student_id
            == student.strip()
        )

    if set_uuid is not None:
        stmt = stmt.where(
            Submission.exam_set_id
            == set_uuid
        )

    if status_filter is not None:
        stmt = stmt.where(
            Submission.status
            == status_filter
        )

    # -----------------------------------------------------------------------
    # Default sorting
    # -----------------------------------------------------------------------

    stmt = stmt.order_by(
        Submission.submitted_at.desc(),
        Submission.id.asc(),
    )

    # -----------------------------------------------------------------------
    # Get total count before pagination
    # -----------------------------------------------------------------------

    count_stmt = (
        select(func.count())
        .select_from(
            stmt.subquery()
        )
    )

    total = int(
        session.execute(
            count_stmt
        ).scalar_one()
    )

    # -----------------------------------------------------------------------
    # Apply pagination
    # -----------------------------------------------------------------------

    stmt = (
        stmt
        .offset(offset)
        .limit(capped_limit)
    )

    rows = session.execute(stmt).all()

    # -----------------------------------------------------------------------
    # Build response
    # -----------------------------------------------------------------------

    submissions: list[dict[str, Any]] = []

    for (
        submission,
        exam_set,
        exam,
        user,
    ) in rows:

        submitted_at = submission.submitted_at

        submissions.append(
            {
                "id": str(
                    submission.id
                ),

                "student_name": (
                    user.display_name
                ),

                "kcet_student_id": (
                    user.kcet_student_id
                    or ""
                ),

                "exam_set_id": str(
                    submission.exam_set_id
                ),

                "set_label": (
                    exam_set.set_label
                ),

                "subject": (
                    exam.subject
                ),

                "score_pct": float(
                    submission.score_pct
                ),

                "time_taken_sec": int(
                    submission.time_taken_sec
                ),

                "submitted_at": (
                    submitted_at.isoformat()
                    if submitted_at is not None
                    else None
                ),

                "status": (
                    submission.status
                ),

                "pass_flag": (
                    float(
                        submission.score_pct
                    ) >= 50.0
                ),
            }
        )

    # -----------------------------------------------------------------------
    # Empty-state
    # -----------------------------------------------------------------------

    is_empty = total == 0

    return {
        "submissions": submissions,
        "total": total,
        "empty": is_empty,
        "filters": filters_response,
        "limit": capped_limit,
        "offset": offset,
    }


__all__ = ["router"]