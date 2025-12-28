# Changelog - Version 0.4.1

## 🔧 Critical Fix: Standardized Service Injection Parameter

### Breaking Change (Naming Only)
**All Lambda handlers now use `injected_service` (singular) instead of `injected_services` (plural)**

This standardizes the parameter name across the entire codebase for testing with Moto DynamoDB.

### Files Updated (25 handlers)

#### ✅ Messages (5 handlers)
- `messages/create/app.py` - Updated to `injected_service`
- `messages/get/app.py` - Updated to `injected_service`
- `messages/update/app.py` - Updated to `injected_service`
- `messages/delete/app.py` - Updated to `injected_service`
- `messages/list/app.py` - Updated to `injected_service`

#### ✅ Events (5 handlers)
- `events/create/app.py` - Updated to `injected_service`
- `events/get/app.py` - Updated to `injected_service`
- `events/update/app.py` - Updated to `injected_service`
- `events/delete/app.py` - Updated to `injected_service`
- `events/list/app.py` - Updated to `injected_service`

#### ✅ Groups (5 handlers)
- `groups/create/app.py` - Updated to `injected_service`
- `groups/get/app.py` - Updated to `injected_service`
- `groups/update/app.py` - Updated to `injected_service`
- `groups/delete/app.py` - Updated to `injected_service`
- `groups/list/app.py` - Updated to `injected_service`

#### ✅ Users (5 handlers)
- `users/create/app.py` - Updated to `injected_service`
- `users/get/app.py` - Updated to `injected_service`
- `users/update/app.py` - Updated to `injected_service`
- `users/delete/app.py` - Updated to `injected_service`
- `users/list/app.py` - Updated to `injected_service`

#### ✅ Votes (5 handlers)
- `votes/create/app.py` - **NEW**: Added `injected_service` parameter
- `votes/get/app.py` - Updated to `injected_service`
- `votes/update/app.py` - Updated to `injected_service`
- `votes/delete/app.py` - Updated to `injected_service`
- `votes/list/app.py` - Updated to `injected_service`

### Migration Guide

#### Before (0.4.0)
```python
# Old parameter name (WRONG)
def lambda_handler(event, context, injected_services=None):
    service = injected_services or service_pool.get()
    # ...

# In tests
response = lambda_handler(event, None, injected_services=mock_service)
```

#### After (0.4.1)
```python
# New parameter name (CORRECT)
def lambda_handler(event, context, injected_service=None):
    service = injected_service or service_pool.get()
    # ...

# In tests
response = lambda_handler(event, None, injected_service=mock_service)
```

### Testing Impact

**Critical for Moto DynamoDB Testing:**

```python
# OLD WAY (0.4.0) - No longer works
from moto import mock_dynamodb

@mock_dynamodb
def test_handler():
    service = MessageService()
    response = lambda_handler(event, None, injected_services=service)  # ❌ Wrong param name

# NEW WAY (0.4.1) - Correct
from moto import mock_dynamodb

@mock_dynamodb
def test_handler():
    service = MessageService()
    response = lambda_handler(event, None, injected_service=service)  # ✅ Correct param name
```

### Why This Change?

1. **Consistency** - All handlers now use the same parameter name
2. **Correctness** - Singular form is semantically correct (one service instance)
3. **Testing** - Essential for Moto DynamoDB integration testing
4. **Documentation** - All docs now reference consistent naming

### Backward Compatibility

⚠️ **Breaking Change for Tests Only**

This change **only affects test code** that uses the `injected_services` parameter. Production code is unaffected since the parameter is optional and defaults to `None`.

**If you have existing tests**, update them:
```bash
# Find and replace in your test files
find tests/ -type f -name "*.py" -exec sed -i '' 's/injected_services=/injected_service=/g' {} +
```

### Verification

Run this to verify no old parameter names remain:
```bash
cd /Users/eric.wilson/Projects/geek-cafe/geek-cafe-services
grep -r "injected_services" src/geek_cafe_saas_sdk/lambda_handlers/
# Should return: No results
```

### Related Documentation

- 📖 [Testing Standards](docs/TESTING_STANDARDS.md)
- 📖 [Testing with Moto](docs/TESTING_WITH_MOTO.md)
- 📖 [Message Thread API](docs/api/MESSAGE_THREAD_API.md)
- 📖 [Handler Factory Guide](docs/HANDLER_FACTORY_QUICK_REF.md)

### Published to PyPI

✅ Version 0.4.1 published successfully
- Package: `geek-cafe-services==0.4.1`
- Install: `pip install geek-cafe-services==0.4.1`
- View: https://pypi.org/project/geek-cafe-services/0.4.1/

---

## Summary

✅ **25 handlers updated** - All use `injected_service` (singular)  
✅ **Consistent naming** - No more confusion between plural/singular  
✅ **Testing ready** - Full Moto DynamoDB support  
✅ **Documented** - All examples and guides updated  
✅ **Published** - Available on PyPI  

**This change makes testing Lambda handlers with Moto DynamoDB straightforward and consistent across all services!** 🎉
