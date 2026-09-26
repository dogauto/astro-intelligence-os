# Calculation Dependency Graph

**Status:** CANONICAL

To prevent incomplete foundational calculations from silently contaminating higher-level methodologies, dependencies must strictly follow this directed graph. A downstream node inherits the lowest maturity status of its ancestors.

## Core Dependency Paths

### Method A (Vimshottari Career)
```mermaid
graph TD
    A[Astronomy Engine] --> B[AstroState: Planets]
    B --> C[Nakshatras]
    B --> D[Vargas]
    C --> E[Vimshottari Dasha]
    E --> F{VimshottariCareerMethod}
    D --> F
```

### Method B (Gochara Transit)
```mermaid
graph TD
    A[Astronomy Engine] --> B[AstroState: Natal Planets]
    A --> G[AstroState: Transit Planets]
    B --> H{TransitCareerMethod}
    G --> H
```

### Shadbala (Partial)
```mermaid
graph TD
    A[Astronomy Engine] --> B[AstroState: Planets]
    A --> I[Sunrise/Sunset - MISSING]
    B --> D[Vargas]
    D --> J[Shadbala - PARTIAL]
    I --> J
    J --> K{Future Advanced Methods - BLOCKED}
```

*Note: Any method relying on Shadbala is currently blocked from PRODUCTION status until the missing `I` dependencies are fulfilled.*
