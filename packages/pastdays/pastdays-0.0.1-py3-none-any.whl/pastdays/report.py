import numpy as np


class Report:

    def __init__(self, outcomes, k, lookahead_minutes):
        self.outcomes = outcomes
        self.k = k
        self.lookahead_minutes = lookahead_minutes

    def summary(self):
        if not self.outcomes:
            print("No similar days found.")
            return

        final_moves = np.array([o["final_move"] for o in self.outcomes])
        max_ups = np.array([o["max_up"] for o in self.outcomes])
        max_downs = np.array([o["max_down"] for o in self.outcomes])

        print("Past Similar Days Report")
        print("-" * 30)
        print(f"Matched days: {len(self.outcomes)}")
        print(f"Lookahead window: {self.lookahead_minutes} minutes\n")

        print(f"Median final move: {np.median(final_moves):.2f}%")
        print(f"Best move observed: {np.max(max_ups):.2f}%")
        print(f"Worst move observed: {np.min(max_downs):.2f}%")

        print("\nDistribution:")
        print(f"Positive days: {(final_moves > 0).sum()}")
        print(f"Negative days: {(final_moves < 0).sum()}")
        print(f"Flat days: {(final_moves == 0).sum()}")
