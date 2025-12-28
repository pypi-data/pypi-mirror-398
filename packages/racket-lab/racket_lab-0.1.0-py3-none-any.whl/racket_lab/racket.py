from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Racket:
    """
    Represents a tennis racket with physical properties.
    Immutable to ensure safe chainable customizations.
    """
    name: str
    mass_g: float
    balance_cm: float
    swingweight: float

    @property
    def mass_kg(self) -> float:
        return self.mass_g / 1000.0

    def recoil_weight(self) -> float:
        """
        Calculates the Recoil Weight (RW) of the racket.
        Formula: SW - Mass_kg * (Balance_cm - 10)^2
        RW represents the resistance to angular acceleration around the balance point.
        """
        mass_kg = self.mass_g / 1000.0
        return self.swingweight - (mass_kg * (self.balance_cm - 10) ** 2)

    def mgr_i(self) -> float:
        """
        Calculates the Maneuverability Index (MGR/I).
        Formula derived from pendulum physics:
        (Mass_kg * 980.5 * Balance_cm) / (SW + (20 * Mass_kg * Balance_cm) - (100 * Mass_kg))
        
        Typical values range from 20 to 21.5. 
        Higher values indicate easier timing/maneuverability.
        """
        mass_kg = self.mass_g / 1000.0
        numerator = mass_kg * 980.5 * self.balance_cm
        denominator = self.swingweight + (20 * mass_kg * self.balance_cm) - (100 * mass_kg)
        
        if denominator == 0:
            raise ValueError("Denominator in MGR/I calculation is zero.")
            
        return numerator / denominator

    def customize(self, mass_added_g: float, position_cm: float) -> Racket:
        """
        Adds weight to the racket at a specific position and returns a NEW Racket instance.
        
        Physics:
        - New Mass: Simple addition.
        - New Balance: Moment of moments ((M1*B1 + m2*b2) / (M1+m2))
        - New Swingweight: Parallel Axis Theorem (SW_new = SW_old + m_added_kg * (d - 10)^2)
          Note: d is distance from pivot (10cm from butt cap).
        
        Args:
            mass_added_g: Weight added in grams.
            position_cm: Position of added weight in cm from butt cap.
            
        Returns:
            A new Racket instance with updated specs.
        """
        new_mass_g = self.mass_g + mass_added_g
        
        # Calculate new balance point
        # Moment = Force * Distance. Here we use Mass * Distance as gravity cancels out.
        current_moment = self.mass_g * self.balance_cm
        added_moment = mass_added_g * position_cm
        new_balance_cm = (current_moment + added_moment) / new_mass_g
        
        # Calculate new Swingweight using Parallel Axis Theorem
        # The pivot for SW is standard 10cm from butt cap.
        # Added SW = mass_kg * r^2
        # r = distance from the 10cm pivot point = (position_cm - 10)
        mass_added_kg = mass_added_g / 1000.0
        r_cm = position_cm - 10.0
        added_sw = mass_added_kg * (r_cm ** 2)
        new_swingweight = self.swingweight + added_sw
        
        return Racket(
            name=f"{self.name} (Customized)",
            mass_g=new_mass_g,
            balance_cm=new_balance_cm,
            swingweight=new_swingweight
        )
