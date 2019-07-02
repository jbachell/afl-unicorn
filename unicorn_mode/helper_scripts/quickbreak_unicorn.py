import os
import argparse
import subprocess
import datetime
import time
import json


parser = argparse.ArgumentParser()
parser.add_argument('program', type=str, help="Path to program.  MUST be in current directory!")
parser.add_argument('-a', '--args_for_program', help="Arguments for program to run with.  Default is none.", action="append")
parser.add_argument('breakpoint', type=str, help="Breakpoint to start dump at, use only hex string, including 0x")
parser.add_argument('--path_to_gef', help="Looking for gef.py.  Default will be current directory.", action="store")
parser.add_argument('--path_to_dumper', help="Looking for unicorn_dumper_gdb.py.  Default will be current directory.", action="store")
parser.add_argument('--path_to_gdbserver', help="Looking for gdbserver on phone.  Default will be /data/local/tmp/gdbserver/gdbserver", action="store")
parser.add_argument('-p', '--port', help="Port to listen to.", action="store")
parser.add_argument('-d', '--debug', default=False, action="store_true", help="Dump all commandline info.")
parser.add_argument('--attach', default=False, action="store_true", help="Attach to running program.")
parser.add_argument('-dr', '--dump-regs', default=False, action="store_true", help="Dump regs at given breakpoint to terminal.")
parser.add_argument('-y', '--force-yes', default=False, action="store_true", help="Skip the continue (please run once without this option).")
args = parser.parse_args()


if not args.force_yes:
    print("\nA few notes:\n\nPLEASE put program in current directory!!! \nThis program will not work without it there!\n"
          "I think I did a good job, but program is still in testing phase ... \n... So keep any eye out for bugs\n"
          "Be careful about names! adb push will delete!\nALSO any UnicornContext* in current directory may delete!\n"
          "-h for full list of arguments, "
          "-y to avoid this menu\n"
          "\nExample usage: my_program 0xffffffff -a arg1 -a arg2\n"
          "               my_program main -a arg1 -a arg2\n")

    ans = raw_input("Continue: (y/n): ")
else:
    ans = 'y'

if ans == 'y':
    print("[+] Starting to parse arguments ...")
    failed = False
    try:
        print("[*] Breaking at " + str(hex((int(args.breakpoint, 16)))) + " in assembly.")
        breakFunc = False
    except:
        breakFunc = True
        print("[*] Breaking at function " + args.breakpoint)
    if not args.args_for_program:
        args.args_for_program = ""
        print("[*] No args for program.")
    else:
        args.args_for_program = ' '.join(args.args_for_program)
        print("[*] Args for program are: " + args.args_for_program)
        if args.attach:
            print("[-] WARNING! Program arguments are not used in attach mode.")
    if not args.port:
        args.port = "4321"
    print("[*] Port set to: " + args.port)
    if not args.path_to_gef:
        args.path_to_gef = "gef.py"
        print("[*] Looking for gef.py in current directory.")
    else:
        print("[*] Path to gef is " + args.path_to_gef)
    if not args.path_to_dumper:
        args.path_to_dumper = "unicorn_dumper_gdb.py"
        print("[*] Looking for unicorn_dumper_gdb.py in current directory.")
    else:
        print("[*] Path for dumper is " + args.path_to_dumper)
    if not args.path_to_gdbserver:
        args.path_to_gdbserver = "/data/local/tmp/gdbserver/gdbserver"
        print("[*] Path for gdbserver is /data/local/tmp/gdbserver/gdbserver")
    else:
        print("[*] Path for gdbserver is " + args.path_to_gdbserver)

    timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d')
    output_path = "Instructions_" + timestamp
    instruct = open(str(output_path), "w+")

    instruct.write("source " + args.path_to_gef + "\n")
    instruct.write("target remote :" + args.port + "\n")
    if not breakFunc:
        instruct.write("b *" + args.breakpoint + "\n")
    else:
        instruct.write("b " + args.breakpoint + "\n")
    instruct.write("c" + "\n")
    instruct.write("source " + args.path_to_dumper + "\n")
    instruct.write("quit\n")
    instruct.close()

    if args.debug:
        os.system("adb push " + args.program + " /data/local/tmp")
        os.system("adb forward tcp:" + args.port + " tcp:" + args.port)
        os.system("adb shell su -c chmod +x /data/local/tmp/" + args.program)
        # os.system("adb shell su -c " + args.path_to_gdbserver + " :" + args.port + " /data/local/tmp/" + args.program + " " + args.args_for_program + " &")
        if not args.attach:
            os.system("adb shell su -c " + args.path_to_gdbserver + " :" + args.port + " /data/local/tmp/" + args.program + " " + args.args_for_program + "> /dev/null 2>&1 &")
        else:
            # Copied code from below!
            output__path = "Instructions__attach" + timestamp
            instruct = open(str(output__path), "w+")

            print("[*] Attaching to PID ... (Can fail if multiple PID's exist)")

            instruct.write("su" + "\n")
            instruct.write("pidof " + args.program + "> data/local/tmp/pid_lolhere.txt\n")
            instruct.write(args.path_to_gdbserver + " --attach :" + args.port + " `cat /data/local/tmp/pid_lolhere.txt`" + " > /dev/null 2>&1 &" + "\n")
            instruct.write("rm " + "/data/local/tmp/pid_lolhere.txt\n")
            instruct.close()

            os.system("adb shell < " + output__path)
        os.system("arm-linux-gnueabi-gdb " + args.program + " < " + output_path)
        # subprocess.check_output("adb shell su -c rm /data/local/tmp/" + args.program, shell=True)
        # subprocess.check_output("adb forward --remove-all", shell=True)
        # subprocess.check_output("rm " + output_path, shell=True)
        print("\n\nIf --attach was used, other errors might be possible.  Check instructions__attach in your current directory.")
        exit(0)

    if not failed:
        try:
            subprocess.check_output("adb forward tcp:" + args.port + " tcp:" + args.port, shell=True)
            if not args.attach:
                subprocess.check_output("adb push " + args.program + " /data/local/tmp", shell=True)
                print("[+] Pushed program to /data/local/tmp")
                os.system("adb shell su -c chmod +x /data/local/tmp/" + args.program + "> /dev/null 2>&1")
                os.system("adb shell su -c " + args.path_to_gdbserver + " :" + args.port + " /data/local/tmp/" + args.program + " " + args.args_for_program + "> /dev/null 2>&1 &")
            else:
                output__path = "Instructions__attach" + timestamp
                instruct = open(str(output__path), "w+")

                print("[*] Attaching to PID ...")

                instruct.write("su" + "\n")
                instruct.write("pidof " + args.program + "> data/local/tmp/pid_lolhere.txt\n")
                instruct.write(args.path_to_gdbserver + " --attach :" + args.port + " `cat /data/local/tmp/pid_lolhere.txt`" + " > /dev/null 2>&1 &" + "\n")
                instruct.write("rm " + "/data/local/tmp/pid_lolhere.txt\n")
                instruct.close()

                os.system("adb shell < " + output__path)

                print("[+] Attached successfully!")
            print("[+] Started listener")
        except:
            print("[-] Something went wrong with ADB, is your device connected? Is the program path right?")
            failed = True

    print("[*] Runing GDB ...")
    if not failed:
        try:
            print("[*] Any output from program's STDERR should show below ...")
            os.system("arm-linux-gnueabi-gdb " + args.program + " < " + output_path + "> /dev/null 2>&1")
        except:
            print("[-] Something went wrong with GDB ... either GDB isn't here, breakpoint didn't work, or the paths for the dumper/gef are off.  Trying '-d' might help.")
            failed = True

    output_path1 = args.program + "_" + args.breakpoint

    if not failed:
        print("[+] GDB finished!")

    if not failed:
        try:
            os.system("cp -r UnicornContext* " + "herelolol")
            if args.dump_regs:
                print("[*] Preparing to print registers ...")
                try:
                    index_file_path = os.path.join(os.getcwd() + "/herelolol", "_index.json")
                    if not os.path.isfile(index_file_path):
                        print("[-] Something went wrong, the json index file wasn't found.")
                        failed = True
                    index_file = open(index_file_path, 'r')
                    context = json.load(index_file)
                    print("Dump at breakpoint " + args.breakpoint + ":")
                    for reg, value in sorted (context['regs'].iteritems()):
                        print(">>> {0:>4}: 0x{1:016x}".format(reg, value))
                    index_file.close()
                    print("[+] Registers dumped!")
                except:
                    print("[-] Reading registers failed. Is json installed?")
            if len(os.listdir(os.getcwd() + '/herelolol')) == 0:
                print("[-] Unicorn failed to dump.  Try the '-d' option.  Maybe the listener isn't up?")
                subprocess.check_output("rm -r herelolol UnicornContext*", shell=True)
                failed = True
        except:
            print("[-] Missing directory, something went wrong.  ")
            failed = True

    print("[*] Cleaning up :)")
    try:
        subprocess.check_output("adb shell su -c rm /data/local/tmp/" + args.program, shell=True)
        subprocess.check_output("adb forward --remove-all", shell=True)
        subprocess.check_output("rm " + output_path, shell=True)
        if args.attach:
            subprocess.check_output("rm " + output__path, shell=True)
    except:
        print("[-] Clean up failed.")

    if not failed:
        if not os.path.exists(output_path1):
              os.makedirs(output_path1)
        os.system("mv UnicornContext* " + args.program + "_" + args.breakpoint)
        subprocess.check_output("rm -r herelolol", shell=True)
        print("[+] All set! Look for new directory named " + args.program + "_" + args.breakpoint)

    if failed:
        print("[-] Failed")

else:
    print("[-] Execution failed.")