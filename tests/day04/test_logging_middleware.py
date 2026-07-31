# [Ngày 4] Pytest — LoggingMiddleware ghi log request

import logging

import pytest


@pytest.mark.asyncio
async def test_logging_middleware_records_request(client, caplog):
    """Gọi endpoint bất kỳ — middleware ghi log method, path, status_code, latency_ms."""
    caplog.set_level(logging.INFO, logger="taskhub")

    response = await client.get("/")

    assert response.status_code == 200
    assert any(
        "Request: method=GET path=/ status_code=200 latency_ms=" in record.message
        for record in caplog.records
    )
