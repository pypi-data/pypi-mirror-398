import os
import subprocess
import sys
import re
import termios
import tty
import select
import threading
import time
import importlib.metadata

# 𝗠𝗮𝗻𝗮𝗴𝗲𝗱 𝗕𝘆 @𝗡𝗮𝗰𝘁𝗶𝗿𝗲

def check_root():
    if os.geteuid() != 0:
        print("\033[1;31mYour VPS/Machine is Not Root! Please Use Root Environment.\033[0m")
        sys.exit(1)

def check_supervisor_installed():
    try:
        subprocess.run(
            ["supervisord", "-v"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[INFO] Supervisor installing...")
        subprocess.run(
            ["sudo", "apt", "update", "-o", "Acquire::AllowInsecureRepositories=true"],
            check=True
        )
        subprocess.run(["sudo", "apt", "install", "supervisor", "-y"], check=True)

def detect_virtualenv_activate_path():
    venv_path = os.environ.get("VIRTUAL_ENV")
    if venv_path:
        activate_path = os.path.join(venv_path, "bin", "activate")
        if os.path.exists(activate_path):
            return activate_path
    return None

def prepare_command(raw_command):
    activate_path = detect_virtualenv_activate_path()
    if activate_path:
        return f"bash -c 'source {activate_path} && {raw_command}'"
    return raw_command

def _is_data():
    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

def get_filtered_input(prompt):
    sys.stdout.write("\033[1;33m" + prompt + "\033[0m")
    sys.stdout.flush()
    result = ""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    allowed_re = re.compile(r"[A-Za-z0-9-]")

    try:
        tty.setraw(fd)
        while True:
            ch = sys.stdin.read(1)

            if ch in ("\r", "\n"):
                sys.stdout.write("\n")
                break

            if ch == "\x03":
                raise KeyboardInterrupt

            if ch in ("\x7f", "\b"):
                if result:
                    result = result[:-1]
                    sys.stdout.write("\b \b")
                continue

            if allowed_re.fullmatch(ch):
                result += ch
                sys.stdout.write(ch)
            else:
                sys.stdout.write(ch)
                sys.stdout.write("\b \b")

            sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    return result

def get_custom_process_name():
    try:
        process_name = get_filtered_input(
            "┌─╼ 𝗘𝗻𝘁𝗲𝗿 𝗣𝗿𝗼𝗰𝗲𝘀𝘀 𝗡𝗮𝗺𝗲\n└────╼ ❯❯❯ "
        )
    except KeyboardInterrupt:
        print("\n\033[1;31mOperation Cancelled By User.\033[0m")
        sys.exit(1)

    if not process_name or not re.fullmatch(r"[A-Za-z0-9-]+", process_name):
        print("\n\033[1;31mProcess name is invalid.\033[0m")
        sys.exit(1)

    conf_path = f"/etc/supervisor/conf.d/{process_name}.conf"
    if os.path.exists(conf_path):
        print("\n\033[1;31mProcess Name Already Existing.\033[0m")
        sys.exit(1)

    return process_name

def extract_process_name_from_argv():
    binary = os.path.basename(sys.argv[0])
    match = re.fullmatch(r"supercore\[([A-Za-z0-9-]+)\]", binary)
    if match:
        return match.group(1)
    return None

def create_supervisor_conf(command, process_name):
    current_dir = os.getcwd()
    conf_path = f"/etc/supervisor/conf.d/{process_name}.conf"

    conf_content = f"""[program:{process_name}]
directory={current_dir}
command={command}
autostart=true
autorestart=true
stderr_logfile=/var/log/{process_name}.err.log
stdout_logfile=/var/log/{process_name}.out.log
user=root
numprocs=1
"""

    tmp_path = f"/tmp/{process_name}.conf"
    with open(tmp_path, "w") as f:
        f.write(conf_content)

    subprocess.run(["sudo", "mv", tmp_path, conf_path], check=True)

def start_supervisor_process(process_name):
    subprocess.run(["sudo", "supervisorctl", "reread"], check=True)
    subprocess.run(["sudo", "supervisorctl", "update"], check=True)

    print(f"""
\033[1;92mSupervisor Process Started Successfully!

Process Name: {process_name}

Quick Commands:
supervisorctl restart {process_name}
supervisorctl stop {process_name}
supervisorctl start {process_name}

Logs:
tail -f /var/log/{process_name}.out.log
tail -f /var/log/{process_name}.err.log

Config:
nano /etc/supervisor/conf.d/{process_name}.conf
\033[0m
""")

    print("\033[1;33mPress CTRL+C to exit logs view\033[0m\n")

    def tail_logs():
        out = subprocess.Popen(
            ["tail", "-f", f"/var/log/{process_name}.out.log"],
            stdout=subprocess.PIPE
        )
        err = subprocess.Popen(
            ["tail", "-f", f"/var/log/{process_name}.err.log"],
            stdout=subprocess.PIPE
        )

        def stream(pipe):
            for line in iter(pipe.readline, b''):
                sys.stdout.write(line.decode())
                sys.stdout.flush()

        threading.Thread(target=stream, args=(out.stdout,), daemon=True).start()
        threading.Thread(target=stream, args=(err.stdout,), daemon=True).start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            out.terminate()
            err.terminate()

    tail_logs()

def print_version():
    try:
        version = importlib.metadata.version("supercore")
        print(f"\033[1;92mV{version}\033[0m")
    except importlib.metadata.PackageNotFoundError:
        print("\033[1;31mSupercore is not installed properly.\033[0m")

def main():
    check_root()

    if len(sys.argv) < 2:
        print("\033[1;31mSpecify Command To Start Process.\033[0m")
        sys.exit(1)

    if len(sys.argv) == 2 and sys.argv[1] in ["-v", "--v"]:
        print_version()
        sys.exit(0)

    raw_command = " ".join(sys.argv[1:])

    check_supervisor_installed()

    prepared_command = prepare_command(raw_command)

    process_name = extract_process_name_from_argv()

    if process_name:
        conf_path = f"/etc/supervisor/conf.d/{process_name}.conf"
        if os.path.exists(conf_path):
            print("\n\033[1;31mProcess Name Already Existing.\033[0m")
            sys.exit(1)
    else:
        process_name = get_custom_process_name()

    create_supervisor_conf(prepared_command, process_name)
    start_supervisor_process(process_name)

if __name__ == "__main__":
    main()