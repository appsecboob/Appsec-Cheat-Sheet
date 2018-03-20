#encoding: utf-8
from __future__ import print_function
from builtins import str
import ipaddress
import datetime
import os
import sys
from twisted.names import client, dns, server, hosts as hosts_module, root, cache, resolve
from twisted.internet import reactor
from twisted.python.runtime import platform

TTL = 0
dict = {}
dont_print_ip_range = '74.125.0.0/16'
FILENAME = "dns-log-" + str(datetime.datetime.now().strftime("%H-%M-%S.%f-%d-%m-%Y"))+'.log'
WHITELISTEDIP = ''
INTERNALIP = ''
PORT = 53

def OpenLogFile():
	global f
	major = sys.version_info[0]
	if major == 3:
		f = open(FILENAME, 'a')
	else:
		f = open(FILENAME, 'ab')

def CloseLogFile():
	f.close()

def search_file_for_all(hosts_file, name):
	results = []
	if name not in dict or dict[name] < 1:
		ip = WHITELISTEDIP
	else:
		ip = INTERNALIP
	if name not in dict:
		dict[name] = 0
	dict[name] += 1
	print('================================================================================================')
	print('Response with A record: ', name.decode('utf-8'), ' -> ', ip, sep='')
	print('================================================================================================')
	OpenLogFile()
	print('================================================================================================', file=f)
	print('Response with A record: ', name.decode('utf-8'), ' -> ', ip, file=f, sep='')
	print('================================================================================================', file=f)
	CloseLogFile()
	results.append(hosts_module.nativeString(ip))
	return results

class Resolver(hosts_module.Resolver):
	def _aRecords(self, name):
		return tuple([
			dns.RRHeader(name, dns.A, dns.IN, TTL, dns.Record_A(addr, TTL))			#TTL为0
			for addr in search_file_for_all(hosts_module.FilePath(self.file), name)
			if hosts_module.isIPAddress(addr)
		])

class PrintClientAddressDNSServerFactory(server.DNSServerFactory):
	def buildProtocol(self, addr):
		if (ipaddress.ip_address(u"%s" % str(addr.host)) in ipaddress.ip_network(u"%s" % str(dont_print_ip_range))) == False:
			print('------------------------------------------------------------------------------------------------')
			print("ServerTime: ",datetime.datetime.now().strftime("%H:%M:%S.%f %d-%m-%Y"), sep='')
			print("Request: Connection to DNSServerFactory from: ", addr.host," on port: ",addr.port," using ",addr.type,sep='')
			print('------------------------------------------------------------------------------------------------')
			OpenLogFile()
			print('------------------------------------------------------------------------------------------------', file=f)
			print("ServerTime: ",datetime.datetime.now().strftime("%H:%M:%S.%f %d-%m-%Y"), file=f, sep='')
			print("Request: Connection to DNSServerFactory from: ", addr.host," on port: ",addr.port," using ",addr.type, file=f, sep='')
			print('------------------------------------------------------------------------------------------------', file=f)
			CloseLogFile()
		return server.DNSServerFactory.buildProtocol(self, addr)

class PrintClientAddressDNSDatagramProtocol(dns.DNSDatagramProtocol):
	def datagramReceived(self, datagram, addr):
		if (ipaddress.ip_address(u"%s" % str(addr[0])) in ipaddress.ip_network(u"%s" % str(dont_print_ip_range))) == False:
			print('------------------------------------------------------------------------------------------------')
			print("ServerTime: ",datetime.datetime.now().strftime("%H:%M:%S.%f %d-%m-%Y"), sep='')
			print("Request: Datagram to DNSDatagramProtocol from: ", addr[0], " on port: ", addr[1], sep='')
			print('------------------------------------------------------------------------------------------------')
			OpenLogFile()
			print('------------------------------------------------------------------------------------------------', file=f)
			print("ServerTime: ",datetime.datetime.now().strftime("%H:%M:%S.%f %d-%m-%Y"), file=f, sep='')
			print("Request: Datagram to DNSDatagramProtocol from: ", addr[0], " on port: ", addr[1], file=f, sep='')
			print('------------------------------------------------------------------------------------------------', file=f)
			CloseLogFile()
		return dns.DNSDatagramProtocol.datagramReceived(self, datagram, addr)

def create_resolver(servers=None, resolvconf=None, hosts=None):
	if platform.getType() == 'posix':
		if resolvconf is None:
			resolvconf = b'/etc/resolv.conf'
		if hosts is None:
			hosts = b'/etc/hosts'
		the_resolver = client.Resolver(resolvconf, servers)
		host_resolver = Resolver(hosts)
	else:
		if hosts is None:
			hosts = r'c:\windows\hosts'
		from twisted.internet import reactor
		bootstrap = client._ThreadedResolverImpl(reactor)
		host_resolver = Resolver(hosts)
		the_resolver = root.bootstrap(bootstrap, resolverFactory=client.Resolver)
	return resolve.ResolverChain([host_resolver, cache.CacheResolver(), the_resolver])

def main(port):
	factory = PrintClientAddressDNSServerFactory(
		clients=[create_resolver(servers=[('8.8.8.8', 53)], hosts='hosts')],
	)
	protocol = PrintClientAddressDNSDatagramProtocol(controller=factory)
	reactor.listenUDP(PORT, protocol)
	reactor.listenTCP(PORT, factory)
	print('------------------------------------------------------------------------------------------------')
	print("DNS Server started...\nListening on port: "+ str(PORT) +"\nLog file name: "+ FILENAME +"\nNot showing/logging requests from IP range: "+ dont_print_ip_range)
	print('------------------------------------------------------------------------------------------------\n\n')
	reactor.run()

if __name__ == '__main__':
	if len(sys.argv) != 4:
		print("Usage: python "+sys.argv[0]+" WhitelistedIP InternalIP Port")
		print ("Example: python "+sys.argv[0]+" 216.58.214.206 169.254.169.254 53")
		exit(1)
	else:
		WHITELISTEDIP = sys.argv[1]
		INTERNALIP = sys.argv[2]
		PORT = int(sys.argv[3])
	main(PORT)
