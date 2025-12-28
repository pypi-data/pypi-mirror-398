import subprocess
import os
import time
import json
from pathlib import Path
import logging
import logging.handlers
import sys
import argparse
import signal
import re
import grpc
import uuid

# 导入生成的gRPC代码
from . import sysom_signal_pb2
from . import sysom_signal_pb2_grpc

def is_valid_uuid(uuid_string):
    """
    验证字符串是否为有效的UUID格式
    """
    try:
        uuid_obj = uuid.UUID(uuid_string)
        return str(uuid_obj) == uuid_string.lower()
    except (TypeError, ValueError, AttributeError):
        return False

# 全局变量
logger = None
running = True

def setup_logging(log_file='/var/log/sysom-pai-client.log', daemon_mode=False, log_level='INFO'):
    """设置日志配置，支持日志轮转"""
    # 清除现有的处理器
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # 创建logger
    logger_instance = logging.getLogger('sysom_pai_client')
    
    # 设置日志级别
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger_instance.setLevel(level)
    
    # 创建带轮转功能的文件处理器
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5  # 保留5个备份文件
    )
    file_handler.setLevel(level)
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(formatter)
    
    # 清除现有处理器并添加新的处理器
    logger_instance.handlers.clear()
    logger_instance.addHandler(file_handler)
    logger_instance.propagate = False  # 防止日志传播到根logger
    
    # 如果不是守护进程模式，也添加控制台输出
    if not daemon_mode:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger_instance.addHandler(console_handler)
    
    return logger_instance

def daemonize(pid_file=None):
    """将进程转为守护进程"""
    try:
        pid = os.fork()
        if pid > 0:
            # 父进程退出
            sys.exit(0)
    except OSError as e:
        print("fork failed: {}".format(e))
        sys.exit(1)
    
    # 修改子进程环境
    os.chdir("/")
    os.setsid()
    os.umask(0)
    
    # 第二次fork
    try:
        pid = os.fork()
        if pid > 0:
            # 第二个父进程退出
            sys.exit(0)
    except OSError as e:
        print("Second fork failed: {}".format(e))
        sys.exit(1)
    
    # 重定向标准输入、输出、错误
    sys.stdin.flush()
    sys.stdout.flush()
    sys.stderr.flush()
    
    with open('/dev/null', 'r') as dev_null_r:
        os.dup2(dev_null_r.fileno(), sys.stdin.fileno())
    
    with open('/var/log/sysom-pai-client.log', 'a') as log_file:
        os.dup2(log_file.fileno(), sys.stdout.fileno())
        os.dup2(log_file.fileno(), sys.stderr.fileno())
    
    # 写入PID文件
    if pid_file:
        with open(pid_file, 'w') as f:
            f.write(str(os.getpid()))

def signal_handler(signum, frame):
    """信号处理函数"""
    global running
    if logger:
        logger.info("Received signal {}, preparing to exit...".format(signum))
    running = False

def get_hostname():
    """获取当前主机名"""
    try:
        result = subprocess.run(["hostname"], capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return os.environ.get("HOSTNAME", "")

def check_logtail_process():
    """检查是否有ilogtail进程在运行"""
    try:
        # 使用更兼容的方式
        result = subprocess.run(["/usr/bin/pgrep", "ilogtail"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if logger:
            logger.debug("pgrep ilogtail result: returncode={}, stdout={}, stderr={}".format(
                result.returncode, result.stdout.decode() if result.stdout else '', 
                result.stderr.decode() if result.stderr else ''))
        return result.returncode == 0
    except FileNotFoundError:
        # pgrep命令不存在
        if logger:
            logger.debug("pgrep command not found")
        else:
            print("pgrep command not found")
        return False
    except Exception as e:
        if logger:
            logger.debug("Error running pgrep ilogtail: {}".format(str(e)))
        else:
            print("Error running pgrep ilogtail: {}".format(str(e)))
        return False

def get_logtail_config():
    """获取ilogtail配置参数"""
    # 从环境变量获取配置，提供默认值
    user_id = os.environ.get("LOGTAIL_USER_ID", "1808078950770264")
    user_defined_id = os.environ.get("LOGTAIL_USER_DEFINED_ID", "pai_user-defined-1")
    return user_id, user_defined_id

def configure_logtail_user_identity():
    """配置ilogtail用户标识"""
    # 获取配置参数
    user_id, user_defined_id = get_logtail_config()
    
    # 配置用户标识目录
    user_dir = "/etc/ilogtail/users"
    os.makedirs(user_dir, exist_ok=True)
    user_file = os.path.join(user_dir, user_id)
    # 只创建空文件，不写入内容
    open(user_file, "w").close()
        
    # 配置用户自定义标识
    user_defined_file = "/etc/ilogtail/user_defined_id"
    
    try:
        # 检查文件是否存在且包含目标标识
        if os.path.exists(user_defined_file):
            with open(user_defined_file, "r") as f:
                current_content = f.read()
                
            # 检查目标标识是否已存在于文件中
            # 这里假设标识是按行存储的
            existing_ids = [line.strip() for line in current_content.splitlines() if line.strip()]
            
            if user_defined_id in existing_ids:
                logger.info("ilogtail user identity already configured, User ID: {}, Custom ID: {}".format(user_id, user_defined_id))
                return
                
            # 如果标识不存在，将其追加到文件中
            with open(user_defined_file, "a") as f:
                # 如果文件不为空且最后一行没有换行符，先添加换行符
                if current_content and not current_content.endswith('\n'):
                    f.write('\n')
                f.write(user_defined_id + '\n')
        else:
            # 文件不存在，创建并写入标识
            with open(user_defined_file, "w") as f:
                f.write(user_defined_id + '\n')
                
    except Exception as e:
        # 如果出现异常，尝试重新写入（保持原有行为）
        logger.warning("Error checking or updating user defined identity: {}, rewriting configuration".format(str(e)))
        with open(user_defined_file, "w") as f:
            f.write(user_defined_id + '\n')
    
    logger.info("ilogtail user identity configuration completed, User ID: {}, Custom ID: {}".format(user_id, user_defined_id))

def install_and_configure_logtail(region_id, network_mode="internal"):
    """安装并配置ilogtail日志收集组件"""
    logger.info("Starting to install ilogtail, Region: {}, Network Mode: {}".format(region_id, network_mode))
    
    # 下载logtail安装脚本
    if network_mode == "internal":
        download_url = "http://logtail-release-{}.oss-{}-internal.aliyuncs.com/linux64/logtail.sh".format(region_id, region_id)
    else:
        download_url = "http://logtail-release-{}.oss-{}.aliyuncs.com/linux64/logtail.sh".format(region_id, region_id)
    
    # 下载安装脚本
    cmd_wget = ["wget", download_url, "-O", "logtail.sh"]
    result = subprocess.run(cmd_wget)
    if result.returncode != 0:
        logger.error("Failed to download logtail.sh")
        return result.returncode
    
    # 添加执行权限
    os.chmod("logtail.sh", 0o755)
    
    # 安装logtail
    install_suffix = "{}-{}".format(region_id, network_mode) if network_mode != "internal" else region_id
    cmd_install = ["./logtail.sh", "install", install_suffix]
    result = subprocess.run(cmd_install)
    if result.returncode != 0:
        logger.error("Failed to install logtail")
        return result.returncode
    
    # 配置用户标识
    configure_logtail_user_identity()
    
    logger.info("ilogtail installation and configuration completed")
    return 0

def update_logtail_config():
    """更新ilogtail配置文件，添加max_read_buffer_size配置项"""
    config_path = "/usr/local/ilogtail/ilogtail_config.json"
    
    if not os.path.exists(config_path):
        logger.warning("ilogtail config file not found: {}".format(config_path))
        return False
    
    try:
        # 读取现有配置
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # 检查配置是否已经包含目标项且值相同
        current_value = config_data.get("max_read_buffer_size")
        target_value = 8388608
        
        if current_value == target_value:
            logger.info("ilogtail config already has max_read_buffer_size = {}, no update needed".format(target_value))
            return False  # 配置未变化，无需重启
        
        # 更新配置
        config_data["max_read_buffer_size"] = target_value
        
        # 写回配置文件
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
        
        logger.info("Updated ilogtail config with max_read_buffer_size: {}".format(target_value))
        return True  # 配置已更新，需要重启
        
    except json.JSONDecodeError as e:
        logger.error("Failed to parse ilogtail config JSON: {}".format(str(e)))
        return False
    except Exception as e:
        logger.error("Failed to update ilogtail config: {}".format(str(e)))
        return False

def restart_logtail_if_needed():
    """如果ilogtail配置已更新，则重启ilogtail服务"""
    try:
        logger.info("Restarting ilogtail service...")
        
        # 使用 stdout 和 stderr 参数替代 capture_output
        result = subprocess.run(["sudo", "/etc/init.d/ilogtaild", "restart"], 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                              universal_newlines=True)
        
        if result.returncode != 0:
            logger.error("Failed to restart ilogtail: {}".format(result.stderr))
            return False
        
        logger.info("ilogtail service restarted successfully")
        return True
        
    except Exception as e:
        logger.error("Exception when restarting ilogtail: {}".format(str(e)))
        return False

def setup_logtail_if_needed():
    """检查并设置ilogtail"""
    config_updated = False
    
    if check_logtail_process():
        logger.info("Detected ilogtail process is running, configuring user identity...")
        configure_logtail_user_identity()
        
        # 更新配置并检查是否需要重启
        config_updated = update_logtail_config()
    else:
        logger.info("No ilogtail process detected, starting installation...")
        # 尝试从环境变量获取区域信息
        region_id = os.environ.get("REGION_ID") or os.environ.get("REGION") or "cn-wulanchabu"
        network_mode = os.environ.get("NETWORK_MODE") or "internal"
        install_and_configure_logtail(region_id, network_mode)
        
        # 安装完成后更新配置
        config_updated = update_logtail_config()
    
    # 如果配置已更新，重启ilogtail服务
    if config_updated:
        restart_logtail_if_needed()

def sanitize_log_message(message):
    """清理日志消息中的特殊字符"""
    # 移除或替换不可打印的字符
    sanitized = re.sub(r'[^\x20-\x7E\x0A\x0D]', '.', message)
    return sanitized

def send_grpc_request(address, method="GetSignal"):
    """向指定地址发送gRPC请求"""
    try:
        # 解析地址
        if ':' in address:
            host, port = address.rsplit(':', 1)
            port = int(port)
        else:
            host = address
            port = 23456  # 默认端口
        
        # 创建gRPC通道
        channel = grpc.insecure_channel('{}:{}'.format(host, port))
        
        # 创建服务stub
        stub = sysom_signal_pb2_grpc.SysomServiceStub(channel)
        
        # 构造请求数据
        request = sysom_signal_pb2.SysomRequest()
        # 添加客户端标识
        request.client_id = os.environ.get("POD_NAME", get_hostname())
        # 添加时间戳
        request.timestamp = int(time.time())
        
        logger.debug("Sending gRPC request to {} using method {}".format(address, method))
        
        # 根据方法调用不同的gRPC方法
        if method == "GetSignal":
            response = stub.GetSignal(request, timeout=5)
        elif method == "ReportResult":
            response = stub.ReportResult(request, timeout=5)
        
        # 验证 diagnosis_id 是否为有效的UUID格式
        diagnosis_id_str = response.diagnosis_id if response.diagnosis_id else ""
        if diagnosis_id_str and not is_valid_uuid(diagnosis_id_str):
            logger.warning("Invalid UUID format for diagnosis_id: {}, setting to empty".format(diagnosis_id_str))
            response.diagnosis_id = ""
        
        logger.debug("gRPC response: status={}, signal={}, diagnosis_id={}".format(
            response.status, response.signal, response.diagnosis_id))
        
        return response.status, response.signal, response.diagnosis_id, response.options, response.timestamp
        
    except grpc.RpcError as e:
        # 简化错误日志，使用DEBUG级别
        if logger:
            logger.debug("gRPC error {}: {}".format(e.code().name, address))
        return str(e.code().name), "", "", "", "", 0
    except Exception as e:
        error_msg = sanitize_log_message(str(e))
        import traceback
        if logger:
            logger.debug("gRPC request error: {}\nFull traceback:\n{}".format(
                error_msg, 
                traceback.format_exc()
            ))
        return "ERROR", "", error_msg, "", "", 0

def write_signal_file(signal_dir="/pai_aimaster/job/sysom/", signal_type="", diagnosis_id=""):
    """在共享目录中写入信号文件"""
    try:
        # 验证 diagnosis_id 是否为有效的UUID格式
        if diagnosis_id and not is_valid_uuid(diagnosis_id):
            logger.warning("Invalid UUID format for diagnosis_id in write_signal_file: {}, ignoring".format(diagnosis_id))
            diagnosis_id = ""  # 设置为空字符串
        
        # 确保目录存在
        Path(signal_dir).mkdir(parents=True, exist_ok=True)
        
        # 根据信号类型和诊断ID创建文件
        if signal_type and signal_type != "":
            if diagnosis_id and diagnosis_id != "":
                signal_file_path = os.path.join(signal_dir, "{}-{}".format(signal_type, diagnosis_id))
            else:
                signal_file_path = os.path.join(signal_dir, signal_type)
            
            with open(signal_file_path, "w") as f:
                f.write("Signal received at {}\n".format(time.strftime('%Y-%m-%d %H:%M:%S')))
                f.write("Signal Type: {}\n".format(signal_type))
                if diagnosis_id and diagnosis_id != "":
                    f.write("Diagnosis ID: {}\n".format(diagnosis_id))
            
            logger.info("Signal file written: {}".format(signal_file_path))
            return signal_file_path
        else:
            logger.debug("Empty signal type, skipping file creation")
            return None
            
    except Exception as e:
        logger.error("Failed to write signal file: {}".format(str(e)))
        return None

def check_and_report_completed_diagnostics(signal_dir="/pai_aimaster/job/sysom/"):
    """检查信号文件是否已被删除，并报告已完成的诊断"""
    try:
        if not os.path.exists(signal_dir):
            return
            
        # 遍历信号目录中的所有文件
        for filename in os.listdir(signal_dir):
            # 检查是否符合命名规则
            if "-" in filename and filename.startswith(("SYSOM_JOB_SLOW_DIAGNOSIS_SIGNAL", 
                                                       "SYSOM_JOB_HANG_DIAGNOSIS_SIGNAL", 
                                                       "SYSOM_JOB_PROFILING_DIAGNOSIS_SIGNAL")):
                # 提取信号类型和诊断ID
                parts = filename.split("-", 1)
                signal_type = parts[0]
                diagnosis_id = parts[1] if len(parts) > 1 else ""
                
                # 检查文件是否还存在
                file_path = os.path.join(signal_dir, filename)
                if not os.path.exists(file_path):
                    # 文件已被删除，表示诊断完成，需要报告给服务器
                    report_diagnosis_result(signal_type, diagnosis_id, "SUCCESS", {
                        "status": "SUCCESS", 
                        "message": "Signal processed successfully",
                        "elapsed_time": 0  # 由于不知道开始时间，这里设置为0
                    })
                    
    except Exception as e:
        logger.error("Error checking completed diagnostics: {}".format(str(e)))
def report_diagnosis_result(signal_type, diagnosis_id, status, result_data):
    """向服务器报告诊断结果"""
    aimaster_addr = os.environ.get("AIMASTER_ADDR")
    if not aimaster_addr:
        logger.error("AIMASTER_ADDR not set, cannot report result")
        return
    
    try:
        # 构造诊断结果JSON
        result_json = {
            "client_id": os.environ.get("POD_NAME", get_hostname()),  # 添加client_id字段
            "signal_type": signal_type,
            "diagnosis_id": diagnosis_id,
            "status": status.upper(),  # 将状态转换为大写 (SUCCESS, TIMEOUT等)
            "message": result_data.get("message", ""),
            "elapsed_time": result_data.get("elapsed_time", 0)  # 添加elapsed_time字段
        }
        
        # 将结果转换为JSON字符串，以便通过gRPC发送
        result_json_str = json.dumps(result_json)
        
        logger.info("Reporting diagnosis result for {}-{}: status={}, result={}".format(
            signal_type, diagnosis_id, status, result_json))
        
        # 发送报告结果请求，将诊断结果放在diagnosis_result字段中
        status_code, _, _, _, _ = send_grpc_request_with_result(aimaster_addr, result_json_str)
        
        if status_code == "OK":
            logger.info("Successfully reported diagnosis result for {}-{}".format(signal_type, diagnosis_id))
        else:
            logger.warning("Failed to report diagnosis result: status={}".format(status_code))
    except Exception as e:
        logger.error("Exception reporting diagnosis result: {}".format(str(e)))

def send_grpc_request_with_result(address, result_data_json):
    """向指定地址发送包含诊断结果的gRPC请求"""
    try:
        # 解析地址
        if ':' in address:
            host, port = address.rsplit(':', 1)
            port = int(port)
        else:
            host = address
            port = 23456  # 默认端口
        
        # 创建gRPC通道
        channel = grpc.insecure_channel('{}:{}'.format(host, port))
        
        # 创建服务stub
        stub = sysom_signal_pb2_grpc.SysomServiceStub(channel)
        
        # 构造请求数据
        request = sysom_signal_pb2.SysomRequest()
        # 添加客户端标识
        request.client_id = os.environ.get("POD_NAME", get_hostname())
        # 添加时间戳
        request.timestamp = int(time.time())
        # 添加诊断结果到diagnosis_result字段（这是proto定义中的第3个字段）
        request.diagnosis_result = result_data_json
        
        logger.debug("Sending gRPC request with result to {}: {}".format(address, result_data_json))
        
        # 调用ReportResult方法
        response = stub.ReportResult(request, timeout=5)
        
        logger.debug("gRPC ReportResult response: status={}, signal={}, diagnosis_id={}".format(
            response.status, response.signal, response.diagnosis_id))
        
        return response.status, response.signal, response.diagnosis_id, response.options, response.timestamp
        
    except grpc.RpcError as e:
        if logger:
            logger.debug("gRPC error {}: {}".format(e.code().name, address))
        return str(e.code().name), "", "", "", "", 0
    except Exception as e:
        error_msg = sanitize_log_message(str(e))
        import traceback
        if logger:
            logger.debug("gRPC request error: {}\nFull traceback:\n{}".format(
                error_msg, 
                traceback.format_exc()
            ))
        return "ERROR", "", error_msg, "", "", 0

# 在全局变量部分添加
class SignalState:
    IDLE = "idle"           # 空闲状态，可以接收新信号
    PROCESSING = "processing"  # 正在处理信号
    COMPLETED = "completed"   # 信号处理完成

current_signal_state = SignalState.IDLE
current_signal_info = {
    "signal_type": "",
    "diagnosis_id": "",
    "file_path": "",
    "start_time": 0  # 添加开始处理时间戳
}

def check_signal_consumed(signal_dir="/pai_aimaster/job/sysom/"):
    """检查当前信号是否已被消费（信号文件是否已被删除）"""
    global current_signal_info, current_signal_state
    
    if current_signal_state != SignalState.PROCESSING:
        return True  # 不在处理状态，无需检查
    
    # 检查信号文件是否还存在
    if current_signal_info["file_path"] and os.path.exists(current_signal_info["file_path"]):
        # 检查是否超时（5分钟 = 300秒）
        elapsed_time = time.time() - current_signal_info["start_time"]
        if elapsed_time > 300:  # 5分钟超时
            logger.warning("Signal timeout: {}-{} after {} seconds, removing file and reporting timeout".format(
                current_signal_info["signal_type"], 
                current_signal_info["diagnosis_id"],
                elapsed_time))
            
            # 删除信号文件
            try:
                os.remove(current_signal_info["file_path"])
                logger.info("Removed timeout signal file: {}".format(current_signal_info["file_path"]))
            except Exception as e:
                logger.error("Failed to remove timeout signal file {}: {}".format(
                    current_signal_info["file_path"], str(e)))
            
            # 报告超时异常结果
            report_diagnosis_result(
                current_signal_info["signal_type"], 
                current_signal_info["diagnosis_id"],
                "TIMEOUT",  # 状态为超时异常，使用大写
                {"status": "TIMEOUT", "message": "Signal not consumed within 5 minutes", "elapsed_time": elapsed_time}
            )
            
            # 清除当前信号信息并恢复空闲状态
            current_signal_info = {
                "signal_type": "",
                "diagnosis_id": "",
                "file_path": "",
                "start_time": 0
            }
            current_signal_state = SignalState.IDLE
            return True
        
        return False  # 信号尚未被消费
    
    # 信号已被消费，更新状态
    current_signal_state = SignalState.COMPLETED
    elapsed_time = time.time() - current_signal_info["start_time"]  # 计算实际消费时间
    logger.info("Signal consumed: {}-{}, elapsed time: {} seconds".format(
        current_signal_info["signal_type"], 
        current_signal_info["diagnosis_id"],
        elapsed_time))
    
    # 报告诊断完成（正常状态）
    report_diagnosis_result(
        current_signal_info["signal_type"], 
        current_signal_info["diagnosis_id"],
        "SUCCESS",  # 状态为成功，使用大写
        {"status": "SUCCESS", "message": "Signal processed successfully", "elapsed_time": elapsed_time}
    )
    
    # 清除当前信号信息并恢复空闲状态
    current_signal_info = {
        "signal_type": "",
        "diagnosis_id": "",
        "file_path": "",
        "start_time": 0
    }
    current_signal_state = SignalState.IDLE
    return True

def main_loop(aimaster_addr):
    """主循环：每秒轮询AIMASTER_ADDR进行gRPC调用"""
    global running, current_signal_info, current_signal_state
    logger.info("Starting to listen to {} signals via gRPC...".format(aimaster_addr))
    
    while running:
        try:
            # 检查当前信号是否已被消费或超时
            if not check_signal_consumed():
                # 信号尚未被消费，等待一段时间再检查
                time.sleep(1)
                continue
            
            # 检查已完成的诊断并报告
            check_and_report_completed_diagnostics()
            
            # 只有在空闲状态才请求新信号
            if current_signal_state == SignalState.IDLE:
                # 发送gRPC请求获取Sysom信号
                status, signal_type, diagnosis_id, options, timestamp = send_grpc_request(aimaster_addr)
                
                # 验证 diagnosis_id 是否为有效的UUID格式
                if diagnosis_id and not is_valid_uuid(diagnosis_id):
                    logger.warning("Invalid UUID format for received diagnosis_id: {}, ignoring".format(diagnosis_id))
                    diagnosis_id = ""  # 设置为空字符串
                
                # 如果状态为OK且有信号，则处理信号
                if status == "OK" and signal_type:
                    logger.info("Received Sysom signal: {}, diagnosis_id: {}".format(
                        signal_type, diagnosis_id))
                    file_path = write_signal_file(signal_type=signal_type, diagnosis_id=diagnosis_id)
                    
                    # 更新信号信息和状态，记录开始时间
                    current_signal_info = {
                        "signal_type": signal_type,
                        "diagnosis_id": diagnosis_id,
                        "file_path": file_path,
                        "start_time": time.time()  # 记录开始处理时间
                    }
                    current_signal_state = SignalState.PROCESSING
                elif status != "OK" and status != "NOT_FOUND":
                    logger.debug("Received status: {}, signal: {}".format(status, signal_type))
            
            # 等待1秒后继续下一次轮询
            time.sleep(1)
            
        except Exception as e:
            error_msg = sanitize_log_message(str(e))
            logger.error("Exception occurred in main loop: {}".format(error_msg))
            time.sleep(1)  # 出现异常时也等待1秒

def create_prof_aifg_structure():
    """创建prof_aifg所需的目录结构和软链接"""
    
    # 定义路径
    signal_dir = "/pai_aimaster/job/sysom/"
    prof_aifg_file = os.path.join(signal_dir, "prof_aifg")
    symlink_path = "/var/sysom/ilog/prof_aifg"
    
    try:
        # 创建目录 /pai_aimaster/job/sysom/
        os.makedirs(signal_dir, exist_ok=True)
        logger.info("Created directory: {}".format(signal_dir))
        
        # 创建文件 /pai_aimaster/job/sysom/prof_aifg
        # 如果文件不存在则创建空文件
        if not os.path.exists(prof_aifg_file):
            with open(prof_aifg_file, "w") as f:
                f.write("")  # 创建空文件
            logger.info("Created file: {}".format(prof_aifg_file))
        else:
            logger.info("File already exists: {}".format(prof_aifg_file))
        
        # 确保软链接的父目录 /var/sysom/ilog/ 存在
        symlink_dir = os.path.dirname(symlink_path)
        os.makedirs(symlink_dir, exist_ok=True)
        logger.info("Ensured directory exists: {}".format(symlink_dir))
        
        # 如果软链接已存在，先删除
        if os.path.islink(symlink_path):
            os.unlink(symlink_path)
            logger.info("Removed existing symlink: {}".format(symlink_path))
        
        # 创建软链接
        os.symlink(prof_aifg_file, symlink_path)
        logger.info("Created symlink: {} -> {}".format(symlink_path, prof_aifg_file))
        
    except Exception as e:
        logger.error("Failed to create prof_aifg structure: {}".format(str(e)))

def run_client():
    """运行客户端主程序"""
    # 从环境变量获取AIMASTER_ADDR
    aimaster_addr = os.environ.get("AIMASTER_ADDR")
    if not aimaster_addr:
        if logger:
            logger.error("Error: Environment variable AIMASTER_ADDR not set")
        else:
            print("Error: Environment variable AIMASTER_ADDR not set")
        return 1
    
    if logger:
        logger.info("Using AIMASTER_ADDR: {}".format(aimaster_addr))
    else:
        print("Using AIMASTER_ADDR: {}".format(aimaster_addr))
    
    # 检查并设置ilogtail
    setup_logtail_if_needed()
    
    # 创建prof_aifg目录结构和软链接
    create_prof_aifg_structure()
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 启动主循环
    main_loop(aimaster_addr)
    
    if logger:
        logger.info("Program exited normally")

def main():
    global logger
    
    parser = argparse.ArgumentParser(description='SysOM PAI Client')
    parser.add_argument('-d', '--daemon', action='store_true', help='Run as daemon')
    parser.add_argument('-p', '--pid-file', default='/var/run/sysom-pai-client.pid', help='PID file path')
    parser.add_argument('-l', '--log-file', default='/var/log/sysom-pai-client.log', help='Log file path')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], 
                       help='Log level (default: INFO)')
    
    args = parser.parse_args()
    
    # 设置日志
    logger = setup_logging(args.log_file, args.daemon, args.log_level)
    
    if args.daemon:
        # 以守护进程方式运行
        daemonize(args.pid_file)
        # 守护进程模式下重新设置日志
        logger = setup_logging(args.log_file, True, args.log_level)
        logger.info("Running in daemon mode with log level: {}".format(args.log_level))
    
    # 运行客户端
    run_client()

if __name__ == "__main__":
    main()