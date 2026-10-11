variable "aws_region" {
  type        = string
  description = "AWS region for the non-production environment."
  default     = "us-east-1"
}

variable "environment" {
  type        = string
  description = "Deployment environment name."
  default     = "staging"

  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "environment must be staging or production."
  }
}

variable "image_uri" {
  type        = string
  description = "Immutable RAGDiff API image URI, including a tag or digest."
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR range for the environment VPC."
  default     = "10.42.0.0/16"
}

variable "db_instance_class" {
  type        = string
  description = "RDS instance class."
  default     = "db.t4g.micro"
}

variable "enable_deletion_protection" {
  type        = bool
  description = "Protect production database from accidental deletion."
  default     = false
}
