"""Complex module."""


class Complex:
    @staticmethod
    def has_complex() -> bool:
        """Überprüft, ob complexPyTorch installiert ist.

        Returns:
            bool: True, wenn complexPyTorch installiert ist, sonst False.
        """
        try:
            import complexPyTorch

            return True
        except ImportError:
            return False
