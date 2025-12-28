import math
import threading
from datetime import datetime
from django.apps import apps
from importlib import import_module
import os
import platform
from app_console.models import ConsoleProcess
from django.conf import settings
import subprocess
from collections import deque
import psutil
import shlex


class ConsoleUtils:
    @staticmethod
    def run_command(cmd, log_file_path, mode='w'):
        try:
            cmd_parts = shlex.split(cmd)
        except ValueError as e:
            print(f"Error parsing command: {e}")
            return None

        if not cmd_parts:
            return None

        try:
            if platform.system() == "Windows":
                full_cmd = ['python', 'manage.py'] + cmd_parts
                with open(log_file_path, mode, encoding='utf-8') as log_file:
                    process = subprocess.Popen(
                        full_cmd,
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                        text=True,
                        shell=True
                    )

            elif platform.system() == "Linux":
                base_cmd = [
                    f'{settings.BASE_DIR}/venv/bin/python3',
                    f'{settings.BASE_DIR}/manage.py'
                ] + cmd_parts

                with open(log_file_path, mode, encoding='utf-8') as log_file:
                    process = subprocess.Popen(
                        base_cmd,
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        env={**os.environ, "PYTHONUNBUFFERED": "1"}
                    )
        except (FileNotFoundError, IndexError) as e:
            print(f"Error starting process: {e}")
            return None

        def process_wait(process):
            process.wait()
            ConsoleProcess.objects.filter(pid=process.pid, project_id=settings.PROJECT_ID).update(pid=None)

        threading.Thread(target=process_wait, kwargs={'process': process}).start()

        return process

    @staticmethod
    def available_commands():
        commands_dir_path = os.path.join(apps.get_app_config('app_console').path, 'management', 'commands')
        available_commands = []

        if os.path.exists(commands_dir_path):
            for file in os.listdir(commands_dir_path):
                if file.endswith('.py') and file != '__init__.py':
                    command_name = file.replace('.py', '')
                    try:
                        command_module = import_module(f"app_console.management.commands.{command_name}")
                        if hasattr(command_module, 'Command'):
                            command_class = command_module.Command
                            if getattr(command_class, 'is_enable', False):
                                available_commands.append({
                                    'cmd': command_name,
                                    'name': getattr(command_class, 'name', None),
                                    'proc_id': getattr(command_class, 'proc_id', None),
                                    'proc_num_max': getattr(command_class, 'proc_num_max', None),
                                    'sort': getattr(command_class, 'sort', float('inf')),
                                    'skip_check_active': getattr(command_class, 'skip_check_active', False),
                                })
                    except ModuleNotFoundError:
                        pass
        available_commands = sorted(available_commands, key=lambda cmd: cmd['sort'])
        return available_commands

    @staticmethod
    def output_command(log_file_path, maxlen=None):
        content = ''
        if os.path.exists(log_file_path):
            with open(log_file_path, "r", encoding='utf-8') as log_file:
                if maxlen:
                    lines = deque(log_file, maxlen=20)
                    content = "".join(lines)
                else:
                    content = "".join(log_file.readlines())
        return content

    @staticmethod
    def kill_command(pid):
        try:
            parent = psutil.Process(pid)
            for child in parent.children(recursive=True):
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass
            parent.terminate()
            return True
        except psutil.NoSuchProcess:
            return False

    @staticmethod
    def convert_bytes_to_string(n):
        if n == 0:
            return '0 B'
        unit_symbols = ('B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB')
        exponent = int(math.log(n, 1024))
        exponent = min(exponent, len(unit_symbols) - 1)
        quotient = float(n) / (1024 ** exponent)
        return f"{quotient:.1f} {unit_symbols[exponent]}"

    @staticmethod
    def system_info(python_processes_only=False):
        system_data = {}

        if not python_processes_only:
            disk_info_list = []
            try:
                partitions = psutil.disk_partitions(all=False)
                for partition in partitions:
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        disk_info = {
                            'filesystem': partition.device,
                            'size': ConsoleUtils.convert_bytes_to_string(usage.total),
                            'used': ConsoleUtils.convert_bytes_to_string(usage.used),
                            'avail': ConsoleUtils.convert_bytes_to_string(usage.free),
                            'percent': f"{usage.percent:.1f}%",
                            'mountpoint': partition.mountpoint,
                        }
                        disk_info_list.append(disk_info)
                    except Exception as e:
                        print(f"Could not get usage for {partition.mountpoint}: {e}")
                        disk_info = {
                            'filesystem': partition.device, 'size': 'N/A', 'used': 'N/A',
                            'avail': 'N/A', 'percent': 'N/A',
                            'mountpoint': partition.mountpoint + f' (Error)',
                        }
                        disk_info_list.append(disk_info)
            except Exception as e:
                print(f"Error getting partitions: {e}")
            system_data['disk_usage'] = disk_info_list

            try:
                mem = psutil.virtual_memory()
                swap = psutil.swap_memory()
                system_data['memory'] = {
                    'ram_total': ConsoleUtils.convert_bytes_to_string(mem.total),
                    'ram_available': ConsoleUtils.convert_bytes_to_string(mem.available),
                    'ram_used': ConsoleUtils.convert_bytes_to_string(mem.used),
                    'ram_percent': f"{mem.percent:.1f}%",
                    'swap_total': ConsoleUtils.convert_bytes_to_string(swap.total),
                    'swap_used': ConsoleUtils.convert_bytes_to_string(swap.used),
                    'swap_percent': f"{swap.percent:.1f}%",
                }
            except Exception as e:
                print(f"Could not get memory info: {e}")
                system_data['memory'] = None

            try:
                cpu_overall_percent = psutil.cpu_percent(interval=0.2)
                system_data['cpu'] = {
                    'physical_cores': psutil.cpu_count(logical=False),
                    'total_cores': psutil.cpu_count(logical=True),
                    'usage_percent': f"{cpu_overall_percent:.1f}%",
                }
            except Exception as e:
                print(f"Could not get CPU info: {e}")
                system_data['cpu'] = None

            try:
                load_avg = psutil.getloadavg()
                system_data['load_average'] = {
                    '1min': f"{load_avg[0]:.2f}",
                    '5min': f"{load_avg[1]:.2f}",
                    '15min': f"{load_avg[2]:.2f}",
                }
            except Exception as e:
                print(f"Could not get load average: {e}")
                system_data['load_average'] = None

        python_processes = []
        try:
            attrs = ['pid', 'name', 'username', 'cpu_percent', 'memory_info', 'memory_percent', 'cmdline', 'create_time', 'ppid']
            procs = {p.info['pid']: p for p in psutil.process_iter(attrs=attrs)}

            for pid, proc in procs.items():
                cmdline = proc.info.get('cmdline')
                is_python = False
                if proc.info.get('name') and 'python' in proc.info['name'].lower():
                    is_python = True
                elif cmdline and any('python' in arg.lower() for arg in cmdline):
                    is_python = True

                if is_python and python_processes_only:
                    if isinstance(cmdline, list):
                        if len(cmdline) > 1:
                            cmdline.pop(0)
                        cmdline_str = ' '.join(cmdline)
                        if 'manage.py runserver 8000' in cmdline_str or 'multiprocessing.spawn' in cmdline_str or '--wait-for-signal' in cmdline_str:
                            is_python = False
                        else:
                            parent_pid = proc.info['ppid']
                            if parent_pid in procs:
                                parent_proc = procs[parent_pid]
                                parent_name = parent_proc.info.get('name', '').lower()
                                parent_cmdline = parent_proc.info.get('cmdline')

                                is_parent_python = False
                                if 'python' in parent_name:
                                    is_parent_python = True
                                elif parent_cmdline and any('python' in arg.lower() for arg in parent_cmdline):
                                    is_parent_python = True
                                if is_parent_python:
                                    is_python = False

                if is_python:
                    cpu_p = proc.info.get('cpu_percent')
                    mem_p = proc.info.get('memory_percent')
                    mem_rss = proc.info.get('memory_info').rss if proc.info.get('memory_info') else 0

                    child_count = 0
                    try:
                        children = proc.children(recursive=False)
                        child_count = len(children)
                    except psutil.Error:
                        pass

                    python_processes.append({
                        'pid': proc.info.get('pid'),
                        'user': proc.info.get('username', 'N/A'),
                        'cpu_percent': f"{cpu_p:.1f}%" if cpu_p is not None else 'N/A',
                        'mem_rss': ConsoleUtils.convert_bytes_to_string(mem_rss),
                        'mem_percent': f"{mem_p:.1f}%" if mem_p is not None else 'N/A',
                        'command': ' '.join(cmdline) if cmdline else proc.info.get('name', 'N/A'),
                        'started': datetime.fromtimestamp(proc.info['create_time']).strftime('%Y-%m-%d %H:%M:%S') if proc.info.get('create_time') else 'N/A',
                        'child_count': child_count
                    })
        except Exception as e:
            print(f"Error iterating processes: {e}")

        system_data['python_processes'] = python_processes

        return system_data
