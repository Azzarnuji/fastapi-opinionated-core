import os


async def html_content(path):
    domains_path = "app/domains"
    print(f"Loading HTML file from: {os.path.join(domains_path, path)}")
    with open(os.path.join(domains_path, path), "r", encoding="utf-8") as f:
        return f.read()