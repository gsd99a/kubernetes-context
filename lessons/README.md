# Lessons Learned

This directory tracks lessons learned, issues encountered, and best practices for the AKS Workflow Agent.

## Structure

Each lesson should be documented in its own file with:
- **Issue**: What problem was encountered
- **Solution**: How it was resolved
- **Code/Command**: Example fix
- **Date**: When discovered

## File Naming

Use descriptive names: `lesson_<topic>_<date>.md`

Example:
- `lesson_config_priority_2024-01-15.md`
- `lesson_oomkilled_detection_2024-01-16.md`
- `lesson_azure_auth_2024-01-17.md`

## Categories

### Configuration
- Config file detection
- Namespace precedence
- Multi-config support

### Azure
- Authentication patterns
- AKS context setup
- KeyVault integration

### Kubernetes
- Pod operations
- Troubleshooting
- Resource queries

### Performance
- Query optimization
- Output formatting
- Caching strategies