import unittest

from app.market_mode import MarketMode, action_allowed_in_mode, decide_market_mode
from app.reversal_guard import ReversalGuard, SignalDecision
from config.settings import settings


class MarketModeTests(unittest.TestCase):
    def test_action_allowed_by_mode(self):
        self.assertTrue(action_allowed_in_mode("BUY", MarketMode.LONG_ONLY))
        self.assertFalse(action_allowed_in_mode("SELL", MarketMode.LONG_ONLY))
        self.assertTrue(action_allowed_in_mode("SELL", MarketMode.SHORT_ONLY))
        self.assertFalse(action_allowed_in_mode("BUY", MarketMode.SHORT_ONLY))
        self.assertFalse(action_allowed_in_mode("BUY", MarketMode.NO_TRADE))

    def test_auto_mode_uses_trend_context(self):
        self.assertEqual(decide_market_mode(trend_ema200="UP"), MarketMode.LONG_ONLY)
        self.assertEqual(decide_market_mode(trend_ema200="DOWN"), MarketMode.SHORT_ONLY)
        self.assertEqual(decide_market_mode(volatility="LOW"), MarketMode.NO_TRADE)


class ReversalGuardTests(unittest.TestCase):
    def setUp(self):
        self._original = {
            "EXIT_ON_FIRST_COUNTER_SIGNAL": settings.EXIT_ON_FIRST_COUNTER_SIGNAL,
            "IGNORE_COUNTER_SIGNAL_IN_TREND": settings.IGNORE_COUNTER_SIGNAL_IN_TREND,
            "REVERSAL_CONFIRM_COUNT": settings.REVERSAL_CONFIRM_COUNT,
            "REVERSAL_CONFIRM_MINUTES": settings.REVERSAL_CONFIRM_MINUTES,
            "COOLDOWN_SECONDS": settings.COOLDOWN_SECONDS,
        }
        settings.EXIT_ON_FIRST_COUNTER_SIGNAL = False
        settings.IGNORE_COUNTER_SIGNAL_IN_TREND = True
        settings.REVERSAL_CONFIRM_COUNT = 2
        settings.REVERSAL_CONFIRM_MINUTES = 10
        settings.COOLDOWN_SECONDS = 900

    def tearDown(self):
        for key, value in self._original.items():
            setattr(settings, key, value)

    def test_first_entry_allowed_by_mode(self):
        guard = ReversalGuard()
        result = guard.evaluate("BTC/USDT:USDT", "SELL", MarketMode.SHORT_ONLY)
        self.assertEqual(result.decision, SignalDecision.ENTER)

    def test_counter_signal_ignored_in_trend_mode(self):
        guard = ReversalGuard()
        result = guard.evaluate("BTC/USDT:USDT", "BUY", MarketMode.SHORT_ONLY, "SELL")
        self.assertEqual(result.decision, SignalDecision.IGNORE)

    def test_counter_signal_confirmed_in_both_mode(self):
        guard = ReversalGuard()
        first = guard.evaluate("BTC/USDT:USDT", "BUY", MarketMode.BOTH, "SELL")
        second = guard.evaluate("BTC/USDT:USDT", "BUY", MarketMode.BOTH, "SELL")
        self.assertEqual(first.decision, SignalDecision.IGNORE)
        self.assertEqual(second.decision, SignalDecision.EXIT)

    def test_same_direction_signal_clears_pending(self):
        guard = ReversalGuard()
        guard.evaluate("BTC/USDT:USDT", "BUY", MarketMode.BOTH, "SELL")
        result = guard.evaluate("BTC/USDT:USDT", "SELL", MarketMode.BOTH, "SELL")
        self.assertEqual(result.decision, SignalDecision.IGNORE)
        self.assertNotIn("BTC/USDT:USDT", guard.pending)


if __name__ == "__main__":
    unittest.main()
