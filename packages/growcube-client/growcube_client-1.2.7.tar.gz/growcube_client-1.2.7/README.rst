Python-growcube-client
======================

|PyPI version| |PyPI pyversions| |PyPI license|

This is an asyncio Python library to communicate with `Elecrow
GrowCube <https://shrsl.com/4qit4>`__ devices. **Disclosure**: This is
an affiliate link for `Hands on Katie <https://handsonkatie.com>`__. If
you make a purchase through this link, she may earn a small commission
at no additional cost to you.

By using this library you can communicate directly with the device,
without the need to use the phone app.

Once connected to a device, the library will listen for messages from
the device and use a callback function to return parsed messages to the
application. The application can also send commands to the device.

Installation
------------

::

   pip install growcube-client

Documentation
-------------

The full library documentation can be `found
here <https://jonnybergdahl.github.io/growcube-client/>`__.

Getting started
---------------

The ``src/growcube_sample.py`` file shows how to use the library. It
defines a callback function where the GrowcubeClient sends messages as
they arrive from the Growcube device. To use the sample, change the
``HOST`` variable to the host name or IP address of the Growcube device.
Then run the sample with:

.. code:: bash

   python3 growcube_sample.py

Source code:

.. code:: python

   import asyncio
   from growcube_client import GrowcubeReport, GrowcubeClient


   # Define a on_message_callback function to print messages to the screen
   def callback(report: GrowcubeReport) -> None:
       # Just dump the message to the console
       print(f"Received: {report.get_description()}")


   async def main(host: str) -> None:
       # Create a client instance
       client = GrowcubeClient(host, callback)
       print(f"Connecting to Growcube at {HOST}")

       # Connect to the Growcube and start listening for messages
       await client.connect()

       while True:
           await asyncio.sleep(2)

   if __name__ == "__main__":
       # Set host name or IP address
       HOST = "172.30.2.72"

       asyncio.run(main(HOST))

Sample script output.

.. code:: text

   Connecting to Growcube at 172.30.2.70
   Received: RepDeviceVersionCmd: version 3.6, device_id 12663500
   Received: RepLockstateCmd: lock_state False
   Received: RepWaterStateCmd: water_warning: True
   Received: RepSTHSateCmd: pump: 0, moisture: 26, humidity: 41, temperature: 24
   Received: RepSTHSateCmd: pump: 1, moisture: 26, humidity: 41, temperature: 24
   Received: RepSTHSateCmd: pump: 2, moisture: 30, humidity: 41, temperature: 24
   Received: RepSTHSateCmd: pump: 3, moisture: 33, humidity: 41, temperature: 24

Important device states
~~~~~~~~~~~~~~~~~~~~~~~

+---------------------------------------+----------------------------------------------------+
| Report class                          | Use                                                |
+=======================================+====================================================+
| WaterStateGrowcubeReport              | Water warning                                      |
+---------------------------------------+----------------------------------------------------+
| MoistureHumidityStateGrowcubeReport   | Moisture, humidity and temperature, reported per   |
|                                       | channel. *Note: Humidity and temperature is the    |
|                                       | same for all 4*                                    |
+---------------------------------------+----------------------------------------------------+
| DeviceVersionGrowcubeReport           | Device id and firmware version                     |
+---------------------------------------+----------------------------------------------------+
| PumpOpenGrowcubeReport                | Pump outlet is open for channel                    |
+---------------------------------------+----------------------------------------------------+
| PumpCloseGrowcubeReport               | Pump outlet is closed for channel                  |
+---------------------------------------+----------------------------------------------------+
| CheckSensorGrowcubeReport             | Sensor not connected for channel                   |
+---------------------------------------+----------------------------------------------------+
| CheckPumpBlockedGrowcubeReport        | Pump outlet is blocked for channel                 |
+---------------------------------------+----------------------------------------------------+
| CheckSensorNotConnectedGrowcubeReport | Sensor is not connected for channel                |
+---------------------------------------+----------------------------------------------------+
| LockStateGrowcubeReport               | Device is in locked mode                           |
+---------------------------------------+----------------------------------------------------+
| CheckOutletLockGrowcubeReport         | Pump outlet is locked for channel                  |
+---------------------------------------+----------------------------------------------------+

More advanced use
-----------------

The ``src/growcube_app.py`` file shows how to use the library in a more
advanced application.

To use the app, you need to install ``wxPython`` first, please follow
`the directions
here <https://wiki.wxpython.org/How%20to%20install%20wxPython>`__.

Start the app with:

.. code:: bash

   python3 growcube_app.py

You are greeted with a screen asking for the host name or IP address of
the Growcube device. Enter that and click the *Submit* button. The app
will connect to your Growcube and starts displaying received data.

You can water plants by setting a watering duration and clicking the
*Pump X* button.

.. figure:: assets/app1.png
   :alt: Growcube app page 1

   Growcube app page 1

Adopt Growcube device
---------------------

The ``src/growcube_adopt.py`` file can be used to set WiFi credentials
of a new or factory reset Growcube device, without the need for the
Growcube phone app.

1. Make sure the Growcube flashes it’s red and blue LED’s.
2. Connect to the Growcube_Xxxx WiFi, password is 88888888
3. Run the ``growcube_adopt.py`` file
4. Press the *Connect* button and wait for connection
5. Enter the WiFi credentials and press the *Save* button
6. Wait for the device to connect to WiFi
7. Take a note of the IP address or MAC address as needed

Your Growcube is now connected to your WiFi.

.. figure:: assets/adopt.png
   :alt: Growcube adopt app

   Growcube adopt app

Auto discovery
==============

You can use the sample script ``src/growcube_discover.py`` to search for
devices on your network. By default, it will search for devices on the
local network, but if the devices are located in a separate subnet you
can also specify that network to search in.

.. code:: bash

   python3 growcube_discover.py 192.168.4.0/24

The output will look like this.

::

   Discovering Growcube clients on subnet 172.30.2.0/24
   Trying to connect to 172.30.2.1
   Trying to connect to 172.30.2.2
   ...
   Trying to connect to 172.30.2.254
   Found 2 devices:
   Found device: 172.30.2.71
   Found device: 172.30.2.70

.. |PyPI version| image:: https://badge.fury.io/py/growcube-client.svg
   :target: https://badge.fury.io/py/growcube-client
.. |PyPI pyversions| image:: https://img.shields.io/pypi/pyversions/growcube-client.svg
   :target: https://pypi.python.org/pypi/growcube-client/
.. |PyPI license| image:: https://img.shields.io/pypi/l/ansicolortags.svg
   :target: https://pypi.python.org/pypi/ansicolortags/
