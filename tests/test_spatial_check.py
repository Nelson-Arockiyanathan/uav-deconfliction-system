import unittest
from src.deconfliction.spatial_check import check_spatial_conflict

class TestSpatialCheck(unittest.TestCase):

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
                "waypoints": [(3, 3), (4, 4)],
                "time_window": (0, 5)
            }
        ]

    def test_no_conflict(self):
        result = check_spatial_conflict(self.primary_mission, self.simulated_flights)
        self.assertFalse(result)

    def test_conflict_detected(self):
        self.simulated_flights[0]["waypoints"] = [(1, 1), (2, 2)]
        result = check_spatial_conflict(self.primary_mission, self.simulated_flights)
        self.assertTrue(result)

    def test_edge_case(self):
        self.primary_mission["waypoints"].append((1, 1))
        result = check_spatial_conflict(self.primary_mission, self.simulated_flights)
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()