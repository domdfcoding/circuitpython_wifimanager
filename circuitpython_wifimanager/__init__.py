#!/usr/bin/env python3
#
#  __init__.py
"""
This library provides helper class for boards with builtin WiFi, such as the ESP32-S2.

It has a fairly similar interface to the Adafruit_ESP32SPI_ library's ``adafruit_esp32spi_wifimanager`` module.

This module was designed for the Adafruit `ESP32-S2 Feather`_,
but should work with other boards based on the same or similar chips,
such as the `Metro ESP32-S2`_.
The main requirement is that the chip's WiFi radio is interfaced via the ``wifi``
module [1]_ shipped with CircuitPython.

.. _Adafruit_ESP32SPI: https://github.com/adafruit/Adafruit_CircuitPython_ESP32SPI
.. _ESP32-S2 Feather: https://www.adafruit.com/product/5303
.. _Metro ESP32-S2: https://www.adafruit.com/product/4775
.. [1] https://circuitpython.readthedocs.io/en/latest/shared-bindings/wifi/index.html
"""
#
#  Based adafruit_esp32spi_wifimanager.py
#  from https://github.com/adafruit/Adafruit_CircuitPython_ESP32SPI/
#  SPDX-FileCopyrightText: Copyright (c) 2019 Melissa LeBlanc-Williams for Adafruit Industries
#  SPDX-FileCopyrightText: Copyright (c) 2021 Dominic Davis-Foster
#
#  SPDX-License-Identifier: MIT
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#  DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#  OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
#  OR OTHER DEALINGS IN THE SOFTWARE.
#

# stdlib
import ipaddress
import rtc  # type: ignore[import]  # nodep (CircuitPython builtin)
import socketpool  # type: ignore[import]  # nodep (CircuitPython builtin)
import ssl
import struct
import time
from micropython import const  # nodep (CircuitPython builtin)
from time import sleep

# 3rd party
import adafruit_requests as requests  # type: ignore[import]

if False:  # TYPE_CHECKING
	# stdlib
	import wifi  # type: ignore[import]
	from types import TracebackType
	from typing import Any, Dict, NoReturn, Optional, Tuple, Type, Union

__author__: str = "Dominic Davis-Foster"
__copyright__: str = "2021 Dominic Davis-Foster"
__license__: str = "MIT License"
__version__: str = "0.0.0"
__email__: str = "dominic@davis-foster.co.uk"

__all__ = ["WiFiManager"]

# reference time for NTP (in seconds since 1900-01-01 00:00:00)
TIME1970 = 2208988800  # 1970-01-01 00:00:00


class WiFiManager:
	"""
	A class to help manage the Wi-Fi connection.
	"""

	NORMAL: int = const(1)
	ENTERPRISE: int = const(2)

	def __init__(
			self,
			radio: wifi.Radio,
			secrets: Dict[str, Any],
			status_pixel: Optional[Any] = None,
			connection_type: int = NORMAL,
			debug: bool = False,
			):
		"""
		:param radio: The Wi-Fi radio object we are using (typically ``wifi.radio``).
		:param secrets: The Wi-Fi secrets dict.
		:param status_pixel: (Optional) The pixel device - A NeoPixel, DotStar, or RGB LED.
		:type status_pixel: NeoPixel, DotStar, or RGB LED
		:param debug:
		"""

		# Read the settings
		self.radio = radio
		self.debug = debug
		self.ssid = secrets["ssid"]
		self.password = secrets.get("password", None)
		self._connection_type = connection_type
		self.statuspix = status_pixel
		self.pixel_status(0)
		self._ap_index = 0
		self._pool: "Optional[socketpool.SocketPool]" = None
		self._requests: "Optional[requests.Session]" = None

		# Check for WPA2 Enterprise keys in the secrets dictionary and load them if they exist
		if secrets.get("ent_ssid"):
			self.ent_ssid = secrets["ent_ssid"]
		else:
			self.ent_ssid = secrets["ssid"]
		if secrets.get("ent_ident"):
			self.ent_ident = secrets["ent_ident"]
		else:
			self.ent_ident = ''
		if secrets.get("ent_user"):
			self.ent_user = secrets["ent_user"]
		if secrets.get("ent_password"):
			self.ent_password = secrets["ent_password"]

	# pylint: enable=too-many-arguments

	def reset(self) -> "NoReturn":  # noqa: D102
		raise NotImplementedError

	def connect(self) -> None:
		"""
		Attempt to connect to WiFi using the current settings.
		"""

		if self.debug:
			print("MAC addr:", [hex(i) for i in self.radio.mac_address])

			for access_pt in self.radio.start_scanning_networks():
				print("\t%s\t\tRSSI: %d" % (str(access_pt.ssid, "utf-8"), access_pt.rssi))

			self.radio.stop_scanning_networks()

		if self._connection_type == self.NORMAL:
			self.connect_normal()
		elif self._connection_type == self.ENTERPRISE:
			self.connect_enterprise()
		else:
			raise TypeError("Invalid WiFi connection type specified")

		self._pool = socketpool.SocketPool(self.radio)
		self._requests = requests.Session(self._pool, ssl.create_default_context())

	def _get_next_ap(self) -> "Tuple[str, Optional[str]]":
		if isinstance(self.ssid, (tuple, list)) and isinstance(self.password, (tuple, list)):
			if not self.ssid or not self.password:
				raise ValueError("SSID and Password should contain at least 1 value")
			if len(self.ssid) != len(self.password):
				raise ValueError("The length of SSIDs and Passwords should match")
			access_point = (self.ssid[self._ap_index], self.password[self._ap_index])
			self._ap_index += 1
			if self._ap_index >= len(self.ssid):
				self._ap_index = 0
			return access_point
		if isinstance(self.ssid, (tuple, list)) or isinstance(self.password, (tuple, list)):
			raise NotImplementedError(
					"If using multiple passwords, both SSID and Password should be lists or tuples"
					)
		return self.ssid, self.password

	def connect_normal(self) -> None:
		"""
		Attempt a regular style Wi-Fi connection.
		"""

		failure_count = 0
		(ssid, password) = self._get_next_ap()
		while not self.radio.ap_info:
			try:
				if self.debug:
					print("Connecting to AP...")
				self.pixel_status((100, 0, 0))
				self.radio.connect(ssid, password)
				failure_count = 0
				self.pixel_status((0, 100, 0))
			except (ValueError, RuntimeError) as error:
				print("Failed to connect, retrying\n", error)
				failure_count += 1
				# TODO: need to be able to reset somehow.
				# if failure_count >= self.attempts:
				# 	failure_count = 0
				# 	(ssid, password) = self._get_next_ap()
				# 	# self.reset()
				continue

	def create_ap(self) -> None:
		"""
		Attempt to initialize in Access Point (AP) mode.

		Uses SSID and optional passphrase from the current settings.
		Other Wi-Fi devices will be able to connect to the created Access Point.
		"""

		raise NotImplementedError

		failure_count = 0
		while not self.esp.ap_listening:
			try:
				if self.debug:
					print("Waiting for AP to be initialized...")
				self.pixel_status((100, 0, 0))
				if self.password:
					self.esp.create_AP(bytes(self.ssid, "utf-8"), bytes(self.password, "utf-8"))
				else:
					self.esp.create_AP(bytes(self.ssid, "utf-8"), None)
				failure_count = 0
				self.pixel_status((0, 100, 0))
			except (ValueError, RuntimeError) as error:
				print("Failed to create access point\n", error)
				failure_count += 1
				if failure_count >= self.attempts:
					failure_count = 0
					self.reset()
				continue
		print(f"Access Point created! Connect to ssid:\n {self.ssid}")

	def connect_enterprise(self) -> None:
		"""
		Attempt an enterprise style Wi-Fi connection.
		"""

		raise NotImplementedError

		failure_count = 0
		self.esp.wifi_set_network(bytes(self.ent_ssid, "utf-8"))
		self.esp.wifi_set_entidentity(bytes(self.ent_ident, "utf-8"))
		self.esp.wifi_set_entusername(bytes(self.ent_user, "utf-8"))
		self.esp.wifi_set_entpassword(bytes(self.ent_password, "utf-8"))
		self.esp.wifi_set_entenable()
		while not self.radio.ap_info:
			try:
				if self.debug:
					print("Waiting for the ESP32 to connect to the WPA2 Enterprise AP...")
				self.pixel_status((100, 0, 0))
				sleep(1)
				failure_count = 0
				self.pixel_status((0, 100, 0))
				sleep(1)
			except (ValueError, RuntimeError) as error:
				print("Failed to connect, retrying\n", error)
				failure_count += 1
				if failure_count >= self.attempts:
					failure_count = 0
					self.reset()
				continue

	def get(self, url: str, **kw) -> requests.Response:
		"""
		Pass the Get request to requests and update status LED.

		:param url: The URL to retrieve data from.
		:param dict data: (Optional) Form data to submit.
		:param dict json: (Optional) JSON data to submit. (Data must be :py:obj:`None`).
		:param dict header: (Optional) Header data to include.
		:param bool stream: (Optional) Whether to stream the Response.

		:return: The response from the request.
		"""

		if not self.radio.ap_info:
			self.connect()

		assert self._requests is not None

		self.pixel_status((0, 0, 100))
		return_val = self._requests.get(url, **kw)
		self.pixel_status(0)
		return return_val

	def post(self, url: str, **kw) -> requests.Response:
		"""
		Pass the Post request to requests and update status LED.

		:param url: The URL to post data to.
		:param dict data: (Optional) Form data to submit.
		:param dict json: (Optional) JSON data to submit. (Data must be :py:obj:`None`).
		:param dict header: (Optional) Header data to include.
		:param bool stream: (Optional) Whether to stream the Response.

		:return: The response from the request.
		"""

		if not self.radio.ap_info:
			self.connect()

		assert self._requests is not None

		self.pixel_status((0, 0, 100))
		return_val = self._requests.post(url, **kw)
		return return_val

	def put(self, url: str, **kw) -> requests.Response:
		"""
		Pass the put request to requests and update status LED.

		:param url: The URL to PUT data to.
		:param dict data: (Optional) Form data to submit.
		:param dict json: (Optional) JSON data to submit. (Data must be :py:obj:`None`).
		:param dict header: (Optional) Header data to include.
		:param bool stream: (Optional) Whether to stream the Response.

		:return: The response from the request.
		"""

		if not self.radio.ap_info:
			self.connect()

		assert self._requests is not None

		self.pixel_status((0, 0, 100))
		return_val = self._requests.put(url, **kw)
		self.pixel_status(0)
		return return_val

	def patch(self, url: str, **kw) -> requests.Response:
		"""
		Pass the patch request to requests and update status LED.

		:param url: The URL to PUT data to.
		:param dict data: (Optional) Form data to submit.
		:param dict json: (Optional) JSON data to submit. (Data must be :py:obj:`None`).
		:param dict header: (Optional) Header data to include.
		:param bool stream: (Optional) Whether to stream the Response.

		:return: The response from the request.
		"""

		if not self.radio.ap_info:
			self.connect()

		assert self._requests is not None

		self.pixel_status((0, 0, 100))
		return_val = self._requests.patch(url, **kw)
		self.pixel_status(0)
		return return_val

	def delete(self, url: str, **kw) -> requests.Response:
		"""
		Pass the delete request to requests and update status LED.

		:param url: The URL to PUT data to.
		:param dict data: (Optional) Form data to submit.
		:param dict json: (Optional) JSON data to submit. (Data must be :py:obj:`None`).
		:param dict header: (Optional) Header data to include.
		:param bool stream: (Optional) Whether to stream the Response.

		:return: The response from the request.
		"""

		if not self.radio.ap_info:
			self.connect()

		assert self._requests is not None

		self.pixel_status((0, 0, 100))
		return_val = self._requests.delete(url, **kw)
		self.pixel_status(0)
		return return_val

	def ping(self, host: str, *, timeout: "Optional[float]" = 0.5) -> float:
		"""
		Pass the Ping request to the ESP32, update status LED, return response time.

		:param host: The hostname or IP address to ping.
		:param timeout: How long to wait before timing out.

		:returns: The echo time in seconds, or :py:obj:`None` when it times out.
		"""

		if not self.radio.ap_info:
			self.connect()

		assert self._pool is not None

		self.pixel_status((0, 0, 100))
		addrinfo = self._pool.getaddrinfo(host, 80)
		ip = ipaddress.ip_address(addrinfo[0][4][0])
		response_time = self.radio.ping(ip, timeout=timeout)
		self.pixel_status(0)
		return response_time

	def ip_address(self) -> str:
		"""
		Returns a formatted local IP address, update status pixel.
		"""

		if not self.radio.ap_info:
			self.connect()
		self.pixel_status((0, 0, 100))
		self.pixel_status(0)
		return str(self.radio.ipv4_address)

	def pixel_status(self, value: "Union[int, Tuple[int, int, int]]") -> None:
		"""
		Change Status Pixel if it was defined.

		:param value: The value to set the Board's status LED to.
		"""

		if self.statuspix:
			if hasattr(self.statuspix, "color"):
				self.statuspix.color = value
			else:
				self.statuspix.fill(value)

	def signal_strength(self) -> int:
		"""
		Returns receiving signal strength indicator in dBm.
		"""

		if not self.radio.ap_info:
			self.connect()
		return self.radio.ap_info.rssi

	def deinit(self) -> None:
		"""
		Blank out the NeoPixels and release the socket pool.
		"""

		self.pixel_status(0)

		if self._pool is not None:
			self._pool.close()()

	def __enter__(self) -> "WiFiManager":
		return self

	def __exit__(
			self,
			exception_type: "Optional[Type[BaseException]]",
			exception_value: "Optional[BaseException]",
			traceback: "Optional[TracebackType]",
			) -> None:
		self.deinit()

	def get_ntp_time(self, tz_offset: int = 0, *, debug: bool = False) -> None:
		"""
		Obtain the current time over NTP and set the internal RTC.
		"""

		msg = b'\x1b' + 47 * b'\0'

		if not self.radio.ap_info:
			self.connect()

		assert self._pool is not None

		client = self._pool.socket(self._pool.AF_INET, self._pool.SOCK_DGRAM)
		client.settimeout(30)
		with client:
			client.sendto(msg, ("pool.ntp.org", 123))
			buffer = bytearray(1024)
			size, _ = client.recvfrom_into(buffer)

		t = struct.unpack("!12I", buffer[:size])[10]
		t -= TIME1970

		now = time.localtime(t + tz_offset)
		rtc.RTC().datetime = now
		if debug:
			print("Time set to", now)
