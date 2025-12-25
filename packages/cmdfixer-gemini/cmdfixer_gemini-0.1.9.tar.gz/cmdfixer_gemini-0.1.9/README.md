# Cmd-Fixer

**Cmd-Fixer** is a Python CLI tool that helps you **fix corrupted or incorrect shell commands** using AI. It suggests possible corrections, lets you preview them, and optionally executes the selected command immediately.

---

## Features

* AI-powered shell command fixing using Gemini LLM.
* Interactive CLI with numbered command suggestions.
* Option to execute the suggested command directly.
* Stores API key and user preferences locally for seamless usage.
* Configurable maximum number of suggestions per fix.

---

## Installation

Install the package via `pip`:

```bash
  pip install cmdfixer-gemini
```

---

## First-Time Setup

Before using **Cmd-Fixer**, you must **set up your Gemini API key**. Run the following command:

```bash
  cmdfix setup
```

* You will be prompted to enter your **Gemini API key**.
  (Get your key from [https://aistudio.google.com/api-keys](https://aistudio.google.com/api-keys))
* You will also be asked to set the **maximum number of suggestions** per fix.
* The configuration will be saved locally, so you don’t need to enter it again.

---

## Usage

After setup, you can use **Cmd-Fixer** to fix shell commands:

```bash
  cmdfix fix <your-broken-command>
```

**Options:**

* `--run`: Execute the selected command immediately instead of just previewing it.

Example:

```bash
  cmdfix fix mkdir new_folder --run
```

This will suggest corrected commands for `mkdir new_folder` and execute the chosen one immediately if `--run` is provided.

---

## License

MIT License
