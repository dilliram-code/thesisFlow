"""
Scientific Constants Database and Cross-Referencer.
Curated from authoritative NIST CODATA recommended values.
Provides metadata, SI units, standard numerical values, physical meanings,
canonical equations, and automatic detection in mathematical expressions.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import re


@dataclass(frozen=True)
class ScientificConstant:
    symbol: str
    latex_symbol: str
    name: str
    value: float
    value_display: str
    uncertainty: str
    unit: str
    dimension: str
    meaning: str
    canonical_equation: str
    reference: str
    category: str  # Fundamental, Atomic, Thermodynamic, Electromagnetic, Cosmological


# Authoritative NIST CODATA Constants
SCIENTIFIC_CONSTANTS: Dict[str, ScientificConstant] = {
    "c": ScientificConstant(
        symbol="c",
        latex_symbol="c",
        name="Speed of Light in Vacuum",
        value=299792458.0,
        value_display="299,792,458",
        uncertainty="exact",
        unit="m s⁻¹",
        dimension="L T⁻¹",
        meaning="Universal physical constant representing the maximum speed at which all energy, matter, and information can travel.",
        canonical_equation="E = m c^2 \\quad \\text{and} \\quad c = \\frac{1}{\\sqrt{\\mu_0 \\varepsilon_0}}",
        reference="NIST CODATA 2018 / SI Definition (1983)",
        category="Fundamental"
    ),
    "h": ScientificConstant(
        symbol="h",
        latex_symbol="h",
        name="Planck Constant",
        value=6.62607015e-34,
        value_display="6.62607015 × 10⁻³⁴",
        uncertainty="exact",
        unit="J s",
        dimension="M L² T⁻¹",
        meaning="Quantum of electromagnetic action relating a photon's energy to its frequency.",
        canonical_equation="E = h \\nu",
        reference="NIST CODATA 2018 / SI 26th CGPM (2019)",
        category="Fundamental"
    ),
    "hbar": ScientificConstant(
        symbol="hbar",
        latex_symbol="\\hbar",
        name="Reduced Planck Constant (Dirac Constant)",
        value=1.054571817e-34,
        value_display="1.054571817 × 10⁻³⁴",
        uncertainty="exact",
        unit="J s",
        dimension="M L² T⁻¹",
        meaning="The quantum of angular momentum; standard form of Planck constant in quantum mechanics.",
        canonical_equation="i \\hbar \\frac{\\partial \\psi}{\\partial t} = \\hat{H}\\psi",
        reference="NIST CODATA 2018",
        category="Fundamental"
    ),
    "G": ScientificConstant(
        symbol="G",
        latex_symbol="G",
        name="Newtonian Constant of Gravitation",
        value=6.67430e-11,
        value_display="6.67430(15) × 10⁻¹¹",
        uncertainty="2.2 × 10⁻⁵",
        unit="m³ kg⁻¹ s⁻²",
        dimension="M⁻¹ L³ T⁻²",
        meaning="Empirical physical constant governing the gravitational force between masses.",
        canonical_equation="F = G \\frac{m_1 m_2}{r^2}",
        reference="CODATA Recommended Values (2018)",
        category="Cosmological"
    ),
    "e": ScientificConstant(
        symbol="e",
        latex_symbol="e",
        name="Elementary Charge",
        value=1.602176634e-19,
        value_display="1.602176634 × 10⁻¹⁹",
        uncertainty="exact",
        unit="C",
        dimension="I T",
        meaning="Electric charge carried by a single proton or electron magnitude.",
        canonical_equation="q = n e",
        reference="NIST CODATA 2018 / SI Definition (2019)",
        category="Electromagnetic"
    ),
    "k_B": ScientificConstant(
        symbol="k_B",
        latex_symbol="k_B",
        name="Boltzmann Constant",
        value=1.380649e-23,
        value_display="1.380649 × 10⁻²³",
        uncertainty="exact",
        unit="J K⁻¹",
        dimension="M L² T⁻² Θ⁻¹",
        meaning="Proportionality factor relating average kinetic energy of microscopic particles to absolute temperature.",
        canonical_equation="S = k_B \\ln \\Omega \\quad \\text{and} \\quad E_{avg} = \\frac{3}{2} k_B T",
        reference="NIST CODATA 2018 / SI Definition (2019)",
        category="Thermodynamic"
    ),
    "N_A": ScientificConstant(
        symbol="N_A",
        latex_symbol="N_A",
        name="Avogadro Constant",
        value=6.02214076e23,
        value_display="6.02214076 × 10²³",
        uncertainty="exact",
        unit="mol⁻¹",
        dimension="N⁻¹",
        meaning="Number of constituent particles in one mole of a given substance.",
        canonical_equation="N = n N_A \\quad \\text{and} \\quad R = N_A k_B",
        reference="NIST CODATA 2018 / SI Definition (2019)",
        category="Atomic"
    ),
    "m_e": ScientificConstant(
        symbol="m_e",
        latex_symbol="m_e",
        name="Electron Rest Mass",
        value=9.1093837015e-31,
        value_display="9.1093837015(28) × 10⁻³¹",
        uncertainty="3.0 × 10⁻¹⁰",
        unit="kg",
        dimension="M",
        meaning="Invariant rest mass of the electron.",
        canonical_equation="r_e = \\frac{e^2}{4\\pi\\varepsilon_0 m_e c^2}",
        reference="CODATA Recommended Values (2018)",
        category="Atomic"
    ),
    "m_p": ScientificConstant(
        symbol="m_p",
        latex_symbol="m_p",
        name="Proton Rest Mass",
        value=1.67262192369e-27,
        value_display="1.67262192369(51) × 10⁻²⁷",
        uncertainty="3.1 × 10⁻¹⁰",
        unit="kg",
        dimension="M",
        meaning="Invariant rest mass of a free proton.",
        canonical_equation="m_p \\approx 1836.15 \\, m_e",
        reference="CODATA Recommended Values (2018)",
        category="Atomic"
    ),
    "epsilon_0": ScientificConstant(
        symbol="epsilon_0",
        latex_symbol="\\varepsilon_0",
        name="Vacuum Electric Permittivity",
        value=8.8541878128e-12,
        value_display="8.8541878128(13) × 10⁻¹²",
        uncertainty="1.5 × 10⁻¹⁰",
        unit="F m⁻¹",
        dimension="M⁻¹ L⁻³ T⁴ I²",
        meaning="Capability of classical vacuum to permit electric field lines.",
        canonical_equation="F = \\frac{1}{4\\pi\\varepsilon_0} \\frac{q_1 q_2}{r^2}",
        reference="CODATA Recommended Values (2018)",
        category="Electromagnetic"
    ),
    "mu_0": ScientificConstant(
        symbol="mu_0",
        latex_symbol="\\mu_0",
        name="Vacuum Magnetic Permeability",
        value=1.25663706212e-6,
        value_display="1.25663706212(19) × 10⁻⁶",
        uncertainty="1.5 × 10⁻¹⁰",
        unit="N A⁻² (H m⁻¹)",
        dimension="M L T⁻² I⁻²",
        meaning="Magnetic susceptibility of classical vacuum.",
        canonical_equation="B = \\frac{\\mu_0 I}{2\\pi r}",
        reference="CODATA Recommended Values (2018)",
        category="Electromagnetic"
    ),
    "alpha": ScientificConstant(
        symbol="alpha",
        latex_symbol="\\alpha",
        name="Fine-Structure Constant",
        value=7.2973525693e-3,
        value_display="7.2973525693(11) × 10⁻³ (≈ 1/137.036)",
        uncertainty="1.5 × 10⁻¹⁰",
        unit="dimensionless",
        dimension="1",
        meaning="Fundamental physical constant characterizing the strength of the electromagnetic interaction between elementary charged particles.",
        canonical_equation="\\alpha = \\frac{e^2}{4\\pi\\varepsilon_0 \\hbar c}",
        reference="CODATA Recommended Values (2018)",
        category="Fundamental"
    ),
    "sigma": ScientificConstant(
        symbol="sigma",
        latex_symbol="\\sigma",
        name="Stefan-Boltzmann Constant",
        value=5.670374419e-8,
        value_display="5.670374419 × 10⁻⁸",
        uncertainty="exact",
        unit="W m⁻² K⁻⁴",
        dimension="M T⁻³ Θ⁻⁴",
        meaning="Constant of proportionality in the Stefan-Boltzmann law for blackbody radiation emissive power.",
        canonical_equation="j^* = \\sigma T^4",
        reference="CODATA 2018 / SI Definition",
        category="Thermodynamic"
    ),
    "R": ScientificConstant(
        symbol="R",
        latex_symbol="R",
        name="Molar Gas Constant",
        value=8.314462618,
        value_display="8.314462618",
        uncertainty="exact",
        unit="J mol⁻¹ K⁻¹",
        dimension="M L² T⁻² N⁻¹ Θ⁻¹",
        meaning="Constant relating energy scale in physics to temperature scale for a mole of ideal gas.",
        canonical_equation="P V = n R T",
        reference="CODATA 2018 / SI Definition",
        category="Thermodynamic"
    ),
    "a_0": ScientificConstant(
        symbol="a_0",
        latex_symbol="a_0",
        name="Bohr Radius",
        value=5.29177210903e-11,
        value_display="5.29177210903(80) × 10⁻¹¹",
        uncertainty="1.5 × 10⁻¹⁰",
        unit="m",
        dimension="L",
        meaning="Most probable distance between the nucleus and the electron in a hydrogen atom in its ground state.",
        canonical_equation="a_0 = \\frac{4\\pi\\varepsilon_0\\hbar^2}{m_e e^2}",
        reference="CODATA Recommended Values (2018)",
        category="Atomic"
    ),
}


def get_all_constants() -> List[ScientificConstant]:
    """Return all defined scientific constants."""
    return list(SCIENTIFIC_CONSTANTS.values())


def get_constant_by_symbol(symbol: str) -> Optional[ScientificConstant]:
    """Lookup constant by symbol or key."""
    norm = symbol.strip().replace("\\", "").replace("{", "").replace("}", "")
    if norm in SCIENTIFIC_CONSTANTS:
        return SCIENTIFIC_CONSTANTS[norm]
    # Check alternate keys
    alt_map = {
        "kB": "k_B",
        "k": "k_B",
        "NA": "N_A",
        "me": "m_e",
        "mp": "m_p",
        "eps0": "epsilon_0",
        "varepsilon": "epsilon_0",
        "mu0": "mu_0",
        "h_bar": "hbar",
    }
    alt_key = alt_map.get(norm)
    return SCIENTIFIC_CONSTANTS.get(alt_key) if alt_key else None


def identify_constants_in_equation(expression_str: str) -> List[ScientificConstant]:
    """
    Scans a mathematical expression (LaTeX or plain text) for recognized physical constants.
    Uses regex word boundaries and symbol tokenization.
    """
    found: Dict[str, ScientificConstant] = {}

    # Token-based detection
    tokens = re.findall(r"\\[a-zA-Z_]+|[a-zA-Z]_[a-zA-Z0-9]+|[a-zA-Z]", expression_str)

    symbol_targets = {
        "\\hbar": "hbar",
        "hbar": "hbar",
        "\\varepsilon_0": "epsilon_0",
        "\\epsilon_0": "epsilon_0",
        "\\mu_0": "mu_0",
        "k_B": "k_B",
        "k_b": "k_B",
        "N_A": "N_A",
        "N_a": "N_A",
        "m_e": "m_e",
        "m_p": "m_p",
        "a_0": "a_0",
        "\\alpha": "alpha",
        "\\sigma": "sigma",
    }

    for token in tokens:
        if token in symbol_targets:
            key = symbol_targets[token]
            if key in SCIENTIFIC_CONSTANTS:
                found[key] = SCIENTIFIC_CONSTANTS[key]

    # Check standalone single letters when context matches
    text = expression_str
    if re.search(r"\bc\b|\bc\^2\b", text):
        found["c"] = SCIENTIFIC_CONSTANTS["c"]
    if re.search(r"\bh\b(?![a-zA-Z])", text) and "hbar" not in found:
        # Check if it looks like quantum action
        if "\\nu" in text or "f" in text or "lambda" in text or "E =" in text:
            found["h"] = SCIENTIFIC_CONSTANTS["h"]
    if re.search(r"\bG\b", text) and ("m_1" in text or "m_2" in text or "r^2" in text or "M" in text):
        found["G"] = SCIENTIFIC_CONSTANTS["G"]

    return list(found.values())

