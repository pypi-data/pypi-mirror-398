#!/usr/bin/env python3
import os
import tarfile

def validate():
    data_dir = "data"
    archive = "backup.tar.gz"

    # Check for data directory
    if not os.path.isdir(data_dir):
        return False, (
            "Directory 'data' not found in working directory.\n"
            "Ensure your script runs in the same directory as the 'data' folder."
        )

    # Check for backup.tar.gz
    if not os.path.exists(archive):
        return False, "backup.tar.gz not found. Run backup.sh to create it."

    # Verify archive contents
    try:
        with tarfile.open(archive, "r:gz") as tf:
            names = tf.getnames()
    except tarfile.TarError as e:
        return False, f"Failed to read archive: {e}"

    # Ensure data/ is inside the archive
    has_data = any(name == data_dir or name.startswith(f"{data_dir}/") for name in names)
    if not has_data:
        return False, "Archive does not contain the 'data' directory and its files."

    return True, "✅ backup.tar.gz contains the data directory. Good job!"
