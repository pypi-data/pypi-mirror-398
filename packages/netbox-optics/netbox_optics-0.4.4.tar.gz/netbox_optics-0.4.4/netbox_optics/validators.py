from django.core.exceptions import ValidationError


class UniqueWavelengthsValidator:
    """Validator that ensures all wavelengths in the array are unique."""

    def __call__(self, wavelengths):
        if len(wavelengths) != len(set(wavelengths)):
            duplicates = [w for w in wavelengths if wavelengths.count(w) > 1]
            raise ValidationError(
                f"Wavelengths must be unique. Found duplicate values: {', '.join(f'{w:.2f}' for w in set(duplicates))}"
            )
