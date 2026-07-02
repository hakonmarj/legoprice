output "resource_group_name" {
  description = "Name of the deployed resource group."
  value       = azurerm_resource_group.main.name
}

output "container_registry_login_server" {
  description = "Login server URL for the Azure Container Registry."
  value       = azurerm_container_registry.main.login_server
}

output "container_registry_admin_username" {
  description = "ACR admin username (use as ACR_USERNAME GitHub secret)."
  value       = azurerm_container_registry.main.admin_username
  sensitive   = true
}

output "container_registry_admin_password" {
  description = "ACR admin password (use as ACR_PASSWORD GitHub secret)."
  value       = azurerm_container_registry.main.admin_password
  sensitive   = true
}

output "frontend_url" {
  description = "Public URL of the frontend Container App."
  value       = "https://${azurerm_container_app.frontend.ingress[0].fqdn}"
}

output "backend_url" {
  description = "Public URL of the backend Container App."
  value       = "https://${azurerm_container_app.backend.ingress[0].fqdn}"
}

output "postgres_fqdn" {
  description = "Fully qualified domain name of the PostgreSQL server."
  value       = azurerm_postgresql_flexible_server.main.fqdn
}
