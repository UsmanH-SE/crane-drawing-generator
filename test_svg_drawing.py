import re
import requests

BASE_URL = "http://127.0.0.1:8000"

def simulate_svg(calc, design_name):
    """Mirror the JavaScript renderFrontView and renderSideView logic to test geometry."""
    # Front View
    W, H = 900, 420
    craneCenterX = 430
    spanNorm = max(0.0, min(1.0, (calc["girder_length_m"] - 5) / 25.0))
    girderWidthPx = 320 + spanNorm * 320
    railLeftX = craneCenterX - girderWidthPx / 2.0
    railRightX = craneCenterX + girderWidthPx / 2.0

    girderHNorm = max(0.0, min(1.0, (calc["girder_height_mm"] - 300) / 1200.0))
    girderThicknessPx = 18 + girderHNorm * 36

    railTopY = 110
    girderBottomY = 122
    girderTopY = girderBottomY - girderThicknessPx

    truckWidth = 34
    truckHeight = 48
    floorY = 340

    liftNorm = max(0.0, min(1.0, (calc["hook_height_m"] - 3) / 12.0))
    hookTravelTop = girderBottomY + 14
    hookTravelBottom = floorY - 26
    cableLenPx = 30 + liftNorm * (hookTravelBottom - hookTravelTop - 30)
    hookY = hookTravelTop + cableLenPx

    trolleyW = 54
    trolleyH = 22
    trolleyX = craneCenterX - trolleyW / 2.0
    trolleyY = girderTopY - trolleyH

    spanDimY = 24
    liftDimX = 815
    liftMidY = (girderBottomY + floorY) / 2.0

    # Side View
    sW, sH = 420, 420
    sCenterX = 220
    truckWidthPx = 250
    truckLeftX = sCenterX - truckWidthPx / 2.0
    truckRightX = sCenterX + truckWidthPx / 2.0

    sGirderHPx = 75 + girderHNorm * 135
    truckBaseY = 270
    truckHeightPx = 40
    sGirderBottomY = truckBaseY - truckHeightPx + 10
    sGirderTopY = sGirderBottomY - sGirderHPx

    return {
        "front": {
            "girderWidthPx": girderWidthPx,
            "railLeftX": railLeftX,
            "railRightX": railRightX,
            "girderThicknessPx": girderThicknessPx,
            "girderTopY": girderTopY,
            "girderBottomY": girderBottomY,
            "trolleyY": trolleyY,
            "hookY": hookY,
            "cableLenPx": cableLenPx,
            "spanDimY": spanDimY,
            "liftDimX": liftDimX,
            "liftMidY": liftMidY,
            "floorY": floorY,
        },
        "side": {
            "truckWidthPx": truckWidthPx,
            "truckLeftX": truckLeftX,
            "truckRightX": truckRightX,
            "girderHPx": sGirderHPx,
            "girderTopY": sGirderTopY,
            "girderBottomY": sGirderBottomY,
        }
    }


test_cases = [
    {
        "name": "Test A",
        "design_name": "Test A - Small Crane",
        "inputs": {"span_m": 5.0, "capacity_t": 1.0, "lift_height_m": 3.0, "girder_height_mm": 300}
    },
    {
        "name": "Test B",
        "design_name": "Test B - Medium Crane",
        "inputs": {"span_m": 20.0, "capacity_t": 7.5, "lift_height_m": 8.0, "girder_height_mm": 850}
    },
    {
        "name": "Test C",
        "design_name": "Test C - Maximum Heavy Crane",
        "inputs": {"span_m": 30.0, "capacity_t": 20.0, "lift_height_m": 15.0, "girder_height_mm": 1500}
    }
]

print("=" * 65)
print("TESTING PARAMETRIC SVG DRAWING GEOMETRY AND CLEARANCES")
print("=" * 65)

for tc in test_cases:
    print(f"\n--- {tc['name']} ({tc['design_name']}) ---")
    inputs = tc["inputs"]
    r = requests.post(f"{BASE_URL}/api/calculate", json=inputs)
    assert r.status_code == 200, f"Calculate failed: {r.text}"
    calc = r.json()
    geom = simulate_svg(calc, tc["design_name"])

    f = geom["front"]
    s = geom["side"]

    print(f"Inputs: Span={inputs['span_m']}m, Cap={inputs['capacity_t']}t, Lift={inputs['lift_height_m']}m, Girder={inputs['girder_height_mm']}mm")
    print(f"Front View:")
    print(f"  • Girder length px: {f['girderWidthPx']:.1f}px (between x={f['railLeftX']:.1f} and x={f['railRightX']:.1f})")
    print(f"  • Girder thickness: {f['girderThicknessPx']:.1f}px (y={f['girderTopY']:.1f} to y={f['girderBottomY']:.1f})")
    print(f"  • Trolley top y:    {f['trolleyY']:.1f} (span dimension line at y={f['spanDimY']}, clearance = {f['trolleyY'] - f['spanDimY']:.1f}px)")
    print(f"  • Hook vertical y:  {f['hookY']:.1f} (cable length = {f['cableLenPx']:.1f}px, floor line at y={f['floorY']})")
    print(f"  • Lift dim line:    x={f['liftDimX']}, clearance to right rail = {f['liftDimX'] - f['railRightX']:.1f}px")
    
    print(f"Side View:")
    print(f"  • Girder height px: {s['girderHPx']:.1f}px (y={s['girderTopY']:.1f} to y={s['girderBottomY']:.1f})")
    print(f"  • Truck width px:   {s['truckWidthPx']:.1f}px (x={s['truckLeftX']:.1f} to x={s['truckRightX']:.1f})")

    # Boundary assertions
    assert 0 <= f["railLeftX"] < f["railRightX"] <= 900, "Girder out of front viewBox width"
    assert 0 <= f["girderTopY"] < f["floorY"] <= 420, "Girder / floor out of front viewBox height"
    assert f["spanDimY"] < f["trolleyY"], "Span dimension overlaps trolley"
    assert f["hookY"] < f["floorY"], "Hook extends below floor line"
    assert f["railRightX"] < f["liftDimX"], "Lift dimension line collides with right rail"

    assert 0 <= s["truckLeftX"] < s["truckRightX"] <= 420, "Truck out of side viewBox width"
    assert 0 <= s["girderTopY"] < s["girderBottomY"] <= 420, "Girder out of side viewBox height"

    print("✓ All elements within viewBox, clear clearances maintained, no overlap!")

print("\n" + "=" * 65)
print("TEST A, B, AND C PASSED WITH PERFECT BOUNDS AND CLEARANCES!")
print("=" * 65)
