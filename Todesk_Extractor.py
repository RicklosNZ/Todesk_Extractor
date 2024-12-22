import subprocess
import os
import re
from datetime import datetime
from tkinter import messagebox

# 通过进程获取todesk的PID
def get_PID():
    try:
        result = subprocess.run('tasklist | find /I "ToDesk.exe"', shell=True, capture_output=True, text=True)
        output_lines = result.stdout.strip().split('\n')
        console_data = []
        pid = -1
        for line in output_lines:
            parts = line.split()
            console_data.append(parts)

        for i in console_data:
            if i[2] == "Console":
                pid = i[1]
                break

        return pid
    except subprocess.CalledProcessError as e:
        messagebox.showerror("错误", f"获取PID时执行命令出错，错误信息: {e.stderr}")
        return -1
    except Exception as e:
        messagebox.showerror("错误", f"获取PID时出现未知错误: {str(e)}")
        return -1

# 从内存中获取todesk信息
def dump_Process(pid):
    command = f'procdump64.exe -accepteula -ma {pid}'
    try:
        subprocess.run(command, shell=True, check=False)
    except FileNotFoundError:
        messagebox.showerror("错误", "procdump64.exe程序未找到，请确保该程序在系统环境变量可访问的路径下")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("错误", f"执行转储进程命令出错，错误信息: {e.stderr}")
    except Exception as e:
        messagebox.showerror("错误", f"转储进程时出现未知错误: {str(e)}")

# 获取当前日期
def get_Current_Date():
    try:
        current_date = datetime.now().date()
        return current_date.strftime('%Y%m%d')
    except Exception as e:
        messagebox.showerror("错误", f"获取当前日期时出现错误: {str(e)}")
        return ""

# 从当前根目录下查找刚刚下载下来的todesk文件(.dmp文件)
def find_dmp_file():
    dmp_files = []
    current_dir = os.getcwd()
    for file in os.listdir(current_dir):
        if file.endswith('.dmp'):
            file_path = os.path.join(current_dir, file)
            dmp_files.append(file_path)
    if len(dmp_files) == 0:
        messagebox.showinfo("提示", "当前目录下未找到.dmp文件")
        return None
    elif len(dmp_files) > 1:
        messagebox.showinfo("提示", "当前目录下找到多个.dmp文件")
        return None
    else:
        return dmp_files[0]

# kmp算法数据结构，计算next
def compute_next(pattern):
    m = len(pattern)
    next = [0] * m
    j = 0
    for i in range(1, m):
        while j > 0 and pattern[i]!= pattern[j]:
            j = next[j - 1]
        if pattern[i] == pattern[j]:
            j += 1
        next[i] = j
    return next

# kmp算法实现
def kmp_search(text, pattern):
    n = len(text)
    m = len(pattern)
    next = compute_next(pattern)
    j = 0
    for i in range(0, n):
        while j > 0 and text[i]!= pattern[j]:
            j = next[j - 1]
        if text[i] == pattern[j]:
            j += 1
        if j == m:
            return i - m + 1
    return -1

# 阅读todesk信息，查找到日期出现的地点，并且以其前10000到其后10000构建一个切片，并且将不能解析的字符替换为#
def read_Hex(file_path, date):
    try:
        with open(file_path, 'rb') as file:
            content = file.read()  # content内涵的字节数大概是十亿规模的

        data_segment = content  # 准备开始字符串匹配算法
        index = kmp_search(content, date)
        if index!= -1:
            data_segment = content[max(0, index - 10000):index + 10000]
        else:
            print("查询不到当前所在日期的位置")
            return ""

        hex_list = [format(byte, '02x') for byte in data_segment]
        hex_data = " ".join(hex_list)

        decimal_list = [int(hex_value, 16) for hex_value in hex_data.split()]

        data = ""
        for decimal in decimal_list:
            if (decimal >= 33 and decimal <= 126):
                data += chr(decimal)
            else:
                data += ("#")
        return data
    except FileNotFoundError:
        print(f"读取文件 {file_path} 时出错，文件不存在")
        return ""
    except Exception as e:
        print(f"读取十六进制数据时出现未知错误: {str(e)}")
        return ""

# 通过#号分割可读数据，将其转储到一个列表中
def store_Data(msg):
    result = []
    temp = ""
    for char in msg:
        if char == "#":
            if not temp.endswith("#"):
                temp += char
            else:
                continue
        else:
            temp += char
        if temp.endswith("#"):
            segment = temp.rstrip("#")
            if segment:
                result.append(segment)
            temp = ""
    if temp:
        result.append(temp)

    return result

# 用完之后删除.dmp文件，保护信息
def delete_dmp_file(file_path):
    try:
        os.remove(file_path)
        # messagebox.showinfo("提示", "已成功删除文件！")
    except FileNotFoundError:
        messagebox.showerror("错误", f"删除文件 {file_path} 时出错，文件不存在")
    except Exception as e:
        messagebox.showerror("错误", f"删除.dmp文件时出现未知错误: {str(e)}")

# 获取临时密钥的逻辑：从日期index出发，向前找，最近的一个8位数字字母组合就是临时密钥
def get_tempKey(stored_msg,index):
    # v2.4更新 修复了原有的查找逻辑错误，根据临时密码必然既有数字又有字母来更精确地查找，防止在中间误查到日期等8位全数字的字符串
    pattern = r'^(?=.*[a-zA-Z])(?=.*[0-9])[a-zA-Z0-9]{8}$'  
    for i in range(index-1,-1,-1):
        result = re.match(pattern, stored_msg[i])
        if result:
            return stored_msg[i]
    return None

# 获取安全密钥的逻辑:从日期index出发，向前找，最近的一个8位数字字母组合的后一个就是安全密钥
def get_safeKey(stored_msg,index):
    # v2.4更新 修复了原有的查找逻辑错误，根据临时密码必然既有数字又有字母来更精确地查找，防止在中间误查到日期等8位全数字的字符串
    pattern = r'^(?=.*[a-zA-Z])(?=.*[0-9])[a-zA-Z0-9]{8}$'  
    for i in range(index-1,-1,-1):
        result = re.match(pattern, stored_msg[i])
        if result:
            sec_pattern = r'^[a-zA-Z0-9]{8,}'  # 如果用户设置了安全密码，字符串肯定是一个八位以上的字符串，否则就是没设置
            sec_result=re.match(sec_pattern, stored_msg[i+1])
            if sec_result:
                return stored_msg[i+1]
            else:
                return "未设置"
    return None

# 获取设备ID的逻辑：从日期index出发，向前找，最近的一个9位数字就是设备ID
def get_deviceId(stored_msg,index):
    pattern = r'^\d{9}$'
    for i in range(index-1,-1,-1):
        result = re.match(pattern, stored_msg[i])
        if result:
            return stored_msg[i]
    return None

# 获取手机号的逻辑：从日期index出发，向后找，最近的一个11位数字就是手机号
def get_phone(stored_msg,index):
    pattern = r'^\d{11}$'
    for i in range(index,len(stored_msg)):
        result = re.match(pattern, stored_msg[i])
        if result:
            return stored_msg[i]
    return None



# 最后将信息保存到本地的txt文档中，没有传参，需要最后直接调用
def save_msg():
    result_text = f"设备代码：{device_id}\n临时密码：{temp_key}\n安全密码：{safe_key}\n手机号码：{phone}\n"
    file_name = datetime.now().strftime('%Y%m%d%H%M%S') + "-todesk临时代码.txt"
    try:
        with open(file_name, 'w', encoding='utf-8') as f:
            f.write(result_text)
        messagebox.showinfo("提示", "程序结果已保存到根目录下")
    except IOError as e:
        messagebox.showerror("错误", f"保存信息到文件时出现I/O错误: {str(e)}")
    except Exception as e:
        messagebox.showerror("错误", f"保存信息到文件时出现未知错误: {str(e)}")


if __name__ == "__main__":
    try:
        messagebox.showinfo("声明", "仅供学习使用，严禁用于非法用途，后果自负!")
        pid = get_PID()  # 获取todesk的PID
        dump_Process(pid)  # 根据PID将进程中的数据转储到本地
        date = get_Current_Date()  # 自动获取当前的日期

        file_path = find_dmp_file() #查找当前的.dmp文件
        if file_path:   # 如果有文件（且是唯一的），继续
            date_byte = bytes(date, 'utf-8')    # 创建一个byte变量，将日期转化为byte数据，方便之后kmp匹配
            read_msg = read_Hex(file_path, date_byte)   # 通过kmp算法找到日期位置，制作切片
            stored_msg = store_Data(read_msg)       # 储存数据

            #print(stored_msg)

            delete_dmp_file(file_path)  # 获取信息之后删除原来的.dmp文件
            index = stored_msg.index(date)  # 找到日期所在的索引号
            if index:
                temp_key = get_tempKey(stored_msg,index)
                safe_key = get_safeKey(stored_msg,index)
                device_id = get_deviceId(stored_msg,index)
                phone = get_phone(stored_msg,index)

                messagebox.showinfo("信息", f"设备代码：{device_id}\n临时密码：{temp_key}\n安全密码：{safe_key}\n手机号码：{phone}\n")

                #print(stored_msg[index-100:index+100])

                save_msg()  # 把信息保存到本地的txt文本中

    except Exception as e:
        messagebox.showerror("错误", f"程序主流程出现异常，错误信息: {str(e)}，请检查相关设置或数据，或联系制作者！")