terraform {
  required_providers {
    proxmox = {
      source = "bpg/proxmox"
      version = "0.86.0"
    }
  }
}

provider "proxmox" {
  insecure = true
  endpoint = var.proxmox_endpoint
  api_token = var.proxmox_api_token
}

resource "proxmox_virtual_environment_download_file" "debian_vm_cloud_image" {
  content_type = "import"
  datastore_id = "backup-NAS"
  node_name    = "ca8"
  url          = "https://cloud.debian.org/images/cloud/trixie/20250814-2204/debian-13-generic-amd64-20250814-2204.qcow2"
  # need to rename the file to *.qcow2 to indicate the actual file format for import
  file_name = "trixie-server-cloudimg-amd64-20250814-22040-2.qcow2"
}

resource "proxmox_virtual_environment_vm" "mlonghi-hyperflowbirex" {
  name      = "mlonghi-hyperflowbirex"
  pool_id="mlonghi"
  # create vms on all nodes
  node_name = "CA6"
  # should be true if qemu agent is not installed / enabled on the VM
  stop_on_destroy = true

  tags =["mlonghi"]
  cpu {
    cores = 16
    type  = "host"
  }

  memory {
    dedicated = 16384
    floating = 16384
  }

  initialization {
    user_account {
      keys     = var.default_public_keys
      password = var.default_user_password
      username = var.default_user_username
    }

    ip_config {
      ipv4 {
        address = "dhcp"
      }
    }
  }

  network_device {
    bridge = "vmbr0"
  }

  disk {
    datastore_id = "single_replica_ceph"
    import_from  = proxmox_virtual_environment_download_file.debian_vm_cloud_image.id
    interface    = "virtio0"
    iothread     = true
    discard      = "on"
    size         = 200
  }
}
