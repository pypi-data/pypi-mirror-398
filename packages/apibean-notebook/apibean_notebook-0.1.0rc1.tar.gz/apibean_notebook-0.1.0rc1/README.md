## apibean-notebook

📘 **apibean-notebook** is a lightweight, notebook-first library that provides utilities for executing APIs, managing client sessions, and rendering rich, interactive outputs directly inside Jupyter notebooks.

It is designed to be imported and used **inside notebook cells**, focusing on developer experience, exploration, and observability — without requiring any Jupyter server extensions or infrastructure setup.

### ✨ Key Features

* **In-kernel API execution**

  * Run API calls and commands directly from notebook cells
  * Reuse authenticated client sessions and contexts

* **Rich notebook outputs**

  * Display structured data, tables, logs, and status messages
  * Built on top of `IPython.display` and Jupyter’s rich output system

* **Session-aware helpers**

  * Manage API clients, tokens, and default settings across cells
  * Designed to work naturally with iterative notebook workflows

* **No server-side dependencies**

  * Does not require Jupyter server extensions
  * Fully compatible with JupyterLab, VS Code Notebooks, and cloud notebooks

### 🎯 Design Principles

* Notebook-first, not server-first
* Explicit execution, no hidden side effects
* Rich output over raw logs
* Minimal dependencies and fast import time

### 🔒 Scope and Non-Goals

`apibean-notebook` intentionally does **not**:

* Manage Jupyter servers or kernels
* Start background services
* Perform infrastructure orchestration

These concerns are handled by other packages in the apibean ecosystem.
