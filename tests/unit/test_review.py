from sentinel.review import ReviewRecord, list_reviews, save_review


def test_review_record_is_persisted_locally(tmp_path) -> None:
    record = save_review(tmp_path, ReviewRecord(finding_id="finding", ledger_name="ledger.json", rationale="needs protocol owner review"))
    assert list_reviews(tmp_path)[0].id == record.id
