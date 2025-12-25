class PDBAPIError(Exception):
    """Base class for all PDBAPI exceptions."""
    pass


class PDBAPIInputError(PDBAPIError):
    """Exception raised for invalid input to PDBAPI functions."""
    pass
