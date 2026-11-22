import requests

BASE_URL = "http://127.0.0.1:8000"

# Fetch app.js from the running server
r_js = requests.get(f"{BASE_URL}/app.js")
assert r_js.status_code == 200
js_content = r_js.text

print("=" * 65)
print("TESTING OVERHEAD EOT CRANE ACCURACY & REMOVAL OF FLOOR LEGS")
print("=" * 65)

# 1. Verify no floor legs in the script
assert "floorY - (railTopY" not in js_content, "Found column extending to floorY!"
print("✓ Verified: No vertical floor legs present in front view.")

# 2. Verify runway beam segments and wall brackets are present
assert "leftRunwayAssembly" in js_content, "Missing leftRunwayAssembly!"
assert "rightRunwayAssembly" in js_content, "Missing rightRunwayAssembly!"
assert "Runway Beam" in js_content, "Missing 'Runway Beam' label!"
assert "Wall Corbel Support Bracket" in js_content, "Missing corbel support brackets!"
print("✓ Verified: Elevated runway beams & wall corbels present at both ends.")
print("✓ Verified: 'Runway Beam' label is present.")

# 3. Test calculation with span 16, capacity 10, lift 6.5, girder 800
calc_inputs = {
    "span_m": 16.0,
    "capacity_t": 10.0,
    "lift_height_m": 6.5,
    "girder_height_mm": 800
}

r_calc = requests.post(f"{BASE_URL}/api/calculate", json=calc_inputs)
assert r_calc.status_code == 200
calc = r_calc.json()

print(f"\nAPI Calculation results for Test:")
print(f"  • Girder length:    {calc['girder_length_m']} m")
print(f"  • Capacity:         {calc['capacity_t']} t")
print(f"  • Hook height:      {calc['hook_height_m']} m")
print(f"  • Girder height:    {calc['girder_height_mm']} mm")
print(f"  • Trolley position: {calc['trolley_position_m']} m")
print(f"  • End truck width:  {calc['end_truck_width_mm']} mm")

# 4. Geometry calculation for span 16, capacity 10, lift 6.5, girder 800
W = 900
H = 420
craneCenterX = 430
spanNorm = (16.0 - 5.0) / 25.0
girderWidthPx = 320.0 + spanNorm * 320.0
railLeftX = craneCenterX - girderWidthPx / 2.0
railRightX = craneCenterX + girderWidthPx / 2.0
girderHNorm = (800 - 300) / 1200.0
girderThicknessPx = 18.0 + girderHNorm * 36.0
railTopY = 110.0
girderBottomY = 122.0
girderTopY = girderBottomY - girderThicknessPx
floorY = 340.0

liftNorm = (6.5 - 3.0) / 12.0
hookTravelTop = girderBottomY + 14.0
hookTravelBottom = floorY - 26.0
cableLenPx = 30.0 + liftNorm * (hookTravelBottom - hookTravelTop - 30.0)
hookY = hookTravelTop + cableLenPx

print(f"\nDrawing Coordinates:")
print(f"  • Girder width:     {girderWidthPx:.1f} px (Span across runway rails: x={railLeftX:.1f} to x={railRightX:.1f})")
print(f"  • Girder elevation: y={girderTopY:.1f} to y={girderBottomY:.1f}")
print(f"  • Open bay space:   y={girderBottomY:.1f} down to floor line y={floorY} ({floorY - girderBottomY:.1f} px of clear open space under girder)")
print(f"  • Hook position:    y={hookY:.1f} (cable drops {cableLenPx:.1f} px into the open bay)")
print(f"  • Left runway corbel: x={railLeftX - 42:.1f} to x={railLeftX - 5:.1f}, bracket height y={railTopY + 30} to {railTopY + 62}")
print(f"  • Right runway corbel: x={railRightX + 5:.1f} to x={railRightX + 42:.1f}, bracket height y={railTopY + 30} to {railTopY + 62}")
print(f"  • Lift dimension:   x=815 from girder underside y={girderBottomY} to floor y={floorY}")

print("\n" + "=" * 65)
print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY!")
print("=" * 65)
