#!/usr/bin/python
# encoding: utf-8
import argparse
import socket
import struct
import time
import usb

# Some magic values to be able to read from TEMPer devices presenting
# a USB ID like this: "0c45:7401 Microdia" (check `lsusb`)
VID = 0x0c45L
PID = 0x7401L
TIMEOUT = 4000
COMMANDS = {
  'temp': '\x01\x80\x33\x01\x00\x00\x00\x00',
  'ini1': '\x01\x82\x77\x01\x00\x00\x00\x00',
  'ini2': '\x01\x86\xff\x01\x00\x00\x00\x00',
}
REQ_INT_LEN = 8
ENDPOINT = 0x82
INTERFACE = 1

def _send_data(addr, message):
  sock = socket.socket()
  timeout_in_s = 2
  sock.settimeout(timeout_in_s)
  try:
    sock.connect(addr)
  except socket.timeout:
    print "Took over %d second(s) to connect to %s" % (timeout_in_s, addr)
    return
  except Exception as error:
    print "Unknown exception while connection to %s: %s" % (addr, error)
    return

  try:
    sock.sendall(message)
  except Exception as error:
    print "Unknown exception while sending to %s: %s" % (addr, error)
    return

  print "Data sent successfully."
  sock.shutdown(1)


def _ctrl(dev, data):
  dev.ctrl_transfer(bmRequestType=0x21, bRequest=0x09, wValue=0x0200,
          wIndex=0x01, data_or_wLength=data, timeout=TIMEOUT)

def _read(dev):
  return dev.read(ENDPOINT, REQ_INT_LEN, interface=INTERFACE, timeout=TIMEOUT)

def _take_control(dev):
  try:
    dev.detach_kernel_driver(INTERFACE)
  except usb.USBError:
    pass
  dev.set_configuration()

def _to_celsius(data):
  fmt_bigendian_short = '>h'
  data_s = "".join([chr(byte) for byte in data])
  temp_c = 125.0/32000.0*(struct.unpack(fmt_bigendian_short, data_s[2:4])[0])
  return temp_c

def _to_fahrenheit(temp_in_celsius):
  return temp_in_celsius * 1.8 + 32

def _do_temp_reading(dev):
  if dev.is_kernel_driver_active(INTERFACE):
    _take_control(dev)

  usb.util.claim_interface(dev, INTERFACE)

  _ctrl(dev, COMMANDS['temp'])
  _read(dev)
  _ctrl(dev, COMMANDS['ini1'])
  _read(dev)
  _ctrl(dev, COMMANDS['ini2'])
  _read(dev)
  _read(dev)
  _ctrl(dev, COMMANDS['temp'])
  data = _read(dev)

  usb.util.release_interface(dev, INTERFACE)
  dev.reset()
  return data

def _get_device():
  return usb.core.find(find_all=True, idVendor=VID, idProduct=PID)[0]


def get_reading(fahrenheit = False):
  if fahrenheit:
    return _to_fahrenheit(_to_celsius(_do_temp_reading(_get_device())))
  else:
    return _to_celsius(_do_temp_reading(_get_device()))

def send_to_graphite(addr, metric, value):
  timestamp = int(time.time())
  message = "%s %f %d\n" % (metric, value, timestamp)
  _send_data(addr, message)

def cli():
  parser = argparse.ArgumentParser(
    description='Send temperature to graphite using TEMPer device.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('--no-send', dest='send', default='Do send',
          action='store_false',
          help='do not send reading to graphite server')
  parser.add_argument('--fahrenheit', dest='fahrenheit', default='Use celsius',
          action='store_true',
          help='output temperature in fahrenheit')
  parser.add_argument('--host', metavar='host', type=str, default='localhost',
          help='address of graphite server')
  parser.add_argument('--port', metavar='port', type=int, default=2003,
          help='port of graphite server')
  parser.add_argument('--metric', metavar='metric', type=str,
          default='local.temp', help='graphite metric name')
  args = parser.parse_args()
  addr = (args.host, args.port)
  metric = args.metric
  do_send = args.send
  fahrenheit = True if args.fahrenheit != 'Use celsius' else False

  temp = get_reading(fahrenheit)
  print "Temperature reading: %0.1f°%s" % (temp, 'F' if fahrenheit else 'C')

  if do_send:
    print "Sending to Graphite on %s:%d..." % addr
    send_to_graphite(addr, metric, temp)

if __name__ == '__main__':
  cli()

