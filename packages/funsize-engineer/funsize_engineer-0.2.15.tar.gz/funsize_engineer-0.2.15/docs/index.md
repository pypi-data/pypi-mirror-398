---
layout: default
title: "Building funsize-engineer"
---

<!-- # Building `funsize-engineer`: A Case Study in Agent-First Development -->

**By Dr. Jessica M. Rudd with assistance from Antigravity**

## I. Introduction

In the modern software landscape, the barrier between an idea and a deployable artifact is often the friction of boilerplate and configuration. This post documents the creation of **`funsize-engineer`**, a Python package designed to serve as my terminal-based "business card". Inspired by [David Neal's npm calling card](https://github.com/reverentgeek/reverentgeek-card), I wanted to create a Python equivalent that could be easily distributed and run via PyPI.

The goal was simple: create a distributable Python package that, when run, displays professional contact information and ASCII art in a visually appealing format. However, the *method* of creation was novel. Instead of writing every line of code manually, we utilized **Google Antigravity**, an agentic coding platform. This article demonstrates how the "Agent-First" development paradigm shifts the engineer's role from typist to architect, focusing on task orchestration and verification rather than syntax.

## II. Antigravity Core Functionality

Antigravity operates on a fundamental shift in the developer-tool relationship. It is not merely an autocomplete engine; it is an autonomous agent capable of executing complex, multi-step tasks.

Two core components enable this workflow:

1.  **The Manager View:** Unlike a standard chat interface, Antigravity maintains a structured "Manager View" of the project. It tracks high-level objectives, breaks them down into sub-tasks (e.g., "Scaffold Repository", "Implement Core Logic", "Configure CI/CD"), and maintains context across the entire development lifecycle. This allows the agent to "remember" architectural decisions made in step one while executing step ten.


<pre class="mermaid">
graph TD
    A[Start Project] --> B{Manager View}
    B -->|Task 1| C[Scaffold Repository]
    B -->|Task 2| D[Implement Core Logic]
    B -->|Task 3| E[Configure CI/CD]
    B -->|Task 4| F[Verify Publishing]
    
    C --> G[Artifact: File Structure]
    D --> H[Artifact: card.py]
    E --> I[Artifact: publish.yml]
    
    style B fill:#2d2d2d,stroke:#1493FF,stroke-width:2px,color:#fff
    style G fill:#1e1e1e,stroke:#FF9900,stroke-width:1px,color:#fff
    style H fill:#1e1e1e,stroke:#FF9900,stroke-width:1px,color:#fff
    style I fill:#1e1e1e,stroke:#FF9900,stroke-width:1px,color:#fff
</pre>


2.  **Artifact-Driven Workflow:** The agent does not just stream code into a void. It generates **Artifacts**—structured documents like Implementation Plans, Task Lists, and Code Diffs. These artifacts serve as checkpoints. The agent proposes a plan, the engineer reviews and approves it, and only then does the agent execute. This "Human-in-the-Loop" model ensures that autonomy does not come at the cost of control.

## III. The Package Creation Workflow

The development of `funsize-engineer` followed a structured lifecycle, orchestrated by the agent.

### Phase 1: Planning and Scaffolding
The project began with a high-level directive. The agent analyzed the requirements—a Python package, `rich` library for UI, and PyPI distribution—and generated an implementation plan. It then scaffolded the directory structure, creating `pyproject.toml` for modern standards-compliant packaging and setting up the initial git repository.

### Phase 2: Core Logic Development
With the foundation in place, the agent implemented the core functionality in `funsize_engineer/card.py`. It utilized the `rich` library to create a grid layout, integrating ASCII art loaded from an asset file and styling the text with specific color tokens (e.g., `#1493FF` for branding).

### Phase 3: CI/CD and Versioning
The most complex phase involved automating the release process. The agent configured GitHub Actions workflows to handle dual publishing streams:
*   **TestPyPI:** For development snapshots from the `develop` branch.
*   **PyPI:** For stable releases from the `main` branch.

## IV. Agentic Artifact Review: Validating the Workflow

A critical moment in the project was the configuration of the CI/CD pipeline. The agent proposed a GitHub Actions workflow to automate publishing.

> **Initial Plan Artifact (Excerpt):**
>
> *   *Task:* Configure GitHub Actions for PyPI publishing.
> *   *Action:* Create `.github/workflows/publish.yml`.
> *   *Developer Review:* Required.
>
> **Code Diff (Excerpt):**
>
> ```yaml
> + name: Publish to PyPI
> + on:
> +   push:
> +     branches:
> +       - main
> +       - develop
> + jobs:
> +   build:
> +     runs-on: ubuntu-latest
> +     steps:
> +     - uses: actions/checkout@v4
> +       with:
> +         fetch-depth: 0  # Fetch all history for setuptools-scm
> ```

This artifact allowed the developer to verify that the workflow was correctly targeting both branches and, crucially, that `fetch-depth: 0` was included to ensure `setuptools-scm` could correctly calculate versions from git tags.

## V. Troubleshooting and Iteration

No development process is without friction. We encountered two significant technical hurdles that required agentic problem-solving.

### 1. The "Dev Version" Trap

During the setup of the automated versioning, we encountered an issue where releases from the `main` branch were being tagged with "dev" suffixes (e.g., `0.2.11.dev0`) instead of clean release versions, despite having a correct git tag (e.g., `v0.2.11`).

**The Issue:**
`setuptools-scm` calculates versions based on the distance from the last tag. In our GitHub Actions workflow, we were creating a tag and then checking it out. However, `setuptools-scm` saw the commit *after* the tag (the one triggering the workflow) and assumed it was a "dirty" state, appending a `.dev` suffix. Additionally, the workflow wasn't properly stripping the `v` prefix from tags before passing them to the build system.

**The Resolution:**
The agent diagnosed the issue and implemented a robust fix:
1.  **Explicit Versioning:** Instead of relying on git state, we forced `setuptools-scm` to use the exact version we wanted by setting the `SETUPTOOLS_SCM_PRETEND_VERSION` environment variable.
2.  **Prefix Handling:** We added logic to strip the `v` prefix from git tags (e.g., `v0.2.11` -> `0.2.11`) to ensure Python package compatibility.

```bash
# Force setuptools-scm to use the exact version we want
echo "SETUPTOOLS_SCM_PRETEND_VERSION=${{ env.VERSION_NUMBER }}" >> $GITHUB_ENV
```

### 2. Rendering Diagrams on GitHub Pages

We wanted to include a Mermaid.js diagram to visualize the agentic workflow. However, GitHub Pages (via Jekyll) rendered the mermaid code blocks as raw text instead of diagrams.

**The Fix:**
The agent identified that the default markdown code block syntax (` ```mermaid `) wasn't being processed by the Mermaid JavaScript library. We switched to using raw HTML `<pre class="mermaid">` tags, which allowed the diagram to render perfectly without requiring complex Jekyll plugins.

```html
<pre class="mermaid">
graph TD
    A[Start Project] --> B{Manager View}
    ...
</pre>
```

## VI. Final Code & Output

The result is a lightweight, installable package. The core logic resides in `funsize_engineer/card.py`, which orchestrates the `rich` components.

**Final Example Code:**

```python
# funsize_engineer/card.py
def main():
    console = Console()
    # ... loading assets ...
    
    # Assemble Content
    content = Table.grid(padding=(1, 1))
    content.add_column(justify="center")
    content.add_row(art_panel)
    content.add_row(Text("─" * 100, style="dim"))
    content.add_row(name_text)
    
    console.print(
        Panel(
            content,
            border_style="#1493FF",
            width=108,
            box=ROUNDED
        )
    )
```

**Example Output:**

Running `pipx run funsize-engineer` now renders the following in the terminal:

![Terminal output showing the funsize-engineer calling card with ASCII art dinosaur and contact information](assets/funsize_engineer_card.png)

## VII. Conclusion

The creation of `funsize-engineer` highlights the power of the **Agent-First** methodology. By offloading the implementation details—from directory scaffolding to complex CI/CD scripting—to Antigravity, we focused on the *what* and *why* of the product. The result is a professional-grade Python package built in a fraction of the time, with the agent acting not just as a coder, but as a partner in the engineering process.
