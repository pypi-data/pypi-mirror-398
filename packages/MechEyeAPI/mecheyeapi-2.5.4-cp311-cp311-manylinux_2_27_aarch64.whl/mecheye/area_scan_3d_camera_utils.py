from mecheye.area_scan_3d_camera import *
from mecheye.shared import *


def print_camera_info(camera_info: CameraInfo):
    print(".............................")
    print("Model:                        ", camera_info.model, sep="")
    print("Device name:                  ", camera_info.device_name, sep="")
    print("Serial number:                ", camera_info.serial_number, sep="")
    print("IP address:                   ", camera_info.ip_address, sep="")
    print("Subnet mask:                  ", camera_info.subnet_mask, sep="")
    print("IP address assignment method: ", ip_assignment_method_to_string(
        camera_info.ip_assignment_method), sep="")
    print("Hardware version:             V",
          camera_info.hardware_version.to_string(), sep="")
    print("Firmware version:             V",
          camera_info.firmware_version.to_string(), sep="")
    status = "Supported" if camera_info.supported else "Unsupported"
    print("Support status:               ",
          status, sep="")
    if not camera_info.last_supported_version.is_empty():     
        print("Last supported version:       V",
            camera_info.last_supported_version.to_string(), sep="")       
    print(".............................")
    print()


def print_camera_status(camera_status: CameraStatus):
    print(".....Camera Temperature.....")
    print("CPU :               ",
          f"{camera_status.temperature.cpu_temperature:.1f}", "°C", sep="")
    print("Projector Module:   ",
          f"{camera_status.temperature.projector_temperature:.1f}", "°C", sep="")
    print("............................")
    print()


def print_camera_resolution(camera_resolution: CameraResolutions):
    print("Texture Map size : (width : ", camera_resolution.texture.width,
          ", height : ", camera_resolution.texture.height, ").", sep="")
    print("Depth Map size : (width : ", camera_resolution.depth.width,
          ", height: ", camera_resolution.depth.height, ").", sep="")


def print_camera_matrix(title: str, camera_matrix: CameraMatrix):
    print(title, ": ", sep="")
    print("    [", camera_matrix.fx, ", 0, ", camera_matrix.cx, "]", sep="")
    print("    [0, ", camera_matrix.fy, ", ", camera_matrix.cy, "]", sep="")
    print("    [0, 0, 1]")
    print()


def print_camera_dist_coeffs(title: str, dist_coeffs: CameraDistortion):
    print(title, ": ", sep="")
    print("    k1: ", dist_coeffs.k1, ", k2: ", dist_coeffs.k2, ", p1: ",
          dist_coeffs.p1, ", p2: ", dist_coeffs.p2, ", k3: ", dist_coeffs.k3, sep="")
    print()


def print_transform(title: str, transformation: Transformation):
    print("Rotation: ", title, ": ", sep="")
    for i in range(3):
        print("    [", end="")
        for j in range(3):
            print(transformation.rotation[i][j], end="")
            if j != 2:
                print(", ", end="")
        print("]")
    print()
    print("Translation ", title, ": ", sep="")
    print("    X: ", transformation.translation[0], "mm, Y: ",
          transformation.translation[1], "mm, Z: ", transformation.translation[2], "mm", sep="")
    print()


def print_camera_intrinsics(intrinsics: CameraIntrinsics):
    print_camera_matrix("Texture Camera Matrix",
                        intrinsics.texture.camera_matrix)
    print_camera_dist_coeffs(
        "Texture Camera Distortion Coefficients", intrinsics.texture.camera_distortion)

    print_camera_matrix("Depth Camera Matrix", intrinsics.depth.camera_matrix)
    print_camera_dist_coeffs(
        "Depth Camera Distortion Coefficients", intrinsics.depth.camera_distortion)

    print_transform("From Depth Camera to Texture Camera",
                    intrinsics.depth_to_texture)


def find_and_connect(camera: Camera) -> bool:
    print("Looking for available cameras...")
    camera_infos = Camera.discover_cameras()

    if len(camera_infos) == 0:
        print("No cameras are available.")
        return False

    for i in range(len(camera_infos)):
        print("Mech-Eye device index :", i)
        print_camera_info(camera_infos[i])

    print("Enter the index of the device to which you want to connect: ")
    input_index = 0

    while True:
        input_index = input()
        if input_index.isdigit() and 0 <= int(input_index) < len(camera_infos):
            input_index = int(input_index)
            break
        print("The entered index is invalid. Please enter the device index again: ")

    error_status = camera.connect(camera_infos[input_index])
    if not error_status.is_ok():
        show_error(error_status)
        return False

    print("Successfully connected to the camera.")
    return True


def find_and_connect_multi_camera() -> list:
    print("Looking for available cameras...")

    camera_infos = Camera.discover_cameras()

    if len(camera_infos) == 0:
        print("No cameras are available.")
        return []

    for i in range(len(camera_infos)):
        print("Mech-Eye device index: ", i)
        print_camera_info(camera_infos[i])

    indices = set()

    while True:
        print("Enter the indices of the devices to which you want to connect: ")
        print("Enter the character \"c\" at the end of all the indices")

        input_index = input()
        if input_index == 'c':
            break
        if input_index.isdigit() and 0 <= int(input_index) < len(camera_infos):
            indices.add(int(input_index))
        else:
            print(
                "The entered indices are invalid. Please enter the device indices again: ")

    cameras = []
    for index in indices:
        camera = Camera()
        status = camera.connect(camera_infos[index])
        if status.is_ok():
            cameras.append(camera)
        else:
            show_error(status)

    return cameras


def confirm_capture_3d() -> bool:
    print("Do you want the camera to capture 3D data? Enter \"y\" to confirm or \"n\" to cancel: ")
    while True:
        input_str = input()
        if input_str == "y" or input_str == "Y":
            return True
        elif input_str == "n" or input_str == "N":
            print("The capture command was canceled.")
            return False
        else:
            print(
                "The entered character was invalid. Please enter \"y\" to confirm or \"n\" to cancel:")
