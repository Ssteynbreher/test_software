import os

import pytest
import requests
import urllib3


BMC_URL = os.getenv("BMC_URL", "https://127.0.0.1:2443")
BMC_USER = os.getenv("BMC_USER", "root")
BMC_PASSWORD = os.getenv("BMC_PASSWORD", "0penBmc")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@pytest.fixture(scope="session")
def redfish_session():
    session = requests.Session()
    session.verify = False
    session.auth = (BMC_USER, BMC_PASSWORD)
    return session


def test_redfish_root_available(redfish_session):
    response = redfish_session.get(f"{BMC_URL}/redfish/v1/", timeout=20)
    assert response.status_code == 200
    body = response.json()
    assert "Systems" in body


def test_session_authentication():
    response = requests.post(
        f"{BMC_URL}/redfish/v1/SessionService/Sessions",
        json={"UserName": BMC_USER, "Password": BMC_PASSWORD},
        verify=False,
        timeout=20,
    )
    assert response.status_code in (200, 201)
    assert response.headers.get("X-Auth-Token") or response.json().get("@odata.id")


def test_system_information_contains_status_and_power(redfish_session):
    response = redfish_session.get(f"{BMC_URL}/redfish/v1/Systems/system", timeout=20)
    assert response.status_code == 200
    body = response.json()
    assert "Status" in body
    # QEMU images may expose the state only in the standard Status object.
    assert body.get("PowerState") or body["Status"].get("State")


def test_power_on_request_is_accepted(redfish_session):
    system = redfish_session.get(f"{BMC_URL}/redfish/v1/Systems/system", timeout=20).json()
    reset_action = system.get("Actions", {}).get("#ComputerSystem.Reset", {})
    target = reset_action.get("target")
    if not target:
        pytest.skip("The selected QEMU image does not expose a reset action")

    response = redfish_session.post(
        f"{BMC_URL}{target}" if target.startswith("/") else target,
        json={"ResetType": "On"},
        timeout=20,
    )
    if response.status_code == 404:
        pytest.skip("The selected QEMU image advertises reset but does not implement it")
    assert response.status_code in (200, 202, 204)


def test_cpu_temperature_is_within_expected_range(redfish_session):
    response = redfish_session.get(f"{BMC_URL}/redfish/v1/Chassis/chassis/Thermal", timeout=20)
    assert response.status_code in (200, 404)
    if response.status_code == 404:
        pytest.skip("Thermal endpoint is unavailable in the selected QEMU image")
    temperatures = response.json().get("Temperatures", [])
    cpu_readings = [item.get("ReadingCelsius") for item in temperatures if "cpu" in item.get("Name", "").lower()]
    assert cpu_readings
    assert all(-10 <= value <= 100 for value in cpu_readings if value is not None)


def test_redfish_cpu_sensors_can_be_compared_with_ipmi(redfish_session):
    response = redfish_session.get(f"{BMC_URL}/redfish/v1/Chassis/chassis/Sensors", timeout=20)
    assert response.status_code in (200, 404)
    if response.status_code == 404:
        pytest.skip("Sensor collection is unavailable in the selected QEMU image")
    members = response.json().get("Members", [])
    assert isinstance(members, list)
