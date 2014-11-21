# Vivado-CI
**Vivado-CI** is a continous integration system for Vivado-based projects (VHDL & Verilog). It integrates fully with Travis-Ci and GitHub with minimal configuration

## How to use for your project
Simply copy/paste the `.travis.yml` (and `.gitignore` *if you want*) onto your GitHub project and you are ready to go !

Don't forget to enable Travis-Ci on your repository [here](https://travis-ci.org/profile) !

## (Optional) Configuration

All the configuration of your build is done in the `.travis.yml` file, just change the globals here:


## Build your own CI-server
See `README.md` in the `server-side` directory