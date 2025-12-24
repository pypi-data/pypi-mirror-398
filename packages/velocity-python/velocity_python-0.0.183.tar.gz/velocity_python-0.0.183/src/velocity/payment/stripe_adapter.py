"""
Stripe Connect Payment Processor Adapter

Implements the PaymentProcessorAdapter interface for Stripe Connect with Express accounts.

Key Features:
- Express Connected Accounts for client schools
- Destination charges with application_fee_amount for revenue splits
- Two-phase authorization (manual capture)
- Stripe-managed pricing (zero platform fees)
- AccountLinks for hosted onboarding
"""
import os
import stripe
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from .base_adapter import PaymentProcessorAdapter, ProcessorError


class StripeAdapter(PaymentProcessorAdapter):
    """
    Stripe Connect adapter for payment processing.
    
    Uses Express accounts with destination charges to handle revenue splits.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Stripe adapter with API credentials.
        
        Args:
            config: Dictionary containing:
                - api_key: Stripe secret key (required)
                - publishable_key: Stripe publishable key (optional, for client-side)
                - webhook_secret: Webhook signing secret (optional)
                - environment: 'test' or 'live' (default: 'test')
        """
        super().__init__(config)
        
        # Set Stripe API key
        stripe.api_key = config.get('api_key')
        if not stripe.api_key:
            raise ValueError("Stripe API key is required in config")
        
        self.publishable_key = config.get('publishable_key')
        self.webhook_secret = config.get('webhook_secret')
        self.environment = config.get('environment', 'test')
    
    # ========================================================================
    # ACCOUNT MANAGEMENT
    # ========================================================================
    
    def create_account(self, tx, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a Stripe Express Connected Account for a client school.
        
        Express accounts provide:
        - Simplified onboarding via Stripe-hosted flow
        - Lighter dashboard for schools
        - Platform handles disputes
        """
        try:
            # Extract client data
            client_id = client_data['client_id']
            business_name = client_data.get('business_name', client_data.get('school_name'))
            email = client_data['email']
            
            # Create Express account
            account = stripe.Account.create(
                type='express',  # Express account type
                country='US',
                email=email,
                capabilities={
                    'card_payments': {'requested': True},
                    'transfers': {'requested': True},
                },
                business_type='company',
                company={
                    'name': business_name,
                },
                business_profile={
                    'mcc': '8299',  # Schools and Educational Services
                    'url': client_data.get('website_url'),
                },
                metadata={
                    'client_id': str(client_id),
                    'platform': 'caringcent',
                    'environment': self.environment
                }
            )
            
            # Store in client_payment_accounts table
            payment_account = tx.table('client_payment_accounts').new()
            payment_account['client_id'] = client_id
            payment_account['processor_type'] = 'stripe'
            payment_account['processor_account_id'] = account.id
            payment_account['account_status'] = 'pending'
            payment_account['charges_enabled'] = account.charges_enabled
            payment_account['payouts_enabled'] = account.payouts_enabled
            payment_account['details_submitted'] = account.details_submitted
            payment_account['requirements_data'] = {
                'currently_due': account.requirements.currently_due or [],
                'eventually_due': account.requirements.eventually_due or [],
                'past_due': account.requirements.past_due or [],
                'disabled_reason': account.requirements.disabled_reason,
            }
            payment_account['capabilities'] = {
                'card_payments': account.capabilities.card_payments,
                'transfers': account.capabilities.transfers,
            }
            
            # Create initial onboarding checklist
            checklist = tx.table('client_onboarding_checklists').new()
            checklist['client_id'] = client_id
            checklist['processor_type'] = 'stripe'
            checklist['processor_account_id'] = account.id
            checklist['checklist_state'] = self._generate_initial_checklist()
            checklist['current_step'] = 0
            checklist['completed'] = False
            
            # Mark first step as complete (account created)
            state = checklist['checklist_state']
            state['items']['stripe_account_created']['completed'] = True
            state['items']['stripe_account_created']['completed_at'] = datetime.now(timezone.utc).isoformat()
            checklist['checklist_state'] = state
            
            return {
                'processor_account_id': account.id,
                'status': 'pending',
                'requires_onboarding': True,
                'onboarding_url': None,  # Generated separately via create_onboarding_link
                'charges_enabled': account.charges_enabled,
                'payouts_enabled': account.payouts_enabled,
                'metadata': {
                    'account_type': 'express',
                    'capabilities': account.capabilities,
                    'requirements': account.requirements,
                }
            }
            
        except stripe.error.StripeError as e:
            raise ProcessorError(
                processor='stripe',
                error_code=e.code or 'unknown',
                error_message=str(e),
                metadata={'client_id': client_data.get('client_id')}
            )
    
    def get_account_status(self, tx, processor_account_id: str) -> Dict[str, Any]:
        """
        Retrieve current status of a Stripe Connected Account.
        """
        try:
            account = stripe.Account.retrieve(processor_account_id)
            
            # Update database record
            payment_account = tx.table('client_payment_accounts').find_one({
                'processor_account_id': processor_account_id,
                'processor_type': 'stripe'
            })
            
            if payment_account:
                payment_account['account_status'] = self._determine_account_status(account)
                payment_account['charges_enabled'] = account.charges_enabled
                payment_account['payouts_enabled'] = account.payouts_enabled
                payment_account['details_submitted'] = account.details_submitted
                payment_account['requirements_data'] = {
                    'currently_due': account.requirements.currently_due or [],
                    'eventually_due': account.requirements.eventually_due or [],
                    'past_due': account.requirements.past_due or [],
                    'disabled_reason': account.requirements.disabled_reason,
                    'current_deadline': account.requirements.current_deadline,
                }
                payment_account['updated_at'] = datetime.now(timezone.utc)
            
            return {
                'account_id': account.id,
                'status': self._determine_account_status(account),
                'charges_enabled': account.charges_enabled,
                'payouts_enabled': account.payouts_enabled,
                'requirements_due': account.requirements.currently_due or [],
                'requirements_past_due': account.requirements.past_due or [],
                'requirements_deadline': account.requirements.current_deadline,
                'verification_status': self._get_verification_status(account),
                'metadata': {
                    'details_submitted': account.details_submitted,
                    'disabled_reason': account.requirements.disabled_reason,
                    'capabilities': account.capabilities,
                }
            }
            
        except stripe.error.StripeError as e:
            raise ProcessorError(
                processor='stripe',
                error_code=e.code or 'unknown',
                error_message=str(e),
                metadata={'account_id': processor_account_id}
            )
    
    def create_onboarding_link(self, tx, processor_account_id: str, 
                              return_url: str, refresh_url: str) -> str:
        """
        Generate Stripe AccountLink for hosted Express onboarding flow.
        
        The generated URL redirects the user to Stripe's hosted onboarding,
        which collects all required business and identity information.
        """
        try:
            account_link = stripe.AccountLink.create(
                account=processor_account_id,
                refresh_url=refresh_url,
                return_url=return_url,
                type='account_onboarding',
            )
            
            return account_link.url
            
        except stripe.error.StripeError as e:
            raise ProcessorError(
                processor='stripe',
                error_code=e.code or 'unknown',
                error_message=str(e),
                metadata={'account_id': processor_account_id}
            )
    
    # ========================================================================
    # PAYMENT AUTHORIZATION (PRE-AUTH)
    # ========================================================================
    
    def authorize_payment(self, tx, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pre-authorize a payment using Stripe PaymentIntent with manual capture.
        
        Uses destination charges with application_fee_amount for revenue split.
        """
        try:
            # Extract payment data
            amount_cents = payment_data['amount']
            currency = payment_data.get('currency', 'usd')
            payment_method = payment_data['payment_method']
            processor_account_id = payment_data['processor_account_id']
            revenue_split_percentage = payment_data['revenue_split_percentage']
            
            # Calculate platform fee
            platform_fee_cents = self.calculate_platform_fee(
                amount_cents, 
                revenue_split_percentage
            )
            
            # Create PaymentIntent with manual capture (pre-auth)
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                payment_method=payment_method,
                payment_method_types=['card'],
                capture_method='manual',  # KEY: Don't capture immediately
                confirm=True,  # Confirm immediately (authorize)
                application_fee_amount=platform_fee_cents,  # Platform fee
                transfer_data={
                    'destination': processor_account_id,  # Client's account
                },
                metadata={
                    'client_id': str(payment_data.get('client_id')),
                    'form_sys_id': str(payment_data.get('form_sys_id', '')),
                    'donor_email': payment_data.get('donor_email'),
                    'donor_name': payment_data.get('donor_name'),
                    'platform': 'caringcent',
                    'environment': self.environment,
                }
            )
            
            # Calculate expiration (Stripe holds for 7 days)
            expires_at = datetime.now(timezone.utc) + timedelta(days=7)
            
            return {
                'processor_transaction_id': payment_intent.id,
                'status': 'authorized' if payment_intent.status == 'requires_capture' else 'failed',
                'amount': payment_intent.amount,
                'currency': payment_intent.currency,
                'authorization_code': payment_intent.id,  # Stripe uses PaymentIntent ID
                'expires_at': expires_at,
                'error_message': None,
                'metadata': {
                    'payment_intent': payment_intent,
                    'platform_fee': platform_fee_cents,
                    'client_amount': amount_cents - platform_fee_cents,
                }
            }
            
        except stripe.error.StripeError as e:
            return {
                'processor_transaction_id': None,
                'status': 'failed',
                'amount': payment_data.get('amount'),
                'currency': payment_data.get('currency', 'usd'),
                'authorization_code': None,
                'expires_at': None,
                'error_message': str(e),
                'metadata': {
                    'error_code': e.code,
                    'error_type': type(e).__name__,
                }
            }
    
    # ========================================================================
    # PAYMENT CAPTURE
    # ========================================================================
    
    def capture_payment(self, tx, processor_transaction_id: str, 
                       amount: Optional[int] = None) -> Dict[str, Any]:
        """
        Capture a previously authorized PaymentIntent.
        
        This finalizes the payment and transfers funds according to the
        destination charge configuration (with application fee).
        """
        try:
            # Capture the PaymentIntent
            if amount:
                payment_intent = stripe.PaymentIntent.capture(
                    processor_transaction_id,
                    amount_to_capture=amount
                )
            else:
                payment_intent = stripe.PaymentIntent.capture(
                    processor_transaction_id
                )
            
            # Get charge details (for charge ID)
            charge = payment_intent.charges.data[0] if payment_intent.charges.data else None
            charge_id = charge.id if charge else None
            
            # Calculate amounts
            amount_captured = payment_intent.amount_captured
            platform_fee = payment_intent.application_fee_amount or 0
            client_amount = amount_captured - platform_fee
            
            return {
                'processor_transaction_id': payment_intent.id,
                'processor_charge_id': charge_id,
                'status': 'captured' if payment_intent.status == 'succeeded' else 'failed',
                'amount_captured': amount_captured,
                'platform_fee': platform_fee,
                'client_amount': client_amount,
                'captured_at': datetime.now(timezone.utc),
                'error_message': None,
                'metadata': {
                    'payment_intent': payment_intent,
                    'charge': charge,
                }
            }
            
        except stripe.error.StripeError as e:
            raise ProcessorError(
                processor='stripe',
                error_code=e.code or 'unknown',
                error_message=str(e),
                metadata={'payment_intent_id': processor_transaction_id}
            )
    
    def cancel_payment(self, tx, processor_transaction_id: str, 
                      reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Cancel a previously authorized PaymentIntent before capture.
        
        This releases the hold on the donor's card without charging them.
        """
        try:
            payment_intent = stripe.PaymentIntent.cancel(
                processor_transaction_id,
                cancellation_reason=reason
            )
            
            return {
                'processor_transaction_id': payment_intent.id,
                'status': 'cancelled' if payment_intent.status == 'canceled' else 'failed',
                'cancelled_at': datetime.now(timezone.utc),
                'reason': reason,
                'error_message': None,
            }
            
        except stripe.error.StripeError as e:
            raise ProcessorError(
                processor='stripe',
                error_code=e.code or 'unknown',
                error_message=str(e),
                metadata={'payment_intent_id': processor_transaction_id}
            )
    
    # ========================================================================
    # REFUNDS
    # ========================================================================
    
    def refund_payment(self, tx, processor_charge_id: str, 
                      amount: Optional[int] = None, 
                      reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Refund a captured payment (full or partial).
        
        Stripe automatically handles reversing the application fee proportionally.
        """
        try:
            refund_params = {
                'charge': processor_charge_id,
            }
            
            if amount:
                refund_params['amount'] = amount
            
            if reason:
                refund_params['reason'] = reason
            
            refund = stripe.Refund.create(**refund_params)
            
            # Calculate proportional fee refund
            original_charge = stripe.Charge.retrieve(processor_charge_id)
            original_amount = original_charge.amount
            original_fee = original_charge.application_fee_amount or 0
            
            if amount:
                # Partial refund - calculate proportional fee
                platform_fee_refunded = int((amount / original_amount) * original_fee)
            else:
                # Full refund
                platform_fee_refunded = original_fee
            
            return {
                'refund_id': refund.id,
                'status': refund.status,
                'amount_refunded': refund.amount,
                'platform_fee_refunded': platform_fee_refunded,
                'refunded_at': datetime.fromtimestamp(refund.created, tz=timezone.utc),
                'reason': reason,
                'error_message': None,
            }
            
        except stripe.error.StripeError as e:
            raise ProcessorError(
                processor='stripe',
                error_code=e.code or 'unknown',
                error_message=str(e),
                metadata={'charge_id': processor_charge_id}
            )
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def validate_configuration(self) -> bool:
        """
        Validate that Stripe configuration is complete.
        """
        if not stripe.api_key:
            return False
        
        try:
            # Test API key by retrieving account
            stripe.Account.retrieve()
            return True
        except stripe.error.StripeError:
            return False
    
    def _determine_account_status(self, account) -> str:
        """
        Determine human-readable account status from Stripe Account object.
        """
        if account.charges_enabled and account.payouts_enabled:
            return 'active'
        elif len(account.requirements.past_due or []) > 0:
            return 'restricted'
        elif len(account.requirements.currently_due or []) > 0:
            return 'pending'
        elif account.requirements.disabled_reason:
            return 'disabled'
        else:
            return 'pending'
    
    def _get_verification_status(self, account) -> str:
        """
        Get identity verification status from Stripe Account.
        """
        # Check if identity verification is in requirements
        currently_due = account.requirements.currently_due or []
        eventually_due = account.requirements.eventually_due or []
        
        identity_fields = [
            'individual.verification.document',
            'individual.verification.additional_document',
            'representative.verification.document',
        ]
        
        if any(field in currently_due for field in identity_fields):
            return 'required'
        elif any(field in eventually_due for field in identity_fields):
            return 'eventually_required'
        else:
            return 'verified'
    
    def _generate_initial_checklist(self) -> Dict[str, Any]:
        """
        Generate initial onboarding checklist for Stripe Express accounts.
        """
        return {
            'version': '1.0',
            'processor': 'stripe',
            'items': {
                'stripe_account_created': {
                    'title': 'Stripe Account Created',
                    'description': 'Connect your school to Stripe payment processing',
                    'required': True,
                    'completed': False,
                    'order': 1
                },
                'business_details_submitted': {
                    'title': 'Business Details Submitted',
                    'description': 'Provide your school\'s business information to Stripe',
                    'required': True,
                    'completed': False,
                    'order': 2,
                    'external_step': True  # Requires Stripe-hosted flow
                },
                'bank_account_connected': {
                    'title': 'Bank Account Connected',
                    'description': 'Link your school\'s bank account for payouts',
                    'required': True,
                    'completed': False,
                    'order': 3,
                    'external_step': True
                },
                'identity_verification': {
                    'title': 'Identity Verification',
                    'description': 'Verify authorized representative identity',
                    'required': True,
                    'completed': False,
                    'order': 4,
                    'external_step': True
                },
                'test_payment': {
                    'title': 'Test Payment',
                    'description': 'Process a test donation to verify setup',
                    'required': False,
                    'completed': False,
                    'order': 5
                },
                'revenue_split_configured': {
                    'title': 'Revenue Split Configured',
                    'description': 'Review and confirm payment split settings',
                    'required': True,
                    'completed': False,
                    'order': 6
                }
            }
        }
