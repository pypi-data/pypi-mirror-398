"""Nellika SCB C Extension Module"""

import json
import os
from . import _binding

__version__ = "1.7.0"

# Automatically initialize telemetry on module import (if database env vars are set)
def _auto_init_telemetry():
    """Internal function to initialize telemetry on module import"""
    # Only initialize if we're in an Odoo environment (PGDATABASE is set)
    if os.environ.get('PGDATABASE'):
        try:
            # Call C function to initialize (fetches all data from database)
            _binding._internal_telemetry_init()
        except Exception as e:
            # Silently ignore errors during auto-init
            pass

# Run auto-init
_auto_init_telemetry()

def version():
    """Get module version"""
    return __version__

def create_qr(config_id, amount, reference, channel='ecomm'):
    """
    Create SCB QR code payment
    
    Args:
        config_id: SCB API configuration ID
        amount: Payment amount
        reference: Payment reference
        channel: Payment channel (default: 'ecomm')
    
    Returns:
        dict: Response with 'status' and 'data' keys
              status.code: 1000 = success, other = error
              status.description: Error message if failed
    """
    return _binding.scb_api_create_qr(str(config_id), float(amount), reference, channel)

def check_payment(reference):
    """
    Check SCB payment status
    
    Args:
        reference: Payment reference
    
    Returns:
        dict: JSON response with payment status
    """
    return _binding.scb_api_check_payment(reference)

def refresh_token(config_id):
    """
    Refresh SCB access token using config ID
    
    This method fetches API credentials from the database and refreshes the OAuth token.
    The token URL is automatically determined based on the environment (sandbox/production).
    
    Args:
        config_id: SCB API configuration ID from scb_api_config table
    
    Returns:
        dict: JSON response with access token data
              status.code: 1000 = success, other = error
              status.description: Error message if failed
              data.accessToken: OAuth access token
              data.expiresIn: Token expiry in seconds (typically 1800)
              data.tokenType: Token type ("Bearer")
    
    Environment variables required:
        PGDATABASE, PGHOST, PGPORT, PGUSER, PGPASSWORD
    
    Example:
        result = nell_scb_lib.refresh_token(config_id=1)
        if result['status']['code'] == 1000:
            token = result['data']['accessToken']
    """
    return _binding.scb_api_refresh_token(str(config_id))

def create_qr_full(api_key, access_token, qr_create_url, biller_id, amount, ref1, ref2, ref3="SCB"):
    """
    Create SCB QR code with full parameters
    
    Args:
        api_key: SCB API key
        access_token: Access token from refresh_token()
        qr_create_url: QR creation endpoint URL
        biller_id: PromptPay biller ID
        amount: Payment amount
        ref1: Reference 1 (max 20 chars)
        ref2: Reference 2 (max 12 chars)
        ref3: Reference 3 (default: "SCB")
    
    Returns:
        dict: JSON response with QR code data
    """
    return _binding.scb_api_create_qr_full(
        api_key, access_token, qr_create_url, biller_id,
        float(amount), ref1, ref2, ref3
    )

def create_qr_by_bank_account(bank_account_id, amount, ref1, ref2, ref3="SCB"):
    """
    Create SCB QR code using bank account ID - fetches config from database
    
    This is the recommended method for production use. It:
    - Connects to PostgreSQL (using PGHOST, PGDATABASE env vars)
    - Fetches SCB API config and biller ID from database
    - Automatically refreshes access token
    - Creates QR code via SCB API
    
    Args:
        bank_account_id: Bank account ID from res.partner.bank
        amount: Payment amount
        ref1: Reference 1 (max 20 chars, e.g. "P00001")
        ref2: Reference 2 (max 12 chars, e.g. "TEST")
        ref3: Reference 3 (default: "SCB")
    
    Returns:
        dict: JSON response with QR code data
    
    Environment variables required:
        PGDATABASE: Database name (default: nellika)
        PGHOST: PostgreSQL host (default: localhost)
        PGPORT: PostgreSQL port (default: 5432)
        PGUSER: PostgreSQL user (default: current user)
        PGPASSWORD: PostgreSQL password (optional)
    """
    return _binding.scb_api_create_qr_by_bank(
        str(bank_account_id), float(amount), ref1, ref2, ref3
    )

def create_qr_for_invoice(invoice_id, company_id, config_id, reference, amount, bank_account_id):
    """
    Create QR for invoice with intent caching - returns cached QR if exists
    
    This function implements smart caching:
    - First call: Creates QR via SCB API and stores in scb_payment_intent table
    - Subsequent calls: Returns cached QR from database (no SCB API call)
    
    Args:
        invoice_id: Invoice ID from account.move
        company_id: Company ID
        config_id: SCB API configuration ID
        reference: Payment reference (e.g. "I202500096")
        amount: Payment amount
        bank_account_id: Bank account ID from res.partner.bank
    
    Returns:
        dict: JSON response with intent data
              intent_id: Database intent ID
              reference: Payment reference
              amount: Payment amount
              qr_payload: PromptPay QR string
              qr_image_base64: Base64-encoded PNG image
              transaction_id: SCB transaction ID (if available)
    
    Environment variables required:
        PGDATABASE, PGHOST, PGPORT, PGUSER, PGPASSWORD
    """
    return _binding.create_qr_for_invoice(
        invoice_id=int(invoice_id),
        company_id=int(company_id),
        config_id=int(config_id),
        reference=reference,
        amount=float(amount),
        bank_account_id=str(bank_account_id)
    )

def payment_inquiry(config_id, transaction_ref=None, biller_id=None, 
                   reference1=None, reference2=None, amount=None, 
                   transaction_date=None):
    """
    Check SCB payment status via payment inquiry API
    
    This function supports two inquiry modes:
    1. Tag 31 inquiry: by transaction_ref (partnerTransactionId)
    2. Tag 30 inquiry: by biller_id + reference1
    
    Args:
        config_id: SCB API configuration ID from scb.api.config
        transaction_ref: Transaction reference for Tag 31 inquiry (optional)
        biller_id: PromptPay biller ID for Tag 30 inquiry (optional)
        reference1: Reference 1 for Tag 30 inquiry (optional)
        reference2: Reference 2 for Tag 30 inquiry (optional)
        amount: Payment amount for Tag 30 inquiry (optional)
        transaction_date: Transaction date (YYYY-MM-DD, defaults to today)
    
    Returns:
        dict: JSON response with payment status
              status.code: 1000 = success, other = error
              status.description: Error message if failed
              data: Payment inquiry data (if successful)
    
    Example (Tag 31):
        result = payment_inquiry(config_id=1, transaction_ref="TXN123")
    
    Example (Tag 30):
        result = payment_inquiry(
            config_id=1,
            biller_id="010555555555555",
            reference1="P00001",
            amount="100.00"
        )
    """
    return _binding.scb_api_payment_inquiry(
        config_id=str(config_id),
        transaction_ref=transaction_ref,
        biller_id=biller_id,
        reference1=reference1,
        reference2=reference2,
        amount=amount,
        transaction_date=transaction_date
    )
