#!/usr/bin/env python3

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUNDLER_VERSION = "2.3.25"


def run(cmd, env=None):
    print("+ " + " ".join(str(part) for part in cmd), flush=True)
    subprocess.run(cmd, cwd=ROOT, env=env, check=True)


def output(cmd, env=None):
    return subprocess.check_output(cmd, cwd=ROOT, env=env, text=True).strip()


def candidate_rubies():
    env_ruby = os.environ.get("RUBY")
    if env_ruby:
        yield Path(env_ruby)

    for path in (
        "/opt/homebrew/opt/ruby@3.3/bin/ruby",
        "/usr/local/opt/ruby@3.3/bin/ruby",
        "/opt/homebrew/opt/ruby@3.2/bin/ruby",
        "/usr/local/opt/ruby@3.2/bin/ruby",
        "/opt/homebrew/opt/ruby@3.1/bin/ruby",
        "/usr/local/opt/ruby@3.1/bin/ruby",
    ):
        yield Path(path)

    for name in ("ruby",):
        found = shutil.which(name)
        if found:
            yield Path(found)

    for path in (
        "/opt/homebrew/opt/ruby/bin/ruby",
        "/usr/local/opt/ruby/bin/ruby",
        "/opt/homebrew/bin/ruby",
        "/usr/local/bin/ruby",
    ):
        yield Path(path)


def ruby_version(ruby):
    try:
        return output([str(ruby), "-e", "print RUBY_VERSION"])
    except (OSError, subprocess.CalledProcessError):
        return None


def is_system_ruby(ruby):
    try:
        resolved = ruby.resolve()
    except OSError:
        resolved = ruby
    return str(resolved).startswith("/usr/bin/") or str(resolved).startswith("/System/")


def version_tuple(version):
    return tuple(int(part) for part in version.split(".")[:3])


def find_ruby():
    seen = set()
    system_choice = None

    for ruby in candidate_rubies():
        if not ruby or ruby in seen or not ruby.exists():
            continue
        seen.add(ruby)

        version = ruby_version(ruby)
        if not version:
            continue

        if is_system_ruby(ruby):
            system_choice = (ruby, version)
            continue

        if (2, 7, 0) <= version_tuple(version) < (4, 0, 0):
            return ruby, version

    if system_choice:
        return system_choice

    return None, None


def local_platforms():
    machine = platform.machine().lower()
    release = platform.release().split(".")[0]

    platforms = ["ruby"]
    if sys.platform == "darwin":
        if machine in {"arm64", "aarch64"}:
            platforms.append(f"arm64-darwin-{release}")
        platforms.append(f"x86_64-darwin-{release}")

    return platforms


def build_env(ruby):
    ruby_bin = str(ruby.parent)
    local_bin = str(ROOT / "vendor" / "ruby-bin")
    local_gems = str(ROOT / "vendor" / "ruby-gems")
    env = os.environ.copy()
    env["PATH"] = os.pathsep.join([local_bin, ruby_bin, env.get("PATH", "")])
    env["GEM_HOME"] = local_gems
    env["GEM_PATH"] = local_gems
    env["BUNDLE_PATH"] = str(ROOT / "vendor" / "bundle")
    env["BUNDLE_APP_CONFIG"] = str(ROOT / ".bundle")
    return env


def install_homebrew_ruby():
    brew = shutil.which("brew")
    if not brew:
        raise RuntimeError("Homebrew is not installed, so I cannot install Ruby automatically.")
    run([brew, "install", "ruby@3.3"])


def ensure_not_system_ruby(ruby, version):
    if not is_system_ruby(ruby) and version_tuple(version) < (4, 0, 0):
        return

    raise RuntimeError(
        "\n".join(
            [
                f"Unsupported Ruby was selected: {ruby} ({version}).",
                "Use Ruby 3.x for this GitHub Pages/Jekyll site.",
                "macOS system Ruby is missing the headers needed to build native gems on this machine, and Ruby 4 resolves incompatible GitHub Pages dependencies.",
                "",
                "Install Homebrew Ruby 3.3, then rerun this script:",
                "  brew install ruby@3.3",
                "  python3 scripts/dev.py",
                "",
                "Or let this script install Ruby 3.3:",
                "  python3 scripts/dev.py --install-ruby",
            ]
        )
    )


def ensure_bundler(ruby, env):
    local_bin = ROOT / "vendor" / "ruby-bin"
    local_gems = ROOT / "vendor" / "ruby-gems"
    local_bin.mkdir(parents=True, exist_ok=True)
    local_gems.mkdir(parents=True, exist_ok=True)

    bundle = local_bin / "bundle"
    if bundle.exists():
        try:
            version = output([str(ruby), str(bundle), "-v"], env=env)
            if BUNDLER_VERSION in version:
                return [str(ruby), str(bundle), f"_{BUNDLER_VERSION}_"]
        except (OSError, subprocess.CalledProcessError):
            bundle.unlink(missing_ok=True)

    run(
        [
            str(ruby),
            "-S",
            "gem",
            "install",
            "bundler",
            "-v",
            BUNDLER_VERSION,
            "--install-dir",
            str(local_gems),
            "--bindir",
            str(local_bin),
            "--no-document",
        ],
        env=env,
    )
    return [str(ruby), str(bundle), f"_{BUNDLER_VERSION}_"]


def sync_docs():
    run([sys.executable, ".github/scripts/sync_external_docs.py"])
    run([sys.executable, ".github/scripts/validate_docs.py"])


def ensure_bundle(bundle, env):
    run([*bundle, "config", "set", "path", "vendor/bundle"], env=env)
    run([*bundle, "lock", "--add-platform", *local_platforms()], env=env)
    run([*bundle, "install"], env=env)


def serve(bundle, env, host, port, livereload):
    cmd = [
        *bundle,
        "exec",
        "jekyll",
        "serve",
        "--host",
        host,
        "--port",
        str(port),
        "--watch",
    ]
    if livereload:
        cmd.append("--livereload")
    run(cmd, env=env)


def main():
    parser = argparse.ArgumentParser(description="Run the AnyLog docs site locally without Docker.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default=4000, type=int)
    parser.add_argument("--no-livereload", action="store_true")
    parser.add_argument("--no-sync", action="store_true", help="Skip pulling external docs before serving.")
    parser.add_argument("--skip-install", action="store_true", help="Skip bundle install and use existing gems.")
    parser.add_argument("--install-ruby", action="store_true", help="Install Homebrew Ruby if no non-system Ruby is available.")
    args = parser.parse_args()

    ruby, version = find_ruby()
    if args.install_ruby and (not ruby or is_system_ruby(ruby)):
        install_homebrew_ruby()
        ruby, version = find_ruby()

    if not ruby:
        raise RuntimeError("Ruby was not found. Install Ruby with Homebrew, rbenv, or asdf.")

    ensure_not_system_ruby(ruby, version)
    print(f"Using Ruby {version}: {ruby}")

    env = build_env(ruby)

    if not args.no_sync:
        sync_docs()

    bundle = ensure_bundler(ruby, env)
    if not args.skip_install:
        ensure_bundle(bundle, env)

    serve(bundle, env, args.host, args.port, not args.no_livereload)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped local Jekyll server.")
        sys.exit(130)
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
