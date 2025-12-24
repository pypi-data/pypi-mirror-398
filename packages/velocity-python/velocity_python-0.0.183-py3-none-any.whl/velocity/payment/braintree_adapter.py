"""
Braintree Payment Processor Adapter

Implements the PaymentProcessorAdapter interface for Braintree payment processing.

This adapter wraps the existing Braintree integration to make it compatible with
the processor-agnostic payment flow. Braintree was the original processor and
remains available for legacy clients.

Key Features:
- Platform-centric model (all payments to CaringCent account)
- Manual settlement to clients (not instant split like Stripe)
- Sub-merchant accounts (if configured)
- Authorization with later capture support
"""
import os
import braintree
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from .base_adapter import PaymentProcessorAdapter, ProcessorError


class BraintreeAdapter(PaymentProcessorAdapter):
    """
    Braintree adapter for payment processing.
    
    Uses Braintree sub-merchant accounts with manual settlement.
    All payments go to CaringCent platform account first.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Braintree adapter with API credentials.
        
        Args:
            config: Dictionary containing:
                - merchant_id: Braintree merchant ID (required)
                - public_key: Braintree public key (required)
                - private_key: Braintree private key (required)
                - environment: 'sandbox' or 'production' (default: 'sandbox')
        """
        super().__init__(config)
        
        # Configure Braintree gateway
        environment_name = config.get('environment', 'sandbox')
        bt_environment = (
            braintree.Environment.Production 
            if environment_name == 'production' 
            else braintree.Environment.Sandbox
        )
        
        self.gateway = braintree.BraintreeGateway(
            braintree.Configuration(
                environment=bt_environment,
                merchant_id=config.get('merchant_id'),
                public_key=config.get('public_key'),
                private_key=config.get('private_key')
            )
        )
        
        self.environment = environment_name
    
    # ========================================================================
    # ACCOUNT MANAGEMENT
    # ========================================================================
    
    def create_account(self, tx, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a Braintree sub-merchant account for a client school.
        
        Note: Braintree sub-merchants are simpler than Stripe Connect.
        They don't get separate dashboards or instant payouts.
        """
        try:
            # Extract client data
            client_id = client_data['client_id']
            business_name = client_data.get('business_name', client_data.get('school_name'))
            email = client_data['email']
            
            # Create sub-merchant account
            result = self.gateway.merchant_account.create({
                'individual': {
                    'first_name': client_data.get('first_name', 'Admin'),
                    'last_name': client_data.get('last_name', business_name),
                    'email': email,
                    'phone': client_data.get('phone'),
                    'date_of_birth': client_data.get('date_of_birth'),
                    'ssn': client_data.get('ssn'),  # Last 4 digits
                    'address': {
                        'street_address': client_data.get('address', {}).get('street_address'),
                        'locality': client_data.get('address', {}).get('city'),
                        'region': client_data.get('address', {}).get('state'),
                        'postal_code': client_data.get('address', {}).get('postal_code'),
                    }
                },
                'business': {
                    'legal_name': business_name,
                    'dba_name': client_data.get('dba_name', business_name),
                    'tax_id': client_data.get('tax_id'),
                    'address': {
                        'street_address': client_data.get('business_address', {}).get('street_address'),
                        'locality': client_data.get('business_address', {}).get('city'),
                        'region': client_data.get('business_address', {}).get('state'),
                        'postal_code': client_data.get('business_address', {}).get('postal_code'),
                    }
                },
                'funding': {
                    'descriptor': client_data.get('descriptor', business_name[:22]),
                    'destination': braintree.MerchantAccount.FundingDestination.Bank,
                    'email': email,
                    'mobile_phone': client_data.get('phone'),
                    'account_number': client_data.get('bank_account_number'),
                    'routing_number': client_data.get('bank_routing_number'),
                },
                'tos_accepted': True,
                'master_merchant_account_id': self.gateway.config.merchant_id,
            })
            
            if result.is_success:
                merchant_account = result.merchant_account
                
                # Store in client_payment_accounts table
                payment_account = tx.table('client_payment_accounts').new()
                payment_account['client_id'] = client_id
                payment_account['processor_type'] = 'braintree'
                payment_account['processor_account_id'] = merchant_account.id
                payment_account['account_status'] = merchant_account.status
                payment_account['charges_enabled'] = (merchant_account.status == 'active')
                payment_account['payouts_enabled'] = False  # Manual payouts
                payment_account['details_submitted'] = True
                payment_account['requirements_data'] = {}
                payment_account['capabilities'] = {
                    'card_payments': merchant_account.status == 'active',
                    'manual_settlement': True,
                }
                
                # Create minimal onboarding checklist (Braintree is simpler)
                checklist = tx.table('client_onboarding_checklists').new()
                checklist['client_id'] = client_id
                checklist['processor_type'] = 'braintree'
                checklist['processor_account_id'] = merchant_account.id
                checklist['checklist_state'] = self._generate_initial_checklist()
                checklist['current_step'] = 0
                checklist['completed'] = (merchant_account.status == 'active')
                
                return {
                    'processor_account_id': merchant_account.id,
                    'status': merchant_account.status,
                    'requires_onboarding': (merchant_account.status == 'pending'),
                    'onboarding_url': None,  # No hosted onboarding for Braintree
                    'charges_enabled': (merchant_account.status == 'active'),
                    'payouts_enabled': False,  # Manual settlement
                    'metadata': {
                        'account_type': 'sub_merchant',
                        'master_merchant_id': self.gateway.config.merchant_id,
                    }
                }
            else:
                # Account creation failed
                error_message = '; '.join([
                    f"{error.code}: {error.message}" 
                    for error in result.errors.deep_errors
                ])
                raise ProcessorError(
                    processor='braintree',
                    error_code='account_creation_failed',
                    error_message=error_message,
                    metadata={'client_id': client_id}
                )
            
        except Exception as e:
            if isinstance(e, ProcessorError):
                raise
            raise ProcessorError(
                processor='braintree',
                error_code='unknown_error',
                error_message=str(e),
                metadata={'client_id': client_data.get('client_id')}
            )
    
    def get_account_status(self, tx, processor_account_id: str) -> Dict[str, Any]:
        """
        Retrieve current status of a Braintree sub-merchant account.
        """
        try:
            merchant_account = self.gateway.merchant_account.find(processor_account_id)
            
            # Update database record
            payment_account = tx.table('client_payment_accounts').find_one({
                'processor_account_id': processor_account_id,
                'processor_type': 'braintree'
            })
            
            if payment_account:
                payment_account['account_status'] = merchant_account.status
                payment_account['charges_enabled'] = (merchant_account.status == 'active')
                payment_account['updated_at'] = datetime.now(timezone.utc)
            
            return {
                'account_id': merchant_account.id,
                'status': merchant_account.status,
                'charges_enabled': (merchant_account.status == 'active'),
                'payouts_enabled': False,  # Manual settlement
                'requirements_due': [],
                'requirements_past_due': [],
                'requirements_deadline': None,
                'verification_status': 'verified' if merchant_account.status == 'active' else 'pending',
                'metadata': {
                    'master_merchant_id': merchant_account.master_merchant_account.id,
                    'currency': merchant_account.currency_iso_code,
                }
            }
            
        except braintree.exceptions.NotFoundError:
            raise ProcessorError(
                processor='braintree',
                error_code='account_not_found',
                error_message=f"Merchant account {processor_account_id} not found",
                metadata={'account_id': processor_account_id}
            )
        except Exception as e:
            raise ProcessorError(
                processor='braintree',
                error_code='unknown_error',
                error_message=str(e),
                metadata={'account_id': processor_account_id}
            )
    
    def create_onboarding_link(self, tx, processor_account_id: str, 
                              return_url: str, refresh_url: str) -> str:
        """
        Braintree doesn't support hosted onboarding flows.
        Returns None (onboarding must be done via BackOffice forms).
        """
        return None
    
    # ========================================================================
    # PAYMENT AUTHORIZATION (PRE-AUTH)
    # ========================================================================
    
    def authorize_payment(self, tx, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pre-authorize a payment using Braintree Transaction.sale with submit_for_settlement=False.
        
        Note: Braintree charges to platform account. Revenue split handled manually.
        """
        try:
            # Extract payment data
            amount_cents = payment_data['amount']
            amount_dollars = amount_cents / 100  # Braintree uses dollars
            payment_method_nonce = payment_data['payment_method']
            processor_account_id = payment_data.get('processor_account_id')
            
            # Build transaction params
            transaction_params = {
                'amount': f"{amount_dollars:.2f}",
                'payment_method_nonce': payment_method_nonce,
                'options': {
                    'submit_for_settlement': False,  # Pre-auth only
                },
                'custom_fields': {
                    'client_id': str(payment_data.get('client_id')),
                    'form_sys_id': str(payment_data.get('form_sys_id', '')),
                    'platform': 'caringcent',
                },
            }
            
            # Add sub-merchant account if configured
            if processor_account_id:
                transaction_params['merchant_account_id'] = processor_account_id
            
            # Add customer details
            if payment_data.get('donor_email'):
                transaction_params['customer'] = {
                    'email': payment_data['donor_email'],
                    'first_name': payment_data.get('donor_name', '').split()[0] if payment_data.get('donor_name') else None,
                    'last_name': ' '.join(payment_data.get('donor_name', '').split()[1:]) if payment_data.get('donor_name') else None,
                }
            
            # Create transaction
            result = self.gateway.transaction.sale(transaction_params)
            
            if result.is_success:
                transaction = result.transaction
                
                # Braintree authorizations typically expire in 7 days
                expires_at = datetime.now(timezone.utc) + timedelta(days=7)
                
                return {
                    'processor_transaction_id': transaction.id,
                    'status': 'authorized',
                    'amount': int(float(transaction.amount) * 100),  # Convert back to cents
                    'currency': transaction.currency_iso_code.lower(),
                    'authorization_code': transaction.processor_authorization_code,
                    'expires_at': expires_at,
                    'error_message': None,
                    'metadata': {
                        'transaction': transaction,
                        'processor_response_code': transaction.processor_response_code,
                        'processor_response_text': transaction.processor_response_text,
                    }
                }
            else:
                # Authorization failed
                error_message = result.message
                if result.transaction:
                    error_message = f"{result.transaction.processor_response_text}"
                
                return {
                    'processor_transaction_id': None,
                    'status': 'failed',
                    'amount': payment_data.get('amount'),
                    'currency': payment_data.get('currency', 'usd'),
                    'authorization_code': None,
                    'expires_at': None,
                    'error_message': error_message,
                    'metadata': {
                        'braintree_errors': [
                            f"{error.code}: {error.message}" 
                            for error in result.errors.deep_errors
                        ]
                    }
                }
            
        except Exception as e:
            return {
                'processor_transaction_id': None,
                'status': 'failed',
                'amount': payment_data.get('amount'),
                'currency': payment_data.get('currency', 'usd'),
                'authorization_code': None,
                'expires_at': None,
                'error_message': str(e),
                'metadata': {'error_type': type(e).__name__}
            }
    
    # ========================================================================
    # PAYMENT CAPTURE
    # ========================================================================
    
    def capture_payment(self, tx, processor_transaction_id: str, 
                       amount: Optional[int] = None) -> Dict[str, Any]:
        """
        Capture a previously authorized Braintree transaction.
        
        Submits the authorized transaction for settlement.
        """
        try:
            # Braintree uses submitForSettlement to capture
            if amount:
                amount_dollars = amount / 100
                result = self.gateway.transaction.submit_for_settlement(
                    processor_transaction_id,
                    f"{amount_dollars:.2f}"
                )
            else:
                result = self.gateway.transaction.submit_for_settlement(
                    processor_transaction_id
                )
            
            if result.is_success:
                transaction = result.transaction
                
                amount_captured_cents = int(float(transaction.amount) * 100)
                
                # Note: Revenue split not handled by Braintree - must be calculated separately
                return {
                    'processor_transaction_id': transaction.id,
                    'processor_charge_id': transaction.id,  # Same as transaction ID for Braintree
                    'status': 'captured',
                    'amount_captured': amount_captured_cents,
                    'platform_fee': 0,  # Calculated separately in business logic
                    'client_amount': amount_captured_cents,  # Full amount (split later)
                    'captured_at': datetime.now(timezone.utc),
                    'error_message': None,
                    'metadata': {
                        'transaction': transaction,
                        'settlement_status': transaction.status,
                    }
                }
            else:
                error_message = result.message
                raise ProcessorError(
                    processor='braintree',
                    error_code='capture_failed',
                    error_message=error_message,
                    metadata={'transaction_id': processor_transaction_id}
                )
            
        except Exception as e:
            if isinstance(e, ProcessorError):
                raise
            raise ProcessorError(
                processor='braintree',
                error_code='unknown_error',
                error_message=str(e),
                metadata={'transaction_id': processor_transaction_id}
            )
    
    def cancel_payment(self, tx, processor_transaction_id: str, 
                      reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Cancel (void) a previously authorized Braintree transaction.
        
        This releases the authorization without charging the customer.
        """
        try:
            result = self.gateway.transaction.void(processor_transaction_id)
            
            if result.is_success:
                transaction = result.transaction
                
                return {
                    'processor_transaction_id': transaction.id,
                    'status': 'cancelled',
                    'cancelled_at': datetime.now(timezone.utc),
                    'reason': reason,
                    'error_message': None,
                }
            else:
                error_message = result.message
                raise ProcessorError(
                    processor='braintree',
                    error_code='cancellation_failed',
                    error_message=error_message,
                    metadata={'transaction_id': processor_transaction_id}
                )
            
        except Exception as e:
            if isinstance(e, ProcessorError):
                raise
            raise ProcessorError(
                processor='braintree',
                error_code='unknown_error',
                error_message=str(e),
                metadata={'transaction_id': processor_transaction_id}
            )
    
    # ========================================================================
    # REFUNDS
    # ========================================================================
    
    def refund_payment(self, tx, processor_charge_id: str, 
                      amount: Optional[int] = None, 
                      reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Refund a settled Braintree transaction (full or partial).
        """
        try:
            if amount:
                amount_dollars = amount / 100
                result = self.gateway.transaction.refund(
                    processor_charge_id,
                    f"{amount_dollars:.2f}"
                )
            else:
                result = self.gateway.transaction.refund(processor_charge_id)
            
            if result.is_success:
                refund_transaction = result.transaction
                
                amount_refunded_cents = int(float(refund_transaction.amount) * 100)
                
                return {
                    'refund_id': refund_transaction.id,
                    'status': 'succeeded',
                    'amount_refunded': amount_refunded_cents,
                    'platform_fee_refunded': 0,  # Calculated separately
                    'refunded_at': datetime.now(timezone.utc),
                    'reason': reason,
                    'error_message': None,
                }
            else:
                error_message = result.message
                raise ProcessorError(
                    processor='braintree',
                    error_code='refund_failed',
                    error_message=error_message,
                    metadata={'transaction_id': processor_charge_id}
                )
            
        except Exception as e:
            if isinstance(e, ProcessorError):
                raise
            raise ProcessorError(
                processor='braintree',
                error_code='unknown_error',
                error_message=str(e),
                metadata={'transaction_id': processor_charge_id}
            )
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def validate_configuration(self) -> bool:
        """
        Validate that Braintree configuration is complete.
        """
        try:
            # Test configuration by pinging API
            self.gateway.merchant_account.find(self.gateway.config.merchant_id)
            return True
        except Exception:
            return False
    
    def _generate_initial_checklist(self) -> Dict[str, Any]:
        """
        Generate initial onboarding checklist for Braintree sub-merchants.
        
        Note: Braintree onboarding is simpler - mostly done via BackOffice forms.
        """
        return {
            'version': '1.0',
            'processor': 'braintree',
            'items': {
                'account_created': {
                    'title': 'Braintree Account Created',
                    'description': 'Sub-merchant account created in Braintree',
                    'required': True,
                    'completed': False,
                    'order': 1
                },
                'business_details_verified': {
                    'title': 'Business Details Verified',
                    'description': 'Business information verified by Braintree',
                    'required': True,
                    'completed': False,
                    'order': 2
                },
                'bank_account_verified': {
                    'title': 'Bank Account Verified',
                    'description': 'Bank account verified for settlements',
                    'required': True,
                    'completed': False,
                    'order': 3
                },
            }
        }
