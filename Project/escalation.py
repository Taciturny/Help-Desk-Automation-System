"""
Optimized Escalation System
==========================
Streamlined escalation engine with built-in rules and fallback handling.
"""

import logging
from typing import Any, Dict, List

from data_models import (
    EscalationLevel,
    EscalationPriority,
    EscalationReason,
    EscalationRule,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EscalationEngine:
    def __init__(self):
        self.business_hours = {"start": 9, "end": 17}
        self.rules = self._get_default_rules()

    def _get_default_rules(self) -> List[EscalationRule]:
        return [
            EscalationRule(
                name="Security Incident",
                conditions={"category": "security_incident"},
                escalation_level=EscalationLevel.SECURITY_TEAM,
                priority=EscalationPriority.HIGH,
                reason=EscalationReason.SECURITY_CONCERN,
                contact_info="security-team@company.com",
                response_time_sla=15,
                description="Security team attention required",
                auto_assign=True,
            ),
            EscalationRule(
                name="Low Confidence Classification",
                conditions={"classification_confidence": {"<": 0.3}},
                escalation_level=EscalationLevel.LEVEL_2,
                priority=EscalationPriority.MEDIUM,
                reason=EscalationReason.LOW_CONFIDENCE,
                contact_info="level2-support@company.com",
                response_time_sla=60,
                description="Human review needed for unclear requests",
            ),
            EscalationRule(
                name="Hardware Failure",
                conditions={"category": "hardware_failure"},
                escalation_level=EscalationLevel.LEVEL_2,
                priority=EscalationPriority.HIGH,
                reason=EscalationReason.HARDWARE_FAILURE,
                contact_info="hardware-support@company.com",
                response_time_sla=30,
                description="Hardware specialists required",
            ),
            EscalationRule(
                name="System Outage",
                conditions={
                    "keywords": [
                        "outage",
                        "down",
                        "offline",
                        "not working",
                        "system failure",
                    ]
                },
                escalation_level=EscalationLevel.LEVEL_3,
                priority=EscalationPriority.CRITICAL,
                reason=EscalationReason.SYSTEM_OUTAGE,
                contact_info="system-admin@company.com",
                response_time_sla=15,
                description="System outage requiring immediate attention",
            ),
            EscalationRule(
                name="VIP User Support",
                conditions={"keywords": ["vip", "executive", "ceo", "cto", "director"]},
                escalation_level=EscalationLevel.LEVEL_3,
                priority=EscalationPriority.HIGH,
                reason=EscalationReason.VIP_USER,
                contact_info="vip-support@company.com",
                response_time_sla=30,
                description="VIP user priority support",
            ),
            EscalationRule(
                name="Data Loss",
                conditions={
                    "keywords": [
                        "lost data",
                        "deleted files",
                        "corrupted",
                        "backup",
                        "restore",
                    ]
                },
                escalation_level=EscalationLevel.LEVEL_2,
                priority=EscalationPriority.HIGH,
                reason=EscalationReason.DATA_LOSS,
                contact_info="data-recovery@company.com",
                response_time_sla=45,
                description="Data loss or recovery issue",
            ),
            # Fallback rule for critical unclassified issues
            EscalationRule(
                name="Critical Unclassified",
                conditions={
                    "priority": "critical",
                    "classification_confidence": {"<": 0.5},
                },
                escalation_level=EscalationLevel.LEVEL_3,
                priority=EscalationPriority.CRITICAL,
                reason=EscalationReason.UNKNOWN_CATEGORY,
                contact_info="escalation-team@company.com",
                response_time_sla=30,
                description="Critical issue requiring immediate review",
            ),
        ]

    def evaluate_ticket(self, ticket_data: Dict[str, Any]) -> List[EscalationRule]:
        matching_rules = []
        unmatched_reasons = []

        for rule in self.rules:
            if self._rule_matches(rule, ticket_data):
                matching_rules.append(rule)
            else:
                unmatched_reasons.append(f"Rule '{rule.name}' failed condition check")

        if not matching_rules:
            logger.info(
                f"No escalation rules matched. Reasons: {'; '.join(unmatched_reasons)}"
            )
        else:
            # Sort by priority (CRITICAL > HIGH > MEDIUM > LOW)
            priority_order = {p: i for i, p in enumerate(EscalationPriority)}
            matching_rules.sort(key=lambda r: priority_order[r.priority])
            logger.info(f"Ticket matches {len(matching_rules)} rules")

        return matching_rules

    def _rule_matches(self, rule: EscalationRule, ticket_data: Dict[str, Any]) -> bool:
        for key, condition in rule.conditions.items():
            if not self._evaluate_condition(key, condition, ticket_data):
                return False
        return True

    def _evaluate_condition(
        self, key: str, condition: Any, ticket_data: Dict[str, Any]
    ) -> bool:
        ticket_value = ticket_data.get(key)

        if ticket_value is None:
            return False

        if isinstance(condition, dict):
            # Handle comparison operators like {'<': 0.3}
            for operator, threshold in condition.items():
                if operator == "<" and not (ticket_value < threshold):
                    return False
                elif operator == ">" and not (ticket_value > threshold):
                    return False
                elif operator == "==" and not (ticket_value == threshold):
                    return False
            return True
        elif key == "keywords":
            # Check if keywords appear in text fields
            text_content = " ".join(
                str(ticket_data.get(field, "")).lower()
                for field in ["description", "title", "summary", "user_message"]
            )
            return any(keyword.lower() in text_content for keyword in condition)
        else:
            return condition == ticket_value

    def get_escalation_recommendation(
        self, ticket_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        matching_rules = self.evaluate_ticket(ticket_data)

        if not matching_rules:
            return {
                "should_escalate": False,
                "reason": "No escalation rules matched the ticket criteria",
            }

        primary_rule = matching_rules[0]

        return {
            "should_escalate": True,
            "primary_rule": primary_rule.name,
            "escalation_level": primary_rule.escalation_level.value,
            "priority": primary_rule.priority.value,
            "contact_info": primary_rule.contact_info,
            "response_time_sla": primary_rule.response_time_sla,
            "description": primary_rule.description,
            "auto_assign": primary_rule.auto_assign,
            "total_matches": len(matching_rules),
        }

    def analyze_batch(self, tickets: List[Dict[str, Any]]) -> Dict[str, Any]:
        total_tickets = len(tickets)
        escalated_tickets = 0
        escalation_levels = {}
        priority_distribution = {}

        for ticket in tickets:
            recommendation = self.get_escalation_recommendation(ticket)

            if recommendation["should_escalate"]:
                escalated_tickets += 1

                level = recommendation["escalation_level"]
                escalation_levels[level] = escalation_levels.get(level, 0) + 1

                priority = recommendation["priority"]
                priority_distribution[priority] = (
                    priority_distribution.get(priority, 0) + 1
                )

        return {
            "total_tickets": total_tickets,
            "escalated_tickets": escalated_tickets,
            "escalation_rate": (
                escalated_tickets / total_tickets if total_tickets > 0 else 0
            ),
            "escalation_levels": escalation_levels,
            "priority_distribution": priority_distribution,
        }


def main():
    """Test the optimized escalation engine."""
    print("=== Optimized Escalation Engine Test ===\n")

    engine = EscalationEngine()

    test_tickets = [
        {
            "id": "TICKET-001",
            "title": "Security breach detected",
            "description": "Unauthorized access attempt detected on server",
            "category": "security_incident",
            "classification_confidence": 0.95,
        },
        {
            "id": "TICKET-002",
            "title": "Email not working",
            "description": "Cannot send or receive emails since this morning",
            "category": "email_configuration",
            "classification_confidence": 0.25,
        },
        {
            "id": "TICKET-003",
            "title": "System outage - CRM down",
            "description": "CRM system is completely offline and not working",
            "category": "system_issue",
            "classification_confidence": 0.88,
        },
        {
            "id": "TICKET-004",
            "title": "Critical unknown issue",
            "description": "Something is very wrong but unclear what",
            "priority": "critical",
            "classification_confidence": 0.2,
        },
    ]

    print("=== Individual Ticket Analysis ===")
    for ticket in test_tickets:
        print(f"\n--- {ticket['id']}: {ticket['title']} ---")
        recommendation = engine.get_escalation_recommendation(ticket)

        if recommendation["should_escalate"]:
            print("✅ ESCALATION REQUIRED")
            print(f"Rule: {recommendation['primary_rule']}")
            print(f"Level: {recommendation['escalation_level']}")
            print(f"Priority: {recommendation['priority']}")
            print(f"Contact: {recommendation['contact_info']}")
            print(f"SLA: {recommendation['response_time_sla']} min")
        else:
            print(f"❌ NO ESCALATION NEEDED - {recommendation['reason']}")

    print("\n=== Batch Analysis ===")
    batch_results = engine.analyze_batch(test_tickets)
    print(f"Total tickets: {batch_results['total_tickets']}")
    print(f"Escalated: {batch_results['escalated_tickets']}")
    print(f"Escalation rate: {batch_results['escalation_rate']:.2%}")
    print(f"Levels: {batch_results['escalation_levels']}")


if __name__ == "__main__":
    main()
