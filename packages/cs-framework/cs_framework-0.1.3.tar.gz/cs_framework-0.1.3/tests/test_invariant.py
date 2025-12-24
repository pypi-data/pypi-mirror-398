import unittest
import uuid
from cs_framework.core.concept import Concept
from cs_framework.engine.runner import Runner
from cs_framework.core.invariant import Invariant

class Wallet(Concept):
    def __init__(self, name: str):
        super().__init__(name)
        self._state = {"balance": 100}

    def spend(self, payload: dict):
        self._state["balance"] -= payload.get("amount", 0)

class TestInvariant(unittest.TestCase):
    def test_invariant_violation(self):
        runner = Runner()
        wallet = Wallet("MyWallet")
        runner.register(wallet)

        # Invariant: Balance must be non-negative
        def check_balance(global_state):
            # Find wallet state
            wallet_state = global_state.get(wallet.id)
            if wallet_state:
                return wallet_state["balance"] >= 0
            return True

        inv = Invariant("NoDebt", check_balance, "Balance cannot be negative")
        runner.register(inv)
        runner.start()

        # 1. Valid transaction
        runner.dispatch(wallet.id, "spend", {"amount": 50})
        self.assertEqual(wallet._state["balance"], 50)

        # 2. Invalid transaction (should raise RuntimeError)
        with self.assertRaises(RuntimeError) as cm:
            runner.dispatch(wallet.id, "spend", {"amount": 60})
        
        self.assertIn("Invariant Violation: NoDebt", str(cm.exception))

if __name__ == '__main__':
    unittest.main()
