import json
import requests

BASE_URL = "http://127.0.0.1:8000"

print("=" * 60)
print("FRONTEND INTEGRATION & SERVER TEST SUITE")
print("=" * 60)

# 1. Test Static files served at root
print("\n[1] GET / (Root HTML)")
r = requests.get(BASE_URL + "/")
print(f"Status: {r.status_code}")
assert r.status_code == 200
assert "Parametric Overhead Crane Drawing Generator" in r.text
assert "Single girder EOT crane concept drawing tool" in r.text
assert "frontViewSvg" in r.text
assert "sideViewSvg" in r.text
assert "notesList" in r.text
assert "designsTableBody" in r.text
print("✓ Root index.html successfully served with all UI components")

# 2. Test CSS and JS static files
print("\n[2] GET /style.css and /app.js")
r_css = requests.get(BASE_URL + "/style.css")
r_js = requests.get(BASE_URL + "/app.js")
assert r_css.status_code == 200
assert r_js.status_code == 200
assert "(estimate)" in r_js.text
print(f"✓ style.css ({len(r_css.text)} bytes) and app.js ({len(r_js.text)} bytes) served OK, (estimate) verified in SVG renderer")

# 3. Test recalculation on input change
print("\n[3] Testing calculation on input change (span: 25m, girder_height: 1200mm)")
payload = {
    "span_m": 25.0,
    "capacity_t": 15.0,
    "lift_height_m": 10.0,
    "girder_height_mm": 1200
}
r_calc = requests.post(BASE_URL + "/api/calculate", json=payload)
print(f"Status: {r_calc.status_code}")
calc_res = r_calc.json()
print(f"Calculated drawing values:\n{json.dumps(calc_res, indent=2)}")
assert r_calc.status_code == 200
assert calc_res["girder_length_m"] == 25.0
assert calc_res["trolley_position_m"] == 12.5
assert calc_res["end_truck_width_mm"] == 800
assert "estimate: fixed placeholder value" in calc_res["end_truck_width_note"]
print("✓ Dynamic calculation returned correct dimensions and notes")

# 4. Test Save Design
print("\n[4] Testing Save Design (POST /api/designs)")
save_payload = {
    "name": "Assembly Bay Gantry Crane",
    "span_m": 20.0,
    "capacity_t": 12.0,
    "lift_height_m": 8.0,
    "girder_height_mm": 950
}
r_save = requests.post(BASE_URL + "/api/designs", json=save_payload)
print(f"Status: {r_save.status_code}")
saved_design = r_save.json()
print(f"Saved design:\n{json.dumps(saved_design, indent=2)}")
assert r_save.status_code == 201
saved_id = saved_design["id"]
print(f"✓ Design saved with ID #{saved_id}")

# 5. Test List Designs (shows new design)
print("\n[5] Testing List Designs (GET /api/designs)")
r_list = requests.get(BASE_URL + "/api/designs")
designs = r_list.json()
print(f"Found {len(designs)} saved designs. Most recent: id={designs[0]['id']} name='{designs[0]['name']}'")
assert any(d["id"] == saved_id for d in designs)
print("✓ Saved design appears in list")

# 6. Test Open Design
print(f"\n[6] Testing Open Design (GET /api/designs/{saved_id})")
r_open = requests.get(f"{BASE_URL}/api/designs/{saved_id}")
opened = r_open.json()
print(f"Opened design:\n{json.dumps(opened, indent=2)}")
assert opened["id"] == saved_id
assert opened["name"] == "Assembly Bay Gantry Crane"
assert opened["span_m"] == 20.0
print("✓ Successfully fetched design for opening")

# 7. Test Update Design
print(f"\n[7] Testing Update Design (PUT /api/designs/{saved_id})")
update_payload = {
    "name": "Assembly Bay Gantry Crane - Rev A",
    "span_m": 22.0,
    "capacity_t": 12.0,
    "lift_height_m": 8.5,
    "girder_height_mm": 1000
}
r_update = requests.put(f"{BASE_URL}/api/designs/{saved_id}", json=update_payload)
print(f"Status: {r_update.status_code}")
updated = r_update.json()
print(f"Updated design:\n{json.dumps(updated, indent=2)}")
assert updated["name"] == "Assembly Bay Gantry Crane - Rev A"
assert updated["span_m"] == 22.0
print("✓ Successfully updated design")

# 8. Test Invalid Input (Span = 2)
print("\n[8] Testing Invalid Input Validation (span_m: 2.0, allowed 5 to 30)")
invalid_payload = {
    "span_m": 2.0,
    "capacity_t": 10.0,
    "lift_height_m": 6.5,
    "girder_height_mm": 800
}
r_invalid = requests.post(BASE_URL + "/api/calculate", json=invalid_payload)
print(f"Status: {r_invalid.status_code}")
err_data = r_invalid.json()
print(f"Validation error response:\n{json.dumps(err_data, indent=2)}")
assert r_invalid.status_code == 422
assert "greater than or equal to 5" in str(err_data)
print("✓ 422 validation error returned with clear field details")

print("\n" + "=" * 60)
print("ALL INTEGRATION TESTS PASSED!")
print("=" * 60)
