"""
Minimal type definitions for AWS Lambda
"""

from typing import Protocol, TypedDict, Optional, Dict


class LambdaContext(Protocol):
    """Minimal Lambda context protocol with only properties we use"""

    @property
    def request_id(self) -> str:
        """The identifier of the invocation request"""
        ...

    @property
    def function_name(self) -> Optional[str]:
        """The name of the Lambda function"""
        ...

    @property
    def function_version(self) -> Optional[str]:
        """The version of the function"""
        ...

    @property
    def aws_request_id(self) -> Optional[str]:
        """The AWS request ID"""
        ...


class APIGatewayRequestContext(TypedDict, total=False):
    """Request context from API Gateway event"""

    stage: str
    accountId: str
    requestId: str


class APIGatewayProxyEvent(TypedDict, total=False):
    """Minimal API Gateway proxy event with only fields we use"""

    httpMethod: str
    path: str
    headers: Dict[str, str]
    body: Optional[str]
    pathParameters: Optional[Dict[str, str]]
    queryStringParameters: Optional[Dict[str, str]]
    requestContext: APIGatewayRequestContext
    resource: str
