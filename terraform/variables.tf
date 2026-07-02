variable "project" {
  description = "Short project identifier used in resource names."
  type        = string
  default     = "legoprice"
}

variable "environment" {
  description = "Deployment environment (e.g. prod, staging)."
  type        = string
  default     = "prod"
}

variable "location" {
  description = "Azure region to deploy into."
  type        = string
  default     = "northeurope"
}

variable "acr_sku" {
  description = "SKU for Azure Container Registry (Basic, Standard, Premium)."
  type        = string
  default     = "Basic"
}

variable "postgres_admin_user" {
  description = "PostgreSQL administrator login name."
  type        = string
  default     = "legoadmin"
}

variable "postgres_admin_password" {
  description = "PostgreSQL administrator password."
  type        = string
  sensitive   = true
}

variable "postgres_db_name" {
  description = "Name of the PostgreSQL database."
  type        = string
  default     = "legoprice"
}
