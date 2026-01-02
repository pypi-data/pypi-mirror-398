# ======================================================================================================================
# IMPORTS
# ======================================================================================================================

# STANDARD IMPORTS =====================================================================================================

from typing import *

# THIRD PARTY IMPORTS ==================================================================================================

from manim import *

# MANIMERA IMPORTS =====================================================================================================

from manimera.constants.science import AtomType

# ======================================================================================================================
# BOHR ATOM CLASS
# ======================================================================================================================


class BohrAtom(VGroup):
    """
    Bohr's model of the atom.
    """

    # CLASS VARIABLES ==================================================================================================

    # Electron counts per shell (2*n^2)
    ELECTRONS_PER_SHELL: List[int] = [
        2,  # Shell 1
        8,  # Shell 2
        18,  # Shell 3
        32,  # Shell 4
        50,  # Shell 5
        72,  # Shell 6
        98,  # Shell 7
    ]

    # INITIALIZATION ===================================================================================================

    def __init__(self, atom_type: AtomType, atom_scale: int = 3, **kwargs) -> None:
        """
        Initialize the Bohr atom.

        Args:
            atom_type: The atom type.
            atom_scale: The scale of the atom.

        Returns:
            None

        Raises:
            None
        """
        super().__init__(**kwargs)

        #
        self.atom_type = atom_type
        self.mass_number = atom_type.value[1]
        self.atomic_number = atom_type.value[0]
        self.atom_scale = atom_scale

        # Create Bohr Atom
        self._create_bohr_atom()

        # Return
        return

    # CREATE METHOD ====================================================================================================

    def _create_bohr_atom(self) -> None:
        """
        Create the Bohr atom.

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        # Get subatomic particle counts
        num_protons, num_electrons, num_neutrons = self._get_subatomic_particle_counts()

        # Create nucleus
        nucleus = self._create_nucleus()

        # Add nucleus to the atom
        self.add(nucleus)

        # Scale the atom to fit the screen
        # self.scale_to_fit_width(self.atom_scale)

        # Return
        return

    # INTERNAL METHODS =================================================================================================

    def _create_nucleus(self) -> Dot:
        """
        Create the nucleus of the atom.

        Args:
            None

        Returns:
            A Dot object representing the nucleus of the atom.

        Raises:
            None
        """
        # Create nucleus
        nucleus = Dot(radius=0.2, color=YELLOW)

        # Return
        return nucleus

    # HELPER METHODS ===================================================================================================

    def _get_subatomic_particle_counts(self) -> Tuple[int, int, int]:
        """
        Calculates the count of sub-atomic particles.

        Args:
            None

        Returns:
            A tuple containing the number of protons, electrons, and neutrons.

        Raises:
            None
        """

        # Calculate subatomic particle counts
        num_protons = self.atomic_number
        num_electrons = self.atomic_number
        num_neutrons = self.mass_number - self.atomic_number

        # Return (protons, electrons, neutrons)
        return (num_protons, num_electrons, num_neutrons)

    # REPRESENTATION ===================================================================================================

    def __str__(self) -> str:
        """Return a string representation of the atom."""
        return f"BohrAtom({self.atom_type.name}, Z={self.atomic_number}, A={self.mass_number})"

    def __repr__(self) -> str:
        """Return a string representation of the atom."""
        return f"BohrAtom({self.atom_type.name}, Z={self.atomic_number}, A={self.mass_number})"

    # COMPARISON =======================================================================================================

    def __eq__(self, other) -> bool:
        """Return True if the atoms are equal."""
        if not isinstance(other, BohrAtom):
            return NotImplemented
        return self.atom_type == other.atom_type

    def __ne__(self, other) -> bool:
        """Return True if the atoms are not equal."""
        if not isinstance(other, BohrAtom):
            return NotImplemented
        return not self == other

    def __lt__(self, other) -> bool:
        """Return True if the atom has a lower atomic number."""
        if not isinstance(other, BohrAtom):
            return NotImplemented
        return self.atomic_number < other.atomic_number

    def __le__(self, other) -> bool:
        """Return True if the atom has a lower or equal atomic number."""
        if not isinstance(other, BohrAtom):
            return NotImplemented
        return self.atomic_number <= other.atomic_number

    def __gt__(self, other) -> bool:
        """Return True if the atom has a higher atomic number."""
        if not isinstance(other, BohrAtom):
            return NotImplemented
        return self.atomic_number > other.atomic_number

    def __ge__(self, other) -> bool:
        """Return True if the atom has a higher or equal atomic number."""
        if not isinstance(other, BohrAtom):
            return NotImplemented
        return self.atomic_number >= other.atomic_number

    # HASH =============================================================================================================

    def __hash__(self) -> int:
        """Return a hash of the atom."""
        return hash((self.atom_type, self.atomic_number, self.mass_number))


# ======================================================================================================================
# BOHR ATOM CLASS END
# ======================================================================================================================
