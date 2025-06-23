# 🚀 Reference Architecture for this tutorial
# We will be provisioning below architecture using AWS CDK L1 construct with Python

+---------------------------------------------------------+
|                   AWS VPC: 172.40.0.0/16                |
|                                                         |
|  +------------------+         +------------------+     |
|  |     AZ 1         |         |     AZ 2         |     |
|  |                  |         |                  |     |
|  |  Public Subnet   |         |  Public Subnet   |     |
|  |  172.40.0.0/24   |         |  172.40.2.0/24   |     |
|  |  +------------+  |         |  +------------+  |     |
|  |  | Internet   |  |         |  | Internet   |  |     |
|  |  | Gateway    |  |         |  | Gateway    |  |     |
|  |  +-----+------+  |         |  +-----+------+  |     |
|  |        |         |         |        |         |     |
|  |  +-----+------+  |         |  +-----+------+  |     |
|  |  | Application |  |         |  | Application |  |     |
|  |  | Load        |  |         |  | Load        |  |     |
|  |  | Balancer    |  |         |  | Balancer    |  |     |
|  |  +-----+------+  |         |  +-----+------+  |     |
|  |        |         |         |        |         |     |
|  |  +-----+------+  |         |        |         |     |
|  |  | NAT Gateway |  |         |        |         |     |
|  |  | (AZ1 only)  |  |         |        |         |     |
|  |  +------------+  |         |        |         |     |
|  |                  |         |                  |     |
|  |  Private Subnet  |         |  Private Subnet  |     |
|  |  172.40.1.0/24   |         |  172.40.3.0/24   |     |
|  |  +------------+  |         |  +------------+  |     |
|  |  | EC2        |  |         |  | EC2        |  |     |
|  |  | Instance   |  |         |  | Instance   |  |     |
|  |  +------------+  |         |  +------------+  |     |
|  +------------------+         +------------------+     |
+---------------------------------------------------------+
VPC CIDR: 172.40.0.0/16
Availability Zones: 2 (Multi-AZ for High Availability)

Key Components
1. Public Subnets
AZ	Subnet CIDR	Components
AZ1	172.40.0.0/24	Load Balancer, NAT Gateway
AZ2	172.40.2.0/24	Load Balancer
2. Private Subnets
AZ	Subnet CIDR	Components
AZ1	172.40.1.0/24	EC2 Instance with httpd service
AZ2	172.40.3.0/24	EC2 Instance with httpd service
3. Network Services
Internet Gateway (IGW)
Attached to VPC for public traffic.

NAT Gateway
Deployed only in 172.40.0.0/24 (AZ1) for outbound private subnet traffic.

Traffic Flow
Inbound Traffic:
Internet → Load Balancer (Public Subnets) → EC2 Instances (Private Subnets).

Outbound Traffic:
Private Subnets → NAT Gateway (AZ1) → Internet.

===============================================================================

# 🚀 AWS CDK Setup Guide on Windows + Visual Studio Code

This guide helps you set up an AWS CDK development environment on **Windows** using **Visual Studio Code**. It supports both **TypeScript** and **Python** CDK projects.

---

## ✅ Prerequisites

Make sure the following are installed:

- [Node.js (≥ 18.x)](https://nodejs.org/en/download/)
- [Python (≥ 3.8)](https://www.python.org/downloads/)
- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2-windows.html)
- [Visual Studio Code](https://code.visualstudio.com/Download)
- AWS account with programmatic access (Access Key & Secret)

---

## 🛠️ Steps to Set Up CDK on Windows

### 1. Install AWS CDK CLI

```bash
npm install -g aws-cdk
```

Verify installation:

```bash
cdk --version
```

---

### 2. Configure AWS CLI

```bash
aws configure
```

Provide:
- AWS Access Key ID
- AWS Secret Access Key
- Default region name (e.g., `us-east-1`)
- Output format (default: `json`)

---

### 3. Create a CDK Project

#### 🟨 TypeScript Project

```bash
mkdir my-cdk-app
cd my-cdk-app
cdk init app --language=typescript
```

#### 🟦 Python Project

```bash
mkdir aws_cdk_l1_construct
cd aws_cdk_l1_construct
cdk init app --language=python
```

Activate the Python virtual environment:

```bash
.\.venv\Scripts ctivate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

### 4. Open Project in Visual Studio Code

```bash
code .
```

📦 Recommended VS Code Extensions:
- **AWS Toolkit**
- **Python** (for Python CDK)
- **ESLint / Prettier** (for TypeScript CDK)
- **Prettify JSON**

---

### 5. Bootstrap Your AWS Environment

```bash
cdk bootstrap
```

This creates required resources like S3 buckets and IAM roles.

---

### 6. Synthesize CloudFormation Template

```bash
cdk synth
```

---

### 7. Deploy Your CDK Stack

```bash
cdk deploy
```

---

### 8. Clean Up Resources

```bash
cdk destroy
```

---

## 🧠 Tips

- Run `cdk diff` to preview infrastructure changes.
- Add `.venv/`, `cdk.context.json`, and `node_modules/` to `.gitignore`.
- Use environment variables or `cdk.json` for dynamic configurations.

---