from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from agent.intelligence.contracts import (
    EntityScope,
    EntityType,
    Evidence,
    Policy,
    Signal,
    TimeWindow,
)


def test_signal_contract_rejects_invalid_confidence():
    with pytest.raises(ValidationError):
        Signal(
            signal_id="SIG-X",
            signal_type="test",
            entity_type=EntityType.CUSTOMER,
            entity_id="CUST-X",
            value=True,
            confidence=1.2,
            observed_at=datetime.now(UTC),
            source_interaction_id="INT-X",
            evidence_refs=["EV-X"],
        )


def test_evidence_and_scope_contracts_forbid_untyped_input():
    with pytest.raises(ValidationError):
        Evidence.model_validate(
            {
                "evidence_id": "EV-X",
                "source_interaction_id": "INT-X",
                "source_type": "test",
                "observed_at": datetime.now(UTC),
                "excerpt": "Synthetic evidence",
                "unexpected": True,
            }
        )
    with pytest.raises(ValidationError, match="entity identifier"):
        EntityScope()


def test_policy_and_time_window_validation():
    with pytest.raises(ValidationError, match="review_threshold"):
        Policy(policy_id="p", version="1", name="bad", allow_threshold=0.4, review_threshold=0.8)
    with pytest.raises(ValidationError, match="start"):
        TimeWindow(start=datetime(2026, 9, 2, tzinfo=UTC), end=datetime(2026, 9, 1, tzinfo=UTC))
