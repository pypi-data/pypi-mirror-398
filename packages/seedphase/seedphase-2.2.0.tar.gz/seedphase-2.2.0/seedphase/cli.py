import os
import sys
import hmac
from getpass import getpass

from seedphase.generator import generate_seed

# 🔐 FIXED PASSWORD
PASSWORD = "1616"

# 📍 Unlock flag location (hidden, per-user)
UNLOCK_FILE = os.path.join(
    os.path.expanduser("~"),
    ".seedphase_unlocked"
)

def run():
    # ✅ If already unlocked, skip password
    if os.path.exists(UNLOCK_FILE):
        generate_seed()
        return

    print("🔐 SeedPhase Protected")
    user_pass = getpass("Enter password: ")

    if not hmac.compare_digest(user_pass, PASSWORD):
        print("❌ Access denied")
        sys.exit(1)

    # 🔓 Unlock permanently
    with open(UNLOCK_FILE, "w") as f:
        f.write("unlocked")

    print("✅ Access granted (saved)")
    generate_seed()
