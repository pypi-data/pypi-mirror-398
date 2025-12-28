import unittest
from racket_lab.racket import Racket

class TestRacket(unittest.TestCase):
    def setUp(self):
        # Standard "tweener" racket specs
        self.mass_g = 300.0
        self.balance_cm = 32.0
        self.swingweight = 290.0
        # Signature: name, mass_g, balance_cm, swingweight
        self.racket = Racket("Test Racket", self.mass_g, self.balance_cm, self.swingweight)

    def test_recoil_weight(self):
        # Formula: SW - Mass_kg * (Balance_cm - 10)^2
        # RW = 290 - 0.3 * (22)^2 = 290 - 0.3 * 484 = 290 - 145.2 = 144.8
        expected_rw = 144.8
        self.assertAlmostEqual(self.racket.recoil_weight(), expected_rw, places=2)

    def test_mgr_i(self):
        # Formula: (Mass_kg * 980.5 * Balance_cm) / (SW + (20 * Mass_kg * Balance_cm) - (100 * Mass_kg))
        # Num = 0.3 * 980.5 * 32 = 9412.8
        # Denom = 290 + (20 * 0.3 * 32) - (100 * 0.3) = 290 + 192 - 30 = 452
        # MGR/I = 9412.8 / 452 = 20.8247...
        expected_mgri = 9412.8 / 452
        self.assertAlmostEqual(self.racket.mgr_i(), expected_mgri, places=4)

    def test_customize_mass_only(self):
        # Add 5g at Balance Point (should not change balance)
        new_racket = self.racket.customize(5.0, 32.0)
        
        self.assertEqual(new_racket.mass_g, 305.0)
        self.assertAlmostEqual(new_racket.balance_cm, 32.0, places=2)
        
        # SW increases: 0.005 * (32-10)^2 = 0.005 * 484 = 2.42
        expected_sw = 290 + 2.42
        self.assertAlmostEqual(new_racket.swingweight, expected_sw, places=2)

    def test_customize_polarization(self):
        # Add 2g at 12 o'clock (dictates ~68cm approx, let's say 60cm for simple match from before)
        added_mass = 10.0
        pos = 60.0
        
        new_racket = self.racket.customize(added_mass, pos)
        
        # Mass: 310
        self.assertEqual(new_racket.mass_g, 310.0)
        
        # Balance: (300*32 + 10*60) / 310 = (9600 + 600) / 310 = 10200 / 310 = 32.903...
        expected_bal = (300*32 + 10*60) / 310
        self.assertAlmostEqual(new_racket.balance_cm, expected_bal, places=2)
        
        # SW: 290 + 0.01 * (60-10)^2 = 290 + 0.01 * 2500 = 290 + 25 = 315
        self.assertAlmostEqual(new_racket.swingweight, 315.0, places=2)

    def test_immutability(self):
        original_rw = self.racket.recoil_weight()
        _ = self.racket.customize(10, 50)
        # Original should remain unchanged
        self.assertEqual(self.racket.mass_g, 300.0)
        self.assertEqual(self.racket.recoil_weight(), original_rw)

if __name__ == '__main__':
    unittest.main()
