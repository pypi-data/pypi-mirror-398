# ram_disk.py

Create a RAM disk on macOS. Automatically destroy it as needed.

## Example Usage

### Long-lived RAM disk.

Create a RAM disk at a known path. To remove the RAM disk later do one of:
 - call `unmount_ram_disk()`
 - execute `unmount` in the shell
 - use Finder's `Eject`
 - reboot

*python*

```python
ram_disk_path = mount_ram_disk("1GB", "/Volumes/RAM_DISK")
print(ram_disk_path)  # "/Volumes/RAM_DISK"

# This file is stored in memory.
test_file = ram_disk_path / 'fast_file.txt'
test_file.write_text("This is fast!")

# Optionally destroy the disk.
assert unmount_ram_disk(ram_disk_path)
```

### Temporary RAM disk.

Use `ram_disk` to test a short-lived volume in a context manager.

*python*

```python
with ram_disk("1GB") as ram_disk_path:
    if ram_disk_path:
        print(f"RAM disk created at: {ram_disk_path}")
```

### Slightly-less temporary RAM disk.

Set `unmount_at_exit` to register an `atexit` handler to automatically clean up the disk when the process terminates.

*python*

```python
# Create a RAM disk that will be cleaned up on exit.
ram_disk_path = mount_ram_disk("1GB", unmount_at_exit=True)
```
