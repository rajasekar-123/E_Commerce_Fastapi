import os
import shutil

def run_restructure():
    base_dir = "/app/app"

    moves = [
        ("domain/entities", "models"),
        ("infrastructure/repositories", "repositories"),
        ("application/services", "services"),
        ("presentation/routes", "api/routes"),
        ("core/dependencies.py", "api/dependencies.py"),
        ("infrastructure/llm", "ai/llm"),
        ("infrastructure/embeddings", "ai/embeddings"),
        ("infrastructure/vectorstore", "ai/vectorstore"),
        ("application/ai", "ai/services")
    ]

    # Create target directories
    for target in ["models", "repositories", "services", "api", "api/routes", "ai", "ai/llm", "ai/embeddings", "ai/vectorstore", "ai/services"]:
        os.makedirs(os.path.join(base_dir, target), exist_ok=True)
        init_file = os.path.join(base_dir, target, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                pass

    for src, dst in moves:
        src_path = os.path.join(base_dir, src)
        dst_path = os.path.join(base_dir, dst)
        
        if os.path.isfile(src_path):
            if os.path.exists(src_path) and not os.path.exists(dst_path):
                shutil.move(src_path, dst_path)
        elif os.path.isdir(src_path):
            if os.path.exists(src_path):
                for item in os.listdir(src_path):
                    if item == "__init__.py" and dst != "api/routes": continue # skip some inits to be safe, but let's just move everything
                    s = os.path.join(src_path, item)
                    
                    if "repositories" in src and item.startswith("sqlalchemy_"):
                        d = os.path.join(dst_path, item.replace("sqlalchemy_", ""))
                    else:
                        d = os.path.join(dst_path, item)
                    
                    if os.path.exists(s) and not os.path.exists(d):
                        shutil.move(s, d)

    dirs_to_remove = [
        "domain",
        "infrastructure",
        "application",
        "presentation"
    ]

    for d in dirs_to_remove:
        d_path = os.path.join(base_dir, d)
        if os.path.exists(d_path):
            try:
                shutil.rmtree(d_path, ignore_errors=True)
            except Exception as e:
                print(f"Error removing {d_path}: {e}")

try:
    run_restructure()
except Exception as e:
    print(f"Restructure failed: {e}")
