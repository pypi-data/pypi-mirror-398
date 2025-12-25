
'''
*****************************************************************************************
*
*        =================================================
*             Builder Bot Theme (eYRC 2024-25)
*        =================================================
*
*  This script is intended to check the versions of the installed
*  software/libraries in Task 0A of Builder Bot Theme (eYRC 2024-25).
*
*  Filename:			task0a_cardinal.py
*  Created:				16/07/2024
*  Last Modified:		24/08/2024
*  Author:				Paras Padole, e-Yantra Team
*  
*  This software is made available on an "AS IS WHERE IS BASIS".
*  Licensee/end user indemnifies and will keep e-Yantra indemnified from
*  any and all claim(s) that emanate from the use of the Software or 
*  breach of the terms of this agreement.
*  
*  e-Yantra - An MHRD project under National Mission on Education using ICT (NMEICT)
*
*****************************************************************************************
'''


# Import modules
import time
import string
import random
import re
import base64
from datetime import datetime
import os, sys
import platform
# from unittest import result
import cryptocode
sys.path.insert(0, 'pythonAPI')
from zmqRemoteApi import RemoteAPIClient 
from oauth2client.service_account import ServiceAccountCredentials # type: ignore
import gspread # type: ignore

#############################################
# third-party imprts
import distro
from eyantra_autoeval.utils.common import is_docker, run_shell_command
from rich import print
from rich.console import Console
from rich.prompt import Confirm

################################


# scope = ['https://www.googleapis.com/auth/spreadsheets', "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

# credentials = {
# 		"type": "service_account",
# 		"project_id": "bb-logs-431613",
# 		"private_key_id": "a4506d44024339472c6cae03bddb65257200038b",
# 		"private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDA2GeVj68LVk+O\nsEDyOBAIhRH/0BFaD/rf2Swws+5G3EwC6qddOThCkMNsT4CuzpCLUeC9Na+bZCqZ\ngqv3+ygHCNFzCbVhtAu0/L5BlaYAtSOlwdayEJRcA4d1zyIZ9cvzDne8DKiMzcnU\nbQ1UsDCn5gET0GiHPmIYf7UJHc91TKRPa+echb+UPonL0q/BTXnpiNDDKBDPNdM3\nSszl1Hx0oP+SWiWqsaPdKTUjJzRSBm8Sh3TJrvfENehDwoAg6O+UXbTvy7Jx/EGU\nvmbss0zTD3239KihiYa1flQdAYWZv5E8d9U2YSrye+r8+YLbOMqXaPx/xzXPlrfK\n3wp0YzjBAgMBAAECggEABVwGTfNpMpwWmDE5DtpExM3Y9RZ14v5Cc0XsetqHTuAY\nuzSFC/vW/s+Z5MjVW1ZZkUuoXq3PKHcJUYyehaTs5PwnYQZ2LGXV9PTYv0ceztJ5\n8AWB918rVl7RPRKRgK3yefnvFTJ3XTlraGxS9GV0prfnVAME4qxWytZCxGL4FOsM\n40sS6+V5w10KkS0hyBJU9I6AjZMGcVI96hLQtMlFQOQV62EntrV5o0++Bs6lGczp\nrFt/0u+hazMUlDzY3iKvpgayreO5X7qoJJm6dDWSo6Sfq4wlKA3VveUG+cM3t72R\nRE9eljYOCfw6QD9ORa8XBZtNfN9aGXZIoqKbU92TaQKBgQDlNn30gmczKdwkSRQo\nCt/pPU3+CZWhu5rCnXfeHbfzU9u5GrWH40llgQDjgWgxZqtu/uWZyPuo6AtVEwUy\nkh6HqdzdDx42rhG1GrTbAIiSOn606FG8kQjFps8yqIfVWlL9awiTnCppy2O5QFU0\n9UDDzJubFWkdhR5b4TFft11lKQKBgQDXYeHHduYcjtCrlL4CTI7WWaAqA+VknAES\nxS/+CPZjMOv0OyjYnppI03gEiA2y70n/P4NmdUcwvDnJK7mdvuwrRcvsKF+UeV2y\ng0v3xUzaFaxyasfFZuRCYv7pr1cG/hRcmRI5fd9dlS4xWpkXqe/Yc8oU8pGKkbY9\nz4lf09LR2QKBgQCIUgVNIzU/X5j216OuQPF0ZSp6eLbOTqY3MrH0nxYlGG2oRDNM\nkye2v6eIpxERuG8i/2QMN1U82mzK9xnzPqX7p1GdA33DpXkQjcacLVAML8/lxfm+\nvT9LVe8KwOKwSBztbPfX2lv7OaSgq5tBeM9A4/JzpKM0lFQ+7sqPk51vKQKBgGV8\nGYaC36pVIL24OE+dAzC8ylsBuvTNDTRq9VIdpvrV8lgCCB0JnmjyO3rnII1Pcu5y\nXtfIKuMrzY6cq7lIXL+HA68i1uZ+yUdz1jfJH40i6T6AUeERujwNqU8y7y68SZvY\nBF5SkQznXfyjU79yszCqXm3AXhOM1PIK+A/PH2cBAoGAMLztRveOQxy0eU0Cl9KE\nvL4qbH2XYGn1aEHPTY8Dpx4A1varNKhXzUtHGPhVWPB1Qq//jot6+DgClQ6Kda4C\n+Vh8+1GUxv3DihmGcCvwb8BXwpaPhB9qq/2HnoWvq1bSKnRvA5ab8LC1z/DV1DRZ\nfXKQhr8q5KB9QfMmD8IzhzI=\n-----END PRIVATE KEY-----\n",
# 		"client_email": "balancing-builder-bot@bb-logs-431613.iam.gserviceaccount.com",
# 		"client_id": "105579116913873875207",
# 		"auth_uri": "https://accounts.google.com/o/oauth2/auth",
# 		"token_uri": "https://oauth2.googleapis.com/token",
# 		"auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
# 		"client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/balancing-builder-bot%40bb-logs-431613.iam.gserviceaccount.com",
# 		"universe_domain": "googleapis.com"
# }

# client = gspread.service_account_from_dict(credentials)
# try:
# 	python_cell_update = client.open("BB_Logs").worksheet("task0A")
# 	print(python_cell_update)

# except:
# 	print("\n\t[ERROR] System not able to access internet!\n")
# 	sys.exit()
# values_list = python_cell_update.col_values(1)

# Flags to determine which modules are installed or not
platform_uname = None
conda_flag = None
python_flag = None
cv2_flag = None
numpy_flag = None
matplotlib_flag = None
jupyter_flag = None


# Flags to determine whether the modules installed have correct version or not
conda_env_name_flag = None

# Output file name
file_name = "task0A_output.txt"

# Flag and Global variables to determine whether the CoppeliaSim Remote API Server works fine
coppeliasim_remote_api_flag = None
clientID = 0

left_motor_vel = 0
right_motor_vel = 0




  


# Check whether CoppeliaSim Remote API server is working fine
# def check_coppeliasim_remote_api():

result = {}

def extract_team_id(env_name):
    match = re.search(r'(\d+)', env_name)
    return match.group(0) if match else 'unknown'
 
def evaluate():
	
	# result = {}
	console = Console()
	global result,conda_env_name_flag,coppeliasim_remote_api_flag,left_motor_handle,right_motor_handle,left_motor_vel,right_motor_vel


	try:
			team_id = int(input('\n\tEnter your Team ID (for e.g.: "1234" or "321"): '))
	except ValueError:
			print("\n\t[ERROR] Enter your Team ID which is an integer!\n")
			sys.exit()

	conda_env_name = os.environ['CONDA_DEFAULT_ENV']

	expected_conda_env_name = 'KB_' + str(team_id)

			# Check current Conda environment name is as expected
	if conda_env_name == expected_conda_env_name:
					conda_env_name_flag = 1
	else:
					conda_env_name_flag = 0
					print("\n\t[WARNING] Conda environment name is not found as expected, Make sure it is: KB_%s, re-check the instructions\n" %(str(team_id)))
					result["generate"] = False
					#python_cell_update.update_cell(len(values_list)+1,1,str(team_id) +" Task 0A "+conda_env_name+ " Conda environment name is not found as expected, Make sure it is: BB_"+str(team_id)+", re-check the instructions")
					sys.exit()

	env_name = os.getenv('CONDA_DEFAULT_ENV', 'unknown')
	team_id = extract_team_id(env_name)
				

	platform_uname = platform.uname().system
	conda_env_name = os.getenv('CONDA_DEFAULT_ENV', 'unknown')
	current_time = datetime.now().strftime('%d-%m-%Y %H:%M:%S')

	client = RemoteAPIClient()
	sim = client.getObject('sim')
	defaultIdleFps = sim.getInt32Param(sim.intparam_idle_fps)
	sim.setInt32Param(sim.intparam_idle_fps, 0)

	
	sim.startSimulation()
	return_code=sim.loadModel(str(os.getcwd()+"/Differential_Drive_Robot.ttm"))
	left_motor_handle=sim.getObject('./left_joint')
	right_motor_handle=sim.getObject('./right_joint')


		
	command_msg = ''
	
	print("\n\tCommands to control robot locomotion are:")
	print("\t+-------------------------------------------------------+")

	print("	|	Command to execute	|	Char Input	|")
	print("\t+-------------------------------------------------------+")

	print("	|	Move Forward		| 	'w' OR 'W'	|")
	print("	|	Move Backward		| 	's' OR 'S'	|")
	print("	|	Turn Left		| 	'a' OR 'A'	|")
	print("	|	Turn Right		| 	'd' OR 'D'	|")
	print("	|	Stop			| 	'x' OR 'X'	|")
	print("	|	Quit the program	| 	'q' OR 'Q'	|")
	print("\t+-------------------------------------------------------+")

	while(True):
		
		inp_char = input("\n\tEnter any one of these as input (w, W | a, A | s, S | d, D | x, X | q, Q): ")

		if len(inp_char) == 1:
			
			if inp_char == 'w' or inp_char == 'W':
				left_motor_vel = 2
				right_motor_vel = 2
				command_msg = "Move Forward"
				# print("\n\tmove forward")

			elif inp_char == 'a' or inp_char == 'A':
				left_motor_vel = -2
				right_motor_vel = 2
				command_msg = "Turn Left"
				# print("\n\tturn left")

			elif inp_char == 'd' or inp_char == 'D':
				left_motor_vel = 2
				right_motor_vel = -2
				command_msg = "Turn Right"
				# print("\n\tturn right")

			elif inp_char == 's' or inp_char == 'S':
				left_motor_vel = -2
				right_motor_vel = -2
				command_msg = "Move Backward"
				# print("\n\tmove backward")

			elif inp_char == 'x' or inp_char == 'X':
				left_motor_vel = 0
				right_motor_vel = 0
				command_msg = "Stop"
				# print("\n\tstop")
				
			elif inp_char == 'q' or inp_char == 'Q':
				command_msg = "Quit the program"
				console.print("\n\t\tCommand executed: ", command_msg)
				console.print("\n\t\tCommand executed: ", command_msg)
				result["generate"] = False
				# print("\n\tquitting")
				sim.stopSimulation()
				break
				# return coppeliasim_remote_api_flag

			else:
				coppeliasim_remote_api_flag = 0
				# print("\n\t[WARNING] No command associated with input: ", inp_char)
				# print("\tKinldy provide any one of these as input: w, W, a, A, s, S, d, D, q or Q.")
				console.print("\n\t[WARNING] No command associated with input: ", inp_char)
				console.print("\tKinldy provide any one of these as input: w, W, a, A, s, S, d, D, q or Q.")
				# exit_remote_api_server()
				result["generate"] = False
				sim.stopSimulation()
				break
				# return coppeliasim_remote_api_flag

		else:
			coppeliasim_remote_api_flag = 0
			# print("\n\t[WARNING] Kinldy provide input of only single character!")
			console.print("\n\t[WARNING] Kindly provide input of only single character!")
			# exit_remote_api_server()
			result["generate"] = False
			sim.stopSimulation()
			break
			return coppeliasim_remote_api_flag

		# Set target velocity of both the motors to specific deg/s to make the robot move forward
		return_code=sim.setJointTargetVelocity(left_motor_handle,left_motor_vel)
		return_code=sim.setJointTargetVelocity(right_motor_handle,right_motor_vel)
		console.print("\n\t\tCommand executed: ", command_msg)
		coppeliasim_remote_api_flag = 1
		# break
#########################################################
				
	if (conda_env_name_flag == 1):		
		# coppeliasim_remote_api_flag = check_coppeliasim_remote_api()
	
		if coppeliasim_remote_api_flag != 1:
				console.print("\n\tSomething went wrong. Robot locomotion commands weren't executed!\n")
				console.print("\tBye, see you! Run the program again.\n")
				Coppeliasim = "CoppeliaSim is not working fine"
				result["generate"] = False
				#python_cell_update.update_cell(len(values_list)+1,1,str(team_id)+ " Task 0A "+conda_env_name+" Something went wrong. Robot locomotion commands weren't executed in coppeliasim!" )
				sys.exit()
		else:
				console.print("\n\tVoila, CoppeliaSim Remote API Server works seamlessly!\n")
				Coppeliasim = "CoppeliaSim is working fine!"
				result["generate"] = False
	else:
					sys.exit()

	if os.path.exists(file_name):
		os.remove(file_name)

	if (coppeliasim_remote_api_flag == 1) :
					print('\n\t Python and Coppeliasim tested OK')
					result["generate"] = False
					output_file = open(file_name, "w")
	
					
	platform_uname = cryptocode.encrypt(str(platform_uname), "joker")
	team_id = cryptocode.encrypt(str(team_id), "batman")
	conda_env_name = cryptocode.encrypt(str(conda_env_name), "superman")
	Coppeliasim =  cryptocode.encrypt(str(Coppeliasim), "flash")
	current_time =cryptocode.encrypt(str(current_time), "bane")

	finaldata=[str(team_id)+"\n", str(conda_env_name)+"\n", str(current_time)+"\n", str(platform_uname)+"\n",str(Coppeliasim)+"\n"]
	output_file.writelines(finaldata)
	output_file.close()
			
	# print(platform_uname)              

	print("\t+--------------------------------------------------------------------------+")
	print("	|                          $$$$$$$$$$$$$$$$$$$$$                          |")
	print("	|                       $$$$$$$$$$$$$$$$$$$$$$$$$$$                       |")                          
	print("	|                     $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                     |")
	print("	|                   $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                   |")
	print("	|                 $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                 |")
	print("	|                $$$$$$$$$$    $$$$$$$$$$$$$    $$$$$$$$$$                |")
	print("	|               $$$$$$$$$$      $$$$$$$$$$$      $$$$$$$$$$$              |")    
	print("	|              $$$$$$$$$$$      $$$$$$$$$$$      $$$$$$$$$$$$             |")
	print("	|             $$$$$$$$$$$$$    $$$$$$$$$$$$$    $$$$$$$$$$$$$$            |")
	print("	|            $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$           |")
	print("	|           $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$          |")
	print("	|           $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$          |")
	print("	|           $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ $$$$$          |")
	print("	|            $$$$  $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$   $$$$           |")
	print("	|            $$$$   $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$     $$$$           |")
	print("	|             $$$$    $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$      $$$$            |")
	print("	|              $$$$     $$$$$$$$$$$$$$$$$$$$$$$$$         $$$             |")
	print("	|               $$$$          $$$$$$$$$$$$$$$           $$$$              |")
	print("	|                $$$$$                                $$$$$               |")
	print("	|                 $$$$$$                            $$$$$                 |")
	print("	|                   $$$$$$$                      $$$$$$$                  |")
	print("	|                      $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                     |")
	print("	|                         $$$$$$$$$$$$$$$$$$$$$$$                         |")
	print("	|                            $$$$$$$$$$$$$$$$$                            |")
	print("\t+--------------------------------------------------------------------------+")
			
	if result["generate"]:
		console.print("\n\t[INFO] CoppeliaSim is working fine!\n")    
	return result

# l= evaluate()
# print(l)
# Test the Setup and Check versions of the above imported modules
#if __name__ == '__main__':

	#test_setup()
