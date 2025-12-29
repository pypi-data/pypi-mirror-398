# 🐳 Docker Lens

**Docker Lens** is a lightweight, developer-friendly CLI tool for **debugging running Docker containers**.

It lets you instantly attach a fully-featured debug container to any running container — sharing **network, PID, and filesystem namespaces** — similar to `docker debug`, but **open-source and pip-installable**.

> Think of it as:  
> **`kubectl debug` for Docker containers** 🔍

![Demo](demo.gif){ width=400px }

---

## ✨ Features

- 🔗 Attach a debug container to any running container
- 🧠 Shares **network**, **PID**, and **volumes**
- 🖥️ Fully interactive TTY
- 🧹 Debug container is **removed automatically on exit**
- 📦 Auto-pull debug images if missing
- ⚙️ Configurable default debug image (profiles or custom)
- 🐍 Written in Python, installable via `pip`

---

## 📦 Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install docker-lens
```

### Requirements

- Python 3.10+
- Docker installed and running
- Access to Docker socket (`/var/run/docker.sock`)

---

## 🚀 Usage

### List containers

```bash
docker-lens
```
Equivalent to:
```bash
docker ps
```

### Debug a running container

```bash
docker-lens debug <container_id_or_name>
```

Example:

```bash
docker-lens debug web-api
```

### Specify debug image or shell

```bash
docker-lens debug web-api --image ubuntu:latest --shell /bin/bash
```

### Change the default debug image
Use any custom image:
```bash
docker-lens set image jonlabelle/network-tools
```
Or use one of the pre-defined debug image profiles:
```bash
docker-lens set image network
```

## 🧰 Debug Image Profiles

| Profile | Usage | Image |
|-------|------|------|
| minimal | common system and networking essentials. |kavehmoradian/docker-lens:minimal|
| network | Focused on network debugging and analysis. |kavehmoradian/docker-lens:network|
| process | Focused on process, system, and application debugging. |kavehmoradian/docker-lens:process|
| full | Includes everything from both network and process. |kavehmoradian/docker-lens:full|

---

## ⚙️ Configuration

Config file location:

```
~/.config/docker-lens/config.yaml
```

Example:

```yaml
default_image: kavehmoradian/docker-lens:minimal
```

---


## 🔐 Permissions

If you see:

```
Permission denied while connecting to Docker socket.
```

Fix it:

```bash
sudo usermod -aG docker $USER
newgrp docker
```
