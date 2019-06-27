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
parser.add_argument('-dr', '--dump-regs', default=False, action="store_true", help="Dump regs at given breakpoint to terminal.")
parser.add_argument('-y', '--force-yes', default=False, action="store_true", help="Skip the continue (please run once without this option).")
args = parser.parse_args()


print("A few notes:\nPLEASE put program in current directory!!!\n"
      "I think I did a good job, but program is still in testing phase ... \n... So keep any eye out for bugs\n"
      "Be careful about names! adb push will delete!\nALSO any UnicornContext* in current directory may delete!\n"
      "Example usage: my_program 0xffffffff -a arg1 -a arg2\n")

if not args.force_yes:
    ans = raw_input("Continue: (y/n): ")
else:
    ans = 'y'

if ans == 'y':
    print("[+] Starting to parse arguments ...")
    failed = False
    if not args.args_for_program:
        args.args_for_program = ""
        print("[*] No args for program.")
    else:
        args.args_for_program = ' '.join(args.args_for_program)
        print("[*] Args for program are: " + args.args_for_program)
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
    instruct.write("b *" + args.breakpoint + "\n")
    instruct.write("c" + "\n")
    instruct.write("source " + args.path_to_dumper + "\n")
    instruct.write("quit\n")
    instruct.close()

    if args.debug:
        os.system("adb push " + args.program + " /data/local/tmp")
        os.system("adb forward tcp:" + args.port + " tcp:" + args.port)
        os.system("adb shell su -c chmod +x /data/local/tmp/" + args.program)
        # os.system("adb shell su -c " + args.path_to_gdbserver + " :" + args.port + " /data/local/tmp/" + args.program + " " + args.args_for_program + " &")
        os.system("adb shell su -c " + args.path_to_gdbserver + " :" + args.port + " /data/local/tmp/" + args.program + " " + args.args_for_program + "> /dev/null 2>&1 &")
        os.system("arm-linux-gnueabi-gdb " + args.program + " < " + output_path)
        # subprocess.check_output("adb shell su -c rm /data/local/tmp/" + args.program, shell=True)
        # subprocess.check_output("adb forward --remove-all", shell=True)
        # subprocess.check_output("rm " + output_path, shell=True)
        exit(0)

    if not failed:
        try:
            subprocess.check_output("adb push " + args.program + " /data/local/tmp", shell=True)
            print("[+] Pushed program to /data/local/tmp")
            subprocess.check_output("adb forward tcp:" + args.port + " tcp:" + args.port, shell=True)
            os.system("adb shell su -c chmod +x /data/local/tmp/" + args.program + "> /dev/null 2>&1")
            os.system("adb shell su -c " + args.path_to_gdbserver + " :" + args.port + " /data/local/tmp/" + args.program + " " + args.args_for_program + "> /dev/null 2>&1 &")
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
            print("[-] Something went wrong with GDB ... either GDB isn't here, breakpoint didn't work, or the paths for the dumper/gef are off.")
            failed = True

    output_path1 = args.program + "_" + args.breakpoint

    if not failed:
        print("[+] GDB finished!")

    if not failed:
        os.system("cp -r UnicornContext* " + "herelolol")
        if args.dump_regs:
            print("[*] Preparing to print registers ...")
            try:
                index_file_path = os.path.join(os.getcwd() + "/herelolol", "_index.json")
                if not os.path.isfile(index_file_path):
                    raise Exception("Index file not found. Expected it to be at {}".format(index_file_path))
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

    print("[*] Cleaning up :)")
    try:
        subprocess.check_output("adb shell su -c rm /data/local/tmp/" + args.program, shell=True)
        subprocess.check_output("adb forward --remove-all", shell=True)
        subprocess.check_output("rm " + output_path, shell=True)
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