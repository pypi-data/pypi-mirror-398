def cin():
    a=input().split(' ')
    return a
def cout(a):
    for i in range(0,len(a)-1):
        print(a[i],end=' ')
    print(a[len(a)-1])
import subprocess
def powershell():
    try:
        # 执行powershell命令并捕获输出
        result = subprocess.run(
            ['powershell'],
            capture_output=True,
            text=True
        )
        # 返回标准输出内容
        return result.stdout
    except subprocess.CalledProcessError as e:
        # 命令执行失败时返回错误信息
        return f"Error: {e.stderr}"
    except Exception as e:
        # 处理其他异常
        return f"Exception: {str(e)}"
def cmd(command):
    try:
        # 执行系统命令并捕获输出
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # 返回标准输出内容
        return result.stdout
    except subprocess.CalledProcessError as e:
        # 命令执行失败时返回错误信息
        return f"Error: {e.stderr}"
    except Exception as e:
        # 处理其他异常
        return f"Exception: {str(e)}"    
import ctypes

def is_admin():
    """检查程序是否以管理员权限运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False
import os
def remove(path):
    """删除文件"""
    try:
        os.remove(path)
        return True
    except:
        return False
def write(path,content,mode='w'):
    """写入文件"""
    try:
        with open(path, mode) as file:
            file.write(content)
        return True
    except:
        return False
def read(path):
    try:
        with open(path, 'r') as file:
            content = file.read()
        return content
    except:
        return None
def mkdir(path):
    try:
        os.mkdir(path)
        return True
    except:
        return False
def rmdir(path):
    try:
        os.rmdir(path)
        return True
    except:
        return False
def rename(old_path, new_path):
    try:
        os.rename(old_path, new_path)
        return True
    except:
        return False
def new_file(path):
    try:
        with open(path, 'w') as file:
            return True
    except:
        return False
def copy(src, dst):
    try:
        with open(src, 'r') as file:
            content = file.read()
        with open(dst, 'w') as file:
            file.write(content)
        return True
    except:
        return False
def move(src, dst):
    try:
        os.rename(src, dst)
        return True
    except:
        return False
def list_dir(path):
    try:
        files = os.listdir(path)
        return files
    except:
        return []
        
import zipfile
def unzip(zip_path, extract_path):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        return True
    except:
        return False
def zip(zip_path, files):
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
            for file in files:
                zip_ref.write(file)
        return True
    except:
        return False
def app_open(path):
    try:
        os.startfile(path)
        return True
    except:
        return False
#power
def shutdown():
    try:
        os.system('shutdown -p')
        return True
    except:
        return False
def restart():
    try:
        os.system('shutdown -r')
        return True
    except:
        return False
def choose_to_save(defalt,types,title):
    root=Tk()
    root.withdraw()
    try:
        filedialog.asksaveasfilename(parent=root,defaultextension=defalt,filetypes=types,title=title)
    except:
        return None