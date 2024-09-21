#!/usr/bin/python3.6

import lief
import zipfile
import shutil
import subprocess
import tempfile
import os
import pathlib
import sys
import getpass

APKSIGNER = "/Users/clearain/Library/Android/sdk/build-tools/35.0.0-rc1/apksigner"
ZIPALIGN = "/Users/clearain/Library/Android/sdk/build-tools/35.0.0-rc1/zipalign"
ADB       = "/opt/homebrew/bin/adb"
# KEYSTORE  = "keystore.jks"
# if not os.path.exists(KEYSTORE):
#     print(f"[-] {KEYSTORE} not found")
#     exit(1)
# KEYSTOREPASS = getpass.getpass("Enter keystore password: ")
RELEASEKEY = "releasekey.pk8"
RELEASECERT = "releasekey.x509.pem"
if not (os.path.exists(RELEASEKEY) and os.path.exists(RELEASECERT)):
    print(f"[-] {RELEASEKEY} or {RELEASECERT} not found")
    exit(1)

apk  = sys.argv[1]
lib  = "libgadget.so"
conf = "libgadget.config.so"
newapk = sys.argv[1].split('/')[-1].replace(".apk", "_new.apk")
libpath = sys.argv[2]
if not libpath.endswith(".so"):
    print(f"[-] {libpath} is not a library")
    exit(1)

workingdir = tempfile.mkdtemp(suffix='_lief_frida')

# Unzip
print(f"[+] Unzip the {apk} in {workingdir} using apktool")
os.system(f"apktool d {apk} -f -o {workingdir}")

# Add 'frida-gadget-10.7.3-android-arm64.so' to libtmessages.28.so
libdir = pathlib.Path(workingdir) / "lib"
libcheck_path = libdir / "arm64-v8a" / libpath


print(f"[+] Injecting {lib} into {libcheck_path}")
libcheck = lief.parse(libcheck_path.as_posix())

# Injection
libcheck.add_library("libgadget.so")
libcheck.write(libcheck_path.as_posix())

# Copy the hook library
print(f"[+] Copying {lib} and {conf} in the APK")
shutil.copy(lib, libdir / "arm64-v8a")
shutil.copy(conf, libdir / "arm64-v8a")

print("Waiting for modify the AndroidManifest.xml")
print("Path: ", workingdir)
input("Press Enter to continue...")

# Zip
print(f"[+] APK Packing...")
os.system(f"apktool b {workingdir} -o {newapk}")

# # Align
# print(f"[+] Aligning the APK")
# os.system(f"{ZIPALIGN} -f 8 {newapk} {newapk.replace('_new.apk', '_aligned.apk')}")

# Sign
print(f"[+] Signing the APK")
# os.system(f"{APKSIGNER} sign --ks {KEYSTORE} --ks-pass pass:{KEYSTOREPASS} {newapk}")
os.system(f"{APKSIGNER} sign --align-file-size --key {RELEASEKEY} --cert {RELEASECERT} {newapk}")

if os.path.exists(newapk + ".idsig"):
    os.remove(newapk + ".idsig")

# clean tempfile
shutil.rmtree(workingdir)
