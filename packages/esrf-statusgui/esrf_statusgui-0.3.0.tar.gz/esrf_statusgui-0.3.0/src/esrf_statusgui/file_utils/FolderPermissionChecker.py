import grp
import os
import pwd
import stat
from typing import Optional

# Windows-specific imports
if os.name == "nt":
    import ntsecuritycon
    import win32security


class FolderPermissionChecker:
    def __init__(self, folder_path: str):
        self.folder_path = folder_path
        self.is_unix = os.name == "posix"
        self.is_windows = os.name == "nt"

    def is_admin_owned(self) -> bool:
        """Check if folder is owned by root (Unix) or Administrators (Windows)."""
        if self.is_unix:
            st = os.stat(self.folder_path)
            return st.st_uid == 0  # Root UID = 0
        elif self.is_windows:
            sd = win32security.GetFileSecurity(
                self.folder_path, win32security.OWNER_SECURITY_INFORMATION
            )
            admin_sid = win32security.CreateWellKnownSid(
                win32security.WinBuiltinAdministratorsSid
            )
            return sd.GetSecurityDescriptorOwner() == admin_sid
        return False

    def is_backup_owned(self) -> bool:
        """Check if folder is owned by root (Unix) or Administrators (Windows)."""
        if self.is_unix:
            st = os.stat(self.folder_path)
            return st.st_uid == 34

    def is_readonly(self) -> bool:
        """Check if folder has no write permissions for any user/group."""
        if self.is_unix:
            mode = os.stat(self.folder_path).st_mode
            return (
                (mode & stat.S_IRGRP)  # r for group
                and (mode & stat.S_IXGRP)  # x for group
                and not (mode & stat.S_IWGRP)  # no w for group
                and not (mode & stat.S_IRWXO)  # no permissions for others
            )
        elif self.is_windows:
            sd = win32security.GetFileSecurity(
                self.folder_path, win32security.DACL_SECURITY_INFORMATION
            )
            dacl = sd.GetSecurityDescriptorDacl()
            if dacl is None:  # No DACL = full access
                return False
            for ace_index in range(dacl.GetAceCount()):
                ace = dacl.GetAce(ace_index)
                if ace[1] & ntsecuritycon.FILE_GENERIC_WRITE:
                    return False
            return True
        return False

    def checkOwnedByRoot(
        self, expected_owner: Optional[str] = None, expected_group: Optional[str] = None
    ) -> bool:
        """
        Full permission check with optional owner/group validation.
        Args:
            expected_owner: Check against a specific owner (e.g., 'root' or 'Administrators')
            expected_group: Check against a specific group (Unix only)
        Returns:
            bool: True if all conditions are met
        """
        if not os.path.exists(self.folder_path):
            raise FileNotFoundError(f"Folder not found: {self.folder_path}")

        if self.is_backup_owned():
            return True

        # 1. Check admin ownership
        if not self.is_admin_owned():
            return False

        # 2. Check read-only status
        if not self.is_readonly():
            return False

        # 3. (Unix-only) Check group if specified
        if self.is_unix and expected_group:
            st = os.stat(self.folder_path)
            group_name = grp.getgrgid(st.st_gid).gr_name
            if group_name != expected_group:
                return False

        # 4. (Optional) Custom owner name check
        if expected_owner:
            if self.is_unix:
                st = os.stat(self.folder_path)
                owner_name = pwd.getpwuid(st.st_uid).pw_name
            else:  # Windows
                sd = win32security.GetFileSecurity(
                    self.folder_path, win32security.OWNER_SECURITY_INFORMATION
                )
                owner_sid = sd.GetSecurityDescriptorOwner()
                owner_name, _, _ = win32security.LookupAccountSid(None, owner_sid)
            if owner_name != expected_owner:
                return False

        return True

    def get_details(self) -> dict:
        """Return detailed permission information."""
        details = {
            "path": self.folder_path,
            "exists": os.path.exists(self.folder_path),
            "is_admin_owned": None,
            "is_readonly": None,
            "owner": None,
            "group": None,
            "permissions": None,
        }

        if not details["exists"]:
            return details

        try:
            details["is_admin_owned"] = self.is_admin_owned()
            details["is_readonly"] = self.is_readonly()

            if self.is_unix:
                st = os.stat(self.folder_path)
                details["owner"] = pwd.getpwuid(st.st_uid).pw_name
                details["group"] = grp.getgrgid(st.st_gid).gr_name
                details["permissions"] = oct(st.st_mode & 0o777)
            else:
                sd = win32security.GetFileSecurity(
                    self.folder_path, win32security.OWNER_SECURITY_INFORMATION
                )
                owner_sid = sd.GetSecurityDescriptorOwner()
                details["owner"] = win32security.LookupAccountSid(None, owner_sid)[0]
                details["group"] = (
                    "N/A (Windows)"  # Primary group isn't commonly checked
                )
                details["permissions"] = "ACL-based (complex)"
        except Exception as e:
            details["error"] = str(e)

        return details

    def checkWritePermission(self):
        """
        Check if we have write permissions in a specified folder.

        Args:
            folder_path (str): Path to the folder to test

        Returns:
            bool: True if writing is allowed, False if permission denied
        """
        try:
            # Create a temporary test file name
            test_file = os.path.join(self.folder_path, f"write_test_{os.getpid()}.tmp")

            # Try to write to the file
            with open(test_file, "w") as f:
                f.write("This is a test for write permissions.")

            # Clean up - remove the test file if it was created
            if os.path.exists(test_file):
                os.remove(test_file)

            return True

        except PermissionError:
            return False
        except OSError as e:
            # Handle other OS-related errors (like folder doesn't exist)
            print(f"Error: {e}")
            return False
        except Exception as e:
            # Catch any other unexpected errors
            print(f"Unexpected error: {e}")
            return False

    def printDetails(self):
        """Print detailed permission information."""
        details = self.get_details()
        print(
            f"""
        Folder: {details["path"]}
        Exists: {details["exists"]}
        Owner: {details["owner"]}
        Group: {details["group"]}
        Permissions: {details["permissions"]}
        Is admin owned: {details["is_admin_owned"]}
        Is read-only: {details["is_readonly"]}
        """
        )


if __name__ == "__main__":
    checker = FolderPermissionChecker("/usr/local")
    checker.printDetails()
