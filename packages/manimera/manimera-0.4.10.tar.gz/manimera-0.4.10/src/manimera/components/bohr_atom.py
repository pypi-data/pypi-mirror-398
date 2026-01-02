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
        self._atom_type = atom_type
        self._mass_number = atom_type.value[1]
        self._atomic_number = atom_type.value[0]
        self._atom_scale = atom_scale

        # Shell offset
        self._shell_offset = 1
        self._shell_stroke_width = 2

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
        # Create and add nucleus
        self._nucleus = self._create_nucleus()
        self.add(self._nucleus)

        # Create and add shells and electrons
        self._electrons, self._shells = self._create_electrons()
        self.add(self._shells, self._electrons)

        # Scale the atom to fit the screen
        if self._atom_scale is not None:
            self.scale_to_fit_width(self._atom_scale)

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
                radius=1 + self._shell_offset * i,
                stroke_width=self._shell_stroke_width,
                stroke_color=DARK_GRAY,
            )
            shells.add(shell)

        # Create electrons
        for idx, electron_count in enumerate(electron_counts):
            # Create electron shell
            electron_shell = VGroup()

            # Create electrons
            for electron_idx in range(electron_count):
                electron = Dot(radius=0.05, color=WHITE, stroke_width=0)
                electron.move_to(shells[idx].point_from_proportion(electron_idx / electron_count))
                electron_shell.add(electron)

            # Add electron shell to electrons
            electrons.add(electron_shell)

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

    # PROPERTIES =======================================================================================================

    @property
    def nucleus(self) -> Dot:
        """Return the nucleus of the atom."""
        return self._nucleus

    @property
    def electrons(self) -> VGroup:
        """Return the electrons of the atom."""
        return self._electrons

    @property
    def shells(self) -> VGroup:
        """Return the shells of the atom."""
        return self._shells

    @property
    def atom_scale(self) -> int:
        """Return the scale of the atom."""
        return self._atom_scale

    @property
    def shell_offset(self) -> int:
        """Return the offset of the shells."""
        return self._shell_offset

    @property
    def shell_stroke_width(self) -> int:
        """Return the stroke width of the shells."""
        return self._shell_stroke_width

    @property
    def atomic_number(self) -> int:
        """Return the atomic number of the atom."""
        return self._atomic_number

    @property
    def mass_number(self) -> int:
        """Return the mass number of the atom."""
        return self._mass_number

    @property
    def atom_type(self) -> AtomType:
        """Return the atom type."""
        return self._atom_type


# ======================================================================================================================
# BOHR ATOM CLASS END
# ======================================================================================================================
