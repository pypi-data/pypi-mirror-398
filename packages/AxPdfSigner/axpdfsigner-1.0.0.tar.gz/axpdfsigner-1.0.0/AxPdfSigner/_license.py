"""
License validation module - INTERNAL USE ONLY
This module handles license key validation for the SDK
"""

import hashlib
import datetime
import base64
from typing import Optional, Tuple


class _LicenseValidator:
    """Internal license validator"""
    
    # Master key (in production, this would be more secure)
    _MASTER_KEY = "axBridge2025SecureKey"
    
    def __init__(self):
        self._license_valid = False
        self._license_info = {}
    
    def validate_license(self, license_key: Optional[str] = None) -> bool:
        """
        Validate license key
        
        For now, this is a placeholder. In production:
        - Check license key format
        - Verify signature
        - Check expiration
        - Validate machine binding
        """
        # For SDK version 1.0, we'll allow unlimited usage
        # In future versions, implement proper license validation
        
        if license_key:
            # Parse and validate license key
            try:
                decoded = self._decode_license(license_key)
                if decoded:
                    self._license_valid = True
                    self._license_info = decoded
                    return True
            except:
                pass
        
        # Default: allow usage (for initial release)
        self._license_valid = True
        self._license_info = {
            'type': 'trial',
            'expires': None,
            'features': 'all'
        }
        return True
    
    def _decode_license(self, key: str) -> dict:
        """Decode license key"""
        try:
            # Simple decoding (in production, use proper encryption)
            decoded = base64.b64decode(key).decode('utf-8')
            parts = decoded.split('|')
            
            if len(parts) >= 3:
                return {
                    'type': parts[0],
                    'expires': parts[1],
                    'features': parts[2]
                }
        except:
            pass
        return {}
    
    def check_feature(self, feature: str) -> bool:
        """Check if a feature is enabled"""
        if not self._license_valid:
            return False
        
        features = self._license_info.get('features', '')
        return features == 'all' or feature in features.split(',')
    
    def get_license_info(self) -> dict:
        """Get license information"""
        return self._license_info.copy()
    
    @staticmethod
    def generate_trial_license() -> str:
        """Generate a trial license key"""
        # 30-day trial
        expires = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime('%Y-%m-%d')
        license_data = f"trial|{expires}|all"
        return base64.b64encode(license_data.encode()).decode()


# Global validator instance
_validator = _LicenseValidator()


def validate_license(license_key: Optional[str] = None) -> bool:
    """Validate SDK license"""
    return _validator.validate_license(license_key)


def check_feature(feature: str) -> bool:
    """Check if feature is available"""
    return _validator.check_feature(feature)
