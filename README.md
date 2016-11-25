This is a small build system made to demonstrate how to build an android application from scratch.

## Test Usage

Install the python module:
```shell
python setup.py install
```

Run it on the example folder:
```shell
cd example && androidbuildsystem
```

## Build Configuration

The `androidbuildsystem.yaml` is designed to allow different configuration options for virtual devices and execute scripts before and after each step. The available steps are as follows:
- **Compile** Checks whether the target is valid, creates R.java from the resources, compiles the java sources into bytecode, and finally creates a DEX.
- **Package** Removes the older APKs, and packages the DEX into an APK.
- **Sign** Creates the keystore if none are created, and signs the APK with that key.
- **Install** Checks the virtual devices to see if the requested one is created, if not it creates it, then installs to the emulator or device.
Each one of these steps can be disabled, however they must run in order (for example if Sign is disabled Install will not run).

On every one of these steps there are a `before` and `after` key which allows custom shell commands to run before and after each step.

## Creating a project

Inorder to create a new project run the following command on a new directory:
```shell
androidbuildsystem --init
```

## Arguments

The following arguments can be used in androidbuildsystem:
- `-a` The path to the android SDK. By default this will use `ANDROID_HOME` in the environment variables.
- `-b` The filename of the build configuration. By default this will be `androidbuildsystem.yaml`.
- `-d` The directory to build. By default this will be the current working directory.
- `-i` Initialises the build directory.
- `-j` The path to the Java SDK. By default this will use `JAVA_HOME` in the environment variables.
- `-t` The target to compile with. Use this to override the build configurations target.
- `-v` Prints the version of the build system.
