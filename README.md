**The Measles Monitor** is an interactive Streamlit dashboard developed by the ASU Health Observatory to visualize, compare, and simulate measles outbreaks in the United States.

---

### Tabs Overview

- **Case Trajectory**  
  View weekly confirmed measles cases by state in 2025.

- **Outbreak Map**  
  Animated choropleth showing the geographic spread of cases across the U.S.

- **Then vs. Now**  
  Compare 2025 cases to the 2019 outbreak and track changes in MMR vaccination rates by state.

- **Demographic Lens**  
  Visual breakdowns by age group, vaccination status, and hospitalization outcomes.

- **AZ School Risks**  
  Select any Arizona school to simulate a measles outbreak based on local vaccination coverage.

---

---

### Outbreak Simulation Equations

- **Susceptible Students**  
  `S = N × (1 − v)`  
  _Where:_  
  `N` = total enrollment  
  `v` = MMR immunization rate

- **Final Attack Rate**  
  `z = 1 − exp(−R₀ × z × s)`  
  _Numerically solved where:_  
  `s = S / N`, `R₀ = 12`

- **Total Cases**  
  `C = z × N`

- **Hospitalizations**  
  `H = C × 0.20`

- **Deaths**  
  `D = C × 0.003`

- **Missed School Days (Quarantine)**  
  `M = (S-C × 21) + (C x 4)`

