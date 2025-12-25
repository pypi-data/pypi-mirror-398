import os
from typing import Literal, Optional
from .api_client import JSON, APIClientBase, InvalidInputException


class Storage(APIClientBase):
    def __init__(self, url_base=None, **kwargs):
        super().__init__(url_base or os.environ.get("STORAGE_SERVICE", ""), **kwargs)

    def get_pools(self):
        return self.get_request("/pools")

    def get_importable_pools(self):
        return self.get_request("/pools/importable")

    def get_pool(self, pool_name: str, fields: list = None):
        if not pool_name:
            raise InvalidInputException(f"Expected a valid pool name, received: `{pool_name}`")
        fields = {"fields": ",".join(fields)} if fields else None
        return self.get_request("/pools/{pool_name}", query_args=fields, pool_name=pool_name)

    def clear_pool(self, pool_name: str):
        if not pool_name:
            raise InvalidInputException(f"Expected a valid pool name, received: `{pool_name}`")
        return self.put_request("/pools/{pool_name}/clear", pool_name=pool_name)

    def upgrade_pool(self, pool_name: str):
        if not pool_name:
            raise InvalidInputException(f"Expected a valid pool name, received: `{pool_name}`")
        return self.put_request("/pools/{pool_name}/upgrade", pool_name=pool_name)

    def export_pool(self, pool_name: str):
        if not pool_name:
            raise InvalidInputException(f"Expected a valid pool name, received: `{pool_name}`")
        return self.put_request("/pools/{pool_name}/export", pool_name=pool_name)

    def get_pool_periodic_scrub(self, pool_name: str):
        if not pool_name:
            raise InvalidInputException(f"Expected a valid pool name, received: `{pool_name}`")
        return self.get_request("/pools/{pool_name}/scrub/interval", pool_name=pool_name)

    def set_pool_periodic_scrub(self, pool_name: str, interval: str):
        if not pool_name:
            raise InvalidInputException(f"Expected a valid pool name, received: `{pool_name}`")
        return self.post_request(
            "/pools/{pool_name}/scrub/interval",
            pool_name=pool_name,
            query_args={"interval": interval},
        )

    def delete_pool_periodic_scrub(self, pool_name: str):
        if not pool_name:
            raise InvalidInputException(f"Expected a valid pool name, received: `{pool_name}`")
        return self.delete_request("/pools/{pool_name}/scrub/interval", pool_name=pool_name)

    def start_pool_scrub(self, pool_name: str):
        if not pool_name:
            raise InvalidInputException(f"Expected a valid pool name, received: `{pool_name}`")
        return self.put_request("/pools/{pool_name}/scrub/start", pool_name=pool_name)

    def stop_pool_scrub(self, pool_name: str):
        if not pool_name:
            raise InvalidInputException(f"Expected a valid pool name, received: `{pool_name}`")
        return self.put_request("/pools/{pool_name}/scrub/stop", pool_name=pool_name)

    def get_volumes(self, volume_type: str = None, only_clones: bool = False, label_key: str = ""):
        args = {"only_clones": only_clones, "label_key": label_key}
        if volume_type:
            args["volume_type"] = volume_type
        return self.get_request("/volumes", query_args=args)

    def create_volume(self, pool_name: str, ips: list, volume_type: str = "NFS", quota: str = "none"):
        hosts = [{"ipNetwork": ip, "accessType": "rw"} for ip in ips]
        body = {
            "type": volume_type,
            "pool": pool_name,
            "nfsShareConfig": {"rootAccess": "true", "hosts": hosts},
            "quota": quota,
        }
        return self.post_request("/volumes", body=body)

    def get_volume(self, volume_id: str):
        if not volume_id:
            raise InvalidInputException(f"Expected a valid volume id, received: `{volume_id}`")
        return self.get_request("/volumes/{volume_id}", volume_id=volume_id)

    def delete_volume(self, volume_id: str):
        return self.delete_request("/volumes", query_args={"volume_id": volume_id})

    def promote_volume(self, volume_id: str):
        if not volume_id:
            raise InvalidInputException(f"Expected a valid volume id, received: `{volume_id}`")
        return self.put_request("/volumes/{volume_id}/promote", volume_id=volume_id)

    def get_volume_meta(self, volume_id: str, key: str, snapshot_name: str = None) -> JSON:
        if not volume_id:
            raise InvalidInputException(f"Expected a valid volume id, received: `{volume_id}`")
        query = {"key": key}
        if snapshot_name:
            query["snapshot_name"] = snapshot_name
        return self.get_request("/volumes/{volume_id}/meta", volume_id=volume_id, query_args=query)

    def set_volume_meta(self, volume_id: str, key: str, value: JSON, snapshot_name: str = None):
        if not volume_id:
            raise InvalidInputException(f"Expected a valid volume id, received: `{volume_id}`")
        body = {"key": key, "value": value}
        query = {}
        if snapshot_name:
            query["snapshot_name"] = snapshot_name
        return self.put_request(
            "/volumes/{volume_id}/meta",
            volume_id=volume_id,
            query_args=query,
            body=body,
        )

    def get_volume_snapshots(
        self,
        volume_id: str,
        offset: int = 0,
        limit: int = 0,
        sort_by: str = None,
        sort_direction: Literal["asc", "desc"] = "asc",
    ):
        if not volume_id:
            raise InvalidInputException(f"Expected a valid volume id, received: `{volume_id}`")
        query = {}
        if offset > 0:
            query["offset"] = offset
        if limit > 0:
            query["limit"] = limit
        if sort_by is not None:
            query["sortBy"] = sort_by
            query["sortDirection"] = sort_direction
        return self.get_request("/volumes/{volume_id}/snapshots", volume_id=volume_id, query_args=query)

    def create_volume_snapshot(self, volume_id: str, snapshot_name: str):
        if not volume_id:
            raise InvalidInputException(f"Expected a valid volume id, received: `{volume_id}`")
        return self.post_request(
            "/volumes/{volume_id}/snapshots",
            volume_id=volume_id,
            query_args={"snapshot_name": snapshot_name},
        )

    def get_volume_snapshot(self, volume_id: str, snapshot_name: str):
        if not volume_id:
            raise InvalidInputException(f"Expected a valid volume id, received: `{volume_id}`")
        if not snapshot_name:
            raise InvalidInputException(f"Expected a valid snapshot name, received: `{snapshot_name}`")
        return self.get_request(
            "/volumes/{volume_id}/snapshots/{snapshot_name}",
            volume_id=volume_id,
            snapshot_name=snapshot_name,
        )

    def delete_volume_snapshot(self, volume_id: str, snapshot_name: str):
        if not volume_id:
            raise InvalidInputException(f"Expected a valid volume id, received: `{volume_id}`")
        if not snapshot_name:
            raise InvalidInputException(f"Expected a valid snapshot name, received: `{snapshot_name}`")
        return self.delete_request(
            "/volumes/{volume_id}/snapshots",
            volume_id=volume_id,
            query_args={"snapshot_name": snapshot_name},
        )

    def rollback_volume_snapshot(self, volume_id: str, snapshot_name: str):
        if not volume_id:
            raise InvalidInputException(f"Expected a valid volume id, received: `{volume_id}`")
        if not snapshot_name:
            raise InvalidInputException(f"Expected a valid snapshot name, received: `{snapshot_name}`")
        return self.put_request(
            "/volumes/{volume_id}/snapshots/{snapshot_name}/rollback",
            volume_id=volume_id,
            snapshot_name=snapshot_name,
        )

    def get_volume_snapshot_clones(self, volume_id: str, snapshot_name: str):
        if not volume_id:
            raise InvalidInputException(f"Expected a valid volume id, received: `{volume_id}`")
        if not snapshot_name:
            raise InvalidInputException(f"Expected a valid snapshot name, received: `{snapshot_name}`")
        return self.get_request(
            "/volumes/{volume_id}/snapshots/{snapshot_name}/clones",
            volume_id=volume_id,
            snapshot_name=snapshot_name,
        )

    def create_volume_snapshot_clone(self, volume_id: str, snapshot_name: str):
        if not volume_id:
            raise InvalidInputException(f"Expected a valid volume id, received: `{volume_id}`")
        if not snapshot_name:
            raise InvalidInputException(f"Expected a valid snapshot name, received: `{snapshot_name}`")
        return self.post_request(
            "/volumes/{volume_id}/snapshots/{snapshot_name}/clones",
            volume_id=volume_id,
            snapshot_name=snapshot_name,
        )

    def get_volume_files(
        self,
        volume_id: str,
        path: str = None,
        recursive: bool = False,
        match_pattern: str = None,
    ):
        if not volume_id:
            raise InvalidInputException(f"Expected a valid volume id, received: `{volume_id}`")
        query = {"recursive": recursive}
        if path:
            query["path"] = path
        if match_pattern:
            query["match_pattern"] = match_pattern

        return self.get_request("/volumes/{volume_id}/files", volume_id=volume_id, query_args=query)

    def delete_volume_files(self, volume_id: str, file_path: str = None, pattern: str = None):
        if not volume_id:
            raise InvalidInputException(f"Expected a valid volume id, received: `{volume_id}`")
        return self.delete_request(
            "/volumes/{volume_id}/files",
            volume_id=volume_id,
            body={"volume_id": volume_id, "file_path": file_path, "pattern": pattern},
        )

    def get_volume_file_content(self, volume_id: str, file_path: str):
        if not volume_id:
            raise InvalidInputException(f"Expected a valid volume id, received: `{volume_id}`")
        return self.get_request(
            "/volumes/{volume_id}/files/content",
            volume_id=volume_id,
            query_args={"file_path": file_path},
        )

    def set_volume_file_content(self, volume_id: str, file_path: str, content: str):
        if not volume_id:
            raise InvalidInputException(f"Expected a valid volume id, received: `{volume_id}`")
        return self.post_request(
            "/volumes/{volume_id}/files/content",
            volume_id=volume_id,
            query_args={"file_path": file_path},
            body={"content": content},
        )

    def create_directory_in_volume(self, volume_id: str, dir_path: str):
        if not volume_id:
            raise InvalidInputException(f"Expected a valid volume id, received: `{volume_id}`")
        return self.post_request(
            "/volumes/{volume_id}/folder",
            volume_id=volume_id,
            query_args={"dir_path": dir_path},
        )

    def delete_directory_in_volume(self, volume_id: str, dir_path: str):
        if not volume_id:
            raise InvalidInputException(f"Expected a valid volume id, received: `{volume_id}`")
        return self.delete_request(
            "/volumes/{volume_id}/folder",
            volume_id=volume_id,
            query_args={"dir_path": dir_path},
        )

    def get_file_recovery_volume(self):
        return self.get_request("/file-recovery")

    def create_file_recovery_volume(self, pool_name: str):
        return self.post_request("/file-recovery", body={"pool": pool_name})

    def get_system_information(self):
        return self.get_request("/system")

    def get_disks(self):
        return self.get_request("/disks")

    def refresh_disks(self):
        return self.put_request("/disks")

    def get_files_snapshot(
        self,
        path: str,
        snapshot: Optional[str] = None,
        recursive: bool = False,
        match_pattern: str = None,
    ):
        if not path:
            raise InvalidInputException(f"Expected a valid dir. path, received: `{path}`")
        query = {"path": path, "recursive": recursive}
        if snapshot:
            query["snapshot"] = snapshot
        if match_pattern:
            query["match_pattern"] = match_pattern

        return self.get_request("/files", query_args=query)

    def get_file_content_snapshot(self, path: str, snapshot: Optional[str] = None):
        if not path:
            raise InvalidInputException(f"Expected a valid dir. path, received: `{path}`")
        query = {"path": path}
        if snapshot:
            query["snapshot"] = snapshot
        return self.get_request("/files/content", query_args=query)
