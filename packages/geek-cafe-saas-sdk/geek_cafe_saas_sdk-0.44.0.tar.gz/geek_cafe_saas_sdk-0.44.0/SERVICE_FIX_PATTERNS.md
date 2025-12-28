# Service Fix Patterns for request_context Migration

## Overview
This document provides templates and patterns for migrating services from explicit `tenant_id`/`user_id` parameters to deriving them from `self.request_context`.

## Core Pattern

### Before (Anti-pattern)
```python
def some_method(self, tenant_id: str, user_id: str, target_id: str):
    # Method explicitly requires tenant_id and user_id
    pass
```

### After (Correct pattern)
```python
def some_method(self, target_id: str):
    tenant_id = self.request_context.target_tenant_id
    user_id = self.request_context.target_user_id
    # tenant/user derived from authenticated context
    pass
```

## Common Patterns by Method Type

### 1. Invitation/Assignment Methods
**Pattern**: Distinguish between the actor (from context) and the target (parameter)

```python
# BEFORE
def invite(self, event_id: str, user_id: str, invited_by_user_id: str):
    pass

# AFTER
def invite(self, event_id: str, **kwargs):
    inviter_user_id = self.request_context.target_user_id  # Who's doing the inviting
    invitee_user_id = kwargs.pop('invitee_user_id', inviter_user_id)  # Who's being invited
    pass
```

**Examples**:
- `EventAttendeeService.invite()` - inviter from context, invitee from parameter
- `EventAttendeeService.add_host()` - adder from context, new host from parameter
- `FileShareService.create()` - sharer from context, recipient from parameter

### 2. State Update Methods
**Pattern**: Actor from context, target and new state from parameters

```python
# BEFORE
def update_status(self, resource_id: str, user_id: str, new_status: str):
    pass

# AFTER
def update_status(self, resource_id: str, new_status: str):
    updated_by_user_id = self.request_context.target_user_id
    pass
```

**Examples**:
- `EventAttendeeService.update_rsvp()` - updater from context
- `EventAttendeeService.check_in()` - checker from context, attendee from parameter
- `SubscriptionService.update_status()` - updater from context

### 3. List/Query Methods
**Pattern**: Tenant filtering from context, other filters from parameters

```python
# BEFORE
def list_by_tenant(self, tenant_id: str, status: str = None):
    pass

# AFTER
def list_by_tenant(self, status: str = None):
    tenant_id = self.request_context.target_tenant_id
    pass
```

**Examples**:
- `EventAttendeeService.list_by_event()` - tenant isolation from context
- `UserService.get_users_by_tenant()` - target tenant from context
- `VoteSummaryService.list_by_tenant()` - tenant from context

### 4. Access Control Methods
**Pattern**: Requester from context, resource and permissions from parameters

```python
# BEFORE
def check_access(self, user_id: str, resource_id: str, permission: str):
    pass

# AFTER
def check_access(self, resource_id: str, permission: str):
    requesting_user_id = self.request_context.target_user_id
    pass
```

## Test Update Patterns

### Pattern 1: Update Fixtures
```python
# BEFORE
@pytest.fixture
def service(db):
    test_context = AnonymousContextFactory.create_test_context(user_id='test_user')
    return MyService(db, TABLE_NAME, request_context=test_context)

# AFTER  
@pytest.fixture
def service(db, test_context):
    return MyService(db, TABLE_NAME, request_context=test_context)
```

### Pattern 2: Remove Explicit Parameters from Test Calls
```python
# BEFORE
result = service.invite(
    event_id=event_id,
    user_id="user_guest1",  # ❌ Remove
    invited_by_user_id="user_owner",  # ❌ Remove
    role="attendee"
)

# AFTER
result = service.invite(
    event_id=event_id,
    invitee_user_id="user_guest1",  # ✅ Rename to distinguish from actor
    role="attendee"
)
# inviter comes from test_context (test_user)
```

### Pattern 3: Update Assertions
```python
# BEFORE
assert result.data.invited_by_user_id == "user_owner"

# AFTER
assert result.data.invited_by_user_id == "test_user"  # From test_context
```

## Service-Specific Patterns

### EventAttendeeService
```python
# invite() - inviter from context
def invite(self, event_id: str, **kwargs):
    inviter = self.request_context.target_user_id
    invitee = kwargs.pop('invitee_user_id', inviter)

# add_host() - adder from context
def add_host(self, event_id: str, **kwargs):
    added_by = self.request_context.target_user_id
    host_user_id = kwargs.pop('host_user_id')

# check_in() - checker from context  
def check_in(self, event_id: str, attendee_user_id: str):
    checked_in_by = self.request_context.target_user_id
```

### UserService
```python
# get_users_by_tenant() - tenant from context
def get_users_by_tenant(self, status: str = None):
    tenant_id = self.request_context.target_tenant_id

# update() - updater from context
def update(self, user_id: str, updates: Dict):
    updated_by = self.request_context.target_user_id
```

### TenantService
```python
# get_user_count() - tenant from context
def get_user_count(self):
    tenant_id = self.request_context.target_tenant_id

# can_add_user() - tenant from context
def can_add_user(self):
    tenant_id = self.request_context.target_tenant_id
```

## Backward Compatibility Strategies

### 1. Support Both Parameter Names (Temporary)
```python
def method(self, **kwargs):
    # Support old and new parameter names during migration
    value = kwargs.pop('new_name', None) or kwargs.pop('old_name', None)
```

### 2. Deprecation Warnings
```python
import warnings

def method(self, tenant_id: str = None, **kwargs):
    if tenant_id is not None:
        warnings.warn("tenant_id parameter is deprecated, use request_context",
                      DeprecationWarning, stacklevel=2)
    tenant_id = tenant_id or self.request_context.target_tenant_id
```

## Testing Multi-User Scenarios

Use service factories for clear multi-user tests:

```python
@pytest.fixture
def service_factory(db):
    def _create(user_id='test_user', tenant_id='tenant_123'):
        context = AnonymousContextFactory.create_test_context(
            user_id=user_id, tenant_id=tenant_id
        )
        return MyService(db, TABLE_NAME, request_context=context)
    return _create

def test_multi_user_scenario(service_factory):
    owner = service_factory(user_id='owner')
    guest = service_factory(user_id='guest')
    
    # Owner creates resource
    resource = owner.create(...)
    
    # Guest attempts access
    result = guest.get_by_id(resource.id)
```

## Common Pitfalls

### ❌ Pitfall 1: Confusing Actor with Target
```python
# WRONG - using inviter's ID for both
def invite(self, event_id: str):
    user_id = self.request_context.target_user_id
    attendee.user_id = user_id  # ❌ This makes inviter the attendee!
    attendee.invited_by_user_id = user_id  # ❌ Same person
```

### ❌ Pitfall 2: Removing Necessary Parameters
```python
# WRONG - removed the target user entirely
def update_rsvp(self, event_id: str, status: str):
    user_id = self.request_context.target_user_id
    # ❌ Can only update own RSVP now, can't update for others (admin use case)
```

### ❌ Pitfall 3: Not Updating Internal Calls
```python
def parent_method(self, resource_id: str):
    tenant_id = self.request_context.target_tenant_id
    # ❌ Still passing explicit tenant_id to child method
    return self.child_method(resource_id, tenant_id)
```

## Checklist for Each Service Method

- [ ] Remove `tenant_id` from signature if it should come from context
- [ ] Remove `user_id` from signature if it's the actor (not the target)
- [ ] Rename remaining user parameters to clarify role (invitee_user_id, target_user_id, etc.)
- [ ] Add `tenant_id = self.request_context.target_tenant_id` at method start
- [ ] Add `user_id = self.request_context.target_user_id` for actor tracking
- [ ] Update all internal method calls to match new signatures
- [ ] Update corresponding tests to remove explicit parameters
- [ ] Update test assertions to expect context-derived values
- [ ] Verify multi-tenant isolation still works
