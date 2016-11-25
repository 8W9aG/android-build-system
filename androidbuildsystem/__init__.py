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
      package="com.example.test"
      android:versionCode="1"
      android:versionName="1.0">

    <uses-permission android:name="android.permission.INTERNET"/>
    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION"/>
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>

    <uses-sdk android:minSdkVersion="2"/>

    <application android:icon="@drawable/mylogo"
                 android:label="@string/myApplicationName">
        <activity android:name="com.example.test.HelloAndroid"
                  android:label="@string/myApplicationName">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>

</manifest>"""
android_manifest_file = 'AndroidManifest.xml'


def _printAndExit(print_string):
    print print_string
    sys.exit(1)


def _parseTargets(targets):
    parsed_targets = []
    dash_splits = targets.split('----------');
    for dash_split in dash_splits:
        line_split = dash_split.split('\n')
        identifiers = []
        name = None
        device_type = None
        api_level = None
        revision = None
        skins = []
        for line in line_split:
            line_strip = line.strip()
            colon_split = line_strip.split(':')
            if len(colon_split) < 2:
                continue
            if colon_split[0] == 'id':
                or_splits = colon_split[1].split(' or ')
                for or_split in or_splits:
                    if or_split[0] == '"' and or_split[-1] == '"':
                        identifiers.append(or_split[1:-1].strip())
                    else:
                        identifiers.append(or_split.strip())
            elif colon_split[0] == 'Name':
                name = colon_split[1].strip()
            elif colon_split[0] == 'Type':
                device_type = colon_split[1].strip()
            elif colon_split[0] == 'API level':
                api_level = colon_split[1].strip()
            elif colon_split[0] == 'Revision':
                revision = colon_split[1].strip()
            elif colon_split[0] == 'Skins':
                comma_splits = colon_split[1].split(',')
                for comma_split in comma_splits:
                    skins.append(comma_split.strip())
        if len(identifiers) == 0 or name == None or device_type == None or api_level == None or revision == None or len(skins) == 0:
            continue
        parsed_targets.append({ 'identifiers' : identifiers,
                                'name' : name,
                                'device_type' : device_type,
                                'api_level' : api_level,
                                'revision' : revision,
                                'skins' : skins })
    return parsed_targets


def _compile(args, compile_options):
    # Execute the before scripts
    for before_script in compile_options['before']:
        subprocess.call(before_script, shell=True)
    # Find a list of targets
    print 'Checking target validity...'
    check_target = args.target
    if check_target == None:
        check_target = compile_options['target']
    tools_directory = os.path.join(args.android, 'tools')
    android_tools_program = os.path.join(tools_directory, 'android')
    targets = subprocess.check_output(['android', 'list', 'target'], cwd=tools_directory)
    parsed_targets = _parseTargets(targets)
    parsed_target = None
    for target in parsed_targets:
        if check_target in target['identifiers']:
            parsed_target = target
            break
    if parsed_target == None:
        _printAndExit('Could not find target: ' + check_target + '\n' + targets)
    # Create R.java
    print 'Creating R.java...'
    build_tools_folder = os.path.join(args.android, 'build-tools')
    build_tools_target_folder = ''
    for directory in os.listdir(build_tools_folder):
        if directory.split('.')[0] == parsed_target['api_level']:
            build_tools_target_folder = os.path.join(build_tools_folder, directory)
            break
    android_aapt_program = os.path.join(build_tools_target_folder, 'aapt')
    res_directory = os.path.join(args.directory, 'res')
    src_directory = os.path.join(args.directory, 'src')
    manifest_file = os.path.join(args.directory, android_manifest_file)
    android_jar_file = os.path.join(os.path.join(os.path.join(args.android, 'platforms'), check_target), 'android.jar')
    result = subprocess.check_call([android_aapt_program,
        'package',
        '-f',
        '-m',
        '-S', res_directory,
        '-J', src_directory,
        '-M', manifest_file,
        '-I', android_jar_file])
    if result != 0:
        _printAndExit('Failed to create R.java')
    # Compile
    print 'Compiling...'
    javac_program = os.path.join(args.java, 'bin/javac')
    obj_directory = os.path.join(args.directory, 'obj')
    classpaths = [ android_jar_file, obj_directory ]
    lib_directory = os.path.join(args.directory, 'lib')
    for lib_file in os.listdir(lib_directory):
        if os.path.isfile(lib_file) and os.path.splitext(lib_file)[1] == 'jar':
            classpaths.append(os.path.join(lib_directory, lib_file))
    java_source_paths = []
    for root, dirnames, filenames in os.walk(src_directory):
        for filename in filenames:
            if os.path.splitext(filename)[1] == '.java':
                java_source_paths.append(os.path.join(root, filename))
    for java_source_path in java_source_paths:
        result = subprocess.check_call([javac_program,
            '-d', obj_directory,
            '-classpath', ':'.join(classpaths),
            '-sourcepath', src_directory,
            java_source_path])
        if result != 0:
            _printAndExit('Failed to compile')
    # Create the DEX file
    print 'Creating a DEX file...'
    dx_program = os.path.join(build_tools_target_folder, 'dx')
    classes_dex_file = os.path.join(args.directory, 'bin/classes.dex')
    result = subprocess.call([dx_program,
        '--dex',
        '--output=' + classes_dex_file,
        obj_directory,
        lib_directory])
    if result != 0:
        _printAndExit('Failed to create DEX')
    # Execute the after scripts
    for after_script in compile_options['after']:
        subprocess.call(after_script, shell=True)


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
    manifest_file = os.path.join(args.directory, android_manifest_file)
    if args.init:
        if not os.path.exists(manifest_file):
            open(manifest_file, 'w').write(android_manifest_contents)
        print 'Successfully initialised the required build directories'
        return 0
    if not os.path.exists(android_manifest_file):
        _printAndExit('Could not find ' + android_manifest_file + ' in the build directory')
    _compile(args, build_config['compile'])


if __name__ == "__main__":
    _main()
