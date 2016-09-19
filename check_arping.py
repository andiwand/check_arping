#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import subprocess
import re

prefix = {0: 'OK', 1: 'WARN', 2: 'CRIT', 3: 'UNKN'}

regex_output = r'(\d+(?:\.\d+)?)'
regex_limit = r'^(\d+),(\d+)%$'

def parse_limits(s):
	rta, pl = map(float, re.findall(regex_limit, s)[0])
	return rta, pl / 100

def optionsparser(argv=None):
	parser = argparse.ArgumentParser()
	parser.add_argument('-H', '--host', help='host to ping', type=str, required=True)
	parser.add_argument('-w', '--warning', help='warning threshold pair', type=str, required=True)
	parser.add_argument('-c', '--critical', help='critical threshold pair', type=str, required=True)
	parser.add_argument('-p', '--packets', help='number of ICMP ECHO packets to send (default is %(default)d)', type=int, default=5)
	parser.add_argument('--dest-mac', help='destination mac', type=str, required=True)
	parser.add_argument('-I', '--interface', help="interface to use", type=str, required=True)
	return parser.parse_args(argv)

def arping(host, dest_mac, interface, count=5):
	args = ['arping']
	args += ['-c', str(count)]
	args += ['-T', host]
	args += ['-I', interface]
	args += [dest_mac]
	
	process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	exit_code = os.waitpid(process.pid, 0)
	output = process.communicate()
	
	data = output[0].split('\n')[-3:-1]
	packet_data = re.findall(regex_output, data[0])
	time_data = re.findall(regex_output, data[1])
	result = {}
	if len(packet_data) > 0:
		result['tx'] = int(packet_data[0])
		result['rx'] = int(packet_data[1])
		result['pl'] = float(packet_data[2]) / 100
	if len(time_data) > 0:
		result['rta_min'] = float(time_data[0])
		result['rta_avg'] = float(time_data[1])
		result['rta_max'] = float(time_data[2])
		result['rta_std'] = float(time_data[3])
	
	return (result, output[0], output[1])

def main(argv=None):
	args = optionsparser(argv)
	w_rta, w_pl = parse_limits(args.warning)
	c_rta, c_pl = parse_limits(args.critical)
	try:
		result = arping(args.host, args.dest_mac, args.interface, args.packets)
	except OSError:
		sys.stdout.write('UKNOWN: arping invocation failed!')
		return 3
	if result[2]:
		sys.stdout.write('UKNOWN: ' + result[2])
		return 3
	if result[0] == None:
		sys.stdout.write('UKNOWN: parsing failed: ' + result[1])
		return 3
	result = result[0]
	rta = result.get("rta_avg", -1)
	pl = result["pl"]
	return_code = 0
	if rta >= w_rta or pl >= w_pl:
		return_code = 1
	if rta >= c_rta or pl >= c_pl:
		return_code = 2
	sys.stdout.write(prefix[return_code] + ': time %d loss %d%%' % (rta, pl * 100))
	return return_code

if __name__ == '__main__':
	exit_code = main()
	sys.exit(exit_code)
