"""
Payment Processor Router

Routes payment processing requests to the appropriate processor adapter
based on client configuration and feature flags.

Selection Hierarchy:
1. Form-level override (form_builder_template.payment_processor_override)
2. Client-level selection (customers.payment_processor)
3. Platform default (sys_feature_flags.default_payment_processor)
"""
import os
from typing import Dict, Any, Optional
from .base_adapter import PaymentProcessorAdapter
from .stripe_adapter import StripeAdapter
from .braintree_adapter import BraintreeAdapter


def get_processor_adapter(tx, client_id: str, form_sys_id: Optional[int] = None) -> PaymentProcessorAdapter:
    """
    Get the appropriate payment processor adapter for a client/form.
    
    Selection logic follows hierarchy:
    1. Check form_builder_template.payment_processor_override (if form_sys_id provided)
    2. Check customers.payment_processor
    3. Fall back to sys_feature_flags.default_payment_processor
    
    Args:
        tx: velocity-python transaction object
        client_id: Client identifier
        form_sys_id: Optional form identifier for form-level overrides
    
    Returns:
        Configured PaymentProcessorAdapter instance (StripeAdapter or BraintreeAdapter)
    
    Raises:
        ValueError: If processor type is invalid or not enabled
        ProcessorError: If processor configuration is invalid
    """
    processor_type = _determine_processor_type(tx, client_id, form_sys_id)
    
    # Verify processor is enabled
    if not _is_processor_enabled(tx, processor_type):
        raise ValueError(f"Payment processor '{processor_type}' is not enabled in feature flags")
    
    # Get processor configuration
    config = get_processor_config(processor_type)
    
    # Instantiate appropriate adapter
    if processor_type == 'stripe':
        return StripeAdapter(config)
    elif processor_type == 'braintree':
        return BraintreeAdapter(config)
    else:
        raise ValueError(f"Unsupported payment processor type: {processor_type}")


def _determine_processor_type(tx, client_id: str, form_sys_id: Optional[int] = None) -> str:
    """
    Determine which payment processor to use following configuration hierarchy.
    
    Returns:
        Processor type string ('stripe', 'braintree', etc.)
    """
    # 1. Check form-level override (most specific)
    if form_sys_id:
        form = tx.table('form_builder_template').find(form_sys_id)
        if form and form.get('payment_processor_override'):
            return form['payment_processor_override'].lower()
    
    # 2. Check client-level configuration
    customer = tx.table('customers').find_one({'client_id': client_id})
    if customer and customer.get('payment_processor'):
        return customer['payment_processor'].lower()
    
    # 3. Fall back to platform default
    branch = os.environ.get('USER_BRANCH', 'demo')
    feature_flags = tx.table('sys_feature_flags').find_one({
        'applied_system': branch
    })
    
    if feature_flags and feature_flags.get('default_payment_processor'):
        return feature_flags['default_payment_processor'].lower()
    
    # 4. Ultimate fallback (should never reach here if feature flags are configured)
    return 'braintree'


def _is_processor_enabled(tx, processor_type: str) -> bool:
    """
    Check if a payment processor is enabled in feature flags.
    
    Args:
        tx: velocity-python transaction object
        processor_type: Processor type string ('stripe', 'braintree', etc.)
    
    Returns:
        True if processor is enabled, False otherwise
    """
    branch = os.environ.get('USER_BRANCH', 'demo')
    feature_flags = tx.table('sys_feature_flags').find_one({
        'applied_system': branch
    })
    
    if not feature_flags:
        # No feature flags found - default to braintree only
        return processor_type == 'braintree'
    
    # Check processor-specific flag
    flag_name = f'{processor_type}_enabled'
    return feature_flags.get(flag_name, False)


def get_processor_config(processor_type: str) -> Dict[str, Any]:
    """
    Get configuration dictionary for a payment processor from environment variables.
    
    Args:
        processor_type: Processor type string ('stripe', 'braintree', etc.)
    
    Returns:
        Configuration dictionary with processor-specific keys
    
    Raises:
        ValueError: If required configuration is missing
    """
    if processor_type == 'stripe':
        return _get_stripe_config()
    elif processor_type == 'braintree':
        return _get_braintree_config()
    else:
        raise ValueError(f"Unknown processor type: {processor_type}")


def _get_stripe_config() -> Dict[str, Any]:
    """
    Get Stripe configuration from environment variables.
    
    Expected environment variables:
    - STRIPE_SECRET_KEY or StripeSecretKey
    - STRIPE_PUBLISHABLE_KEY or StripePublishableKey (optional)
    - STRIPE_WEBHOOK_SECRET (optional)
    - STRIPE_ENVIRONMENT or USER_BRANCH (test/live)
    
    Returns:
        Stripe configuration dictionary
    """
    api_key = os.environ.get('STRIPE_SECRET_KEY') or os.environ.get('StripeSecretKey')
    
    if not api_key:
        raise ValueError(
            "Stripe API key not found. Set STRIPE_SECRET_KEY or StripeSecretKey environment variable."
        )
    
    # Determine environment from key prefix or explicit setting
    environment = os.environ.get('STRIPE_ENVIRONMENT')
    if not environment:
        # Infer from key prefix (sk_test_ or sk_live_)
        environment = 'test' if api_key.startswith('sk_test_') else 'live'
    
    return {
        'api_key': api_key,
        'publishable_key': os.environ.get('STRIPE_PUBLISHABLE_KEY') or os.environ.get('StripePublishableKey'),
        'webhook_secret': os.environ.get('STRIPE_WEBHOOK_SECRET'),
        'environment': environment,
    }


def _get_braintree_config() -> Dict[str, Any]:
    """
    Get Braintree configuration from environment variables.
    
    Expected environment variables:
    - BRAINTREE_MERCHANT_ID or BraintreeMerchantId
    - BRAINTREE_PUBLIC_KEY or BraintreePublicKey
    - BRAINTREE_PRIVATE_KEY or BraintreePrivateKey
    - BRAINTREE_ENVIRONMENT (sandbox/production, default: sandbox)
    
    Returns:
        Braintree configuration dictionary
    """
    merchant_id = os.environ.get('BRAINTREE_MERCHANT_ID') or os.environ.get('BraintreeMerchantId')
    public_key = os.environ.get('BRAINTREE_PUBLIC_KEY') or os.environ.get('BraintreePublicKey')
    private_key = os.environ.get('BRAINTREE_PRIVATE_KEY') or os.environ.get('BraintreePrivateKey')
    
    if not all([merchant_id, public_key, private_key]):
        raise ValueError(
            "Braintree configuration incomplete. Required: "
            "BRAINTREE_MERCHANT_ID, BRAINTREE_PUBLIC_KEY, BRAINTREE_PRIVATE_KEY"
        )
    
    environment = os.environ.get('BRAINTREE_ENVIRONMENT', 'sandbox')
    
    return {
        'merchant_id': merchant_id,
        'public_key': public_key,
        'private_key': private_key,
        'environment': environment,
    }


def get_revenue_split_percentage(tx, client_id: str, form_sys_id: Optional[int] = None) -> float:
    """
    Get applicable revenue split percentage following configuration hierarchy.
    
    Hierarchy:
    1. Form-level (form_builder_template.revenue_split_percentage)
    2. Client-level (customers.revenue_split_percentage)
    3. Platform default (sys_feature_flags.default_revenue_split_percentage)
    4. Hardcoded fallback (15.00)
    
    Args:
        tx: velocity-python transaction object
        client_id: Client identifier
        form_sys_id: Optional form identifier
    
    Returns:
        Revenue split percentage as float (e.g., 15.00 for 15%)
    """
    # 1. Try form-level (most specific)
    if form_sys_id:
        form = tx.table('form_builder_template').find(form_sys_id)
        if form and form.get('revenue_split_percentage') is not None:
            return float(form['revenue_split_percentage'])
    
    # 2. Try client-level
    customer = tx.table('customers').find_one({'client_id': client_id})
    if customer and customer.get('revenue_split_percentage') is not None:
        return float(customer['revenue_split_percentage'])
    
    # 3. Platform default from feature flags
    branch = os.environ.get('USER_BRANCH', 'demo')
    feature_flags = tx.table('sys_feature_flags').find_one({
        'applied_system': branch
    })
    
    if feature_flags and feature_flags.get('default_revenue_split_percentage') is not None:
        return float(feature_flags['default_revenue_split_percentage'])
    
    # 4. Hardcoded fallback (should never reach here if setup ran correctly)
    return 15.00


def get_processor_account_id(tx, client_id: str, processor_type: Optional[str] = None) -> Optional[str]:
    """
    Get the processor-specific account ID for a client.
    
    Args:
        tx: velocity-python transaction object
        client_id: Client identifier
        processor_type: Optional processor type (if None, uses routing logic)
    
    Returns:
        Processor account ID string, or None if not configured
    """
    if not processor_type:
        processor_type = _determine_processor_type(tx, client_id)
    
    payment_account = tx.table('client_payment_accounts').find_one({
        'client_id': client_id,
        'processor_type': processor_type
    })
    
    return payment_account['processor_account_id'] if payment_account else None
