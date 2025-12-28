# Payment Handlers

Lambda handlers for payment operations.

## Structure

```
handlers/
├── billing_accounts/
│   ├── create/app.py    - POST /billing-accounts
│   ├── get/app.py       - GET /billing-accounts/{accountId}
│   └── update/app.py    - PATCH /billing-accounts/{accountId}
├── payment_intents/
│   ├── create/app.py    - POST /payment-intents
│   └── get/app.py       - GET /payment-intents/{intentId}
├── payments/
│   ├── record/app.py    - POST /payments (webhook handler)
│   ├── get/app.py       - GET /payments/{paymentId}
│   └── list/app.py      - GET /payments
└── refunds/
    ├── create/app.py    - POST /refunds
    └── get/app.py       - GET /refunds/{refundId}
```

## Billing Account Handlers

### POST /billing-accounts
**Handler:** `billing_accounts/create/app.py`  
**Purpose:** Create a new billing account

**Request Body:**
```json
{
  "accountHolderId": "user-123",
  "accountHolderType": "user",
  "currencyCode": "USD",
  "billingEmail": "user@example.com",
  "billingName": "John Doe",
  "addressLine1": "123 Main St",
  "addressCity": "San Francisco",
  "addressState": "CA",
  "addressPostalCode": "94105",
  "addressCountry": "US",
  "stripeCustomerId": "cus_xxx"
}
```

**Response:** 201 Created
```json
{
  "success": true,
  "data": {
    "accountId": "account-123",
    "accountHolderId": "user-123",
    "currencyCode": "USD",
    "status": "active",
    ...
  }
}
```

---

### GET /billing-accounts/{accountId}
**Handler:** `billing_accounts/get/app.py`  
**Purpose:** Retrieve billing account details

**Path Parameters:**
- `accountId` - Billing account ID

**Response:** 200 OK
```json
{
  "success": true,
  "data": {
    "accountId": "account-123",
    "accountHolderId": "user-123",
    "status": "active",
    ...
  }
}
```

---

### PATCH /billing-accounts/{accountId}
**Handler:** `billing_accounts/update/app.py`  
**Purpose:** Update billing account

**Path Parameters:**
- `accountId` - Billing account ID

**Request Body:**
```json
{
  "billingEmail": "newemail@example.com",
  "defaultPaymentMethodId": "pm_xxx",
  "autoChargeEnabled": true
}
```

**Response:** 200 OK

---

## Payment Intent Handlers

### POST /payment-intents
**Handler:** `payment_intents/create/app.py`  
**Purpose:** Create a payment intent for frontend payment flow

**Request Body:**
```json
{
  "billingAccountId": "account-123",
  "amountCents": 5000,
  "currencyCode": "USD",
  "description": "Subscription payment",
  "receiptEmail": "user@example.com"
}
```

**Response:** 201 Created
```json
{
  "success": true,
  "data": {
    "intentRefId": "intent-123",
    "pspClientSecret": "pi_xxx_secret_yyy",
    "status": "created",
    "amountCents": 5000,
    ...
  }
}
```

---

### GET /payment-intents/{intentId}
**Handler:** `payment_intents/get/app.py`  
**Purpose:** Retrieve payment intent status

**Path Parameters:**
- `intentId` - Payment intent reference ID

**Response:** 200 OK

---

## Payment Handlers

### POST /payments
**Handler:** `payments/record/app.py`  
**Purpose:** Record a settled payment (typically called from webhooks)

**Request Body:**
```json
{
  "billingAccountId": "account-123",
  "paymentIntentRefId": "intent-123",
  "grossAmountCents": 5000,
  "feeAmountCents": 145,
  "currencyCode": "USD",
  "pspType": "stripe",
  "pspTransactionId": "txn_xxx",
  "pspChargeId": "ch_xxx",
  "paymentMethodLast4": "4242",
  "paymentMethodBrand": "visa"
}
```

**Response:** 201 Created
```json
{
  "success": true,
  "data": {
    "paymentId": "payment-123",
    "grossAmountCents": 5000,
    "feeAmountCents": 145,
    "netAmountCents": 4855,
    "status": "succeeded",
    ...
  }
}
```

---

### GET /payments/{paymentId}
**Handler:** `payments/get/app.py`  
**Purpose:** Retrieve payment details

**Path Parameters:**
- `paymentId` - Payment ID

**Response:** 200 OK

---

### GET /payments
**Handler:** `payments/list/app.py`  
**Purpose:** List payments for tenant or billing account

**Query Parameters:**
- `billingAccountId` (optional) - Filter by billing account
- `limit` (optional) - Page size (default: 50, max: 100)

**Response:** 200 OK
```json
{
  "success": true,
  "data": [
    {
      "paymentId": "payment-123",
      "grossAmountCents": 5000,
      "settledUtcTs": 1697500000.0,
      ...
    }
  ]
}
```

---

## Refund Handlers

### POST /refunds
**Handler:** `refunds/create/app.py`  
**Purpose:** Create a refund for a payment

**Request Body:**
```json
{
  "paymentId": "payment-123",
  "amountCents": 5000,
  "reason": "requested_by_customer",
  "description": "Customer requested refund"
}
```

**Response:** 201 Created
```json
{
  "success": true,
  "data": {
    "refundId": "refund-123",
    "paymentId": "payment-123",
    "amountCents": 5000,
    "status": "pending",
    ...
  }
}
```

---

### GET /refunds/{refundId}
**Handler:** `refunds/get/app.py`  
**Purpose:** Retrieve refund status

**Path Parameters:**
- `refundId` - Refund ID

**Response:** 200 OK

---

## Authentication

All handlers require authentication. The `create_handler` factory automatically:
- Validates JWT tokens
- Extracts tenant_id and user_id from the token
- Returns 401 Unauthorized for invalid/missing tokens

## Error Handling

Handlers use the ServiceResult pattern for consistent error responses:

**Success Response:**
```json
{
  "success": true,
  "data": { ... }
}
```

**Error Response:**
```json
{
  "success": false,
  "message": "Error description",
  "errorCode": "ERROR_CODE",
  "statusCode": 400
}
```

## Common HTTP Status Codes

- **200 OK** - Successful GET/LIST operation
- **201 Created** - Successful POST/CREATE operation
- **400 Bad Request** - Validation error
- **401 Unauthorized** - Authentication failed
- **404 Not Found** - Resource not found
- **500 Internal Server Error** - Unexpected error

## Deployment

Each handler is packaged as a separate Lambda function:

```yaml
# SAM/CloudFormation template
CreateBillingAccountFunction:
  Type: AWS::Serverless::Function
  Properties:
    Handler: app.handler
    Runtime: python3.11
    CodeUri: modules/payments/handlers/billing_accounts/create/
    Events:
      Api:
        Type: Api
        Properties:
          Path: /billing-accounts
          Method: post
```

## Testing

See `tests/test_payment_handlers.py` for handler integration tests.

## Related Documentation

- **Service Layer:** `../services/payment_service.py`
- **Models:** `../models/`
- **User Guide:** `/docs/help/payments/`
