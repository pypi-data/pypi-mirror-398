# Monte Carlo GraphQL Schema Library

The `schema.json` and `schema.py` files are auto-generated. **Do not edit them directly**!

If you need to customize the schema, see below. Refer to the
[CONTRIBUTING.md](../../CONTRIBUTING.md) for general development guidelines.

## Schema Customizations

The generated `schema.py` is automatically modified during the build process to apply the following
customizations. This is done via `sed` commands in the [Makefile](../../Makefile), but if we need to
get fancier, we just can update the `customize-schema` target there to call whatever we need to do.

### Connection Type Fix

The `Connection` class is changed from `sgqlc.types.relay.Connection` to `sgqlc.types.Type`.

**Why:** sgqlc automatically makes all types ending in "Connection" inherit from `relay.Connection`,
which makes `Connection` not a valid field type. This causes requests to fail when attempting to
resolve it. Changing it to inherit from `sgqlc.types.Type` fixes this issue.

[Related PR](https://github.com/monte-carlo-data/python-sdk/pull/63)

### Backward-Compatible Enums

All GraphQL enum types use `pycarlo.lib.types.Enum` instead of `sgqlc.types.Enum`. This custom enum
class gracefully handles unknown enum values by returning them as strings instead of raising errors.

**Why:** When new enum values are added to the Monte Carlo API, older SDK versions would crash when
deserializing responses containing these new values. Our custom Enum prevents this by:

- Returning unknown values as plain strings (same type as known values)
- Logging a warning when unknown values are encountered

See [pycarlo/lib/types.py](types.py) for implementation details.
