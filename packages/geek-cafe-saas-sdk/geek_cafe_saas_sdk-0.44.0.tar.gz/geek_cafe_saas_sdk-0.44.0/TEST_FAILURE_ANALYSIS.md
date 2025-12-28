# Test Failure Analysis & Fix Plan

## Summary
**Current State**: 1230 passed ✅ | 101 failed ❌ | 31 errors ⚠️ (Cognito)

**Root Cause**: Service methods still using explicit `tenant_id`/`user_id` parameters instead of deriving from `self.request_context`

## Failure Breakdown by Service

### 1. EventAttendeeService (16 failures) - HIGH PRIORITY
**Issue**: Methods like `invite()`, `accept_invitation()`, `decline_invitation()`, etc. expect explicit `user_id` parameter

**Failed Tests**:
- test_invite_single_user
- test_invite_with_registration_data
- test_add_co_host
- test_accept_invitation
- test_decline_invitation
- test_rsvp_with_plus_one
- test_wait_list_rsvp
- test_promote_from_wait_list
- test_check_in_attendee
- test_cannot_check_in_without_acceptance
- test_list_attendees_by_event
- test_list_attendees_by_status
- test_list_hosts
- test_get_attendee_count
- test_list_user_events
- test_remove_attendee

**Fix Strategy**: Update service methods to:
```python
def invite(self, event_id: str, invitee_user_id: str, **kwargs):
    tenant_id = self.request_context.target_tenant_id
    inviter_user_id = self.request_context.target_user_id  # Person doing the inviting
    # invitee_user_id stays as parameter (the person being invited)
```

### 2. Lambda Handler Tests (12 failures) - HIGH PRIORITY
**Issue**: Handlers may be passing explicit parameters to services

**Failed Tests**:
- test_create_event_success
- test_get_event_success
- test_update_event_success
- test_delete_event_success
- test_list_events_success
- test_list_events_with_filter
- test_invite_single_user
- test_bulk_invite
- test_invite_missing_event_id
- etc.

**Fix Strategy**: Update handlers to not pass `tenant_id`/`user_id` explicitly

### 3. UserService (7 failures)
**Issue**: Methods like `get_users_by_tenant()`, `update()` expecting explicit parameters

**Failed Tests**:
- test_get_users_by_tenant
- test_get_users_by_role
- test_update_user_success
- test_delete_user_prevent_self_delete_block
- test_restore_user_admin_only
- (+ 2 in test_user_service_complete.py)

**Fix Strategy**: Update service to use `self.request_context.target_tenant_id`

### 4. TenantService (6 failures)
**Issue**: Methods may need context-based tenant access control

**Failed Tests**:
- test_get_by_id_wrong_tenant
- test_update_tenant_success
- test_activate_deactivate
- test_get_user_count
- test_can_add_user_unlimited
- test_can_add_user_with_limit

### 5. WebsiteAnalyticsSummaryService (5 failures)
**Issue**: List/query methods expecting explicit `tenant_id`

**Failed Tests**:
- test_update_protects_immutable_fields
- test_list_by_tenant_and_type
- test_list_with_pagination_limit
- test_get_by_id_success
- test_get_by_id_not_found

### 6. EventService New Features (5 failures)
**Issue**: Location/status methods may need parameter updates

**Failed Tests**:
- test_list_by_city
- test_list_by_state
- test_list_nearby_events
- test_publish_draft_event
- test_cancel_event

### 7. SubscriptionService (2 failures)
**Issue**: Methods expecting explicit parameters

**Failed Tests**:
- test_create_subscription
- test_record_payment

### 8. VoteSummaryService (1 failure)
**Issue**: `list_by_tenant()` method

**Failed Test**:
- test_list_by_tenant

## Recommended Implementation Order

1. ✅ **EventAttendeeService** - Most failures, user-facing features
2. **Lambda Handlers** - Integration layer
3. **UserService** - Core authentication/authorization
4. **TenantService** - Multi-tenancy foundation
5. **WebsiteAnalyticsSummaryService** - Analytics features
6. **EventService** - Extended event features
7. **SubscriptionService** - Billing features
8. **VoteSummaryService** - Voting analytics

## Success Criteria
- All 101 failed tests passing
- No regressions in the 1230 currently passing tests
- Consistent `request_context` pattern across all services
