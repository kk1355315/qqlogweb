import os
import shutil

# 配置路径
# NTQQ 默认数据路径
SOURCE_DB_PATH = r"C:\Users\1\Documents\Tencent Files\1355315664\nt_qq\nt_db\nt_msg.db"
# 输出文件路径 (当前目录)
OUTPUT_DB_PATH = "nt_msg_clean.db"

def main():
    print("--- NTQQ 数据库预处理工具 ---")
    
    if not os.path.exists(SOURCE_DB_PATH):
        print(f"[!] 错误: 找不到源文件: {SOURCE_DB_PATH}")
        print("请确认您的 QQ 号路径是否正确。")
        return

    print(f"[*] 源文件: {SOURCE_DB_PATH}")
    print(f"[*] 目标文件: {OUTPUT_DB_PATH}")
    
    try:
        with open(SOURCE_DB_PATH, 'rb') as f_src:
            # NTQQ 的数据库文件前 1024 字节是自定义/加密头
            # 标准 SQLite 工具无法识别，必须切除
            print("[*] 正在切除前 1024 字节混淆头...")
            header = f_src.read(1024) 
            
            # 读取剩余数据
            content = f_src.read()
            
        with open(OUTPUT_DB_PATH, 'wb') as f_dst:
            print(f"[*] 正在写入清洗后的数据 ({len(content)} bytes)...")
            f_dst.write(content)
            
        print("[+] 处理完成！")
        print(f"[+] 您现在可以使用 DB Browser for SQLite 打开: {os.path.abspath(OUTPUT_DB_PATH)}")
        print("[!] 记得使用从 hook_key.js 获取的密钥，并设置正确的 SQLCipher 参数。")
        
    except Exception as e:
        print(f"[!] 处理过程中发生错误: {e}")

if __name__ == "__main__":
    main()
