# Setup_Files — OpenHands Hybrid Environment Setup

This folder contains helper scripts and configuration files used to set up a
hybrid-model OpenHands environment inside Trae IDE.

This workflow assumes:

- You cloned the official OpenHands repository using GitHub Desktop
- You opened the cloned repo in Trae IDE
- You want OpenHands configured with hybrid model routing
- You want Trae to be able to trigger OpenHands tasks directly

---

## 📌 What This Folder Contains

### 1. `setup_openhands_hybrid.py`
A one-shot setup script that:

- Creates the OpenHands config directory:
  `~/.openhands/`
- Writes the hybrid routing config:
  `~/.openhands/openhands.config.json`
- Appends your API keys to your shell profile
- Prints instructions for Trae integration

This script **does not clone OpenHands** because the repo is already cloned.

---

## 🚀 How to Run the Setup Script

From inside Trae’s terminal or your system terminal:

```bash
cd Setup_Files
python setup_openhands_hybrid.py
