import unittest
from src.deconfliction.temporal_check import check_temporal_conflict

class TestTemporalCheck(unittest.TestCase):

    def setUp(self):
        self.primary_mission = {
            "waypoints": [(0, 0), (1, 1), (2, 2)],
            "time_window": (0, 10)
        }
        self.simulated_flights = [
            {
                "waypoints": [(0, 1), (1, 2)],
                "time_window": (5, 15)
            },
            {
                "waypoints": [(2, 2), (3, 3)],
                "time_window": (0, 5)
            }
        ]

    def test_no_conflict(self):
        result = check_temporal_conflict(self.primary_mission, self.simulated_flights)
        self.assertFalse(result)

    def test_conflict_detected(self):
        self.simulated_flights[0]["time_window"] = (8, 12)  # Overlaps with primary mission
        result = check_temporal_conflict(self.primary_mission, self.simulated_flights)
        self.assertTrue(result)

    def test_edge_case(self):
        self.simulated_flights[1]["time_window"] = (10, 12)  # Ends exactly when primary mission ends
        result = check_temporal_conflict(self.primary_mission, self.simulated_flights)
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()