Implement `backup.sh` that creates a reproducible compressed backup for a directory named `data` in the current working directory.

Requirements:
- The script must produce a file named `backup.tar.gz` in CWD.
- The archive must contain the `data` directory (preserving its internal path). Example: when extracted, `data/` and its files should be present.
- Use gzip compression and tar.
- The script should be idempotent: rerunning should replace the old archive (not append).
- The validator will verify the archive exists and contains the expected files.

Teaching points: tar options, relative paths, idempotency, simple error handling.
