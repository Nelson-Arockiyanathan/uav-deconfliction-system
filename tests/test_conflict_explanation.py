import unittest
from src.deconfliction.conflict_explanation import explain_conflicts

class TestConflictExplanation(unittest.TestCase):

    def test_explain_conflicts_single(self):
        conflicts = [
            {
                'location': (10, 20),
                'time': (5, 10),
                'flights': ['Drone A', 'Drone B']
            }
        ]
        expected_output = "Conflict detected at location (10, 20) during time (5, 10) caused by flights: Drone A, Drone B"
        self.assertEqual(explain_conflicts(conflicts), expected_output)

    def test_explain_conflicts_multiple(self):
        conflicts = [
            {
                'location': (10, 20),
                'time': (5, 10),
                'flights': ['Drone A', 'Drone B']
            },
            {
                'location': (15, 25),
                'time': (8, 12),
                'flights': ['Drone C']
            }
        ]
        expected_output = (
            "Conflict detected at location (10, 20) during time (5, 10) caused by flights: Drone A, Drone B\n"
            "Conflict detected at location (15, 25) during time (8, 12) caused by flights: Drone C"
        )
        self.assertEqual(explain_conflicts(conflicts), expected_output)

    def test_explain_conflicts_no_conflicts(self):
        conflicts = []
        expected_output = "No conflicts detected."
        self.assertEqual(explain_conflicts(conflicts), expected_output)

if __name__ == '__main__':
    unittest.main()