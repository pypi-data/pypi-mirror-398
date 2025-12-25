import json
import os
import sys

# --- version import (universal compatible) ---
try:
    from importlib.metadata import version as get_version, PackageNotFoundError
except ImportError:
    try:
        from importlib.metadata import version as get_version, PackageNotFoundError  # < Py3.8 fallback
    except ImportError:
        get_version = None
        PackageNotFoundError = Exception

# --- optional packaging ---
try:
    from packaging import version as parse_ver
except ImportError:
    parse_ver = None

# --- optional requests import ---
try:
    import requests
except ImportError:
    requests = None


def check_for_update(package_name="crystalwindow"):
    """
    Checks PyPI for updates.
    - Works even if `requests`, `packaging`, or `importlib.metadata` missing.
    - Only prints once after updating to avoid spam.
    """
    cache_file = os.path.join(os.path.expanduser("~"), ".cw_version_cache.json")

    if not get_version:
        print("(⚠️ Version check skipped: importlib.metadata missing)")
        return

    try:
        # === get current version ===
        try:
            current_version = get_version(package_name)
        except PackageNotFoundError:
            print(f"(⚠️ '{package_name}' not installed, skipping version check)")
            return

        # === load last check ===
        last_checked = None
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r") as f:
                    data = json.load(f)
                    last_checked = data.get(package_name)
            except Exception:
                pass

        # === try getting PyPI info ===
        latest_version = None
        if requests:
            try:
                res = requests.get(f"https://pypi.org/pypi/{package_name}/json", timeout=3)
                if res.status_code == 200:
                    latest_version = res.json()["info"]["version"]
            except Exception:
                pass
        else:
            print("(ℹ️ requests not installed, skipping online check)")
            return

        if not latest_version:
            return  # offline or bad fetch

        # === compare ===
        if parse_ver:
            cv = parse_ver.parse(current_version)
            lv = parse_ver.parse(latest_version)
        else:
            cv = current_version
            lv = latest_version

        if cv < lv:
            print(f"\n⚠️ Yo dev! '{package_name}' is outdated ({current_version})")
            print(f"👉 Newest is {latest_version}! Run:")
            print(f"   pip install --upgrade {package_name}")
            print(f"Or peep: https://pypi.org/project/{package_name}/{latest_version}/\n")

        elif cv > lv:
            print(f"🚀 Local version ({current_version}) is newer than PyPI ({latest_version}) — flex on 'em 😎")

        else:
            if last_checked != current_version:
                print(f"✅ Up to date! ver = {current_version}.")
                try:
                    with open(cache_file, "w") as f:
                        json.dump({package_name: current_version}, f)
                except Exception:
                    pass

    except Exception as e:
        print(f"(⚠️ Version check skipped: {e})")
