#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import os
import yaml
import pprint
import sys
import subprocess


android_manifest_contents = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
      package="com.mycompany.package1"
      android:versionCode="1"
      android:versionName="1.0">

    <uses-permission android:name="android.permission.INTERNET"/>
    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION"/>
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>

    <uses-sdk android:minSdkVersion="2"/>

    <application android:icon="@drawable/mylogo"
                 android:label="@string/myApplicationName">
        <activity android:name="com.mycompany.package1.HelloAndroid"
                  android:label="@string/myApplicationName">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>

</manifest>"""


def _printAndExit(print_string):
    print print_string
    sys.exit(1)


def _compile(args, compile_options):
    # Find a list of targets
    android_tools_program = os.path.join(args.android, 'tools/android')
    targets = subprocess.check_output([android_tools_program, "list", "target"])
    print targets
    # Check virtual devices
    # Keystore stuff
    # Create resources
    # Compile


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a',
                        '--android',
                        help='The directory of the Android SDK',
                        required=False,
                        default=os.environ.get('ANDROID_HOME'))
    parser.add_argument('-b',
                        '--build',
                        help='The file name of the build configuration',
                        required=False,
                        default='androidbuildsystem.yaml')
    parser.add_argument('-d',
                        '--directory',
                        help='The directory of the build script',
                        required=False,
                        default=os.getcwd())
    parser.add_argument('-i',
                        '--init',
                        help='Initialises a build system folder structure',
                        required=False,
                        default=False,
                        action='store_true')
    parser.add_argument('-j',
                        '--java',
                        help='The directory of the Java SDK',
                        required=False,
                        default=os.environ.get('JAVA_HOME'))
    parser.add_argument('-t',
                        '--target',
                        help='The target to compile against',
                        required=False)
    parser.add_argument('-v',
                        '--version',
                        help='Prints the version of android build system',
                        required=False,
                        default=False,
                        action='store_true')
    args = parser.parse_args()
    if args.version:
        print 'android build system version 1.0.0'
        return
    # Print our build system variables
    print '\nStarting Android App Build with variables:\n'
    print 'Java SDK: ' + str(args.java)
    print 'Android SDK: ' + str(args.android)
    print 'Build Directory: ' + str(args.directory)
    print 'Build File: ' + str(args.build)
    print ''
    # Check our build variables
    if args.java == None:
        _printAndExit('Failed to define the Java SDK Path (-j)')
    if args.android == None:
        _printAndExit('Failed to define the Android SDK Path (-a)')
    # Read our build configuration
    build_file = os.path.join(str(args.directory), str(args.build))
    if os.path.isfile(build_file):
        with open(build_file) as build_f:
            build_config = yaml.safe_load(build_f)
            if build_config == None:
                _printAndExit('Error: Cannot load YAML file ' + build_file)
    else:
        _printAndExit('Error: Cannot find file ' + build_file)
    # Check our build system directory
    check_directories = [ 'src', 'res', 'res/drawable', 'res/layout', 'res/values', 'lib' ]
    for check_directory in check_directories:
        full_check_directory = os.path.join(args.directory, check_directory)
        if not os.path.exists(full_check_directory):
            if args.init:
                os.makedirs(full_check_directory)
            else:
                _printAndExit('Required directory not available: ' + check_directory)
    create_directories = [ 'obj', 'bin', 'doc' ]
    for create_directory in create_directories:
        full_check_directory = os.path.join(args.directory, create_directory)
        if not os.path.exists(full_check_directory):
            os.makedirs(full_check_directory)
    android_manifest_file = os.path.join(args.directory, 'AndroidManifest.xml')
    if args.init:
        if not os.path.exists(android_manifest_file):
            open(android_manifest_file, 'w').write(android_manifest_contents)
        print 'Successfully initialised the required build directories'
        return 0
    if not os.path.exists(android_manifest_file):
        _printAndExit('Could not find AndroidManifest.xml in the build directory')
    _compile(args, build_config['compile'])


if __name__ == "__main__":
    _main()
