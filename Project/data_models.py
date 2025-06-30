"""
Optimized Data Models for Intelligent Help Desk System
======================================================
Streamlined data models with removed redundancy and improved structure.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

# === ENUMERATIONS ===


class RequestCategory(Enum):
    """Enumeration of supported request categories."""

    PASSWORD_RESET = "password_reset"
    SOFTWARE_INSTALLATION = "software_installation"
    HARDWARE_FAILURE = "hardware_failure"
    NETWORK_CONNECTIVITY = "network_connectivity"
    EMAIL_CONFIGURATION = "email_configuration"
    SECURITY_INCIDENT = "security_incident"
    POLICY_QUESTION = "policy_question"
    UNKNOWN = "unknown"
    NON_IT_REQUEST = "non_it_request"


class EscalationPriority(Enum):
    """Unified priority levels for requests and escalations."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EscalationLevel(Enum):
    """Escalation levels for help desk requests."""

    LEVEL_1 = "level_1"
    LEVEL_2 = "level_2"
    LEVEL_3 = "level_3"
    SECURITY_TEAM = "security_team"
    MANAGEMENT = "management"
    VENDOR_SUPPORT = "vendor_support"


class EscalationReason(Enum):
    """Reasons for escalation."""

    LOW_CONFIDENCE = "low_confidence"
    SECURITY_CONCERN = "security_concern"
    HARDWARE_FAILURE = "hardware_failure"
    MANAGEMENT_APPROVAL = "management_approval"
    SYSTEM_OUTAGE = "system_outage"
    VIP_USER = "vip_user"
    DATA_LOSS = "data_loss"
    UNKNOWN_CATEGORY = "unknown_category"
    COMPLEX_TECHNICAL = "complex_technical_issue"


# === CORE DATA MODELS ===


@dataclass
class UserRequest:
    """Represents a user help desk request."""

    id: str
    message: str
    timestamp: str
    user_email: Optional[str] = None
    priority: EscalationPriority = EscalationPriority.MEDIUM


@dataclass
class ClassificationResult:
    """Result of request classification."""

    category: RequestCategory
    confidence: float
    keywords_matched: List[str]
    reasoning: str


@dataclass
class RetrievalResult:
    """Result from knowledge retrieval."""

    content: str
    source: str
    relevance_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeResponse:
    """Complete response from knowledge system."""

    query: str
    answer: str
    relevant_documents: List[RetrievalResult]
    confidence: float


# === ESCALATION MODELS ===


@dataclass
class EscalationRule:
    """Defines conditions and actions for escalation."""

    name: str
    conditions: Dict[str, Any]
    escalation_level: EscalationLevel
    priority: EscalationPriority
    reason: EscalationReason
    contact_info: str
    response_time_sla: int  # minutes
    description: str
    auto_assign: bool = False
    requires_approval: bool = False


@dataclass
class EscalationDecision:
    """Result of escalation analysis."""

    should_escalate: bool
    escalation_level: Optional[EscalationLevel]
    priority: EscalationPriority
    reasons: List[EscalationReason]
    contact_info: str
    response_time_sla: int
    automated_response: str
    additional_info: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.0


# === RESPONSE MODELS ===


@dataclass
class HelpDeskResponse:
    """Complete help desk response to user request."""

    request_id: str
    category: RequestCategory
    classification_confidence: float
    answer: str
    escalation_decision: EscalationDecision
    knowledge_sources: List[str]
    response_confidence: float
    response_time: datetime = field(default_factory=datetime.now)


# === ABSTRACT BASE CLASSES ===


class ClassificationStrategy(ABC):
    """Abstract base class for classification strategies."""

    @abstractmethod
    def classify(self, request: str) -> ClassificationResult:
        """Classify a request and return the result."""
        pass


class EscalationStrategy(ABC):
    """Abstract base class for escalation strategies."""

    @abstractmethod
    def should_escalate(self, context: Dict[str, Any]) -> EscalationDecision:
        """Determine if a request should be escalated."""
        pass


# === UTILITY CLASSES ===


@dataclass
class SystemMetrics:
    """System performance and usage metrics."""

    total_requests: int = 0
    classified_requests: int = 0
    escalated_requests: int = 0
    average_confidence: float = 0.0
    average_response_time: float = 0.0
    category_distribution: Dict[str, int] = field(default_factory=dict)
    escalation_rate: float = 0.0


@dataclass
class RequestContext:
    """Context information for processing requests."""

    user_request: UserRequest
    classification_result: ClassificationResult
    knowledge_response: KnowledgeResponse
    user_history: List[Dict] = field(default_factory=list)
    system_status: Dict[str, Any] = field(default_factory=dict)
    business_hours: bool = True
    processing_time: datetime = field(default_factory=datetime.now)
