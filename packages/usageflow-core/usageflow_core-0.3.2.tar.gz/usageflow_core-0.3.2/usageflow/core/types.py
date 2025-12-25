from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class ApiConfigStrategy:
    id: str  # Assuming ObjectId can be represented as a string
    name: str
    account_id: str
    identity_field_name: str
    identity_field_location: str
    config_data: Dict[str, Any]
    created_at: int
    updated_at: int
    deleted_at: Optional[int] = field(default=None)
    application_id: Optional[str] = field(default=None)


@dataclass
class PolicyV2:
    endpoint_method: str = field(metadata={"json": "method"})
    endpoint_pattern: str = field(metadata={"json": "url"})
    identity_field_name: str = field(metadata={"json": "identityFieldName"})
    identity_field_location: str = field(metadata={"json": "identityFieldLocation"})
    has_rate_limit: bool = field(metadata={"json": "hasRateLimit"})

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "PolicyV2":
        """Convert camelCase JSON keys to snake_case dataclass fields"""
        # Build field map from metadata and convert camelCase JSON keys to snake_case dataclass fields
        field_map = {f.metadata["json"]: name for name, f in cls.__dataclass_fields__.items() if "json" in f.metadata}
        transformed_data = {field_map[k]: v for k, v in data.items() if k in field_map}
        return cls(**transformed_data)


@dataclass
class Policy:
    # Required fields (must come first)
    endpoint_pattern: str = field(metadata={"json": "url"})
    endpoint_method: str = field(metadata={"json": "method"})
    identity_field: str = field(metadata={"json": "identityField"})
    identity_location: str = field(metadata={"json": "identityLocation"})
    # Optional fields (must come after required fields)
    policy_id: Optional[str] = field(default=None, metadata={"json": "policyId"})
    account_id: Optional[str] = field(default=None, metadata={"json": "accountId"})
    application_id: Optional[str] = field(default=None, metadata={"json": "applicationId"})
    rate_limit: Optional[int] = field(default=None, metadata={"json": "rateLimit"})
    rate_limit_interval: Optional[str] = field(default=None, metadata={"json": "rateLimitInterval"})
    has_rate_limit: Optional[bool] = field(default=None, metadata={"json": "hasRateLimit"})
    metering_expression: Optional[str] = field(default=None, metadata={"json": "meteringExpression"})
    metering_trigger: Optional[str] = field(default=None, metadata={"json": "meteringTrigger"})
    stripe_price_id: Optional[str] = field(default=None, metadata={"json": "stripePriceId"})
    stripe_customer_id: Optional[str] = field(default=None, metadata={"json": "stripeCustomerId"})
    created_at: Optional[int] = field(default=None, metadata={"json": "createdAt"})
    updated_at: Optional[int] = field(default=None, metadata={"json": "updatedAt"})
    # ledger_id: Optional[str] = field(default=None, metadata={"json": "ledgerId"})  # Uncomment if needed
    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "Policy":
        """Convert camelCase JSON keys to snake_case dataclass fields, handling both old and new formats"""
        # Map new simplified format to old format (camelCase)
        field_mapping = {
            "url": "endpointPattern",
            "method": "endpointMethod",
            "identityFieldName": "identityField",
            "identityFieldLocation": "identityLocation",
        }

        # Transform new format keys to old format keys (camelCase)
        transformed_data = {}
        for key, value in data.items():
            if key in field_mapping:
                transformed_data[field_mapping[key]] = value
            else:
                transformed_data[key] = value

        # Build field map from metadata and convert camelCase JSON keys to snake_case dataclass fields
        field_map = {f.metadata["json"]: name for name, f in cls.__dataclass_fields__.items() if "json" in f.metadata}
        transformed_data = {field_map[k]: v for k, v in transformed_data.items() if k in field_map}
        return cls(**transformed_data)


@dataclass
class UsageFlowSocketMessage:
    """Base class for WebSocket messages"""
    type: str
    payload: Optional[Dict[str, Any]] = None
    id: Optional[str] = None
    replyTo: Optional[str] = None


@dataclass
class UsageFlowSocketResponse:
    """Base class for WebSocket responses"""
    type: Optional[str] = None  # 'success' or 'error'
    payload: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    error: Optional[str] = None
    id: Optional[str] = None
    replyTo: Optional[str] = None


# Python equivalent of: export type RoutesMap = Record<string, Record<string, boolean>>
RoutesMap = Dict[str, Dict[str, bool]]