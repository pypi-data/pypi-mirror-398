#!/usr/bin/env python3
"""OpenMCP CLI - Deploy MCP servers in seconds"""
import os
import sys
import json
import time
from pathlib import Path

API = os.getenv("OPENMCP_API", "https://api.openmcp-free.app")
CREDS = Path.home() / ".openmcp" / "credentials.json"
VERSION = "0.2.5"

TEMPLATE_MAIN = '''import os
from pydantic import Field
from openmcp import OpenMCP

mcp = OpenMCP("{name}", stateless_http=True)


@mcp.tool()
def add(
    a: float = Field(description="The first number to add", examples=[5.0, 10.5]),
    b: float = Field(description="The second number to add", examples=[3.0, 2.5]),
) -> float:
    """Add two numbers together.
    
    This tool performs basic addition of two floating-point numbers.
    Useful for calculations, aggregations, and mathematical operations.
    
    Examples:
        - add(5.0, 3.0) returns 8.0
        - add(10.5, 2.5) returns 13.0
    """
    return a + b


@mcp.tool()
def subtract(
    a: float = Field(description="The number to subtract from (minuend)", examples=[10.0, 15.5]),
    b: float = Field(description="The number to subtract (subtrahend)", examples=[3.0, 5.5]),
) -> float:
    """Subtract one number from another.
    
    Calculates the difference between two numbers by subtracting the second
    from the first. Returns a negative value if b > a.
    
    Examples:
        - subtract(10.0, 3.0) returns 7.0
        - subtract(5.0, 8.0) returns -3.0
    """
    return a - b


app = mcp.streamable_http_app()

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    print(f"Starting server on 0.0.0.0:{{port}}", flush=True)
    uvicorn.run("main:app", host="0.0.0.0", port=port)
'''

TEMPLATE_REQUIREMENTS = '''mcp-core
uvicorn
starlette
'''

def generate_project_id(name):
    """Generate unique project ID: name + random suffix"""
    import random
    import string
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    clean_name = name.lower().replace("_", "-").replace(" ", "-")[:20]
    return f"{clean_name}-{suffix}"


def get_settings_json(project_id):
    return f'''{{"command": "python main.py", "project_id": "{project_id}"}}
'''

TEMPLATE_README = '''# {name}

MCP server with calculator tools.

## Tools

- **add** — Add two numbers together
- **subtract** — Subtract one number from another

## Run locally

```bash
pip install -r requirements.txt
python main.py
```

Server runs at http://localhost:8000/mcp

## Deploy

```bash
openmcp deploy
```
'''

TEMPLATE_WIDGET_MAIN = '''import os
from starlette.middleware.cors import CORSMiddleware
from openmcp import OpenMCP

PIZZA_MAP_HTML = """<!DOCTYPE html>
<html><head><style>
body {{ font-family: system-ui; margin: 0; background: #1a1a2e; color: white; }}
.map {{ width: 100%; height: 250px; background: linear-gradient(45deg, #16213e, #0f3460); 
       display: flex; align-items: center; justify-content: center; flex-direction: column; }}
.topping {{ color: #ff6b6b; font-size: 2em; }}
.pin {{ font-size: 2em; animation: bounce 1s infinite; }}
@keyframes bounce {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-10px); }} }}
</style></head><body>
<div class="map">
  <div class="pin">📍</div>
  <h1>Pizza Map</h1>
  <p>Finding <span class="topping" id="topping">...</span> near you</p>
</div>
<script>
const output = window.openai?.toolOutput;
if (output?.pizzaTopping) document.getElementById('topping').textContent = output.pizzaTopping;
</script>
</body></html>"""

mcp = OpenMCP("{name}", stateless_http=True)


@mcp.widget(
    uri="ui://widget/pizza-map.html",
    html=PIZZA_MAP_HTML,
    title="Show Pizza Map",
    invoking="Finding pizza spots",
    invoked="Map ready",
)
async def pizza_map(pizzaTopping: str) -> dict:
    """Show a map of pizza spots for a given topping"""
    return {{"pizzaTopping": pizzaTopping}}


app = mcp.streamable_http_app()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    print(f"Starting server on 0.0.0.0:{{port}}", flush=True)
    uvicorn.run("main:app", host="0.0.0.0", port=port)
'''

TEMPLATE_WIDGET_README = '''# {name}

ChatGPT widget app using OpenMCP.

## Widget

- **pizza_map** — Interactive map showing pizza spots

## Run locally

```bash
pip install -r requirements.txt
python main.py
```

Server runs at http://localhost:8000/mcp

## Deploy

```bash
openmcp deploy
```
'''

# Colors
def dim(s): return f"\033[2m{s}\033[0m"
def green(s): return f"\033[32m{s}\033[0m"
def cyan(s): return f"\033[36m{s}\033[0m"
def bold(s): return f"\033[1m{s}\033[0m"


def load_credentials():
    if CREDS.exists():
        return json.loads(CREDS.read_text())
    return None


def save_credentials(creds):
    CREDS.parent.mkdir(parents=True, exist_ok=True)
    CREDS.write_text(json.dumps(creds, indent=2))


def spinner(duration=0.5):
    """Simple spinner animation"""
    frames = ["◐", "◓", "◑", "◒"]
    end = time.time() + duration
    i = 0
    while time.time() < end:
        print(f"\r  {frames[i % 4]}", end="", flush=True)
        time.sleep(0.1)
        i += 1
    print("\r  ", end="", flush=True)


def login():
    """Authenticate with OpenMCP"""
    import webbrowser
    from secrets import token_urlsafe
    import httpx
    
    creds = load_credentials()
    if creds and creds.get("api_key"):
        print(f"\n  {green('✓')} Already authenticated\n")
        return creds["api_key"]

    session = token_urlsafe(16)
    url = f"{API}/login?session={session}"
    
    print(f"\n  {bold('☁  OpenMCP')}\n")
    print(f"  Opening browser to authenticate...\n")
    
    webbrowser.open(url)
    print(f"  {dim('If browser does not open, visit:')}")
    print(f"  {dim(url)}\n")
    
    print(f"  Waiting for authentication ", end="", flush=True)
    
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    i = 0
    for _ in range(120):
        print(f"\r  Waiting for authentication {frames[i % 10]}", end="", flush=True)
        time.sleep(1)
        i += 1
        
        r = httpx.get(f"{API}/auth/status", params={"session": session}, timeout=5)
        data = r.json()
        if data.get("status") == "complete":
            api_key = data["api_key"]
            save_credentials({"api_key": api_key})
            print(f"\r  {green('✓')} Authenticated                    \n")
            return api_key
    
    print(f"\r  Timeout. Please try again.        \n")
    sys.exit(1)


def deploy(project_path=".", project_id=None):
    """Deploy an MCP server"""
    import tarfile
    import tempfile
    import httpx
    
    start_total = time.time()
    
    creds = load_credentials()
    if not creds or not creds.get("api_key"):
        api_key = login()
    else:
        api_key = creds["api_key"]
    
    path = Path(project_path).resolve()
    
    if not project_id:
        settings_file = path / "settings.json"
        if settings_file.exists():
            try:
                settings = json.loads(settings_file.read_text())
                project_id = settings.get("project_id")
            except:
                pass
    
    # Fallback to folder name if no project_id found
    if not project_id:
        project_id = path.name.lower().replace("_", "-").replace(" ", "-")
    
    print(f"\n  {bold('☁  Deploying')} {cyan(project_id)}\n")
    
    # Package
    start_pack = time.time()
    print(f"  Packaging...", end="", flush=True)
    
    with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
        with tarfile.open(tmp.name, "w:gz") as tar:
            for item in path.iterdir():
                if item.name.startswith(".") or item.name in ("__pycache__", "node_modules", ".venv", "venv"):
                    continue
                tar.add(item, arcname=item.name)
        tmp_path = tmp.name
    
    size = os.path.getsize(tmp_path) / 1024
    pack_time = time.time() - start_pack
    print(f"\r  Packaged {dim(f'{size:.1f}KB')} {dim(f'({pack_time:.1f}s)')} {green('✓')}")
    
    # Upload
    start_upload = time.time()
    print(f"  Uploading...", end="", flush=True)
    
    try:
        with open(tmp_path, "rb") as f:
            r = httpx.post(
                f"{API}/deploy",
                params={"project_id": project_id},
                files={"file": ("project.tar.gz", f, "application/gzip")},
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=60
            )
        os.unlink(tmp_path)
        
        if r.status_code == 401:
            print(f"\r  {dim('○')} Session expired. Run: {cyan('openmcp login')}\n")
            sys.exit(1)
        
        if r.status_code != 200:
            print(f"\r  {dim('○')} Error: {r.text}\n")
            sys.exit(1)
        
        upload_time = time.time() - start_upload
        print(f"\r  Uploaded {dim(f'({upload_time:.1f}s)')} {green('✓')}         ")
        
        # Success
        data = r.json()
        total_time = time.time() - start_total
        
        print(f"\n  {green('●')} Live at {bold(data['url'])}")
        print(f"  ⚡ {dim(f'Deployed in {total_time:.1f}s')}")
        
        return project_id, api_key, data['url']
        
    except KeyboardInterrupt:
        print(f"\n\n  {dim('Cancelled')}\n")
        sys.exit(0)
    except httpx.TimeoutException:
        print(f"\r  {dim('○')} Timeout. Try again.\n")
        sys.exit(1)
    except Exception as e:
        print(f"\r  {dim('○')} Error: {e}\n")
        sys.exit(1)


def stream_logs(project_id: str, api_key: str, url: str):
    """Stream logs from deployed project in a 4-line scrolling window"""
    import httpx
    
    # Gradient styles: oldest → newest (faded → bright)
    def fade0(s): return f"\033[38;5;239m{s}\033[0m"
    def fade1(s): return f"\033[38;5;244m{s}\033[0m"
    def fade2(s): return f"\033[38;5;250m{s}\033[0m"
    def fade3(s): return f"\033[38;5;255m{s}\033[0m"
    fades = [fade0, fade1, fade2, fade3]
    
    print(f"  {dim('╶───')}")
    print()
    print()
    print()
    print()
    sys.stdout.flush()
    
    lines = ["", "", "", ""]
    pulse = 0
    start_time = time.time()
    log_count = 0
    
    try:
        with httpx.stream(
            "GET",
            f"{API}/logs/{project_id}",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=None
        ) as r:
            if r.status_code != 200:
                print(f"\033[4A\033[2K  {dim('Could not connect')}")
                return
            
            buffer = ""
            for chunk in r.iter_bytes():
                buffer += chunk.decode("utf-8", errors="replace")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip():
                        lines = lines[1:] + [line[:72]]
                        pulse = (pulse + 1) % 4
                        log_count += 1
                        indicators = ["◜", "◝", "◞", "◟"]
                        
                        print(f"\033[4A", end="")
                        for i, l in enumerate(lines):
                            prefix = indicators[pulse] if i == 3 else " "
                            styled = fades[i](l) if l else ""
                            print(f"\033[2K  {dim(prefix)} {styled}")
                        sys.stdout.flush()
    except KeyboardInterrupt:
        elapsed = int(time.time() - start_time)
        import random
        farewells = [
            "Ship it! 🚀", 
            "You're live. Now make history. ✨",
            "Go break the internet. 🔥",
            "You just leveled up. 🎮",
            "You shipped. The world noticed. 🌍",
            "That was fast. You're faster. ⚡",
            "You built this. Now watch it fly. 🚀",
            "You're unstoppable. Keep going. 💫",
            "Your code is live. Own it. 💪",
            "You did that. Legend. ✨",
        ]
        msg = random.choice(farewells)
        print(f"\033[4A", end="")  
        print(f"\033[J", end="")   
        print(f"  {dim(f'{log_count} logs · {elapsed}s')}")
        print(f"  {msg}\n")
    except Exception:
        pass


def logout():
    """Clear stored credentials"""
    if CREDS.exists():
        CREDS.unlink()
    print(f"\n  {green('✓')} Logged out\n")


def init(name="openmcp-app", chatgpt=False):
    """Scaffold a new MCP server project"""
    project_dir = Path.cwd() / name
    full_path = project_dir.resolve()
    
    if project_dir.exists():
        print(f"\n  {dim('Error:')} Directory {bold(name)} already exists\n")
        sys.exit(1)
    
    # Generate unique project ID
    project_id = generate_project_id(name)
    
    print(f"\nOpenMCP CLI {VERSION}")
    print(f"Scaffolding project {green('✓')}")
    
    project_dir.mkdir()
    
    if chatgpt:
        (project_dir / "main.py").write_text(TEMPLATE_WIDGET_MAIN.format(name=name))
        (project_dir / "README.md").write_text(TEMPLATE_WIDGET_README.format(name=name))
    else:
        (project_dir / "main.py").write_text(TEMPLATE_MAIN.format(name=name))
        (project_dir / "README.md").write_text(TEMPLATE_README.format(name=name))
    
    (project_dir / "requirements.txt").write_text(TEMPLATE_REQUIREMENTS)
    (project_dir / "settings.json").write_text(get_settings_json(project_id))
    
    print(f'> Success! Initialized {bold(name)} app in {dim(str(full_path))}')
    print(f"\nTo deploy:")
    print(f"  {dim('$')} cd {name}")
    print(f"  {dim('$')} openmcp deploy\n")


def main():
    args = sys.argv[1:]
    
    if not args or args[0] in ("-h", "--help", "help"):
        print(f"""
  {bold('☁  OpenMCP')} {dim('— Deploy MCP servers in seconds')}

  {bold('Commands')}
    {cyan('init')} [name]              Create a new MCP server project
    {cyan('init')} --chatgpt [name]    Create a ChatGPT widget app
    {cyan('deploy')} [path] [id]        Deploy current directory
    {cyan('deploy')} --logs [path] [id] Deploy and stream logs
    {cyan('login')}                    Authenticate with OpenMCP
    {cyan('logout')}                   Clear stored credentials

  {bold('Quick Start')}
    openmcp init
    cd openmcp-app
    openmcp deploy
""")
        return
    
    cmd = args[0]
    
    if cmd == "init":
        init_args = args[1:]
        chatgpt = "--chatgpt" in init_args
        remaining = [a for a in init_args if not a.startswith("--")]
        name = remaining[0] if remaining else "openmcp-app"
        init(name, chatgpt=chatgpt)
    elif cmd == "login":
        login()
    elif cmd == "deploy":
        # Parse --logs flag
        show_logs = "--logs" in args
        remaining = [a for a in args[1:] if a != "--logs"]
        
        path = remaining[0] if len(remaining) > 0 else "."
        project_id = remaining[1] if len(remaining) > 1 else None
        
        result = deploy(path, project_id)
        
        if show_logs and result:
            proj_id, api_key, url = result
            stream_logs(proj_id, api_key, url)
    elif cmd == "logout":
        logout()
    else:
        print(f"\n  Unknown command: {cmd}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
