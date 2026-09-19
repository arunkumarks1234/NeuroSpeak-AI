"""
NeuroSpeak-AI — Gamification Service
======================================
Handles streak tracking, XP updates, tier promotion, and daily quest logic.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass

from sqlalchemy.orm import Session
from utils.logger import get_logger

from .pronunciation_service import calculate_xp, get_tier

logger = get_logger(__name__)


@dataclass
class GamificationUpdate:
    xp_earned: int
    new_total_xp: int
    old_tier: str
    new_tier: str
    tier_promoted: bool
    streak_days: int
    streak_extended: bool
    daily_quest_progress: float
    daily_quest_completed: bool


class GamificationService:
    """Updates gamification stats after each pronunciation session."""

    DAILY_QUEST_MINUTES = 15

    def process_session(
        self,
        db: Session,
        user_id: int,
        accuracy: float,
        difficulty: str,
        audio_duration_sec: float,
    ) -> GamificationUpdate:
        """
        Update a user's GamificationStats after a completed session.

        Returns a GamificationUpdate describing all changes made.
        """
        from backend.models import GamificationStats  # lazy import to avoid circular

        stats = db.query(GamificationStats).filter_by(user_id=user_id).first()

        if stats is None:
            stats = GamificationStats(user_id=user_id)
            db.add(stats)
            db.flush()

        today = datetime.date.today()
        now = datetime.datetime.utcnow()

        # ── Streak logic ─────────────────────────────────────────────────────
        old_streak = stats.current_streak_days
        streak_extended = False

        if stats.last_practice_date is not None:
            last_date = stats.last_practice_date.date()
            days_since = (today - last_date).days
            if days_since == 0:
                pass  # Already practiced today — no change
            elif days_since == 1:
                stats.current_streak_days += 1
                streak_extended = True
            else:
                stats.current_streak_days = 1  # Reset streak
                streak_extended = True
        else:
            stats.current_streak_days = 1
            streak_extended = True

        stats.longest_streak_days = max(
            stats.longest_streak_days, stats.current_streak_days
        )
        stats.last_practice_date = now

        # ── XP calculation ───────────────────────────────────────────────────
        xp = calculate_xp(
            accuracy=accuracy,
            difficulty=difficulty,
            streak_days=stats.current_streak_days,
        )

        old_tier = stats.tier
        stats.total_xp += xp
        stats.tier = get_tier(stats.total_xp)
        tier_promoted = stats.tier != old_tier

        # ── Session counters ─────────────────────────────────────────────────
        stats.total_sessions += 1
        practice_minutes = audio_duration_sec / 60.0
        stats.total_practice_minutes += practice_minutes

        if stats.avg_accuracy is None:
            stats.avg_accuracy = accuracy
        else:
            n = stats.total_sessions
            stats.avg_accuracy = round(
                (stats.avg_accuracy * (n - 1) + accuracy) / n, 2
            )

        # ── Daily quest logic ────────────────────────────────────────────────
        quest_date = stats.daily_quest_date
        if quest_date is None or quest_date.date() < today:
            # New day — reset quest
            stats.daily_quest_completed_minutes = 0.0
            stats.daily_quest_completed = False
            stats.daily_quest_date = now

        stats.daily_quest_completed_minutes += practice_minutes
        quest_just_completed = False
        if (
            not stats.daily_quest_completed
            and stats.daily_quest_completed_minutes >= self.DAILY_QUEST_MINUTES
        ):
            stats.daily_quest_completed = True
            quest_just_completed = True
            # Bonus XP for completing daily quest
            stats.total_xp += 50
            xp += 50
            stats.tier = get_tier(stats.total_xp)
            logger.info("User %s completed daily quest (+50 XP)", user_id)

        db.commit()
        db.refresh(stats)

        return GamificationUpdate(
            xp_earned=xp,
            new_total_xp=stats.total_xp,
            old_tier=old_tier,
            new_tier=stats.tier,
            tier_promoted=tier_promoted,
            streak_days=stats.current_streak_days,
            streak_extended=streak_extended,
            daily_quest_progress=min(
                stats.daily_quest_completed_minutes / self.DAILY_QUEST_MINUTES * 100, 100.0
            ),
            daily_quest_completed=stats.daily_quest_completed,
        )
