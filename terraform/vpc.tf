# Create VPC if needed
resource "aws_vpc" "main" {
  count = var.create_vpc ? 1 : 0

  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-vpc"
  })
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  count = var.create_vpc ? 1 : 0

  vpc_id = aws_vpc.main[0].id

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-igw"
  })
}

# Public Subnets
resource "aws_subnet" "public" {
  count = var.create_vpc ? 2 : 0

  vpc_id                  = aws_vpc.main[0].id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-public-subnet-${count.index + 1}"
    Type = "Public"
  })
}

# Private Subnets for RDS
resource "aws_subnet" "private" {
  count = var.create_vpc ? 2 : 0

  vpc_id            = aws_vpc.main[0].id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-private-subnet-${count.index + 1}"
    Type = "Private"
  })
}

# Route Table for Public Subnets
resource "aws_route_table" "public" {
  count = var.create_vpc ? 1 : 0

  vpc_id = aws_vpc.main[0].id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main[0].id
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-public-rt"
  })
}

# Associate Public Subnets with Route Table
resource "aws_route_table_association" "public" {
  count = var.create_vpc ? 2 : 0

  subnet_id      = aws_subnet.public[count.index].id
  route_table_table_id = aws_route_table.public[0].id
}

# NAT Gateway for Private Subnets (if needed for Lambda internet access)
resource "aws_eip" "nat" {
  count = var.create_vpc ? 1 : 0

  domain = "vpc"
  depends_on = [aws_internet_gateway.main]

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-nat-eip"
  })
}

resource "aws_nat_gateway" "main" {
  count = var.create_vpc ? 1 : 0

  allocation_id = aws_eip.nat[0].id
  subnet_id     = aws_subnet.public[0].id

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-nat"
  })

  depends_on = [aws_internet_gateway.main]
}

# Route Table for Private Subnets
resource "aws_route_table" "private" {
  count = var.create_vpc ? 1 : 0

  vpc_id = aws_vpc.main[0].id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[0].id
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-private-rt"
  })
}

# Associate Private Subnets with Route Table
resource "aws_route_table_association" "private" {
  count = var.create_vpc ? 2 : 0

  subnet_id      = aws_subnet.private[count.index].id
  route_table_table_id = aws_route_table.private[0].id
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

# Local values for network configuration
locals {
  vpc_id = var.create_vpc ? aws_vpc.main[0].id : var.vpc_id
  private_subnet_ids = var.create_vpc ? aws_subnet.private[*].id : var.private_subnet_ids
  public_subnet_ids  = var.create_vpc ? aws_subnet.public[*].id : var.public_subnet_ids
}