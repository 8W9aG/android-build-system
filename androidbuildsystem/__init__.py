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
android_strings_xml = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="myApplicationName">Android Test Program</string>
    <string name="helloText">Hello, world!</string>
</resources>"""
android_manifest_file = 'AndroidManifest.xml'


def _printAndExit(print_string):
    """
    Prints a message and exits with an error value.

    Args:
    print_string: The string to print to the console.
    """
    print print_string
    sys.exit(1)


def _parseTargets(targets):
    """
    Parses the targets output by the android SDK into a dictionary.

    Args:
    targets: The string output of the android SDK.
    Returns:
    Dictionaries containing information about the targets.
    """
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


def _parseVirtualDevices(virtual_devices):
    """
    Parses the virtual devices output by the android SDK into names.

    Args:
    targets: The string output of the android SDK.
    Returns:
    Strings containing the names of the virtual devices.
    """
    parsed_virtual_devices = []
    dash_splits = virtual_devices.split('---------');
    for dash_split in dash_splits:
        line_split = dash_split.split('\n')
        if line_split[0] == 'Available Android Virtual Devices:':
            line_split = line_split[1:]
        for line in line_split:
            line_strip = line.strip()
            if 'Name:' in line_strip:
                parsed_virtual_devices.append(line_strip.split(':')[-1].strip())
    return parsed_virtual_devices


def _compile(args, compile_options):
    """
    Performs the compile steps to create java bytecode.

    Args:
    args: The arguments given to the main function.
    compile_options: The build configuration options for compiling
    Returns:
    A string with the absolute path to the build tools folder
    """
    # Execute the before scripts
    for before_script in compile_options['before']:
        subprocess.call(before_script, shell=True)
    # Find a list of targets
    print 'Checking target validity...'
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
    return build_tools_target_folder


def _package(args, package_options, build_tools_target_folder, target):
    """
    Performs the package steps to create an unsigned APK.

    Args:
    args: The arguments given to the main function.
    package_options: The build configuration options for packaging.
    target: The target to package with.
    Returns:
    A string with the absolute path to the unsigned APK file.
    """
    # Execute the before scripts
    for before_script in package_options['before']:
        subprocess.call(before_script, shell=True)
    print 'Packaging APK...'
    # Remove the apks in the bin folder
    bin_directory = os.path.join(args.directory, 'bin')
    for bin_file in os.listdir(bin_directory):
        if bin_file.split('.')[-1] == 'apk':
            os.remove(os.path.join(bin_directory, bin_file))
    # Package the APK
    aapt_program = os.path.join(build_tools_target_folder, 'aapt')
    manifest_file = os.path.join(args.directory, android_manifest_file)
    res_directory = os.path.join(args.directory, 'res')
    android_jar_file = os.path.join(os.path.join(os.path.join(args.android, 'platforms'), target), 'android.jar')
    unsigned_apk_file = os.path.join(os.path.join(args.directory, bin_directory), package_options['name'] + '.unsigned.apk')
    result = subprocess.call([aapt_program,
        'package',
        '-f',
        '-M', manifest_file,
        '-S', res_directory,
        '-I', android_jar_file,
        '-F', unsigned_apk_file,
        bin_directory])
    if result != 0:
        _printAndExit('Failed to package APK')
    # Execute the after scripts
    for after_script in package_options['after']:
        subprocess.call(after_script, shell=True)
    return unsigned_apk_file


def _sign(args, sign_options, unsigned_apk_file, build_tools_target_folder):
    """
    Performs the package steps to create a signed APK.

    Args:
    args: The arguments given to the main function.
    sign_options: The build configuration options for signing.
    unsigned_apk_file: The path to the unsigned APK file.
    build_tools_target_folder: The build tools target folder.
    Returns:
    A string with the absolute path to the zipaligned APK file.
    """
    # Execute the before scripts
    for before_script in sign_options['before']:
        subprocess.call(before_script, shell=True)
    # Check if we have a keystore
    keystore = sign_options['keystore']
    keystore_file = os.path.join(args.directory, 'key.keystore')
    if not os.path.exists(keystore_file):
        print 'Creating a keystore...'
        keytool_program = os.path.join(args.java, 'bin/keytool')
        key_parameters = 'CN=' + keystore['company_name'] + ',\n'
        key_parameters += 'OU=' + keystore['organisational_unit'] + ',\n'
        key_parameters += 'O=' + keystore['organisation'] + ',\n'
        key_parameters += 'L=' + keystore['location'] + ',\n'
        key_parameters += 'S=' + keystore['state'] + ',\n'
        key_parameters += 'C=' + keystore['country']
        result = subprocess.check_call([keytool_program,
            '-genkeypair',
            '-validity', '1000',
            '-dname', key_parameters,
            '-keystore', keystore_file,
            '-storepass', sign_options['storepass'],
            '-keypass', sign_options['keypass'],
            '-alias', sign_options['key_alias'],
            '-keyalg', 'RSA'])
        if result != 0:
            _printAndExit('Failed to create keystore')
    print 'Signing APK...'
    jarsigner_file = os.path.join(args.java, 'bin/jarsigner')
    signed_apk_file = unsigned_apk_file.replace('unsigned.apk', 'signed.apk')
    result = subprocess.check_call([jarsigner_file,
        '-keystore', keystore_file,
        '-storepass', sign_options['storepass'],
        '-keypass', sign_options['keypass'],
        '-signedjar', signed_apk_file,
        unsigned_apk_file,
        sign_options['key_alias']])
    # Zip align the APK
    zipalign_file = os.path.join(build_tools_target_folder, 'zipalign')
    apk_file = signed_apk_file.replace('signed.apk', 'apk')
    result = subprocess.call([zipalign_file,
        '-f',
        '4',
        signed_apk_file,
        apk_file])
    # Execute the after scripts
    for after_script in sign_options['after']:
        subprocess.call(after_script, shell=True)
    return zipalign_file


def _install(args, install_options, profiles, apk_file):
    """
    Performs the package steps to install an APK.

    Args:
    args: The arguments given to the main function.
    install_options: The build configuration options for installing.
    profiles: A list containing the profiles in our build configuration.
    apk_file: The signed APK file.
    """
    # Execute the before scripts
    for before_script in install_options['before']:
        subprocess.call(before_script, shell=True)
    print 'Checking virtual devices...'
    tools_directory = os.path.join(args.android, 'tools')
    android_tools_program = os.path.join(tools_directory, 'android')
    virtual_devices_output = subprocess.check_output(['android', 'list', 'avd'], cwd=tools_directory)
    virtual_devices = _parseVirtualDevices(virtual_devices_output)
    final_profile = None
    for profile in profiles:
        if profile['name'] == install_options['profile']:
            final_profile = profile
            break
    if install_options['profile'] not in virtual_devices:
        # Create the virtual device
        if final_profile == None:
            _printAndExit('Could not find a profile to install the app onto')
        if final_profile['type'] == 'emulator':
            result = subprocess.call([android_tools_program,
                '--verbose',
                'create', 'avd',
                '--name', final_profile['name'],
                '--target', final_profile['target'],
                '--sdcard', final_profile['sdcard'],
                '--abi', final_profile['abi']])
        if result != 0:
            _printAndExit('Failed to create virtual device')
    # Install
    print 'Installing the app...'
    platform_tools_directory = os.path.join(args.android, 'platform-tools')
    adb_program = os.path.join(platform_tools_directory, 'adb')
    device_type = '-e'
    if final_profile['type'] == 'device':
        device_type = '-d'
    result = subprocess.call([adb_program,
        device_type,
        apk_file])
    if result != 0:
        _printAndExit('Failed to install the APK')
    # Execute the after scripts
    for after_script in install_options['after']:
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
    strings_xml_file = os.path.join(os.path.join(os.path.join(args.directory, 'res'), 'values'), 'strings.xml')
    if args.init:
        if not os.path.exists(manifest_file):
            open(manifest_file, 'w').write(android_manifest_contents)
        if not os.path.exists(strings_xml_file):
            open(strings_xml_file, 'w').write(android_strings_xml)
        print 'Successfully initialised the required build directories'
        return 0
    if not os.path.exists(android_manifest_file):
        _printAndExit('Could not find ' + android_manifest_file + ' in the build directory')
    if args.target != None:
        build_config['compile']['target'] = args.target
    if 'compile' in build_config:
        build_tools_target_folder = _compile(args, build_config['compile'])
        if 'package' in build_config:
            unsigned_apk_file = _package(args, build_config['package'], build_tools_target_folder, build_config['compile']['target'])
            if 'sign' in build_config:
                apk_file = _sign(args, build_config['sign'], unsigned_apk_file, build_tools_target_folder)
                if 'install' in build_config:
                    _install(args, build_config['install'], build_config['profiles'], apk_file)
    print 'Build completed'


if __name__ == "__main__":
    _main()
