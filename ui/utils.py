import hashlib

def calculate_hash(data):
    """Calculates the SHA-256 hash of the given data."""
    sha256 = hashlib.sha256()
    sha256.update(data)
    return sha256.hexdigest()

def format_size(size_bytes):
    """Formats the given size in bytes to a human-readable format."""
    if size_bytes == 0:
        return "0 B"
    size_names = ("B", "KB", "MB", "GB", "TB")
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024
        i += 1
    return "{:.2f} {}".format(size_bytes, size_names[i])

# Usage Example
if __name__ == "__main__":
    data = b"Hello, World!"
    hash_value = calculate_hash(data)
    print("SHA-256 Hash:", hash_value)
    
    size = 1024 * 1024 * 3.5
    formatted_size = format_size(size)
    print("Formatted Size:", formatted_size)
