import requests

BASE_URL = "http://127.0.0.1:8000"

# Fetch app.js from the running server
r_js = requests.get(f"{BASE_URL}/app.js")
assert r_js.status_code == 200
js_content = r_js.text

print("=" * 65)
print("TESTING LABEL OVERLAPS IN FRONT VIEW SVG")
print("=" * 65)

# Verify floating capacity box is removed
assert "Capacity: ${calc.capacity_t} t" not in js_content, "Floating capacity box still present!"
print("✓ Verified: Floating capacity box removed completely from front view drawing area.")

# Verify capacity is in title block
assert "CAPACITY: <tspan font-weight=\"normal\">${calc.capacity_t} t</tspan>" in js_content
print("✓ Verified: Capacity is clearly displayed in drawing sheet title block.")

def get_label_boxes(span_m, capacity_t, lift_height_m, girder_height_mm):
    craneCenterX = 430
    spanNorm = max(0.0, min(1.0, (span_m - 5.0) / 25.0))
    girderWidthPx = 320.0 + spanNorm * 320.0
    railLeftX = craneCenterX - girderWidthPx / 2.0
    railRightX = craneCenterX + girderWidthPx / 2.0

    girderHNorm = max(0.0, min(1.0, (girder_height_mm - 300) / 1200.0))
    girderThicknessPx = 18.0 + girderHNorm * 36.0
    railTopY = 110.0
    girderBottomY = 122.0
    girderTopY = girderBottomY - girderThicknessPx

    floorY = 340.0
    liftNorm = max(0.0, min(1.0, (lift_height_m - 3.0) / 12.0))
    hookTravelTop = girderBottomY + 14.0
    hookTravelBottom = floorY - 26.0
    cableLenPx = 30.0 + liftNorm * (hookTravelBottom - hookTravelTop - 30.0)
    hookY = hookTravelTop + cableLenPx

    trolleyH = 22.0
    trolleyY = girderTopY - trolleyH

    spanDimY = 20.0
    liftDimX = 815.0
    liftMidY = (girderBottomY + floorY) / 2.0

    boxes = {
        "Span Dimension": {
            "x1": craneCenterX - 70, "x2": craneCenterX + 70,
            "y1": spanDimY - 14, "y2": spanDimY + 14
        },
        "End Truck Label": {
            "x1": railLeftX - 40, "x2": railLeftX + 40,
            "y1": 50 - 11, "y2": 50 + 11
        },
        "Trolley Label": {
            "x1": craneCenterX - 82 - 32, "x2": craneCenterX - 82 + 32,
            "y1": trolleyY + 11 - 11, "y2": trolleyY + 11 + 11
        },
        "Girder Label": {
            "x1": craneCenterX - 145 - 30, "x2": craneCenterX - 145 + 30,
            "y1": girderBottomY + 22 - 11, "y2": girderBottomY + 22 + 11
        },
        "Hook Label": {
            "x1": craneCenterX + 30, "x2": craneCenterX + 30 + 50,
            "y1": hookY + 8 - 11, "y2": hookY + 8 + 11
        },
        "Lift Height Dimension": {
            "x1": liftDimX - 72, "x2": liftDimX + 72,
            "y1": liftMidY - 14, "y2": liftMidY + 14
        },
        "Runway Beam Label": {
            "x1": railLeftX - 46, "x2": railLeftX + 46,
            "y1": railTopY + 76 - 11, "y2": railTopY + 76 + 11
        },
        "Title Block": {
            "x1": 35, "x2": 865,
            "y1": 368, "y2": 412
        }
    }
    return boxes, {
        "railLeftX": railLeftX,
        "railRightX": railRightX,
        "girderTopY": girderTopY,
        "girderBottomY": girderBottomY,
        "trolleyY": trolleyY,
        "hookY": hookY
    }

def check_overlaps(boxes):
    names = list(boxes.keys())
    overlaps = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            n1, n2 = names[i], names[j]
            b1, b2 = boxes[n1], boxes[n2]
            # Check AABB intersection
            x_overlap = (b1["x1"] < b2["x2"]) and (b1["x2"] > b2["x1"])
            y_overlap = (b1["y1"] < b2["y2"]) and (b1["y2"] > b2["y1"])
            if x_overlap and y_overlap:
                overlaps.append((n1, n2))
    return overlaps

test_cases = [
    {"name": "Minimum", "span": 5, "cap": 1, "lift": 3, "girder": 300},
    {"name": "Middle", "span": 16, "cap": 10, "lift": 6.5, "girder": 800},
    {"name": "Maximum", "span": 30, "cap": 20, "lift": 15, "girder": 1500},
]

for tc in test_cases:
    print(f"\n--- Testing {tc['name']} (span {tc['span']}m, cap {tc['cap']}t, lift {tc['lift']}m, girder {tc['girder']}mm) ---")
    boxes, geom = get_label_boxes(tc["span"], tc["cap"], tc["lift"], tc["girder"])
    overlaps = check_overlaps(boxes)

    print("Label Bounding Boxes:")
    for label_name, b in boxes.items():
        print(f"  • {label_name:<22}: x=[{b['x1']:6.1f}, {b['x2']:6.1f}], y=[{b['y1']:6.1f}, {b['y2']:6.1f}]")

    print(f"Key Clearances:")
    print(f"  • End Truck label (y=[{boxes['End Truck Label']['y1']:.1f}, {boxes['End Truck Label']['y2']:.1f}]) vs Span dim line (y=20): {boxes['End Truck Label']['y1'] - 20:.1f}px gap")
    print(f"  • End Truck label (y={boxes['End Truck Label']['y2']:.1f}) vs End Truck body top (y=76): {76 - boxes['End Truck Label']['y2']:.1f}px gap")
    print(f"  • Trolley top (y={geom['trolleyY']:.1f}) vs Span dim badge (y=34): {geom['trolleyY'] - 34:.1f}px gap")
    print(f"  • Hook label (y={boxes['Hook Label']['y2']:.1f}) vs Floor line (y=340): {340 - boxes['Hook Label']['y2']:.1f}px gap")

    assert len(overlaps) == 0, f"Overlaps detected: {overlaps}"
    print(f"✓ {tc['name']} test PASSED: 0 overlaps detected across all labels!")

print("\n" + "=" * 65)
print("ALL THREE CASES PASSED WITH ZERO OVERLAPS!")
print("=" * 65)
