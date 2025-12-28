"""
Example: Lambda Event Logging Usage

Shows how Lambda event logging works with the SDK's handler framework.
No code changes needed - just set environment variable!

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import os
import json
from geek_cafe_saas_sdk.lambda_handlers import create_handler
from geek_cafe_saas_sdk.modules.votes.services.vote_service import VoteService


# =============================================================================
# Example 1: Basic Handler with Event Logging
# =============================================================================

def example_basic_logging():
    """
    Example showing automatic event logging.
    
    When LOG_LAMBDA_EVENTS=true, the event is automatically logged.
    No changes to your handler code required!
    """
    
    # Enable event logging (normally set in Lambda environment)
    os.environ["LOG_LAMBDA_EVENTS"] = "true"
    
    # Create handler as normal
    handler_wrapper = create_handler(
        service_class=VoteService,
        require_body=True,
        convert_case=True
    )
    
    def lambda_handler(event, context):
        """Your Lambda handler - unchanged!"""
        return handler_wrapper.execute(event, context, create_vote)
    
    def create_vote(event, service, user_context):
        """Your business logic - unchanged!"""
        payload = event["parsed_body"]
        return service.create_vote(
            tenant_id=user_context["tenant_id"],
            user_id=user_context["user_id"],
            vote_type=payload["vote_type"],
            target_id=payload["target_id"]
        )
    
    # Simulate Lambda invocation
    test_event = {
        "httpMethod": "POST",
        "path": "/api/votes",
        "headers": {
            "content-type": "application/json",
            "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        },
        "body": json.dumps({
            "vote_type": "upvote",
            "target_id": "item-123"
        }),
        "requestContext": {
            "authorizer": {
                "claims": {
                    "custom:user_id": "user-456",
                    "custom:tenant_id": "tenant-789"
                }
            }
        }
    }
    
    # When handler runs, event is automatically logged (sanitized)
    # CloudWatch will show:
    # INFO Lambda event received
    # {
    #   "event": {
    #     "httpMethod": "POST",
    #     "headers": {
    #       "authorization": "Bear...[MASKED]"
    #     },
    #     ...
    #   }
    # }
    
    print("✅ Event would be logged automatically when handler executes")
    print("✅ Sensitive fields (authorization) are sanitized")
    print("✅ No code changes required!")


# =============================================================================
# Example 2: Demonstration of Sanitization
# =============================================================================

def example_sanitization():
    """
    Example showing what sanitization does to sensitive data.
    """
    from geek_cafe_saas_sdk.utilities.logging_utility import LoggingUtility
    
    # Event with sensitive data
    event = {
        "httpMethod": "POST",
        "path": "/api/auth/login",
        "headers": {
            "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abc123xyz",
            "x-api-key": "sk_live_1234567890abcdefghij",
            "content-type": "application/json"
        },
        "body": json.dumps({
            "username": "john.doe",
            "password": "SuperSecret123!",
            "api_key": "internal_key_xyz",
            "remember_me": True
        }),
        "requestContext": {
            "accountId": "123456789012"
        }
    }
    
    print("\n" + "="*70)
    print("ORIGINAL EVENT (contains sensitive data):")
    print("="*70)
    print(json.dumps(event, indent=2))
    
    # Sanitize
    sanitized = LoggingUtility.sanitize_event_for_logging(event)
    
    print("\n" + "="*70)
    print("SANITIZED EVENT (safe for logging):")
    print("="*70)
    print(json.dumps(sanitized, indent=2))
    
    print("\n" + "="*70)
    print("WHAT WAS SANITIZED:")
    print("="*70)
    print("✅ authorization header: Masked to 'Bear...xyz'")
    print("✅ x-api-key header: Masked to 'sk_l...hij'")
    print("✅ password field: REDACTED completely")
    print("✅ api_key field: REDACTED completely")
    print("✅ Safe fields (username, remember_me) preserved")
    print("="*70)


# =============================================================================
# Example 3: Testing with Event Logging
# =============================================================================

def example_testing():
    """
    Example showing how to use event logging in tests.
    """
    
    print("\n" + "="*70)
    print("TESTING WITH EVENT LOGGING:")
    print("="*70)
    
    # Enable logging for this test
    os.environ["LOG_LAMBDA_EVENTS"] = "true"
    
    print("✅ Set LOG_LAMBDA_EVENTS=true for debugging")
    print("✅ Run your test")
    print("✅ Check test output - you'll see the event logged")
    print("✅ Verify your test event structure is correct")
    
    # In your actual test:
    # def test_vote_creation():
    #     os.environ["LOG_LAMBDA_EVENTS"] = "true"
    #     
    #     event = {...}  # Your test event
    #     response = lambda_handler(event, context)
    #     
    #     # Event will be logged, helping you debug test issues
    #     assert response["statusCode"] == 201
    
    # Disable after test
    os.environ["LOG_LAMBDA_EVENTS"] = "false"
    print("✅ Disable after debugging to reduce noise")


# =============================================================================
# Example 4: Production Debugging Workflow
# =============================================================================

def example_production_workflow():
    """
    Example workflow for debugging production issues.
    """
    
    print("\n" + "="*70)
    print("PRODUCTION DEBUGGING WORKFLOW:")
    print("="*70)
    
    workflow = """
    1. Issue Reported
       └─> "API returning 400 but logs unclear why"
    
    2. Enable Event Logging (NO DEPLOYMENT NEEDED!)
       └─> AWS Console: Set LOG_LAMBDA_EVENTS=true
       └─> OR CLI: aws lambda update-function-configuration ...
    
    3. Reproduce Issue
       └─> Invoke API endpoint
       └─> Check CloudWatch Logs
    
    4. See Exact Event Structure
       └─> CloudWatch shows:
           {
             "message": "Lambda event received",
             "event": {
               "body": "{\\"missing_field\\":\\"value\\"}",
               "headers": {...},
               ...
             }
           }
    
    5. Identify Issue
       └─> "Ah! Request is missing required field!"
    
    6. Fix and Verify
       └─> Fix client code
       └─> Test with logging still enabled
       └─> Confirm fix works
    
    7. Disable Logging
       └─> Set LOG_LAMBDA_EVENTS=false
       └─> Reduce log volume
    
    Total Time: 5-10 minutes vs hours of debugging!
    """
    
    print(workflow)


# =============================================================================
# Example 5: CloudWatch Insights Queries
# =============================================================================

def example_cloudwatch_queries():
    """
    Example CloudWatch Insights queries for event logs.
    """
    
    print("\n" + "="*70)
    print("CLOUDWATCH INSIGHTS QUERIES:")
    print("="*70)
    
    queries = {
        "All Event Logs": """
            fields @timestamp, @message, event.httpMethod, event.path
            | filter @message like /Lambda event received/
            | sort @timestamp desc
            | limit 20
        """,
        
        "POST Requests Only": """
            fields @timestamp, event.path, event.body
            | filter @message like /Lambda event received/
            | filter event.httpMethod = "POST"
            | sort @timestamp desc
        """,
        
        "Events with Errors": """
            fields @timestamp, event.path, event.body
            | filter @message like /Lambda event received/
            | filter event.body like /error/
            | sort @timestamp desc
        """,
        
        "Events by Path": """
            fields @timestamp, event.httpMethod
            | filter @message like /Lambda event received/
            | filter event.path = "/api/votes"
            | count() by event.httpMethod
        """,
        
        "Authorization Headers": """
            fields @timestamp, event.headers.authorization
            | filter @message like /Lambda event received/
            | filter event.headers.authorization like /Bearer/
        """
    }
    
    for name, query in queries.items():
        print(f"\n{name}:")
        print(query.strip())


# =============================================================================
# Run Examples
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("LAMBDA EVENT LOGGING EXAMPLES")
    print("=" * 70)
    
    # Example 1: Basic usage
    example_basic_logging()
    
    # Example 2: Sanitization demonstration
    example_sanitization()
    
    # Example 3: Testing
    example_testing()
    
    # Example 4: Production workflow
    example_production_workflow()
    
    # Example 5: CloudWatch queries
    example_cloudwatch_queries()
    
    print("\n" + "=" * 70)
    print("✅ ALL EXAMPLES COMPLETE")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("  • Set LOG_LAMBDA_EVENTS=true to enable")
    print("  • No code changes required")
    print("  • Sensitive data automatically sanitized")
    print("  • Works for all handlers using SDK")
    print("  • Disable when debugging complete")
    print("=" * 70)
