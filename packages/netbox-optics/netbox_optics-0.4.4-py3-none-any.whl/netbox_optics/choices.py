class WavelengthStatus:
    """Status of Wavelength in optical connection"""

    FREE = "free"
    RESERVED = "reserved"

    @classmethod
    def choices(cls):
        return [(cls.FREE, "Free"), (cls.RESERVED, "Reserved")]
