# HPPM — Hemin Python Project Manager

> **A lightweight, single-file project manager for local Python and Jupyter projects.**

HPPM (Hemin Python Project Manager) is a lightweight tool designed to simplify the creation and management of local **Python and Jupyter projects**.

It provides a simple **browser-based interface** while automatically handling the initial project setup, directories, and environment-related tasks.

The goal is simple:

> **Run one file, let HPPM handle the setup, and start working on your project.**

---

## ✨ Features

* 🐍 Python & Jupyter focused
* 📦 **Single-file application**
* 🌐 Browser-based user interface
* 📁 Automatic project directory creation
* ⚙️ Simplified environment setup
* ▶️ Easy project launching
* 💻 Designed for local use
* 🚫 No traditional installation required
* 🔬 Suitable for research and scientific computing workflows

---

## 🎯 Why HPPM?

Starting a new Python or Jupyter project often involves repetitive setup tasks:

* Creating project directories
* Creating virtual environments
* Installing dependencies
* Managing project environments
* Launching Jupyter
* Keeping projects organized

HPPM is designed to reduce this setup overhead.

Instead of manually preparing the environment and project structure every time, simply run HPPM and use its web-based interface to create and manage your projects.

> **Run it. Create a project. Start working.**

---

## 🚀 Getting Started

HPPM is distributed as a **single Python file**:

```text
HeminPythonProjectManager.py
```

There is no installer or complex project structure required.

### 1. Download

Download `HeminPythonProjectManager.py` from this repository.

### 2. Choose a location

Place the file in any folder where you want HPPM and its projects to be stored.

For example:

```text
My Tools/
└── HPPM/
    └── HeminPythonProjectManager.py
```

### 3. Run HPPM

Run the Python file:

```bash
python HeminPythonProjectManager.py
```

On the first run, HPPM automatically creates its required files and directories in the **same location as the Python file**.

### 4. Launch HPPM

After the initial setup, HPPM creates an `HPPM.bat` file.

On Windows, you can use this file to conveniently launch HPPM in the future without manually running the Python script.

---

## 📂 Automatic Setup

HPPM requires no manual creation of its internal directories.

When `HeminPythonProjectManager.py` is run for the first time, it automatically creates the required local structure alongside the Python file.

The resulting structure is similar to:

```text
HPPM/
├── HeminPythonProjectManager.py
├── HPPM.bat
├── HPPM/
└── Projects/
```

The generated components are used for:

* `HeminPythonProjectManager.py` — the main HPPM application
* `HPPM.bat` — a convenient launcher for starting HPPM
* `HPPM/` — HPPM's internal system data
* `Projects/` — the location used for projects created through HPPM

The exact contents of the generated directories are managed automatically by HPPM.

---

## 🔄 Basic Workflow

```text
HeminPythonProjectManager.py
            │
            ▼
        First Run
            │
            ▼
     Automatic Setup
            │
      ┌─────┼─────┐
      ▼     ▼     ▼
HPPM  Projects  HPPM.bat
                  │
                  ▼
             Launch HPPM
                  │
                  ▼
            Web Interface
                  │
                  ▼
         Manage Your Projects
```

---

## 🌐 Browser-Based Interface

HPPM uses a **local web interface** instead of a traditional desktop GUI.

The application runs on your local computer, while your web browser provides the interface for interacting with HPPM.

This approach keeps the application lightweight while providing a simple and familiar graphical experience.

No external web service is required for the core HPPM workflow.

---

## 📓 Jupyter & Python Projects

HPPM is designed primarily around Python and Jupyter-based workflows.

It can be useful for projects involving:

* Jupyter Notebooks
* Python scripting
* Data analysis
* Scientific computing
* Machine learning
* Data visualization
* Experimental research workflows

---

## 🔬 Research & Scientific Computing

HPPM was created from a practical research perspective.

As a researcher working in **Surveying Engineering, Remote Sensing, Earth Observation, Geospatial Science, and scientific computing**, I frequently work with Python and Jupyter-based projects.

The motivation behind HPPM was to reduce the repetitive technical steps involved in starting a new project and make local project management more convenient.

HPPM can be particularly useful for workflows involving:

* 🌍 Remote Sensing
* 🛰️ Earth Observation
* 🗺️ Geospatial Science
* 📍 GIS and spatial analysis
* 📡 Satellite image processing
* 📐 Surveying
* 📷 Photogrammetry
* 📊 Scientific data analysis
* 🤖 Machine learning
* 📓 Jupyter-based research

HPPM is **not limited to geospatial applications** and can be used for any suitable local Python/Jupyter workflow.

---

## 🧩 Single-File Design

One of the main design principles of HPPM is **simplicity**.

The application is distributed as a single Python file:

```text
HeminPythonProjectManager.py
```

You do not need to clone a complex Python project or manually assemble multiple application files.

Simply place the file where you want it and run it.

HPPM takes care of its required local structure automatically.

---

## 🖥️ Requirements

* **Python 3.x**
* A modern web browser
* **Windows** is currently the primary target platform

Python must be available on the system in order to run the application.

---

## 🤖 AI-Assisted Development

HPPM was developed using an **AI-assisted development workflow**.

The concept, requirements, workflow, interface direction, testing, debugging, evaluation, and iterative improvements were guided and supervised by **Hemin Azizi**.

AI tools were extensively used to assist with implementation and code generation.

The development process can therefore be described as:

> **Human-directed, AI-assisted development.**

The project concept, product direction, design decisions, requirements, and final evaluation were driven by the author.

---

## 📌 Project Status

HPPM is an evolving project developed from practical needs in research and scientific computing workflows.

The current version focuses on providing a simple and lightweight way to create and manage local Python/Jupyter projects.

Features and implementation details may evolve over time.

---

## 🗺️ Roadmap

Potential future improvements include:

* [ ] Improved project management
* [ ] Additional project configuration options
* [ ] Enhanced environment management
* [ ] Project templates
* [ ] Improved Jupyter integration
* [ ] Additional scientific-computing features
* [ ] Improved user interface
* [ ] Cross-platform support

---

## 👨‍🔬 Author

**Hemin Azizi**

*Geospatial Research · Remote Sensing · Earth Observation · Scientific Computing*

Research interests include:

* Remote Sensing
* Earth Observation
* Geospatial Science
* Spatial Data Analysis
* Scientific Computing

---

## 📄 License

HPPM is released under the **MIT License**.

See the [`LICENSE`](LICENSE) file for the full license text.

---

<p align="center">

**Created, designed & maintained by Hemin Azizi ,developed with AI assistance**

</p>
