## Vivado-CI - Server Side ##

**Vivado-CI** is a tool that uses Xilinx Vivado but is not endosed by Xilinx.
This guide will let you setup your own CI servernode

### 1 - Installing Xilinx Vivado on your server. ###

This part is totally **optional** if Vivado is already installed on your server.

To install Vivado, you need a desktop environment (don't worry, we will remove it at the end of the installation). I tested the installation on a cloud server with 512Mb of RAM and it did not work, I recommend using at least 1Gb of RAM to be able to install Vivado

If you want to use a Cloud service, I used [Digital Ocean](https://www.digitalocean.com/?refcode=6200f0600676) *(referral link, you'll get $10 to test it but you can create an account without the referral link)* to instanciate my server. You then need to install a desktop to install Xilinx.
[This link](https://www.digitalocean.com/community/tutorials/how-to-setup-vnc-for-ubuntu-12) will help you do it via VNC on a Ubuntu (12.04 to 14.10).
Once you booted up on the desktop, you will be able to install Vivado, you need to install it in the default location: `/opt/Xilinx`.
Once you don't need the desktop anymore, you can remove it:

	service vncserver stop
	update-rc.d -f vncserver remove

Then disable the X server by changing in `/etc/default/grub`

	GRUB_CMDLINE_LINUX_DEFAULT="text"

You might also need more than 1Gb of RAM for the design process. I would recommend to either get a bigger server or create some virtual memory with a swap file ([see here for a good overview](https://www.digitalocean.com/community/tutorials/how-to-configure-virtual-memory-swap-file-on-a-vps)), 4 or 8 Gb in total should be ok. You can install Zram to make the swap faster.

### 2 - Installing Vivado-CI ###

First make sure that git and python2 are installed, and copy this git:

	sudo apt-get install git python
	git clone https://github.com/Viq111/Vivado-CI.git Vivado-CI
	
Then execute the server script and your CI server should be up and running !

	cd Vivado-CI/server-side
	python VivadoCi.py
	