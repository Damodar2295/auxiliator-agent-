"""Realistic synthetic inputs representing an upstream semantic/data foundation."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from agent.intelligence.contracts import Entity, EntityType, Evidence, Fact, Relationship, Signal

SYNTHETIC_DATA_NOTICE = "SYNTHETIC / POC DATA — not production customer information"


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=UTC)


class SyntheticIntelligenceRepository:
    """Read-only replacement point for future Salesforce and Knowledge Fabric adapters."""

    def __init__(self) -> None:
        self.entities = _entities()
        self.evidence = _evidence()
        self.signals = _signals()
        self.facts = _facts()
        self.relationships = _relationships()
        self.metrics: dict[str, dict[str, float]] = {
            "OPP-3001": {"days_in_stage": 37, "engagement_30d_change": -0.42, "spend_90d_change": -0.18},
            "OPP-3002": {"days_in_stage": 11, "engagement_30d_change": 0.26, "spend_90d_change": 0.12},
            "CUST-1001": {"travel_spend_share": 0.61, "cashback_category_share": 0.22},
            "CUST-1002": {"travel_spend_share": 0.14, "cashback_category_share": 0.68},
        }

    def list_entities(self, entity_type: EntityType | None = None) -> list[Entity]:
        values = list(self.entities.values())
        if entity_type:
            values = [entity for entity in values if entity.entity_type == entity_type]
        return sorted(values, key=lambda item: item.entity_id)

    def get_entity(self, entity_id: str) -> Entity | None:
        return self.entities.get(entity_id)

    def get_evidence(self, evidence_id: str) -> Evidence | None:
        return self.evidence.get(evidence_id)

    def list_evidence(self, evidence_ids: list[str] | None = None) -> list[Evidence]:
        if evidence_ids is None:
            return list(self.evidence.values())
        return [self.evidence[item] for item in evidence_ids if item in self.evidence]

    def metadata(self) -> dict[str, Any]:
        return {
            "notice": SYNTHETIC_DATA_NOTICE,
            "entities": len(self.entities),
            "signals": len(self.signals),
            "evidence": len(self.evidence),
            "facts": len(self.facts),
            "relationships": len(self.relationships),
        }


def _entities() -> dict[str, Entity]:
    items = [
        Entity(
            entity_id="CUST-1001",
            entity_type=EntityType.CUSTOMER,
            display_name="Avery Chen (Synthetic)",
            attributes={"segment": "premium", "region": "US-East"},
        ),
        Entity(
            entity_id="CUST-1002",
            entity_type=EntityType.CUSTOMER,
            display_name="Jordan Patel (Synthetic)",
            attributes={"segment": "consumer", "region": "US-West"},
        ),
        Entity(
            entity_id="CUST-1003",
            entity_type=EntityType.CUSTOMER,
            display_name="Morgan Lee (Synthetic)",
            attributes={"segment": "small-business", "region": "US-Central"},
        ),
        Entity(
            entity_id="CUST-1004",
            entity_type=EntityType.CUSTOMER,
            display_name="Riley Johnson (Synthetic)",
            attributes={"segment": "premium", "region": "US-East"},
        ),
        Entity(
            entity_id="ACCT-2001",
            entity_type=EntityType.ACCOUNT,
            display_name="Northstar Retail (Synthetic)",
            attributes={"industry": "Retail", "tier": "Enterprise"},
            parent_ids=["CUST-1001"],
        ),
        Entity(
            entity_id="ACCT-2002",
            entity_type=EntityType.ACCOUNT,
            display_name="Summit Travel Group (Synthetic)",
            attributes={"industry": "Travel", "tier": "Enterprise"},
            parent_ids=["CUST-1002"],
        ),
        Entity(
            entity_id="ACCT-2003",
            entity_type=EntityType.ACCOUNT,
            display_name="Harbor Services (Synthetic)",
            attributes={"industry": "Business Services", "tier": "Mid-Market"},
            parent_ids=["CUST-1003"],
        ),
        Entity(
            entity_id="OPP-3001",
            entity_type=EntityType.OPPORTUNITY,
            display_name="Northstar Platform Expansion (Synthetic)",
            attributes={"stage": "Solution Validation", "amount": 425000, "currency": "USD"},
            parent_ids=["ACCT-2001"],
        ),
        Entity(
            entity_id="OPP-3002",
            entity_type=EntityType.OPPORTUNITY,
            display_name="Summit Rewards Renewal (Synthetic)",
            attributes={"stage": "Discovery", "amount": 180000, "currency": "USD"},
            parent_ids=["ACCT-2002"],
        ),
        Entity(
            entity_id="CALL-8801",
            entity_type=EntityType.INTERACTION,
            display_name="Northstar pricing call (Synthetic)",
            attributes={"channel": "call", "duration_minutes": 38},
            parent_ids=["OPP-3001"],
        ),
        Entity(
            entity_id="CASE-8802",
            entity_type=EntityType.INTERACTION,
            display_name="Rewards complaint case (Synthetic)",
            attributes={"channel": "service_case"},
            parent_ids=["CUST-1002"],
        ),
    ]
    return {item.entity_id: item for item in items}


def _evidence() -> dict[str, Evidence]:
    items = [
        Evidence(
            evidence_id="EV-9001",
            source_interaction_id="CALL-8801",
            source_type="mock_call_summary",
            observed_at=_dt("2026-08-28T15:00:00"),
            excerpt="The buyer said pricing was above the approved range and requested a revised value case.",
            signal_id="SIG-1001",
            provenance={"system": "mock_semantic_layer", "record": "CALL-8801"},
            reliability=0.92,
        ),
        Evidence(
            evidence_id="EV-9002",
            source_interaction_id="CALL-8801",
            source_type="mock_call_summary",
            observed_at=_dt("2026-08-28T15:00:00"),
            excerpt="The buyer named Atlas Rewards as an alternative under evaluation.",
            signal_id="SIG-1002",
            provenance={"system": "mock_semantic_layer", "record": "CALL-8801"},
            reliability=0.9,
        ),
        Evidence(
            evidence_id="EV-9003",
            source_interaction_id="ACTIVITY-7710",
            source_type="mock_crm_activity_metric",
            observed_at=_dt("2026-08-31T12:00:00"),
            excerpt="Customer engagement declined 42 percent over the trailing 30-day period.",
            signal_id="SIG-1003",
            provenance={"system": "mock_salesforce_adapter", "record": "OPP-3001"},
            reliability=0.96,
        ),
        Evidence(
            evidence_id="EV-9004",
            source_interaction_id="CALL-8801",
            source_type="mock_call_summary",
            observed_at=_dt("2026-08-28T15:00:00"),
            excerpt="The team remains interested if implementation effort and measurable value are clarified.",
            signal_id="SIG-1004",
            provenance={"system": "mock_semantic_layer", "record": "CALL-8801"},
            reliability=0.88,
        ),
        Evidence(
            evidence_id="EV-9010",
            source_interaction_id="CASE-8802",
            source_type="mock_service_case",
            observed_at=_dt("2026-08-30T09:30:00"),
            excerpt="Customer reported that expected travel points were not credited after a hotel purchase.",
            signal_id="SIG-1010",
            provenance={"system": "mock_service_platform", "record": "CASE-8802"},
            reliability=0.95,
        ),
        Evidence(
            evidence_id="EV-9011",
            source_interaction_id="CASE-8802",
            source_type="mock_service_case",
            observed_at=_dt("2026-08-30T09:30:00"),
            excerpt="The complaint topic was classified upstream as rewards fulfillment.",
            signal_id="SIG-1011",
            provenance={"system": "mock_semantic_layer", "record": "CASE-8802"},
            reliability=0.91,
        ),
        Evidence(
            evidence_id="EV-9020",
            source_interaction_id="SPEND-6601",
            source_type="mock_aggregate_metric",
            observed_at=_dt("2026-08-31T00:00:00"),
            excerpt="Sixty-one percent of eligible spend was in travel categories over the prior 90 days.",
            signal_id="SIG-1020",
            provenance={"system": "mock_analytics_layer", "record": "CUST-1001"},
            reliability=0.94,
        ),
        Evidence(
            evidence_id="EV-9021",
            source_interaction_id="SPEND-6602",
            source_type="mock_aggregate_metric",
            observed_at=_dt("2026-08-31T00:00:00"),
            excerpt="Cashback-category affinity measured 0.22 over the prior 90 days.",
            signal_id="SIG-1021",
            provenance={"system": "mock_analytics_layer", "record": "CUST-1001"},
            reliability=0.94,
        ),
        Evidence(
            evidence_id="EV-9030",
            source_interaction_id="ACTIVITY-7722",
            source_type="mock_crm_activity_metric",
            observed_at=_dt("2026-08-31T12:00:00"),
            excerpt="Account engagement declined 31 percent and no customer-owned next step is recorded.",
            signal_id="SIG-1030",
            provenance={"system": "mock_salesforce_adapter", "record": "ACCT-2003"},
            reliability=0.93,
        ),
    ]
    return {item.evidence_id: item for item in items}


def _signals() -> list[Signal]:
    raw: list[tuple[str, str, EntityType, str, bool | int | float | str | list[str], float, str, list[str]]] = [
        ("SIG-1001", "pricing_objection", EntityType.OPPORTUNITY, "OPP-3001", True, 0.91, "CALL-8801", ["EV-9001"]),
        (
            "SIG-1002",
            "competitor_mention",
            EntityType.OPPORTUNITY,
            "OPP-3001",
            "Atlas Rewards",
            0.88,
            "CALL-8801",
            ["EV-9002"],
        ),
        (
            "SIG-1003",
            "engagement_change",
            EntityType.OPPORTUNITY,
            "OPP-3001",
            -0.42,
            0.96,
            "ACTIVITY-7710",
            ["EV-9003"],
        ),
        ("SIG-1004", "purchase_intent", EntityType.OPPORTUNITY, "OPP-3001", True, 0.82, "CALL-8801", ["EV-9004"]),
        ("SIG-1005", "sales_intent", EntityType.OPPORTUNITY, "OPP-3001", True, 0.86, "CALL-8801", ["EV-9004"]),
        ("SIG-1006", "spend_shift", EntityType.ACCOUNT, "ACCT-2001", -0.18, 0.89, "SPEND-6610", ["EV-9003"]),
        (
            "SIG-1007",
            "product_interest",
            EntityType.OPPORTUNITY,
            "OPP-3001",
            ["Enterprise Platform", "Analytics"],
            0.84,
            "CALL-8801",
            ["EV-9004"],
        ),
        ("SIG-1010", "complaint_detected", EntityType.CUSTOMER, "CUST-1002", True, 0.97, "CASE-8802", ["EV-9010"]),
        (
            "SIG-1011",
            "complaint_topic",
            EntityType.CUSTOMER,
            "CUST-1002",
            "rewards_fulfillment",
            0.91,
            "CASE-8802",
            ["EV-9011"],
        ),
        ("SIG-1020", "travel_affinity", EntityType.CUSTOMER, "CUST-1001", 0.87, 0.93, "SPEND-6601", ["EV-9020"]),
        ("SIG-1021", "cashback_affinity", EntityType.CUSTOMER, "CUST-1001", 0.34, 0.9, "SPEND-6602", ["EV-9021"]),
        (
            "SIG-1022",
            "merchant",
            EntityType.CUSTOMER,
            "CUST-1001",
            ["Skyline Air", "Harbor Hotels"],
            0.89,
            "SPEND-6601",
            ["EV-9020"],
        ),
        (
            "SIG-1023",
            "commodity",
            EntityType.CUSTOMER,
            "CUST-1001",
            ["airfare", "lodging"],
            0.86,
            "SPEND-6601",
            ["EV-9020"],
        ),
        ("SIG-1030", "engagement_change", EntityType.ACCOUNT, "ACCT-2003", -0.31, 0.93, "ACTIVITY-7722", ["EV-9030"]),
        ("SIG-1040", "travel_affinity", EntityType.CUSTOMER, "CUST-1002", 0.22, 0.9, "SPEND-6620", ["EV-9010"]),
        ("SIG-1041", "cashback_affinity", EntityType.CUSTOMER, "CUST-1002", 0.81, 0.92, "SPEND-6621", ["EV-9011"]),
    ]
    observed = _dt("2026-08-31T12:00:00")
    return [
        Signal(
            signal_id=item[0],
            signal_type=item[1],
            entity_type=item[2],
            entity_id=item[3],
            value=item[4],
            confidence=item[5],
            observed_at=observed,
            source_interaction_id=item[6],
            evidence_refs=item[7],
        )
        for item in raw
    ]


def _facts() -> list[Fact]:
    observed = _dt("2026-08-31T12:00:00")
    return [
        Fact(
            entity_id="OPP-3001",
            name="opportunity_stage",
            value="Solution Validation",
            source="mock_salesforce_adapter",
            observed_at=observed,
        ),
        Fact(
            entity_id="OPP-3001",
            name="opportunity_amount",
            value=425000,
            source="mock_salesforce_adapter",
            observed_at=observed,
        ),
        Fact(
            entity_id="ACCT-2001",
            name="account_industry",
            value="Retail",
            source="mock_salesforce_adapter",
            observed_at=observed,
        ),
        Fact(
            entity_id="OPP-3001", name="next_step", value=None, source="mock_salesforce_adapter", observed_at=observed
        ),
    ]


def _relationships() -> list[Relationship]:
    return [
        Relationship(source_entity_id="CUST-1001", relationship_type="member_of", target_entity_id="ACCT-2001"),
        Relationship(source_entity_id="ACCT-2001", relationship_type="has_opportunity", target_entity_id="OPP-3001"),
        Relationship(source_entity_id="OPP-3001", relationship_type="has_interaction", target_entity_id="CALL-8801"),
        Relationship(source_entity_id="CUST-1002", relationship_type="member_of", target_entity_id="ACCT-2002"),
    ]
