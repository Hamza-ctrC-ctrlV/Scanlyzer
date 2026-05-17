"""
Supabase client initialization and database operations
"""
import os
import logging
from supabase import create_client, Client
from dotenv import load_dotenv
from io import BytesIO
import json

load_dotenv()

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Lazily initialized clients so importing this module does not fail in tests
# or local scripts that do not need Supabase access.
supabase: Client | None = None
supabase_admin: Client | None = None


def _get_supabase_client() -> Client:
    """Return the anon Supabase client, creating it on first use."""
    global supabase
    if supabase is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in .env")
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return supabase


def _get_supabase_admin_client() -> Client:
    """Return the admin Supabase client, creating it on first use."""
    global supabase_admin
    if supabase_admin is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env")
        supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return supabase_admin


def create_tables_if_not_exist():
    """Create users and scans tables in Supabase (run once during startup)"""
    # Note: Manually create tables in Supabase dashboard with this schema:
    # 
    # users table:
    # - id (UUID, Primary Key)
    # - email (Text, Unique)
    # - created_at (Timestamp)
    # 
    # scans table:
    # - id (UUID, Primary Key)
    # - user_id (UUID, FK to users.id)
    # - scan_date (Timestamp)
    # - target_url (Text)
    # - vulnerabilities_count (Integer)
    # - patches_count (Integer)
    # - file_path_vulnerabilities (Text)  # stored report JSON text for backward compatibility
    # - file_path_patches (Text)          # stored report JSON text for backward compatibility
    # - created_at (Timestamp)
    pass


def signup(email: str, password: str) -> dict:
    """Register a new user with email and password"""
    try:
        response = _get_supabase_client().auth.sign_up({
            "email": email,
            "password": password,
        })
        
        # Handle response - session may be None if email verification is required
        session = response.session if response.session else None
        
        return {
            "success": True,
            "user_id": response.user.id,
            "email": response.user.email,
            "session": {
                "access_token": session.access_token if session else response.user.id,
                "refresh_token": session.refresh_token if session else None,
            } if session or response.user else None,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def login(email: str, password: str) -> dict:
    """Login user with email and password"""
    try:
        response = _get_supabase_client().auth.sign_in_with_password({
            "email": email,
            "password": password,
        })
        
        # Ensure session exists
        if not response.session:
            return {"success": False, "error": "No session created. Please check your credentials."}
        
        return {
            "success": True,
            "user_id": response.user.id,
            "email": response.user.email,
            "session": {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def verify_token(token: str) -> dict:
    """Verify JWT token and return user info"""
    try:
        response = _get_supabase_client().auth.get_user(token)
        return {
            "success": True,
            "user_id": response.user.id,
            "email": response.user.email,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def ensure_user_profile(user_id: str, email: str | None = None) -> dict:
    """Create or update the profile row required by scans.user_id."""
    try:
        supabase_admin_client = _get_supabase_admin_client()
        existing = supabase_admin_client.table("users").select("id,email").eq("id", user_id).execute()
        if existing.data:
            return {"success": True, "data": existing.data[0]}

        profile_email = email
        if not profile_email:
            profile_email = f"{user_id}@users.local"

        response = supabase_admin_client.table("users").upsert({
            "id": user_id,
            "email": profile_email,
        }).execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        return {"success": False, "error": str(e)}


def save_scan(user_id: str, target_url: str, vulnerabilities_count: int,
              patches_count: int, file_path_vulnerabilities: str,
              file_path_patches: str, scan_id: str, email: str | None = None,
              vulnerabilities_report: dict | None = None,
              patches_report: dict | None = None) -> dict:
    """Save a scan record to the database"""
    try:
        profile_result = ensure_user_profile(user_id=user_id, email=email)
        if not profile_result["success"]:
            return profile_result

        supabase_admin_client = _get_supabase_admin_client()

        # If full report objects are provided, attempt to upload them to Supabase Storage
        final_vul_path = file_path_vulnerabilities
        final_patch_path = file_path_patches

        # Compute score and stats if patches_report is provided
        query_suffix = ""
        if patches_report and isinstance(patches_report, dict):
            patches = patches_report.get("patches", [])
            if patches:
                from utils.helpers import compute_scan_stats
                score, stats, _ = compute_scan_stats(patches)
                import urllib.parse
                encoded_stats = urllib.parse.quote(json.dumps(stats))
                duration = patches_report.get("scan_duration_total", 0)
                query_suffix = f"?score={score}&stats={encoded_stats}&duration={duration}"

        try:
            if vulnerabilities_report is not None:
                bucket = os.getenv("SUPABASE_REPORTS_BUCKET", "vulnerabilities")
                object_path = f"{user_id}/{scan_id}-vulnerabilities.json"
                upload_res = upload_report_to_storage(bucket, object_path, json.dumps(vulnerabilities_report, ensure_ascii=False).encode("utf-8"))
                if upload_res.get("success"):
                    # prefer public URL when available
                    final_vul_path = upload_res.get("public_url") or f"{bucket}/{object_path}"

            if patches_report is not None:
                bucket = os.getenv("SUPABASE_PATCHES_BUCKET", "patches")
                object_path = f"{user_id}/{scan_id}-patches.json"
                upload_res = upload_report_to_storage(bucket, object_path, json.dumps(patches_report, ensure_ascii=False).encode("utf-8"))
                if upload_res.get("success"):
                    final_patch_path = (upload_res.get("public_url") or f"{bucket}/{object_path}") + query_suffix
        except Exception:
            # Fall back to storing raw JSON text if upload fails
            if vulnerabilities_report is not None:
                final_vul_path = json.dumps(vulnerabilities_report, ensure_ascii=False)
            if patches_report is not None:
                final_patch_path = json.dumps(patches_report, ensure_ascii=False)

        # Prevent duplicate rows for the same scan_id
        existing = supabase_admin_client.table("scans").select("id").eq("scan_id", scan_id).execute()
        
        if existing.data:
            response = supabase_admin_client.table("scans").update({
                "vulnerabilities_count": vulnerabilities_count,
                "patches_count": patches_count,
                "file_path_vulnerabilities": final_vul_path,
                "file_path_patches": final_patch_path,
            }).eq("scan_id", scan_id).execute()
        else:
            response = supabase_admin_client.table("scans").insert({
                "user_id": user_id,
                "target_url": target_url,
                "vulnerabilities_count": vulnerabilities_count,
                "patches_count": patches_count,
                "file_path_vulnerabilities": final_vul_path,
                "file_path_patches": final_patch_path,
                "scan_id": scan_id,
            }).execute()
            
        return {"success": True, "data": response.data}
    except Exception as e:
        return {"success": False, "error": str(e)}


def upload_report_to_storage(bucket: str, object_path: str, content_bytes: bytes, content_type: str = "application/json") -> dict:
    """Upload bytes to Supabase Storage using the admin client.

    Returns dict with keys: success, public_url (if available), path, error
    """
    try:
        logger.debug("Uploading to bucket '%s' at path '%s'", bucket, object_path)
        bucket_client = _get_supabase_admin_client().storage.from_(bucket)

        # supabase-py 2.x requires file_options with content-type to avoid 400.
        # upsert=true overwrites if the object already exists (re-saves the same scan).
        file_options = {
            "content-type": content_type,
            "upsert": "true",
        }

        try:
            bucket_client.upload(path=object_path, file=content_bytes, file_options=file_options)
            logger.debug("Upload successful")
        except TypeError:
            # Older SDK versions use positional args without file_options
            bucket_client.upload(object_path, content_bytes)
            logger.debug("Upload successful (legacy SDK path)")

        # Try to obtain a public URL
        public_url = None
        try:
            public_info = bucket_client.get_public_url(object_path)
            if isinstance(public_info, dict):
                public_url = public_info.get("publicURL") or public_info.get("public_url")
            elif isinstance(public_info, str):
                public_url = public_info
        except Exception:
            public_url = None

        # If public_url is not available, attempt signed URL (short-lived)
        if not public_url:
            try:
                signed = bucket_client.create_signed_url(object_path, 60 * 60)
                if isinstance(signed, dict):
                    public_url = signed.get("signedURL") or signed.get("signed_url")
            except Exception:
                public_url = None

        return {"success": True, "path": f"{bucket}/{object_path}", "public_url": public_url}
    except Exception as e:
        error_msg = str(e)
        logger.error("Upload to %s/%s failed: %s", bucket, object_path, error_msg)
        return {"success": False, "error": error_msg}



def download_report_from_storage(public_url_or_path: str) -> dict:
    """Download a stored report. Accepts either a public URL or a stored path like 'bucket/object'.

    Returns dict with keys: success, data (bytes or parsed JSON), error
    """
    if not public_url_or_path or not isinstance(public_url_or_path, str):
        return {"success": False, "error": "Empty or invalid path"}

    try:
        # Strip query parameters that might have been appended for metadata storage
        if "?" in public_url_or_path:
            public_url_or_path = public_url_or_path.split("?")[0]

        # Skip Windows paths (old format like C:\Users\...)
        if public_url_or_path.startswith("C:") or "\\" in public_url_or_path:
            return {"success": False, "error": f"Local file path not supported: {public_url_or_path}"}

        # If it's an HTTP URL, extract bucket and path from Supabase URL
        if public_url_or_path.startswith("http"):
            # URL format: https://...supabase.co/storage/v1/object/public/BUCKET/PATH/TO/OBJECT
            try:
                parts = public_url_or_path.split("/storage/v1/object/public/")
                if len(parts) != 2:
                    raise ValueError("Not a Supabase storage URL")
                rest = parts[1]
                bucket, *obj_parts = rest.split("/", 1)
                obj = obj_parts[0] if obj_parts else ""
                if not obj:
                    raise ValueError("No object path in URL")
            except Exception:
                # Try direct HTTP GET as fallback
                import requests
                try:
                    r = requests.get(public_url_or_path, timeout=10)
                    r.raise_for_status()
                    try:
                        return {"success": True, "data": r.json()}
                    except Exception:
                        return {"success": True, "data": r.content}
                except Exception as e:
                    return {"success": False, "error": f"HTTP GET failed: {str(e)}"}
        else:
            # Expect 'bucket/path/to/object'
            if "/" not in public_url_or_path:
                return {"success": False, "error": "Invalid storage path format"}
            bucket, obj = public_url_or_path.split("/", 1)

        # Use admin client to download (always works for service role)
        bucket_client = _get_supabase_admin_client().storage.from_(bucket)
        try:
            data = bucket_client.download(obj)
            # SDK returns bytes
            if isinstance(data, (bytes, bytearray)):
                try:
                    return {"success": True, "data": json.loads(data.decode("utf-8"))}
                except Exception:
                    return {"success": True, "data": data}
            else:
                # file-like object
                content = data.read() if hasattr(data, 'read') else data
                try:
                    return {"success": True, "data": json.loads(content.decode("utf-8"))}
                except Exception:
                    return {"success": True, "data": content}
        except Exception as e:
            return {"success": False, "error": f"Download failed: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_user_scans(user_id: str) -> dict:
    """Retrieve all scans for a user"""
    try:
        response = _get_supabase_admin_client().table("scans").select("*").eq("user_id", user_id).order("scan_date", desc=True).execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_scan_by_id(scan_id: str) -> dict:
    """Retrieve a specific scan by scan_id"""
    try:
        # Don't use .single() - it causes 406 errors. Just fetch and check the result.
        response = _get_supabase_admin_client().table("scans").select("*").eq("scan_id", scan_id).execute()
        if response.data and len(response.data) > 0:
            return {"success": True, "data": response.data[0]}
        else:
            return {"success": False, "error": f"No scan found with scan_id: {scan_id}"}
    except Exception as e:
        logger.error("get_scan_by_id(%s): %s: %s", scan_id, type(e).__name__, e)
        return {"success": False, "error": str(e)}
