# Offline candle admission prototype

Question: can a settling/stability check prevent admission of the observed early AAVE version, while preserving all captured versions and truthful entry timing?

This prototype has no network collector, no study state writer, no orders and no automatic integration. It requires a candle to be at least 60 seconds past its close and have two identical observations at least 15 seconds apart. A changed pending version restarts stability. These are declared engineering choices; they do not guarantee venue finality and were not selected by trading outcomes. All observed parsed versions are retained. Once admitted, any later change still raises an integrity error; admitted history is never overwritten. Entry timing uses actual admission and book receipt times, retains the original 60-second delay/120-second grace, and refuses late or pre-admission books.

The fixture contains the actual two archived AAVE versions. Its third observation is expressly synthetic. Tests establish gate behavior, not fill feasibility or edge. The current A halt is not repaired by this prototype. An adoption changes data admission timing and requires a separately identified protocol; neither A nor B is silently amended.
