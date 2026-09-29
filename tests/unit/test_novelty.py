from sentinel.novelty import detect_novelty_signals


def test_novelty_engine_marks_parameterized_delegatecall_for_review() -> None:
    assessment, findings = detect_novelty_signals({
        "src/Proxy.sol": "contract Proxy { function execute(address target, bytes calldata data) external { target.delegatecall(data); } }",
    })

    assert assessment["review_required"] is True
    assert {item.detector for item in findings} >= {"parameterized-delegatecall"}
    assert all(item.status.value == "human_review_required" for item in findings)


def test_novelty_engine_does_not_claim_a_vulnerability_without_signals() -> None:
    assessment, findings = detect_novelty_signals({"src/Safe.sol": "contract Safe { uint256 private value; }"})

    assert assessment["candidate_count"] == 0
    assert findings == []
