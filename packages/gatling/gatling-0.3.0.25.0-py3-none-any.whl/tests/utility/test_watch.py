import unittest
from datetime import timedelta
import time

from gatling.utility.watch import Watch, watch_time  # adjust import path if needed


class TestWatchTime(unittest.TestCase):
    """Functional tests for Watch class and @watch_time decorator (no timing checks)."""

    # ------------------------------------------------------------
    def test_watch_time_decorator(self):
        """Ensure @watch_time executes and returns expected value."""

        @watch_time
        def decorated_function(value):
            """Simple test function that returns its argument."""
            # a small sleep just to simulate work
            time.sleep(0.01)
            return f"OK-{value}"

        result = decorated_function("demo")

        # Function runs successfully
        self.assertIsInstance(result, str)
        self.assertTrue(result.startswith("OK-"))

    # ------------------------------------------------------------
    def test_watch_class_methods(self):
        """Ensure Watch methods run and return correct types."""

        watch = Watch()

        # see_timedelta() should return timedelta
        td = watch.see_timedelta()
        self.assertIsInstance(td, timedelta)

        # see_seconds() should return float
        secs = watch.see_seconds()
        self.assertIsInstance(secs, float)

        # total_timedelta() should return timedelta
        total_td = watch.total_timedelta()
        self.assertIsInstance(total_td, timedelta)

        # total_seconds() should return float
        total_secs = watch.total_seconds()
        self.assertIsInstance(total_secs, float)

        # Internal structure check
        self.assertTrue(hasattr(watch, "records"))
        self.assertIsInstance(watch.records, list)

        print("\nAll Watch methods executed and returned correct types.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
