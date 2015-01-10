# Vivado-CI

**NOTICE: The server has been brought down, please create your own server (see README in server-side folder), then just change the address in the `.travis.yml`**


**Vivado-CI** is a continous integration system for Vivado-based projects (VHDL & Verilog). It integrates fully with Travis-Ci and GitHub with minimal configuration

## How to use for your project
Simply copy the `.travis.yml` (and `.gitignore` *if you want*) onto your GitHub project and you are ready to go !

Don't forget to enable Travis-CI on your repository [here](https://travis-ci.org/profile) !

## (Optional) Configuration

All the configuration of your build is done in the `.travis.yml` file, just change the globals here:

- `VIVADO_CI_SERVER` and `VIVADO_CI_PORT` defines the host on which the repository will be built. If you create your own Vivado-CI Server, make sure you modify these values when you provide the `.travis.yml`
- `XPR_PATH` is the path to the Vivado project which will be built. This path should match one and only one project, currently multiple builds is not supported.

The python script is executed at each step of the travis stages so that for example the Vivado-CI can clone your repository while it's still doing some other work.

## Build your own CI-server

Because this software is open-source, you can build your own CI Server integrated with Travis (I do not have something better than what is listed here).
See the `README.md` in the `server-side` directory for the instructions.