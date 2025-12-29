"""Event type enumerations for Autonomize Observer."""

from enum import Enum


class EventCategory(str, Enum):
    """Top-level event categories."""

    TRACE = "trace"  # OTEL traces/spans (observability)
    AUDIT = "audit"  # User/system actions (compliance)
    SYSTEM = "system"  # Internal system events
    METRIC = "metric"  # Aggregated metrics


class TraceEventType(str, Enum):
    """OTEL Trace event types."""

    # Trace lifecycle
    TRACE_START = "trace_start"
    TRACE_END = "trace_end"

    # Span lifecycle
    SPAN_START = "span_start"
    SPAN_END = "span_end"
    SPAN = "span"  # Complete span (start + end)

    # LLM-specific
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    LLM_STREAM_START = "llm_stream_start"
    LLM_STREAM_CHUNK = "llm_stream_chunk"
    LLM_STREAM_END = "llm_stream_end"

    # Tool/Function calls
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"

    # Agent-specific
    AGENT_STEP = "agent_step"
    AGENT_DECISION = "agent_decision"
    AGENT_ACTION = "agent_action"


class AuditEventType(str, Enum):
    """Audit event types for compliance/tracking."""

    # Resource CRUD
    RESOURCE_CREATED = "resource_created"
    RESOURCE_READ = "resource_read"
    RESOURCE_UPDATED = "resource_updated"
    RESOURCE_DELETED = "resource_deleted"
    RESOURCE_ACCESSED = "resource_accessed"

    # Authentication/Authorization
    AUTH_LOGIN = "auth_login"
    AUTH_LOGOUT = "auth_logout"
    AUTH_FAILED = "auth_failed"
    AUTH_TOKEN_REFRESH = "auth_token_refresh"
    AUTH_TOKEN_REVOKED = "auth_token_revoked"

    # Permission changes
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REMOVED = "role_removed"

    # Data operations
    DATA_EXPORTED = "data_exported"
    DATA_IMPORTED = "data_imported"
    DATA_SHARED = "data_shared"
    SENSITIVE_DATA_ACCESS = "sensitive_data_access"

    # Configuration
    CONFIG_CHANGED = "config_changed"
    SECRET_ACCESSED = "secret_accessed"
    SECRET_ROTATED = "secret_rotated"
    SECRET_CREATED = "secret_created"
    SECRET_DELETED = "secret_deleted"

    # API
    API_REQUEST = "api_request"
    API_ERROR = "api_error"
    RATE_LIMITED = "rate_limited"
    WEBHOOK_SENT = "webhook_sent"
    WEBHOOK_RECEIVED = "webhook_received"

    # Compliance
    CONSENT_GIVEN = "consent_given"
    CONSENT_WITHDRAWN = "consent_withdrawn"
    DATA_DELETION_REQUEST = "data_deletion_request"
    DATA_RETENTION_EXPIRED = "data_retention_expired"

    # Execution
    FLOW_EXECUTED = "flow_executed"
    JOB_EXECUTED = "job_executed"
    BATCH_PROCESSED = "batch_processed"

    # AI
    AI_INTERACTION = "ai_interaction"

    # Data high-level
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    DATA_EXPORT = "data_export"

    # Auth high-level
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"


class AuditAction(str, Enum):
    """Simple CRUD actions for audit logging."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    SHARE = "share"
    EXPORT = "export"
    IMPORT = "import"
    LOGIN = "login"
    LOGOUT = "logout"


class SystemEventType(str, Enum):
    """Internal system event types."""

    # Service lifecycle
    SERVICE_STARTED = "service_started"
    SERVICE_STOPPED = "service_stopped"
    SERVICE_HEALTH_CHECK = "service_health_check"
    SERVICE_DEGRADED = "service_degraded"

    # Job management
    JOB_STARTED = "job_started"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    JOB_CANCELLED = "job_cancelled"

    # Circuit breaker
    CIRCUIT_BREAKER_OPEN = "circuit_breaker_open"
    CIRCUIT_BREAKER_CLOSE = "circuit_breaker_close"
    CIRCUIT_BREAKER_HALF_OPEN = "circuit_breaker_half_open"

    # Cache
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    CACHE_EVICTION = "cache_eviction"

    # Queue
    QUEUE_OVERFLOW = "queue_overflow"
    QUEUE_EMPTY = "queue_empty"
    MESSAGE_DEAD_LETTERED = "message_dead_lettered"


class ResourceType(str, Enum):
    """Types of resources that can be audited."""

    # Langflow/AI Studio
    FLOW = "flow"
    COMPONENT = "component"
    FOLDER = "folder"
    TEMPLATE = "template"

    # Users & Auth
    USER = "user"
    API_KEY = "api_key"
    SESSION = "session"
    TOKEN = "token"

    # Projects
    PROJECT = "project"
    WORKSPACE = "workspace"
    ORGANIZATION = "organization"

    # Data
    DATASET = "dataset"
    DOCUMENT = "document"
    FILE = "file"
    VECTOR_STORE = "vector_store"

    # Integrations
    MCP_SERVER = "mcp_server"
    INTEGRATION = "integration"
    WEBHOOK = "webhook"
    CONNECTION = "connection"

    # Models
    MODEL_CONFIG = "model_config"
    PROMPT_TEMPLATE = "prompt_template"
    AGENT = "agent"
    LLM_MODEL = "llm_model"

    # System
    CONFIGURATION = "configuration"
    SECRET = "secret"
    PERMISSION = "permission"
    ROLE = "role"

    # Generic
    RESOURCE = "resource"


class SpanKind(str, Enum):
    """OTEL Span Kind - indicates the relationship between spans."""

    UNSPECIFIED = "UNSPECIFIED"
    INTERNAL = "INTERNAL"  # Internal operation (default)
    SERVER = "SERVER"  # Handles incoming requests
    CLIENT = "CLIENT"  # Makes outgoing requests (LLM calls, HTTP)
    PRODUCER = "PRODUCER"  # Produces messages
    CONSUMER = "CONSUMER"  # Consumes messages


class SpanStatus(str, Enum):
    """OTEL Span Status Code."""

    UNSET = "UNSET"
    OK = "OK"
    ERROR = "ERROR"


class TraceSource(str, Enum):
    """Source of the trace - for routing and processing."""

    LANGFLOW = "langflow"  # AI Studio / Langflow flows
    DIRECT_LLM = "direct_llm"  # Direct LLM calls
    HTTP = "http"  # HTTP request tracing
    DATABASE = "database"  # Database operation tracing
    AGENT = "agent"  # Autonomous agent traces
    CUSTOM = "custom"  # Custom user-defined traces


class AuditSeverity(str, Enum):
    """Severity level for audit events."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditOutcome(str, Enum):
    """Outcome of an audited action."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    DENIED = "denied"


class ComplianceFramework(str, Enum):
    """Compliance frameworks for audit events."""

    HIPAA = "hipaa"
    GDPR = "gdpr"
    SOC2 = "soc2"
    PCI_DSS = "pci_dss"
    ISO_27001 = "iso_27001"
    CCPA = "ccpa"
    FERPA = "ferpa"
