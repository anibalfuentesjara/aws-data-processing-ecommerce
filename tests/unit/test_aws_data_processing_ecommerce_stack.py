import aws_cdk as core
import aws_cdk.assertions as assertions

from aws_data_processing_ecommerce.aws_data_processing_ecommerce_stack import AwsDataProcessingEcommerceStack

# example tests. To run these tests, uncomment this file along with the example
# resource in aws_data_processing_ecommerce/aws_data_processing_ecommerce_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = AwsDataProcessingEcommerceStack(app, "aws-data-processing-ecommerce")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
