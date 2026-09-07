import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen


# ============================================================
# APP CONFIGURATION
# ============================================================

APP_TITLE = "HPPM"
APP_FOLDER_NAME = "HPPM"

_HERE = Path(__file__).resolve().parent

if _HERE.name == APP_FOLDER_NAME:
    # Permanent installation:
    # .../HPPM/HPPM.py
    #
    # SOURCE_DIR remains the directory containing:
    # Projects/
    # HPPM/
    SOURCE_DIR = _HERE.parent
    APP_DIR = _HERE
else:
    # First-run/original script
    SOURCE_DIR = _HERE
    APP_DIR = SOURCE_DIR / APP_FOLDER_NAME

PROJECTS_DIR = SOURCE_DIR / "Projects"

DATA_DIR = APP_DIR / ".ppm"
CONFIG_FILE = DATA_DIR / "config.json"
PROJECTS_FILE = DATA_DIR / "projects.json"

PERMANENT_SCRIPT = APP_DIR / "HPPM.py"
BAT_FILE = SOURCE_DIR / "HPPM.bat"

HOST = "127.0.0.1"

SESSION_TOKEN = uuid.uuid4().hex

KERNEL_PREFIX = "ppm-"

CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0

PROJECT_NAME_RE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$"
)

# name -> {
#     "proc": subprocess.Popen,
#     "port": int,
#     "log": file
# }
RUNNING = {}


# ============================================================
# WEB UI
# ============================================================

HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">

<title>HPPM(Hemin Python Project Manager)</title>

<link
    href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
    rel="stylesheet"
>

<link
    href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css"
    rel="stylesheet"
>

<link
    href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap"
    rel="stylesheet"
>

<style>

:root{
    --paper:#F7F6F2;
    --surface:#FFFFFF;
    --ink:#20242A;
    --muted:#6C7580;
    --line:#E4E1D8;

    --primary:#1F4E5F;
    --primary-ink:#FFFFFF;

    --good:#3C7A5A;
    --good-bg:#E9F2EC;

    --warn:#93601C;
    --warn-bg:#FBF0DE;

    --danger:#A6402B;
    --danger-bg:#FBEAE6;
}

*{
    box-sizing:border-box;
}

body{
    background:var(--paper);
    color:var(--ink);
    font-family:'IBM Plex Sans',system-ui,sans-serif;
}

.app{
    max-width:760px;
    margin:auto;
    padding:40px 20px 60px;
}

.mono{
    font-family:'IBM Plex Mono',ui-monospace,Menlo,monospace;
    font-size:.82rem;
}

.muted{
    color:var(--muted);
}

.mark{
    width:30px;
    height:30px;
    border-radius:8px;
    background:var(--primary);
    color:#fff;

    display:inline-flex;
    align-items:center;
    justify-content:center;

    font-family:'IBM Plex Mono',monospace;
    font-weight:500;
    font-size:.82rem;

    margin-right:10px;
}

.wordmark{
    font-weight:600;
    font-size:1.05rem;
    letter-spacing:-.01em;
}

.panel{
    background:var(--surface);
    border:1px solid var(--line);
    border-radius:14px;
    overflow:hidden;
}

.btn{
    border-radius:8px;
    font-weight:500;
}

.btn-primary{
    background:var(--primary);
    border-color:var(--primary);
}

.btn-primary:hover{
    background:#173d4a;
    border-color:#173d4a;
}

.btn-outline-secondary{
    color:var(--ink);
    border-color:var(--line);
}

.btn-outline-secondary:hover{
    background:var(--paper);
    color:var(--ink);
    border-color:var(--line);
}

.btn-outline-danger{
    border-color:var(--line);
    color:var(--danger);
}

.btn-outline-danger:hover{
    background:var(--danger-bg);
    color:var(--danger);
    border-color:var(--danger);
}

.pill{
    display:inline-flex;
    align-items:center;
    gap:6px;

    padding:3px 10px;

    border-radius:999px;

    font-size:.78rem;
    font-weight:500;

    white-space:nowrap;
}

.pill-ready{
    background:var(--good-bg);
    color:var(--good);
}

.pill-running{
    background:var(--good-bg);
    color:var(--good);
}

.pill-warn{
    background:var(--warn-bg);
    color:var(--warn);
}

.dot{
    width:6px;
    height:6px;
    border-radius:50%;
    background:currentColor;
    display:inline-block;
}


/* ============================================================
   PROJECT ROW
   ============================================================ */

.row-item{
    border-top:1px solid var(--line);
    padding:16px 4px;
}

.row-item:first-child{
    border-top:0;
}


/*
   First line:
       Project name     Status        Open Delete

   Second line:
       Project path
*/

.project-top{
    display:flex;
    align-items:center;
    justify-content:space-between;

    gap:12px;
    min-width:0;
}

.project-main{
    min-width:0;
    flex:1 1 auto;
}

.project-title{
    display:flex;
    align-items:center;
    gap:8px;

    min-width:0;
}

.proj-name{
    font-weight:600;

    /*
       Project names are limited by PROJECT_NAME_RE,
       but keep this safe anyway.
    */
    overflow-wrap:anywhere;
    word-break:break-word;
}

.project-actions{
    display:flex;
    align-items:center;
    gap:8px;

    flex:0 0 auto;
}

.project-path{
    margin-top:7px;

    line-height:1.45;

    /*
       IMPORTANT:
       Long Windows paths are allowed to wrap.
       This prevents the path from pushing buttons
       outside the project row.
    */
    overflow-wrap:anywhere;
    word-break:break-word;

    white-space:normal;
}


/* ============================================================
   SETUP
   ============================================================ */

.setup-path{
    background:var(--paper);
    border:1px solid var(--line);

    border-radius:10px;

    padding:14px 16px;

    overflow-wrap:anywhere;
    word-break:break-word;
}

a.muted{
    text-decoration:underline;
    text-decoration-color:var(--line);
}

a.muted:hover{
    color:var(--ink);
    text-decoration-color:var(--ink);
}

.empty{
    border:1px dashed var(--line);
    border-radius:14px;

    padding:48px 24px;

    text-align:center;
}


/* ============================================================
   BUSY BAR
   ============================================================ */

#busybar{
    position:fixed;

    top:0;
    left:0;

    height:3px;
    width:100%;

    opacity:0;

    transition:opacity .15s;

    z-index:2000;

    background:
        linear-gradient(
            90deg,
            transparent,
            var(--primary),
            transparent
        );

    background-size:60% 100%;

    animation:slide 1.1s linear infinite;
}

body.busy #busybar{
    opacity:1;
}

@keyframes slide{
    0%{
        background-position:-60% 0;
    }

    100%{
        background-position:160% 0;
    }
}

body.busy .btn{
    opacity:.6;
    pointer-events:none;
    cursor:wait;
}


/* ============================================================
   MOBILE
   ============================================================ */

@media (max-width:700px){

    .app{
        padding:24px 12px 48px;
    }

    .project-top{
        align-items:flex-start;
    }

    .project-actions{
        flex:0 0 auto;
    }

    .project-actions .btn-primary{
        padding-left:10px;
        padding-right:10px;
    }

    .project-path{
        font-size:.78rem;
    }
}

</style>
</head>


<body>

<div id="busybar"></div>

<div class="app">

<nav class="d-flex justify-content-between align-items-center mb-4">

    <div class="d-flex align-items-center">

        <span class="mark">{H}</span>

        <span class="wordmark">
            HPPM
        </span>

    </div>


    <div class="d-flex gap-2">

        <button
            class="btn btn-outline-secondary btn-sm"
            onclick="cleanupKernels()"
            title="Stop leftover Jupyter kernels and servers from deleted projects"
        >
            <i class="bi bi-broom me-1"></i>
            Clean Jupyter
        </button>


        <button
            class="btn btn-outline-secondary btn-sm"
            onclick="syncProjects()"
            title="Remove entries for projects whose folder no longer exists"
        >
            <i class="bi bi-arrow-repeat me-1"></i>
            Sync
        </button>

    </div>

</nav>


<div id="app"></div>


<div class="text-center small muted mt-4">

    Created, designed & maintained by

    <a
        href="https://github.com/heminazizi"
        target="_blank"
        rel="noopener"
        class="muted"
    >
        Hemin Azizi
    </a>

    ,developed with AI assistance

</div>

</div>


<div class="toast-container position-fixed bottom-0 end-0 p-3">

    <div id="toast" class="toast">

        <div class="toast-body"></div>

    </div>

</div>


<script>

const $ = s => document.querySelector(s);

const TOKEN = "__PPM_TOKEN__";

let state = null;

let busyCount = 0;


function setBusy(delta){

    busyCount = Math.max(
        0,
        busyCount + delta
    );

    document.body.classList.toggle(
        "busy",
        busyCount > 0
    );
}


async function api(url, options = {}){

    setBusy(1);

    try{

        const r = await fetch(
            url,
            {
                headers:{
                    "Content-Type":"application/json",
                    "X-PPM-Token":TOKEN
                },

                ...options
            }
        );


        const d = await r.json().catch(
            () => ({
                ok:false,
                error:"Unexpected server response."
            })
        );


        if(!r.ok || d.ok === false){

            throw new Error(
                d.error || "Something went wrong."
            );

        }


        return d;

    }

    finally{

        setBusy(-1);

    }

}


function esc(s){

    return String(s).replace(
        /[&<>"']/g,

        c => ({
            "&":"&amp;",
            "<":"&lt;",
            ">":"&gt;",
            '"':"&quot;",
            "'":"&#39;"
        }[c])
    );

}


function toast(msg, good = false){

    const t = $("#toast");

    t.querySelector(".toast-body").textContent = msg;

    t.className =
        "toast " +
        (good ? "text-bg-success" : "text-bg-danger");


    bootstrap.Toast.getOrCreateInstance(
        t,
        {
            delay:5000
        }
    ).show();

}


/* ============================================================
   RENDER
   ============================================================ */

function render(){

    const a = $("#app");


    /* --------------------------------------------------------
       SETUP SCREEN
       -------------------------------------------------------- */

    if(!state.setup){

        a.innerHTML = `

        <div class="panel p-4 p-md-5">

            <h2 class="fw-semibold mb-2">
                Set up your workspace
            </h2>

            <p class="muted mb-4">

                This creates a permanent copy of the manager,
                a Projects folder, and a desktop launcher.
                Nothing else on your system is touched.

            </p>


            <div class="setup-path mb-2 mono">
                ${esc(state.app_dir)}
            </div>


            <div class="setup-path mb-2 mono">
                ${esc(state.projects_dir)}
            </div>


            <div class="setup-path mb-4 mono">
                ${esc(state.bat_file)}
            </div>


            <p class="small muted mb-4">

                Once setup finishes, use the launcher above
                to open the manager going forward.
                This original file can be deleted.

            </p>


            <button
                id="setupBtn"
                class="btn btn-primary"
                onclick="setup()"
            >
                Set up
            </button>

        </div>

        `;

        return;
    }


    const ps = state.projects || [];


    /* --------------------------------------------------------
       PROJECT LIST
       -------------------------------------------------------- */

    a.innerHTML = `

    <div class="panel p-4 mb-4">

        <div
            class="d-flex flex-wrap justify-content-between
                   align-items-start gap-3 mb-3"
        >

            <div>

                <h2 class="fw-semibold mb-1">
                    Your projects
                </h2>

                <div class="muted small">

                    ${ps.length}

                    project${ps.length === 1 ? "" : "s"}

                </div>

            </div>


            <button
                class="btn btn-primary"
                onclick="createProject()"
            >

                <i class="bi bi-plus-lg me-1"></i>

                New project

            </button>

        </div>


        <div
            class="row g-3 small pt-2"
            style="border-top:1px solid var(--line)"
        >

            <div class="col-md-6">

                <span class="muted">
                    Projects folder
                </span>

                <div class="mono mt-1"
                     style="overflow-wrap:anywhere">
                    ${esc(state.projects_dir)}
                </div>

            </div>


            <div class="col-md-3">

                <span class="muted">
                    Python
                </span>

                <div class="mt-1">
                    ${esc(state.python_version)}
                </div>

            </div>


            <div class="col-md-3">

                <span class="muted">
                    JupyterLab
                </span>

                <div class="mt-1">
                    ${esc(state.jupyterlab_version || "Installed")}
                </div>

            </div>

        </div>

    </div>


    ${
        ps.length

        ?

        `<div class="panel p-4">

            ${ps.map(p => {

                const pill =
                    p.running

                    ?

                    `<span class="pill pill-running">
                        <span class="dot"></span>
                        Running
                    </span>`

                    :

                    p.status === "Ready"

                    ?

                    `<span class="pill pill-ready">
                        <span class="dot"></span>
                        Ready
                    </span>`

                    :

                    `<span class="pill pill-warn">
                        <span class="dot"></span>
                        Needs repair
                    </span>`;


                return `

                <div class="row-item">


                    <!-- FIRST LINE:
                         NAME + STATUS + BUTTONS
                    -->

                    <div class="project-top">


                        <div class="project-main">

                            <div class="project-title">

                                <span class="proj-name">
                                    ${esc(p.name)}
                                </span>

                                ${pill}

                            </div>

                        </div>


                        <div class="project-actions">


                            <button
                                class="btn btn-primary btn-sm"
                                onclick="openProject('${esc(p.name)}')"
                            >

                                <i class="bi bi-box-arrow-up-right me-1"></i>

                                Open

                            </button>


                            <button
                                class="btn btn-outline-danger
                                       btn-icon btn-sm"

                                onclick="deleteProject('${esc(p.name)}')"

                                title="Delete project"
                            >

                                <i class="bi bi-trash3"></i>

                            </button>


                        </div>


                    </div>


                    <!-- SECOND LINE:
                         PATH
                    -->

                    <div class="project-path mono muted">

                        ${esc(p.path)}

                    </div>


                </div>

                `;

            }).join("")}

        </div>`

        :

        `<div class="empty">

            <h5 class="fw-semibold mb-2">
                No projects yet
            </h5>

            <p class="muted mb-3">
                Create your first project to get started.
            </p>

            <button
                class="btn btn-primary"
                onclick="createProject()"
            >
                Create new project
            </button>

        </div>`
    }

    `;

}


/* ============================================================
   LOAD STATE
   ============================================================ */

async function load(){

    try{

        state = await api("/api/state");

        render();

    }

    catch(e){

        toast(e.message);

    }

}


/* ============================================================
   SETUP
   ============================================================ */

async function setup(){

    const b = $("#setupBtn");

    b.disabled = true;

    b.innerHTML =
        '<span class="spinner-border spinner-border-sm me-2"></span>' +
        'Setting up...';


    try{

        await api(
            "/api/setup",
            {
                method:"POST"
            }
        );


        $("#app").innerHTML = `

        <div class="panel p-4 p-md-5">

            <h2 class="fw-semibold mb-2">
                Setup complete
            </h2>


            <p class="muted mb-4">

                Close this window now, then open the manager
                from the launcher that was just created —
                that's the copy you'll use from now on:

            </p>


            <div class="setup-path mono mb-4">

                ${esc(state.bat_file)}

            </div>


            <p class="small muted mb-0">

                A shortcut to that file on your Desktop or
                Start Menu makes this a one-click launch next time.
                This original file is no longer needed and can be deleted.

            </p>

        </div>

        `;


        toast(
            "Setup completed successfully.",
            true
        );

    }

    catch(e){

        toast(e.message);

        b.disabled = false;

        b.textContent = "Set up";

    }

}


/* ============================================================
   CREATE PROJECT
   ============================================================ */

async function createProject(){

    const name = prompt(
        "Project name (letters, numbers, - and _ only):"
    );


    if(name === null){
        return;
    }


    try{

        await api(
            "/api/projects",
            {
                method:"POST",

                body:JSON.stringify({
                    name:name.trim()
                })
            }
        );


        await load();


        toast(
            "Project created successfully.",
            true
        );

    }

    catch(e){

        toast(e.message);

    }

}


/* ============================================================
   OPEN PROJECT
   ============================================================ */

async function openProject(name){

    try{

        await api(
            "/api/projects/open",
            {
                method:"POST",

                body:JSON.stringify({
                    name:name
                })
            }
        );


        toast(
            "JupyterLab is starting...",
            true
        );

    }

    catch(e){

        toast(e.message);

    }

}


/* ============================================================
   DELETE PROJECT
   ============================================================ */

async function deleteProject(name){

    const typed = prompt(
        `To permanently delete "${name}", type the project name exactly:`
    );


    if(typed === null){
        return;
    }


    if(typed !== name){

        toast(
            "The project name did not match. Nothing was deleted."
        );

        return;
    }


    try{

        await api(
            "/api/projects/delete",
            {
                method:"POST",

                body:JSON.stringify({
                    name:name,
                    confirm:typed
                })
            }
        );


        await load();


        toast(
            "Project deleted successfully.",
            true
        );

    }

    catch(e){

        toast(e.message);

    }

}


/* ============================================================
   SYNC
   ============================================================ */

async function syncProjects(){

    try{

        const d = await api(
            "/api/sync",
            {
                method:"POST"
            }
        );


        await load();


        toast(
            d.message,
            true
        );

    }

    catch(e){

        toast(e.message);

    }

}


/* ============================================================
   CLEANUP JUPYTER
   ============================================================ */

async function cleanupKernels(){

    try{

        const d = await api(
            "/api/kernels/cleanup",
            {
                method:"POST"
            }
        );


        toast(
            d.message,
            true
        );


        await load();

    }

    catch(e){

        toast(e.message);

    }

}


load();

</script>


<script
    src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js">
</script>

</body>
</html>
"""


# ============================================================
# JSON HELPERS
# ============================================================

def load_json(path, default):
    try:
        return json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    except Exception:
        return default


def save_json(path, data):

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    tmp = path.with_suffix(
        path.suffix + ".tmp"
    )

    tmp.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    tmp.replace(path)


# ============================================================
# CONFIG / REGISTRY
# ============================================================

def get_config():

    return load_json(
        CONFIG_FILE,
        {
            "version":3,
            "setup_complete":False
        }
    )


def get_registry():

    return load_json(
        PROJECTS_FILE,
        {
            "version":3,
            "projects":{}
        }
    )


def ensure_dirs():

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    PROJECTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


# ============================================================
# PYTHON / VENV
# ============================================================

def venv_python(venv):

    return venv / (
        "Scripts/python.exe"
        if os.name == "nt"
        else "bin/python"
    )


def run_cmd(args, timeout=900):

    return subprocess.run(
        [str(x) for x in args],

        stdout=subprocess.PIPE,

        stderr=subprocess.STDOUT,

        text=True,

        encoding="utf-8",

        errors="replace",

        timeout=timeout,

        creationflags=CREATE_NO_WINDOW
    )


# ============================================================
# JUPYTERLAB
# ============================================================

def jupyterlab_version():

    try:

        r = run_cmd(
            [
                sys.executable,
                "-m",
                "jupyter",
                "lab",
                "--version"
            ],
            30
        )


        if (
            r.returncode == 0
            and r.stdout.strip()
        ):

            return r.stdout.strip().splitlines()[-1]


    except Exception:
        pass


    return None


def ensure_jupyterlab():

    if jupyterlab_version():
        return


    try:

        run_cmd(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--upgrade",
                "pip"
            ],
            300
        )

    except Exception:
        pass


    r = run_cmd(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "jupyterlab"
        ],
        1800
    )


    if (
        r.returncode != 0
        and re.search(
            r"permission denied|access is denied|winerror\s*5",
            r.stdout or "",
            re.I
        )
    ):

        r = run_cmd(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--user",
                "jupyterlab"
            ],
            1800
        )


    if r.returncode != 0:

        detail = (
            r.stdout or ""
        ).strip().splitlines()


        detail = (
            "\n".join(detail[-8:])
            if detail
            else
            "No output was returned by pip."
        )


        raise RuntimeError(
            "JupyterLab could not be installed. "
            "This is usually caused by an outdated pip, "
            "a firewall/antivirus blocking Python's access "
            "to PyPI, or missing permissions on this Python "
            "installation.\n\n"
            "Details from pip:\n"
            + detail
        )


# ============================================================
# PROJECT VALIDATION
# ============================================================

def valid_name(name):

    return (
        bool(
            PROJECT_NAME_RE.fullmatch(
                name or ""
            )
        )
        and name.lower()
        not in {
            "con",
            "prn",
            "aux",
            "nul"
        }
    )


def project_path(name):

    if not valid_name(name):

        raise ValueError(
            "Invalid project name."
        )


    root = PROJECTS_DIR.resolve()

    p = (
        PROJECTS_DIR / name
    ).resolve()


    if p.parent != root:

        raise ValueError(
            "Invalid project location."
        )


    return p


# ============================================================
# KERNEL MANAGEMENT
# ============================================================

def kernel_id_for_project(name):

    """
    Generate a deterministic kernel ID from the project name.

    Example:

        MyProject
        ->
        ppm-myproject

        Test_Project
        ->
        ppm-test_project

    This makes it possible to identify which kernel
    belongs to which project later.
    """

    return (
        KERNEL_PREFIX
        + name.lower()
    )


def kernel_dir(path):

    # Jupyter discovers user-installed kernels reliably on Windows.
    # The project kernel itself is registered with the project's Python,
    # but stored in Jupyter's normal per-user kernels directory.
    # This is more robust than hiding kernels behind a venv-local search path.
    return Path(path) / ".jupyter" / "kernels"


def register_kernel(vp, name, path=None):

    vp = Path(vp).resolve()
    kid = kernel_id_for_project(name)

    if not vp.exists():
        raise RuntimeError(
            "The project's virtual-environment Python was not found.\n\n"
            + str(vp)
        )

    # IMPORTANT: install the kernelspec through the project's Python, but use
    # Jupyter's standard per-user kernels directory. This makes it visible to
    # the JupyterLab server even when JupyterLab itself runs under the manager
    # Python. The kernel process still uses THIS project's Python executable.
    r = run_cmd(
        [
            str(vp),
            "-m",
            "ipykernel",
            "install",
            "--user",
            "--name",
            kid,
            "--display-name",
            f"Python ({name})"
        ],
        180
    )

    if r.returncode != 0:
        detail = (r.stdout or "").strip().splitlines()
        raise RuntimeError(
            "The project environment was created, but its Jupyter kernel "
            "could not be registered.\n\n"
            + ("\n".join(detail[-10:]) if detail else "No output was returned.")
        )

    return kid


def list_kernels():

    try:

        r = run_cmd(
            [
                sys.executable,
                "-m",
                "jupyter",
                "kernelspec",
                "list",
                "--json"
            ],
            30
        )


        if r.returncode != 0:
            return {}


        return json.loads(
            r.stdout
        ).get(
            "kernelspecs",
            {}
        )


    except Exception:

        return {}


def remove_kernel(kid):

    if not kid:
        return


    try:

        r = run_cmd(
            [
                sys.executable,
                "-m",
                "jupyter",
                "kernelspec",
                "remove",
                kid,
                "-f"
            ],
            30
        )


        if r.returncode != 0:

            spec = list_kernels().get(
                kid,
                {}
            )


            p = Path(
                spec.get(
                    "resource_dir",
                    ""
                )
            )


            if p.exists():

                shutil.rmtree(
                    p,
                    ignore_errors=True
                )


    except Exception:
        pass


# ============================================================
# RUNNING JUPYTER SERVERS
# ============================================================

def stop_tracked(name):

    r = RUNNING.pop(
        name,
        None
    )


    if (
        not r
        or r.get("proc") is None
        or r["proc"].poll() is not None
    ):

        return


    try:

        if os.name == "nt":

            subprocess.run(
                [
                    "taskkill",
                    "/PID",
                    str(r["proc"].pid),
                    "/T",
                    "/F"
                ],

                stdout=subprocess.DEVNULL,

                stderr=subprocess.DEVNULL,

                timeout=10,

                creationflags=CREATE_NO_WINDOW
            )

        else:

            r["proc"].terminate()


    except Exception:
        pass


    try:

        if r.get("log"):
            r["log"].close()

    except Exception:
        pass


def _wait_and_open(port, deadline):

    url = (
        f"http://{HOST}:{port}/lab"
    )


    while time.time() < deadline:

        try:

            urlopen(
                f"http://{HOST}:{port}/",
                timeout=1.5
            )

            break


        except URLError:

            time.sleep(.4)


        except Exception:

            break


    webbrowser.open(url)


# ============================================================
# START JUPYTER
# ============================================================

def _force_project_kernel_in_notebooks(path, kernel_id, display_name):
    """
    Make existing project notebooks explicitly use this project's kernel.

    This matters because an already-created .ipynb can carry its own
    metadata.kernelspec, which takes precedence over the server's default.
    Only notebook metadata is changed; cells and outputs are untouched.
    """
    path = Path(path)
    for nb in path.rglob("*.ipynb"):
        if any(part in {".venv", ".ipynb_checkpoints"} for part in nb.parts):
            continue
        try:
            data = json.loads(nb.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                continue
            meta = data.setdefault("metadata", {})
            if not isinstance(meta, dict):
                continue
            meta["kernelspec"] = {
                "display_name": display_name,
                "language": "python",
                "name": kernel_id,
            }
            nb.write_text(
                json.dumps(data, ensure_ascii=False, indent=1) + "\n",
                encoding="utf-8"
            )
        except (OSError, ValueError, TypeError):
            # A damaged/unreadable notebook must not prevent JupyterLab from
            # opening the project.
            continue


def start_jupyter(name, path):

    r = RUNNING.get(name)

    if (
        r
        and r.get("proc")
        and r["proc"].poll() is None
    ):
        webbrowser.open(
            f"http://{HOST}:{r['port']}/lab"
        )
        return

    path = Path(path).resolve()
    venv = path / ".venv"
    vp = venv_python(venv)

    if not vp.exists():
        raise RuntimeError(
            "This project's virtual environment is missing. "
            "Repair or recreate the project."
        )

    port = free_port()
    log_path = DATA_DIR / f"jupyter-{name}.log"

    # --------------------------------------------------------
    # Ensure the project kernel exists in the venv itself.
    # --------------------------------------------------------

    item = get_registry()["projects"].get(name, {})
    kernel_id = kernel_id_for_project(name)
    specs = list_kernels()

    if kernel_id not in specs:

        old_kid = item.get("kernel_id")

        kernel_id = register_kernel(
            vp,
            name,
            path
        )

        if old_kid and old_kid != kernel_id:
            remove_kernel(old_kid)

        reg = get_registry()

        if name in reg["projects"]:
            reg["projects"][name]["kernel_id"] = kernel_id
            reg["projects"][name]["display_name"] = f"Python ({name})"

            save_json(
                PROJECTS_FILE,
                reg
            )

    # --------------------------------------------------------
    # Project-local Jupyter configuration.
    # --------------------------------------------------------

    config_dir = path / ".jupyter"
    config_dir.mkdir(parents=True, exist_ok=True)

    # Do NOT restrict KernelSpecManager.kernel_dirs to the project folder.
    # The kernel is installed with `ipykernel install --user`, which is the
    # standard and reliable discovery mechanism used by JupyterLab on Windows.
    # We only allow THIS project's kernel and make it the default.
    config_text = (
        "c = get_config()\n"
        "\n"
        f"c.KernelSpecManager.allowed_kernelspecs = {{{kernel_id!r}}}\n"
        "c.KernelSpecManager.ensure_native_kernel = False\n"
        f"c.MappingKernelManager.default_kernel_name = {kernel_id!r}\n"
        f"c.AsyncMappingKernelManager.default_kernel_name = {kernel_id!r}\n"
    )

    for config_file in (
        config_dir / "jupyter_server_config.py",
        config_dir / "jupyter_lab_config.py",
    ):
        config_file.write_text(config_text, encoding="utf-8")

    _force_project_kernel_in_notebooks(
        path,
        kernel_id,
        f"Python ({name})"
    )

    # --------------------------------------------------------
    # Environment.
    # --------------------------------------------------------

    env = os.environ.copy()
    env["JUPYTER_CONFIG_DIR"] = str(config_dir)

    # --------------------------------------------------------
    # Start JupyterLab.
    # --------------------------------------------------------

    log_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    logf = open(
        log_path,
        "w",
        encoding="utf-8",
        errors="replace"
    )

    proc = subprocess.Popen(
        [
            # JupyterLab may run from the manager's Python.
            # The notebook kernel is explicitly the project's vp.
            sys.executable,
            "-m",
            "jupyter",
            "lab",

            "--notebook-dir",
            str(path),

            "--no-browser",

            "--ip",
            HOST,

            "--port",
            str(port),

            "--ServerApp.token=",

            # Keep kernel discovery standard; restrict only the visible choice.
            "--KernelSpecManager.ensure_native_kernel=False",
            "--KernelSpecManager.allowed_kernelspecs",
            kernel_id,
            "--MappingKernelManager.default_kernel_name",
            kernel_id
        ],

        cwd=str(path),

        env=env,

        stdout=logf,

        stderr=subprocess.STDOUT,

        creationflags=CREATE_NO_WINDOW
    )

    # --------------------------------------------------------
    # Check startup.
    # --------------------------------------------------------

    for _ in range(20):

        if proc.poll() is not None:
            break

        time.sleep(.25)

    if proc.poll() is not None:

        logf.close()

        try:
            tail = (
                log_path.read_text(
                    encoding="utf-8",
                    errors="replace"
                )
                .strip()
                .splitlines()
            )
        except Exception:
            tail = []

        detail = (
            "\n".join(tail[-12:])
            if tail
            else
            "No output was captured."
        )

        raise RuntimeError(
            "JupyterLab could not start for this project."
            "\n\nDetails:\n"
            + detail
        )

    RUNNING[name] = {
        "proc": proc,
        "port": port,
        "log": logf
    }

    threading.Thread(
        target=_wait_and_open,
        args=(
            port,
            time.time() + 30
        ),
        daemon=True
    ).start()


# ============================================================
# WINDOWS PROCESS CLEANUP
# ============================================================

def stop_project_processes(path):

    if os.name != "nt":
        return


    needle = str(
        path.resolve()
    ).lower()


    try:

        ps = (
            "Get-CimInstance Win32_Process "
            "| Select-Object ProcessId,CommandLine "
            "| ConvertTo-Json -Compress"
        )


        r = subprocess.run(

            [
                "powershell",
                "-NoProfile",
                "-Command",
                ps
            ],

            stdout=subprocess.PIPE,

            stderr=subprocess.PIPE,

            text=True,

            encoding="utf-8",

            errors="replace",

            timeout=20,

            creationflags=CREATE_NO_WINDOW
        )


        if (
            r.returncode != 0
            or not r.stdout.strip()
        ):

            return


        rows = json.loads(
            r.stdout
        )


        rows = (
            rows
            if isinstance(rows, list)
            else [rows]
        )


        own = os.getpid()


        for row in rows:

            cmd = (
                row.get("CommandLine")
                or ""
            ).lower()


            pid = row.get(
                "ProcessId"
            )


            if (
                needle in cmd
                and pid
                and int(pid) != own
            ):

                subprocess.run(

                    [
                        "taskkill",
                        "/PID",
                        str(pid),
                        "/T",
                        "/F"
                    ],

                    stdout=subprocess.DEVNULL,

                    stderr=subprocess.DEVNULL,

                    timeout=10,

                    creationflags=CREATE_NO_WINDOW
                )


        time.sleep(.8)


    except Exception:
        pass


# ============================================================
# PROJECT FILES
# ============================================================

def write_project_files(path):

    (
        path / ".gitignore"
    ).write_text(
        ".venv/\n"
        "__pycache__/\n"
        ".ipynb_checkpoints/\n"
        "*.pyc\n",
        encoding="utf-8"
    )


    (
        path / "README.md"
    ).write_text(

        f"# {path.name}\n\n"
        "Hemin Python project managed by "
        "Hemin Python Project Manager.\n",

        encoding="utf-8"
    )


    (
        path / "requirements.txt"
    ).write_text(
        "",
        encoding="utf-8"
    )


# ============================================================
# CREATE PROJECT
# ============================================================

def create_project(name):

    if not valid_name(name):

        raise ValueError(
            "Project name must be 1–64 characters "
            "and use only letters, numbers, "
            "hyphens, or underscores."
        )


    p = project_path(name)


    if p.exists():

        raise ValueError(
            "A project with this name already exists."
        )


    # Make sure JupyterLab exists before creating
    # the project.
    ensure_jupyterlab()


    p.mkdir(
        parents=True
    )


    kid = None


    try:

        # ----------------------------------------------------
        # Project folders
        # ----------------------------------------------------

        for d in (
            "notebooks",
            "src",
            "data"
        ):

            (p / d).mkdir()


        # ----------------------------------------------------
        # Virtual environment
        # ----------------------------------------------------

        v = p / ".venv"


        r = run_cmd(
            [
                sys.executable,
                "-m",
                "venv",
                v
            ],
            600
        )


        if r.returncode != 0:

            raise RuntimeError(
                "Python could not create "
                "the project's virtual environment."
            )


        vp = venv_python(v)


        # ----------------------------------------------------
        # Install ipykernel inside THIS project
        # ----------------------------------------------------

        r = run_cmd(
            [
                vp,
                "-m",
                "pip",
                "install",
                "ipykernel"
            ],
            900
        )


        if r.returncode != 0:

            raise RuntimeError(
                "The project environment was created, "
                "but ipykernel could not be installed."
            )


        # ----------------------------------------------------
        # Create project-specific kernel
        #
        # Example:
        #
        #     Project: MyProject
        #     Kernel:  ppm-myproject
        # ----------------------------------------------------

        kid = register_kernel(
            vp,
            name,
            p
        )


        write_project_files(p)


        # ----------------------------------------------------
        # Save project registry
        # ----------------------------------------------------

        reg = get_registry()


        reg["projects"][name] = {

            "name":name,

            "path":str(p),

            "kernel_id":kid,

            "display_name":
                f"Python ({name})"

        }


        save_json(
            PROJECTS_FILE,
            reg
        )


    except Exception:

        if kid:

            # The kernel is private to this project,
            # but remove it from the filesystem too.
            try:

                shutil.rmtree(
                    kernel_dir(p)
                    / kid,
                    ignore_errors=True
                )

            except Exception:
                pass


        shutil.rmtree(
            p,
            ignore_errors=True
        )

        raise


# ============================================================
# SYNC PROJECTS
# ============================================================

def sync_projects():

    reg = get_registry()

    removed = []


    for name, item in list(
        reg["projects"].items()
    ):

        p = Path(
            item.get(
                "path",
                ""
            )
        )


        if not p.exists():

            # Remove old registered kernel
            remove_kernel(
                item.get(
                    "kernel_id"
                )
            )


            # Also stop a tracked server
            stop_tracked(name)


            del reg[
                "projects"
            ][name]


            removed.append(name)


    save_json(
        PROJECTS_FILE,
        reg
    )


    cleanup_orphan_kernels(reg)


    return removed


# ============================================================
# CLEANUP ORPHAN KERNELS
# ============================================================

def cleanup_orphan_kernels(reg=None):

    reg = (
        reg
        or get_registry()
    )


    known = {
        x.get("kernel_id")
        for x in reg["projects"].values()
    }


    specs = list_kernels()

    removed = 0


    for kid in specs:

        if (
            kid.startswith(KERNEL_PREFIX)
            and kid not in known
        ):

            remove_kernel(kid)

            removed += 1


    stopped = 0


    for name in list(
        RUNNING.keys()
    ):

        if name not in reg["projects"]:

            stop_tracked(name)

            stopped += 1


    return removed, stopped


# ============================================================
# DELETE PROJECT
# ============================================================

def delete_project(
    name,
    confirmation
):

    reg = get_registry()


    item = reg[
        "projects"
    ].get(name)


    if not item:

        raise ValueError(
            "Project not found."
        )


    if confirmation != name:

        raise ValueError(
            "Confirmation did not match. "
            "Nothing was deleted."
        )


    p = project_path(name)


    # --------------------------------------------------------
    # Missing folder
    # --------------------------------------------------------

    if not p.exists():

        remove_kernel(
            item.get("kernel_id")
        )

        stop_tracked(name)

        del reg[
            "projects"
        ][name]


        save_json(
            PROJECTS_FILE,
            reg
        )

        return


    # --------------------------------------------------------
    # Stop everything belonging to project
    # --------------------------------------------------------

    stop_tracked(name)

    stop_project_processes(p)


    # --------------------------------------------------------
    # Remove project kernel
    # --------------------------------------------------------

    remove_kernel(
        item.get("kernel_id")
    )


    # --------------------------------------------------------
    # Delete project folder
    # --------------------------------------------------------

    try:

        shutil.rmtree(p)


    except PermissionError:

        raise RuntimeError(
            "The project is still in use. "
            "Close JupyterLab and any files opened "
            "from this project, then try again."
        )


    except OSError:

        raise RuntimeError(
            "Windows could not remove this project. "
            "Close applications using it, then try again."
        )


    # --------------------------------------------------------
    # Remove registry entry
    # --------------------------------------------------------

    del reg[
        "projects"
    ][name]


    save_json(
        PROJECTS_FILE,
        reg
    )


# ============================================================
# SETUP
# ============================================================

def setup():

    ensure_dirs()

    ensure_jupyterlab()


    # --------------------------------------------------------
    # Create permanent HPPM.py
    # --------------------------------------------------------

    if (
        SOURCE_DIR.resolve()
        != APP_DIR.resolve()
    ):

        try:

            shutil.copy2(
                Path(__file__).resolve(),
                PERMANENT_SCRIPT
            )

        except Exception:

            raise RuntimeError(
                "Setup could not create "
                "the permanent manager file."
            )

    else:

        PERMANENT_SCRIPT.parent.mkdir(
            parents=True,
            exist_ok=True
        )


    # --------------------------------------------------------
    # Create launcher
    # --------------------------------------------------------

    pythonw = Path(
        sys.executable
    ).with_name(
        "pythonw.exe"
    )


    pyexe = (
        pythonw
        if pythonw.exists()
        else
        Path(sys.executable)
    )


    bat = (
        '@echo off\n'
        f'start "" "{pyexe}" '
        f'"{PERMANENT_SCRIPT}"\n'
    )


    BAT_FILE.write_text(
        bat,
        encoding="utf-8"
    )


    # --------------------------------------------------------
    # Save config
    # --------------------------------------------------------

    save_json(
        CONFIG_FILE,

        {
            "version":3,

            "setup_complete":True,

            "app_dir":
                str(APP_DIR),

            "projects_dir":
                str(PROJECTS_DIR)
        }
    )


    save_json(
        PROJECTS_FILE,
        get_registry()
    )


# ============================================================
# STATE
# ============================================================

def state():

    ensure_dirs()


    c = get_config()


    if c.get(
        "setup_complete"
    ):

        sync_projects()


    reg = get_registry()

    ps = []


    for name, item in reg[
        "projects"
    ].items():

        p = Path(
            item["path"]
        )


        r = RUNNING.get(name)


        running = bool(

            r

            and r.get("proc")

            and r["proc"].poll() is None

        )


        status = (

            "Running"

            if running

            else

            (

                "Ready"

                if (
                    p.exists()
                    and venv_python(
                        p / ".venv"
                    ).exists()
                )

                else

                "Needs repair"
            )
        )


        ps.append({

            "name":
                name,

            "path":
                str(p),

            "status":
                status,

            "running":
                running,

            "kernel_id":
                item.get(
                    "kernel_id",
                    kernel_id_for_project(name)
                ),

            "display_name":
                item.get(
                    "display_name",
                    f"Python ({name})"
                )

        })


    return {

        "ok":True,

        "setup":
            bool(
                c.get(
                    "setup_complete"
                )
            ),

        "app_dir":
            str(APP_DIR),

        "projects_dir":
            str(PROJECTS_DIR),

        "bat_file":
            str(BAT_FILE),

        "python_version":
            platform.python_version(),

        "jupyterlab_version":
            jupyterlab_version(),

        "projects":
            ps

    }


# ============================================================
# HTTP HANDLER
# ============================================================

class Handler(
    BaseHTTPRequestHandler
):


    def log_message(
        self,
        *args
    ):

        # Silence HTTP server logs
        pass


    def send_json(
        self,
        d,
        status=200
    ):

        b = json.dumps(
            d,
            ensure_ascii=False
        ).encode()


        self.send_response(status)


        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )


        self.send_header(
            "Content-Length",
            str(len(b))
        )


        self.end_headers()


        self.wfile.write(b)


    def read_json(self):

        n = int(
            self.headers.get(
                "Content-Length",
                "0"
            )
            or 0
        )


        return json.loads(
            self.rfile.read(n)
            or b"{}"
        )


    # ========================================================
    # GET
    # ========================================================

    def do_GET(self):

        try:

            p = urlparse(
                self.path
            ).path


            if p == "/":

                b = HTML.replace(
                    "__PPM_TOKEN__",
                    SESSION_TOKEN
                ).encode()


                self.send_response(200)


                self.send_header(
                    "Content-Type",
                    "text/html; charset=utf-8"
                )


                self.send_header(
                    "Content-Length",
                    str(len(b))
                )


                self.end_headers()


                self.wfile.write(b)


            elif p == "/api/state":

                self.send_json(
                    state()
                )


            else:

                self.send_json(
                    {
                        "ok":False,
                        "error":"Page not found."
                    },
                    404
                )


        except Exception as e:

            self.send_json(
                {
                    "ok":False,
                    "error":friendly(e)
                },
                500
            )


    # ========================================================
    # POST
    # ========================================================

    def do_POST(self):

        try:

            # ------------------------------------------------
            # Session verification
            # ------------------------------------------------

            if (
                self.headers.get(
                    "X-PPM-Token"
                )
                != SESSION_TOKEN
            ):

                self.send_json(
                    {
                        "ok":False,

                        "error":
                            "Request could not be verified. "
                            "Please reload the page."
                    },
                    403
                )

                return


            p = urlparse(
                self.path
            ).path


            d = self.read_json()


            # ------------------------------------------------
            # SETUP
            # ------------------------------------------------

            if p == "/api/setup":

                setup()

                self.send_json(
                    {"ok":True}
                )

                return


            # ------------------------------------------------
            # CREATE
            # ------------------------------------------------

            if p == "/api/projects":

                create_project(
                    d.get(
                        "name",
                        ""
                    ).strip()
                )


                self.send_json(
                    {"ok":True}
                )

                return


            # ------------------------------------------------
            # OPEN
            # ------------------------------------------------

            if p == "/api/projects/open":

                name = d.get(
                    "name",
                    ""
                )


                item = get_registry()[
                    "projects"
                ].get(name)


                if not item:

                    raise ValueError(
                        "Project not found."
                    )


                pp = project_path(name)


                if not pp.exists():

                    raise ValueError(
                        "This project folder is missing. "
                        "Use Sync to clean it up."
                    )


                start_jupyter(
                    name,
                    pp
                )


                self.send_json(
                    {"ok":True}
                )

                return


            # ------------------------------------------------
            # DELETE
            # ------------------------------------------------

            if p == "/api/projects/delete":

                delete_project(
                    d.get(
                        "name",
                        ""
                    ),
                    d.get(
                        "confirm",
                        ""
                    )
                )


                self.send_json(
                    {"ok":True}
                )

                return


            # ------------------------------------------------
            # SYNC
            # ------------------------------------------------

            if p == "/api/sync":

                x = sync_projects()


                if x:

                    if len(x) == 1:

                        message = (
                            "Sync complete. "
                            "Cleaned 1 missing project entry."
                        )

                    else:

                        message = (
                            f"Sync complete. "
                            f"Cleaned {len(x)} missing "
                            "project entries."
                        )

                else:

                    message = (
                        "Sync complete. "
                        "Everything is up to date."
                    )


                self.send_json(
                    {
                        "ok":True,
                        "message":message
                    }
                )

                return


            # ------------------------------------------------
            # CLEANUP
            # ------------------------------------------------

            if p == "/api/kernels/cleanup":

                removed, stopped = (
                    cleanup_orphan_kernels()
                )


                if (
                    not removed
                    and not stopped
                ):

                    msg = (
                        "Nothing to clean up. "
                        "No leftover Jupyter kernels "
                        "or running servers were found."
                    )

                else:

                    parts = []


                    if removed:

                        parts.append(

                            f"removed {removed} "
                            f"leftover kernel"
                            f"{'s' if removed != 1 else ''}"

                        )


                    if stopped:

                        parts.append(

                            f"stopped {stopped} "
                            f"running server"
                            f"{'s' if stopped != 1 else ''} "
                            "for deleted projects"

                        )


                    msg = (
                        "Jupyter cleanup complete: "
                        + ", ".join(parts)
                        + "."
                    )


                self.send_json(
                    {
                        "ok":True,
                        "message":msg
                    }
                )

                return


            # ------------------------------------------------
            # UNKNOWN
            # ------------------------------------------------

            self.send_json(
                {
                    "ok":False,
                    "error":"Unknown request."
                },
                404
            )


        except Exception as e:

            self.send_json(
                {
                    "ok":False,
                    "error":friendly(e)
                },
                400
            )


# ============================================================
# ERROR HANDLING
# ============================================================

def friendly(e):

    if isinstance(
        e,
        (
            ValueError,
            RuntimeError
        )
    ):

        return str(e)


    return (
        "The operation could not be completed. "
        "Please try again."
    )


# ============================================================
# FREE PORT
# ============================================================

def free_port():

    with socket.socket() as s:

        s.bind(
            (
                HOST,
                0
            )
        )

        return s.getsockname()[1]


# ============================================================
# MAIN
# ============================================================

def main():

    ensure_dirs()


    port = free_port()


    server = ThreadingHTTPServer(
        (
            HOST,
            port
        ),
        Handler
    )


    url = (
        f"http://{HOST}:{port}/"
    )


    webbrowser.open(url)


    try:

        server.serve_forever()


    except KeyboardInterrupt:

        pass


    finally:

        server.server_close()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()