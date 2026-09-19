"""Test concept extraction and deduplication logic for KCET MCQs."""
import re

def extract_concept_fingerprint(q_text: str) -> str:
    """Extracts the underlying concept archetype of a question to prevent repetitive numerical variations."""
    if not q_text or not isinstance(q_text, str):
        return ""
    q = q_text.lower()
    
    # Physics Concepts
    if "projectile" in q or "launched" in q:
        if "maximum height" in q or "h_max" in q or "highest point" in q:
            return "concept:phy_projectile_max_height"
        if "range" in q or "horizontal distance" in q:
            return "concept:phy_projectile_range"
        if "time of flight" in q:
            return "concept:phy_projectile_time_of_flight"
        return "concept:phy_projectile_general"

    if "capacitor" in q or "capacitance" in q:
        if "energy" in q or "electrostatic energy" in q or "stored" in q:
            return "concept:phy_capacitor_energy"
        if "series" in q:
            return "concept:phy_capacitor_series"
        if "parallel" in q:
            return "concept:phy_capacitor_parallel"
        if "dielectric" in q:
            return "concept:phy_capacitor_dielectric"

    if "resistor" in q or "resistance" in q or "resistors" in q:
        if "parallel" in q:
            return "concept:phy_resistors_parallel"
        if "series" in q:
            return "concept:phy_resistors_series"
        if "stretched" in q or "length" in q:
            return "concept:phy_wire_stretching_resistance"
        if "wheatstone" in q or "bridge" in q:
            return "concept:phy_wheatstone_bridge"

    if "lens" in q or "mirror" in q or "focal length" in q:
        if "power" in q or "diopter" in q or "dioptres" in q:
            return "concept:phy_lens_power"
        if "combination" in q or "in contact" in q:
            return "concept:phy_lens_combination"
        if "magnification" in q:
            return "concept:phy_lens_magnification"

    if "refractive index" in q or "speed of light" in q:
        return "concept:phy_refraction_speed"

    if "de broglie" in q or "photoelectric" in q or "work function" in q:
        if "work function" in q or "threshold" in q:
            return "concept:phy_photoelectric_work_function"
        if "de broglie" in q:
            return "concept:phy_de_broglie_wavelength"

    if "transformer" in q:
        return "concept:phy_transformer_turns_ratio"

    if "bohr" in q or "orbit" in q or "atom" in q:
        if "radius" in q:
            return "concept:phy_bohr_orbit_radius"
        if "energy level" in q or "ionization" in q:
            return "concept:phy_bohr_energy_level"

    if "half-life" in q or "radioactive" in q or "decay" in q:
        return "concept:phy_radioactive_decay"

    if "carnot" in q or "efficiency" in q:
        return "concept:phy_carnot_engine"

    if "spring" in q or "force constant" in q:
        return "concept:phy_spring_potential_energy"

    if "shm" in q or "simple harmonic" in q:
        if "maximum velocity" in q or "v_max" in q:
            return "concept:phy_shm_max_velocity"
        if "time period" in q or "frequency" in q:
            return "concept:phy_shm_time_period"

    if "escape velocity" in q:
        return "concept:phy_escape_velocity"

    if "acceleration due to gravity" in q or "value of g" in q:
        return "concept:phy_gravity_variation"

    if "young's double slit" in q or "fringe width" in q:
        return "concept:phy_ydse_fringe_width"

    # Chemistry Concepts
    if "mole" in q or "molarity" in q or "molality" in q or "normality" in q:
        return "concept:chem_concentration_unit"

    if "arrhenius" in q or "activation energy" in q or "rate constant" in q:
        return "concept:chem_kinetics_arrhenius"

    if "nernst" in q or "emf of cell" in q or "standard reduction potential" in q:
        return "concept:chem_electrochemistry_nernst"

    if "ph of" in q or "buffer" in q or "solubility product" in q or "ksp" in q:
        return "concept:chem_ionic_equilibrium"

    if "aldol" in q or "cannizzaro" in q or "tollens" in q or "fehling" in q:
        return "concept:chem_organic_named_reaction"

    if "hybridization" in q or "vsepr" in q or "geometry" in q:
        return "concept:chem_bonding_hybridization"

    # Default fallback to normalized text fingerprint if no specific concept rule matched
    clean = re.sub(r"[^\w\s]", "", q)
    return " ".join(clean.split())

# Test questions
q1 = "A projectile is launched with an initial velocity of 20 m/s at an angle of 30° with the horizontal. The maximum height reached is:"
q2 = "A projectile is launched with an initial velocity of 50 m/s at an angle of 60° with the horizontal. The maximum height reached is:"
q3 = "A capacitor of capacitance 10 µF is charged by 50 V. The electrostatic energy stored is:"
q4 = "A capacitor of capacitance 20 µF is charged by 100 V. The electrostatic energy stored is:"

print("Q1 concept:", extract_concept_fingerprint(q1))
print("Q2 concept:", extract_concept_fingerprint(q2))
print("Q3 concept:", extract_concept_fingerprint(q3))
print("Q4 concept:", extract_concept_fingerprint(q4))
assert extract_concept_fingerprint(q1) == extract_concept_fingerprint(q2)
assert extract_concept_fingerprint(q3) == extract_concept_fingerprint(q4)
print("Concept extraction assertion PASSED successfully!")
