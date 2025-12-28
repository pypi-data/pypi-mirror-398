"""
Data Masking - PII protection with automatic detection and masking
Supports reversible anonymization for dev/test environments and compliance masking.
"""

from typing import Any, Dict, List, Optional, Pattern, Callable
from dataclasses import dataclass
from enum import Enum
import re
from datetime import datetime


class MaskingStrategy(Enum):
    """Data masking strategies"""
    FULL_MASK = "FULL_MASK"              # X's for full field
    PARTIAL_MASK = "PARTIAL_MASK"        # Show only start/end
    HASH = "HASH"                        # Irreversible hash
    SHUFFLE = "SHUFFLE"                  # Randomize values
    TOKENIZE = "TOKENIZE"                # Replace with token
    NULLIFY = "NULLIFY"                  # Replace with NULL
    ENCRYPT = "ENCRYPT"                  # Encrypt field
    REDACT = "REDACT"                    # Remove from output


class DataClassification(Enum):
    """Data sensitivity classification"""
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"
    PII = "PII"
    PHI = "PHI"  # Protected Health Information
    PCI = "PCI"  # Payment Card Industry


@dataclass
class MaskingRule:
    """Rule for masking specific data"""
    column_name: str
    strategy: MaskingStrategy
    classification: DataClassification
    pattern: Optional[Pattern] = None
    preserve_length: bool = True
    custom_mask_fn: Optional[Callable] = None


class MaskingPatterns:
    """Common patterns for detecting PII"""
    
    # Email pattern
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    # Phone pattern (US)
    PHONE_PATTERN = re.compile(r'^\+?1?\d{9,15}$')
    
    # Credit card pattern
    CC_PATTERN = re.compile(r'^\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}$')
    
    # SSN pattern
    SSN_PATTERN = re.compile(r'^\d{3}-\d{2}-\d{4}$')
    
    # Date of birth pattern
    DOB_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    
    # IP address pattern
    IP_PATTERN = re.compile(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$')
    
    @staticmethod
    def detect_type(value: str) -> Optional[str]:
        """Auto-detect data type"""
        if not isinstance(value, str):
            return None
        
        if MaskingPatterns.EMAIL_PATTERN.match(value):
            return "email"
        elif MaskingPatterns.PHONE_PATTERN.match(value):
            return "phone"
        elif MaskingPatterns.CC_PATTERN.match(value):
            return "credit_card"
        elif MaskingPatterns.SSN_PATTERN.match(value):
            return "ssn"
        elif MaskingPatterns.DOB_PATTERN.match(value):
            return "dob"
        elif MaskingPatterns.IP_PATTERN.match(value):
            return "ip_address"
        
        return None


class MaskingEngine:
    """Executes data masking operations"""
    
    @staticmethod
    def mask_full(value: Any, preserve_length: bool = True) -> str:
        """Full masking - replace with X's"""
        if value is None:
            return "NULL"
        
        length = len(str(value))
        mask = "X" * length if preserve_length else "XXXX"
        
        return mask
    
    @staticmethod
    def mask_partial(value: str, show_start: int = 2, show_end: int = 2) -> str:
        """Partial masking - show only start and end"""
        if value is None or len(value) <= show_start + show_end:
            return MaskingEngine.mask_full(value)
        
        start = value[:show_start]
        end = value[-show_end:]
        middle_length = len(value) - show_start - show_end
        
        return f"{start}{'*' * middle_length}{end}"
    
    @staticmethod
    def mask_email(email: str) -> str:
        """Mask email - show only domain"""
        parts = email.split("@")
        if len(parts) != 2:
            return MaskingEngine.mask_partial(email)
        
        local = parts[0]
        domain = parts[1]
        masked_local = f"{local[0]}***"
        
        return f"{masked_local}@{domain}"
    
    @staticmethod
    def mask_phone(phone: str) -> str:
        """Mask phone - show only area code and last digit"""
        digits = re.sub(r'\D', '', phone)
        if len(digits) < 10:
            return MaskingEngine.mask_partial(phone)
        
        return f"({digits[:3]}) ***-**{digits[-1]}"
    
    @staticmethod
    def mask_credit_card(cc: str) -> str:
        """Mask credit card - show only last 4 digits"""
        digits = re.sub(r'\D', '', cc)
        return f"**** **** **** {digits[-4:]}"
    
    @staticmethod
    def mask_ssn(ssn: str) -> str:
        """Mask SSN - show only last 4"""
        digits = re.sub(r'\D', '', ssn)
        if len(digits) != 9:
            return MaskingEngine.mask_full(ssn)
        
        return f"***-**-{digits[-4:]}"
    
    @staticmethod
    def mask_ip_address(ip: str) -> str:
        """Mask IP address"""
        parts = ip.split(".")
        if len(parts) != 4:
            return MaskingEngine.mask_partial(ip)
        
        return f"{parts[0]}.{parts[1]}.0.0"
    
    @staticmethod
    def mask_by_type(value: str, data_type: str) -> str:
        """Mask based on detected type"""
        if data_type == "email":
            return MaskingEngine.mask_email(value)
        elif data_type == "phone":
            return MaskingEngine.mask_phone(value)
        elif data_type == "credit_card":
            return MaskingEngine.mask_credit_card(value)
        elif data_type == "ssn":
            return MaskingEngine.mask_ssn(value)
        elif data_type == "ip_address":
            return MaskingEngine.mask_ip_address(value)
        else:
            return MaskingEngine.mask_full(value)


class DataMasking:
    """Main data masking system"""
    
    def __init__(self):
        self.rules: Dict[str, MaskingRule] = {}
        self.auto_detect_enabled = True
        self.mask_operations = 0
    
    def add_rule(self, rule: MaskingRule):
        """Add a masking rule"""
        self.rules[rule.column_name] = rule
    
    def add_column_rule(self, column_name: str, 
                       strategy: MaskingStrategy,
                       classification: DataClassification):
        """Add masking rule for a column"""
        rule = MaskingRule(column_name, strategy, classification)
        self.add_rule(rule)
    
    def mask_field(self, value: Any, column_name: str, 
                  rule: Optional[MaskingRule] = None) -> Any:
        """Mask a single field"""
        
        if value is None:
            return None
        
        # Use provided rule or lookup
        if rule is None:
            rule = self.rules.get(column_name)
        
        # Auto-detect if no rule
        if rule is None and self.auto_detect_enabled:
            data_type = MaskingPatterns.detect_type(str(value))
            if data_type:
                return MaskingEngine.mask_by_type(str(value), data_type)
            return value
        
        if rule is None:
            return value
        
        # Apply custom mask function if provided
        if rule.custom_mask_fn:
            return rule.custom_mask_fn(value)
        
        # Apply strategy
        if rule.strategy == MaskingStrategy.FULL_MASK:
            return MaskingEngine.mask_full(value, rule.preserve_length)
        elif rule.strategy == MaskingStrategy.PARTIAL_MASK:
            return MaskingEngine.mask_partial(str(value))
        elif rule.strategy == MaskingStrategy.HASH:
            return f"HASH({hash(str(value)) & 0xffffff})"
        elif rule.strategy == MaskingStrategy.NULLIFY:
            return None
        elif rule.strategy == MaskingStrategy.REDACT:
            return "[REDACTED]"
        else:
            return value
        
        self.mask_operations += 1
    
    def mask_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Mask all fields in a row"""
        masked_row = {}
        
        for column, value in row.items():
            masked_row[column] = self.mask_field(value, column)
        
        return masked_row
    
    def mask_dataset(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Mask multiple rows"""
        return [self.mask_row(row) for row in rows]
    
    def get_column_classification(self, column_name: str) -> Optional[DataClassification]:
        """Get classification for column"""
        rule = self.rules.get(column_name)
        return rule.classification if rule else None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get masking statistics"""
        return {
            "rules_configured": len(self.rules),
            "auto_detect_enabled": self.auto_detect_enabled,
            "mask_operations": self.mask_operations,
            "columns_by_classification": self._get_columns_by_classification()
        }
    
    def _get_columns_by_classification(self) -> Dict[str, List[str]]:
        """Get columns grouped by classification"""
        grouped = {}
        
        for column, rule in self.rules.items():
            classification = rule.classification.value
            if classification not in grouped:
                grouped[classification] = []
            grouped[classification].append(column)
        
        return grouped


class AnonymizationEngine:
    """Reversible anonymization for dev/test environments"""
    
    def __init__(self):
        self.value_map: Dict[str, str] = {}  # Original -> Anonymous
        self.reverse_map: Dict[str, str] = {}  # Anonymous -> Original
        self.counter = 0
    
    def anonymize(self, value: str, value_type: str = "generic") -> str:
        """Create anonymous version of value"""
        if value in self.value_map:
            return self.value_map[value]
        
        anonymous = f"{value_type}_{self.counter}"
        self.counter += 1
        
        self.value_map[value] = anonymous
        self.reverse_map[anonymous] = value
        
        return anonymous
    
    def deanonymize(self, anonymous_value: str) -> Optional[str]:
        """Recover original value"""
        return self.reverse_map.get(anonymous_value)
    
    def get_mapping_statistics(self) -> Dict[str, Any]:
        """Get anonymization statistics"""
        return {
            "anonymized_count": len(self.value_map),
            "unique_types": len(set(v.split("_")[0] for v in self.value_map.values()))
        }


class ComplianceMasking:
    """Compliance-specific masking (GDPR, HIPAA, PCI-DSS)"""
    
    @staticmethod
    def get_gdpr_mask_rules() -> Dict[str, MaskingRule]:
        """Get GDPR-compliant masking rules"""
        return {
            "email": MaskingRule("email", MaskingStrategy.PARTIAL_MASK, DataClassification.PII),
            "phone": MaskingRule("phone", MaskingStrategy.HASH, DataClassification.PII),
            "address": MaskingRule("address", MaskingStrategy.REDACT, DataClassification.PII),
            "date_of_birth": MaskingRule("date_of_birth", MaskingStrategy.REDACT, DataClassification.PII),
        }
    
    @staticmethod
    def get_hipaa_mask_rules() -> Dict[str, MaskingRule]:
        """Get HIPAA-compliant masking rules"""
        return {
            "patient_id": MaskingRule("patient_id", MaskingStrategy.HASH, DataClassification.PHI),
            "ssn": MaskingRule("ssn", MaskingStrategy.REDACT, DataClassification.PHI),
            "medical_record": MaskingRule("medical_record", MaskingStrategy.NULLIFY, DataClassification.PHI),
            "diagnosis": MaskingRule("diagnosis", MaskingStrategy.REDACT, DataClassification.PHI),
        }
    
    @staticmethod
    def get_pci_dss_mask_rules() -> Dict[str, MaskingRule]:
        """Get PCI-DSS-compliant masking rules"""
        return {
            "credit_card": MaskingRule("credit_card", MaskingStrategy.PARTIAL_MASK, DataClassification.PCI),
            "cvv": MaskingRule("cvv", MaskingStrategy.REDACT, DataClassification.PCI),
            "card_holder": MaskingRule("card_holder", MaskingStrategy.HASH, DataClassification.PCI),
        }


if __name__ == "__main__":
    print("✓ Data masking module loaded successfully")
