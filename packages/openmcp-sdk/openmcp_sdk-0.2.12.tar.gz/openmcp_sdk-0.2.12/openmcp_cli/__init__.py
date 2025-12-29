#!/usr/bin/env python3
"""OpenMCP CLI - Deploy MCP servers in seconds"""
import os
import sys
import json
import time
from pathlib import Path

API = os.getenv("OPENMCP_API", "https://api.openmcp-free.app")
CREDS = Path.home() / ".openmcp" / "credentials.json"
VERSION = "0.2.12"

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

TEMPLATE_REQUIREMENTS = '''openmcp-sdk
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

Server runs at http://0.0.0.0:8000/mcp

## Deploy

```bash
openmcp deploy
```
'''

TEMPLATE_WIDGET_MAIN = '''import os
from openmcp import OpenMCP

mcp = OpenMCP("{name}", stateless_http=True)


@mcp.widget(
    uri="ui://widget/pizza-map",
    entrypoint="pizzaz.html",
    title="Show Pizza Map",
    invoking="Hand-tossing a map",
    invoked="Served a fresh map",
)
async def pizza_map(pizzaTopping: str) -> dict:
    """Show a map of pizza spots for a given topping"""
    return {{"pizzaTopping": pizzaTopping}}


@mcp.widget(
    uri="ui://widget/pizza-carousel",
    entrypoint="pizzaz-carousel.html",
    title="Show Pizza Carousel",
    invoking="Carousel some spots",
    invoked="Served a fresh carousel",
)
async def pizza_carousel(pizzaTopping: str) -> dict:
    """Show a carousel of pizza spots"""
    return {{"pizzaTopping": pizzaTopping}}


@mcp.widget(
    uri="ui://widget/pizza-albums",
    entrypoint="pizzaz-albums.html",
    title="Show Pizza Album",
    invoking="Hand-tossing an album",
    invoked="Served a fresh album",
)
async def pizza_albums(pizzaTopping: str) -> dict:
    """Show a photo album of pizza spots"""
    return {{"pizzaTopping": pizzaTopping}}


@mcp.widget(
    uri="ui://widget/pizza-list",
    entrypoint="pizzaz-list.html",
    title="Show Pizza List",
    invoking="Hand-tossing a list",
    invoked="Served a fresh list",
)
async def pizza_list(pizzaTopping: str) -> dict:
    """Show a list of pizza spots"""
    return {{"pizzaTopping": pizzaTopping}}


@mcp.widget(
    uri="ui://widget/pizza-shop",
    entrypoint="pizzaz-shop.html",
    title="Open Pizzaz Shop",
    invoking="Opening the shop",
    invoked="Shop opened",
)
async def pizza_shop(pizzaTopping: str) -> dict:
    """Open the Pizzaz shop"""
    return {{"pizzaTopping": pizzaTopping}}


app = mcp.streamable_http_app()

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    print(f"Starting server on 0.0.0.0:{{port}}", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=port)
'''

TEMPLATE_WIDGET_README = '''# {name}

ChatGPT widget app using OpenMCP with build system.

## Widgets

- **counter** — Interactive counter with +/- buttons
- **weather** — Weather card showing city and temperature
- **todo_list** — Todo list with checkboxes

## Setup

```bash
pip install -r requirements.txt
cd assets && npm install && cd ..
```

## Run locally

```bash
python main.py
```

On startup, OpenMCP runs `npm run build` in assets/ to compile widgets.
Server runs at http://0.0.0.0:8000/mcp

## Deploy

```bash
openmcp deploy
```
'''

TEMPLATE_ASSETS_PACKAGE_JSON = '''{
  "name": "pizza-widgets",
  "private": true,
  "type": "module",
  "scripts": {
    "build": "node build.mjs",
    "dev": "vite"
  },
  "dependencies": {
    "@openai/apps-sdk-ui": "^0.2.1",
    "clsx": "^2.1.1",
    "embla-carousel": "^8.0.0",
    "embla-carousel-react": "^8.0.0",
    "framer-motion": "^12.0.0",
    "lucide-react": "^0.500.0",
    "mapbox-gl": "^3.14.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "react-router-dom": "^7.0.0"
  },
  "devDependencies": {
    "@tailwindcss/vite": "^4.0.0",
    "@types/node": "^22.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@vitejs/plugin-react": "^4.3.0",
    "fast-glob": "^3.3.0",
    "tailwindcss": "^4.0.0",
    "typescript": "^5.6.0",
    "vite": "^6.0.0",
    "vite-plugin-singlefile": "^2.0.0"
  }
}
'''

TEMPLATE_ASSETS_BUILD_SCRIPT = '''/**
 * Auto-discovers all HTML files in entrypoints/ and builds each one.
 * Automatically injects global CSS (src/index.css) like OpenAI SDK does.
 * 
 * Mapping: entrypoints/foo.html -> dist/foo.html
 */

import { execSync } from "child_process";
import fg from "fast-glob";
import fs from "fs";
import path from "path";

const ENTRYPOINTS_DIR = "entrypoints";
const DIST_DIR = "dist";
const GLOBAL_CSS = "src/index.css";

const entryFiles = fg.sync(`${ENTRYPOINTS_DIR}/*.html`);

if (entryFiles.length === 0) {
  console.log(`No HTML files in ${ENTRYPOINTS_DIR}/`);
  process.exit(0);
}

console.log(`\\nBuilding ${entryFiles.length} widgets:\\n`);

if (!fs.existsSync(DIST_DIR)) {
  fs.mkdirSync(DIST_DIR);
}

function ensureGlobalCss(htmlPath) {
  const html = fs.readFileSync(htmlPath, "utf-8");
  if (html.includes(GLOBAL_CSS)) return htmlPath;
  
  const cssLink = `  <link rel="stylesheet" href="../${GLOBAL_CSS}">\\n`;
  const injected = html.replace("</head>", cssLink + "</head>");
  
  const tempPath = htmlPath.replace(".html", ".tmp.html");
  fs.writeFileSync(tempPath, injected);
  return tempPath;
}

let success = 0;
let failed = 0;
const tempFiles = [];

for (const entryFile of entryFiles) {
  const basename = path.basename(entryFile, ".html");
  process.stdout.write(`   ${basename}... `);
  
  try {
    const buildFile = ensureGlobalCss(entryFile);
    if (buildFile !== entryFile) tempFiles.push(buildFile);
    
    execSync(`npx vite build`, { 
      stdio: ["pipe", "pipe", "pipe"],
      env: { ...process.env, ENTRY_FILE: buildFile, OUTPUT_NAME: basename }
    });
    console.log("✓");
    success++;
  } catch (err) {
    console.log("✗");
    console.error(`      ${err.stderr?.toString().trim() || err.message}`);
    failed++;
  }
}

for (const tmp of tempFiles) {
  try { fs.unlinkSync(tmp); } catch {}
}

console.log(`\\n${success} built, ${failed} failed -> ${DIST_DIR}/\\n`);
if (failed > 0) process.exit(1);
'''

TEMPLATE_ASSETS_VITE_CONFIG = '''/**
 * Vite config for widget builds.
 * Expects ENTRY_FILE and OUTPUT_NAME env vars.
 */

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { viteSingleFile } from "vite-plugin-singlefile";
import tailwindcss from "@tailwindcss/vite";

const ENTRY_FILE = process.env.ENTRY_FILE;
const OUTPUT_NAME = process.env.OUTPUT_NAME;

if (!ENTRY_FILE || !OUTPUT_NAME) {
  throw new Error("ENTRY_FILE and OUTPUT_NAME env vars required.\\nRun: npm run build");
}

export default defineConfig({
  plugins: [tailwindcss(), react(), viteSingleFile()],
  build: {
    outDir: "dist",
    emptyOutDir: false,
    rollupOptions: {
      input: ENTRY_FILE,
      output: {
        entryFileNames: `${OUTPUT_NAME}.js`,
        assetFileNames: `${OUTPUT_NAME}.[ext]`,
      },
    },
  },
  esbuild: {
    jsx: "automatic",
    jsxImportSource: "react",
  },
});
'''

TEMPLATE_ASSETS_NPMRC = '''registry=https://registry.npmjs.org/
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
                # Skip build artifacts, caches, and venvs (rebuilt on server)
                if item.name.startswith(".") or item.name in ("__pycache__", "node_modules", "dist", ".venv", "venv"):
                    continue
                # Also skip dist inside assets/
                if item.is_dir():
                    def add_filtered(tar, item, arcname):
                        if item.is_file():
                            tar.add(item, arcname=arcname)
                        elif item.is_dir():
                            for sub in item.iterdir():
                                sub_arcname = f"{arcname}/{sub.name}"
                                if sub.name in ("node_modules", "dist", "__pycache__"):
                                    continue
                                add_filtered(tar, sub, sub_arcname)
                    add_filtered(tar, item, item.name)
                else:
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
            print(f"\r  {dim('○')} Session expired, re-authenticating...\n")
            logout(quiet=True)
            api_key = login()
            # Retry deploy with new credentials
            return deploy(project_path, project_id)
        
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


def logout(quiet=False):
    """Clear stored credentials"""
    if CREDS.exists():
        CREDS.unlink()
    if not quiet:
        print(f"\n  {green('✓')} Logged out\n")


def get_templates_dir():
    """Get path to bundled templates directory"""
    import importlib.resources
    return importlib.resources.files("openmcp") / "templates"


def copy_template_dir(src, dst):
    """Copy template directory"""
    import shutil
    shutil.copytree(src, dst)


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
        templates_dir = get_templates_dir()
        chatgpt_template = templates_dir / "chatgpt"
        
        (project_dir / "main.py").write_text(TEMPLATE_WIDGET_MAIN.format(name=name))
        (project_dir / "README.md").write_text(TEMPLATE_WIDGET_README.format(name=name))
        
        # Create assets folder with build system
        assets_dir = project_dir / "assets"
        assets_dir.mkdir()
        (assets_dir / "package.json").write_text(TEMPLATE_ASSETS_PACKAGE_JSON)
        (assets_dir / "vite.config.mts").write_text(TEMPLATE_ASSETS_VITE_CONFIG)
        (assets_dir / "build.mjs").write_text(TEMPLATE_ASSETS_BUILD_SCRIPT)
        (assets_dir / ".npmrc").write_text(TEMPLATE_ASSETS_NPMRC)
        
        template_assets = chatgpt_template / "assets"
        copy_template_dir(template_assets / "entrypoints", assets_dir / "entrypoints")
        copy_template_dir(template_assets / "src", assets_dir / "src")
        
        print(f'> Success! Created {bold(name)} in {dim(str(full_path))}')
    else:
        (project_dir / "main.py").write_text(TEMPLATE_MAIN.format(name=name))
        (project_dir / "README.md").write_text(TEMPLATE_README.format(name=name))
        print(f'> Success! Created {bold(name)} in {dim(str(full_path))}')
    
    print(f"\n  {dim('$')} cd {name}")
    print(f"  {dim('$')} openmcp deploy\n")
    
    (project_dir / "requirements.txt").write_text(TEMPLATE_REQUIREMENTS)
    (project_dir / "settings.json").write_text(get_settings_json(project_id))


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
