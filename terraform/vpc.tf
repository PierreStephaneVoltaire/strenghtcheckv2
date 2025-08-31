# Create VPC
resource "aws_vpc" "main" {

  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-vpc-${local.resource_suffix}"
  })
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-igw-${local.resource_suffix}"
  })
}

# Public Subnets
resource "aws_subnet" "public" {
  count = 2

  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-public-subnet-${count.index + 1}-${local.resource_suffix}"
    Type = "Public"
  })
}

# Private Subnets for RDS
resource "aws_subnet" "private" {
  count = 2

  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-private-subnet-${count.index + 1}-${local.resource_suffix}"
    Type = "Private"
  })
}

# Route Table for Public Subnets
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-public-rt-${local.resource_suffix}"
  })
}

# Associate Public Subnets with Route Table
resource "aws_route_table_association" "public" {
  count = 2

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Data source for latest Amazon Linux AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Conditional NAT Gateway (expensive option)
resource "aws_eip" "nat" {
  count      = var.use_fck_nat ? 0 : 1
  domain     = "vpc"
  depends_on = [aws_internet_gateway.main]

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-nat-eip-${local.resource_suffix}"
  })
}

resource "aws_nat_gateway" "main" {
  count         = var.use_fck_nat ? 0 : 1
  allocation_id = aws_eip.nat[0].id
  subnet_id     = aws_subnet.public[0].id

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-nat-${local.resource_suffix}"
  })

  depends_on = [aws_internet_gateway.main]
}

# fck-nat EC2 instance (cost-effective alternative)
resource "aws_security_group" "fck_nat" {
  count       = var.use_fck_nat ? 1 : 0
  name        = "${var.project_name}-fck-nat-sg-${local.resource_suffix}"
  description = "Security group for fck-nat instance"
  vpc_id      = aws_vpc.main.id

  # Allow all traffic from private subnets
  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["10.0.10.0/24", "10.0.11.0/24"]
    description = "Allow all TCP from private subnets"
  }

  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "udp"
    cidr_blocks = ["10.0.10.0/24", "10.0.11.0/24"]
    description = "Allow all UDP from private subnets"
  }

  # Allow ICMP from private subnets
  ingress {
    from_port   = -1
    to_port     = -1
    protocol    = "icmp"
    cidr_blocks = ["10.0.10.0/24", "10.0.11.0/24"]
    description = "Allow ICMP from private subnets"
  }

  # Allow SSH from anywhere (for management)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow SSH"
  }

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-fck-nat-sg-${local.resource_suffix}"
  })
}

# fck-nat EC2 Instance
resource "aws_instance" "fck_nat" {
  count                  = var.use_fck_nat ? 1 : 0
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.fck_nat_instance_type
  subnet_id              = aws_subnet.public[0].id
  vpc_security_group_ids = [aws_security_group.fck_nat[0].id]
  source_dest_check      = false

  user_data_base64 = base64encode(<<-EOF
    #!/bin/bash
    yum update -y
    
    # Enable IP forwarding
    echo 'net.ipv4.ip_forward = 1' >> /etc/sysctl.conf
    sysctl -p
    
    # Configure iptables for NAT
    yum install -y iptables-services
    systemctl enable iptables
    systemctl start iptables
    
    # Flush existing rules
    iptables -F
    iptables -t nat -F
    iptables -t mangle -F
    
    # Set up NAT rule
    iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
    
    # Allow forwarding
    iptables -A FORWARD -i eth0 -o eth0 -m state --state RELATED,ESTABLISHED -j ACCEPT
    iptables -A FORWARD -i eth0 -o eth0 -j ACCEPT
    
    # Save iptables rules
    service iptables save
    
    # Install CloudWatch agent for monitoring
    yum install -y amazon-cloudwatch-agent
    
    # Configure auto-healing (restart if unhealthy)
    cat > /etc/systemd/system/fck-nat-health.service << 'HEALTHEOF'
    [Unit]
    Description=fck-nat health check
    After=network.target
    
    [Service]
    Type=oneshot
    ExecStart=/bin/bash -c 'ping -c 3 8.8.8.8 || (echo "Health check failed, restarting networking"; systemctl restart network)'
    
    [Install]
    WantedBy=multi-user.target
    HEALTHEOF
    
    cat > /etc/systemd/system/fck-nat-health.timer << 'TIMEREOF'
    [Unit]
    Description=Run fck-nat health check every 5 minutes
    
    [Timer]
    OnCalendar=*:0/5
    Persistent=true
    
    [Install]
    WantedBy=timers.target
    TIMEREOF
    
    systemctl enable fck-nat-health.timer
    systemctl start fck-nat-health.timer
    
  EOF
  )

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-fck-nat-${local.resource_suffix}"
    Type = "fck-nat"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# Elastic IP for fck-nat
resource "aws_eip" "fck_nat" {
  count      = var.use_fck_nat ? 1 : 0
  instance   = aws_instance.fck_nat[0].id
  domain     = "vpc"
  depends_on = [aws_internet_gateway.main]

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-fck-nat-eip-${local.resource_suffix}"
  })
}

# Route Table for Private Subnets
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  # Conditional routing based on NAT type
  dynamic "route" {
    for_each = var.use_fck_nat ? [] : [1]
    content {
      cidr_block     = "0.0.0.0/0"
      nat_gateway_id = aws_nat_gateway.main[0].id
    }
  }

  dynamic "route" {
    for_each = var.use_fck_nat ? [1] : []
    content {
      cidr_block           = "0.0.0.0/0"
      network_interface_id = aws_instance.fck_nat[0].primary_network_interface_id
    }
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-private-rt-${local.resource_suffix}"
  })

  depends_on = [
    aws_nat_gateway.main,
    aws_instance.fck_nat
  ]
}

# Associate Private Subnets with Route Table
resource "aws_route_table_association" "private" {
  count = 2

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

# Local values for network configuration
locals {
  vpc_id = aws_vpc.main.id
  private_subnet_ids = aws_subnet.private[*].id
  public_subnet_ids  = aws_subnet.public[*].id
}