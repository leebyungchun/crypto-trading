from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

from app.market_mode import MarketMode, action_allowed_in_mode
from config.settings import settings


class SignalDecision(str, Enum):
    ENTER = "ENTER"
    EXIT = "EXIT"
    IGNORE = "IGNORE"


@dataclass
class GuardResult:
    decision: SignalDecision
    reason: str


@dataclass
class PendingReversal:
    action: str
    count: int
    first_seen: datetime
    last_seen: datetime


def is_counter_signal(current_action: str, incoming_action: str) -> bool:
    return current_action.upper() in {"BUY", "SELL"} and incoming_action.upper() in {"BUY", "SELL"} and current_action.upper() != incoming_action.upper()


class ReversalGuard:
    """Stateful guard for fake counter signals and post-exit cooldowns."""

    def __init__(self):
        self.pending: dict[str, PendingReversal] = {}
        self.cooldown_until: dict[str, datetime] = {}

    def evaluate(
        self,
        symbol: str,
        incoming_action: str,
        market_mode: MarketMode,
        current_action: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> GuardResult:
        now = now or datetime.now(timezone.utc)
        incoming_action = incoming_action.upper()
        current_action = current_action.upper() if current_action else None

        if incoming_action == "EXIT":
            self.clear_pending(symbol)
            return GuardResult(SignalDecision.EXIT, "explicit EXIT signal")

        if incoming_action not in {"BUY", "SELL"}:
            return GuardResult(SignalDecision.IGNORE, f"unsupported action: {incoming_action}")

        if not current_action:
            cooldown = self.cooldown_until.get(symbol)
            if cooldown and now < cooldown:
                return GuardResult(SignalDecision.IGNORE, f"cooldown active until {cooldown.isoformat()} UTC")
            if action_allowed_in_mode(incoming_action, market_mode):
                self.clear_pending(symbol)
                return GuardResult(SignalDecision.ENTER, f"{incoming_action} allowed in {market_mode.value}")
            return GuardResult(SignalDecision.IGNORE, f"{incoming_action} blocked by {market_mode.value}")

        if incoming_action == current_action:
            self.clear_pending(symbol)
            return GuardResult(SignalDecision.IGNORE, "same-direction signal while position is already open")

        if not is_counter_signal(current_action, incoming_action):
            return GuardResult(SignalDecision.IGNORE, "not a valid counter signal")

        if settings.IGNORE_COUNTER_SIGNAL_IN_TREND and market_mode != MarketMode.BOTH and action_allowed_in_mode(current_action, market_mode):
            self.clear_pending(symbol)
            return GuardResult(SignalDecision.IGNORE, f"counter signal ignored in {market_mode.value}")

        if settings.EXIT_ON_FIRST_COUNTER_SIGNAL:
            self.clear_pending(symbol)
            return GuardResult(SignalDecision.EXIT, "first counter signal exits position")

        pending = self._record_pending(symbol, incoming_action, now)
        window = timedelta(minutes=settings.REVERSAL_CONFIRM_MINUTES)
        expired = now - pending.first_seen > window
        if expired:
            pending = self._reset_pending(symbol, incoming_action, now)

        if pending.count >= settings.REVERSAL_CONFIRM_COUNT:
            self.clear_pending(symbol)
            return GuardResult(
                SignalDecision.EXIT,
                f"counter signal confirmed {pending.count} times within {settings.REVERSAL_CONFIRM_MINUTES} minutes",
            )

        return GuardResult(
            SignalDecision.IGNORE,
            f"counter signal pending {pending.count}/{settings.REVERSAL_CONFIRM_COUNT}",
        )

    def mark_exit(self, symbol: str, now: Optional[datetime] = None):
        now = now or datetime.now(timezone.utc)
        self.clear_pending(symbol)
        if settings.COOLDOWN_SECONDS > 0:
            self.cooldown_until[symbol] = now + timedelta(seconds=settings.COOLDOWN_SECONDS)

    def clear_pending(self, symbol: str):
        self.pending.pop(symbol, None)

    def _record_pending(self, symbol: str, action: str, now: datetime) -> PendingReversal:
        pending = self.pending.get(symbol)
        if not pending or pending.action != action:
            return self._reset_pending(symbol, action, now)
        pending.count += 1
        pending.last_seen = now
        return pending

    def _reset_pending(self, symbol: str, action: str, now: datetime) -> PendingReversal:
        pending = PendingReversal(action=action, count=1, first_seen=now, last_seen=now)
        self.pending[symbol] = pending
        return pending
