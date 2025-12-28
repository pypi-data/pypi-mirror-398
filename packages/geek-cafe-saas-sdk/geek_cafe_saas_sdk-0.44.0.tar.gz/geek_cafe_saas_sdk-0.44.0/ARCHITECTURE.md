# Architecture Overview

## Project Structure

```
geek-cafe-services/
├── src/geek_cafe_saas_sdk/
│   ├── core/                      # Foundational types and patterns
│   │   ├── service_result.py      # Standardized service response wrapper
│   │   ├── service_errors.py      # Common error types
│   │   └── audit_mixin.py         # Audit trail functionality
│   │
│   ├── models/                    # DynamoDB models
│   │   ├── base_model.py          # Base model with common patterns
│   │   ├── event.py               # Event model
│   │   ├── user.py                # User model
│   │   ├── group.py               # Group model
│   │   ├── message_thread.py      # Message thread model
│   │   ├── vote.py                # Vote model
│   │   └── website_analytics.py   # Analytics models
│   │
│   ├── services/                  # Business logic layer
│   │   ├── database_service.py    # Base database service
│   │   ├── event_service.py       # Event operations
│   │   ├── user_service.py        # User operations
│   │   ├── group_service.py       # Group operations
│   │   ├── message_thread_service.py  # Message operations
│   │   ├── vote_service.py        # Vote operations
│   │   └── vote_tally_service.py  # Vote aggregation
│   │
│   ├── lambda_handlers/           # AWS Lambda handlers
│   │   ├── _base/                 # Internal base handlers
│   │   │   ├── base_handler.py
│   │   │   ├── api_key_handler.py
│   │   │   ├── public_handler.py
│   │   │   └── service_pool.py
│   │   ├── events/                # ✅ Complete CRUDL
│   │   ├── users/                 # ✅ Complete CRUDL
│   │   ├── groups/                # ✅ Complete CRUDL
│   │   ├── messages/              # ✅ Complete CRUDL
│   │   └── votes/                 # ✅ Complete CRUDL
│   │
│   ├── middleware/                # Cross-cutting concerns
│   │   ├── auth.py                # Authentication middleware
│   │   ├── cors.py                # CORS handling
│   │   ├── error_handling.py      # Error middleware
│   │   └── validation.py          # Request validation
│   │
│   └── utilities/                 # Helper utilities
│       ├── response.py            # HTTP response builders
│       ├── lambda_event_utility.py # Lambda event parsing
│       ├── dynamodb_utils.py      # DynamoDB helpers
│       ├── jwt_utility.py         # JWT handling
│       └── custom_exceptions.py   # Custom exceptions
│
├── tests/                         # Test suite
│   ├── common/                    # Shared test utilities
│   ├── test_*_service.py          # Service tests
│   ├── test_lambda_handlers/      # Handler integration tests
│   └── test_*.py                  # Various test files
│
└── docs/                          # Documentation
    ├── api/                       # API documentation
    ├── guides/                    # Usage guides
    └── services/                  # Service documentation
```

## Design Principles

### 1. Multi-Tenant by Default
Every resource is scoped by `tenant_id`, ensuring complete data isolation between customers.

```python
from geek_cafe_saas_sdk.core.request_context import RequestContext

# Services use RequestContext for automatic tenant/user isolation
request_context = RequestContext(event)  # Extracts from JWT

event_service = EventService(
    dynamodb=db,
    table_name=TABLE_NAME,
    request_context=request_context  # Enforces tenant isolation
)

# Service methods use context internally - security is automatic
result = event_service.create(payload={
    'title': 'My Event',
    'description': '...'
})
```

### 2. Consistent Service Pattern
All services follow the same pattern:

- **ServiceResult wrapper**: Consistent return type for success/error handling
- **CRUD operations**: Create, Read, Update, Delete with soft deletes
- **Access control**: Built-in tenant and user validation
- **Error handling**: Standardized error responses

```python
# Every service method returns ServiceResult
result: ServiceResult[Event] = service.create(...)

if result.success:
    event = result.data
else:
    error = result.error
```

### 3. Lambda Handler Infrastructure

**Base Handlers** (`_base/`)
- `BaseLambdaHandler`: Core handler functionality
- `ApiKeyLambdaHandler`: Adds API key validation
- `PublicLambdaHandler`: No authentication required
- `ServicePool`: Connection pooling for warm starts

**Resource Handlers** (events, users, groups, messages, votes)
- Each resource has complete CRUDL operations
- Consistent authentication via Cognito JWT
- Service pooling for performance
- Testability via service injection

### 4. DynamoDB Optimization

**Single Table Design**
- One table for all resources
- Efficient GSI indexes for common queries
- Tenant-isolated partitions

**Key Patterns**
```python
# Primary Key (PK/SK)
PK: "TENANT#{tenant_id}"
SK: "EVENT#{event_id}"

# GSI for user queries
GSI1PK: "USER#{user_id}"
GSI1SK: "ts#{timestamp}"
```

### 5. Testing Strategy

**Integration Tests**
- Use `moto` for DynamoDB mocking
- Service injection for handler testing
- Complete end-to-end workflows

**Test Fixtures**
- `db_helpers.py`: DynamoDB setup helpers
- `lambda_helpers.py`: Event builders and test utilities

```python
# Clean test pattern
def test_create_event(integration_setup, helper):
    db, event_service = integration_setup
    
    event = helper.build_proxy_event(body={"title": "Test"})
    response = lambda_handler(event, None, injected_service=event_service)
    
    assert response['statusCode'] == 201
```

## Key Features

### Service Pooling
Reduces Lambda cold starts by 80-90% through connection reuse:

```python
# Module level - initialized once
service_pool = ServicePool(EventService)

def lambda_handler(event, context):
    # Reuses service on warm invocations
    service = service_pool.get()
```

### Authentication Flow
1. API Gateway validates Cognito JWT
2. Claims passed in `requestContext.authorizer.claims`
3. Handler extracts `custom:user_id` and `custom:tenant_id`
4. Service enforces tenant isolation

### Error Handling
Consistent error responses across all handlers:

```python
{
  "statusCode": 400,
  "body": {
    "error": "Validation failed",
    "errorCode": "VALIDATION_ERROR"
  }
}
```

### Soft Deletes
Resources are marked as deleted, not physically removed:

```python
# Delete operation
result = service.delete(resource_id, tenant_id, user_id)
# Sets: deleted=True, deleted_at=timestamp
```

## Performance Optimizations

1. **Service Pooling**: Reuse DB connections on warm starts
2. **GSI Indexes**: Efficient queries without table scans  
3. **Batch Operations**: Support for bulk reads/writes
4. **Pagination**: Cursor-based pagination for large result sets

## Security Features

1. **Tenant Isolation**: Every query scoped by tenant_id
2. **Soft Deletes**: Audit trail preservation
3. **Access Control**: User-level permissions per operation
4. **JWT Validation**: Via API Gateway authorizer

## Extension Points

### Adding New Resources

1. **Create Model** in `models/`
2. **Create Service** in `services/`
3. **Create Lambda Handlers** in `lambda_handlers/`
4. **Write Tests** following existing patterns

### Custom Middleware

Add to `middleware/` and apply to handlers:

```python
@custom_middleware
@handle_cors
@handle_errors
def lambda_handler(event, context):
    pass
```

### Custom Validators

Extend validation in `utilities/` or add per-service validation.

## Deployment

### As a Library
```bash
pip install geek-cafe-services
```

### Lambda Deployment
Use CDK-Factory to deploy handlers as part of your platform stacks.

```bash
# AWS CDK (via CDK-Factory)
lambda.Function(this, 'EventCreate', {
  code: lambda.Code.fromAsset('lambda_handlers/events/create'),
  handler: 'app.handler'
})
```

## Best Practices

1. ✅ Always use `ServiceResult` for service responses
2. ✅ Require `tenant_id` for all operations
3. ✅ Use soft deletes, never hard deletes
4. ✅ Pool services in Lambda handlers
5. ✅ Inject services in tests
6. ✅ Follow CRUDL pattern for consistency
7. ✅ Document breaking changes until 1.0 GA

## Version Information

- **Current Version**: 0.3.0
- **Python**: 3.13+
- **Status**: Pre-1.0 (breaking changes possible)
- **Test Coverage**: 83.7% (482 tests)

## References

- **Service Pattern**: `docs/services_pattern.md`
- **Lambda Handlers**: `docs/api/lambda_handlers.md`
- **Handler Structure**: `docs/guides/lambda_handler_structure.md`
- **DynamoDB Models**: `docs/dynamodb_models.md`
