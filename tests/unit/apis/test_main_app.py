from fastapi.testclient import TestClient

from listingautopilot.main import app


def test_main_app_registers_core_routers_and_metrics():
    client = TestClient(app)

    health_response = client.get("/health")
    providers_response = client.get("/v1/providers")
    metrics_response = client.get("/metrics")

    assert health_response.status_code == 200
    assert health_response.json()["status"] == "ok"
    assert providers_response.status_code == 200
    assert providers_response.json()[0]["provider_type"] == "demo"
    assert metrics_response.status_code == 200


def test_openapi_includes_bearer_auth_security_scheme():
    openapi_schema = app.openapi()

    assert openapi_schema["components"]["securitySchemes"]["BearerAuth"] == {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    assert openapi_schema["paths"]["/health"]["get"]["security"] == [
        {"BearerAuth": []}
    ]
    assert "/v1/projects/{project_id}/assets" in openapi_schema["paths"]
    assert "/v1/assets/{asset_id}" in openapi_schema["paths"]
    assert "/v1/projects/{project_id}/designs" in openapi_schema["paths"]
    assert "/v1/designs/{design_id}" in openapi_schema["paths"]
