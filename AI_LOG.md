# AI Development Log

## 1. Tools used
- **Antigravity (AI coding agent)**: Used for writing, editing, and executing code and test scripts directly in the workspace from my prompts.
- **Muse**: Used for planning the project stages, reviewing visual screenshots, and preparing structured prompts before sending them to the agent.

## 2. How I worked
I split the project into small, manageable steps: requirements, system design, backend development, frontend construction, drawing refinements, and testing. After each step, I ran the code, reviewed the result, and verified that everything worked before moving on to the next prompt.

## 3. Key prompts

### Prompt 1: Backend skeleton
- **What I asked for**: Build the backend only using FastAPI, SQLite, and Pydantic. Create endpoints to calculate drawing numbers, save designs, list designs newest first, fetch one by ID, update by ID, and health check, with strict range validation.
- **What came out**: Clean backend code with `main.py`, `database.py`, `models.py`, `requirements.txt`, and an automated test suite verifying all 6 endpoints and validation rules.

### Prompt 2: Frontend page with SVG views
- **What I asked for**: Build a single-page frontend in `static/` with `index.html`, `style.css`, and `app.js`. Serve it from `/` in FastAPI, with an input form, dynamic front and side SVG views connected to `/api/calculate`, and a saved designs table.
- **What came out**: A working single-page application that debounced input changes, called the API, drew parametric front and side SVGs, and supported saving and reopening designs.

### Prompt 3: Drawing readability fix
- **What I asked for**: Make the drawings bigger (viewBoxes 900x420 and 420x420). Fix overlapping text by using readable labels (at least 13px) with white backgrounds, proper dimension lines with arrowheads at both ends, a ground line, part labels, and an engineering drawing title block.
- **What came out**: Clearer drawings with large viewBoxes, bidirectional dimension arrows, white badges behind all labels, a floor line, and a sheet title block showing design metadata and a concept disclaimer.

### Prompt 4: Engineering accuracy fix
- **What I asked for**: The front view had vertical legs to the floor, which made it look like a gantry crane rather than an overhead crane. Remove the legs completely, draw runway beam segments with wall brackets at both ends, leave open space beneath the girder, and keep the floor line only as a lift height reference.
- **What came out**: Corrected EOT crane drawing with elevated runway beams and wall corbels under the end trucks, no vertical columns to the floor, and an open bay beneath the girder.

### Prompt 5: Label overlap fix
- **What I asked for**: At large spans (like 30 m), the floating dark capacity box overlapped the End Truck label. Remove the floating capacity box (since capacity is already in the title block), place the End Truck label cleanly above the truck, and verify that no labels collide across minimum, middle, and maximum values.
- **What came out**: Clean front view with the floating capacity box removed, the End Truck label placed clear of other labels, and no overlaps in the minimum, middle, and maximum test cases.

## 4. When the AI was wrong and how I caught it
- **The Uvicorn command**: The generated README originally told me to run `uvicorn main:app --reload`. When I ran this in my Windows terminal, PowerShell returned a `CommandNotFoundException` because Python's user Scripts directory was not on my system PATH. I caught it by running the command myself. I fixed it by running `python -m uvicorn main:app --reload`, which works reliably because Python is on PATH.
- **Drawing legs to the floor**: The initial front view drawing drew vertical support columns going from the end trucks down to the floor line. An overhead crane runs on elevated runway beams attached to building columns, so legs to the floor turned it into a gantry crane. I caught this during visual review and had the AI replace the legs with elevated runway beams and wall corbels.
- **Label overlap at 30 m span**: At maximum span (30 m), the floating capacity box in the top-left overlapped the End Truck label, making both unreadable. I caught this by running boundary tests with minimum, middle, and maximum inputs. I fixed it by removing the redundant floating box (the capacity is already displayed in the title block) and centering the End Truck label with clear margins.

## 5. How I tested
- **Automated endpoint tests**: The coding agent generated Python test scripts for the API endpoints. I reviewed the results (status codes, JSON structure, sorting, 404 and 422 handling) and then tested the same flows manually in the browser and on the /docs page.
- **Boundary value tests**: Tested the app at minimum values (span 5 m, capacity 1 t, lift 3 m, girder 300 mm), middle values (span 16 m, capacity 10 t, lift 6.5 m, girder 800 mm), and maximum values (span 30 m, capacity 20 t, lift 15 m, girder 1500 mm) to verify that drawing geometry scales properly and labels never collide.
- **Validation error tests**: Submitted invalid numbers (such as span = 2 m) and checked that the UI displayed plain-English error messages from the backend without crashing.
- **Persistence tests**: Saved a design, refreshed the browser, reloaded the design using the "Open" button, updated its parameters, and restarted the server process to confirm that data survived in the `cranes.db` SQLite file.
