from src.legal_record_dedupe import THRESHOLD, Record, find_near_duplicate


class FakeVectors:
    def __init__(self, score: float, metadata: dict[str, str]) -> None:
        self.score = score
        self.metadata = metadata

    def request(self, path: str, payload: dict) -> dict:
        assert path == "/vector/query"
        assert payload["embedding"] == [0.1, 0.2]
        return {"items": [{"score": self.score, "metadata": self.metadata}]}


def test_signed_delivery_and_deadline_followup_link_to_same_matter() -> None:
    followup = Record("matter-104", "deadline_follow_up", "Signed lease received; confirm filing deadline")
    result = find_near_duplicate(FakeVectors(THRESHOLD, {"matter_id": "matter-104"}), [0.1, 0.2])
    assert followup.kind == "deadline_follow_up"
    assert result == {"decision": "near_duplicate", "match": {"matter_id": "matter-104"}}


def test_distant_record_stays_new() -> None:
    result = find_near_duplicate(FakeVectors(0.2, {"matter_id": "matter-999"}), [0.1, 0.2])
    assert result == {"decision": "new_matter", "match": None}
