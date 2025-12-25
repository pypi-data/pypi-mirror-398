class PLINK2Error(Exception):
    """Raised when PLINK2 execution fails."""
    pass


class PhenotypeMeasureError(Exception):
    """Raised when phenotype measure extraction or processing fails."""
    pass