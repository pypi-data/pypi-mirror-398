"""
External field interactions (magnetic, electric, strain).

Magnetic field interactions:
    H_mag = μ_B [g_L (L_z B_z) + g_s (S · B) + 2δ_f (S_z B_z)]
    
Electric field interactions:
    H_el = E_x Z + E_y X
    
Strain field interactions:
    H_strain = -Y_x L_x + Y_y L_y + Y_z L_z

Where:
    - μ_B: Bohr magneton (0.057883671 meV/T)
    - g_L: Orbital g-factor (orbital_red_fact)
    - g_s: Spin g-factor (2.0023)
    - B: Magnetic field vector
    - E: Electric field vector
    - Y: Strain field vector
"""

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jahn_teller_dynamics.math.matrix_mechanics import MatrixOperator
    import jahn_teller_dynamics.math.maths as maths
    import jahn_teller_dynamics.physics.quantum_system as qs
else:
    import jahn_teller_dynamics.math.maths as maths
    import jahn_teller_dynamics.physics.quantum_system as qs

# Physical constants
BOHR_MAGNETON_MEV_T = 0.057883671  # meV/T
G_FACTOR = 2.0023  # Electron spin g-factor


def create_magnetic_field_interaction(
    system_tree: 'qs.quantum_system_tree',
    Bx: float, By: float, Bz: float,
    orbital_red_fact: float,
    f_factor: float,
    delta_f_factor: float
) -> 'MatrixOperator':
    """
    Construct magnetic field interaction Hamiltonian.
    
    Formula:
        H_mag = μ_B [g_L (L_z B_z) + g_s (S · B) + 2δ_f (S_z B_z)]
        
    Where:
        - μ_B = 0.057883671 meV/T (Bohr magneton)
        - g_L = orbital_red_fact (orbital g-factor)
        - g_s = 2.0023 (spin g-factor)
        - B = (Bx, By, Bz) magnetic field vector in Tesla
        - f_factor: f reduction factor
        - delta_f_factor: Delta f factor
    
    Physical interpretation:
        The first term (g_L L_z B_z) is the orbital Zeeman effect.
        The second term (g_s S · B) is the spin Zeeman effect.
        The third term (2δ_f S_z B_z) is the anisotropic spin coupling.
    
    Args:
        system_tree: Quantum system tree
        Bx, By, Bz: Magnetic field components in Tesla
        orbital_red_fact: Orbital reduction factor (g_L)
        f_factor: f reduction factor
        delta_f_factor: Delta f factor
        
    Returns:
        MatrixOperator: Magnetic field Hamiltonian at root node level
        
    Raises:
        ValueError: If required operators are not found
    """
    # Get root node ID dynamically for reusability
    root_node_id = system_tree.root_node.id
    
    # Spin operators at root node level
    Sz = system_tree.create_operator('Sz', root_node_id, 'spin_system')
    Sy = system_tree.create_operator('Sy', root_node_id, 'spin_system')
    Sx = system_tree.create_operator('Sx', root_node_id, 'spin_system')
    
    # Orbital operator at root node level
    Lz = system_tree.create_operator('Lz', root_node_id, 'orbital_system')
    
    # Construct interaction according to formula
    H_spin = BOHR_MAGNETON_MEV_T * G_FACTOR * (Bx*Sx + By*Sy + Bz*Sz)
    H_orbital = BOHR_MAGNETON_MEV_T * f_factor * Bz * Lz
    H_spin_z = 2 * BOHR_MAGNETON_MEV_T * delta_f_factor * Bz * Sz
    
    return H_spin + H_orbital + H_spin_z


def create_electric_field_interaction(
    system_tree: 'qs.quantum_system_tree',
    Ex: float, Ey: float
) -> 'MatrixOperator':
    """
    Construct electric field interaction Hamiltonian.
    
    Formula:
        H_el = E_x Z + E_y X
        
    Where:
        - E_x, E_y: Electric field components
        - X, Z: Orbital position operators
    
    Args:
        system_tree: Quantum system tree
        Ex, Ey: Electric field components
        
    Returns:
        MatrixOperator: Electric field Hamiltonian at root node level
        
    Raises:
        ValueError: If required operators are not found
    """
    # Get root node ID dynamically for reusability
    root_node_id = system_tree.root_node.id
    
    Z = system_tree.create_operator('Z_orb', root_node_id, 'orbital_system')
    X = system_tree.create_operator('X_orb', root_node_id, 'orbital_system')
    return Ex * Z + Ey * X


def create_strain_field_interaction(
    system_tree: 'qs.quantum_system_tree',
    strain_field: 'maths.col_vector'
) -> 'MatrixOperator':
    """
    Construct strain field interaction Hamiltonian.
    
    Formula:
        H_strain = -Y_x L_x + Y_y L_y + Y_z L_z
        
    Where:
        - Y = (Yx, Yy, Yz): Strain field vector
        - L_x, L_y, L_z: Orbital angular momentum operators
    
    Args:
        system_tree: Quantum system tree
        strain_field: Strain field vector (Yx, Yy, Yz)
        
    Returns:
        MatrixOperator: Strain field Hamiltonian at root node level
        
    Raises:
        ValueError: If required operators are not found
    """
    # Get root node ID dynamically for reusability
    root_node_id = system_tree.root_node.id
    
    Lx = system_tree.create_operator('Lx', root_node_id, 'orbital_system')
    Ly = system_tree.create_operator('Ly', root_node_id, 'orbital_system')
    Lz = system_tree.create_operator('Lz', root_node_id, 'orbital_system')
    
    Yx = strain_field[0] if len(strain_field) > 0 else 0.0
    Yy = strain_field[1] if len(strain_field) > 1 else 0.0
    Yz = strain_field[2] if len(strain_field) > 2 else 0.0
    
    return -Yx*Lx + Yy*Ly + Yz*Lz

