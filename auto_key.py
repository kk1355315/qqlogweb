import frida
import sys
import time
import threading

# 自动获取 PID
def get_qq_pid():
    import ctypes
    # 使用 frida 的 device.enumerate_processes() 可能更方便
    # 但为了稳健，我们先尝试 attach 到名字
    pass

def on_message(message, data):
    if message['type'] == 'send':
        payload = message['payload']
        if payload['type'] == 'key':
            print(f"\n[SUCCESS] KEY FOUND!")
            print(f"Key: {payload['key']}")
            print(f"DB:  {payload['db_name']}")
            print(f"Source: {payload['module_name']} ({payload['module_name']})")
            print("\nWriting key to 'key.txt'...")
            with open("key.txt", "w") as f:
                f.write(payload['key'])
            # 拿到 Key 后退出
            print("[*] Exiting...")
            sys.exit(0)
        elif payload['type'] == 'log':
            print(f"[JS] {payload['content']}")
        elif payload['type'] == 'error':
            print(f"[JS Error] {payload['content']}")
    else:
        print(message)

def main():
    print("[*] Waiting for QQ process...")
    try:
        # 尝试连接到本地设备
        device = frida.get_local_device()
        
        # 查找 QQ 进程
        target_process = None
        processes = device.enumerate_processes()
        
        # 策略：找内存占用最大的 QQ.exe
        qq_procs = [p for p in processes if p.name.lower() == "qq.exe"]
        
        if not qq_procs:
            print("[-] QQ.exe not found. Please start QQ.")
            return

        # 简单的启发式：通常主进程 ID 较小或者有特定的特征，
        # 但这里我们尝试全部 hook 或者让用户指定？
        # 既然前面手动失败了，我们这里尝试最暴力的：Hook 那个内存最大的（如果是 Python API 能拿到内存信息的话）
        # Frida API 的 Process 对象没有内存信息。
        # 我们只能尝试 Attach 所有的 QQ 进程，或者尝试之前识别出的 PID 30652 (如果它还在)
        
        # 为了“自主调试”，我们尝试 Attach 到列表中的第一个，如果不成功就下一个？
        # 或者同时 Attach 所有？ (可能导致冲突)
        
        # 既然我们有 tasklist，我们调用一下系统命令来辅助决策
        import subprocess
        import re
        
        cmd = 'tasklist /FI "IMAGENAME eq QQ.exe" /FO CSV /NH'
        output = subprocess.check_output(cmd, shell=True).decode('gbk', errors='ignore')
        
        # 解析 CSV: "QQ.exe","30652","Console","1","295,864 K"
        # 我们需要找到内存最大的那个 PID
        
        max_mem = -1
        target_pid = -1
        
        for line in output.splitlines():
            if "QQ.exe" in line:
                parts = line.split('","')
                if len(parts) >= 5:
                    pid = int(parts[1])
                    mem_str = parts[4].replace(' K"', '').replace(',', '')
                    mem = int(mem_str)
                    
                    if mem > max_mem:
                        max_mem = mem
                        target_pid = pid
        
        if target_pid == -1:
            print("[-] Could not determine main QQ process.")
            target_pid = qq_procs[0].pid # Fallback
        
        print(f"[*] Targeting QQ Process PID: {target_pid} (Mem: {max_mem} K)")
        
        session = device.attach(target_pid)
        print(f"[+] Attached to PID {target_pid}")
        
        with open("hook_key.js", "r", encoding="utf-8") as f:
            script_code = f.read()
            
        script = session.create_script(script_code)
        script.on('message', on_message)
        script.load()
        
        print("[*] Script loaded. Please interact with QQ (Click chats) to trigger key...")
        
        # 保持运行 (30秒超时)
        timeout = 60
        start_time = time.time()
        try:
            while True:
                if time.time() - start_time > timeout:
                    print(f"[-] Timeout ({timeout}s). No key detected.")
                    print("[-] Please try running the script again and clicking QQ faster.")
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            print("[*] Detaching...")
            session.detach()
            
    except frida.ProcessNotFoundError:
        print("[-] Process not found.")
    except Exception as e:
        print(f"[-] Error: {e}")

if __name__ == "__main__":
    main()
