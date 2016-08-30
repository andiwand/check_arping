#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import subprocess
import re

prefix = {0: 'OK', 1: 'WARN', 2: 'CRIT', 3: 'UNKN'}

regex_output = r'\s*(.*?)\:\s*(\d+(?:\.\d*)?)(\w*)\s*?.*?(?:$|\|)'
regex_limit = r'^(\d+),(\d+)%$'

def parse_limits(s):
	return map(float, re.findall(regex_limit, s)[0])

def optionsparser(argv=None):
	parser = argparse.ArgumentParser()
	parser.add_argument('-H', '--host', help='host to ping', type=str, required=True)
	parser.add_argument('-w', '--warning', help='warning threshold pair', type=str, required=True)
	parser.add_argument('-c', '--critical', help='critical threshold pair', type=str, required=True)
	parser.add_argument('-p', '--packets', help='number of ICMP ECHO packets to send (default is %(default)d)', type=int, default=5)
	parser.add_argument('--dest-mac', help='destination mac', type=str)
	return parser.parse_args(argv)

def nping(host, proto='icmp', count=5, dest_mac=None):
	args = ['nping']
	args += ['--' + proto]
	args += ['-c', str(count)]
	if dest_mac: args += ['--dest-mac', dest_mac]
	args += [host]
	
	nping = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	exit_code = os.waitpid(nping.pid, 0)
	output = nping.communicate()
	
	if exit_code != 0 and not output[1]:
		data = '\n'.join(output[0].strip().split('\n')[-3:-1])
		data_parsed = re.findall(regex_output, data, flags=re.M)
		result = tuple(map(float, (l[1] for l in data_parsed)))
	
	return (result, output[0], output[1])

def main(argv=None):
	args = optionsparser(argv)
	w_rta, w_pl = parse_limits(args.warning)
	c_rta, c_pl = parse_limits(args.critical)
	try:
		result = nping(args.host, 'icmp', args.packets, args.dest_mac)
	except OSError:
		sys.stdout.write('UKNOWN: nping invocation failed!')
		return 3
	if result[2]:
		sys.stdout.write('UKNOWN: ' + result[2])
		return 3
	if result[0] == None:
		sys.stdout.write('UKNOWN: parsing failed: ' + result[1])
		return 3
	rta = result[0][2]
	pl = result[0][5] / result[0][3]
	return_code = 0
	if rta >= w_rta or pl >= w_pl:
		return_code = 1
	if rta >= c_rta or pl >= c_pl:
		return_code = 2
	sys.stdout.write(prefix[return_code] + ': time: %d, loss: %d' % (rta, pl))
	return return_code

if __name__ == '__main__':
	exit_code = main()
	sys.exit(exit_code)

