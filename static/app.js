/**
 * Parametric Overhead Crane Drawing Generator - Frontend
 * Interacts with FastAPI backend:
 * - POST /api/calculate (Live SVG drawing calculations)
 * - POST /api/designs (Save new crane design)
 * - GET  /api/designs (Fetch saved designs)
 * - GET  /api/designs/{id} (Fetch single design)
 * - PUT  /api/designs/{id} (Update existing design)
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const craneForm = document.getElementById("craneForm");
  const inputName = document.getElementById("inputName");
  const inputSpan = document.getElementById("inputSpan");
  const inputCapacity = document.getElementById("inputCapacity");
  const inputLiftHeight = document.getElementById("inputLiftHeight");
  const inputGirderHeight = document.getElementById("inputGirderHeight");

  const btnSave = document.getElementById("btnSave");
  const btnUpdate = document.getElementById("btnUpdate");
  const btnReset = document.getElementById("btnReset");
  const btnRefresh = document.getElementById("btnRefresh");

  const activeBadge = document.getElementById("activeBadge");
  const errorArea = document.getElementById("errorArea");
  const successArea = document.getElementById("successArea");

  const frontViewSvg = document.getElementById("frontViewSvg");
  const sideViewSvg = document.getElementById("sideViewSvg");
  const notesList = document.getElementById("notesList");
  const designsTableBody = document.getElementById("designsTableBody");

  // Application State
  let activeDesignId = null;
  let calculationDebounceTimer = null;

  // Utilities
  function showSuccess(msg) {
    successArea.textContent = msg;
    successArea.style.display = "block";
    errorArea.style.display = "none";
    setTimeout(() => {
      successArea.style.display = "none";
    }, 4500);
  }

  function showError(messages) {
    if (Array.isArray(messages)) {
      if (messages.length === 1) {
        errorArea.textContent = messages[0];
      } else {
        errorArea.innerHTML = "<strong>Validation Errors:</strong><ul>" +
          messages.map(m => `<li>${escapeHtml(m)}</li>`).join("") +
          "</ul>";
      }
    } else {
      errorArea.textContent = messages;
    }
    errorArea.style.display = "block";
    successArea.style.display = "none";
  }

  function clearError() {
    errorArea.style.display = "none";
    errorArea.textContent = "";
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function parseValidationErrors(errorData) {
    if (!errorData || !errorData.detail) {
      return ["An unexpected error occurred."];
    }
    if (typeof errorData.detail === "string") {
      return [errorData.detail];
    }
    if (Array.isArray(errorData.detail)) {
      return errorData.detail.map(item => {
        const field = item.loc && item.loc.length > 1 ? item.loc.slice(1).join(".") : "input";
        return `${field}: ${item.msg}`;
      });
    }
    return [JSON.stringify(errorData.detail)];
  }

  function getFormValues() {
    return {
      name: inputName.value.trim(),
      span_m: parseFloat(inputSpan.value),
      capacity_t: parseFloat(inputCapacity.value),
      lift_height_m: parseFloat(inputLiftHeight.value),
      girder_height_mm: parseInt(inputGirderHeight.value, 10),
    };
  }

  // --- API CALL: Calculate Dimensions & Redraw ---
  async function triggerCalculation() {
    clearError();
    const values = getFormValues();

    // Client check before sending to avoid unnecessary NaN calls
    if (isNaN(values.span_m) || isNaN(values.capacity_t) || isNaN(values.lift_height_m) || isNaN(values.girder_height_mm)) {
      showError("Please enter valid numerical values for all dimension fields.");
      return;
    }

    try {
      const response = await fetch("/api/calculate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          span_m: values.span_m,
          capacity_t: values.capacity_t,
          lift_height_m: values.lift_height_m,
          girder_height_mm: values.girder_height_mm,
        }),
      });

      if (!response.ok) {
        const errJson = await response.json();
        showError(parseValidationErrors(errJson));
        return;
      }

      const calcData = await response.json();
      renderFrontView(calcData);
      renderSideView(calcData);
      renderNotes(calcData.notes);
    } catch (err) {
      showError(`Network error while calculating: ${err.message}`);
    }
  }

  function onInputChanged() {
    if (calculationDebounceTimer) {
      clearTimeout(calculationDebounceTimer);
    }
    calculationDebounceTimer = setTimeout(() => {
      triggerCalculation();
    }, 280);
  }

  // Bind input listeners
  [inputSpan, inputCapacity, inputLiftHeight, inputGirderHeight].forEach(input => {
    input.addEventListener("input", onInputChanged);
  });

  // --- SVG Renderers ---

  function createMarkerDefs() {
    return `
      <defs>
        <marker id="arrow-start" viewBox="0 0 10 10" refX="2" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M 10 1.5 L 1 5 L 10 8.5 z" fill="#1f3a5f" />
        </marker>
        <marker id="arrow-end" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">
          <path d="M 0 1.5 L 9 5 L 0 8.5 z" fill="#1f3a5f" />
        </marker>
        <pattern id="ground-hatch" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <line x1="0" y1="0" x2="0" y2="10" stroke="#cbd5e1" stroke-width="1.5" />
        </pattern>
      </defs>
    `;
  }

  function renderFrontView(calc) {
    const W = 900;
    const H = 420;
    const craneCenterX = 430; // Centered with clearance on right for lift dimension line
    const designName = inputName.value.trim() || "Overhead Crane Concept";

    // Parametric scaling
    // Span: 5 to 30 m -> pixel width 320 to 640
    const spanNorm = Math.max(0, Math.min(1, (calc.girder_length_m - 5) / (30 - 5)));
    const girderWidthPx = 320 + spanNorm * 320;
    const railLeftX = craneCenterX - girderWidthPx / 2;
    const railRightX = craneCenterX + girderWidthPx / 2;

    // Girder Height: 300 to 1500 mm -> thickness 18 to 54 px
    const girderHNorm = Math.max(0, Math.min(1, (calc.girder_height_mm - 300) / (1500 - 300)));
    const girderThicknessPx = 18 + girderHNorm * 36;

    const railTopY = 110;
    const girderBottomY = 122;
    const girderTopY = girderBottomY - girderThicknessPx;

    const truckWidth = 34;
    const truckHeight = 48;
    const floorY = 340;

    // Lift Height: 3 to 15 m -> hook vertical position down toward floor
    const liftNorm = Math.max(0, Math.min(1, (calc.hook_height_m - 3) / (15 - 3)));
    const hookTravelTop = girderBottomY + 14;
    const hookTravelBottom = floorY - 26;
    const cableLenPx = 30 + liftNorm * (hookTravelBottom - hookTravelTop - 30);
    const hookY = hookTravelTop + cableLenPx;

    // Trolley positioned at span centre
    const trolleyW = 54;
    const trolleyH = 22;
    const trolleyX = craneCenterX - trolleyW / 2;
    const trolleyY = girderTopY - trolleyH;

    // Dimension lines
    const spanDimY = 20;
    const liftDimX = 815;
    const liftMidY = (girderBottomY + floorY) / 2;

    frontViewSvg.innerHTML = `
      ${createMarkerDefs()}
      <rect width="${W}" height="${H}" class="svg-bg" />

      <!-- Runway Beams & Wall Brackets (Elevated, No Legs to Floor) -->
      <!-- Left Runway Beam & Wall Corbel Bracket -->
      <g id="leftRunwayAssembly">
        <!-- Wall Backing Plate & Hatching -->
        <line x1="${railLeftX - 50}" y1="${railTopY + 16}" x2="${railLeftX - 58}" y2="${railTopY + 8}" stroke="#94a3b8" stroke-width="1.2" />
        <line x1="${railLeftX - 50}" y1="${railTopY + 36}" x2="${railLeftX - 58}" y2="${railTopY + 28}" stroke="#94a3b8" stroke-width="1.2" />
        <line x1="${railLeftX - 50}" y1="${railTopY + 56}" x2="${railLeftX - 58}" y2="${railTopY + 48}" stroke="#94a3b8" stroke-width="1.2" />
        <rect x="${railLeftX - 50}" y="${railTopY + 6}" width="8" height="60" fill="#64748b" stroke="#334155" stroke-width="1" />

        <!-- Wall Corbel Support Bracket -->
        <polygon points="${railLeftX - 42},${railTopY + 30} ${railLeftX - 5},${railTopY + 30} ${railLeftX - 42},${railTopY + 62}" fill="#cbd5e1" stroke="#475569" stroke-width="1.5" />

        <!-- Elevated Runway Beam Segment -->
        <rect x="${railLeftX - 42}" y="${railTopY + 12}" width="84" height="18" fill="#94a3b8" stroke="#475569" stroke-width="1.5" rx="1" />
        
        <!-- Rail Head Segment on Runway Beam -->
        <rect x="${railLeftX - 35}" y="${railTopY}" width="70" height="12" class="svg-rail" rx="1" />

        <!-- Runway Beam Callout Label -->
        <g transform="translate(${railLeftX}, ${railTopY + 76})">
          <rect x="-46" y="-11" width="92" height="22" rx="3" fill="#ffffff" stroke="#5a6b7d" stroke-width="1.2" />
          <text x="0" y="4" font-size="11" font-weight="600" fill="#1f3a5f" text-anchor="middle">Runway Beam</text>
          <line x1="0" y1="-11" x2="0" y2="-44" stroke="#5a6b7d" stroke-width="1.2" />
        </g>
      </g>

      <!-- Right Runway Beam & Wall Corbel Bracket -->
      <g id="rightRunwayAssembly">
        <!-- Wall Backing Plate & Hatching -->
        <line x1="${railRightX + 50}" y1="${railTopY + 8}" x2="${railRightX + 58}" y2="${railTopY + 16}" stroke="#94a3b8" stroke-width="1.2" />
        <line x1="${railRightX + 50}" y1="${railTopY + 28}" x2="${railRightX + 58}" y2="${railTopY + 36}" stroke="#94a3b8" stroke-width="1.2" />
        <line x1="${railRightX + 50}" y1="${railTopY + 48}" x2="${railRightX + 58}" y2="${railTopY + 56}" stroke="#94a3b8" stroke-width="1.2" />
        <rect x="${railRightX + 42}" y="${railTopY + 6}" width="8" height="60" fill="#64748b" stroke="#334155" stroke-width="1" />

        <!-- Wall Corbel Support Bracket -->
        <polygon points="${railRightX + 5},${railTopY + 30} ${railRightX + 42},${railTopY + 30} ${railRightX + 42},${railTopY + 62}" fill="#cbd5e1" stroke="#475569" stroke-width="1.5" />

        <!-- Elevated Runway Beam Segment -->
        <rect x="${railRightX - 42}" y="${railTopY + 12}" width="84" height="18" fill="#94a3b8" stroke="#475569" stroke-width="1.5" rx="1" />

        <!-- Rail Head Segment on Runway Beam -->
        <rect x="${railRightX - 35}" y="${railTopY}" width="70" height="12" class="svg-rail" rx="1" />
      </g>

      <!-- End Trucks -->
      <rect x="${railLeftX - truckWidth / 2}" y="${railTopY - truckHeight + 14}" width="${truckWidth}" height="${truckHeight}" rx="2" class="svg-end-truck" />
      <circle cx="${railLeftX - 8}" cy="${railTopY + 6}" r="5" class="svg-wheel" />
      <circle cx="${railLeftX + 8}" cy="${railTopY + 6}" r="5" class="svg-wheel" />

      <rect x="${railRightX - truckWidth / 2}" y="${railTopY - truckHeight + 14}" width="${truckWidth}" height="${truckHeight}" rx="2" class="svg-end-truck" />
      <circle cx="${railRightX - 8}" cy="${railTopY + 6}" r="5" class="svg-wheel" />
      <circle cx="${railRightX + 8}" cy="${railTopY + 6}" r="5" class="svg-wheel" />

      <!-- Main Girder Beam across the span -->
      <rect x="${railLeftX}" y="${girderTopY}" width="${girderWidthPx}" height="${girderThicknessPx}" rx="1" class="svg-girder" />

      <!-- Trolley (centered at span/2) -->
      <rect x="${trolleyX}" y="${trolleyY}" width="${trolleyW}" height="${trolleyH}" rx="3" class="svg-trolley" />
      <circle cx="${trolleyX + 12}" cy="${girderTopY}" r="4.5" class="svg-wheel" />
      <circle cx="${trolleyX + trolleyW - 12}" cy="${girderTopY}" r="4.5" class="svg-wheel" />

      <!-- Hoist Cable / Rope -->
      <line x1="${craneCenterX}" y1="${girderTopY}" x2="${craneCenterX}" y2="${hookY}" class="svg-wire" />

      <!-- Hook assembly -->
      <g transform="translate(${craneCenterX}, ${hookY})">
        <circle cx="0" cy="0" r="6" fill="#475569" stroke="#1f3a5f" stroke-width="1.5" />
        <path d="M 0 6 C 0 18 -14 18 -14 9 C -14 4.5 -8 3.5 -5 7" class="svg-hook" />
      </g>

      <!-- Floor / Ground Line & Hatching -->
      <rect x="35" y="${floorY}" width="830" height="20" fill="url(#ground-hatch)" />
      <line x1="35" y1="${floorY}" x2="865" y2="${floorY}" stroke="#1f3a5f" stroke-width="2.5" />
      <text x="45" y="${floorY - 6}" font-size="11" font-weight="bold" fill="#64748b" letter-spacing="0.5">FLOOR / GROUND LEVEL</text>

      <!-- Part Labels (with clear space outside shapes) -->
      <!-- End Truck Label -->
      <g transform="translate(${railLeftX}, 50)">
        <rect x="-40" y="-11" width="80" height="22" rx="3" fill="#ffffff" stroke="#5a6b7d" stroke-width="1.2" />
        <text x="0" y="4" font-size="11" font-weight="600" fill="#1f3a5f" text-anchor="middle">End Truck</text>
        <line x1="0" y1="11" x2="0" y2="24" stroke="#5a6b7d" stroke-width="1.2" />
      </g>

      <!-- Trolley Label -->
      <g transform="translate(${craneCenterX - 82}, ${trolleyY + 11})">
        <rect x="-32" y="-11" width="64" height="22" rx="3" fill="#ffffff" stroke="#5a6b7d" stroke-width="1.2" />
        <text x="0" y="4" font-size="11" font-weight="600" fill="#1f3a5f" text-anchor="middle">Trolley</text>
        <line x1="32" y1="0" x2="52" y2="0" stroke="#5a6b7d" stroke-width="1.2" />
      </g>

      <!-- Girder Label -->
      <g transform="translate(${craneCenterX - 145}, ${girderBottomY + 22})">
        <rect x="-30" y="-11" width="60" height="22" rx="3" fill="#ffffff" stroke="#5a6b7d" stroke-width="1.2" />
        <text x="0" y="4" font-size="11" font-weight="600" fill="#1f3a5f" text-anchor="middle">Girder</text>
        <line x1="0" y1="-11" x2="0" y2="-17" stroke="#5a6b7d" stroke-width="1.2" />
      </g>

      <!-- Hook Label -->
      <g transform="translate(${craneCenterX + 30}, ${hookY + 8})">
        <rect x="0" y="-11" width="50" height="22" rx="3" fill="#ffffff" stroke="#5a6b7d" stroke-width="1.2" />
        <text x="25" y="4" font-size="11" font-weight="600" fill="#1f3a5f" text-anchor="middle">Hook</text>
        <line x1="0" y1="0" x2="-10" y2="0" stroke="#5a6b7d" stroke-width="1.2" />
      </g>

      <!-- Span Dimension Line & Extension Lines (Above Girder) -->
      <line x1="${railLeftX}" y1="${spanDimY}" x2="${railRightX}" y2="${spanDimY}" class="svg-dim-line" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)" stroke-width="1.5" />
      <line x1="${railLeftX}" y1="${spanDimY - 8}" x2="${railLeftX}" y2="${railTopY}" class="svg-ext-line" stroke-width="1.2" />
      <line x1="${railRightX}" y1="${spanDimY - 8}" x2="${railRightX}" y2="${railTopY}" class="svg-ext-line" stroke-width="1.2" />
      <g transform="translate(${craneCenterX}, ${spanDimY})">
        <rect x="-70" y="-14" width="140" height="28" rx="4" fill="#ffffff" stroke="#1f3a5f" stroke-width="1.5" />
        <text x="0" y="5" font-size="13.5" font-weight="bold" fill="#1f3a5f" text-anchor="middle">Span: ${calc.girder_length_m} m</text>
      </g>

      <!-- Lift Height Dimension Line & Extension Lines (Right side down to floor) -->
      <line x1="${liftDimX}" y1="${girderBottomY}" x2="${liftDimX}" y2="${floorY}" class="svg-dim-line" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)" stroke-width="1.5" />
      <line x1="${railRightX + 16}" y1="${girderBottomY}" x2="${liftDimX + 18}" y2="${girderBottomY}" class="svg-ext-line" stroke-width="1.2" />
      <line x1="${railRightX + 16}" y1="${floorY}" x2="${liftDimX + 18}" y2="${floorY}" class="svg-ext-line" stroke-width="1.2" />
      <g transform="translate(${liftDimX}, ${liftMidY})">
        <rect x="-72" y="-14" width="144" height="28" rx="4" fill="#ffffff" stroke="#1f3a5f" stroke-width="1.5" />
        <text x="0" y="5" font-size="13.5" font-weight="bold" fill="#1f3a5f" text-anchor="middle">Lift Height: ${calc.hook_height_m} m</text>
      </g>

      <!-- Title Block (Engineering Drawing Sheet Header at Bottom) -->
      <g transform="translate(35, 368)">
        <rect x="0" y="0" width="830" height="44" fill="#f8fafc" stroke="#1f3a5f" stroke-width="1.5" rx="3" />
        <line x1="0" y1="24" x2="830" y2="24" stroke="#cbd5e1" stroke-width="1" />
        <!-- Row 1 Parameters -->
        <text x="12" y="16" font-size="11.5" font-weight="bold" fill="#1f3a5f">DESIGN: <tspan font-weight="normal">${escapeHtml(designName)}</tspan></text>
        <text x="310" y="16" font-size="11.5" font-weight="bold" fill="#1f3a5f">SPAN: <tspan font-weight="normal">${calc.girder_length_m} m</tspan></text>
        <text x="430" y="16" font-size="11.5" font-weight="bold" fill="#1f3a5f">CAPACITY: <tspan font-weight="normal">${calc.capacity_t} t</tspan></text>
        <text x="555" y="16" font-size="11.5" font-weight="bold" fill="#1f3a5f">LIFT HT: <tspan font-weight="normal">${calc.hook_height_m} m</tspan></text>
        <text x="685" y="16" font-size="11.5" font-weight="bold" fill="#1f3a5f">GIRDER HT: <tspan font-weight="normal">${calc.girder_height_mm} mm</tspan></text>
        <!-- Row 2 Warning note -->
        <text x="415" y="38" font-size="12" font-weight="bold" fill="#b91c1c" text-anchor="middle">Concept drawing — not for manufacturing</text>
      </g>
    `;
  }

  function renderSideView(calc) {
    const W = 420;
    const H = 420;
    const centerX = 220; // Slightly shifted right to give room on left for Girder Height dimension line

    // End Truck Width is 800 mm (estimate) -> drawn to 250 px
    const truckWidthPx = 250;
    const truckLeftX = centerX - truckWidthPx / 2;
    const truckRightX = centerX + truckWidthPx / 2;

    // Girder Height drawn to scale: 300 to 1500 mm -> 75 to 210 px
    const girderHNorm = Math.max(0, Math.min(1, (calc.girder_height_mm - 300) / (1500 - 300)));
    const girderHPx = 75 + girderHNorm * 135;

    const truckBaseY = 270;
    const truckHeightPx = 40;
    const girderBottomY = truckBaseY - truckHeightPx + 10;
    const girderTopY = girderBottomY - girderHPx;

    // I-beam profile parameters (centered at centerX)
    const flangeW = 110;
    const flangeH = 14;
    const webW = 20;
    const beamLeftX = centerX - flangeW / 2;

    // Dimension lines
    const truckDimY = 372;
    const girderDimX = 75;
    const girderMidY = (girderTopY + girderBottomY) / 2;

    sideViewSvg.innerHTML = `
      ${createMarkerDefs()}
      <rect width="${W}" height="${H}" class="svg-bg" />

      <!-- Elevated Runway Beam & Rail Assembly (under the end truck) -->
      <!-- Rail Head on Runway Beam -->
      <rect x="65" y="296" width="310" height="12" class="svg-rail" rx="1" />
      <!-- Runway Beam / Girder profile -->
      <rect x="75" y="308" width="290" height="10" fill="#94a3b8" stroke="#475569" stroke-width="1.2" />
      <rect x="208" y="318" width="24" height="22" fill="#94a3b8" stroke="#475569" stroke-width="1.2" />
      <rect x="140" y="340" width="160" height="8" fill="#94a3b8" stroke="#475569" stroke-width="1.2" />
      <text x="220" y="333" font-size="10.5" font-weight="600" fill="#1f3a5f" text-anchor="middle">Runway Beam</text>

      <!-- Wheels (two wheels on the end truck) -->
      <circle cx="${truckLeftX + 35}" cy="284" r="14" class="svg-wheel" />
      <circle cx="${truckRightX - 35}" cy="284" r="14" class="svg-wheel" />

      <!-- End Truck Body (Side Elevation) -->
      <rect x="${truckLeftX}" y="${truckBaseY - truckHeightPx}" width="${truckWidthPx}" height="${truckHeightPx}" rx="3" class="svg-end-truck" />
      <circle cx="${truckLeftX + 35}" cy="284" r="4.5" fill="#cbd5e1" />
      <circle cx="${truckRightX - 35}" cy="284" r="4.5" fill="#cbd5e1" />

      <!-- End Truck Label -->
      <text x="${centerX}" y="${truckBaseY - truckHeightPx / 2 + 5}" font-size="11.5" font-weight="600" fill="#ffffff" text-anchor="middle">
        End Truck (Side Profile)
      </text>

      <!-- Girder Section (I-Beam Profile, drawn larger and centered) -->
      <!-- Top Flange -->
      <rect x="${beamLeftX}" y="${girderTopY}" width="${flangeW}" height="${flangeH}" class="svg-girder" />
      <!-- Web -->
      <rect x="${centerX - webW / 2}" y="${girderTopY + flangeH}" width="${webW}" height="${girderHPx - 2 * flangeH}" class="svg-girder" />
      <!-- Bottom Flange -->
      <rect x="${beamLeftX}" y="${girderBottomY - flangeH}" width="${flangeW}" height="${flangeH}" class="svg-girder" />

      <!-- Girder Section Part Label -->
      <g transform="translate(${centerX}, ${girderTopY - 10})">
        <rect x="-65" y="-11" width="130" height="22" rx="3" fill="#ffffff" stroke="#5a6b7d" stroke-width="1.2" />
        <text x="0" y="4" font-size="11" font-weight="600" fill="#1f3a5f" text-anchor="middle">Girder Cross-Section</text>
      </g>

      <!-- Girder Height Dimension Line & Extension Lines (Beside Girder on Left) -->
      <line x1="${girderDimX}" y1="${girderTopY}" x2="${girderDimX}" y2="${girderBottomY}" class="svg-dim-line" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)" stroke-width="1.5" />
      <line x1="${beamLeftX - 5}" y1="${girderTopY}" x2="${girderDimX - 16}" y2="${girderTopY}" class="svg-ext-line" stroke-width="1.2" />
      <line x1="${beamLeftX - 5}" y1="${girderBottomY}" x2="${girderDimX - 16}" y2="${girderBottomY}" class="svg-ext-line" stroke-width="1.2" />
      <g transform="translate(${girderDimX}, ${girderMidY})">
        <rect x="-72" y="-14" width="144" height="28" rx="4" fill="#ffffff" stroke="#1f3a5f" stroke-width="1.5" />
        <text x="0" y="5" font-size="13" font-weight="bold" fill="#1f3a5f" text-anchor="middle">Girder Height: ${calc.girder_height_mm} mm</text>
      </g>

      <!-- End Truck Width Dimension Line & Extension Lines (Below Truck) -->
      <line x1="${truckLeftX}" y1="${truckDimY}" x2="${truckRightX}" y2="${truckDimY}" class="svg-dim-line" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)" stroke-width="1.5" />
      <line x1="${truckLeftX}" y1="${truckBaseY + 6}" x2="${truckLeftX}" y2="${truckDimY + 14}" class="svg-ext-line" stroke-width="1.2" />
      <line x1="${truckRightX}" y1="${truckBaseY + 6}" x2="${truckRightX}" y2="${truckDimY + 14}" class="svg-ext-line" stroke-width="1.2" />
      <g transform="translate(${centerX}, ${truckDimY})">
        <rect x="-155" y="-14" width="310" height="28" rx="4" fill="#ffffff" stroke="#1f3a5f" stroke-width="1.5" />
        <text x="0" y="5" font-size="13" font-weight="bold" fill="#1f3a5f" text-anchor="middle">End Truck Width: ${calc.end_truck_width_mm} mm (estimate)</text>
      </g>
    `;
  }

  function renderNotes(notes) {
    notesList.innerHTML = "";
    if (!notes || notes.length === 0) {
      notesList.innerHTML = "<li>No notes returned from calculation.</li>";
      return;
    }
    notes.forEach(noteText => {
      const li = document.createElement("li");
      li.textContent = noteText;
      notesList.appendChild(li);
    });
  }

  // --- API CALL: Saved Designs List ---
  async function fetchDesigns() {
    try {
      const res = await fetch("/api/designs");
      if (!res.ok) {
        designsTableBody.innerHTML = `<tr><td colspan="8" class="empty-state">Failed to load designs (${res.status})</td></tr>`;
        return;
      }
      const designs = await res.json();
      if (!designs || designs.length === 0) {
        designsTableBody.innerHTML = `<tr><td colspan="8" class="empty-state">No saved designs yet. Create one above!</td></tr>`;
        return;
      }

      designsTableBody.innerHTML = designs.map(d => {
        const updatedDate = d.updated_at ? new Date(d.updated_at).toLocaleString() : "-";
        return `
          <tr data-id="${d.id}">
            <td><strong>#${d.id}</strong></td>
            <td><strong>${escapeHtml(d.name)}</strong></td>
            <td>${d.span_m.toFixed(1)}</td>
            <td>${d.capacity_t.toFixed(1)}</td>
            <td>${d.lift_height_m.toFixed(1)}</td>
            <td>${d.girder_height_mm}</td>
            <td style="font-size: 0.8rem; color: var(--text-muted);">${updatedDate}</td>
            <td style="text-align: center;">
              <button type="button" class="btn btn-sm btn-outline btn-open-design" data-id="${d.id}">Open</button>
            </td>
          </tr>
        `;
      }).join("");

      // Bind Open buttons
      document.querySelectorAll(".btn-open-design").forEach(btn => {
        btn.addEventListener("click", () => {
          const id = parseInt(btn.getAttribute("data-id"), 10);
          openDesign(id);
        });
      });
    } catch (err) {
      designsTableBody.innerHTML = `<tr><td colspan="8" class="empty-state">Error: ${escapeHtml(err.message)}</td></tr>`;
    }
  }

  async function openDesign(id) {
    clearError();
    try {
      const res = await fetch(`/api/designs/${id}`);
      if (!res.ok) {
        const errJson = await res.json();
        showError(parseValidationErrors(errJson));
        return;
      }
      const design = await res.json();

      // Populate form fields
      activeDesignId = design.id;
      inputName.value = design.name;
      inputSpan.value = design.span_m;
      inputCapacity.value = design.capacity_t;
      inputLiftHeight.value = design.lift_height_m;
      inputGirderHeight.value = design.girder_height_mm;

      // Update UI state
      activeBadge.textContent = `Design #${design.id}`;
      activeBadge.className = "status-badge badge-loaded";
      btnUpdate.disabled = false;

      // Trigger recalculation and redraw
      await triggerCalculation();
      showSuccess(`Loaded design "${design.name}" (#${design.id})`);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err) {
      showError(`Error opening design #${id}: ${err.message}`);
    }
  }

  // --- API CALL: Save Design (POST /api/designs) ---
  btnSave.addEventListener("click", async () => {
    clearError();
    const values = getFormValues();

    if (!values.name) {
      showError("Design Name is required.");
      return;
    }

    try {
      const res = await fetch("/api/designs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(values),
      });

      if (!res.ok) {
        const errJson = await res.json();
        showError(parseValidationErrors(errJson));
        return;
      }

      const saved = await res.json();
      activeDesignId = saved.id;
      activeBadge.textContent = `Design #${saved.id}`;
      activeBadge.className = "status-badge badge-loaded";
      btnUpdate.disabled = false;

      showSuccess(`Design "${saved.name}" saved successfully with ID #${saved.id}`);
      fetchDesigns();
    } catch (err) {
      showError(`Failed to save design: ${err.message}`);
    }
  });

  // --- API CALL: Update Design (PUT /api/designs/{id}) ---
  btnUpdate.addEventListener("click", async () => {
    if (!activeDesignId) {
      showError("No saved design is currently selected for update.");
      return;
    }
    clearError();
    const values = getFormValues();

    if (!values.name) {
      showError("Design Name is required.");
      return;
    }

    try {
      const res = await fetch(`/api/designs/${activeDesignId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(values),
      });

      if (!res.ok) {
        const errJson = await res.json();
        showError(parseValidationErrors(errJson));
        return;
      }

      const updated = await res.json();
      showSuccess(`Design #${updated.id} ("${updated.name}") updated successfully.`);
      fetchDesigns();
    } catch (err) {
      showError(`Failed to update design: ${err.message}`);
    }
  });

  // --- Reset Form to New ---
  btnReset.addEventListener("click", () => {
    activeDesignId = null;
    activeBadge.textContent = "New Design";
    activeBadge.className = "status-badge badge-new";
    btnUpdate.disabled = true;
    inputName.value = "Standard Workshop Crane";
    inputSpan.value = 16.0;
    inputCapacity.value = 10.0;
    inputLiftHeight.value = 6.5;
    inputGirderHeight.value = 800;
    clearError();
    showSuccess("Form reset to new design.");
    triggerCalculation();
  });

  btnRefresh.addEventListener("click", () => {
    fetchDesigns();
  });

  // Initial Boot
  triggerCalculation();
  fetchDesigns();
});
