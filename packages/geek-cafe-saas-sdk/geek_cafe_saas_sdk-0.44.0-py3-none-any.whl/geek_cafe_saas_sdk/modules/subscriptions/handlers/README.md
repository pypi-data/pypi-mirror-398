# Subscriptions Domain Handlers

Lambda handlers for subscription management operations.

## Directory Structure

```
handlers/
├── plans/
│   ├── list/app.py          # GET /plans
│   ├── get/app.py           # GET /plans/{planId}
│   ├── create/app.py        # POST /plans (admin)
│   └── update/app.py        # PATCH /plans/{planId} (admin)
├── addons/
│   ├── list/app.py          # GET /addons
│   ├── get/app.py           # GET /addons/{addonId}
│   ├── create/app.py        # POST /addons (admin)
│   └── update/app.py        # PATCH /addons/{addonId} (admin)
├── discounts/
│   ├── validate/app.py      # POST /discounts/validate
│   ├── create/app.py        # POST /discounts (admin)
│   └── get/app.py           # GET /discounts/{discountId} (admin)
└── usage/
    ├── record/app.py        # POST /usage
    └── aggregate/app.py     # GET /usage/aggregate
```

---

## Plan Handlers

### GET /plans
List public subscription plans.

**Authentication:** None (public endpoint)

**Query Parameters:**
- `status` (string, optional) - Filter by status (default: "active")
- `isPublic` (boolean, optional) - Filter by visibility (default: true)
- `limit` (integer, optional) - Max results (default: 50)

**Response:** 200 OK
```json
{
  "success": true,
  "data": [
    {
      "id": "plan-123",
      "planCode": "pro",
      "planName": "Pro Plan",
      "priceMonthly Cents": 2999,
      "priceAnnualCents": 29990,
      "features": {...},
      "limits": {...}
    }
  ]
}
```

### GET /plans/{planId}
Get a specific plan.

**Authentication:** None (public endpoint)

**Path Parameters:**
- `planId` (string, required) - Plan ID

**Response:** 200 OK

### POST /plans (Admin)
Create a new plan.

**Authentication:** Required (admin)

**Request Body:**
```json
{
  "planCode": "enterprise",
  "planName": "Enterprise Plan",
  "priceMonthly Cents": 9999,
  "description": "For large teams",
  "features": {
    "api_access": true,
    "sso": true,
    "white_label": true
  },
  "limits": {
    "max_projects": -1,
    "max_storage_gb": 1000
  }
}
```

**Response:** 201 Created

### PATCH /plans/{planId} (Admin)
Update a plan.

**Authentication:** Required (admin)

**Request Body:** Fields to update

**Response:** 200 OK

---

## Addon Handlers

### GET /addons
List public addons.

**Authentication:** None (public endpoint)

**Query Parameters:**
- `status` (string, optional) - Filter by status
- `category` (string, optional) - Filter by category
- `limit` (integer, optional) - Max results

**Response:** 200 OK

### GET /addons/{addonId}
Get a specific addon.

**Authentication:** None (public endpoint)

**Response:** 200 OK

### POST /addons (Admin)
Create a new addon.

**Authentication:** Required (admin)

**Request Body:**
```json
{
  "addonCode": "chat",
  "addonName": "Chat Module",
  "pricingModel": "fixed",
  "priceMonthly Cents": 1500,
  "description": "Real-time chat",
  "category": "communication",
  "features": {
    "realtime_messaging": true,
    "file_sharing": true
  }
}
```

**Response:** 201 Created

### PATCH /addons/{addonId} (Admin)
Update an addon.

**Authentication:** Required (admin)

**Response:** 200 OK

---

## Discount Handlers

### POST /discounts/validate
Validate a discount code.

**Authentication:** None (public endpoint)

**Request Body:**
```json
{
  "discountCode": "SUMMER25",
  "planCode": "pro",
  "amountCents": 2999,
  "isFirstPurchase": false
}
```

**Response:** 200 OK (if valid)
```json
{
  "success": true,
  "data": {
    "id": "discount-123",
    "discountCode": "SUMMER25",
    "discountType": "percentage",
    "percentOff": 25.0,
    "duration": "repeating",
    "durationInMonths": 3
  }
}
```

**Error Response:** 400 Bad Request (if invalid)
```json
{
  "success": false,
  "message": "Discount code is not currently valid"
}
```

### POST /discounts (Admin)
Create a new discount.

**Authentication:** Required (admin)

**Request Body:**
```json
{
  "discountCode": "WELCOME50",
  "discountName": "Welcome Discount",
  "discountType": "percentage",
  "percentOff": 50.0,
  "duration": "once",
  "maxRedemptions": 1000,
  "firstTimeTransaction": true
}
```

**Response:** 201 Created

### GET /discounts/{discountId} (Admin)
Get a discount by ID.

**Authentication:** Required (admin)

**Response:** 200 OK

---

## Usage Handlers

### POST /usage
Record a usage event for metered billing.

**Authentication:** Required

**Request Body:**
```json
{
  "subscriptionId": "sub-123",
  "addonCode": "extra_storage",
  "meterEventName": "storage_gb",
  "quantity": 50.5,
  "action": "increment",
  "idempotencyKey": "unique-key-123",
  "metadata": {
    "source": "api"
  }
}
```

**Response:** 201 Created

### GET /usage/aggregate
Get aggregated usage for a period.

**Authentication:** Required

**Query Parameters:**
- `subscriptionId` (string, required)
- `addonCode` (string, required)
- `periodStart` (timestamp, required)
- `periodEnd` (timestamp, required)

**Response:** 200 OK
```json
{
  "success": true,
  "data": 150.75
}
```

---

## Authentication

**Public Endpoints (no auth):**
- GET /plans
- GET /plans/{planId}
- GET /addons
- GET /addons/{addonId}
- POST /discounts/validate

**User Endpoints (auth required):**
- POST /usage
- GET /usage/aggregate

**Admin Endpoints (admin auth required):**
- POST /plans
- PATCH /plans/{planId}
- POST /addons
- PATCH /addons/{addonId}
- POST /discounts
- GET /discounts/{discountId}

---

## Error Handling

All handlers return standardized error responses:

```json
{
  "success": false,
  "message": "Error description",
  "errorCode": "ERROR_CODE"
}
```

**Common Error Codes:**
- `VALIDATION_ERROR` - Invalid input
- `NOT_FOUND` - Resource not found
- `INTERNAL_ERROR` - Server error

---

## Deployment

Each handler is designed to be deployed as a separate Lambda function with API Gateway integration.

### Example SAM Template

```yaml
PlanListFunction:
  Type: AWS::Serverless::Function
  Properties:
    CodeUri: src/geek_cafe_saas_sdk/modules/subscriptions/handlers/plans/list/
    Handler: app.handler
    Runtime: python3.11
    Events:
      ListPlans:
        Type: Api
        Properties:
          Path: /plans
          Method: get
```

---

## Testing

Handlers support dependency injection for testing:

```python
from handlers.plans.list.app import lambda_handler

# Mock service
class MockService:
    def list_plans(self, **kwargs):
        return ServiceResult.success_result([])

# Test
event = {"queryStringParameters": {"status": "active"}}
response = lambda_handler(event, None, injected_service=MockService())
```

---

## Request/Response Format

### Request Format

Handlers automatically convert camelCase to snake_case:

```json
{
  "planCode": "pro",        // Converted to plan_code
  "priceMonthly Cents": 2999  // Converted to price_monthly_cents
}
```

### Response Format

All responses follow the ServiceResult pattern:

**Success:**
```json
{
  "success": true,
  "data": {...}
}
```

**Error:**
```json
{
  "success": false,
  "message": "Error message",
  "errorCode": "ERROR_CODE"
}
```

---

## Environment Variables

Required environment variables:

- `DYNAMODB_TABLE_NAME` - DynamoDB table name
- `AWS_REGION` - AWS region

---

## Notes

- Plan and addon handlers are public to allow pricing page display
- Usage handlers require authentication to prevent abuse
- Discount validation is public but discount management is admin-only
- All admin operations should implement proper authorization checks
