#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Haitest保存的性能数据做一层处理
实现与 smartPerf 的 SaveData 接口相同的逻辑
"""

import json
import os
import time
import traceback
from typing import Dict, Any, Optional, Tuple

from .models import OSType
from .logger import get_logger

logger = get_logger(__name__)


class SaveDataWrapper:
    """性能数据保存封装类"""

    def __init__(self, os_type: OSType):
        """
        初始化保存数据封装器
        """
        self.os_type = os_type

    def process_json_file(self, file_path: str) -> bool:
        """
        直接处理JSON文件，解析并改写

        Args:
            file_path: JSON文件路径

        Returns:
            bool
        """

        try:
            # 1. 检查文件是否存在
            if not os.path.exists(file_path):
                return False

            logger.info(f"开始处理JSON文件: {file_path}")

            # 2. 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                data = f.read()

            # 3. 解析JSON数据
            try:
                save_sysmontap = json.loads(data)
            except json.JSONDecodeError as e:
                logger.error(f"性能数据JSON解析错误: {e}\n{traceback.format_exc()}")
                return False

            # 5. 构建处理后的数据（进行数据分析和统计）
            processed_data = self._build_processed_data(save_sysmontap)

            if processed_data is None:
                return False

            # 6. 重新写入处理后的数据
            processed_json = json.dumps(processed_data, ensure_ascii=False, indent=2)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(processed_json)
            return True

        except Exception as e:
            logger.error(f"处理性能采集的json文件过程中发生错误: {e}\n{traceback.format_exc()}")
            return False

    def _build_processed_data(self, save_sysmontap: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        构建处理后的数据，进行数据分析和统计

        Args:
            save_sysmontap: 原始保存的性能数据

        Returns:
            Dict: 处理后的数据
        """
        try:
            # 处理所有数据列表
            data_list = []

            for info in save_sysmontap.get('DataList', []):
                # 转换时间戳
                timestamp = self._to_timestamp(info.get('TimeStamp'))
                if timestamp is None:
                    continue

                # 转换数据信息
                transformed_data = self._transform_info(info)
                if transformed_data:
                    data_list.append(transformed_data)

            # 计算指标
            indicators_map = self._calc_indicators(data_list)
            if indicators_map is None:
                return None

            # 构建概览数据
            overview_map = {'ALL': indicators_map.get('ALL', [])}

            # 构建最终结果
            result = {
                'DataList': data_list,
                'AbsDataStartTime': save_sysmontap.get('AbsDataStartTime', 0),
                'AppDisplayName': save_sysmontap.get('AppDisplayName', ''),
                'AppVersion': save_sysmontap.get('AppVersion', ''),
                'AppPackageName': save_sysmontap.get('AppPackageName', ''),
                'DeviceModel': save_sysmontap.get('DeviceModel', ''),
                'OSType': save_sysmontap.get('OSType', ''),
                'OSVersion': save_sysmontap.get('OSVersion', ''),
                'Overview': overview_map,
                'Fps': indicators_map.get('Fps', []),
                'CpuUsage': indicators_map.get('CpuUsage', []),
                'MemoryUsage': indicators_map.get('MemoryUsage', []),
                'NetworkUsage': indicators_map.get('NetworkUsage', []),
                'Temperature': indicators_map.get('Temperature', []),
                'GpuUsage': indicators_map.get('GpuUsage', []),
                'Power': indicators_map.get('Power', []),
            }

            return result

        except Exception as e:
            logger.error(f"构建处理数据失败: {e}")
            return None

    def _to_timestamp(self, time_value) -> Optional[int]:
        """转换时间戳"""
        if time_value is None:
            return None

        try:
            if isinstance(time_value, (int, float)):
                return int(time_value)
            elif isinstance(time_value, str):
                return int(float(time_value))
            else:
                return int(time_value)
        except (ValueError, TypeError):
            logger.error(f"时间戳转换失败: {time_value}")
            return None

    def _transform_info(self, info: Dict[str, Any]) -> Optional[
        Dict[str, Any]]:
        """转换信息数据"""
        try:
            time_val = self._to_timestamp(info.get('TimeStamp'))
            if time_val is None:
                return None

            if self.os_type != OSType.IOS:
                # Android/Harmony数据处理
                transformed = {
                    'CommonFPS': {
                        'Fps': info.get('AndroidFps', {}).get('fps', 0),
                        'Jank': info.get('AndroidFps', {}).get('Jank', 0),
                        'BigJank': info.get('BigJank', {}).get('BigJank', 0),
                        'Stutter': info.get('Stutter', {}).get('Stutter', 0),
                        'SmallJank': info.get('SmallJank', {}).get('SmallJank', 0)
                    },
                    'CommonGPUUsage': {
                        'GpuUsage': info.get('GpuUsage', {}).get('GpuUsage')
                    },
                    'CpuUsage': {
                        'AppUsage': info.get('CpuUsage', {}).get('AppUsage', 0),
                        'TotalUsage': info.get('CpuUsage', {}).get('TotalUsage', 0)
                    },
                    'NetworkUsage': {
                        'UpSpeed': info.get('NetworkUsage', {}).get('UpSpeed', 0),
                        'DownSpeed': info.get('NetworkUsage', {}).get('DownSpeed', 0)
                    },
                    'Temperature': info.get('Temperature'),
                    'Power': info.get('Power'),
                    'MemoryUsage': {
                        'Memory': info.get('AndroidMemoryUsage', {}).get('Memory', 0),
                        'SwapMemory': info.get('AndroidMemoryUsage', {}).get('SwapMemory', 0),
                        'VirtualMemory': info.get('VirtualMemory', {}).get('VirtualMemory', 0)
                    },
                    'TimeStamp': info.get('TimeStamp'),
                    'FrameTime': info.get('FrameTime', {'FrameTimeData': [{'Time': time_val}]})
                }
            else:
                # iOS数据处理
                transformed = {
                    'CommonFPS': {
                        'Fps': info.get('IosFps', {}).get('FPS2') or info.get('IosFps', {}).get('FPS', 0),
                        'Stutter': info.get('Stutter', {}).get('Stutter', 0),
                        'Jank': info.get('IosFps', {}).get('Jank', 0),
                        'BigJank': info.get('BigJank', {}).get('BigJank', 0),
                        'SmallJank': info.get('SmallJank', {}).get('SmallJank', 0)
                    },
                    'CommonGPUUsage': {
                        'Tiler': info.get('IosGPUUsage', {}).get('Tiler'),
                        'Render': info.get('IosGPUUsage', {}).get('Render'),
                        'Device': info.get('IosGPUUsage', {}).get('Device')
                    },
                    'TimeStamp': info.get('TimeStamp'),
                    'CpuUsage': {
                        'AppUsage': info.get('CpuUsage', {}).get('AppUsage', 0),
                        'TotalUsage': info.get('CpuUsage', {}).get('TotalUsage', 0)
                    },
                    'MemoryUsage': {
                        'Memory': info.get('MemoryUsage', {}).get('Memory', 0),
                        'VirtualMemory': info.get('VirtualMemory', {}).get('VirtualMemory', 0)
                    },
                    'NetworkUsage': {
                        'UpSpeed': info.get('NetworkUsage', {}).get('UpSpeed', 0),
                        'DownSpeed': info.get('NetworkUsage', {}).get('DownSpeed', 0)
                    },
                    'Temperature': info.get('Temperature'),
                    'Power': info.get('Power'),
                    'FrameTime': {'FrameTimeData': info.get('FrameTimeData', [{'Time': time_val}])}
                }

            return transformed

        except Exception as e:
            logger.error(f"转换信息数据失败: {e}")
            return None

    def _calc_indicators(self, data_list: list) -> Optional[Dict[str, list]]:
        """计算性能指标"""
        try:
            if not data_list:
                return {'ALL': []}

            # 初始化指标详情
            indicator_detail = {
                'TotalFPS': 0,
                'Gte18FPSCount': 0,
                'Gte25FPSCount': 0,
                'TotalAppCpuUsage': 0,
                'Lte60AppCpuUsageCount': 0,
                'Lte80AppCpuUsageCount': 0,
                'TotalCpuUsage': 0,
                'Lte60CpuUsageCount': 0,
                'Lte80CpuUsageCount': 0,
                'TotalMemory': 0,
                'TotalSwapMemory': 0,
                'TotalVirtualMemory': 0,
                'TotalStutter': 0,
                'MinFPS': 0,
                'MaxFPS': 0,
                'TotalJank': 0,
                'TotalBigJank': 0,
                'TotalSmallJank': 0,
                'TotalUpSpeed': 0,
                'TotalDownSpeed': 0,
                'TotalPower': 0,
                'TotalVoltage': 0,
                'TotalCurrent': 0,
                'TotalBatteryTemperature': 0,
                'TotalCpuTemperature': 0,
                'PeakCpuUsage': 0,
                'PeakAppCpuUsage': 0,
                'MaxMemory': 0,
                'MaxSwapMemory': 0,
                'MaxVirtualMemory': 0,
                'MaxCpuTemperature': 0,
                'MaxBatteryTemperature': 0,
                'TotalFrameTime': 0,
                'TotalFrameTimeNum': 0,
                'Gte100FrameTimeNum': 0,
                'PeakFrameTime': 0,
                'TotalGPUUsage': 0,
                'TotalRender': 0,
                'TotalTiler': 0,
                'TotalDevice': 0,
                'AllFPS': [],
                'AllAppCpuUsage': [],
                'AllCpuUsage': [],
                'AllMemory': [],
                'AllSwapMemory': [],
                'AllVirtualMemory': [],
                'AllBatteryTemperature': [],
                'AllCpuTemperature': [],
                'AllPower': []
            }

            # 收集数据
            for info in data_list:
                fps = info.get('CommonFPS', {}).get('Fps', 0)
                app_cpu = info.get('CpuUsage', {}).get('AppUsage', 0)
                total_cpu = info.get('CpuUsage', {}).get('TotalUsage', 0)
                memory = info.get('MemoryUsage', {}).get('Memory', 0)
                swap_memory = info.get('MemoryUsage', {}).get('SwapMemory', 0)
                virtual_memory = info.get('MemoryUsage', {}).get('VirtualMemory', 0)
                up_speed = info.get('NetworkUsage', {}).get('UpSpeed', 0)
                down_speed = info.get('NetworkUsage', {}).get('DownSpeed', 0)
                battery_temp = info.get('Temperature', {}).get('BatteryTemperature', 0)
                cpu_temp = info.get('Temperature', {}).get('CpuTemperature', 0)
                power = info.get('Power', {})
                power_value = power.get('Power', 0) if power else 0
                voltage = power.get('Voltage', 0) if power else 0
                current = power.get('Current', 0) if power else 0

                # GPU相关数据
                gpu_usage = info.get('CommonGPUUsage', {}).get('GpuUsage', 0)
                render = info.get('CommonGPUUsage', {}).get('Render', 0)
                tiler = info.get('CommonGPUUsage', {}).get('Tiler', 0)
                device = info.get('CommonGPUUsage', {}).get('Device', 0)

                # Jank相关数据
                jank = info.get('CommonFPS', {}).get('Jank', 0)
                big_jank = info.get('CommonFPS', {}).get('BigJank', 0)
                small_jank = info.get('CommonFPS', {}).get('SmallJank', 0)
                stutter = info.get('CommonFPS', {}).get('Stutter', 0)

                # 累计统计
                indicator_detail['TotalFPS'] += fps
                indicator_detail['TotalAppCpuUsage'] += app_cpu
                indicator_detail['TotalCpuUsage'] += total_cpu
                indicator_detail['TotalMemory'] += memory
                indicator_detail['TotalSwapMemory'] += swap_memory
                indicator_detail['TotalVirtualMemory'] += virtual_memory
                indicator_detail['TotalUpSpeed'] += up_speed
                indicator_detail['TotalDownSpeed'] += down_speed
                indicator_detail['TotalPower'] += power_value
                indicator_detail['TotalVoltage'] += voltage
                indicator_detail['TotalCurrent'] += current
                indicator_detail['TotalBatteryTemperature'] += battery_temp
                indicator_detail['TotalCpuTemperature'] += cpu_temp
                indicator_detail['TotalJank'] += jank
                indicator_detail['TotalBigJank'] += big_jank
                indicator_detail['TotalSmallJank'] += small_jank
                indicator_detail['TotalStutter'] += stutter
                indicator_detail['TotalGPUUsage'] += gpu_usage
                indicator_detail['TotalRender'] += render
                indicator_detail['TotalTiler'] += tiler
                indicator_detail['TotalDevice'] += device

                # 收集数组数据
                indicator_detail['AllFPS'].append(fps)
                indicator_detail['AllAppCpuUsage'].append(app_cpu)
                indicator_detail['AllCpuUsage'].append(total_cpu)
                indicator_detail['AllMemory'].append(memory)
                indicator_detail['AllSwapMemory'].append(swap_memory)
                indicator_detail['AllVirtualMemory'].append(virtual_memory)
                indicator_detail['AllBatteryTemperature'].append(battery_temp)
                indicator_detail['AllCpuTemperature'].append(cpu_temp)
                indicator_detail['AllPower'].append(power_value)

                # 计算极值
                if indicator_detail['MinFPS'] == 0 or indicator_detail['MinFPS'] > fps:
                    indicator_detail['MinFPS'] = fps
                if indicator_detail['MaxFPS'] <= fps:
                    indicator_detail['MaxFPS'] = fps
                if indicator_detail['PeakCpuUsage'] <= total_cpu:
                    indicator_detail['PeakCpuUsage'] = total_cpu
                if indicator_detail['PeakAppCpuUsage'] <= app_cpu:
                    indicator_detail['PeakAppCpuUsage'] = app_cpu
                if indicator_detail['MaxMemory'] <= memory:
                    indicator_detail['MaxMemory'] = memory
                if indicator_detail['MaxSwapMemory'] <= swap_memory:
                    indicator_detail['MaxSwapMemory'] = swap_memory
                if indicator_detail['MaxVirtualMemory'] <= virtual_memory:
                    indicator_detail['MaxVirtualMemory'] = virtual_memory
                if indicator_detail['MaxCpuTemperature'] <= cpu_temp:
                    indicator_detail['MaxCpuTemperature'] = cpu_temp
                if indicator_detail['MaxBatteryTemperature'] <= battery_temp:
                    indicator_detail['MaxBatteryTemperature'] = battery_temp

                # 统计FPS范围
                if fps >= 18:
                    indicator_detail['Gte18FPSCount'] += 1
                if fps >= 25:
                    indicator_detail['Gte25FPSCount'] += 1

                # 统计CPU使用率范围
                if app_cpu <= 60:
                    indicator_detail['Lte60AppCpuUsageCount'] += 1
                if app_cpu <= 80:
                    indicator_detail['Lte80AppCpuUsageCount'] += 1
                if total_cpu <= 60:
                    indicator_detail['Lte60CpuUsageCount'] += 1
                if total_cpu <= 80:
                    indicator_detail['Lte80CpuUsageCount'] += 1

                # 处理FrameTime数据
                frame_time_data = info.get('FrameTime', {}).get('FrameTimeData', [])
                for ft in frame_time_data:
                    frame_time = ft.get('FrameTime', 0)
                    indicator_detail['TotalFrameTime'] += frame_time
                    indicator_detail['TotalFrameTimeNum'] += 1
                    if frame_time >= 100:
                        indicator_detail['Gte100FrameTimeNum'] += 1
                    if indicator_detail['PeakFrameTime'] <= frame_time:
                        indicator_detail['PeakFrameTime'] = frame_time

            # 计算平均值和百分比
            length = len(data_list)
            if length == 0:
                return {'ALL': []}

            # 计算各项指标
            avg_fps = indicator_detail['TotalFPS'] / length
            gte18_fps_percent = (indicator_detail['Gte18FPSCount'] / length) * 100
            gte25_fps_percent = (indicator_detail['Gte25FPSCount'] / length) * 100
            avg_app_cpu = indicator_detail['TotalAppCpuUsage'] / length
            avg_cpu = indicator_detail['TotalCpuUsage'] / length
            avg_memory = indicator_detail['TotalMemory'] / length
            avg_swap_memory = indicator_detail['TotalSwapMemory'] / length
            avg_virtual_memory = indicator_detail['TotalVirtualMemory'] / length
            avg_up_speed = indicator_detail['TotalUpSpeed'] / length
            avg_down_speed = indicator_detail['TotalDownSpeed'] / length
            avg_power = indicator_detail['TotalPower'] / length
            avg_voltage = indicator_detail['TotalVoltage'] / length
            avg_current = indicator_detail['TotalCurrent'] / length
            avg_battery_temp = indicator_detail['TotalBatteryTemperature'] / length
            avg_cpu_temp = indicator_detail['TotalCpuTemperature'] / length
            avg_frame_time = indicator_detail['TotalFrameTime'] / indicator_detail['TotalFrameTimeNum'] if \
                indicator_detail['TotalFrameTimeNum'] > 0 else 0
            gte100_frame_time_percent = (indicator_detail['Gte100FrameTimeNum'] / indicator_detail[
                'TotalFrameTimeNum']) * 100 if indicator_detail['TotalFrameTimeNum'] > 0 else 0

            # 新增指标计算
            lte60_app_cpu_percent = (indicator_detail['Lte60AppCpuUsageCount'] / length) * 100
            lte80_app_cpu_percent = (indicator_detail['Lte80AppCpuUsageCount'] / length) * 100
            lte60_cpu_percent = (indicator_detail['Lte60CpuUsageCount'] / length) * 100
            lte80_cpu_percent = (indicator_detail['Lte80CpuUsageCount'] / length) * 100
            jank_10min = (indicator_detail['TotalJank'] / length) * 600
            big_jank_10min = (indicator_detail['TotalBigJank'] / length) * 600
            small_jank_10min = (indicator_detail['TotalSmallJank'] / length) * 600
            stutter_percent = indicator_detail['TotalStutter'] / length
            avg_gpu_usage = indicator_detail['TotalGPUUsage'] / length
            avg_render = indicator_detail['TotalRender'] / length
            avg_tiler = indicator_detail['TotalTiler'] / length
            avg_device = indicator_detail['TotalDevice'] / length
            sum_battery = avg_current * avg_voltage / 1000 * length / 1000 / 3600  # 总电量计算

            # 计算P50分位数
            fps_p50 = self._calculate_percentile(indicator_detail['AllFPS'], 50)
            app_cpu_p50 = self._calculate_percentile(indicator_detail['AllAppCpuUsage'], 50)
            cpu_p50 = self._calculate_percentile(indicator_detail['AllCpuUsage'], 50)
            memory_p50 = self._calculate_percentile(indicator_detail['AllMemory'], 50)
            swap_memory_p50 = self._calculate_percentile(indicator_detail['AllSwapMemory'], 50)
            virtual_memory_p50 = self._calculate_percentile(indicator_detail['AllVirtualMemory'], 50)
            power_p50 = self._calculate_percentile(indicator_detail['AllPower'], 50)
            battery_temp_p50 = self._calculate_percentile(indicator_detail['AllBatteryTemperature'], 50)
            cpu_temp_p50 = self._calculate_percentile(indicator_detail['AllCpuTemperature'], 50)

            # 构建指标结果
            indicators = {
                'Fps': [
                    {'Name': 'Avg(FPS)', 'Value': avg_fps, 'Unit': '帧/s', 'Key': 'fps'},
                    {'Name': 'FPS>=18', 'Value': gte18_fps_percent, 'Unit': '%', 'Key': 'fps'},
                    {'Name': 'FPS>=25', 'Value': gte25_fps_percent, 'Unit': '%', 'Key': 'fps'},
                    {'Name': 'Max(FPS)', 'Value': indicator_detail['MaxFPS'], 'Unit': '帧/s', 'Key': 'fps'},
                    {'Name': 'Min(FPS)', 'Value': indicator_detail['MinFPS'], 'Unit': '帧/s', 'Key': 'fps'},
                    {'Name': 'Jank', 'Value': indicator_detail['TotalJank'], 'Unit': '', 'Key': 'Jank'},
                    {'Name': 'Big Jank', 'Value': indicator_detail['TotalBigJank'], 'Unit': '', 'Key': 'BigJank'},
                    {'Name': 'Small Jank', 'Value': indicator_detail['TotalSmallJank'], 'Unit': '', 'Key': 'SmallJank'},
                    {'Name': 'Jank[/10min]', 'Value': jank_10min, 'Unit': '', 'Key': 'Jank'},
                    {'Name': 'Big Jank[/10min]', 'Value': big_jank_10min, 'Unit': '', 'Key': 'BigJank'},
                    {'Name': 'Small Jank[/10min]', 'Value': small_jank_10min, 'Unit': '', 'Key': 'SmallJank'},
                    {'Name': 'Stutter', 'Value': stutter_percent, 'Unit': '%', 'Key': 'Stutter'},
                    {'Name': 'Avg(FTime)[ms]', 'Value': avg_frame_time, 'Unit': '', 'Key': 'fps'},
                    {'Name': 'Peak(FTime)', 'Value': indicator_detail['PeakFrameTime'], 'Unit': '', 'Key': 'fps'},
                    {'Name': 'FTime>=100ms[%]', 'Value': gte100_frame_time_percent, 'Unit': '', 'Key': 'fps'},
                    {'Name': 'P50(FPS)', 'Value': fps_p50, 'Unit': '', 'Key': 'fps'}
                ],
                'CpuUsage': [
                    {'Name': 'Avg(AppCPU)', 'Value': avg_app_cpu, 'Unit': '%', 'Key': 'AppUsage'},
                    {'Name': 'AppCPU<=60%', 'Value': lte60_app_cpu_percent, 'Unit': '', 'Key': 'AppUsage'},
                    {'Name': 'AppCPU<=80%', 'Value': lte80_app_cpu_percent, 'Unit': '', 'Key': 'AppUsage'},
                    {'Name': 'Peak(AppCPU)', 'Value': indicator_detail['PeakAppCpuUsage'], 'Unit': '',
                     'Key': 'AppUsage'},
                    {'Name': 'P50(AppCPU)', 'Value': app_cpu_p50, 'Unit': '', 'Key': 'AppUsage'},
                    {'Name': 'Avg(TotalCPU)', 'Value': avg_cpu, 'Unit': '%', 'Key': 'TotalUsage'},
                    {'Name': 'TotalCPU<=60%', 'Value': lte60_cpu_percent, 'Unit': '', 'Key': 'TotalUsage'},
                    {'Name': 'TotalCPU<=80%', 'Value': lte80_cpu_percent, 'Unit': '', 'Key': 'TotalUsage'},
                    {'Name': 'Peak(TotalCPU)', 'Value': indicator_detail['PeakCpuUsage'], 'Unit': '',
                     'Key': 'TotalUsage'},
                    {'Name': 'P50(TotalCPU)', 'Value': cpu_p50, 'Unit': '', 'Key': 'TotalUsage'}
                ],
                'MemoryUsage': [
                    {'Name': 'Avg(Memory)', 'Value': avg_memory, 'Unit': 'MB', 'Key': 'Memory'},
                    {'Name': 'Avg(SwapMemory)', 'Value': avg_swap_memory, 'Unit': 'MB', 'Key': 'SwapMemory'},
                    {'Name': 'Avg(VirtualMemory)', 'Value': avg_virtual_memory, 'Unit': 'MB', 'Key': 'VirtualMemory'},
                    {'Name': 'Peak(Memory)', 'Value': indicator_detail['MaxMemory'], 'Unit': 'MB', 'Key': 'Memory'},
                    {'Name': 'Peak(SwapMemory)', 'Value': indicator_detail['MaxSwapMemory'], 'Unit': 'MB',
                     'Key': 'SwapMemory'},
                    {'Name': 'Peak(VirtualMemory)', 'Value': indicator_detail['MaxVirtualMemory'], 'Unit': 'MB',
                     'Key': 'VirtualMemory'},
                    {'Name': 'P50(Memory)', 'Value': memory_p50, 'Unit': 'MB', 'Key': 'Memory'}
                ],
                'NetworkUsage': [
                    {'Name': 'Avg(Send)[KB/s]', 'Value': avg_up_speed, 'Unit': '', 'Key': 'UpSpeed'},
                    {'Name': 'Avg(Recv)[KB/s]', 'Value': avg_down_speed, 'Unit': '', 'Key': 'DownSpeed'},
                    {'Name': 'Sum(Send)[KB]', 'Value': indicator_detail['TotalUpSpeed'], 'Unit': '', 'Key': 'UpSpeed'},
                    {'Name': 'Sum(Recv)[KB]', 'Value': indicator_detail['TotalDownSpeed'], 'Unit': '',
                     'Key': 'DownSpeed'},
                    {'Name': 'Send[KB/10min]', 'Value': avg_up_speed * 600, 'Unit': '', 'Key': 'UpSpeed'},
                    {'Name': 'Recv[KB/10min]', 'Value': avg_down_speed * 600, 'Unit': '', 'Key': 'DownSpeed'}
                ],
                'Temperature': [
                    {'Name': 'Avg(BatteryTemp)', 'Value': avg_battery_temp, 'Unit': '℃', 'Key': 'BatteryTemperature'},
                    {'Name': 'Max(BatteryTemp)', 'Value': indicator_detail['MaxBatteryTemperature'], 'Unit': '℃',
                     'Key': 'BatteryTemperature'},
                    {'Name': 'P50(BatteryTemp)', 'Value': battery_temp_p50, 'Unit': '℃', 'Key': 'BatteryTemperature'}
                ],
                'Power': [
                    {'Name': 'Avg(Power)', 'Value': avg_power, 'Unit': 'mW', 'Key': 'Power'},
                    {'Name': 'P50(Power)', 'Value': power_p50, 'Unit': 'mW', 'Key': 'Power'},
                    {'Name': 'Sum(Battery)', 'Value': sum_battery, 'Unit': 'mWh', 'Key': 'BatLevel'},
                    {'Name': 'Avg(Voltage)', 'Value': avg_voltage, 'Unit': 'mV', 'Key': 'Voltage'},
                    {'Name': 'Avg(Current)', 'Value': avg_current, 'Unit': 'mA', 'Key': 'Current'}
                ],
                'GpuUsage': []
            }

            # 添加GPU相关指标
            if self.os_type != OSType.IOS:
                # Android GPU指标
                indicators['GpuUsage'] = [
                    {'Name': 'Avg(GPUUsage)', 'Value': avg_gpu_usage, 'Unit': '%', 'Key': 'GpuUsage'}
                ]
            else:
                # iOS GPU指标
                indicators['GpuUsage'] = [
                    {'Name': 'Avg(Render)', 'Value': avg_render, 'Unit': '%', 'Key': 'Render'},
                    {'Name': 'Avg(Device)', 'Value': avg_device, 'Unit': '%', 'Key': 'Device'},
                    {'Name': 'Avg(Tiler)', 'Value': avg_tiler, 'Unit': '%', 'Key': 'Tiler'}
                ]

            # 添加CPU温度指标（非iOS设备）
            if self.os_type != OSType.IOS:
                indicators['Temperature'].extend([
                    {'Name': 'Avg(CPUTemp)', 'Value': avg_cpu_temp, 'Unit': '℃', 'Key': 'CpuTemperature'},
                    {'Name': 'Max(CPUTemp)', 'Value': indicator_detail['MaxCpuTemperature'], 'Unit': '℃',
                     'Key': 'CpuTemperature'},
                    {'Name': 'P50(CPUTemp)', 'Value': cpu_temp_p50, 'Unit': '℃', 'Key': 'CpuTemperature'}
                ])

            # 合并所有指标
            all_indicators = []
            for category in ['Fps', 'CpuUsage', 'MemoryUsage', 'NetworkUsage', 'Temperature', 'GpuUsage', 'Power']:
                all_indicators.extend(indicators[category])

            indicators['ALL'] = all_indicators

            return indicators

        except Exception as e:
            logger.error(f"计算指标失败: {e}")
            return None

    def _calculate_percentile(self, values: list, percent: int) -> float:
        """计算分位数"""
        if not values:
            return 0.0

        if len(values) == 1:
            return values[0]

        if percent <= 0 or percent >= 100:
            return sum(values) / len(values)

        sorted_values = sorted(values)
        size = (len(sorted_values) - 1) / 100.0
        position = size * percent
        floor = int(position)

        if floor >= len(sorted_values) - 1:
            return sorted_values[-1]

        value = sorted_values[floor] + (sorted_values[floor + 1] - sorted_values[floor]) * (position - floor)
        return value


# 使用示例
def main():
    """使用示例"""
    wrapper = SaveDataWrapper(OSType.ANDROID)

    # 创建测试JSON文件
    import tempfile
    temp_dir = tempfile.gettempdir()
    test_file = os.path.join(temp_dir, "test_data.json")

    # 创建测试数据
    test_data = {
        "AppDisplayName": "",  # 应用显示名称（当前为空）
        "AppVersion": "9.02.10.30581",  # 应用版本号
        "AppPackageName": "com.tencent.qqlive",  # 应用包名（腾讯视频）
        "DeviceModel": "MEIZU 18",  # 设备型号（魅族18）
        "OSType": "ANDROID",  # 操作系统类型
        "OSVersion": "13",  # 操作系统版本（Android 13）
        "CpuType": "arm64-v8a",  # CPU架构（64位ARM架构）
        "GpuType": "",  # GPU类型
        "CaseName": "",  # 测试用例名称
        "AbsDataStartTime": 1759042512657,  # 数据采集开始时间戳（毫秒）
        "DataList": [
            {
                "AndroidFps": {
                    "Jank": 0,  # 卡顿次数（当前为0，表示无卡顿）
                    "fps": 57.633972  # 当前帧率
                },
                "TimeStamp": "5902",  # 数据采集时间戳（相对于开始时间的偏移）
                "BigJank": {
                    "BigJank": 0  # 大卡顿次数
                },
                "SmallJank": {
                    "SmallJank": 0  # 小卡顿次数
                },
                "Stutter": {
                    "Stutter": 0  # 卡顿率（0%）
                },
                "FrameTime": {
                    "FrameTime": [
                        {
                            "time": 4918,  # 帧的时间戳（相对于开始时间的偏移）
                            "frameTime": 16  # 单帧渲染时间（毫秒）
                        },
                        {
                            "time": 4935,
                            "frameTime": 16
                        },
                        {
                            "time": 5902,
                            "frameTime": 16
                        }
                    ]
                },
                "CpuUsage": {
                    "TotalUsage": 38.6,  # 总CPU使用率（百分比）
                    "AppUsage": 16.3  # 应用CPU使用率（百分比）
                },
                "GpuUsage": {
                    "GpuUsage": 14.765758  # GPU使用率（百分比）
                },
                "Temperature": {
                    "CpuTemperature": 49,  # CPU温度（°C）
                    "BatteryTemperature": 43  # 电池温度（°C）
                },
                "Power": {
                    "Current": 0,  # 电流（mA）
                    "Voltage": 4391,  # 电压（mV，4.391V）
                    "Power": 0,  # 功耗（mW）
                    "BatLevel": 100  # 电池电量（%）
                },
                "AndroidMemoryUsage": {
                    "Memory": 1018.5419921875,  # 内存使用量
                    "SwapMemory": 0.2412109375  # 交换内存使用量
                },
                "VirtualMemory": {
                    "VirtualMemory": 359752  # 虚拟内存使用量
                },
                "NetworkUsage": {
                    "UpSpeed": 3.2822266,  # 上传速度（网络上传速度）
                    "DownSpeed": 2.7773438  # 下载速度（网络下载速度）
                },
                "IsDelete": False
            }
        ]
    }

    # 写入测试文件
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)

    # 直接处理JSON文件
    success = wrapper.process_json_file(
        file_path=test_file
    )

    if success:
        logger.info("处理成功")
    else:
        logger.error("处理失败")


if __name__ == "__main__":
    main()
