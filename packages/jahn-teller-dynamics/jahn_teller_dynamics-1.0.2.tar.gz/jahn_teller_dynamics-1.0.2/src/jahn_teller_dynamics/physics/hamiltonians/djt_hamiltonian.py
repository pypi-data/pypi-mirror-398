"""
Dynamic Jahn-Teller (DJT) Hamiltonian construction.

This module provides functions to construct the DJT Hamiltonian:
    H_DJT = K ⊗ I + F(X ⊗ σ_z - Y ⊗ σ_x) + G((XX-YY) ⊗ σ_z + 2XY ⊗ σ_x)

Where:
    - K: Phonon kinetic energy operator
    - X, Y: Position operators (normal mode coordinates)
    - XX, YY, XY: Quadratic position operators
    - σ_x, σ_z: Pauli matrices (orbital operators)
    - F, G: Taylor coefficients from JT theory
    - ⊗: Tensor product

Physical interpretation:
    The first term (K ⊗ I) is the phonon energy.
    The second term (F(...)) is the linear JT coupling.
    The third term (G(...)) is the quadratic JT coupling.

References:
    - Bersuker, I. B. (2006). The Jahn-Teller Effect. Cambridge University Press.
    - Section 3.2, equation (3.15)
"""

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jahn_teller_dynamics.physics.jahn_teller_theory import Jahn_Teller_Theory
    from jahn_teller_dynamics.math.matrix_mechanics import MatrixOperator
    import jahn_teller_dynamics.physics.quantum_system as qs
else:
    import jahn_teller_dynamics.physics.quantum_system as qs


def create_one_mode_djt_hamiltonian(
    system_tree: 'qs.quantum_system_tree',
    jt_theory: 'Jahn_Teller_Theory'
) -> 'MatrixOperator':
    """
    Construct the one-mode DJT Hamiltonian.
    
    Formula:
        H = K ⊗ I + F(X ⊗ σ_z - Y ⊗ σ_x) + G((XX-YY) ⊗ σ_z + 2XY ⊗ σ_x)
    
    Where:
        - K: Phonon kinetic energy operator
        - X, Y: Position operators
        - XX, YY, XY: Quadratic position operators  
        - σ_x, σ_z: Orbital operators (Pauli matrices)
        - F, G: Taylor coefficients from JT theory
    
    Args:
        system_tree: Quantum system tree containing operators
        jt_theory: Jahn-Teller theory parameters (F, G, hw)
        
    Returns:
        MatrixOperator: The DJT Hamiltonian
        
    Raises:
        ValueError: If required operators are not found in system_tree
    """
    # Extract phonon operators
    X = system_tree.create_operator('X', 'nuclei')
    Y = system_tree.create_operator('Y', 'nuclei')
    XX = system_tree.create_operator('XX', 'nuclei')
    YY = system_tree.create_operator('YY', 'nuclei')
    XY = system_tree.create_operator('XY', 'nuclei')
    K = system_tree.create_operator('K', 'nuclei')
    
    # Extract electron operators
    s0 = system_tree.find_subsystem('electron_system').create_id_op()
    sz = system_tree.create_operator('Z_orb', 'electron_system')
    sx = system_tree.create_operator('X_orb', 'electron_system')
    
    # Construct Hamiltonian according to formula:
    # H = K ⊗ I + F(X ⊗ σ_z - Y ⊗ σ_x) + G((XX-YY) ⊗ σ_z + 2XY ⊗ σ_x)
    H = (K ** s0 + 
         jt_theory.F * (X ** sz - Y ** sx) + 
         jt_theory.G * ((XX - YY) ** sz + (2 * XY) ** sx))
    
    return H


def create_multi_mode_djt_hamiltonian(
    system_tree: 'qs.quantum_system_tree',
    jt_theory: 'Jahn_Teller_Theory'
) -> 'MatrixOperator':
    """
    Construct multi-mode DJT Hamiltonian as sum over modes.
    
    Formula:
        H = Σ_i [K_i ⊗ I + F_i(X_i ⊗ σ_z + Y_i ⊗ σ_x) + G_i((XX_i-YY_i) ⊗ σ_z - 2XY_i ⊗ σ_x)]
    
    Where the sum is over all phonon modes i.
    
    Args:
        system_tree: Quantum system tree
        jt_theory: JT theory parameters
        
    Returns:
        MatrixOperator: Multi-mode DJT Hamiltonian
        
    Raises:
        ValueError: If required operators are not found
    """
    import jahn_teller_dynamics.math.matrix_mechanics as mm
    
    hamiltons = []
    nuclei = system_tree.find_subsystem('nuclei')
    
    # Handle case where find_subsystem returns a list
    if isinstance(nuclei, list):
        nuclei = nuclei[0]
    
    for osc_mode in nuclei.children:
        # Set quantum for this mode
        jt_theory.set_quantum(osc_mode.mode)
        
        # Get operators for this mode
        osc_mode_id = osc_mode.id
        X = system_tree.create_operator('X', subsys_id='nuclei', operator_sys=osc_mode_id)
        Y = system_tree.create_operator('Y', subsys_id='nuclei', operator_sys=osc_mode_id)
        XX = system_tree.create_operator('XX', subsys_id='nuclei', operator_sys=osc_mode_id)
        YY = system_tree.create_operator('YY', subsys_id='nuclei', operator_sys=osc_mode_id)
        XY = system_tree.create_operator('XY', subsys_id='nuclei', operator_sys=osc_mode_id)
        K = system_tree.create_operator('K', subsys_id='nuclei', operator_sys=osc_mode_id)
        
        s0 = system_tree.create_operator('s0', 'electron_system')
        sz = system_tree.create_operator('sz', 'electron_system')
        sx = system_tree.create_operator('sx', 'electron_system')
        
        # Construct mode Hamiltonian
        h = (K ** s0 + 
             jt_theory.F * (X ** sz + Y ** sx) + 
             jt_theory.G * ((XX - YY) ** sz - (2 * XY) ** sx))
        hamiltons.append(h)
    
    return sum(hamiltons)

