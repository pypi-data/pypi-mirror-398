# clevercx-security-master-types

Python type definitions for CleverCX Security Master database entities.

**Generated from**: PostgreSQL database via `sqlacodegen`

## Installation

```bash
pip install clevercx-security-master-types
```

## Usage

```python
from clevercx_security_master_types import (
    Security,
    SecurityHistoricalPrice,
    SecurityCalculation,
    SecurityReferenceVersion,
    SecurityMetadataVersion,
    SecuritySettingsVersion,
    SecurityComposition,
    VSecuritiesCurrent,
)

# Use with your database queries
def get_security(row: dict) -> Security:
    return Security(**row)
```

## Available Types

- `Security` - Core security identity
- `SecurityHistoricalPrice` - Historical price data
- `SecurityCalculation` - Calculated metrics
- `SecurityReferenceVersion` - Vendor reference data
- `SecurityMetadataVersion` - Internal metadata
- `SecuritySettingsVersion` - Calculation settings
- `SecurityComposition` - Portfolio composition
- `SecurityReturn` - Return data
- `DataSource` - Data source definitions
- `VSecuritiesCurrent` - Current security view (denormalized)

## Related Packages

| Package | Purpose |
|---------|---------|
| `@clevercx/security-master-types` (npm) | TypeScript types |
| `@clevercx/security-master-prisma` (npm) | Prisma schema for querying |

## License

MIT
