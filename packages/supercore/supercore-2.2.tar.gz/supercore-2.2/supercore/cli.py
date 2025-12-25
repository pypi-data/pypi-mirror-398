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
        subprocess.run(["sudo", "apt", "update", "-o", "Acquire::AllowInsecureRepositories=true"], check=True)
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
    else:
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
            if not ch:
                continue
            if ch in ("\r", "\n"):
                sys.stdout.write("\n")
                sys.stdout.flush()
                break
            if ch == "\x03":
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                raise KeyboardInterrupt
            if ch in ("\x7f", "\b"):
                if len(result) > 0:
                    result = result[:-1]
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
                continue
            if allowed_re.fullmatch(ch):
                result += ch
                sys.stdout.write(ch)
                sys.stdout.flush()
                continue
            sys.stdout.write(ch)
            sys.stdout.flush()
            sys.stdout.write("\b \b")
            sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return result

def get_custom_process_name():
    try:
        process_name = get_filtered_input("┌─╼ 𝗘𝗻𝘁𝗲𝗿 𝗣𝗿𝗼𝗰𝗲𝘀𝘀 𝗡𝗮𝗺𝗲\n└────╼ ❯❯❯ ")
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
    with open(f"/tmp/{process_name}.conf", "w") as f:
        f.write(conf_content)
    subprocess.run(["sudo", "mv", f"/tmp/{process_name}.conf", conf_path], check=True)
    return process_name

def start_supervisor_process(process_name):
    print("\n")
    subprocess.run(["sudo", "supervisorctl", "reread"], check=True)
    subprocess.run(["sudo", "supervisorctl", "update"], check=True)
    print(f"\033[1;92m"
          f"\nSupervisor Process Started Successfully!\n"
          f"Process Name: {process_name}\n\n"
          f"Quick Commands:\n"
          f"supervisorctl restart {process_name}\n"
          f"supervisorctl stop {process_name}\n"
          f"supervisorctl start {process_name}\n\n"
          f"Logs Trace Commands:\n"
          f"tail -f /var/log/{process_name}.out.log\n"
          f"tail -f /var/log/{process_name}.err.log\n\n"
          f"To Manage Config File:\n"
          f"nano /etc/supervisor/conf.d/{process_name}.conf\n"
          f"\033[0m")

    print("\n\033[1;33m--------------------------Press CTRL+C to Exit Logs--------------------------\033[0m\n")

    def tail_logs():
        out_proc = subprocess.Popen(
            ["tail", "-n", "+1", "-f", f"/var/log/{process_name}.out.log"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        err_proc = subprocess.Popen(
            ["tail", "-n", "+1", "-f", f"/var/log/{process_name}.err.log"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        def stream(pipe):
            for line in iter(pipe.readline, b''):
                sys.stdout.write(line.decode())
                sys.stdout.flush()

        t1 = threading.Thread(target=stream, args=(out_proc.stdout,))
        t2 = threading.Thread(target=stream, args=(err_proc.stdout,))
        t1.daemon = True
        t2.daemon = True
        t1.start()
        t2.start()

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            while True:
                sys.stdout.flush()
                if _is_data():
                    ch = sys.stdin.read(1)
                    if ch.lower() == "e":
                        break
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        out_proc.terminate()
        err_proc.terminate()

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
    process_name = get_custom_process_name()
    create_supervisor_conf(prepared_command, process_name)
    start_supervisor_process(process_name)

if __name__ == "__main__":
    main()