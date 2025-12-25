# src/yggdrasil/databricks/workspaces/databricks_path.py
from __future__ import annotations

import io
import time
import urllib.parse as urlparse
from contextlib import contextmanager
from enum import Enum
from pathlib import PurePosixPath, Path as SysPath
from typing import BinaryIO, Iterator, Optional, Tuple, Union, TYPE_CHECKING

from databricks.sdk.service.catalog import VolumeType

from ...libs.databrickslib import databricks

if databricks is not None:
    from databricks.sdk.service.workspace import ImportFormat, ObjectType
    from databricks.sdk.errors.platform import NotFound, ResourceDoesNotExist, BadRequest, PermissionDenied, AlreadyExists, ResourceAlreadyExists

    NOT_FOUND_ERRORS = NotFound, ResourceDoesNotExist, BadRequest, PermissionDenied
    ALREADY_EXISTS_ERRORS = AlreadyExists, ResourceAlreadyExists, BadRequest

if TYPE_CHECKING:
    from .workspace import Workspace


__all__ = [
    "DatabricksPathKind",
    "DatabricksPath"
]


def _seg_to_str(s) -> str:
    # Handles DatabricksPath, PurePosixPath, Windows Path, etc.
    if isinstance(s, SysPath):
        return s.as_posix()
    return str(s)


class DatabricksPathKind(str, Enum):
    WORKSPACE = "workspace"
    VOLUME = "volume"
    DBFS = "dbfs"

    @classmethod
    def parse(cls, path: str, workspace: Optional["Workspace"] = None) -> Tuple["DatabricksPathKind", Optional["Workspace"], str]:
        from .workspace import Workspace

        if path.startswith("/Workspace") or path.startswith("/Users") or path.startswith("/Shared"):
            if path.startswith("/Users/me"):
                workspace = Workspace() if workspace is None else workspace
                path = path.replace("/Users/me", "/Users/%s" % workspace.current_user.user_name)

            return cls.WORKSPACE, workspace, path
        if path.startswith("/Volumes"):
            return cls.VOLUME, workspace, path

        if path.startswith("dbfs://"):
            parsed = urlparse.urlparse(path)
            kind, _, inner_path = cls.parse(parsed.path)
            workspace = Workspace(host=parsed.hostname) if workspace is None else workspace

            return kind, workspace, inner_path

        return cls.DBFS, workspace, path


class DatabricksPath(SysPath, PurePosixPath):
    _kind: DatabricksPathKind
    _workspace: Optional["Workspace"]

    _is_file: Optional[bool]
    _is_dir: Optional[bool]

    _raw_status: Optional[dict]
    _raw_status_refresh_time: float

    def __new__(
        cls,
        *pathsegments,
        workspace: Optional["Workspace"] = None,
        is_file: Optional[bool] = None,
        is_dir: Optional[bool] = None,
        raw_status: Optional[dict] = None,
        raw_status_refresh_time: float = 0
    ):
        if not pathsegments:
            joined = ""
        else:
            first = _seg_to_str(pathsegments[0])

            # Special case: if someone passes a dbfs://... URL segment, keep it URL-like
            if first.startswith("dbfs://"):
                rest = [_seg_to_str(s).lstrip("/") for s in pathsegments[1:]]
                joined = first.rstrip("/")
                if rest:
                    joined += "/" + "/".join(rest)
            else:
                joined = str(PurePosixPath(*(_seg_to_str(s) for s in pathsegments)))

        kind, w, p = DatabricksPathKind.parse(joined)

        obj = super().__new__(cls, p)

        obj._kind = kind
        obj._workspace = w if workspace is None else workspace
        obj._is_file = is_file
        obj._is_dir = is_dir
        obj._raw_status = raw_status
        obj._raw_status_refresh_time = raw_status_refresh_time

        return obj

    def __enter__(self):
        self.workspace.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.workspace.__exit__(exc_type, exc_val, exc_tb)

    @property
    def workspace(self):
        if self._workspace is None:
            from .workspace import Workspace

            self._workspace = Workspace()
        return self._workspace

    @property
    def kind(self):
        return self._kind

    def is_file(self, *, follow_symlinks = True):
        if self._is_file is None:
            self.refresh_status()
        return self._is_file

    def is_dir(self, *, follow_symlinks = True):
        if self._is_dir is None:
            self.refresh_status()
        return self._is_dir

    def volume_parts(self) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[PurePosixPath]]:
        if self._kind != DatabricksPathKind.VOLUME:
            return None, None, None, None

        s = str(self)
        segs = s.split("/")  # ['', 'Volumes', catalog?, schema?, volume?, ...]

        # still keep the basic sanity check
        if len(segs) < 2 or segs[1] != "Volumes":
            raise ValueError(f"Invalid volume path: {s!r}")

        catalog = segs[2] if len(segs) > 2 and segs[2] else None
        schema = segs[3] if len(segs) > 3 and segs[3] else None
        volume = segs[4] if len(segs) > 4 and segs[4] else None

        # rel path only makes sense after /Volumes/<catalog>/<schema>/<volume>
        if len(segs) > 5:
            rel = "/".join(segs[5:])
            rel_path = PurePosixPath(rel) if rel else PurePosixPath(".")
        else:
            rel_path = None

        return catalog, schema, volume, rel_path

    def refresh_status(self):
        with self as connected:
            sdk = connected.workspace.sdk()

            try:
                if connected._kind == DatabricksPathKind.VOLUME:
                    info = sdk.files.get_metadata(connected.as_files_api_path())

                    connected._raw_status = info
                    connected._is_file, connected._is_dir = True, False
                elif connected._kind == DatabricksPathKind.WORKSPACE:
                    info = sdk.workspace.get_status(connected.as_workspace_api_path())

                    is_dir = info.object_type in (ObjectType.DIRECTORY, ObjectType.REPO)
                    connected._raw_status = info
                    connected._is_file, connected._is_dir = not is_dir, is_dir
                else:
                    info = sdk.dbfs.get_status(connected.as_dbfs_api_path())

                    connected._raw_status = info
                    connected._is_file, connected._is_dir = not info.is_dir, info.is_dir

                connected._raw_status_refresh_time = time.time()
            except (NotFound, ResourceDoesNotExist, BadRequest, PermissionDenied):
                found = next(connected.ls(fetch_size=1, recursive=False, raise_error=False), None)

                if found is None:
                    connected._is_file, connected._is_dir = False, False
                else:
                    connected._is_file, connected._is_dir = False, True

        return connected

    def clear_cache(self):
        self._raw_status = None
        self._raw_status_refresh_time = 0

        self._is_file = None
        self._is_dir = None


    # ---- API path normalization helpers ----

    def as_workspace_api_path(self) -> str:
        """
        Workspace API typically uses paths like /Users/... (not /Workspace/Users/...)
        so we strip the leading /Workspace when present.
        """
        s = str(self)
        return s[len("/Workspace") :] if s.startswith("/Workspace") else s

    def as_dbfs_api_path(self) -> str:
        """
        DBFS REST wants absolute DBFS paths like /tmp/x.
        If the user passes /dbfs/tmp/x (FUSE-style), strip the /dbfs prefix.
        """
        s = str(self)
        return s[len("/dbfs") :] if s.startswith("/dbfs") else s

    def as_files_api_path(self) -> str:
        """
        Files API takes absolute paths, e.g. /Volumes/<...>/file
        """
        return str(self)

    def with_segments(self, *pathsegments):
        """Construct a new path object from any number of path-like objects.
        Subclasses may override this method to customize how new path objects
        are created from methods like `iterdir()`.
        """
        return type(self)(*pathsegments, workspace=self._workspace)

    def exists(self, *, follow_symlinks=True) -> bool:
        if self.is_file():
            return True
        if self.is_dir():
            return True
        return False

    def mkdir(self, mode = 0o777, parents = True, exist_ok = True):
        """
        Create a new directory at this given path.
        """
        with self as connected:
            connected.clear_cache()

            try:
                if connected._kind == DatabricksPathKind.WORKSPACE:
                    connected.workspace.sdk().workspace.mkdirs(self.as_workspace_api_path())
                elif connected._kind == DatabricksPathKind.VOLUME:
                    return connected._create_volume_dir(mode=mode, parents=parents, exist_ok=exist_ok)
                elif connected._kind == DatabricksPathKind.DBFS:
                    connected.workspace.sdk().dbfs.mkdirs(self.as_dbfs_api_path())

                connected._is_file, connected._is_dir = False, True
            except (NotFound, ResourceDoesNotExist):
                if not parents or self.parent == self:
                    raise

                connected.parent.mkdir(parents=True, exist_ok=True)
                connected.mkdir(mode, parents=False, exist_ok=exist_ok)
            except (AlreadyExists, ResourceAlreadyExists):
                # Cannot rely on checking for EEXIST, since the operating system
                # could give priority to other errors like EACCES or EROFS
                if not exist_ok:
                    raise

    def _ensure_volume(self, exist_ok: bool = True):
        catalog_name, schema_name, volume_name, rel = self.volume_parts()
        sdk = self.workspace.sdk()

        if catalog_name:
            try:
                sdk.catalogs.create(name=catalog_name)
            except (AlreadyExists, ResourceAlreadyExists, PermissionDenied, BadRequest):
                # Cannot rely on checking for EEXIST, since the operating system
                # could give priority to other errors like EACCES or EROFS
                if not exist_ok:
                    raise

        if schema_name:
            try:
                sdk.schemas.create(catalog_name=catalog_name, name=schema_name)
            except (AlreadyExists, ResourceAlreadyExists, PermissionDenied, BadRequest):
                # Cannot rely on checking for EEXIST, since the operating system
                # could give priority to other errors like EACCES or EROFS
                if not exist_ok:
                    raise

        if volume_name:
            try:
                sdk.volumes.create(
                    catalog_name=catalog_name,
                    schema_name=schema_name,
                    name=volume_name,
                    volume_type=VolumeType.MANAGED
                )
            except (AlreadyExists, ResourceAlreadyExists, BadRequest):
                # Cannot rely on checking for EEXIST, since the operating system
                # could give priority to other errors like EACCES or EROFS
                if not exist_ok:
                    raise

    def _create_volume_dir(self, mode = 0o777, parents = True, exist_ok = True):
        path = self.as_files_api_path()
        sdk = self.workspace.sdk()

        try:
            sdk.files.create_directory(path)
        except (BadRequest, NotFound, ResourceDoesNotExist) as e:
            if not parents:
                raise

            message = str(e)

            if "not exist" in message:
                self._ensure_volume()

            sdk.files.create_directory(path)
        except (AlreadyExists, ResourceAlreadyExists, BadRequest):
            # Cannot rely on checking for EEXIST, since the operating system
            # could give priority to other errors like EACCES or EROFS
            if not exist_ok:
                raise

        self.clear_cache()
        self._is_file, self._is_dir = False, True

    def remove(self, recursive: bool = True):
        if self.is_file():
            return self.rmfile()
        else:
            return self.rmdir(recursive=recursive)

    def rmfile(self):
        try:
            if self._kind == DatabricksPathKind.VOLUME:
                return self._remove_volume_file()
            elif self._kind == DatabricksPathKind.WORKSPACE:
                return self._remove_workspace_file()
            elif self._kind == DatabricksPathKind.DBFS:
                return self._remove_dbfs_file()
        finally:
            self.clear_cache()

    def _remove_volume_file(self):
        sdk = self.workspace.sdk()

        try:
            sdk.files.delete(self.as_files_api_path())
        except (NotFound, ResourceDoesNotExist, BadRequest, PermissionDenied):
            pass

    def _remove_workspace_file(self):
        sdk = self.workspace.sdk()

        try:
            sdk.workspace.delete(self.as_workspace_api_path(), recursive=True)
        except (NotFound, ResourceDoesNotExist, BadRequest, PermissionDenied):
            pass

    def _remove_dbfs_file(self):
        sdk = self.workspace.sdk()

        try:
            sdk.dbfs.delete(self.as_dbfs_api_path(), recursive=True)
        except (NotFound, ResourceDoesNotExist, BadRequest, PermissionDenied):
            pass

    def rmdir(self, recursive: bool = True):
        with self as connected:
            try:
                if connected._kind == DatabricksPathKind.WORKSPACE:
                    connected.workspace.sdk().workspace.delete(
                        self.as_workspace_api_path(),
                        recursive=recursive
                    )
                elif connected._kind == DatabricksPathKind.VOLUME:
                    return self._remove_volume_dir(recursive=recursive)
                else:
                    connected.workspace.sdk().dbfs.delete(
                        self.as_dbfs_api_path(),
                        recursive=recursive
                    )
            except (NotFound, ResourceDoesNotExist, BadRequest, PermissionDenied):
                pass
            finally:
                connected.clear_cache()

    def _remove_volume_dir(self, recursive: bool = True):
        root_path = self.as_files_api_path()
        catalog_name, schema_name, volume_name, rel = self.volume_parts()

        sdk = self.workspace.sdk()

        if rel is None:
            try:
                sdk.volumes.delete(f"{catalog_name}.{schema_name}.{volume_name}")
            except (NotFound, ResourceDoesNotExist, BadRequest, PermissionDenied):
                pass
        elif volume_name is None:
            try:
                sdk.schemas.delete(f"{catalog_name}.{schema_name}", force=True)
            except (NotFound, ResourceDoesNotExist, BadRequest, PermissionDenied):
                pass
        else:
            try:
                sdk.files.delete_directory(root_path)
            except (NotFound, ResourceDoesNotExist, BadRequest, PermissionDenied) as e:
                message = str(e)

                if recursive and "directory is not empty" in message:
                    for child_path in self.ls():
                        child_path.remove(recursive=True)
                    sdk.files.delete_directory(root_path)
                else:
                    pass

        self.clear_cache()

    def ls(self, recursive: bool = False, fetch_size: int = None, raise_error: bool = True):
        if self._kind == DatabricksPathKind.VOLUME:
            for _ in self._ls_volume(recursive=recursive, fetch_size=fetch_size, raise_error=raise_error):
                yield _
        elif self._kind == DatabricksPathKind.WORKSPACE:
            for _ in self._ls_workspace(recursive=recursive, fetch_size=fetch_size, raise_error=raise_error):
                yield _
        elif self._kind == DatabricksPathKind.DBFS:
            for _ in self._ls_dbfs(recursive=recursive, fetch_size=fetch_size, raise_error=raise_error):
                yield _

    def _ls_volume(self, recursive: bool = False, fetch_size: int = None, raise_error: bool = True):
        catalog_name, schema_name, volume_name, rel = self.volume_parts()
        sdk = self.workspace.sdk()

        if rel is None:
            if volume_name is None:
                try:
                    for info in sdk.volumes.list(
                        catalog_name=catalog_name,
                        schema_name=schema_name
                    ):
                        base = DatabricksPath(
                            f"/Volumes/{info.catalog_name}/{info.schema_name}/{info.name}",
                            workspace=self.workspace,
                            is_file=False,
                            is_dir=True
                        )

                        if recursive:
                            for sub in base._ls_volume(recursive=recursive):
                                yield sub
                        else:
                            yield base
                except (NotFound, ResourceDoesNotExist, BadRequest, PermissionDenied):
                    if raise_error:
                        raise
            elif schema_name is None:
                try:
                    for info in sdk.schemas.list(catalog_name=catalog_name,):
                        base = DatabricksPath(
                            f"/Volumes/{info.catalog_name}/{info.name}",
                            workspace=self.workspace,
                            is_file=False,
                            is_dir=True
                        )

                        if recursive:
                            for sub in base._ls_volume(recursive=recursive):
                                yield sub
                        else:
                            yield base
                except (NotFound, ResourceDoesNotExist, BadRequest, PermissionDenied):
                    if raise_error:
                        raise
            else:
                try:
                    for info in sdk.catalogs.list():
                        base = DatabricksPath(
                            f"/Volumes/{info.name}",
                            workspace=self.workspace,
                            is_file=False,
                            is_dir=True
                        )

                        if recursive:
                            for sub in base._ls_volume(recursive=recursive):
                                yield sub
                        else:
                            yield base
                except (NotFound, ResourceDoesNotExist, BadRequest, PermissionDenied):
                    if raise_error:
                        raise
        else:
            try:
                for info in sdk.files.list_directory_contents(self.as_files_api_path(), page_size=fetch_size):
                    base = DatabricksPath(
                        info.path,
                        workspace=self.workspace,
                        is_file=not info.is_directory,
                        is_dir=info.is_directory
                    )

                    if recursive and info.is_directory:
                        for sub in base._ls_volume(recursive=recursive):
                            yield sub
                    else:
                        yield base
            except (NotFound, ResourceDoesNotExist, BadRequest, PermissionDenied):
                if raise_error:
                    raise

    def _ls_workspace(self, recursive: bool = True, fetch_size: int = None, raise_error: bool = True):
        sdk = self.workspace.sdk()

        try:
            for info in sdk.workspace.list(self.as_workspace_api_path(), recursive=recursive):
                is_dir = info.object_type in (ObjectType.DIRECTORY, ObjectType.REPO)
                base = DatabricksPath(
                    info.path,
                    workspace=self.workspace,
                    is_file=not is_dir,
                    is_dir=is_dir
                )

                yield base
        except (NotFound, ResourceDoesNotExist, BadRequest, PermissionDenied):
            if raise_error:
                raise

    def _ls_dbfs(self, recursive: bool = True, fetch_size: int = None, raise_error: bool = True):
        sdk = self.workspace.sdk()

        try:
            for info in sdk.dbfs.list(self.as_workspace_api_path(), recursive=recursive):
                base = DatabricksPath(
                    info.path,
                    workspace=self.workspace,
                    is_file=not info.is_dir,
                    is_dir=info.is_dir
                )

                yield base
        except (NotFound, ResourceDoesNotExist, BadRequest, PermissionDenied):
            if raise_error:
                raise

    @contextmanager
    def open(
        self,
        mode='r',
        buffering=-1,
        encoding=None,
        errors=None,
        newline=None,
        *,
        workspace: Optional["Workspace"] = None,
        overwrite: bool = True,
    ) -> Iterator[Union[BinaryIO, io.TextIOBase]]:
        """
        Open this Databricks path using databricks-sdk's WorkspaceClient.

        Supported:
          - read:  "rb", "r"
          - write: "wb", "w"  (buffered; uploads on close for WORKSPACE/VOLUME)

        Notes:
          - VOLUME: uses w.files.download/upload (Files API). :contentReference[oaicite:5]{index=5}
          - DBFS: uses w.dbfs.open when possible. :contentReference[oaicite:6]{index=6}
          - WORKSPACE: uses w.workspace.download/upload. :contentReference[oaicite:7]{index=7}
        """
        if mode not in {"rb", "r", "wb", "w"}:
            raise ValueError(f"Unsupported mode {mode!r}. Use r/rb/w/wb.")

        if encoding is None:
            encoding = None if "b" in mode else "utf-8"
        reading = "r" in mode

        if reading:
            with self.open_read(encoding=encoding) as f:
                yield f
        else:
            with self.open_write(encoding=encoding) as f:
                yield f

    @contextmanager
    def open_read(self, encoding: str | None = None):
        with self as connected:
            if connected._kind == DatabricksPathKind.VOLUME:
                with connected._open_read_volume(encoding=encoding) as f:
                    yield f
            elif connected._kind == DatabricksPathKind.WORKSPACE:
                with connected._open_read_workspace(encoding=encoding) as f:
                    yield f
            else:
                with connected._open_read_dbfs(encoding=encoding) as f:
                    yield f

    @contextmanager
    def _open_read_volume(self, encoding: str | None = None):
        workspace_client = self.workspace.sdk()
        path = self.as_files_api_path()

        # Files.download returns a stream-like response body. :contentReference[oaicite:8]{index=8}
        resp = workspace_client.files.download(path)
        raw = io.BytesIO(resp.contents.read())

        if encoding is not None:
            with io.TextIOWrapper(raw, encoding=encoding) as f:
                yield f
        else:
            with raw as f:
                yield f

    @contextmanager
    def _open_read_workspace(self, encoding: str | None = None):
        workspace_client = self.workspace.sdk()
        path = self.as_workspace_api_path()

        # Files.download returns a stream-like response body. :contentReference[oaicite:8]{index=8}
        raw = workspace_client.workspace.download(path)  # returns BinaryIO :contentReference[oaicite:10]{index=10}

        if encoding is not None:
            raw = io.BytesIO(raw.read())

            with io.TextIOWrapper(raw, encoding=encoding) as f:
                yield f
        else:
            with raw as f:
                yield f

    @contextmanager
    def _open_read_dbfs(self, encoding: str | None = None):
        workspace_client = self.workspace.sdk()
        path = self.as_dbfs_api_path()

        # dbfs.open gives BinaryIO for streaming reads :contentReference[oaicite:12]{index=12}
        raw = workspace_client.dbfs.open(path, read=True)

        if encoding is not None:
            with io.TextIOWrapper(raw, encoding=encoding) as f:
                yield f
        else:
            with raw as f:
                yield f

    @contextmanager
    def open_write(self, encoding: str | None = None):
        with self as connected:
            if connected._kind == DatabricksPathKind.VOLUME:
                with connected._open_write_volume(encoding=encoding) as f:
                    yield f
            elif connected._kind == DatabricksPathKind.WORKSPACE:
                with connected._open_write_workspace(encoding=encoding) as f:
                    yield f
            else:
                with connected._open_write_dbfs(encoding=encoding) as f:
                    yield f

    @contextmanager
    def _open_write_volume(self, encoding: str | None = None, overwrite: bool = True):
        workspace_client = self.workspace.sdk()
        path = self.as_files_api_path()

        # Buffer locally then upload stream on exit. :contentReference[oaicite:9]{index=9}
        buf = io.BytesIO()

        if encoding is not None:
            tw = io.TextIOWrapper(buf, encoding=encoding, write_through=True)
            try:
                yield tw
            finally:
                tw.flush()
                buf.seek(0)

                try:
                    workspace_client.files.upload(path, buf, overwrite=overwrite)
                except (NotFound, ResourceDoesNotExist, BadRequest):
                    self.parent.mkdir(parents=True, exist_ok=True)
                    workspace_client.files.upload(path, buf, overwrite=overwrite)

                tw.detach()
        else:
            try:
                yield buf
            finally:
                buf.seek(0)

                try:
                    workspace_client.files.upload(path, buf, overwrite=overwrite)
                except (NotFound, ResourceDoesNotExist, BadRequest):
                    self.parent.mkdir(parents=True, exist_ok=True)
                    workspace_client.files.upload(path, buf, overwrite=overwrite)

    @contextmanager
    def _open_write_workspace(self, encoding: str | None = None, overwrite: bool = True):
        workspace_client = self.workspace.sdk()
        path = self.as_workspace_api_path()

        # Buffer then upload (AUTO works for workspace files) :contentReference[oaicite:11]{index=11}
        buf = io.BytesIO()

        if encoding is not None:
            tw = io.TextIOWrapper(buf, encoding=encoding, write_through=True)
            try:
                yield tw
            finally:
                tw.flush()
                buf.seek(0)

                try:
                    workspace_client.workspace.upload(
                        path, buf, format=ImportFormat.AUTO, overwrite=overwrite
                    )
                except Exception as e:
                    message = str(e)
                    if "parent folder" in message and "does not exist" in message:
                        self.parent.mkdir(parents=True)
                        buf.seek(0)
                        workspace_client.workspace.upload(
                            path, buf, format=ImportFormat.AUTO, overwrite=overwrite
                        )
                    else:
                        raise e

                tw.detach()
        else:
            try:
                yield buf
            finally:
                buf.seek(0)

                try:
                    workspace_client.workspace.upload(
                        path, buf, format=ImportFormat.AUTO, overwrite=overwrite
                    )
                except Exception as e:
                    message = str(e)
                    if "parent folder" in message and "does not exist" in message:
                        self.parent.mkdir(parents=True)
                        buf.seek(0)
                        workspace_client.workspace.upload(
                            path, buf, format=ImportFormat.AUTO, overwrite=overwrite
                        )
                    else:
                        raise e

    @contextmanager
    def _open_write_dbfs(self, encoding: str | None = None, overwrite: bool = True):
        workspace_client = self.workspace.sdk()
        path = self.as_dbfs_api_path()

        raw = workspace_client.dbfs.open(path, write=True, overwrite=overwrite)  # :contentReference[oaicite:13]{index=13}

        if encoding is not None:
            with io.TextIOWrapper(raw, encoding=encoding) as f:
                yield f
        else:
            with raw as f:
                yield f

        self.clear_cache()
        self._is_file, self._is_dir = True, False