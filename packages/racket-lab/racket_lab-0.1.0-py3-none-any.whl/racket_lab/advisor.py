from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional
import math
from .racket import Racket  # Assuming Racket class is in racket.py

class StringMaterial(Enum):
    POLYESTER = auto()
    MULTIFILAMENT = auto()
    NATURAL_GUT = auto()
    SYNTHETIC_GUT = auto()

@dataclass
class PlayerProfile:
    has_injury_history: bool = False
    prefers_spin: bool = True
    level: str = "intermediate"  # beginner, intermediate, advanced

class StringsAdvisor:
    """
    Logic for recommending string setups based on physics and player health.
    """
    
    @staticmethod
    def suggest_tension(material: StringMaterial, head_size_sq_in: int, profile: PlayerProfile) -> int:
        """
        Calculates optimal reference tension (lbs).
        """
        # 1. Start with a standard baseline
        tension = 52.0
        
        # 2. Adjust for Material Stiffness (Polyester is stiff -> drop tension)
        if material == StringMaterial.POLYESTER:
            tension -= 4  # Drop tension to open up the sweet spot
        elif material == StringMaterial.NATURAL_GUT:
            tension += 2  # Gut is powerful, needs control
            
        # 3. Adjust for Racket Physics (Trampoline Effect)
        # Larger heads (>100) have more power -> need tighter strings for control
        if head_size_sq_in > 100:
            tension += 2
        elif head_size_sq_in < 98:
            tension -= 2
            
        # 4. Adjust for Health (The "Doctor" logic)
        if profile.has_injury_history and material == StringMaterial.POLYESTER:
            # Strong warning logic: dropping tension significantly for safety
            tension -= 4
            
        return int(round(tension))

class RacketMatcher:
    """
    Finds similar rackets using vector distance algorithms.
    """
    
    @staticmethod
    def find_closest_match(current_racket: Racket, database: List[Racket]) -> Racket:
        """
        Returns the racket from the database that is most similar to the current_racket.
        Uses Weighted Euclidean Distance.
        """
        best_match = None
        min_distance = float('inf')
        
        for candidate in database:
            if candidate.name == current_racket.name:
                continue # Skip itself
            
            # Normalize differences (approximate normalization factors)
            # We weight Swingweight (SW) higher because it defines "feel"
            mass_diff = abs(current_racket.mass_kg - candidate.mass_kg) * 100 # *100 to make it comparable to SW
            bal_diff = abs(current_racket.balance_cm - candidate.balance_cm) * 2
            sw_diff = abs(current_racket.swingweight - candidate.swingweight)
            
            # Weighted Distance Formula
            # Distance = sqrt( (2*MassDiff)^2 + (BalanceDiff)^2 + (1.5*SW_Diff)^2 )
            distance = math.sqrt( (2 * mass_diff)**2 + (bal_diff)**2 + (1.5 * sw_diff)**2 )
            
            if distance < min_distance:
                min_distance = distance
                best_match = candidate
                
        return best_match
