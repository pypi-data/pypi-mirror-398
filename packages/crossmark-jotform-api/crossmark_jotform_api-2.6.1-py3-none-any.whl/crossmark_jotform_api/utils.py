def fix_query_key(key: str) -> str:
    if not key.startswith("q"):
        print(
            f"[JotForm] Filter key '{key}' does not start with 'q', prepending 'q'."
        )
        return "q" + key
    return key