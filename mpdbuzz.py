#!/usr/bin/env python
# coding: utf-8

# mpdbuzz.py - Control MPD using Playstation USB Buzzer [For *nix systems]
# Copyright © 2010, 2011 Lukas Martini

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import time
import threading

from optparse import OptionParser
from mpd import (MPDClient, CommandError)

# Fixme: Last buzzer is missing
ASSOC = {32: (0, 0), 33: (0, 4), 34: (0, 3), 35: (0, 2), 36: (0, 1), 37: (1, 0), 38: (1, 4), 39: (1, 3), 40: (1, 2), 41: (1, 1), 42: (2, 0), 43: (2, 4), 44: (2, 3), 45: (2, 2), 46: (2, 1), 47: (3, 0), 48: (3, 4), 49: (3, 3), 50: (3, 2), 51: (3, 1)}

class mpdHandler(MPDClient):
	def __init__(self, host, port, password):
		MPDClient.__init__(self)

		try:
			self.connect(host=host, port=port)
		except __import__("socket").gaierror:
			print("Couldn't connect to {0}:{1}".format(host, port))
			exit(1)
		except __import__("socket").error:
			print("Couldn't connect using port {0}, but there seems to be a server at that IP.".format(port))
			exit(1)

		if password:
			try:
				self.password(password)
			except CommandError:
				exit(1)
		
		print("Connected to {0}:{1}".format(host, port))

	def keepalive(self):
		while True:
			print("Sending ping...")
			self.ping()
			time.sleep(30)

class buzz(object):
	def __init__(self, client):
		self.lastCommandNumber = False
		self.lastTime = False
		self.client = client

	def map(self, commandNumber):
		if commandNumber == self.lastCommandNumber and time.time() - self.lastTime < 0.2:
			return

		self.lastCommandNumber = commandNumber
		self.lastTime = time.time()
		
		if commandNumber in ASSOC:
			button = ASSOC[commandNumber]

			print("Spieler {0}: Button #{1}.".format(str(button[0]+1), button[1]+1))
			
			if button[1] == 0:
				self.client.next()
			elif button[1] == 1:
				self.client.previous()
			elif button[1] == 2:
				if self.client.status()['state'] == 'play':
					self.client.pause()
				else:
					self.client.play()
			elif button[1] == 3:
				newVolume = int(self.client.status()['volume']) + 10
				if newVolume <= 100:
					self.client.setvol(newVolume)
					print newVolume
				else:
					self.client.setvol(100)
			elif button[1] == 4:
				newVolume = int(self.client.status()['volume']) - 10
				if newVolume >= 0:
					self.client.setvol(newVolume)
					print newVolume
				else:
					self.client.setvol(0)

	def dump(self, f):
		i = 0
		while True:
			buf = f.read(16)
			line = ""
			count = 0
			
			for j in buf:
				if count != 10:
					count += 1
					continue

				count = 0
				oStr = ord(j)
				
				if oStr > 4:
					self.map(oStr)

if __name__ == '__main__':
	parser = OptionParser(version='%prog v0.1')
	parser.add_option("-p", "--port", dest="port", default = 6600) 
	parser.add_option("-w", "--password", dest="password", default = False)
	(options, args) = parser.parse_args()

	if len(args) < 2:
		print "USAGE: {0} [device] [server]".format(sys.argv[0])
		exit(1)

	mpdHandler = mpdHandler(args[1], options.port, options.password)

	keepaliveThread = threading.Thread(target=mpdHandler.keepalive)
	keepaliveThread.start()

	# Something like /dev/input/event8
	f = open(args[0],"rb")
	buzz =  buzz(mpdHandler)
	buzz.dump(f)
