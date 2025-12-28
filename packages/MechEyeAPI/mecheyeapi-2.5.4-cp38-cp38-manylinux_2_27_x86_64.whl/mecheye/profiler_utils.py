from mecheye.profiler import *
from mecheye.shared import *
import numpy as np


def print_profiler_info(profiler_info: ProfilerInfo):
    print(".........................................")
    print("Model:                         ", profiler_info.model, sep="")
    print("Device name:                   ", profiler_info.device_name, sep="")
    print("Controller serial number:      ",
          profiler_info.controller_sn, sep="")
    print("Sensor head serial number:     ", profiler_info.sensor_sn, sep="")
    print("IP address:                    ", profiler_info.ip_address, sep="")
    print("Subnet mask:                   ", profiler_info.subnet_mask, sep="")
    print("IP address assignment method:  ", ip_assignment_method_to_string(
        profiler_info.ip_assignment_method), sep="")
    print("Hardware version:              V",
          profiler_info.hardware_version.to_string(), sep="")
    print("Firmware version:              V",
          profiler_info.firmware_version.to_string(), sep="")
    status = "Supported" if profiler_info.supported else "Unsupported"
    print("Support status:                ",status, sep="")
    if not profiler_info.last_supported_version.is_empty():     
        print("Last supported version:        V",
            profiler_info.last_supported_version.to_string(), sep="")             
    print(".........................................")
    print()


def find_and_connect(profiler: Profiler) -> bool:
    print("Looking for available profilers...")
    profiler_infos = Profiler.discover_profilers()

    if len(profiler_infos) == 0:
        print("No profilers are available.")
        return False

    for i in range(len(profiler_infos)):
        print("Mech-Eye device index : ", i)
        print_profiler_info(profiler_infos[i])

    print("Enter the index of the device to which you want to connect: ")
    input_index = 0

    while True:
        input_index = input()
        if input_index.isdigit() and 0 <= int(input_index) < len(profiler_infos):
            input_index = int(input_index)
            break
        print("The entered index is invalid. Please enter the device index again: ")

    error_status = profiler.connect(profiler_infos[input_index])
    if not error_status.is_ok():
        show_error(error_status)
        return False

    print("Successfully connected to the profiler.")
    return True


def find_and_connect_multi_profiler() -> list:
    print("Looking for available profilers...")

    profiler_infos = Profiler.discover_profilers()

    if len(profiler_infos) == 0:
        print("No profilers are available.")
        return []

    for i in range(len(profiler_infos)):
        print("Mech-Eye device index: ", i)
        print_profiler_info(profiler_infos[i])

    indices = set()

    while True:
        print("Enter the indices of the devices to which you want to connect: ")
        print("Enter the character \"c\" at the end of all the indices")

        input_index = input()
        if input_index == 'c':
            break
        if input_index.isdigit() and 0 <= int(input_index) < len(profiler_infos):
            indices.add(int(input_index))
        else:
            print(
                "The entered indices are invalid. Please enter the device indices again: ")

    profilers = []
    for index in indices:
        profiler = Profiler()
        status = profiler.connect(profiler_infos[index])
        if status.is_ok():
            profilers.append(profiler)
        else:
            show_error(status)

    return profilers


def confirm_capture() -> bool:
    print("Do you want the profiler to capture image? Enter \"y\" to confirm or \"n\" to cancel: ")
    while True:
        input_str = input()
        if input_str == "y" or input_str == "Y":
            return True
        elif input_str == "n" or input_str == "N":
            print("The capture command was canceled.")
            return False
        else:
            print(
                "The entered character was invalid. Please enter \"y\" ot confirm or \"n\" to cancel:")


def print_profiler_status(profiler_status: ProfilerStatus):
    print(".....Profiler temperatures.....")
    print("Controller CPU: ",
          f"{profiler_status.temperature.controller_cpu_temperature:.1f}", "°C", sep="")
    print("Sensor CPU:     ",
          f"{profiler_status.temperature.sensor_cpu_temperature:.1f}", "°C", sep="")
    print("...............................")
    print()


def get_trigger_interval_distance() -> float:
    while True:
        print(
            "Please enter encoder trigger interval distance (unit: um, min: 1, max: 65535): ")
        trigger_interval_distance = input()
        if trigger_interval_distance.isdigit() and 1 <= float(trigger_interval_distance) <= 65535:
            return float(trigger_interval_distance)
        print("Input invalid!")


def save_point_cloud(profile_batch: ProfileBatch, user_set: UserSet, save_ply: bool = True, save_csv: bool = True, is_organized: bool = True):
    if profile_batch.is_empty():
        return

    error, x_resolution = user_set.get_float_value(
        XAxisResolution.name)
    if not error.is_ok():
        show_error(error)
        return

    error, y_resolution = user_set.get_float_value(YResolution.name)
    if not error.is_ok():
        show_error(error)
        return
    # # Uncomment the following line for custom Y Unit
    # y_resolution = get_trigger_interval_distance()

    error, line_scan_trigger_source = user_set.get_enum_value(
        LineScanTriggerSource.name)
    if not error.is_ok():
        show_error(error)
        return
    use_encoder_values = line_scan_trigger_source == LineScanTriggerSource.Value_Encoder

    error, trigger_interval = user_set.get_int_value(
        EncoderTriggerInterval.name)
    if not error.is_ok():
        show_error(error)
        return

    print("Save the point cloud.")
    if (save_csv):
        profile_batch.save_untextured_point_cloud(x_resolution, y_resolution, use_encoder_values,
                                                  trigger_interval, FileFormat_CSV, "PointCloud.csv", CoordinateUnit_Millimeter, is_organized)
    if (save_ply):
        profile_batch.save_untextured_point_cloud(x_resolution, y_resolution, use_encoder_values,
                                                  trigger_interval, FileFormat_PLY, "PointCloud.ply", CoordinateUnit_Millimeter, is_organized)
