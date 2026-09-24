"""Platform Admin Dashboard — aggregated metrics endpoint.

GET /api/admin/dashboard  (requires platform_admin)

Returns a single JSON object with every KPI tile the admin dashboard
needs:
  - Platform overview (institutions, students, questions, exams)
  - Question bank breakdown (admin vs institution, per subject)
  - Subscription summary (active, expired, trial, revenue)
  - Exam activity (total created, total attempted, recent)
  - Recent institutions (last 5 registered)
  - Alerts (expiring subscriptions, inactive institutions)
"""

from __future__ import annotations
import os

import logging
from datetime import datetime, timedelta
from typing import Any

import os
from flask import Blueprint, request, g, make_response, jsonify, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db.models import Exam, ExamSet, IndexedFile, Question, Submission, User
from ..db.session import get_session
from ..db.subscription_models import Institution, Subscription, SubscriptionPlan
from ..middleware.rbac import require_admin

logger = logging.getLogger("smartkcet.admin.dashboard")

router = Blueprint("admin_dashboard", __name__)


@router.route("/dashboard", methods=["GET"])
def get_admin_dashboard()-> Any:    
    _admin = require_admin()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Return all KPI metrics for the platform admin dashboard."""

    now = datetime.utcnow()
    soon = now + timedelta(days=30)
    from sqlalchemy import case

    # ── 1. Institutions Aggregation ───────────────────────────────────────────
    inst_agg = session.execute(
        select(
            func.count(Institution.id),
            func.count(case((Institution.subscription_status.in_(["active", "trial", "overdue", "grace_period"]), 1))),
            func.count(case((Institution.subscription_status == "inactive", 1)))
        )
    ).one()
    total_institutions = inst_agg[0] or 0
    active_institutions = inst_agg[1] or 0
    inactive_count = inst_agg[2] or 0

    # ── 2. Users / Students Aggregation ───────────────────────────────────────
    user_agg = session.execute(
        select(
            func.count(User.id),
            func.count(User.institution_id)
        ).where(User.role == "student")
    ).one()
    total_students = user_agg[0] or 0
    institution_linked_students = user_agg[1] or 0
    direct_students = total_students - institution_linked_students

    # ── 3. Questions Aggregation ──────────────────────────────────────────────
    q_agg = session.execute(
        select(
            func.count(case((Question.institution_id.is_(None), 1))),
            func.count(Question.institution_id)
        )
    ).one()
    admin_questions_total = q_agg[0] or 0
    institution_questions_total = q_agg[1] or 0

    admin_q_by_subject = dict(
        session.execute(
            select(Question.subject, func.count(Question.id))
            .where(Question.institution_id.is_(None))
            .group_by(Question.subject)
        ).all()
    )

    inst_q_rows = session.execute(
        select(Institution.name, func.count(Question.id))
        .join(Question, Question.institution_id == Institution.id)
        .group_by(Institution.id, Institution.name)
        .order_by(func.count(Question.id).desc())
        .limit(10)
    ).all()
    institution_question_counts = [{"name": r[0], "count": r[1]} for r in inst_q_rows]

    # ── 4. Exams Aggregation ──────────────────────────────────────────────────
    exam_agg = session.execute(
        select(
            func.count(Exam.id),
            func.count(case((Exam.is_published.is_(True), 1)))
        )
    ).one()
    total_exams = exam_agg[0] or 0
    published_exams = exam_agg[1] or 0

    exams_by_subject = dict(
        session.execute(
            select(Exam.subject, func.count(Exam.id))
            .group_by(Exam.subject)
        ).all()
    )

    # ── 5. Submissions Aggregation ────────────────────────────────────────────
    subm_agg = session.execute(
        select(
            func.count(Submission.id),
            func.avg(case((Submission.status == "completed", Submission.score_pct)))
        )
    ).one()
    total_attempts = subm_agg[0] or 0
    avg_score = round(float(subm_agg[1] or 0), 1)

    # ── 6. Subscriptions Aggregation ──────────────────────────────────────────
    sub_agg = session.execute(
        select(
            func.count(case((Subscription.status.in_(["active", "trial", "grace_period"]), 1))),
            func.count(case((Subscription.status.in_(["expired", "cancelled"]), 1))),
            func.count(case((Subscription.status == "overdue", 1)))
        )
    ).one()
    active_subscriptions = sub_agg[0] or 0
    expired_subscriptions = sub_agg[1] or 0
    overdue_subscriptions = sub_agg[2] or 0

    inst_sub_rows = session.execute(
        select(
            Institution.id,
            Institution.name,
            Institution.subscription_status,
            Subscription.status,
            Subscription.next_renewal_date,
            SubscriptionPlan.name,
            SubscriptionPlan.price,
        )
        .outerjoin(
            Subscription,
            Subscription.institution_id == Institution.id,
        )
        .outerjoin(SubscriptionPlan, SubscriptionPlan.id == Subscription.plan_id)
        .order_by(Institution.registered_at.desc())
        .limit(100)
    ).all()

    institution_subscriptions = []
    seen_institutions = set()
    for row in inst_sub_rows:
        inst_id = str(row[0])
        if inst_id in seen_institutions:
            continue
        seen_institutions.add(inst_id)
        institution_subscriptions.append({
            "institution_id": inst_id,
            "institution_name": row[1],
            "institution_status": row[2],
            "subscription_status": row[3] or "none",
            "next_renewal_date": row[4].isoformat() if row[4] else None,
            "plan_name": row[5] or "—",
            "price": float(row[6]) if row[6] else None,
        })

    # Alerts: subscriptions expiring within 30 days
    expiring_soon = session.execute(
        select(
            Institution.name,
            Subscription.next_renewal_date,
            Subscription.status,
        )
        .join(Subscription, Subscription.institution_id == Institution.id)
        .where(
            Subscription.status.in_(["active", "trial", "overdue"]),
            Subscription.next_renewal_date.isnot(None),
            Subscription.next_renewal_date <= soon,
            Subscription.next_renewal_date >= now,
        )
        .order_by(Subscription.next_renewal_date)
        .limit(10)
    ).all()

    alerts = []
    for name, renewal, sub_status in expiring_soon:
        days_left = (renewal - now).days
        alerts.append({
            "type": "subscription_expiring",
            "severity": "warning" if days_left > 7 else "error",
            "message": f"{name}: subscription expires in {days_left} day{'s' if days_left != 1 else ''}",
            "days_left": days_left,
        })

    if inactive_count > 0:
        alerts.append({
            "type": "inactive_institutions",
            "severity": "info",
            "message": f"{inactive_count} institution{'s' if inactive_count != 1 else ''} with no active subscription",
            "count": int(inactive_count),
        })

    # ── 7. Recent Institutions ────────────────────────────────────────────────
    recent_inst_rows = session.execute(
        select(
            Institution.id,
            Institution.name,
            Institution.subscription_status,
            Institution.registered_at,
        )
        .order_by(Institution.registered_at.desc())
        .limit(5)
    ).all()

    recent_institutions = [
        {
            "id": str(r[0]),
            "name": r[1],
            "status": r[2],
            "registered_at": r[3].isoformat() if r[3] else None,
        }
        for r in recent_inst_rows
    ]

    # ── 8. Indexed Files Aggregation ──────────────────────────────────────────
    file_agg = session.execute(
        select(
            func.count(case((IndexedFile.institution_id.is_(None), 1))),
            func.count(IndexedFile.institution_id)
        )
    ).one()
    admin_files = file_agg[0] or 0
    institution_files = file_agg[1] or 0

    # ── 9. Direct Students List (Batched Subscription Lookup) ─────────────────
    direct_student_rows = session.execute(
        select(User.id, User.display_name, User.email, User.kcet_student_id, User.created_at)
        .where(User.role == "student", User.institution_id.is_(None))
        .order_by(User.created_at.desc())
        .limit(20)
    ).all()

    direct_student_ids = [r[0] for r in direct_student_rows]
    user_sub_map = {}
    if direct_student_ids:
        sub_rows = session.execute(
            select(Subscription.user_id, Subscription.status)
            .where(Subscription.user_id.in_(direct_student_ids))
            .order_by(Subscription.created_at.desc())
        ).all()
        for uid, sub_stat in sub_rows:
            if uid not in user_sub_map:
                user_sub_map[uid] = sub_stat

    direct_students_list = [
        {
            "id": str(r[0]),
            "name": r[1] or "—",
            "email": r[2],
            "kcet_student_id": r[3] or "—",
            "subscription_status": user_sub_map.get(r[0]) or "active",
            "created_at": r[4].isoformat() if r[4] else None,
        }
        for r in direct_student_rows
    ]

    # ── 10. Recent Activity (Optimized Joined Queries) ────────────────────────
    recent_activity = []
    recent_subm_rows = session.execute(
        select(
            Submission.id,
            Submission.score_pct,
            Submission.time_taken_sec,
            Submission.submitted_at,
            User.display_name,
            Exam.exam_name,
            Exam.subject
        )
        .outerjoin(User, User.id == Submission.user_id)
        .outerjoin(ExamSet, ExamSet.id == Submission.exam_set_id)
        .outerjoin(Exam, Exam.id == ExamSet.exam_id)
        .order_by(Submission.submitted_at.desc())
        .limit(6)
    ).all()

    for s_id, s_score, s_time, s_at, u_name, e_name, e_subj in recent_subm_rows:
        user_name = u_name or "Student"
        exam_title = e_name or e_subj or "Exam"
        mins = (s_time or 0) // 60
        secs = (s_time or 0) % 60
        score_pct = float(s_score or 0)
        recent_activity.append({
            "id": str(s_id),
            "type": "exam_submission",
            "title": f"{user_name} completed {exam_title}",
            "subtitle": f"Score: {score_pct}% ({mins}m {secs}s)",
            "timestamp": s_at.isoformat() if s_at else None,
            "badge": "Exam",
            "badge_color": "green" if score_pct >= 50 else "blue",
        })

    recent_users = session.execute(
        select(User)
        .where(User.role == "student")
        .order_by(User.created_at.desc())
        .limit(4)
    ).scalars().all()
    for u in recent_users:
        recent_activity.append({
            "id": str(u.id),
            "type": "user_registration",
            "title": f"Student registered: {u.display_name}",
            "subtitle": f"ID: {u.kcet_student_id or '—'} • {u.email}",
            "timestamp": u.created_at.isoformat() if u.created_at else None,
            "badge": "Student",
            "badge_color": "purple",
        })

    recent_activity.sort(key=lambda x: x["timestamp"] or "", reverse=True)

    # ── Assemble response ─────────────────────────────────────────────────────
    return {
        "generated_at": now.isoformat(),

        # Overview KPIs
        "overview": {
            "total_institutions": int(total_institutions),
            "active_institutions": int(active_institutions),
            "total_students": int(total_students),
            "institution_linked_students": int(institution_linked_students),
            "direct_students": int(direct_students),
            "total_questions": int(admin_questions_total + institution_questions_total),
            "admin_questions": int(admin_questions_total),
            "institution_questions": int(institution_questions_total),
            "total_exams": int(total_exams),
            "published_exams": int(published_exams),
            "total_exam_attempts": int(total_attempts),
            "avg_score": avg_score,
            "active_subscriptions": int(active_subscriptions),
            "expired_subscriptions": int(expired_subscriptions),
            "overdue_subscriptions": int(overdue_subscriptions),
            "admin_indexed_files": int(admin_files),
            "institution_indexed_files": int(institution_files),
        },

        # Question bank breakdown
        "question_bank": {
            "admin_by_subject": {s: int(v) for s, v in admin_q_by_subject.items()},
            "institution_by_institution": institution_question_counts,
        },

        # Exams breakdown
        "exams": {
            "by_subject": {s: int(v) for s, v in exams_by_subject.items()},
        },

        # Institution subscriptions
        "institution_subscriptions": institution_subscriptions,

        # Recent institutions
        "recent_institutions": recent_institutions,

        # Direct students
        "direct_students": direct_students_list,

        # Recent activity
        "recent_activity": recent_activity[:10],

        # Alerts
        "alerts": alerts,
        "alert_count": len(alerts),
    }


__all__ = ["router"]
