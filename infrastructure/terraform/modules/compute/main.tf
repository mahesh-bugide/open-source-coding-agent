data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023*-x86_64"]
  }
}

resource "aws_ecr_repository" "api" {
  name = "${var.name_prefix}-api"
  tags = var.tags
}

resource "aws_ecr_repository" "agent" {
  name = "${var.name_prefix}-agent"
  tags = var.tags
}

resource "aws_ecr_repository" "vllm" {
  name = "${var.name_prefix}-vllm"
  tags = var.tags
}

resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/${var.name_prefix}/api"
  retention_in_days = 14
  tags              = var.tags
}

resource "aws_cloudwatch_log_group" "agent" {
  name              = "/ecs/${var.name_prefix}/agent"
  retention_in_days = 14
  tags              = var.tags
}

resource "aws_ecs_cluster" "this" {
  name = "${var.name_prefix}-cluster"
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  tags = var.tags
}

resource "aws_iam_role" "ecs_task_execution" {
  name = "${var.name_prefix}-ecs-task-execution"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = { Service = "ecs-tasks.amazonaws.com" },
      Action = "sts:AssumeRole",
    }],
  })
  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_lb" "api" {
  name               = substr(replace("${var.name_prefix}-alb", "_", "-"), 0, 32)
  internal           = false
  load_balancer_type = "application"
  subnets            = var.public_subnet_ids
  security_groups    = [var.alb_sg_id]
  tags               = var.tags
}

resource "aws_lb_target_group" "api" {
  name        = substr(replace("${var.name_prefix}-api", "_", "-"), 0, 32)
  port        = 8080
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"
  health_check {
    path                = "/health"
    matcher             = "200-299"
    interval            = 20
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
  tags = var.tags
}

resource "aws_lb_listener" "api" {
  load_balancer_arn = aws_lb.api.arn
  port              = 80
  protocol          = "HTTP"
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}

resource "aws_ecs_task_definition" "api" {
  family                   = "${var.name_prefix}-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "1024"
  memory                   = "2048"
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn

  container_definitions = jsonencode([
    {
      name      = "api",
      image     = var.api_image,
      essential = true,
      portMappings = [{
        containerPort = 8080,
        hostPort      = 8080,
        protocol      = "tcp",
      }],
      environment = [
        { name = "APP_ENV", value = "production" },
        { name = "POSTGRES_DSN", value = var.postgres_dsn },
        { name = "REDIS_URL", value = var.redis_url },
        { name = "MODEL_BASE_URL", value = var.model_base_url },
        { name = "MODEL_NAME", value = var.model_name },
        { name = "MODEL_MODE", value = "remote" },
        { name = "DEV_API_KEY", value = var.dev_api_key },
        { name = "REQUIRE_API_KEY", value = "true" },
        { name = "SANDBOX_MODE", value = "docker" },
      ],
      logConfiguration = {
        logDriver = "awslogs",
        options = {
          awslogs-group         = aws_cloudwatch_log_group.api.name,
          awslogs-region        = data.aws_region.current.name,
          awslogs-stream-prefix = "ecs",
        },
      },
    },
  ])

  tags = var.tags
}

data "aws_region" "current" {}

resource "aws_ecs_service" "api" {
  name            = "${var.name_prefix}-api"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.api_sg_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8080
  }

  depends_on = [aws_lb_listener.api]
  tags       = var.tags
}

resource "aws_ecs_task_definition" "agent" {
  family                   = "${var.name_prefix}-agent"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn

  container_definitions = jsonencode([
    {
      name      = "agent",
      image     = var.agent_image,
      essential = true,
      portMappings = [{
        containerPort = 8090,
        hostPort      = 8090,
        protocol      = "tcp",
      }],
      logConfiguration = {
        logDriver = "awslogs",
        options = {
          awslogs-group         = aws_cloudwatch_log_group.agent.name,
          awslogs-region        = data.aws_region.current.name,
          awslogs-stream-prefix = "ecs",
        },
      },
    },
  ])

  tags = var.tags
}

resource "aws_ecs_service" "agent" {
  name            = "${var.name_prefix}-agent"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.agent.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.agent_sg_id]
    assign_public_ip = false
  }

  tags = var.tags
}

resource "aws_iam_role" "gpu_instance_role" {
  name = "${var.name_prefix}-gpu-instance-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = { Service = "ec2.amazonaws.com" },
      Action = "sts:AssumeRole",
    }],
  })
  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "gpu_ssm" {
  role       = aws_iam_role.gpu_instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "gpu" {
  name = "${var.name_prefix}-gpu-profile"
  role = aws_iam_role.gpu_instance_role.name
}

resource "aws_launch_template" "gpu" {
  name_prefix   = "${var.name_prefix}-gpu-"
  image_id      = data.aws_ami.amazon_linux.id
  instance_type = var.gpu_instance_type

  vpc_security_group_ids = [var.vllm_sg_id]
  iam_instance_profile {
    name = aws_iam_instance_profile.gpu.name
  }

  user_data = base64encode(<<-EOT
    #!/bin/bash
    set -euxo pipefail
    dnf update -y
    dnf install -y docker
    systemctl enable docker
    systemctl start docker
    docker run -d --restart unless-stopped --gpus all --name vllm \
      -p 8001:8001 ${var.vllm_image}
  EOT
  )

  tag_specifications {
    resource_type = "instance"
    tags          = merge(var.tags, { Name = "${var.name_prefix}-gpu" })
  }
}

resource "aws_autoscaling_group" "gpu" {
  name                = "${var.name_prefix}-gpu-asg"
  desired_capacity    = 1
  min_size            = 1
  max_size            = 1
  vpc_zone_identifier = var.private_subnet_ids

  launch_template {
    id      = aws_launch_template.gpu.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "${var.name_prefix}-gpu"
    propagate_at_launch = true
  }
}
