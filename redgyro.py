#!/usr/bin/env python3

import subprocess
import os
import sys
import csv
import sys
import glob

auto_detect_redline = True
redline_path = "redline" # Overwride here if no auto detect

redline_paths = [
	"redline",
	"C:/Program Files/REDCINE-X PRO One-Off 64-bit/redline",
	"C:/Program Files/REDCINE-X PRO 64-bit/redline"
]

if redline_path not in redline_paths:
	redline_paths.insert(0, redline_path)

if auto_detect_redline:
	found = False
	for path in redline_paths:
		try:
			process = subprocess.Popen([path],
								stdout=subprocess.PIPE, 
						        stderr=subprocess.PIPE)
			print(f"Found redline at: {path}")
			redline_path = path
			found = True
			break
		except FileNotFoundError:
			pass

	if not found:
		raise RuntimeError("REDline not found.... Please ensure redline is in the PATH")


def run_redline(video, params=[], show_error=False):
	process = subprocess.Popen([redline_path, "--i", video, "--useMeta"] + params,
                     stdout=subprocess.PIPE, 
                     stderr=subprocess.PIPE)
	stdout, stderr = process.communicate()
	stdout = stdout.decode()
	stderr = stderr.decode()
	if stderr and show_error:
		print("Error:")
		print(stderr)

	return stdout, stderr

def write_gcsv(video, meta_data, imu_data, tscale=1, gscale=0.01745329251, ascale=1, orientation="zyx"):
	outfile = video.rstrip("R3D").rstrip("r3d")+"gcsv"
	print(f"Writing {outfile}")
	with open(outfile, "w") as out:
		out.write(f"GYROFLOW IMU LOG\nversion,1.1\nid,RED Cinema {meta_data.get('Camera Model')}\n")
		out.write(f"orientation,{orientation}\n")
		out.write(f"note,R3D to gcsv converter\n")
		out.write(f"tscale,{tscale}\n")
		out.write(f"gscale,{gscale}\n")
		out.write(f"ascale,{ascale}\n")
		out.write("t,gx,gy,gz,ax,ay,az\n")

		for line in imu_data:
			out.write(",".join([str(x) for x in line]) + "\n")

def read_csv_string(s):
	lines = s.splitlines()
	header = lines[0]
	parsed_data = {}
	fields = header.split(",")
	for field in fields:
		parsed_data[field] = []

	for line in lines[1:]:
		for i, data in enumerate(line.split(",")):
			parsed_data[fields[i]].append(data)

	return parsed_data, fields

def get_metadata_gyro(video):
	meta_1, _ = run_redline(video, ["--printMeta", "1"])
	meta_1_dict = {}
	for line in meta_1.splitlines():
		split_line = line.split(":\t")
		if len(split_line) == 2:
			meta_1_dict[split_line[0]] = split_line[1]
	
	cam_model = meta_1_dict.get("Camera Model")
	if cam_model == None:
		print("No valid metadata found")
		return False

	print(f"Camera: {cam_model}")
	FPS = float(meta_1_dict["Record FPS"])

	meta_7, _ = run_redline(video, ["--printMeta", "7"])
	has_async_imu = meta_7 != ""
	if has_async_imu:
		print("Using async IMU data")

		parsed, fields = read_csv_string(meta_7)
		tscale = 1e-6
		timestamp = [int(t) for t in parsed["Timestamp"]]
		# start at zero
		timestamp = [t-timestamp[0] for t in timestamp]
		N = len(timestamp)
		sample_rate = N/((timestamp[-1] - timestamp[0]) * tscale)
		imu_data = []
		# Remove redundant zeros
		gx, gy, gz = [[val.rstrip("0") for val in parsed[field]] for field in ["Rotation X", "Rotation Y", "Rotation Z"]]
		ax, ay, az = [[val.rstrip("0") for val in parsed[field]] for field in ["Acceleration X", "Acceleration Y", "Acceleration Z"]]
		for i in range(N):
			imu_data.append([timestamp[i], gx[i], gy[i], gz[i], ax[i], ay[i], az[i]])

		gscale = 0.1745329251 # 10 * pi/180
		write_gcsv(video, meta_1_dict, imu_data, tscale, gscale, 1)
		return True

	else:
		meta_5, _ = run_redline(video, ["--printMeta", "5"])
		has_perframe_imu = meta_5 != ""
		if has_perframe_imu:
			print("Using per frame IMU data")

			parsed, fields = read_csv_string(meta_5)
			motion_check = [float(rx)==0 for rx in parsed["Rotation X"]]
			if not False in motion_check:
				print("No motion found, skipping")
				return False

			imu_data = []
			# Remove redundant zeros
			gx, gy, gz = [[val.rstrip("0") for val in parsed[field]] for field in ["Rotation X", "Rotation Y", "Rotation Z"]]
			ax, ay, az = [[val.rstrip("0") for val in parsed[field]] for field in ["Acceleration X", "Acceleration Y", "Acceleration Z"]]
			for i in range(len(parsed["FrameNo"])):
				imu_data.append([parsed["FrameNo"][i], gx[i], gy[i], gz[i], ax[i], ay[i], az[i]])

			gscale = 0.01745329251 # pi/180
			write_gcsv(video, meta_1_dict, imu_data, 1/FPS, gscale, 1)
			return True
		
		else:
			print("No IMU data found")
			return False

if __name__ == "__main__":
	args = sys.argv

	if len(args) != 2:
		print("-- Basic R3D to gcsv converter --")
		print("Requires REDline installed")
		print("USAGE: ")
		print("Convert file to gcsv:\npython redgyro.py <filename.R3D>\n")
		print("Or convert all R3D files in working dir:\npython redgyro.py --all")
	
	elif len(args) == 2:
		if args[1] == "--all":
			r3d_files = glob.glob("*.R3D")
			print("Converting following files (note: split files may be processed multiple times...):")
			print("\n".join(r3d_files))
			for file in r3d_files:
				print(f"\nConverting {file}...")
				succ = get_metadata_gyro(file)
				print("Successfully converted file" if succ else "Failed to convert file")
		else:
			if os.path.isfile(args[1]):
				get_metadata_gyro(args[1])
			else:
				raise FileNotFoundError(f"File {args[1]} not found")