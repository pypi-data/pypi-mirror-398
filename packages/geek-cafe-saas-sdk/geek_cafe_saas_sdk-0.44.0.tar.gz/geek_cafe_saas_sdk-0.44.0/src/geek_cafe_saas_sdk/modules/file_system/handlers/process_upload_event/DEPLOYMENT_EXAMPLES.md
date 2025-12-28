# S3 Upload Event Router - Deployment Examples

The `process_upload_event` handler is a **reusable template** configured entirely through environment variables. Deploy it with different configurations without changing code!

---

## 🎯 Use Cases

### 1. EventBridge Fan-Out (Recommended)

**Best for:** Multiple consumers need to react to file uploads

```yaml
# SAM template.yaml
ProcessUploadEventFunction:
  Type: AWS::Serverless::Function
  Properties:
    Handler: geek_cafe_saas_sdk.modules.files.handlers.process_upload_event.app.lambda_handler
    Runtime: python3.11
    Environment:
      Variables:
        ROUTING_STRATEGY: eventbridge
        EVENTBRIDGE_BUS_NAME: file-system-events
        EVENT_SOURCE: file-system.s3
        EVENT_DETAIL_TYPE: FileUploaded
        FILTER_PREFIX: uploads/    # Only process uploads/ folder
    Events:
      S3Upload:
        Type: S3
        Properties:
          Bucket: !Ref UploadBucket
          Events: s3:ObjectCreated:*
          Filter:
            S3Key:
              Rules:
                - Name: prefix
                  Value: uploads/
```

**Then create EventBridge rules** for downstream processing:

```yaml
# Metadata updater rule
UpdateMetadataRule:
  Type: AWS::Events::Rule
  Properties:
    EventBusName: file-system-events
    EventPattern:
      source:
        - file-system.s3
      detail-type:
        - FileUploaded
    Targets:
      - Arn: !GetAtt UpdateFileMetadataFunction.Arn
        Id: UpdateMetadata

# Virus scanner rule
VirusScanRule:
  Type: AWS::Events::Rule
  Properties:
    EventBusName: file-system-events
    EventPattern:
      source:
        - file-system.s3
      detail-type:
        - FileUploaded
    Targets:
      - Arn: !GetAtt VirusScanFunction.Arn
        Id: VirusScan

# Thumbnail generator rule (only for images)
ThumbnailRule:
  Type: AWS::Events::Rule
  Properties:
    EventBusName: file-system-events
    EventPattern:
      source:
        - file-system.s3
      detail-type:
        - FileUploaded
      detail:
        key:
          - suffix: .jpg
          - suffix: .png
          - suffix: .gif
    Targets:
      - Arn: !GetAtt GenerateThumbnailFunction.Arn
        Id: GenerateThumbnail
```

---

### 2. SQS Queue for Sequential Processing

**Best for:** Single workflow processes uploads sequentially

```yaml
# SAM template.yaml
ProcessUploadEventFunction:
  Type: AWS::Serverless::Function
  Properties:
    Handler: geek_cafe_saas_sdk.modules.files.handlers.process_upload_event.app.lambda_handler
    Runtime: python3.11
    Environment:
      Variables:
        ROUTING_STRATEGY: sqs
        SQS_QUEUE_URL: !Ref FileProcessingQueue
        FILTER_PREFIX: uploads/
    Events:
      S3Upload:
        Type: S3
        Properties:
          Bucket: !Ref UploadBucket
          Events: s3:ObjectCreated:*

FileProcessingQueue:
  Type: AWS::SQS::Queue
  Properties:
    QueueName: file-processing-queue
    VisibilityTimeout: 300
    RedrivePolicy:
      deadLetterTargetArn: !GetAtt DeadLetterQueue.Arn
      maxReceiveCount: 3

# Consumer function
FileProcessorFunction:
  Type: AWS::Serverless::Function
  Properties:
    Handler: process_file.lambda_handler
    Events:
      QueueEvent:
        Type: SQS
        Properties:
          Queue: !GetAtt FileProcessingQueue.Arn
          BatchSize: 10
```

---

### 3. Direct Lambda Invocation

**Best for:** Simple workflows with single processor

```yaml
# SAM template.yaml
ProcessUploadEventFunction:
  Type: AWS::Serverless::Function
  Properties:
    Handler: geek_cafe_saas_sdk.modules.files.handlers.process_upload_event.app.lambda_handler
    Runtime: python3.11
    Environment:
      Variables:
        ROUTING_STRATEGY: lambda
        TARGET_LAMBDA_ARN: !GetAtt FileProcessorFunction.Arn
    Events:
      S3Upload:
        Type: S3
        Properties:
          Bucket: !Ref UploadBucket
          Events: s3:ObjectCreated:*
    Policies:
      - LambdaInvokePolicy:
          FunctionName: !Ref FileProcessorFunction

FileProcessorFunction:
  Type: AWS::Serverless::Function
  Properties:
    Handler: process_file.lambda_handler
    Runtime: python3.11
```

---

### 4. Logging Only (Testing/Development)

**Best for:** Testing S3 events without processing

```yaml
ProcessUploadEventFunction:
  Type: AWS::Serverless::Function
  Properties:
    Handler: geek_cafe_saas_sdk.modules.files.handlers.process_upload_event.app.lambda_handler
    Runtime: python3.11
    Environment:
      Variables:
        ROUTING_STRATEGY: none
        POWERTOOLS_SERVICE_NAME: s3-event-logger
        LOG_LEVEL: DEBUG
    Events:
      S3Upload:
        Type: S3
        Properties:
          Bucket: !Ref UploadBucket
          Events: s3:ObjectCreated:*
```

---

## 🎛️ Configuration Options

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ROUTING_STRATEGY` | No | `eventbridge` | How to route: `eventbridge`, `sqs`, `lambda`, `none` |
| `EVENTBRIDGE_BUS_NAME` | For EventBridge | `default` | EventBridge bus name |
| `EVENT_SOURCE` | No | `file-system.s3` | Event source name |
| `EVENT_DETAIL_TYPE` | No | `FileUploaded` | EventBridge detail type |
| `SQS_QUEUE_URL` | For SQS | - | SQS queue URL |
| `TARGET_LAMBDA_ARN` | For Lambda | - | Target Lambda function ARN |
| `FILTER_PREFIX` | No | - | Only process keys with this prefix |
| `FILTER_SUFFIX` | No | - | Only process keys with this suffix |
| `POWERTOOLS_SERVICE_NAME` | No | - | Service name for logging |
| `LOG_LEVEL` | No | `INFO` | Log level: DEBUG, INFO, WARN, ERROR |

---

## 📦 Event Payload Format

The handler extracts and forwards this payload:

```json
{
  "bucket": "my-upload-bucket",
  "key": "uploads/tenant-123/file.pdf",
  "size": 1024576,
  "etag": "d41d8cd98f00b204e9800998ecf8427e",
  "eventTime": "2025-11-25T12:34:56.789Z",
  "eventName": "ObjectCreated:Put",
  "requestParameters": {
    "sourceIPAddress": "203.0.113.5"
  },
  "responseElements": {
    "x-amz-request-id": "C3D13FE58DE4C810",
    "x-amz-id-2": "..."
  }
}
```

---

## 🚀 Advanced Examples

### Multi-Stage Processing

```yaml
# Stage 1: S3 → EventBridge (fan-out)
ProcessUploadEventFunction:
  Environment:
    Variables:
      ROUTING_STRATEGY: eventbridge
      EVENTBRIDGE_BUS_NAME: file-system-events

# Stage 2: EventBridge → SQS (specific workflows)
UpdateMetadataRule:
  Targets:
    - Arn: !GetAtt MetadataQueue.Arn

# Stage 3: SQS → Lambda (batch processing)
UpdateMetadataFunction:
  Events:
    QueueEvent:
      Type: SQS
      Properties:
        Queue: !GetAtt MetadataQueue.Arn
        BatchSize: 10
```

### Filtered Routing

```yaml
# Only process PDFs in uploads/documents/
Environment:
  Variables:
    ROUTING_STRATEGY: eventbridge
    FILTER_PREFIX: uploads/documents/
    FILTER_SUFFIX: .pdf
```

### Multi-Tenant Routing

```yaml
# Separate processing per tenant
ProcessTenant1Function:
  Environment:
    Variables:
      ROUTING_STRATEGY: sqs
      SQS_QUEUE_URL: !Ref Tenant1Queue
      FILTER_PREFIX: uploads/tenant-1/

ProcessTenant2Function:
  Environment:
    Variables:
      ROUTING_STRATEGY: sqs
      SQS_QUEUE_URL: !Ref Tenant2Queue
      FILTER_PREFIX: uploads/tenant-2/
```

---

## 📊 IAM Permissions

### For EventBridge

```yaml
Policies:
  - Statement:
      - Effect: Allow
        Action:
          - events:PutEvents
        Resource: !Sub arn:aws:events:${AWS::Region}:${AWS::AccountId}:event-bus/file-system-events
```

### For SQS

```yaml
Policies:
  - Statement:
      - Effect: Allow
        Action:
          - sqs:SendMessage
        Resource: !GetAtt FileProcessingQueue.Arn
```

### For Lambda

```yaml
Policies:
  - LambdaInvokePolicy:
      FunctionName: !Ref TargetFunction
```

---

## 🧪 Testing

### Test with AWS CLI

```bash
# Invoke with sample S3 event
aws lambda invoke \
  --function-name process-upload-event \
  --payload file://test-event.json \
  response.json

cat response.json
```

### Sample test event (`test-event.json`):

```json
{
  "Records": [
    {
      "eventVersion": "2.1",
      "eventSource": "aws:s3",
      "eventTime": "2025-11-25T12:34:56.000Z",
      "eventName": "ObjectCreated:Put",
      "s3": {
        "bucket": {
          "name": "my-upload-bucket"
        },
        "object": {
          "key": "uploads/test-file.pdf",
          "size": 1024,
          "eTag": "d41d8cd98f00b204e9800998ecf8427e"
        }
      }
    }
  ]
}
```

---

## 💡 Best Practices

1. **Use EventBridge for flexibility** - Easy to add new consumers
2. **Set appropriate filters** - Process only relevant files
3. **Monitor with CloudWatch** - Track routing success/failures
4. **Use dead letter queues** - Capture failed events
5. **Keep handler lightweight** - <100ms execution time
6. **Tag your resources** - Track costs per workflow

---

## 🎓 Migration from Old Handler

If you have the old `FileUploadProcessor` implementation:

1. **Deploy new handler** with `ROUTING_STRATEGY=eventbridge`
2. **Create EventBridge rule** that invokes old processor
3. **Test in parallel** (both handlers run temporarily)
4. **Switch S3 trigger** to new handler once validated
5. **Deprecate old handler**

---

**This handler is production-ready and fully configurable!** 🚀
