# -*- coding: utf-8 -*-
#2025/12/27  python_xueba
import os
import sys
import platform
import shutil
import subprocess
import json
import argparse
import time
import socket
from datetime import datetime

try:
    import requests
    from colorama import Fore, Style, init
    init(autoreset=True)
except ImportError:
    print("Error: Requires 'requests' and 'colorama'. Run: pip install requests colorama")
    sys.exit(1)

# ==========================================
# 全局镜像源配置
# ==========================================

GITHUB_SOURCES = [
    "https://raw.githubusercontent.com/521xueweihan/GitHub520/main/src/hosts",
    "https://hosts.gitcdn.top/hosts.txt",
    "https://raw.staticdn.net/ineo6/hosts/master/next-hosts",
    "https://ghp.ci/https://raw.githubusercontent.com/521xueweihan/GitHub520/main/src/hosts",
    "https://raw.fastgit.org/521xueweihan/GitHub520/main/src/hosts"
]

PIP_MIRRORS = [
    "https://pypi.tuna.tsinghua.edu.cn/simple", "https://mirrors.aliyun.com/pypi/simple/",
    "https://pypi.douban.com/simple", "https://mirrors.ustc.edu.cn/pypi/web/simple"
]

NPM_MIRRORS = [
    "https://registry.npmmirror.com", "https://registry.npm.taobao.org"
]

CARGO_SOURCES = [
    "sparse+https://mirrors.sjtug.sjtu.edu.cn/git/crates.io-index/", 
    "sparse+https://mirrors.tuna.tsinghua.edu.cn/git/crates.io-index.git"
]

DOCKER_REGISTRIES = [
    "https://docker.m.daocloud.io", "https://docker.1panel.live",
    "https://docker.mirrors.ustc.edu.cn", "https://hub-mirror.c.163.com"
]

APT_MIRRORS_UBUNTU = [
    ("https://mirrors.tuna.tsinghua.edu.cn/ubuntu/", "清华"),
    ("https://mirrors.aliyun.com/ubuntu/", "阿里云"),
    ("https://mirrors.ustc.edu.cn/ubuntu/", "中科大")
]

APT_MIRRORS_DEBIAN = [
    ("https://mirrors.tuna.tsinghua.edu.cn/debian/", "清华"),
    ("https://mirrors.aliyun.com/debian/", "阿里云"),
    ("https://mirrors.ustc.edu.cn/debian/", "中科大")
]

TERMUX_PKG_MIRRORS = [
    "https://mirrors.tuna.tsinghua.edu.cn/termux/stable/"
]

# ==========================================
# 核心逻辑类
# ==========================================

class Accelerator:
    def __init__(self):
        self.system = platform.system()
        self.is_root = self._check_root()
        self.is_termux = 'com.termux' in os.environ.get('PREFIX', '')

    def _log(self, level, msg):
        colors = {"INFO": Fore.CYAN, "SUCCESS": Fore.GREEN, "WARN": Fore.YELLOW, "ERROR": Fore.RED}
        print(f"{colors.get(level, Fore.WHITE)}[{level}] {msg}")

    def _check_root(self):
        if self.system == "Windows":
            try:
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin()
            except:
                return False
        return os.geteuid() == 0

    def _backup(self, path):
        if not os.path.exists(path): return
        try:
            shutil.copy2(path, f"{path}.bak.{int(time.time())}")
        except: pass

    def _ensure_dir(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)

    def _flush_dns(self):
        try:
            if self.system == "Windows": subprocess.run(['ipconfig', '/flushdns'], shell=True, check=True)
            elif self.system == "Darwin": subprocess.run(['sudo', 'killall', '-HUP', 'mDNSResponder'], check=False)
        except: pass

    def _fetch(self, url):
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=6)
            return r.text if r.status_code == 200 else None
        except: return None

    # --- GitHub ---
    def fix_github(self):
        self._log("INFO", "加速 GitHub...")
        hosts = r"C:\Windows\System32\drivers\etc\hosts" if self.system == "Windows" else "/etc/hosts"
        
        if not os.access(hosts, os.W_OK):
            self._log("WARN", "需要 Root/Admin 权限修改 Hosts")
            return

        content = None
        for url in GITHUB_SOURCES:
            if content: break
            content = self._fetch(url)

        if not content:
            self._log("ERROR", "所有 GitHub Hosts 源均失效")
            return

        lines = [l.strip() for l in content.splitlines() if l.strip() and not l.startswith("#")]
        self._backup(hosts)

        try:
            with open(hosts, 'r', encoding='utf-8', errors='ignore') as f:
                old = f.readlines()
            new = []
            skip = False
            for l in old:
                if "GITHUB_SPEEDUP_START" in l: skip = True
                if "GITHUB_SPEEDUP_END" in l: skip = False
                if not skip: new.append(l)
            
            with open(hosts, 'w', encoding='utf-8') as f:
                f.writelines(new)
                if new and not new[-1].endswith('\n'): f.write('\n')
                f.write("\n# --- GITHUB_SPEEDUP_START ---\n# Update by fuckit\n")
                f.write("\n".join(lines) + "\n# --- GITHUB_SPEEDUP_END ---\n")
            
            self._log("SUCCESS", "GitHub Hosts 已更新")
            self._flush_dns()
        except Exception as e:
            self._log("ERROR", f"写入失败: {e}")

    # --- Python (Pip / UV) ---
    def fix_pip(self):
        self._log("INFO", "加速 Pip...")
        path = os.path.expanduser(r"~\pip\pip.ini") if self.system == "Windows" else os.path.expanduser("~/.pip/pip.conf")
        self._ensure_dir(path)
        self._backup(path)
        
        mirror = PIP_MIRRORS[0]
        host = mirror.split('/')[2]
        
        try:
            with open(path, 'w') as f:
                f.write(f"[global]\nindex-url = {mirror}\ntrusted-host = {host}\ntimeout = 60\n")
            self._log("SUCCESS", f"Pip 已指向 {host}")
        except Exception as e:
            self._log("ERROR", f"Pip 失败: {e}")

    def fix_uv(self):
        self._log("INFO", "加速 UV...")
        path = os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), "uv", "uv.toml")
        self._ensure_dir(path)
        self._backup(path)
        try:
            with open(path, 'w') as f:
                f.write(f'[index]\ndefault = "{PIP_MIRRORS[0]}"\n')
            self._log("SUCCESS", "UV 已加速")
        except Exception as e:
            self._log("ERROR", f"UV 失败: {e}")

    # --- Node.js (NPM) ---
    def fix_npm(self):
        self._log("INFO", "加速 NPM...")
        path = os.path.expanduser("~/.npmrc")
        self._backup(path)
        try:
            with open(path, 'w') as f:
                f.write(f"registry={NPM_MIRRORS[0]}\n")
            self._log("SUCCESS", f"NPM 已指向 {NPM_MIRRORS[0]}")
        except Exception as e:
            self._log("ERROR", f"NPM 失败: {e}")

    # --- Docker ---
    def fix_docker(self):
        if self.system == "Windows":
            self._log("INFO", "Windows Docker 请手动配置镜像: " + DOCKER_REGISTRIES[0])
            return
        if not self.is_root:
            self._log("WARN", "Docker 需要 Root 权限")
            return

        self._log("INFO", "加速 Docker...")
        path = "/etc/docker/daemon.json"
        self._backup(path)
        try:
            conf = {}
            if os.path.exists(path):
                with open(path, 'r') as f: conf = json.load(f)
            conf["registry-mirrors"] = DOCKER_REGISTRIES
            with open(path, 'w') as f: json.dump(conf, f, indent=4)
            subprocess.run(["systemctl", "daemon-reload"], check=False)
            subprocess.run(["systemctl", "restart", "docker"], check=False)
            self._log("SUCCESS", "Docker 已重启")
        except Exception as e:
            self._log("ERROR", f"Docker 失败: {e}")

    # --- Linux / Termux (Apt / Pkg) ---
    def fix_apt(self):
        if self.is_termux:
            self.fix_termux()
            return

        if self.system != "Linux" or not self.is_root:
            self._log("WARN", "Apt 需要 Linux Root 环境")
            return

        self._log("INFO", "加速 Apt...")
        distro, codename = None, None
        try:
            with open("/etc/os-release") as f:
                for l in f:
                    if l.startswith("ID="): distro = l.strip().split('=')[1].strip('"').lower()
                    if l.startswith("VERSION_CODENAME="): codename = l.strip().split('=')[1].strip('"')
        except: pass

        if not distro: return
        sources = "/etc/apt/sources.list"
        self._backup(sources)
        
        try:
            url, name = APT_MIRRORS_UBUNTU[0] if "ubuntu" in distro else APT_MIRRORS_DEBIAN[0]
            sec = "http://security.ubuntu.com/ubuntu/" if "ubuntu" in distro else "https://security.debian.org/debian-security/"
            
            content = f"""# Generated by fuckit
deb {url} {codename} main restricted universe multiverse
deb {url} {codename}-updates main restricted universe multiverse
deb {url} {codename}-backports main restricted universe multiverse
deb {sec} {codename}-security main restricted universe multiverse
"""
            with open(sources, 'w') as f: f.write(content)
            self._log("SUCCESS", f"{distro} 已切换至 {name}")
        except Exception as e:
            self._log("ERROR", f"Apt 失败: {e}")

    def fix_termux(self):
        self._log("INFO", "加速 Termux Pkg...")
        if not self.is_root:
            self._log("WARN", "修改 Pkg 源需要 Root (pkg install tsu)")
            return
        
        sources = "/data/data/com.termux/files/usr/etc/apt/sources.list"
        self._backup(sources)
        try:
            # 清华 Termux 源
            content = f"# The main termux repository\ndeb {TERMUX_PKG_MIRRORS[0]} main\n"
            with open(sources, 'w') as f: f.write(content)
            self._log("SUCCESS", "Termux 源已更新")
        except Exception as e:
            self._log("ERROR", f"Termux 失败: {e}")

    # --- Cargo (Rust) ---
    def fix_cargo(self):
        self._log("INFO", "加速 Cargo...")
        path = os.path.expanduser("~/.cargo/config")
        self._ensure_dir(path)
        self._backup(path)
        try:
            content = f"""[source.crates-io]
replace-with = 'sjtu'
[source.sjtu]
registry = "{CARGO_SOURCES[0]}"
"""
            with open(path, 'w') as f: f.write(content)
            self._log("SUCCESS", "Cargo 已加速")
        except Exception as e:
            self._log("ERROR", f"Cargo 失败: {e}")

    # --- Composer (PHP) ---
    def fix_composer(self):
        self._log("INFO", "加速 Composer...")
        path = os.path.expanduser("~/.composer/config.json")
        self._ensure_dir(path)
        self._backup(path)
        try:
            conf = {"config": {"repo": {"packagist": {"type": "composer", "url": "https://mirrors.aliyun.com/composer/"}}}}
            with open(path, 'w') as f: json.dump(conf, f)
            self._log("SUCCESS", "Composer 已加速")
        except Exception as e:
            self._log("ERROR", f"Composer 失败: {e}")

    # --- Homebrew (macOS) ---
    def fix_brew(self):
        if self.system != "Darwin":
            self._log("WARN", "Homebrew 仅适用于 macOS")
            return
        
        self._log("INFO", "加速 Homebrew (Bottles)...")
        shellrc = os.path.expanduser("~/.zshrc") if os.path.exists(os.path.expanduser("~/.zshrc")) else os.path.expanduser("~/.bash_profile")
        line = 'export HOMEBREW_BOTTLE_DOMAIN=https://mirrors.tuna.tsinghua.edu.cn/homebrew-bottles'
        
        try:
            content = ""
            if os.path.exists(shellrc):
                with open(shellrc, 'r') as f: content = f.read()
            
            if "HOMEBREW_BOTTLE_DOMAIN" not in content:
                with open(shellrc, 'a') as f:
                    f.write(f"\n# Fuckit Brew Mirror\n{line}\n")
                self._log("SUCCESS", "Homebrew 配置已写入 Shell 启动项")
            else:
                self._log("INFO", "Homebrew 已配置")
        except Exception as e:
            self._log("ERROR", f"Homebrew 失败: {e}")

# ==========================================
# 主入口
# ==========================================

def main():
    parser = argparse.ArgumentParser(description="Dev All-in-One Accelerator v2.0")
    parser.add_argument('command', nargs='?', default='fuckit', help="Command (default: fuckit)")
    
    parser.add_argument('--github', action='store_true', help="Accelerate GitHub")
    parser.add_argument('--pip', action='store_true', help="Accelerate Pip")
    parser.add_argument('--uv', action='store_true', help="Accelerate UV")
    parser.add_argument('--npm', action='store_true', help="Accelerate NPM")
    parser.add_argument('--docker', action='store_true', help="Accelerate Docker")
    parser.add_argument('--apt', action='store_true', help="Accelerate Apt/Pkg (Linux/Termux)")
    parser.add_argument('--cargo', action='store_true', help="Accelerate Cargo (Rust)")
    parser.add_argument('--composer', action='store_true', help="Accelerate Composer (PHP)")
    parser.add_argument('--brew', action='store_true', help="Accelerate Homebrew (macOS)")
    parser.add_argument('--all', action='store_true', help="Run all suitable accelerators")

    args = parser.parse_args()

    if args.command != 'fuckit':
        print("Usage: fuckit [options]")
        return

    acc = Accelerator()
    
    print(Fore.YELLOW + Style.BRIGHT + "╔══════════════════════════════════════╗")
    print(Fore.YELLOW + Style.BRIGHT + "║     Dev All-in-One Accelerator v2.0    ║")
    print(Fore.YELLOW + Style.BRIGHT + "╚══════════════════════════════════════╝")

    if args.all:
        acc.fix_github()
        acc.fix_pip()
        acc.fix_uv()
        acc.fix_npm()
        acc.fix_cargo()
        acc.fix_composer()
        
        if acc.system == "Darwin": acc.fix_brew()
        if acc.system != "Windows": acc.fix_docker()
        
        if acc.system == "Linux": acc.fix_apt()
        elif acc.is_termux: acc.fix_termux()
    else:
        if args.github: acc.fix_github()
        if args.pip: acc.fix_pip()
        if args.uv: acc.fix_uv()
        if args.npm: acc.fix_npm()
        if args.cargo: acc.fix_cargo()
        if args.composer: acc.fix_composer()
        if args.docker: acc.fix_docker()
        if args.apt: acc.fix_apt()
        if args.brew: acc.fix_brew()

        if not any([args.github, args.pip, args.uv, args.npm, args.docker, args.apt, args.cargo, args.composer, args.brew]):
            print(Fore.CYAN + "请指定加速类型，例如: fuckit --all 或 fuckit --github --npm")

    print(Fore.GREEN + "\n✨ All Done ✨\n")

if __name__ == "__main__":
    main()