import unittest
from racket_lab.advisor import StringsAdvisor, RacketMatcher, StringMaterial, PlayerProfile
from racket_lab.racket import Racket

class TestAdvisor(unittest.TestCase):
    
    def test_suggest_tension_poly_injury(self):
        profile = PlayerProfile(has_injury_history=True)
        tension = StringsAdvisor.suggest_tension(StringMaterial.POLYESTER, 100, profile)
        self.assertEqual(tension, 44)
        
    def test_suggest_tension_gut_control(self):
        profile = PlayerProfile(has_injury_history=False)
        tension = StringsAdvisor.suggest_tension(StringMaterial.NATURAL_GUT, 95, profile)
        self.assertEqual(tension, 52)

    def test_suggest_tension_big_head(self):
        profile = PlayerProfile()
        tension = StringsAdvisor.suggest_tension(StringMaterial.SYNTHETIC_GUT, 105, profile)
        self.assertEqual(tension, 54)
        
    def test_find_closest_match(self):
        # Target: Pure Drive-ish: 300g, 32cm, 290SW
        target = Racket("Target", 300, 32, 290)
        
        # Candidate 1: Identical specs but different name
        r1 = Racket("Match", 300, 32, 290)
        
        # Candidate 2: Different Mass
        r2 = Racket("Heavy", 305, 32, 290)
        
        # Candidate 3: Itself (should skip)
        r3 = Racket("Target", 300, 32, 290)
        
        candidates = [r1, r2, r3]
        
        match = RacketMatcher.find_closest_match(target, candidates)
        self.assertEqual(match.name, "Match")

if __name__ == '__main__':
    unittest.main()
