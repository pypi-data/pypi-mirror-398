# S3 Upload Event Router

**Lightweight, configurable S3 event router** - Deploy with different configs without changing code!

## 🎯 Purpose

This handler is **intentionally minimal**. It:
1. ✅ Receives S3 upload events
2. ✅ Validates and extracts event data
3. ✅ Routes to configured destination (EventBridge/SQS/Lambda)
4. ✅ Returns immediately (<100ms)

**It does NOT:**
- ❌ Process files directly
- ❌ Update metadata
- ❌ Make business logic decisions

## 🚀 Quick Start

Deploy with environment variables - no code changes needed!

### EventBridge (Recommended)

```yaml
Environment:
  Variables:
    ROUTING_STRATEGY: eventbridge
    EVENTBRIDGE_BUS_NAME: file-system-events
```

### SQS Queue

```yaml
Environment:
  Variables:
    ROUTING_STRATEGY: sqs
    SQS_QUEUE_URL: https://sqs.region.amazonaws.com/account/queue
```

### Direct Lambda

```yaml
Environment:
  Variables:
    ROUTING_STRATEGY: lambda
    TARGET_LAMBDA_ARN: arn:aws:lambda:region:account:function:processor
```

## 📚 Full Documentation

See [DEPLOYMENT_EXAMPLES.md](./DEPLOYMENT_EXAMPLES.md) for:
- Complete SAM template examples
- EventBridge rule patterns
- Multi-stage processing
- Testing instructions
- IAM permissions

## 🎓 Pattern: Separation of Concerns

```
S3 Event → Router (this) → EventBridge/SQS
                              ↓
                    Downstream Processors
                    - Update metadata
                    - Virus scan  
                    - Generate thumbnails
                    - ML pipeline
```

**Benefits:**
- ✅ Fast S3 response
- ✅ Decoupled workflows
- ✅ Easy to add new consumers
- ✅ Independent scaling
- ✅ Better error handling

## 💡 This is the Right Pattern!

Your instinct was correct - S3 event handlers should be lightweight routers, not heavy processors.