# Lesson: Config File Priority Resolution

**Date:** 2024-01-15
**Category:** Configuration

## Issue

Users were confused about which namespace to use when both CLI argument and config file specified different namespaces.

## Solution

CLI arguments should always take precedence over config file values. Implemented clear priority order:

1. CLI argument (highest priority)
2. Config file value
3. Default value or prompt user (lowest priority)

## Code Pattern

```python
# In agent initialization
if args.namespace:
    self.namespace = args.namespace  # CLI wins
elif self.config.get('namespace'):
    self.namespace = self.config['namespace']  # Config fallback
else:
    self.namespace = None  # Will prompt user

# Visual feedback
print(f"Using namespace: {self.namespace} (from {'CLI' if args.namespace else 'config'})")
```

## Result

Users now understand which namespace is active and can override config values via CLI when needed.

## Related Files

- `aks-workflow-agent.py` - Main agent script
- `README.md` - Usage documentation