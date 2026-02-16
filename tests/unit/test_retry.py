from payments_pipeline.utils.retry import RetryConfig, retry_call


class TransientError(RuntimeError):
    pass


def test_retry_call_retries_then_succeeds() -> None:
    state = {"n": 0}

    def flaky() -> str:
        state["n"] += 1
        if state["n"] < 3:
            raise TransientError("try again")
        return "ok"

    value = retry_call(
        flaky,
        retryable_exceptions=(TransientError,),
        config=RetryConfig(max_attempts=4, base_delay_seconds=0.0, max_delay_seconds=0.0),
    )
    assert value == "ok"
    assert state["n"] == 3
