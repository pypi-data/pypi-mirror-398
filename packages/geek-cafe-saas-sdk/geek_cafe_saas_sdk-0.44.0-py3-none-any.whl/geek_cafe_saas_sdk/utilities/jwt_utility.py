"""
JWT Token Utility for parsing JWT tokens.

This module provides utilities for parsing JWT tokens in Lambda functions.
Note: This is for parsing pre-validated tokens from API Gateway authorizers,
not for token validation/verification.
"""

import json
import base64
from typing import Dict, Any, Optional
from aws_lambda_powertools import Logger

logger = Logger(__name__)


class JwtUtility:
    """Utility class for parsing JWT tokens."""

    @staticmethod
    def parse_jwt_payload(token: str) -> Optional[Dict[str, Any]]:
        """
        Parse the payload from a JWT token without verification.
        
        This method extracts and decodes the payload section of a JWT token.
        It does NOT verify the token signature - use this only for tokens
        that have already been validated by API Gateway authorizers.
        
        Args:
            token: The JWT token string (with or without 'Bearer ' prefix)
            
        Returns:
            The decoded payload as a dictionary, or None if parsing fails
            
        Raises:
            ValueError: If the token format is invalid
        """
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            elif token.startswith('bearer '):
                token = token[7:]
            
            # JWT tokens have 3 parts separated by dots: header.payload.signature
            parts = token.split('.')
            if len(parts) != 3:
                raise ValueError(f"Invalid JWT format: expected 3 parts, got {len(parts)}")
            
            # Get the payload (second part)
            payload_part = parts[1]
            
            # Add padding if needed (base64 requires length to be multiple of 4)
            payload_part = JwtUtility._add_base64_padding(payload_part)
            
            # Decode the base64-encoded payload
            decoded_bytes = base64.urlsafe_b64decode(payload_part)
            decoded_str = decoded_bytes.decode('utf-8')
            
            # Parse the JSON payload
            payload = json.loads(decoded_str)
            
            logger.debug(f"Successfully parsed JWT payload with keys: {list(payload.keys())}")
            return payload
            
        except Exception as e:
            logger.warning(f"Failed to parse JWT token: {str(e)}")
            return None

    @staticmethod
    def parse_jwt_header(token: str) -> Optional[Dict[str, Any]]:
        """
        Parse the header from a JWT token.
        
        Args:
            token: The JWT token string (with or without 'Bearer ' prefix)
            
        Returns:
            The decoded header as a dictionary, or None if parsing fails
        """
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            elif token.startswith('bearer '):
                token = token[7:]
            
            # JWT tokens have 3 parts separated by dots: header.payload.signature
            parts = token.split('.')
            if len(parts) != 3:
                raise ValueError(f"Invalid JWT format: expected 3 parts, got {len(parts)}")
            
            # Get the header (first part)
            header_part = parts[0]
            
            # Add padding if needed
            header_part = JwtUtility._add_base64_padding(header_part)
            
            # Decode the base64-encoded header
            decoded_bytes = base64.urlsafe_b64decode(header_part)
            decoded_str = decoded_bytes.decode('utf-8')
            
            # Parse the JSON header
            header = json.loads(decoded_str)
            
            logger.debug(f"Successfully parsed JWT header: {header}")
            return header
            
        except Exception as e:
            logger.warning(f"Failed to parse JWT header: {str(e)}")
            return None

    @staticmethod
    def get_claim_from_token(token: str, claim_key: str) -> Optional[str]:
        """
        Extract a specific claim from a JWT token.
        
        Args:
            token: The JWT token string
            claim_key: The claim key to extract (e.g., 'sub', 'email', 'custom:user_id')
            
        Returns:
            The claim value as a string, or None if not found
        """
        payload = JwtUtility.parse_jwt_payload(token)
        if not payload:
            return None
        
        claim_value = payload.get(claim_key)
        if claim_value is not None:
            return str(claim_value)
        
        return None

    @staticmethod
    def _add_base64_padding(encoded_string: str) -> str:
        """
        Add padding to a base64-encoded string if needed.
        
        Base64 strings must have a length that's a multiple of 4.
        JWT tokens often omit the padding characters.
        
        Args:
            encoded_string: The base64-encoded string
            
        Returns:
            The padded base64 string
        """
        # Calculate how many padding characters we need
        padding_needed = 4 - (len(encoded_string) % 4)
        
        # Add padding if needed (but not if it's already a multiple of 4)
        if padding_needed != 4:
            encoded_string += '=' * padding_needed
        
        return encoded_string

    @staticmethod
    def is_token_expired(token: str) -> Optional[bool]:
        """
        Check if a JWT token is expired based on the 'exp' claim.
        
        Args:
            token: The JWT token string
            
        Returns:
            True if expired, False if not expired, None if exp claim not found or parsing failed
        """
        import time
        
        payload = JwtUtility.parse_jwt_payload(token)
        if not payload:
            return None
        
        exp_claim = payload.get('exp')
        if exp_claim is None:
            return None
        
        try:
            # 'exp' claim is typically a Unix timestamp
            exp_timestamp = int(exp_claim)
            current_timestamp = int(time.time())
            
            return current_timestamp > exp_timestamp
            
        except (ValueError, TypeError):
            logger.warning(f"Invalid 'exp' claim format: {exp_claim}")
            return None

    @staticmethod
    def get_token_info(token: str) -> Dict[str, Any]:
        """
        Get comprehensive information about a JWT token.
        
        Args:
            token: The JWT token string
            
        Returns:
            Dictionary containing token information including header, payload, and metadata
        """
        info = {
            'valid': False,
            'header': None,
            'payload': None,
            'expired': None,
            'claims': {},
        }
        
        try:
            # Parse header and payload
            header = JwtUtility.parse_jwt_header(token)
            payload = JwtUtility.parse_jwt_payload(token)
            
            if header and payload:
                info['valid'] = True
                info['header'] = header
                info['payload'] = payload
                info['expired'] = JwtUtility.is_token_expired(token)
                
                # Extract common claims
                common_claims = [
                    'sub', 'iss', 'aud', 'exp', 'iat', 'nbf', 'jti',
                    'email', 'name', 'given_name', 'family_name',
                    'custom:user_id', 'custom:tenant_id', 'custom:user_roles'
                ]
                
                for claim in common_claims:
                    if claim in payload:
                        info['claims'][claim] = payload[claim]
            
        except Exception as e:
            logger.error(f"Error getting token info: {str(e)}")
        
        return info
