import os
import subprocess
import sys

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    os.chdir("../")
    sys.dont_write_bytecode = True
    flag = True
    process: subprocess.Popen
    restart = False
    while True:
        if flag:
            flag = False
            print("### RUN SUBPROCESS ###")
            args = ["python", "./src/main.py"]
            if restart:
                args.append("RESTART")
            process = subprocess.Popen(
                args=args,
                encoding="utf-8",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=os.getcwd(),
                env=os.environ,
            )
            print(f"<{process.pid}>:{process.args}")

        sys.stdout.write(process.stdout.readline())
        code = process.poll()

        if code is not None:
            print("### EXIT SUB PROCESS ###")
            if code != 233:
                sys.exit(process.returncode)
            flag = True
            restart = True
