"""
Hamiltonian construction modules for Jahn-Teller physics.

This package provides pure functions to construct various Hamiltonians:
- DJT (Dynamic Jahn-Teller) Hamiltonians
- Spin-orbit coupling interactions
- External field interactions (magnetic, electric, strain)

All functions are designed to be:
- Pure (no side effects)
- Well-documented with physics formulas
- Testable independently
"""

from .djt_hamiltonian import (
    create_one_mode_djt_hamiltonian,
    create_multi_mode_djt_hamiltonian,
)

from .spin_orbit import (
    create_spin_orbit_coupling,
)

from .field_interactions import (
    create_magnetic_field_interaction,
    create_electric_field_interaction,
    create_strain_field_interaction,
    BOHR_MAGNETON_MEV_T,
    G_FACTOR,
)

__all__ = [
    'create_one_mode_djt_hamiltonian',
    'create_multi_mode_djt_hamiltonian',
    'create_spin_orbit_coupling',
    'create_magnetic_field_interaction',
    'create_electric_field_interaction',
    'create_strain_field_interaction',
    'BOHR_MAGNETON_MEV_T',
    'G_FACTOR',
]

