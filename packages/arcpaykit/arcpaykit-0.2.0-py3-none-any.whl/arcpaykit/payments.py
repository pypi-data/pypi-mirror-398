"""Payment operations for ArcPayKit."""

from typing import Dict, Any, Optional, Literal
from .client import ArcPayClient


class Payments:
    """Payment operations."""
    
    def __init__(self, client: ArcPayClient):
        """
        Initialize Payments client.
        
        Args:
            client: ArcPayClient instance
        """
        self.client = client
    
    def create(
        self,
        amount: str,
        currency: Optional[str] = None,
        description: Optional[str] = None,
        customer_email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new payment (happy path - recommended for most users).
        
        This method only requires essential fields. All advanced fields are inferred:
        - merchant_wallet: Uses merchant's default wallet from profile
        - is_test: Inferred from API key prefix (sk_arc_test_ / sk_arc_live_)
        - payment_asset: Defaults to ARC USDC
        - settlement_currency: Defaults to USDC
        - payment_chain_id: Inferred automatically
        
        Args:
            amount: Payment amount (as string, e.g., "100.00")
            currency: Payment currency (optional, defaults to "USDC")
            description: Payment description (optional)
            customer_email: Customer email address (optional)
            
        Returns:
            Payment creation response with checkout_url
            
        Example:
            >>> payment = arcpay.payments.create(
            ...     amount="100.00",
            ...     currency="USDC",
            ...     description="Payment for order #123",
            ...     customer_email="customer@example.com"
            ... )
        """
        data: Dict[str, Any] = {
            "amount": amount,
        }
        
        if currency is not None:
            data["currency"] = currency
        if description is not None:
            data["description"] = description
        if customer_email is not None:
            data["customerEmail"] = customer_email
        
        # All other fields are inferred server-side
        return self.client.request("/api/payments/create", method="POST", data=data)
    
    def create_advanced(
        self,
        amount: str,
        merchant_wallet: Optional[str] = None,
        currency: Optional[str] = None,
        settlement_currency: Optional[Literal["USDC", "EURC"]] = None,
        payment_asset: Optional[str] = None,
        payment_chain_id: Optional[int] = None,
        conversion_path: Optional[str] = None,
        estimated_fees: Optional[str] = None,
        description: Optional[str] = None,
        customer_email: Optional[str] = None,
        expires_in_minutes: Optional[int] = None,
        is_test: Optional[bool] = None,
        gas_sponsored: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Create a new payment with full control (advanced users only).
        
        Most users should use payments.create() instead.
        This method allows full control over all payment parameters.
        
        Args:
            amount: Payment amount (as string, e.g., "100.00")
            merchant_wallet: Merchant wallet address (optional, uses default if not provided)
            currency: Payment currency (default: "USDC")
            settlement_currency: Settlement currency ("USDC" or "EURC")
            payment_asset: Specific asset identifier
            payment_chain_id: Chain ID for payment
            conversion_path: Conversion path JSON string
            estimated_fees: Estimated fees
            description: Payment description
            customer_email: Customer email address
            expires_in_minutes: Expiration time in minutes
            is_test: Test mode flag
            gas_sponsored: Gas sponsorship preference
            
        Returns:
            Payment creation response with checkout_url
        """
        data: Dict[str, Any] = {
            "amount": amount,
        }
        
        if merchant_wallet is not None:
            data["merchantWallet"] = merchant_wallet
        if currency is not None:
            data["currency"] = currency
        if settlement_currency is not None:
            data["settlementCurrency"] = settlement_currency
        if payment_asset is not None:
            data["paymentAsset"] = payment_asset
        if payment_chain_id is not None:
            data["paymentChainId"] = payment_chain_id
        if conversion_path is not None:
            data["conversionPath"] = conversion_path
        if estimated_fees is not None:
            data["estimatedFees"] = estimated_fees
        if description is not None:
            data["description"] = description
        if customer_email is not None:
            data["customerEmail"] = customer_email
        if expires_in_minutes is not None:
            data["expiresInMinutes"] = expires_in_minutes
        if is_test is not None:
            data["isTest"] = is_test
        if gas_sponsored is not None:
            data["gasSponsored"] = gas_sponsored
        
        return self.client.request("/api/payments/create", method="POST", data=data)
    
    def retrieve(self, payment_id: str) -> Dict[str, Any]:
        """
        Retrieve a payment by ID.
        
        Args:
            payment_id: Payment ID (e.g., "pay_...")
            
        Returns:
            Payment details
        """
        return self.client.request(f"/api/payments/{payment_id}")
    
    def submit_tx(
        self,
        payment_id: str,
        tx_hash: str,
        payer_wallet: str,
        customer_email: Optional[str] = None,
        customer_name: Optional[str] = None,
        gas_sponsored: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Submit a transaction hash for a payment.
        
        Args:
            payment_id: Payment ID
            tx_hash: Transaction hash
            payer_wallet: Payer wallet address
            customer_email: Customer email (optional)
            customer_name: Customer name (optional)
            gas_sponsored: Gas sponsorship preference (optional)
            
        Returns:
            Confirmation response
        """
        data: Dict[str, Any] = {
            "paymentId": payment_id,
            "txHash": tx_hash,
            "payerWallet": payer_wallet,
        }
        
        if customer_email is not None:
            data["customerEmail"] = customer_email
        if customer_name is not None:
            data["customerName"] = customer_name
        if gas_sponsored is not None:
            data["gasSponsored"] = gas_sponsored
        
        return self.client.request("/api/payments/submit-tx", method="POST", data=data)
    
    def confirm(
        self,
        payment_id: str,
        tx_hash: str,
        payer_wallet: str,
        customer_email: Optional[str] = None,
        customer_name: Optional[str] = None,
        gas_sponsored: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Confirm a payment (legacy endpoint).
        
        Args:
            payment_id: Payment ID
            tx_hash: Transaction hash
            payer_wallet: Payer wallet address
            customer_email: Customer email (optional)
            customer_name: Customer name (optional)
            gas_sponsored: Gas sponsorship preference (optional)
            
        Returns:
            Confirmation response
        """
        data: Dict[str, Any] = {
            "paymentId": payment_id,
            "txHash": tx_hash,
            "payerWallet": payer_wallet,
        }
        
        if customer_email is not None:
            data["customerEmail"] = customer_email
        if customer_name is not None:
            data["customerName"] = customer_name
        if gas_sponsored is not None:
            data["gasSponsored"] = gas_sponsored
        
        return self.client.request("/api/payments/confirm", method="POST", data=data)
    
    def fail(self, payment_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Mark a payment as failed.
        
        Args:
            payment_id: Payment ID
            reason: Optional failure reason
            
        Returns:
            Failure response
        """
        data: Dict[str, Any] = {"paymentId": payment_id}
        if reason is not None:
            data["reason"] = reason
        
        return self.client.request("/api/payments/fail", method="POST", data=data)
    
    def expire(self, payment_id: str) -> Dict[str, Any]:
        """
        Expire a payment.
        
        Args:
            payment_id: Payment ID
            
        Returns:
            Expiration response
        """
        data = {"paymentId": payment_id}
        return self.client.request("/api/payments/expire", method="POST", data=data)

