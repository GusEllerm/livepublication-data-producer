import sys

def log_step(message: str):
    print(f"🔹 {message}")

def log_success(message: str):
    print(f"✅ {message}")

def log_warning(message: str):
    print(f"⚠️  {message}")

def log_error(message: str):
    print(f"❌ {message}", file=sys.stderr)

def log_inline(message: str):
    print(f"\r{message}", end="")
    sys.stdout.flush()

def log_block(header: str, lines: list[str]):
    """
    Log a block of messages under a single header.

    Args:
        header (str): The header message for the block.
        lines (list of str): Lines to print beneath the header.
    """
    print(header)
    for line in lines:
        print(line)
