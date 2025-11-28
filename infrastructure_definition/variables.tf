variable "proxmox_endpoint" {
  description = "url for proxmox api"
}
variable "proxmox_api_token" {
  description = "secret for proxmox api"
}
variable "default_public_keys" {
  description = "default ssh pub key"
}
variable "default_user_password" {
  description = "vms and containers password"
}
variable "default_user_username" {
  description = "vms and containers password"
}
variable "cluster_nodes" {
  type = map(string)
  default = {
    0 = "CA5"
    1 = "CA6"
    2 = "ca7"
    3 = "ca8"
  }
}
