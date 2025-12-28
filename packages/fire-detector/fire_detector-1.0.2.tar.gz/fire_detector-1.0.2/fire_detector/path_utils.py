import os

def resolve_model_path(default_filename=None, explicit_path=None):
    if explicit_path:
        p = explicit_path
        if not os.path.isabs(p):
            p = os.path.abspath(p)
        if os.path.exists(p):
            return p
    base_dir = os.path.dirname(__file__)
    names = [default_filename] if default_filename else []
    for name in names:
        candidates = [
            os.path.join(base_dir, "models", name),
            os.path.join(base_dir, "..", "models", name),
            os.path.join(os.path.dirname(base_dir), "models", name),
            os.path.join(os.getcwd(), "models", name),
        ]
        for c in candidates:
            if os.path.exists(c):
                return os.path.abspath(c)
        cur = base_dir
        for _ in range(4):
            cur = os.path.dirname(cur)
            c = os.path.join(cur, "models", name)
            if os.path.exists(c):
                return os.path.abspath(c)
    return None
