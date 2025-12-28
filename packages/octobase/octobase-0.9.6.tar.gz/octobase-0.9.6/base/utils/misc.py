#!/opt/local/bin/python
''' Useful functions unlike any other. '''

import base
import fcntl
import os


def PrivateIp(ipaddr):
  ''' if the ipaddr is on a private network, returns the first octets; handles both IP v4 and v6 '''
  for candidate in ['10.', '192.168.', 'fd'] + ['172.' + str(x) + '.' for x in range(16,32)]:
    if ipaddr.startswith(candidate):
      return candidate


def GeneralizeIp4(ipaddr):
  ''' rounds the IPv4 address to each successive octet being '.0' and returns a list '''
  tokens          = ipaddr.split('.')
  prefixes        = [tokens[0], '.'.join(tokens[:2]), '.'.join(tokens[:3])]
  ipaddies        = [prefixes[0] + '.0.0.0', prefixes[1] + '.0.0', prefixes[2] + '.0']
  return [x for x in ipaddies if x != ipaddr]



def ReverseReadLines(file, buf_size=8192):
  ''' A proper memory-buffered generator to read the lines of a text file in reverse order.
      Thanks http://stackoverflow.com/questions/2301789/read-a-file-in-reverse-order-using-python
  '''
  segment         = None
  offset          = 0
  file.seek(0, os.SEEK_END)
  file_size       = remaining_size = file.tell()
  while remaining_size > 0:
    offset        = min(file_size, offset + buf_size)
    file.seek(file_size - offset)
    buffer        = file.read(min(remaining_size, buf_size))
    remaining_size -= buf_size
    lines         = buffer.split('\n')
    # the first line of the buffer is probably not a complete line so
    # we'll save it and append it to the last line of the next buffer
    # we read
    if segment is not None:
      # if the previous chunk starts right from the beginning of line
      # do not concact the segment to the last line of new chunk
      # instead, yield the segment first
      if buffer[-1] != '\n':
        lines[-1] += segment
      else:
        yield segment
    segment       = lines[0]
    for index in range(len(lines) - 1, 0, -1):
      if len(lines[index]):
        yield lines[index]
  # Don't yield None if the file was empty
  if segment is not None:
    yield segment



class LockedFileOpen:
  ''' opens a file for binary read-write while underneath a UNIX-style exclusive lock '''

  def __init__(self, filepath):
    self.filepath   = filepath
    self.fileno     = None

  def __enter__(self):
    self.fileno     = os.open(self.filepath, os.O_RDWR)
    fcntl.flock(self.fileno, fcntl.LOCK_EX)
    return open(self.fileno, 'r+b', closefd=False)

  def __exit__(self, *_, **__):
    fcntl.flock(self.fileno, fcntl.LOCK_UN)
    os.close(self.fileno)
