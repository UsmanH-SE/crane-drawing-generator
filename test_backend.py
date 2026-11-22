import json
import subprocess
import sys
import time
import requests

SERVER_URL = "http://127.0.0.1:8000"


def wait_for_server(timeout=10.0):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{SERVER_URL}/api/health", timeout=1)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.3)
    return False


def run_tests():
    print("=" * 60)
    print("PARAMETRIC OVERHEAD CRANE DRAWING GENERATOR - TEST SUITE")
    print("=" * 60)

    # 1. Health check
    print("\n[TEST 1] GET /api/health")
    res = requests.get(f"{SERVER_URL}/api/health")
    print(f"Status: {res.status_code}")
    print(f"Response: {json.dumps(res.json(), indent=2)}")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
    print("✓ Health check PASSED")

    # 2. Calculation endpoint - valid input
    print("\n[TEST 2] POST /api/calculate - Valid Drawing Inputs")
    calc_payload = {
        "span_m": 16.0,
        "capacity_t": 10.0,
        "lift_height_m": 6.5,
        "girder_height_mm": 800,
    }
    res = requests.post(f"{SERVER_URL}/api/calculate", json=calc_payload)
    print(f"Status: {res.status_code}")
    data = res.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    assert res.status_code == 200
    assert data["girder_length_m"] == 16.0
    assert data["hook_height_m"] == 6.5
    assert data["girder_height_mm"] == 800
    assert data["trolley_position_m"] == 8.0
    assert data["end_truck_width_mm"] == 800
    assert data["capacity_t"] == 10.0
    assert "notes" in data and len(data["notes"]) == 6
    print("✓ Calculate valid PASSED")

    # 3. Calculation endpoint - validation error (out of bounds span & capacity)
    print("\n[TEST 3] POST /api/calculate - Validation Error (span_m=2.0 < 5.0, capacity_t=25.0 > 20.0)")
    invalid_calc = {
        "span_m": 2.0,
        "capacity_t": 25.0,
        "lift_height_m": 6.5,
        "girder_height_mm": 800,
    }
    res = requests.post(f"{SERVER_URL}/api/calculate", json=invalid_calc)
    print(f"Status: {res.status_code}")
    print(f"Response: {json.dumps(res.json(), indent=2)}")
    assert res.status_code == 422
    print("✓ Calculate validation error PASSED (returned 422)")

    # 4. Create design
    print("\n[TEST 4] POST /api/designs - Create Design")
    design_payload = {
        "name": "Standard Workshop EOT Crane",
        "span_m": 18.5,
        "capacity_t": 5.0,
        "lift_height_m": 7.0,
        "girder_height_mm": 750,
    }
    res = requests.post(f"{SERVER_URL}/api/designs", json=design_payload)
    print(f"Status: {res.status_code}")
    design1 = res.json()
    print(f"Response: {json.dumps(design1, indent=2)}")
    assert res.status_code == 201
    assert "id" in design1
    assert design1["name"] == "Standard Workshop EOT Crane"
    design1_id = design1["id"]
    print(f"✓ Create design PASSED (Created id: {design1_id})")

    # 5. Create a second design to verify ordering
    print("\n[TEST 5] POST /api/designs - Create Second Design")
    design2_payload = {
        "name": "Heavy Foundry Crane",
        "span_m": 24.0,
        "capacity_t": 16.0,
        "lift_height_m": 12.0,
        "girder_height_mm": 1200,
    }
    time.sleep(0.1)
    res2 = requests.post(f"{SERVER_URL}/api/designs", json=design2_payload)
    design2 = res2.json()
    print(f"Status: {res2.status_code}")
    print(f"Response: {json.dumps(design2, indent=2)}")
    assert res2.status_code == 201
    design2_id = design2["id"]
    print(f"✓ Create second design PASSED (Created id: {design2_id})")

    # 6. List all designs (newest first)
    print("\n[TEST 6] GET /api/designs - List All Designs (Newest First)")
    res = requests.get(f"{SERVER_URL}/api/designs")
    print(f"Status: {res.status_code}")
    designs_list = res.json()
    print(f"Total designs count: {len(designs_list)}")
    print(f"First in list (newest): id={designs_list[0]['id']} name='{designs_list[0]['name']}'")
    assert res.status_code == 200
    assert len(designs_list) >= 2
    assert designs_list[0]["id"] == design2_id  # Most recent first
    print("✓ List designs PASSED (sorted newest first)")

    # 7. Get design by ID
    print(f"\n[TEST 7] GET /api/designs/{design1_id} - Get Specific Design")
    res = requests.get(f"{SERVER_URL}/api/designs/{design1_id}")
    print(f"Status: {res.status_code}")
    print(f"Response: {json.dumps(res.json(), indent=2)}")
    assert res.status_code == 200
    assert res.json()["id"] == design1_id
    print("✓ Get design by ID PASSED")

    # 8. Get non-existent design
    print("\n[TEST 8] GET /api/designs/99999 - Non-existent ID (404 expected)")
    res = requests.get(f"{SERVER_URL}/api/designs/99999")
    print(f"Status: {res.status_code}")
    print(f"Response: {json.dumps(res.json(), indent=2)}")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()
    print("✓ 404 on missing design PASSED")

    # 9. Update design
    print(f"\n[TEST 9] PUT /api/designs/{design1_id} - Update Design")
    update_payload = {
        "name": "Standard Workshop EOT Crane - Upgraded",
        "span_m": 20.0,
        "capacity_t": 7.5,
        "lift_height_m": 8.0,
        "girder_height_mm": 850,
    }
    res = requests.put(f"{SERVER_URL}/api/designs/{design1_id}", json=update_payload)
    print(f"Status: {res.status_code}")
    updated = res.json()
    print(f"Response: {json.dumps(updated, indent=2)}")
    assert res.status_code == 200
    assert updated["name"] == "Standard Workshop EOT Crane - Upgraded"
    assert updated["span_m"] == 20.0
    assert updated["capacity_t"] == 7.5
    print("✓ Update design PASSED")

    # 10. Update non-existent design
    print("\n[TEST 10] PUT /api/designs/99999 - Non-existent ID (404 expected)")
    res = requests.put(f"{SERVER_URL}/api/designs/99999", json=update_payload)
    print(f"Status: {res.status_code}")
    print(f"Response: {json.dumps(res.json(), indent=2)}")
    assert res.status_code == 404
    print("✓ 404 on updating missing design PASSED")

    # 11. Validation error on Create Design (e.g. empty name, girder_height_mm < 300)
    print("\n[TEST 11] POST /api/designs - Validation Error (Empty Name & girder_height_mm=200)")
    invalid_design = {
        "name": "   ",
        "span_m": 15.0,
        "capacity_t": 5.0,
        "lift_height_m": 5.0,
        "girder_height_mm": 200,
    }
    res = requests.post(f"{SERVER_URL}/api/designs", json=invalid_design)
    print(f"Status: {res.status_code}")
    print(f"Response: {json.dumps(res.json(), indent=2)}")
    assert res.status_code == 422
    print("✓ Validation error on create design PASSED (returned 422 with field errors)")

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000", "--log-level", "warning"]
    )

    try:
        if not wait_for_server(timeout=10.0):
            print("ERROR: Server failed to start within timeout", file=sys.stderr)
            sys.exit(1)
        run_tests()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
