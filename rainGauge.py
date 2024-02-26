"""Handles my rain gauge controller."""
import serial
import time
import logging

def checkCheckSum(arr):
	"""Return whether the checksum of an API frame is valid."""
	# input a XBee API frame with the checksum
	check = sum(arr[3:])    # sum the bytes of the frame except frame
                            # delimiter and length bytes (include checksum)
	check = check & 255     # if the last eight bits of the sum equal 0xFF (255)
	if check == 255:        # then the checksum is correct
		return True
	else:
		return False

def procRXDataSample(arr):
	"""Return the setting of a particular pin on the remote XBee."""
	# input XBee frame with the checksum
	logging.debug('digital sample mask: {0:16b}'.format(int.from_bytes(arr[16:18], "big")))	#debug
	logging.debug('tdigital samples: {0:16b}'.format(int.from_bytes(arr[19:21], "big")))	# debug
	DI3 = int.from_bytes(arr[16:18], "big") & int.from_bytes(arr[19:21], "big")
	return DI3

def calcCheckSum(arr):
	"""Calculate whether the check sum of a received frame is valid."""
    # input: a XBee API frame without the checksum represented as an array of bytes
	check = sum(arr[3:])    # add up the individual bytes of the frame
				# except the frame delimiter and the length bytes
	check = check & 255     # keep only last eight bits
	check = 255 - check     # subtract from 255
	return arr + bytes([check])

def bldRemoteATComm(ATCommand, parmString, disableACK):	
	"""Build an AT command frame from the desired command and optional parameters."""
	# input the AT command and the parameters string eg. 'D0' and '4' for ATD04 command
	arr = b'~'				# start with frame delimiter and length set to 0
	arrLen = len(ATCommand) + len(parmString) + 13	# length field of frame; total len - delim, length, and check
	arr = arr + bytes([arrLen >> 8, arrLen % 256])
	arr = arr + b'\x17'				# frame type  17 hex
	arr = arr + b'\04'				# frame id nonzero to get a response
	arr = arr + b'\x00\x13\xa2\x00@\xa0\x96\xa1'	# 64 bit destination
	arr = arr + b'\xff\xfe'				# 16 bit destination address - 0xFFFE for unknown
	arr = arr + bytes([b'\x02'[0] + disableACK])	# remote command option - 0x02 means apply changes
	arr = arr + bytes(ATCommand,"utf-8")		# given AT command
	if len(parmString) > 0:				# given parameters (if present)
		arr = arr + parmString
	arr = calcCheckSum(arr)				# add check sum to arr
	logging.info('RemoteATComm frame: '+arr.hex())
	return arr


if __name__ == "__main__":
	logging.basicConfig(filename='rainGauge.log', level=logging.INFO, filemode='a', 
						format='%(asctime)s:%(levelname)s:%(message)s')
	ser = serial.Serial('/dev/ttyUSB0', 9600)	#assume XBee connected to USB0
	ser.timeout=86400					# remote may take up to an day to send data
	tipCount = 0

	while True:
		xFrame = ser.read(4)
		if len(xFrame) == 0:			#probably means ser.read timed out
			break
		if chr(xFrame[0]) != '~':		#probably means we caught the tail-end of a frame
			logging.info('Bad frame rcvd; first char not "~": '+xFrame.hex())
			continue
		logging.debug('frame len: ', int.from_bytes(xFrame[1:3], "big"))  # debugging
		xFrame = xFrame + ser.read(int.from_bytes(xFrame[1:3], "big"))
		if checkCheckSum(xFrame):
			logging.info('Good frame rcvd: ' + xFrame.hex())
			#print("".join(["{}:".format(i) for i in time.localtime()[3:6] ]), 'Good frame rcvd: ', xFrame)
			if 'x%02x'%xFrame[3] == 'x92':	# rcvd remote data sample
				swState = procRXDataSample(xFrame)&8	# bit three of digital sample
				logging.debug('\tswitch state: ', swState)
				if swState == 8:
					tipCount = tipCount + 1
					print('TIPCOUNT: ', tipCount)
					ser.write(bldRemoteATComm('D0',b'\x05', True))	# clear latch
					time.sleep(.01)
					ser.write(bldRemoteATComm('D0',b'\x04', True))	# so latch operates next time
					# ser.write(bldRemoteATComm('D3',b'\x03', False))	
					# ser.write(bldRemoteATComm('WR', '', False))
				else:
				#	ser.write(bldRemoteATComm('ST', b'\x7D'))	# wait 60 msec to sleep
					ser.write(bldRemoteATComm('%V','', False))
			elif 'x%02x'%xFrame[3] == 'x97':
				if xFrame[15:17] == b'%V':
					print('mV: ', '%4d'%(int.from_bytes(xFrame[18:20], "big")*1200/1024))
		else:
			logging.warning('Bad frame: ' + xFrame.hex())


	if len(xFrame) == 0:
		logging.error('serial read timed out: ')
