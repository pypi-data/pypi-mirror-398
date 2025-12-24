"""
Velocity Payment Processing Module

Provides processor-agnostic payment processing with pluggable adapters for
different payment gateways (Stripe, Braintree, etc.).

This module is designed to be used across multiple projects that need payment
processing capabilities, maintaining consistency and reducing code duplication.

Usage:
    from velocity.payment import get_processor_adapter
    
    @engine.transaction
    def process_payment(tx, client_id, payment_data):
        adapter = get_processor_adapter(tx, client_id)
        result = adapter.authorize_payment(tx, payment_data)
        return result

Available Adapters:
    - StripeAdapter: Stripe Connect with Express accounts
    - BraintreeAdapter: Braintree sub-merchant accounts

Configuration:
    Adapters are configured via environment variables. See router.py for details.
"""

from .base_adapter import PaymentProcessorAdapter, ProcessorError
from .stripe_adapter import StripeAdapter
from .braintree_adapter import BraintreeAdapter
from .router import (
    get_processor_adapter,
    get_processor_config,
    get_revenue_split_percentage,
    get_processor_account_id,
)

__all__ = [
    # Base classes
    'PaymentProcessorAdapter',
    'ProcessorError',
    
    # Adapters
    'StripeAdapter',
    'BraintreeAdapter',
    
    # Router functions
    'get_processor_adapter',
    'get_processor_config',
    'get_revenue_split_percentage',
    'get_processor_account_id',
]

__version__ = '1.0.0'
