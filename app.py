import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_autoscaling as autoscaling,
    aws_elasticloadbalancingv2 as elbv2,
)
from constructs import Construct

class WebServerStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create VPC
        vpc = ec2.Vpc(self, "WebServerVPC", max_azs=2)

        # Create Security Group
        security_group = ec2.SecurityGroup(
            self, "WebServerSG",
            vpc=vpc,
            allow_all_outbound=True
        )
        security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(80),
            "Allow HTTP traffic"
        )
        security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(22),
            "Allow SSH access"
        )

        # User data to install and start Apache
        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            "yum update -y",
            "yum install -y httpd",
            "systemctl start httpd",
            "systemctl enable httpd"
        )

        # Create Auto Scaling Group
        asg = autoscaling.AutoScalingGroup(
            self, "WebServerASG",
            vpc=vpc,
            instance_type=ec2.InstanceType("t2.micro"),
            machine_image=ec2.AmazonLinuxImage(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2),
            user_data=user_data,
            security_group=security_group,
            min_capacity=1,
            max_capacity=3,
            desired_capacity=2,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            associate_public_ip_address=True
        )

        # Create Application Load Balancer
        alb = elbv2.ApplicationLoadBalancer(
            self, "WebServerALB",
            vpc=vpc,
            internet_facing=True
        )

        # Add Listener to ALB
        listener = alb.add_listener(
            "WebServerListener",
            port=80,
            open=True
        )

        # Add ASG as target to listener
        listener.add_targets(
            "WebServerTarget",
            port=80,
            targets=[asg]
        )

        # Output the ALB DNS name
        cdk.CfnOutput(
            self, "LoadBalancerDNS",
            value=alb.load_balancer_dns_name,
            description="Load Balancer DNS Name"
        )

app = cdk.App()
WebServerStack(app, "WebServerStack")
app.synth()