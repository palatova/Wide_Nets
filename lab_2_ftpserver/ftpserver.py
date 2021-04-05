import os
import sys
import logging

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

authorizer = DummyAuthorizer()
authorizer.add_user("user", "12345", "C:/Users", perm="elradfmw")
authorizer.add_user("taty", "0805", "C:/Users", perm="elradfmw")
authorizer.add_anonymous(os.getcwd())

handler = FTPHandler
handler.authorizer = authorizer

server = FTPServer(("127.17.6.1", 1026), handler)
server.serve_forever()

class FTPThreadServer(threading.Thread):

	def QUIT(self, cmd):
		try:
			self.client.send('221 Goodbye.\r\n')
		except:
			pass
		finally:
			print ('Closing connection from ' + str(self.client_address) + '...')
			self.close_datasock()
			self.client.close()
			quit()

	def LIST(self, cmd):
		print ('LIST', self.cwd)
		(client_data, client_address) = self.start_datasock()

		try:
			listdir = os.listdir(self.cwd)
			if not len(listdir):
				max_length = 0
			else:
				max_length = len(max(listdir, key=len))

			header = '| %*s | %9s | %12s | %20s | %11s | %12s |' % (max_length, 'Name', 'Filetype', 'Filesize', 'Last Modified', 'Permission', 'User/Group')
			table = '%s\n%s\n%s\n' % ('-' * len(header), header, '-' * len(header))
			client_data.send(table)
			
			for i in listdir:
				path = os.path.join(self.cwd, i)
				stat = os.stat(path)
				data = '| %*s | %9s | %12s | %20s | %11s | %12s |\n' % (max_length, i, 'Directory' if os.path.isdir(path) else 'File', str(stat.st_size) + 'B', time.strftime('%b %d, %Y %H:%M', time.localtime(stat.st_mtime))
					, oct(stat.st_mode)[-4:], str(stat.st_uid) + '/' + str(stat.st_gid)) 
				client_data.send(data)
			
			table = '%s\n' % ('-' * len(header))
			client_data.send(table)
			
			self.client.send('\r\n226 Directory send OK.\r\n')
		except (Exception, e):
			print ('ERROR: ' + str(self.client_address) + ': ' + str(e))
			self.client.send('426 Connection closed; transfer aborted.\r\n')
		finally: 
			client_data.close()
			self.close_datasock()

	def PWD(self, cmd):
		self.client.send('257 \"%s\".\r\n' % self.cwd)

	def CWD(self, cmd):
		dest = os.path.join(self.cwd, cmd[4:].strip())
		if (os.path.isdir(dest)):
			self.cwd = dest
			self.client.send('250 OK \"%s\".\r\n' % self.cwd)
		else:
			print ('ERROR: ' + str(self.client_address) + ': No such file or directory.')
			self.client.send('550 \"' + dest + '\": No such file or directory.\r\n')

	def CDUP(self, cmd):
		dest = os.path.abspath(os.path.join(self.cwd, '..'))
		if (os.path.isdir(dest)):
			self.cwd = dest
			self.client.send('250 OK \"%s\".\r\n' % self.cwd)
		else:
			print ('ERROR: ' + str(self.client_address) + ': No such file or directory.')
			self.client.send('550 \"' + dest + '\": No such file or directory.\r\n')


	def MKD(self, cmd):
		path = cmd[4:].strip()
		dirname = os.path.join(self.cwd, path)
		try:
			if not path:
				self.client.send('501 Missing arguments <dirname>.\r\n')
			else:
				os.mkdir(dirname)
				self.client.send('250 Directory created: ' + dirname + '.\r\n')
		except (Exception, e):
			print ('ERROR: ' + str(self.client_address) + ': ' + str(e))
			self.client.send('550 Failed to create directory ' + dirname + '.')

	def RMD(self, cmd):
		path = cmd[4:].strip()
		dirname = os.path.join(self.cwd, path)
		try:
			if not path:
				self.client.send('501 Missing arguments <dirname>.\r\n')
			else:
				os.rmdir(dirname)
				self.client.send('250 Directory deleted: ' + dirname + '.\r\n')
		except (Exception, e):
			print ('ERROR: ' + str(self.client_address) + ': ' + str(e))
			self.client.send('550 Failed to delete directory ' + dirname + '.')

	def STOR(self, cmd):
		path = cmd[4:].strip()
		if not path:
			self.client.send('501 Missing arguments <filename>.\r\n')
			return

		fname = os.path.join(self.cwd, path)
		(client_data, client_address) = self.start_datasock()
		
		try:
			file_write = open(fname, 'w')
			while True:
				data = client_data.recv(1024)
				if not data:
					break
				file_write.write(data)

			self.client.send('226 Transfer complete.\r\n')
		except (Exception, e):
			print ('ERROR: ' + str(self.client_address) + ': ' + str(e))
			self.client.send('425 Error writing file.\r\n')
		finally:
			client_data.close()
			self.close_datasock()
			file_write.close()

	def RETR(self, cmd):
		path = cmd[4:].strip()
		if not path:
			self.client.send('501 Missing arguments <filename>.\r\n')
			return

		fname = os.path.join(self.cwd, path)
		(client_data, client_address) = self.start_datasock()
		if not os.path.isfile(fname):
			self.client.send('550 File not found.\r\n')
		else:
			try:
				file_read = open(fname, "r")
				data = file_read.read(1024)

				while data:
					client_data.send(data)
					data = file_read.read(1024)

				self.client.send('226 Transfer complete.\r\n')
			except (Exception, e):
				print ('ERROR: ' + str(self.client_address) + ': ' + str(e))
				self.client.send('426 Connection closed; transfer aborted.\r\n')
			finally:
				client_data.close()
				self.close_datasock()
				file_read.close()


