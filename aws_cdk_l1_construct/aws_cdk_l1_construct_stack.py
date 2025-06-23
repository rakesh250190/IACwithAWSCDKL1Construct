from aws_cdk import (
    # Duration,
    Stack,
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elb,
    aws_iam as iam,
    aws_ssm as ssm,
    CfnOutput,
    CfnCreationPolicy, 
    CfnResourceSignal
    # aws_sqs as sqs,
)
import base64
from constructs import Construct

class AwsCdkL1ConstructStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        #####VPC CONSTRUCT#############
        vpc=ec2.CfnVPC(self,"DEMOVPC",
                       cidr_block="172.40.0.0/16",
                       enable_dns_hostnames=True,
                       enable_dns_support=True,
                       tags=[{'key':"Name",
                              'value': "DemoVPC"}])
        
        #######INTERNET GATEWAY CONSTRUCT##########
        
        internet_gateway=ec2.CfnInternetGateway(self, "INTERNETGATEWAY",
                                                tags=[{'key':"Name",
                                                       'value':"DemoIG"}])
        
        ######Attach INTERNET GATEWAY to VPC#########

        ig_attachment = ec2.CfnVPCGatewayAttachment(self,"VPCGATEWAYATTACHMENT",
                                                    vpc_id=vpc.ref,
                                                    internet_gateway_id=internet_gateway.ref)


       
        ##########PRIVATE and PUBLIC SUBNET in 2 AZ###############

        subnets= [
        {"Public":True,"cidr":"172.40.0.0/24"},
        {"Public":False,"cidr":"172.40.1.0/24"},
        {"Public":True,"cidr":"172.40.2.0/24"},
        {"Public": False, "cidr":"172.40.3.0/24"}
        ]  ###List of dictionaries used for creating subnets
        
        public_subnets=[] #Holds list of provisioned public subnet resources
        private_subnets=[] #Holds list of provisioned private subnet resources
        public_route_table={}  #Holds list of provisioned private route tables

        for i, list_item in enumerate(subnets):
            #print(i ,list_item)
            az=0 #this variable used to iterate over availability zones

            if i >1: 
                az=1
            
            #Create public and private subnets in 2 AZ's
            subnet_resource = ec2.CfnSubnet(self,f'demosubnet{i}',
                                         vpc_id=vpc.ref,
                                         availability_zone=self.availability_zones[az],
                                         map_public_ip_on_launch=list_item["Public"],
                                         cidr_block=list_item["cidr"],
                                         tags=[
                                             {'key':"Name",
                                              'value':f'subnet{i+1}'}
                                         ])
            
          
            
            

            ####Provision Route table for each subnet 
            ##By default, route table will have local route entry for VPC CIDR block as destination
            route_table=ec2.CfnRouteTable(self,f'route_table{i+1}',
                                        vpc_id=vpc.ref,
                                        tags=[
                                            {
                                                'key': "Name",
                                                'value' : f'route-table{i+1}'
                                            }
                                        ]
                                    )

            
            if list_item["Public"]:
                ##For public subnet, add route to internet gateway for
                route_rule=ec2.CfnRoute(self,f'route-rule_{i}',
                                           route_table_id=route_table.ref,
                                           destination_cidr_block="0.0.0.0/0",
                                           gateway_id=internet_gateway.ref
                                           )
                #######PROVISION NAT GATEWAY ONLY ONCE########
                if i==0:

                    #Create EIP for nat gateway
                    elastic_ip=ec2.CfnEIP(self,"elastic-ip",                                          
                                          )
                    
                    ##Provision new NAT Gateway
                    nat_gateway = ec2.CfnNatGateway(self,
                                                    "nat-gateway",
                                                    subnet_id=subnet_resource.ref,
                                                    allocation_id=elastic_ip.attr_allocation_id
                                                    )
                               
                public_subnets.append(subnet_resource)
            else:
                private_subnets.append(subnet_resource)

                ###For private route table, route internet traffic to nat gateway
                route_rule_to_nat = ec2.CfnRoute(self,f"route-to-nat{i}",
                                                 route_table_id=route_table.ref,
                                                 nat_gateway_id=nat_gateway.ref,
                                                 destination_cidr_block="0.0.0.0/0")
            route_association=ec2.CfnSubnetRouteTableAssociation(self,
                                                                 f'route_associate{i+1}',
                                                                 route_table_id=route_table.ref,
                                                                 subnet_id=subnet_resource.ref)
            
        ###Load Balancer Security Group Ingress rule for port 80#####
        load_balancer_sg_ingress=ec2.CfnSecurityGroup.IngressProperty(
            ip_protocol="tcp",
            cidr_ip="0.0.0.0/0",
            to_port=80,
            from_port=80
        )

        #####Egress security rule for LB to allow outbound traffic within VPC on port 80
        load_balancer_sg_egress=ec2.CfnSecurityGroup.EgressProperty(
            ip_protocol="tcp",
            cidr_ip=vpc.cidr_block,
            to_port=80,
            from_port=80
        )

        ###Create new load balancer Security Group
        load_balancer_sg = ec2.CfnSecurityGroup(self,"lb-sg",security_group_ingress=[load_balancer_sg_ingress],
                                                security_group_egress=[load_balancer_sg_egress],
                                                 group_name="public-sg",
                                                 group_description="load balancer security group",
                                                 vpc_id=vpc.ref)
        
        ####Ingress rule for EC2 security group to receive traffic from LB security group on port 80
        ec2_security_group_ingress=ec2.CfnSecurityGroup.IngressProperty(
                                                               ip_protocol="tcp",
                                                               source_security_group_id=load_balancer_sg.ref,
                                                               from_port=80,
                                                               to_port=80)
        
        ###Egress security group rule for EC2 for internet access. This request will go via nat gateway
        ec2_security_group_egress=ec2.CfnSecurityGroup.EgressProperty(
                                                             ip_protocol="-1",
                                                             cidr_ip="0.0.0.0/0",
                                                             to_port=-1,
                                                             from_port=-1)
        


        ###Security group for EC2 instance for private subnet
        ec2_security_group=ec2.CfnSecurityGroup(self,"httpd-security-group",
                                                group_description="EC2 Security froup for HTTPD",
                                                vpc_id=vpc.ref,
                                                group_name="httpd-security-group",
                                                security_group_ingress=[ec2_security_group_ingress],
                                                security_group_egress=[ec2_security_group_egress]
                                                )
        ec2_security_group.node.add_dependency(load_balancer_sg)

        
        #############EC2 CONFIG###################

        ###Create New EC2 Role with AWS managed SSM policy
        ec2_instance_role=iam.CfnRole(self,"ec2-instance-role",
                                         managed_policy_arns=["arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"],
                                         assume_role_policy_document={
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {
                                "Service": [
                                    "ec2.amazonaws.com"
                                ]
                            },
                            "Action": [
                                "sts:AssumeRole"
                            ]
                        }
                    ]
                },
                role_name="SSMRoleforEC2Instance"
                )
        
        ec2_instance_profile=iam.CfnInstanceProfile(self,"ec2-instance-profile",
                                                    roles=[ec2_instance_role.role_name],
                                                    instance_profile_name="ec2-instance-profile")
        
        
        ##Read latest amazon linux
        ami_id=ssm.StringParameter.value_for_string_parameter(self,
                                                              parameter_name="/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-6.1-x86_64"
                                                              )
        ec2_instances=[]
        for i,subnet in enumerate(private_subnets):
            user_data_script=f"""#!/bin/bash
            yum update -y
            yum install -y aws-cfn-bootstrap
            yum install httpd -y
            echo 'Hello from {self.availability_zones[i]}' > /var/www/html/index.html
            systemctl start httpd
            sleep 10
            curl http://localhost
            /opt/aws/bin/cfn-signal --exit-code $? \
            --stack {self.stack_name} \
            --resource HTTPDinstance{i} \
            --region {self.region}

"""        
            encoded_user_data=base64.b64encode(user_data_script.encode()).decode()

            ###Provision EC2 resource with user data
            ec2_resource=ec2.CfnInstance(self,f"HTTPDinstance{i}",
                                         availability_zone=self.availability_zones[i],
                                         security_group_ids=[ec2_security_group.ref],
                                         subnet_id=subnet.attr_subnet_id,
                                         
                                         iam_instance_profile=ec2_instance_profile.instance_profile_name,
                                         instance_type="t2.micro",
                                         image_id=ami_id,
                                         
                                         user_data=encoded_user_data,
                                         tags=[
                                             {
                                                 'key': "Name",
                                                 'value': f'HTTPD-instance-{i}'
                                             }
                                         ]

                                        )
            
            ###EC2 Reource creation policy waiting  for CFN signal
            ec2_resource.cfn_options.creation_policy=CfnCreationPolicy(
                resource_signal=CfnResourceSignal(
                    count=1,
                    timeout="PT3M"
                )
            )
            ec2_instances.append(ec2_resource)
        


        #############LOAD BALANCER COFIG#########################
         
        ##New Load Balancer    
        load_balancer = elb.CfnLoadBalancer(self, "App-load-balancer",
                                            subnets=[i.ref for i in public_subnets],
                                                     name="load-balancer",
                                                     security_groups=[load_balancer_sg.attr_group_id])
        load_balancer.node.add_dependency(load_balancer_sg)
        
        ####Target Group to target EC2 instances on port 80
        lb_target_group = elb.CfnTargetGroup(self,"lb-target-group",
                                             protocol="HTTP",
                                             health_check_enabled=True,
                                             health_check_interval_seconds=10,
                                             health_check_path="/",
                                             health_check_port="80",
                                             health_check_protocol="HTTP",
                                             healthy_threshold_count=2,
                                             target_type="instance",
                                             vpc_id=vpc.ref,
                                             targets=[elb.CfnTargetGroup.TargetDescriptionProperty(
                                                 id=instance.ref,
                                                 port=80
                                             ) for instance in ec2_instances],
                                             port=80
                                            )
        
        lb_target_group.node.add_dependency(ec2_resource)
        
        ##Load Balancer Listner for port 80
        lb_listner = elb.CfnListener(self,"lb-listner",
                                     default_actions=[elb.CfnListener.ActionProperty(
                                         type="forward",
                                         target_group_arn=lb_target_group.attr_target_group_arn
                                        
                                     )],
                                     load_balancer_arn=load_balancer.attr_load_balancer_arn,
                                     port=80,
                                     protocol="HTTP")

      
        ############LOAD BALANCER CONFIG END HERE############

        ###Print Load balancer DNS
        CfnOutput(self,"elb-url",
                  value=load_balancer.attr_dns_name)