# pyright: reportTypedDictNotRequiredAccess=false, reportMissingModuleSource=false

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, cast
from urllib.parse import urlparse

import googleapiclient.discovery
from flask import Blueprint, g, render_template, request
from google.api_core.retry import Retry
from google.oauth2.credentials import Credentials

from .auth import auth_required


if TYPE_CHECKING:
    from collections.abc import Iterator

    from flask.typing import ResponseValue
    from googleapiclient._apis.drive.v2 import DriveResource as DriveV2Resource
    from googleapiclient._apis.drive.v3 import DriveResource as DriveV3Resource
    from googleapiclient._apis.drive.v3 import File as FileV3
    from googleapiclient._apis.oauth2.v2 import Oauth2Resource
bp = Blueprint("drive", __name__, url_prefix="/drive")


def _get_drive_v3_resource() -> DriveV3Resource:
    if not hasattr(g, "drive_resource"):
        g.drive_resource = googleapiclient.discovery.build(
            "drive", "v3", credentials=cast(Credentials, g.credentials)
        )
    return g.drive_resource


def _get_drive_v2_resource() -> DriveV2Resource:
    if not hasattr(g, "drive_resource"):
        g.drive_resource = googleapiclient.discovery.build(
            "drive", "v2", credentials=cast(Credentials, g.credentials)
        )
    return g.drive_resource


@bp.route("/hello")
@auth_required
def hello() -> ResponseValue:
    oauth2_client: Oauth2Resource = googleapiclient.discovery.build(
        "oauth2", "v2", credentials=cast(Credentials, g.credentials)
    )
    user = oauth2_client.userinfo().v2().me().get().execute()
    return f"hello {user} (drive: /hello)"


@bp.route("/select_folder")
@auth_required
def select_folder() -> ResponseValue:
    q = request.args.get("q", "")
    own = request.args.get("own", "1") == "1"
    shared = request.args.get("shared", "1") == "1"
    searched = "q" in request.args

    folders: list[FileV3] = []
    if searched:
        query_parts = ["mimeType='application/vnd.google-apps.folder'", "trashed=false"]
        if q:
            escaped = q.replace("\\", "\\\\").replace("'", "\\'")
            query_parts.append(f"name contains '{escaped}'")
        if own and not shared:
            query_parts.append("'me' in owners")
        elif shared and not own:
            query_parts.append("not 'me' in owners")

        drive = _get_drive_v3_resource()
        result = (
            drive.files()
            .list(
                q=" and ".join(query_parts),
                orderBy="name",
                pageSize=100,
                fields="files(id,name)",
            )
            .execute()
        )
        folders = result.get("files", [])

    return render_template(
        "select_folder.html",
        q=q,
        own=own,
        shared=shared,
        folders=folders,
        searched=searched,
    )


_FILE_ID_MIN_LEN = 20

_CATALOG_FIELDS = (
    "nextPageToken,"
    "files(id,name,mimeType,shortcutDetails,createdTime,modifiedTime,"
    "lastModifyingUser(emailAddress),quotaBytesUsed,inheritedPermissionsDisabled)"
)
_PERMISSION_FIELDS = (
    "permissions(type,emailAddress,role,pendingOwner,permissionDetails(inherited))"
)

_DRIVE_BATCH_LIMIT = 100
_RETRY = Retry(timeout=300)


@dataclass
class Perm:
    pending_owner: str = ""
    owner: str = ""
    writers: list[str] = field(default_factory=list)
    inherited_writers: list[str] = field(default_factory=list)
    commenters: list[str] = field(default_factory=list)
    inherited_commenters: list[str] = field(default_factory=list)
    viewers: list[str] = field(default_factory=list)
    inherited_viewers: list[str] = field(default_factory=list)


def make_row(f: FileV3) -> dict[str, str | bool]:
    print(json.dumps(f, indent=2))
    perm = Perm()
    for p in f.get("permissions", []):
        principal = ""
        if p["type"] == "anyone":
            principal = "anyone"
        elif p["type"] in ["user", "group"]:
            principal = p["emailAddress"]
        else:
            msg = f"unhandled type {p['type']}"
            raise RuntimeError(msg)
        inherited = cast(bool, p["permissionDetails"][0]["inherited"])
        if p["type"] == "user" and p["pendingOwner"]:
            perm.pending_owner = principal
        if p["role"] == "owner":
            perm.owner = principal
        elif p["role"] == "writer":
            p_field = perm.inherited_writers if inherited else perm.writers
            p_field.append(principal)
        elif p["role"] == "commenter":
            p_field = perm.inherited_commenters if inherited else perm.commenters
            p_field.append(principal)
        elif p["role"] == "reader":
            p_field = perm.inherited_viewers if inherited else perm.viewers
            p_field.append(principal)
        else:
            msg = f"unhandled role {p['role']}"
            raise RuntimeError(msg)
        # TODO: MORE

    shortcut_details = f.get("shortcutDetails", {})
    return {
        "id": f["id"],
        "name": f["name"],
        "mimeType": f["mimeType"],
        "shortcuttId": shortcut_details.get("targetId", ""),
        "shortcutMimeType": shortcut_details.get("targetMimeType", ""),
        "createdTime": f["createdTime"],
        "modifiedTime": f["modifiedTime"],
        "lastModifiedBy": f.get("lastModifyingUser", {}).get("emailAddress", ""),
        "quotaBytesUsed": f["quotaBytesUsed"],
        "inheritedPermissionsDisabled": f["inheritedPermissionsDisabled"],
        "pendingOwner": perm.pending_owner or "",
        "owner": perm.owner or "",
        "writers": ",".join(perm.writers),
        "inheritedWriters": ",".join(perm.inherited_writers),
        "commenters": ",".join(perm.commenters),
        "inheritedCommenters": ",".join(perm.inherited_commenters),
        "viewers": ",".join(perm.viewers),
        "inheritedViewers": ",".join(perm.inherited_viewers),
    }


def _write_batch_to_spreadsheet(files: list[FileV3]) -> None:
    # print(json.dumps(files, indent=2))
    rows = [make_row(f) for f in files]
    print(json.dumps(rows, indent=2))


def _add_permission_details(batch: list[FileV3]) -> None:
    drive = _get_drive_v3_resource()
    by_id = {f["id"]: f for f in batch}

    def callback(
        request_id: str, response: FileV3, exception: Exception | None
    ) -> None:
        if exception:
            raise exception
        f = by_id.get(request_id)
        if f is None:
            msg = f"unexpected request_id {request_id} in batch callback"
            raise KeyError(msg)
        perms = response.get("permissions")
        if perms is not None:
            # Permissions can be missing if we don't have sufficient access.
            f["permissions"] = perms

    for i in range(0, len(batch), _DRIVE_BATCH_LIMIT):
        http_batch = drive.new_batch_http_request()  # pyright: ignore[reportUnknownMemberType]
        for f in batch[i : i + _DRIVE_BATCH_LIMIT]:
            http_batch.add(
                drive.files().get(fileId=f["id"], fields=_PERMISSION_FIELDS),
                request_id=f["id"],
                callback=callback,
            )
        _RETRY(http_batch.execute)()


def _enumerate_folder(folder_id: str) -> Iterator[FileV3]:
    drive = _get_drive_v3_resource()
    queue = [folder_id]
    while queue:
        current_id = queue.pop(0)
        page_token = ""
        while True:
            req = drive.files().list(
                q=f"'{current_id}' in parents and trashed=false",
                fields=_CATALOG_FIELDS,
                pageSize=1000,
                pageToken=page_token,
            )
            resp = _RETRY(req.execute)()
            for item in resp.get("files", []):
                if item.get("mimeType") == "application/vnd.google-apps.folder":
                    queue.append(item["id"])
                yield item
            page_token = resp.get("nextPageToken")
            if not page_token:
                break


@bp.route("/catalog")
@auth_required
def catalog() -> ResponseValue:
    folder_url = request.args.get("folder_url", "")
    submitted = "folder_url" in request.args
    count = 0
    error = ""

    if submitted and folder_url:
        parts = [
            p for p in urlparse(folder_url).path.split("/") if len(p) > _FILE_ID_MIN_LEN
        ]
        if not parts:
            error = f"Could not extract folder ID from: {folder_url}"
        else:
            folder_id = parts[-1]
            batch: list[FileV3] = []
            for item in _enumerate_folder(folder_id):
                batch.append(item)
                if len(batch) >= _DRIVE_BATCH_LIMIT:
                    _add_permission_details(batch)
                    _write_batch_to_spreadsheet(batch)
                    count += len(batch)
                    batch.clear()
            if batch:
                _add_permission_details(batch)
                _write_batch_to_spreadsheet(batch)
                count += len(batch)

    return render_template(
        "catalog.html",
        folder_url=folder_url,
        submitted=submitted,
        count=count,
        error=error,
    )


@bp.route("/transfer_file")
@auth_required
def transfer_file() -> ResponseValue:
    # TODO: handle errors!
    # TODO: reject recipient == owner
    # TODO: don't transfer to non-writer on folder (that can be inherited though)
    file_url = request.args.get("file_url", "")
    new_owner = request.args.get("new_owner", "")
    # TODO: would be nice to optionally append @gmail.com to new_owner i
    transfer = request.args.get("transfer", "")
    result = ""
    if transfer:
        parts = [
            p for p in urlparse(file_url).path.split("/") if len(p) > _FILE_ID_MIN_LEN
        ]
        if not parts:
            result = f"Invalid url {file_url}"
            file_url = ""
        else:
            file_id = parts[-1]
            result = f"didn't actually transfer {file_url} ({file_id})to {new_owner}"
            drive_resource = _get_drive_v2_resource()
            #   v2 javascript
            #   const response = Drive.Permissions.insert(
            #     {
            #       role: "writer", type: "user", value: RECIPIENT, pendingOwner: true
            #     },
            #     fileId,
            #     {
            #       fields: "emailAddress,type,role,id,pendingOwner",
            #     },
            #   )

            permissions_resource = drive_resource.permissions()
            ps = permissions_resource.list(
                fileId=file_id,
                fields="items(emailAddress,type,role,id,pendingOwner,permissionDetails)",
            ).execute()["items"]
            ps_before = [
                p
                for p in ps
                if p.get("emailAddress", None) == new_owner
                and p.get("role", None) in {"owner", "writer"}
            ]
            print(json.dumps(ps_before, indent=2))
            roles = [p["role"] for p in ps_before]
            print(f"{roles=}")
            owner = "owner" in roles
            writer = "writer" in roles
            if owner or not writer:
                result = (
                    "recipient is already owner"
                    if owner
                    else "recipient must already be editor"
                )
                print(result)
                return render_template(
                    "transfer_file.html",
                    file_url=file_url,
                    new_owner=new_owner,
                    result=result,
                )
            # insert + writer works in v2. create + writer does not work in v3.
            # should be checking whether they are also editor on the folder.
            # re-sends if we repeat? re-sends, so we could make not re-sending an option
            # TODO: is it insert? update? either?
            # TODO: presumably writer not owner
            _ = permissions_resource.insert(
                fileId=file_id,
                body={
                    "role": "writer",
                    "type": "user",
                    "value": new_owner,
                    "pendingOwner": True,
                },
            ).execute()
            return render_template(
                "transfer_file.html",
                file_url=file_url,
                new_owner=new_owner,
                result="done?",
            )
            ps = (
                permissions_resource.list(
                    fileId=file_id,
                    fields="permissions(emailAddress,type,role,id,pendingOwner,permissionDetails)",
                ).execute()
            )["permissions"]
            ps_before = [p for p in ps if p.get("emailAddress", None) == new_owner]
            print(json.dumps(ps_before, indent=2))
            roles = [p.get("role", None) for p in ps_before]
            owner = "owner" in roles
            writer = "writer" in roles
            if owner or not writer:
                result = (
                    "recipient is already owner"
                    if owner
                    else "recipient must already be editor"
                )
            else:
                not_inherited = bool(
                    [
                        p
                        for p in ps_before
                        if p.get("role", None) == "writer"
                        and not p.get("permissions", {}).get(
                            "inherited", True
                        )  # Default to True in case inherited is missing
                    ]
                )
                if True or not not_inherited:
                    _ = permissions_resource.create(
                        fileId=file_id,
                        body={
                            "role": "writer",
                            "type": "user",
                            "emailAddress": new_owner,
                            "pendingOwner": True,
                        },
                    ).execute()
                    result = "transfer started?"
                else:
                    result = "time to transfer..."

                # _ = (
                #     drive.permissions()
                #     .create(
                #         fileId=file_id,
                #         body={
                #             "pendingOwner": True,
                #             "role": "writer",
                #             "type": "user",
                #             "emailAddress": new_owner,
                #         },
                #     )
                #     .execute()
                # )
            print(result)

    return render_template(
        "transfer_file.html", file_url=file_url, new_owner=new_owner, result=result
    )
