import struct, collections

class AMF3Date:
	date = 0.0
	def __init__(self, date):
		self.date = date
	def __str__(self):
		return 'timestamp ['+str(self.date)+']'

class AMF3:
	
	data = None
	index = -1
	
	string_list = []
	
	def __init__(self, data = bytes()):
		self.data = data
		self.string_list = []
	
	
	def raw_byte(self):
		self.index += 1
		return self.data[self.index]
	
	def raw_bytes(self, count):
		self.index += count
		return self.data[self.index - count + 1:self.index + 1]
	
	
	def read_file(self, file):
		with open(file, mode='rb') as f:
			self.data = bytes(f.read())
		self.index = -1
		self.string_list = []
		return self.read_value()
	def write_file(self, file, object = None):
		if object != None:
			self.serialize(object)
		with open(file, mode='wb') as f:
			f.write(self.data)
	def serialize(self, object):
		self.index = -1
		self.data = bytearray()
		self.string_list = []
		self.write_value(object)
		return self.data
	
	def read_value(self):
		tag = self.raw_byte()
		if tag == 0x01: return None
		if tag == 0x02: return False
		if tag == 0x03: return True
		if tag == 0x04: return self.read_int()
		if tag == 0x05: raise ValueError("double")
		if tag == 0x06: return self.read_string()
		if tag == 0x07: raise ValueError("XML")
		if tag == 0x08: return self.read_date()
		if tag == 0x09: return self.read_array()
		if tag == 0x0a: return self.read_object()
		raise ValueError("unknown tag "+hex(tag)+" at "+hex(self.index))
	def write_value(self, value):
		t = type(value)
		if value is None:
			self.data.append(0x01)
		elif t is bool:
			self.data.append(0x03 if value else 0x02)
		elif t is int:
			self.data.append(0x04)
			self.write_int(value)
		elif t is str:
			self.data.append(0x06)
			self.write_string(value)
		elif t is AMF3Date:
			self.data.append(0x08)
			self.write_date(value)
		elif t is list:
			self.data.append(0x09)
			self.write_array(value)
		elif t is dict or t is collections.OrderedDict:
			self.data.append(0x0a)
			self.write_object(value)
		else:
			raise ValueError(str(t)+" :: "+str(value))
	
	def read_object(self):
		r = collections.OrderedDict()
		while True:
			header = self.raw_byte()
			if header == 0x01: break
			assert header == 0x0b and self.index == 1
			# start of file has 0x0b
			#print("header found: "+hex(header))
		while True:
			field_name = self.read_string()
			if field_name == '': break # i.e. ending 0x01
			if field_name in r: raise ValueError(field_name+" already in "+str(r))
			#print("reading field "+field_name)
			r[field_name] = self.read_value()
			#print(" -> "+str(r[field_name]))
		return r
	def write_object(self, object):
		if len(self.data) == 1: # not sure what this flag is, but it is only set for the outermost object
			self.data.append(0x0b)
		self.data.append(0x01)
		for field_name in object:
			self.write_string(field_name)
			self.write_value(object[field_name])
		self.data.append(0x01)
	
	def read_array(self):
		length = self.read_int() >> 1
		assert self.raw_byte() == 0x01
		r = []
		while length > 0:
			#print("reading array value")
			r.append(self.read_value())
			#print(" -> "+str(r[-1]))
			length -= 1
		return r
	def write_array(self, array):
		self.write_int((len(array) << 1) | 0x01)
		self.data.append(0x01)
		for val in array:
			self.write_value(val)
	
	def read_date(self):
		assert self.raw_byte() == 0x01
		return AMF3Date(struct.unpack('>d', self.raw_bytes(8))[0])
	def write_date(self, date):
		self.data.append(0x01)
		self.data.extend(struct.pack('>d', date.date))
	
	def read_int(self):
		result = 0
		while True:
			result <<= 7
			b = self.raw_byte()
			if result == 0 and b == 0xff: # TODO is this correct?
				self.index -= 1
				return struct.unpack('>i', self.raw_bytes(4))[0]
			result += (b - 0x80 if b >= 0x80 else b)
			if b < 0x80:
				return result
	def write_int(self, value):
		if value == 0:
			self.data.append(0x00)
		elif value < 0:
			self.data.extend(struct.pack('>i', value))
		else:
			result = []
			while value > 0:
				result = [(value & 0x7f) + (0x80 if len(result) > 0 else 0)] + result
				value >>= 7
			self.data.extend(result)
	
	def read_string(self):
		length = self.read_int()
		if length & 0x01 == 0:
			return self.string_list[length >> 1]
		length >>= 1
		r = self.data[self.index + 1 : self.index + length + 1].decode('utf-8')
		self.index += length
		if r != '':
			self.string_list.append(r)
		return r
	def write_string(self, string):
		if string != '' and string in self.string_list:
			self.write_int(self.string_list.index(string) << 1)
		else:
			string_bytes = string.encode('utf-8')
			self.write_int((len(string_bytes) << 1) | 0x01)
			self.data.extend(string_bytes)
			if string != '':
				self.string_list.append(string)
	
#import os
#save_dir = os.path.expanduser("~")+'/AppData/Roaming/dungeoneering/Local Store'
#save_slot = 1
#print(AMF3().read_file(os.path.join(save_dir, 'slot'+str(save_slot)+'.sav')))
	