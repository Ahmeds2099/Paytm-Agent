from __future__ import annotations

import unittest

from mock_paytm import seed_data


class DemoFixtureResetTests(unittest.TestCase):
    def test_reset_restores_mutable_fixture_stores_and_counters(self):
        seed_data.QR_STORE["MID001"]["qr_status"] = "active"
        seed_data.SETTLEMENT_STORE["TXN001"]["amount"] = 0
        seed_data.REFUND_APPROVAL_STORE["approval"] = {"status": "pending"}
        seed_data.create_ticket("MID001", "qr_inactive")
        seed_data.create_refund("TXN999", 12)

        seed_data.reset_demo_fixtures()

        self.assertEqual(seed_data.QR_STORE["MID001"]["qr_status"], "inactive")
        self.assertEqual(seed_data.SETTLEMENT_STORE["TXN001"]["amount"], 1200.50)
        self.assertEqual(seed_data.REFUND_APPROVAL_STORE, {})
        self.assertNotIn("TXN999", seed_data.REFUND_STORE)
        self.assertEqual(seed_data.TICKET_STORE, seed_data._INITIAL_TICKET_STORE)
        self.assertEqual(seed_data.create_ticket("MID001", "qr_inactive")["ticket_id"], "TICKET-001")

    def tearDown(self):
        seed_data.reset_demo_fixtures()


if __name__ == "__main__":
    unittest.main()
