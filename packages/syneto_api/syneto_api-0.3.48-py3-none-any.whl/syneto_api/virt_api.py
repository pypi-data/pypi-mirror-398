import os
from ipaddress import IPv4Address

from .api_client import APIClientBase, InvalidInputException


class Virtualization(APIClientBase):
    def __init__(self, url_base=None, **kwargs):
        super().__init__(url_base or os.environ.get("VIRTUALIZATION_SERVICE", ""), **kwargs)

        # Deprecated methods, please don't use them
        self.get_vm_by_syn_id = self.get_virtual_machine

    def get_hypervisors(self):
        return self.get_request("/hypervisors")

    def get_hypervisor(self, hypervisor_id: str):
        if not hypervisor_id:
            raise InvalidInputException(f"Expected a valid hypervisor id, received: `{hypervisor_id}`")
        return self.get_request("/hypervisors/{uuid}", uuid=hypervisor_id)

    def get_vms(self):
        return self.get_request("/vms")

    def get_virtual_machine(self, vm_syn_id: str):
        if not vm_syn_id:
            raise InvalidInputException(f"Expected a valid virtual machine id, received: `{vm_syn_id}`")
        return self.get_request("/vms/{vm_syn_id}", vm_syn_id=vm_syn_id)

    def edit_vm(self, vm_syn_id: str, body: dict):
        if not vm_syn_id:
            raise InvalidInputException(f"Expected a valid virtual machine id, received: `{vm_syn_id}`")
        return self.patch_request("/vms/{vm_syn_id}", vm_syn_id=vm_syn_id, body=body)

    def get_vmware_hosts(self):
        return self.get_request("/vmware/hosts")

    def get_vmware_datastores(self):
        return self.get_request("/vmware/datastores")

    def get_vm_snapshot(self, vm_syn_id: str, snapshot_name: str):
        if not vm_syn_id:
            raise InvalidInputException(f"Expected a valid virtual machine id, received: `{vm_syn_id}`")
        snapshots = self.get_request("/vmware/vms/{vm_syn_id}/snapshots", vm_syn_id=vm_syn_id)
        return next((snap for snap in snapshots if snap["name"] == snapshot_name), None)

    def get_vm_snapshots(self, vm_syn_id: str):
        if not vm_syn_id:
            raise InvalidInputException(f"Expected a valid virtual machine id, received: `{vm_syn_id}`")
        return self.get_request("/vmware/vms/{vm_syn_id}/snapshots", vm_syn_id=vm_syn_id)

    def create_vm_snapshot(
        self,
        vm_syn_id: str,
        snapshot_name: str,
        quiesce: bool = True,
        dumpmem: bool = False,
    ):
        if not vm_syn_id:
            raise InvalidInputException(f"Expected a valid virtual machine id, received: `{vm_syn_id}`")
        body = {
            "vmSynId": vm_syn_id,
            "snapshotName": snapshot_name,
            "description": snapshot_name,
            "quiesce": quiesce,
            "dumpmem": dumpmem,
        }
        return self.post_request(
            "/vmware/vms/{vm_syn_id}/snapshots",
            vm_syn_id=vm_syn_id,
            query_args={"in_background": "False"},
            body=body,
        )

    def delete_vm_snapshot(self, vm_syn_id, snapshot_ref_id, consolidate=True, remove_children=True):
        if not vm_syn_id:
            raise InvalidInputException(f"Expected a valid virtual machine id, received: `{vm_syn_id}`")
        body = {
            "vmSynId": vm_syn_id,
            "snapshotRefId": snapshot_ref_id,
            "consolidate": consolidate,
            "removeChildren": remove_children,
        }
        self.delete_request(
            "/vmware/vms/{vm_syn_id}/snapshots",
            vm_syn_id=vm_syn_id,
            query_args={"in_background": "False"},
            body=body,
            success_codes=[200, 202, 204],
        )

    def create_nas_datastore(self, server: str, mountpoint: str, hosts_syn_ids=None, datastore_name=None):
        return self.post_request(
            "/vmware/datastores",
            body={
                "server": server,
                "name": datastore_name,
                "mountpoint": mountpoint,
                "hosts_syn_ids": hosts_syn_ids if hosts_syn_ids else [],
            },
        )

    def delete_nas_datastore(self, syn_id: str = None, mountpoint: str = None):
        return self.delete_request(
            "/vmware/datastores",
            query_args={
                "datastore_syn_id": syn_id if syn_id else "",
                "datastore_mountpoint": mountpoint,
            },
        )

    def get_virtual_machine_cbt_info(self, vm_syn_id: str):
        if not vm_syn_id:
            raise InvalidInputException(f"Expected a valid virtual machine id, received: `{vm_syn_id}`")
        return self.get_request("/vmware/vms/{vm_syn_id}/cbt", vm_syn_id=vm_syn_id)

    def enable_virtual_machine_cbt(self, vm_syn_id: str):
        if not vm_syn_id:
            raise InvalidInputException(f"Expected a valid virtual machine id, received: `{vm_syn_id}`")
        return self.put_request(
            "/vmware/vms/{vm_syn_id}/cbt",
            vm_syn_id=vm_syn_id,
            query_args={"action": "enable_cbt"},
            body={},
            success_codes=[200, 409, 500],
        )

    def get_vm_snapshot_by_ref(self, vm_syn_id: str, snapshot_ref: str):
        if not vm_syn_id:
            raise InvalidInputException(f"Expected a valid virtual machine id, received: `{vm_syn_id}`")
        if not snapshot_ref:
            raise InvalidInputException(f"Expected a valid VM snapshot ref, received: `{snapshot_ref}`")
        return self.get_request(
            "/vmware/vms/{vm_syn_id}/snapshots/{snapshot_ref}",
            vm_syn_id=vm_syn_id,
            snapshot_ref=snapshot_ref,
        )

    def get_image_repository(self):
        return self.get_request("/v1/imageRepository")


class V1Virtualization(Virtualization):
    def get_hypervisors(self):
        return self.get_request("/v1/hypervisors")

    def get_hypervisor(self, hypervisor_id: str):
        if not hypervisor_id:
            raise InvalidInputException(f"Expected a valid hypervisor id, received: `{hypervisor_id}`")
        return self.get_request("/v1/hypervisors/{uuid}", uuid=hypervisor_id)

    def get_virtual_machines(self):
        return self.get_request("/virtualMachines")

    def get_virtual_volumes(self):
        return self.get_request("/v1/virtualVolumes")

    def get_virtual_machine(self, id: str):
        if not id:
            raise InvalidInputException(f"Expected a valid virtual machine id, received: `{id}`")
        return self.get_request("/virtualMachines/{id}", id=id)

    def edit_virtual_machine(self, id: str, body: dict):
        if not id:
            raise InvalidInputException(f"Expected a valid virtual machine id, received: `{id}`")
        return self.patch_request("/virtualMachines/{id}", id=id, body=body)

    def get_virtual_machine_conf_file_content(self, id: str) -> str:
        if self._use_asyncio:
            raise InvalidInputException("Async client does not support this function at this time")
        if not id:
            raise InvalidInputException(f"Expected a valid virtual machine id, received: `{id}`")

        result = self.get_request("/virtualMachines/{id}:confFileContent", id=id)
        return result.decode("utf8")

    def enable_virtual_machine_cbt(self, id: str) -> str:
        if not id:
            raise InvalidInputException(f"Expected a valid virtual machine id, received: `{id}`")
        return self.patch_request("/virtualMachines/{id}", id=id, body={"cbtEnabled": True})

    def get_vm_snapshots(self, id: str):
        if not id:
            raise InvalidInputException(f"Expected a valid virtual machine id, received: `{id}`")
        return super().get_request("/virtualMachines/{id}/snapshots", id=id)

    def get_vm_snapshot(self, id: str, snapshot_name: str):
        if self._use_asyncio:
            raise InvalidInputException("Async client does not support this function at this time")
        snapshots = self.get_vm_snapshots(id)
        return next((snap for snap in snapshots if snap["name"] == snapshot_name), None)

    def register_from_snapshot(
        self,
        name: str,
        compute_host_id: str,
        volume_id: str,
        snapshot_name: str,
        keep_original_volume: bool = False,
        folder_id: str = "",
        as_template: bool = False,
        keep_mac_address: bool = False,
        power_on: bool = False,
        connect_networks: bool = True,
        clear_location_uuids: bool = False,
        policy_id: str = None,
        snapshot_consistency: str = None,
        storage_network: IPv4Address = None,
        replica_targets: list[dict] = None,
    ):
        if self._use_asyncio:
            raise InvalidInputException("Async client does not support this function at this time")

        body = {
            "name": name,
            "asTemplate": as_template,
            "computeHostId": compute_host_id,
            "folderId": folder_id,
            "keepMacAddress": keep_mac_address,
            "powerOn": power_on,
            "connectNetworks": connect_networks,
            "clearLocationUuids": clear_location_uuids,
            "volumeId": volume_id,
            "snapshotName": snapshot_name,
            "keepOriginal": keep_original_volume,
            "policy_id": policy_id,
            "snapshot_consistency": snapshot_consistency,
            "storage_network": str(storage_network) if storage_network else None,
            "replicaTargets": replica_targets,
        }

        return self.post_request("/v1/virtualMachines:registerFromSnapshot", body=body)

    def get_compute_host(self, id: str):
        if self._use_asyncio:
            raise InvalidInputException("Async client does not support this function at this time")

        if not id:
            raise InvalidInputException(f"Expected a valid compute host id, received: `{id}`")

        return self.get_request("/v1/computeHosts/{id}", id=id)

    def get_compute_host_supported_hardware_versions(self, id: str):
        if self._use_asyncio:
            raise InvalidInputException("Async client does not support this function at this time")

        if not id:
            raise InvalidInputException(f"Expected a valid compute host id, received: `{id}`")

        return self.get_request("/v1/computeHosts/{id}/supportedHardwareVersions", id=id)

    def get_datacenter(self, datacenter_id: str):
        if not datacenter_id:
            raise InvalidInputException(f"Expected a valid datacenter id, received: `{datacenter_id}`")
        return self.get_request(f"/v1/datacenter/{datacenter_id}")

    def remove_datacenter_node(self, datacenter_id: str, node_id: str):
        if not datacenter_id:
            raise InvalidInputException(f"Expected a valid datacenter id, received: `{datacenter_id}`")
        if not node_id:
            raise InvalidInputException(f"Expected a valid node id, received: `{node_id}`")
        return self.delete_request(f"/v1/datacenter/{datacenter_id}/nodes/{node_id}")

    def destroy_datacenter(self, datacenter_id: str):
        if not datacenter_id:
            raise InvalidInputException(f"Expected a valid datacenter id, received: `{datacenter_id}`")
        return self.delete_request(f"/v1/datacenter/{datacenter_id}")

    def trigger_datacenter_sync(
        self,
        datacenter_id: str,
        source_node_id: str,
        target_node_id: str = None,
        reason: str = None,
    ):
        if not datacenter_id:
            raise InvalidInputException(f"Expected a valid datacenter id, received: `{datacenter_id}`")
        if not source_node_id:
            raise InvalidInputException(f"Expected a valid source node id, received: `{source_node_id}`")
        body = {
            "sourceNodeId": source_node_id,
            "targetNodeId": target_node_id,
            "reason": reason,
        }
        return self.post_request(f"/v1/datacenter/{datacenter_id}:sync", body=body)

    def leave_datacenter(self, datacenter_id: str):
        if not datacenter_id:
            raise InvalidInputException(f"Expected a valid datacenter id, received: `{datacenter_id}`")
        return self.post_request(f"/v1/datacenter/{datacenter_id}:leave")
