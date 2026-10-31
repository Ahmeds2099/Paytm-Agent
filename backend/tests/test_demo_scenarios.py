from __future__ import annotations

import unittest

from app.services.demo_scenarios import get_scenario, list_merchants


class DemoScenarioDescriptionTests(unittest.TestCase):
    def test_every_demo_scenario_has_a_description(self):
        merchants = list_merchants()

        self.assertTrue(merchants)
        self.assertTrue(
            all(
                isinstance(merchant.get("scenario_description"), str)
                and merchant["scenario_description"].strip()
                for merchant in merchants
            )
        )

    def test_pending_settlement_explains_priority_follow_up(self):
        merchant = next(
            merchant
            for merchant in list_merchants()
            if merchant["scenario_id"] == "settlement_pending"
        )

        self.assertEqual(
            merchant["scenario_label"],
            "Pending Settlement · Priority Follow-up",
        )
        self.assertIn("TXN002", merchant["scenario_description"])
        self.assertIn("₹750", merchant["scenario_description"])
        self.assertIn("priority support ticket", merchant["scenario_description"])

    def test_repeated_complaint_explains_escalation_threshold(self):
        merchant = next(
            merchant
            for merchant in list_merchants()
            if merchant["scenario_id"] == "repeated_escalation"
        )
        scenario = get_scenario(merchant["merchant_id"])

        self.assertIn("two support tickets", merchant["scenario_description"])
        self.assertIn("second consecutive repeat", merchant["scenario_description"])
        self.assertIn("second consecutive repeat complaint", scenario["prompt_context"])


if __name__ == "__main__":
    unittest.main()
