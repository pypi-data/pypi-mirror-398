"""
Spin-orbit coupling (SOC) interactions.

This module provides functions to construct SOC Hamiltonians:
    H_SOC = λ (L_z ⊗ S_z)

Where:
    - λ: SOC strength (intrinsic_soc * p_factor for full model, lambda_theory for minimal)
    - L_z: Orbital angular momentum operator
    - S_z: Spin angular momentum operator

Physical interpretation:
    The spin-orbit coupling couples the orbital angular momentum (L_z)
    with the spin angular momentum (S_z), with strength λ.

References:
    - Abragam, A., & Bleaney, B. (1970). Electron Paramagnetic Resonance 
      of Transition Ions. Oxford University Press.
"""

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jahn_teller_dynamics.math.matrix_mechanics import MatrixOperator
    import jahn_teller_dynamics.physics.quantum_system as qs
else:
    import jahn_teller_dynamics.physics.quantum_system as qs


def create_spin_orbit_coupling(
    system_tree: 'qs.quantum_system_tree',
    lambda_soc: float
) -> 'MatrixOperator':
    """
    Construct spin-orbit coupling Hamiltonian.
    
    Formula:
        H_SOC = λ (L_z ⊗ S_z)
    
    Where:
        - λ: SOC strength in meV
        - L_z: Orbital angular momentum operator
        - S_z: Spin angular momentum operator
    
    Args:
        system_tree: Quantum system tree
        lambda_soc: SOC strength in meV
        
    Returns:
        MatrixOperator: SOC Hamiltonian at root node level
        
    Raises:
        ValueError: If required operators are not found
    """
    # Get root node ID dynamically for reusability
    root_node_id = system_tree.root_node.id
    
    # Create operators at root node level
    Sz = system_tree.create_operator('Sz', root_node_id, 'spin_system')
    Lz = system_tree.create_operator('Lz', root_node_id, 'orbital_system')
    return lambda_soc * (Lz * Sz)

