import ast
import datetime

class ByteFormatter:
	def __init__(
		self,
		byte_encoded_data):
		self.byte_encoded_data = byte_encoded_data

	def _format_byte_to_dict(self):
		dict_str =  self.byte_encoded_data.decode('UTF-8')
		data = ast.literal_eval(dict_str)
		data['set']['timestamp'] = datetime.datetime.now().isoformat()
		return data

	def _extract_nc_line(self, bfc_data):
		datapoints = bfc_data['set']['datapoints']
		for datapoint in datapoints:
			if datapoint["name"] == "NCLine":
				return datapoint["value"]
		