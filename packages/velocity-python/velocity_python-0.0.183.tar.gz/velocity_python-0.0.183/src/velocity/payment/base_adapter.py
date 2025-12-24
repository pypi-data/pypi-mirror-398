"""
Base Payment Processor Adapter Interface

Defines the standard interface that all payment processor adapters must implement.
This allows the system to work with multiple processors (Stripe, Braintree, etc.) 
through a unified API.

Design Pattern: Adapter Pattern with Strategy Pattern
- Each processor implements this interface
- Business logic remains processor-agnostic
- Routing logic selects appropriate adapter at runtime
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime


class PaymentProcessorAdapter(ABC):
    """
    Abstract base class for payment processor adapters.
    
    All payment processors (Stripe, Braintree, etc.) must implement these methods
    to ensure consistent behavior across the platform.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize adapter with configuration.
        
        Args:
            config: Dictionary containing processor-specific configuration
                    (API keys, environment settings, etc.)
        """
        self.config = config
        self.processor_name = self.__class__.__name__.replace('Adapter', '').lower()
    
    # ========================================================================
    # ACCOUNT MANAGEMENT
    # ========================================================================
    
    @abstractmethod
    def create_account(self, tx, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a connected/sub-merchant account for a client.
        
        Args:
            tx: velocity-python transaction object
            client_data: Dictionary containing client information:
                - client_id: Internal client identifier
                - business_name: Legal business name
                - email: Contact email
                - phone: Contact phone (optional)
                - tax_id: Tax ID/EIN (optional)
                - address: Business address dict (optional)
        
        Returns:
            Dictionary containing:
                - processor_account_id: External account identifier
                - status: Account status (pending/active/restricted)
                - requires_onboarding: Boolean indicating if further setup needed
                - onboarding_url: URL for hosted onboarding (if applicable)
                - metadata: Additional processor-specific data
        
        Raises:
            ProcessorError: If account creation fails
        """
        pass
    
    @abstractmethod
    def get_account_status(self, tx, processor_account_id: str) -> Dict[str, Any]:
        """
        Retrieve current status of a connected account.
        
        Args:
            tx: velocity-python transaction object
            processor_account_id: External account identifier
        
        Returns:
            Dictionary containing:
                - account_id: Processor account identifier
                - status: Current status (active/pending/restricted/disabled)
                - charges_enabled: Boolean - can accept payments
                - payouts_enabled: Boolean - can receive payouts
                - requirements_due: List of outstanding requirements
                - verification_status: Identity verification status
                - metadata: Additional status information
        
        Raises:
            ProcessorError: If status check fails
        """
        pass
    
    @abstractmethod
    def create_onboarding_link(self, tx, processor_account_id: str, 
                              return_url: str, refresh_url: str) -> str:
        """
        Generate URL for hosted onboarding flow (if supported by processor).
        
        Args:
            tx: velocity-python transaction object
            processor_account_id: External account identifier
            return_url: URL to redirect after successful completion
            refresh_url: URL to redirect if session expires
        
        Returns:
            Onboarding URL string (or None if processor doesn't support hosted onboarding)
        
        Raises:
            ProcessorError: If link generation fails
        """
        pass
    
    # ========================================================================
    # PAYMENT AUTHORIZATION (PRE-AUTH)
    # ========================================================================
    
    @abstractmethod
    def authorize_payment(self, tx, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pre-authorize a payment without capturing funds.
        
        This is Phase 1 of the two-phase payment flow. Funds are held but not
        transferred until capture_payment() is called.
        
        Args:
            tx: velocity-python transaction object
            payment_data: Dictionary containing:
                - amount: Amount in cents (integer)
                - currency: ISO currency code (default: 'usd')
                - payment_method: Payment method token/ID
                - client_id: Internal client identifier
                - processor_account_id: External account identifier
                - revenue_split_percentage: Platform fee percentage (e.g., 15.00)
                - metadata: Additional transaction metadata
                - donor_email: Donor email address
                - donor_name: Donor full name
                - form_sys_id: Related form identifier (optional)
        
        Returns:
            Dictionary containing:
                - processor_transaction_id: External transaction identifier
                - status: Authorization status (authorized/failed)
                - amount: Authorized amount in cents
                - currency: Transaction currency
                - authorization_code: Processor authorization code (if applicable)
                - expires_at: When authorization expires (datetime)
                - error_message: Error details if failed (optional)
                - metadata: Additional processor-specific data
        
        Raises:
            ProcessorError: If authorization fails
        """
        pass
    
    # ========================================================================
    # PAYMENT CAPTURE
    # ========================================================================
    
    @abstractmethod
    def capture_payment(self, tx, processor_transaction_id: str, 
                       amount: Optional[int] = None) -> Dict[str, Any]:
        """
        Capture a previously authorized payment (Phase 2).
        
        Args:
            tx: velocity-python transaction object
            processor_transaction_id: External transaction identifier from authorize_payment()
            amount: Amount to capture in cents (None = capture full authorized amount)
        
        Returns:
            Dictionary containing:
                - processor_transaction_id: External transaction identifier
                - processor_charge_id: Final charge identifier (may differ from transaction_id)
                - status: Capture status (captured/failed)
                - amount_captured: Actual amount captured in cents
                - platform_fee: Platform fee amount in cents
                - client_amount: Amount transferred to client in cents
                - captured_at: Capture timestamp (datetime)
                - error_message: Error details if failed (optional)
                - metadata: Additional processor-specific data
        
        Raises:
            ProcessorError: If capture fails
        """
        pass
    
    @abstractmethod
    def cancel_payment(self, tx, processor_transaction_id: str, 
                      reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Cancel a previously authorized payment before capture.
        
        Args:
            tx: velocity-python transaction object
            processor_transaction_id: External transaction identifier from authorize_payment()
            reason: Optional cancellation reason
        
        Returns:
            Dictionary containing:
                - processor_transaction_id: External transaction identifier
                - status: Cancellation status (cancelled/failed)
                - cancelled_at: Cancellation timestamp (datetime)
                - reason: Cancellation reason
                - error_message: Error details if failed (optional)
        
        Raises:
            ProcessorError: If cancellation fails
        """
        pass
    
    # ========================================================================
    # REFUNDS
    # ========================================================================
    
    @abstractmethod
    def refund_payment(self, tx, processor_charge_id: str, 
                      amount: Optional[int] = None, 
                      reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Refund a captured payment (full or partial).
        
        Args:
            tx: velocity-python transaction object
            processor_charge_id: External charge identifier from capture_payment()
            amount: Amount to refund in cents (None = full refund)
            reason: Optional refund reason
        
        Returns:
            Dictionary containing:
                - refund_id: External refund identifier
                - status: Refund status (succeeded/pending/failed)
                - amount_refunded: Actual amount refunded in cents
                - platform_fee_refunded: Platform fee refunded in cents
                - refunded_at: Refund timestamp (datetime)
                - reason: Refund reason
                - error_message: Error details if failed (optional)
        
        Raises:
            ProcessorError: If refund fails
        """
        pass
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    @abstractmethod
    def validate_configuration(self) -> bool:
        """
        Validate that adapter configuration is complete and correct.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        pass
    
    def get_processor_name(self) -> str:
        """
        Get the name of this processor (stripe, braintree, etc.).
        
        Returns:
            Lowercase processor name string
        """
        return self.processor_name
    
    def calculate_platform_fee(self, amount_cents: int, 
                               revenue_split_percentage: float) -> int:
        """
        Calculate platform fee from total amount.
        
        Args:
            amount_cents: Total transaction amount in cents
            revenue_split_percentage: Platform fee percentage (e.g., 15.00 for 15%)
        
        Returns:
            Platform fee amount in cents (integer)
        """
        return int(amount_cents * (revenue_split_percentage / 100))
    
    def calculate_client_amount(self, amount_cents: int, 
                               revenue_split_percentage: float) -> int:
        """
        Calculate amount that goes to client after platform fee.
        
        Args:
            amount_cents: Total transaction amount in cents
            revenue_split_percentage: Platform fee percentage (e.g., 15.00 for 15%)
        
        Returns:
            Client amount in cents (integer)
        """
        platform_fee = self.calculate_platform_fee(amount_cents, revenue_split_percentage)
        return amount_cents - platform_fee


class ProcessorError(Exception):
    """
    Base exception for payment processor errors.
    
    Attributes:
        processor: Name of the processor that raised the error
        error_code: Processor-specific error code
        error_message: Human-readable error message
        metadata: Additional error context
    """
    
    def __init__(self, processor: str, error_code: str, 
                 error_message: str, metadata: Optional[Dict[str, Any]] = None):
        self.processor = processor
        self.error_code = error_code
        self.error_message = error_message
        self.metadata = metadata or {}
        super().__init__(f"[{processor}] {error_code}: {error_message}")
