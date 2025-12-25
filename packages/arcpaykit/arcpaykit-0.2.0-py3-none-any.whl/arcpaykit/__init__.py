"""
ArcPayKit Python SDK

Official ArcPay Python SDK for accepting stablecoin payments.
"""

from .client import ArcPayClient, ArcPayError
from .payments import Payments

__version__ = "0.1.0"


class ArcPay:
    """Main SDK class for ArcPayKit."""
    
    def __init__(self, api_key: str, base_url: str = "https://pay.arcpaykit.com"):
        """
        Initialize the ArcPay client.
        
        Args:
            api_key: Your ArcPay API key
            base_url: Optional base URL (defaults to https://pay.arcpaykit.com)
        """
        client = ArcPayClient(api_key, base_url)
        self.payments = Payments(client)


# Export main classes
__all__ = ["ArcPay", "ArcPayClient", "ArcPayError", "Payments"]

