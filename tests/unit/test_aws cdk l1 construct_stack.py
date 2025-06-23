import aws_cdk as core
import aws_cdk.assertions as assertions

from aws cdk l1 construct.aws cdk l1 construct_stack import AwsCdkL1ConstructStack

# example tests. To run these tests, uncomment this file along with the example
# resource in aws cdk l1 construct/aws cdk l1 construct_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = AwsCdkL1ConstructStack(app, "aws-cdk-l1-construct")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
