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

    def __init__(self, atom_type: AtomType, atom_scale: Optional[int] = None, **kwargs) -> None:
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

        # Instance variables
        self.atom_type = atom_type
        self.mass_number = atom_type.value[1]
        self.atomic_number = atom_type.value[0]
        self.atom_scale = atom_scale

        # Shell offset
        self.shell_offset = 1
        self.shell_stroke_width = 2

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
        num_electrons = self._get_electrons()
        num_neutrons = self._get_neutrons()
        num_protons = self._get_protons()

        # Create and add nucleus
        nucleus = self._create_nucleus()
        self.add(nucleus)

        # Create and add shells
        electrons, shells = self._create_electrons()
        self.add(shells, electrons)

        # Scale the atom to fit the screen
        if self.atom_scale is not None:
            self.scale_to_fit_width(self.atom_scale)

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
        nucleus = Dot(radius=0.2, color=YELLOW, stroke_width=0)

        # Return
        return nucleus

    def _create_electrons(self) -> VGroup:
        """
        Create the shells of the atom.

        Args:
            None

        Returns:
            A VGroup object representing the shells of the atom.

        Raises:
            None
        """
        # Create shells
        shells = VGroup()
        electrons = VGroup()

        # Get electron counts per shell
        num_shells, electron_counts = self._get_electron_counts_per_shell()

        # Create shells
        for i in range(num_shells):
            shell = Circle(
                radius=1 + self.shell_offset * i,
                stroke_width=self.shell_stroke_width,
                stroke_color=DARK_GRAY,
            )
            shells.add(shell)

        # Create electrons
        for idx, electron_count in enumerate(electron_counts):
            for electron_idx in range(electron_count):
                electron = Dot(radius=0.05, color=WHITE, stroke_width=0)
                electron.move_to(shells[idx].point_from_proportion(electron_idx / electron_count))
                electrons.add(electron)

        # Return
        return electrons, shells

    # HELPER METHODS ===================================================================================================

    def _get_electrons(self) -> int:
        """Returns the number of electrons in the atom."""
        return self.atomic_number

    def _get_protons(self) -> int:
        """Returns the number of protons in the atom."""
        return self.atomic_number

    def _get_neutrons(self) -> int:
        """Returns the number of neutrons in the atom."""
        return self.mass_number - self.atomic_number

    def _get_electrons_in_shell(self, n: int) -> int:
        """
        Returns the number of electrons in shell n.

        Args:
            n: The shell number.

        Returns:
            The number of electrons in the shell.

        Raises:
            ValueError: Raises an exception if n is less than 1.
        """
        # Validate n
        if n < 1:
            raise ValueError("Shell number must be greater than 0.")

        # Return
        return 2 * n * n

    def _get_electron_counts_per_shell(self) -> Tuple[int, List[int]]:
        """
        Returns the number of electrons per shell.

        Args:
            None

        Returns:
            Tuple[int, List[int]]: A tuple containing the number of shells and a list of electron counts per shell.

        Raises:
            None
        """
        # Get total electron count
        electrons: int = self._get_electrons()

        # Get electron counts per shell
        electron_counts: List[int] = list()

        # Iterate through each shell
        while electrons > 0:
            if electrons > 0:
                shell_electrons = min(electrons, self._get_electrons_in_shell(len(electron_counts) + 1))
                electron_counts.append(shell_electrons)
                electrons -= shell_electrons
            else:
                break

        # Return
        return (len(electron_counts), electron_counts)

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

    # PUBLIC METHODS ===================================================================================================

    def get_name(self) -> Tex:
        """Return the name of the atom."""
        return Tex(self.atom_type.name)

    def get_atomic_number(self) -> Tex:
        """Return the atomic number of the atom."""
        return Tex(self.atomic_number)

    def get_mass_number(self) -> Tex:
        """Return the mass number of the atom."""
        return Tex(self.mass_number)


# ======================================================================================================================
# BOHR ATOM CLASS END
# ======================================================================================================================
