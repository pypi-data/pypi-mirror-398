# File System Lambda Handlers

Lambda handlers for the file system with lineage tracking support.

---

## Handler Structure

```
handlers/
├── files/              # Basic file operations
│   ├── create/         # Upload file
│   ├── get/            # Get file metadata
│   ├── download/       # Download file content
│   └── list/           # List files
│
└── lineage/            # Lineage operations
    ├── get_lineage/    # Get file lineage
    ├── create_main/    # Create main file from original
    ├── create_derived/ # Create derived file from main
    ├── prepare_bundle/ # Prepare lineage bundle (metadata only)
    └── download_bundle/# Download complete bundle (with content)
```

---

## File Operations

### POST /files - Upload File

**Handler:** `files/create/app.py`

**Body:**
```json
{
  "fileName": "document.pdf",
  "fileData": "base64_encoded_content",
  "mimeType": "application/pdf",
  "directoryId": "dir-123",
  "versioningStrategy": "explicit",
  "description": "Q1 Report",
  "tags": ["report", "2024"],
  
  // Optional lineage fields:
  "fileRole": "original",
  "parentFileId": "file-parent",
  "originalFileId": "file-original",
  "transformationType": "convert",
  "transformationOperation": "xls_to_csv",
  "transformationMetadata": {
    "source_format": "xls",
    "target_format": "csv"
  }
}
```

**Response:** `201` with file metadata

---

### GET /files/{fileId} - Get File Metadata

**Handler:** `files/get/app.py`

**Path Parameters:**
- `fileId` - File ID

**Response:** `200` with file metadata including lineage fields

---

### GET /files/{fileId}/download - Download File

**Handler:** `files/download/app.py`

**Path Parameters:**
- `fileId` - File ID

**Response:** `200` with:
```json
{
  "file_id": "file-123",
  "file_name": "document.pdf",
  "mime_type": "application/pdf",
  "file_size": 12345,
  "file_data": "base64_encoded_content",
  "content_type": "application/pdf"
}
```

---

### GET /files - List Files

**Handler:** `files/list/app.py`

**Query Parameters:**
- `directoryId` (optional) - Filter by directory
- `ownerId` (optional) - Filter by owner (defaults to current user)
- `limit` (optional) - Max results (default: 100)

**Response:** `200` with array of file objects

---

## Lineage Operations

### GET /files/{fileId}/lineage - Get File Lineage

**Handler:** `lineage/get_lineage/app.py`

**Path Parameters:**
- `fileId` - File ID

**Response:** `200` with:
```json
{
  "selected": {file object},
  "main": {file object or null},
  "original": {file object or null},
  "allDerived": [{file objects}]
}
```

---

### POST /files/lineage/main - Create Main File

**Handler:** `lineage/create_main/app.py`

Convert an original file to a main file (e.g., XLS → CSV).

**Body:**
```json
{
  "originalFileId": "file-123",
  "fileName": "data.csv",
  "fileData": "base64_encoded_content",
  "mimeType": "text/csv",
  "transformationOperation": "xls_to_csv",
  "transformationMetadata": {
    "source_format": "xls",
    "target_format": "csv",
    "converter_version": "1.0"
  },
  "directoryId": "dir-456"
}
```

**Response:** `201` with main file metadata

---

### POST /files/lineage/derived - Create Derived File

**Handler:** `lineage/create_derived/app.py`

Create a derived file from a main file (e.g., data cleaning).

**Body:**
```json
{
  "mainFileId": "file-456",
  "fileName": "data_clean_v1.csv",
  "fileData": "base64_encoded_content",
  "transformationOperation": "data_cleaning_v1",
  "transformationMetadata": {
    "cleaning_version": 1,
    "operations": ["remove_nulls", "normalize_units"],
    "rows_processed": 1000
  },
  "directoryId": "dir-789"
}
```

**Response:** `201` with derived file metadata

---

### GET /files/{fileId}/bundle - Prepare Lineage Bundle

**Handler:** `lineage/prepare_bundle/app.py`

Get bundle metadata without file content (lightweight).

**Path Parameters:**
- `fileId` - File ID

**Response:** `200` with:
```json
{
  "selectedFile": {file object},
  "mainFile": {file object},
  "originalFile": {file object},
  "metadata": {
    "selectedFileId": "...",
    "selectedFileName": "...",
    "transformationChain": [
      {"step": 1, "type": "original", "fileId": "...", "fileName": "..."},
      {"step": 2, "type": "convert", "fileId": "...", "fileName": "...", "operation": "..."},
      {"step": 3, "type": "clean", "fileId": "...", "fileName": "...", "operation": "..."}
    ]
  }
}
```

---

### GET /files/{fileId}/bundle/download - Download Lineage Bundle

**Handler:** `lineage/download_bundle/app.py`

Download complete bundle with file content (heavier).

**Path Parameters:**
- `fileId` - File ID

**Response:** `200` with:
```json
{
  "selected": {
    "file": {file object},
    "data": "base64_encoded_content"
  },
  "main": {
    "file": {file object},
    "data": "base64_encoded_content"
  },
  "original": {
    "file": {file object},
    "data": "base64_encoded_content"
  },
  "metadata": {transformation chain}
}
```

---

## API Gateway Configuration

### Example SAM Template

```yaml
Resources:
  # File Operations
  FileUpload:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: handlers/files/create/
      Handler: app.handler
      Events:
        ApiEvent:
          Type: Api
          Properties:
            Path: /files
            Method: POST
            Auth:
              Authorizer: CognitoAuthorizer

  FileGet:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: handlers/files/get/
      Handler: app.handler
      Events:
        ApiEvent:
          Type: Api
          Properties:
            Path: /files/{fileId}
            Method: GET
            Auth:
              Authorizer: CognitoAuthorizer

  FileDownload:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: handlers/files/download/
      Handler: app.handler
      Events:
        ApiEvent:
          Type: Api
          Properties:
            Path: /files/{fileId}/download
            Method: GET
            Auth:
              Authorizer: CognitoAuthorizer

  FileList:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: handlers/files/list/
      Handler: app.handler
      Events:
        ApiEvent:
          Type: Api
          Properties:
            Path: /files
            Method: GET
            Auth:
              Authorizer: CognitoAuthorizer

  # Lineage Operations
  GetLineage:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: handlers/lineage/get_lineage/
      Handler: app.handler
      Events:
        ApiEvent:
          Type: Api
          Properties:
            Path: /files/{fileId}/lineage
            Method: GET
            Auth:
              Authorizer: CognitoAuthorizer

  CreateMain:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: handlers/lineage/create_main/
      Handler: app.handler
      Events:
        ApiEvent:
          Type: Api
          Properties:
            Path: /files/lineage/main
            Method: POST
            Auth:
              Authorizer: CognitoAuthorizer

  CreateDerived:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: handlers/lineage/create_derived/
      Handler: app.handler
      Events:
        ApiEvent:
          Type: Api
          Properties:
            Path: /files/lineage/derived
            Method: POST
            Auth:
              Authorizer: CognitoAuthorizer

  PrepareBundle:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: handlers/lineage/prepare_bundle/
      Handler: app.handler
      Events:
        ApiEvent:
          Type: Api
          Properties:
            Path: /files/{fileId}/bundle
            Method: GET
            Auth:
              Authorizer: CognitoAuthorizer

  DownloadBundle:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: handlers/lineage/download_bundle/
      Handler: app.handler
      Events:
        ApiEvent:
          Type: Api
          Properties:
            Path: /files/{fileId}/bundle/download
            Method: GET
            Auth:
              Authorizer: CognitoAuthorizer
```

---

## Authentication

All handlers require secure authentication (Cognito JWT tokens).

**Required User Context:**
- `user_id` - User performing the action
- `tenant_id` - Organization/tenant ID
- `email` - User email (optional)

---

## Error Responses

All handlers return standard error responses:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "file_name is required",
    "details": {"field": "file_name"}
  }
}
```

**Common Error Codes:**
- `VALIDATION_ERROR` - Invalid input
- `NOT_FOUND` - File not found
- `ACCESS_DENIED` - Insufficient permissions
- `INVALID_FILE_ROLE` - Lineage role mismatch

---

## Testing

Each handler can be tested independently:

```python
from handlers.files.create import app

# Mock event
event = {
    "body": json.dumps({
        "fileName": "test.txt",
        "fileData": base64.b64encode(b"test").decode(),
        "mimeType": "text/plain"
    }),
    "requestContext": {
        "authorizer": {
            "claims": {
                "sub": "user-123",
                "custom:tenant_id": "tenant-456"
            }
        }
    }
}

# Test
result = app.lambda_handler(event, None)
print(result)
```

---

## Next Steps

1. Deploy handlers using SAM/CloudFormation
2. Configure API Gateway routes
3. Set up Cognito authorizer
4. Test each endpoint
5. Monitor CloudWatch logs
