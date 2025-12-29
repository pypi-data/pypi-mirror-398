import base64
import requests  # type: ignore[import-untyped]
import time
from typing import Any, Annotated, TypedDict

APS_BASE_URL = "https://developer.api.autodesk.com"
MD_BASE_URL = f"{APS_BASE_URL}/modelderivative/v2"


class PropertiesPayload(TypedDict, total=False):
    data: Annotated[dict[str, Any], "APS properties response payload"]


def to_md_urn(wip_urn: str) -> str:
    """Convert WIP URN to Model Derivative URN."""
    raw = wip_urn.split("?", 1)[0]
    encoded = base64.urlsafe_b64encode(raw.encode("utf8")).decode("utf8")
    return encoded.rstrip("=")


def get_revit_version_from_manifest(manifest: dict) -> str | None:
    """Extract Revit version from manifest."""
    try:
        derivatives = manifest.get("derivatives", [])
        if not derivatives:
            return None

        for derivative in derivatives:
            properties = derivative.get("properties", {})
            doc_info = properties.get("Document Information", {})
            rvt_version = doc_info.get("RVTVersion")
            if rvt_version:
                return str(rvt_version)

        return None
    except Exception as e:
        print(f"Error extracting Revit version from manifest: {e}")
        return None


def fetch_manifest(autodesk_file_param, token):
    """Fetch model derivative manifest."""
    version = autodesk_file_param.get_latest_version(token)
    urn = version.urn
    encoded_urn = base64.urlsafe_b64encode(urn.encode()).decode().rstrip("=")
    url = f"https://developer.api.autodesk.com/modelderivative/v2/designdata/{encoded_urn}/manifest"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_viewables_from_urn(
    token: str, object_urn: Annotated[str, "URN in bs64"]
) -> list[dict[str, Any]]:
    """
    Get available viewables (views) from a translated model.
    """

    response = requests.get(
        f"{MD_BASE_URL}/designdata/{object_urn}/manifest",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    response.raise_for_status()

    manifest = response.json()
    viewables: list[dict[str, Any]] = []

    def clean_name(name: str) -> str:
        """Normalize view name by stripping cosmetic prefixes."""
        return name.replace("[3D] ", "").replace("[2D] ", "").strip()

    # Prefer a single derivative tree (svf2 first, then svf) to avoid double-processing
    derivatives = manifest.get("derivatives", [])
    derivative = next(
        (d for d in derivatives if d.get("outputType") == "svf2"),
        next((d for d in derivatives if d.get("outputType") == "svf"), None),
    )

    if not derivative:
        print("No svf/svf2 derivative found in manifest")
        return viewables

    seen: set[tuple[str, str]] = set()  # (guid, display_name)
    for geom in derivative.get("children", []):
        if geom.get("type") != "geometry":
            continue
        role = geom.get("role", "")
        if role not in ["3d", "2d"]:
            continue
        guid = geom.get("guid")
        if not guid:
            continue

        base_name = geom.get("name", "") or "Unnamed View"
        candidate_names = [base_name]
        for child in geom.get("children", []):
            if child.get("type") == "view":
                candidate_names.append(child.get("name") or base_name)

        display_name = None
        for name in candidate_names:
            cleaned = clean_name(name)
            if cleaned:
                display_name = cleaned
                break
        if not display_name:
            display_name = base_name or "Unnamed View"

        key = (guid, display_name)
        if key in seen:
            continue
        seen.add(key)
        viewables.append({"guid": guid, "name": display_name, "role": role})

    return viewables


def get_view_names_from_manifest(manifest: dict) -> list[str]:
    """
    Extract view names from a model derivative manifest for IFC export selection.
    Returns a list of view names that can be used in MultiSelectField options.
    """
    seen = set()
    view_names = []

    for derivative in manifest.get("derivatives", []):
        if derivative.get("outputType") in ["svf", "svf2"]:
            for geometry_node in derivative.get("children", []):
                if geometry_node.get("type") == "geometry" and geometry_node.get(
                    "role"
                ) in ["3d", "2d"]:
                    # base name is the geometry node name
                    base_name = geometry_node.get("name", "")
                    candidate_names = [base_name]
                    # if there is a child of type view with its own name, include that too
                    for child_node in geometry_node.get("children", []):
                        if child_node.get("type") == "view":
                            name = child_node.get("name", "") or base_name
                            candidate_names.append(name)
                    for name in candidate_names:
                        if not name:
                            continue
                        # remove any cosmetic prefixes
                        clean = name.replace("[3D] ", "").replace("[2D] ", "")
                        if clean not in seen:
                            seen.add(clean)
                            view_names.append(clean)

    print(f"Found {len(view_names)} view name(s) in manifest")
    return view_names


def get_2lo_token(client_id: str, client_secret: str) -> str:
    r = requests.post(
        f"{APS_BASE_URL}/authentication/v2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "data:read data:write bucket:create bucket:read bucket:update viewables:read",
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def get_metadata_viewables(
    token: str,
    urn_bs64: Annotated[str, "URN in base64"],
    *,
    timeout: int = 60,
    poll_interval_s: float = 2.0,
    max_poll_time_s: float = 120.0,
) -> list[dict[str, Any]]:
    """
    Fetch available metadata viewables from GET /{urn}/metadata.
    """
    url = f"{MD_BASE_URL}/designdata/{urn_bs64}/metadata"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    deadline = time.monotonic() + max_poll_time_s
    while True:
        resp = requests.get(url, headers=headers, timeout=timeout)

        if resp.status_code == 202:
            if time.monotonic() >= deadline:
                raise RuntimeError(f"Timed out waiting for metadata for {url}")
            time.sleep(poll_interval_s)
            continue

        resp.raise_for_status()
        payload = resp.json()
        break

    data = payload.get("data")
    if isinstance(data, dict):
        views = data.get("metadata", [])
        return views if isinstance(views, list) else []

    if isinstance(data, list):
        return data

    return []


def get_all_model_properties(
    token: str,
    urn_bs64: Annotated[str, "URN in base64"],
    model_guid: str,
    *,
    force: bool = False,
    timeout: int = 60,
    poll_interval_s: float = 2.0,
    max_poll_time_s: float = 120.0,
    session: requests.Session | None = None,
) -> PropertiesPayload:
    """
    Fetch ALL object properties for a translated model view (viewable).

    - calls GET /{urn}/metadata/{modelGuid}/properties.
    - If the service returns 202 (still processing), it retries until 200 or timeout.
    - If force=True, sends x-ads-force: true to force re-parsing properties.

    Returns the raw JSON response from the Properties endpoint.
    """
    s = session or requests.Session()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    if force:
        headers["x-ads-force"] = "true"

    props_url = f"{MD_BASE_URL}/designdata/{urn_bs64}/metadata/{model_guid}/properties"
    deadline = time.monotonic() + max_poll_time_s
    while True:
        resp = s.get(props_url, headers=headers, timeout=timeout)

        # 202 means: accepted, processing not complete; repeat until 200
        if resp.status_code == 202:
            if time.monotonic() >= deadline:
                raise RuntimeError(
                    "Timed out waiting for APS Model Derivative to finish processing "
                    f"(last status 202) for {props_url}"
                )
            time.sleep(poll_interval_s)
            continue

        if resp.status_code >= 400:
            detail = ""
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text[:500]
            raise RuntimeError(
                f"APS request failed: {resp.status_code} {resp.reason} for {props_url}. Details: {detail}"
            )

        return resp.json()
