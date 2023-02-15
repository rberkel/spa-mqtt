import asyncio
import paho.mqtt.client as mqtt
import json
import Heater
from geckolib import GeckoAsyncSpaMan, GeckoSpaEvent

MQTT_BROKER_IP = 'MQTT_BROKER_IP'
MQTT_BROKER_PORT = 1883

SPA_CLIENT_ID = "SPA_CLIENT_ID"
SPA_IP = None

class SampleSpaMan(GeckoAsyncSpaMan):
    """Sample spa man implementation"""

    async def handle_event(self, event: GeckoSpaEvent, **kwargs) -> None:
        # Uncomment this line to see events generated
        #print(f"{event}: {kwargs}")
        pass

class Spa():
    def __init__(self):
        self._mqtt_client = None
        self._watercare_command_pending = False
        self._temperature_command_pending = False
        self._watercare_mode = "Energy Saving"
        self._temperature_setpoint = 37.0
        self._mqtt_connect()        

    def _mqtt_connect(self, ip_address=MQTT_BROKER_IP, port=MQTT_BROKER_PORT, timeout=60):
        # Create an instance of the Paho MQTT Client class
        self._mqtt_client = mqtt.Client()

        # Create the callbacks
        self._mqtt_client.on_connect = self._on_mqtt_connect
        self._mqtt_client.on_message = self._on_mqtt_message

        # Connect to the broker
        self._mqtt_client.connect(ip_address, port, timeout)

        # Non blocking call that processes network traffic, dispatches callbacks and
        # handles reconnecting in a seperate thread.
        self._mqtt_client.loop_start()

    def _mqtt_disconnect(self):
        # Stop the loop that we started earlier
        self._mqtt_client.loop_stop()

        # Disconnect from broker
        self._mqtt_client.disconnect()
    
    def _on_mqtt_connect(self, client, userdata, flags, rc):
        print(f'Connected with result code {str(rc)}')
        self._mqtt_client.subscribe(topic='spa/command/operationMode')
        self._mqtt_client.subscribe(topic='spa/command/heaterSetpoint')

    def _on_mqtt_message(self, client, userdata, msg):
        if msg.topic == 'spa/command/operationMode':
            self._watercare_mode = json.loads(msg.payload)
            self._watercare_command_pending = True
        if msg.topic == 'spa/command/heaterSetpoint':
            self._temperature_setpoint = float(msg.payload)
            self._temperature_command_pending = True
    
    def send_heater_status(self, h: Heater):        
        self._mqtt_client.publish('spa/heater', str(json.dumps(Heater.heater_to_dict(h))))

    async def spa_control(self):
        async with SampleSpaMan(SPA_CLIENT_ID, spa_address=SPA_IP) as spaman:
            # Wait for descriptors to be available
            await spaman.wait_for_descriptors()

            if len(spaman.spa_descriptors) == 0:
                print("**** There were no spas found on your network.")
                return

            spa_descriptor = spaman.spa_descriptors[0]

            await spaman.async_set_spa_info(
                spa_descriptor.ipaddress,
                spa_descriptor.identifier_as_string,
                spa_descriptor.name,
            )

            counter = 0

            while(True):
                # Wait for the facade to be ready
                await spaman.wait_for_facade()
                
                if(self._watercare_command_pending):
                    self._watercare_command_pending = False
                    await spaman.facade.water_care.async_set_mode(self._watercare_mode)
                
                if(self._temperature_command_pending):
                    self._temperature_command_pending = False
                    #spaman.facade.water_heater.set_target_temperature(self._temperature_setpoint)
                    await spaman.facade.water_heater.async_set_target_temperature(self._temperature_setpoint)
                    
                if(counter >= 59):
                    heater_dict = {}
                    heater_dict['activeSetpoint'] = float(spaman.facade.water_heater.real_target_temperature)
                    heater_dict['configuredSetpoint'] = float(spaman.facade.water_heater.target_temperature)
                    heater_dict['operationState'] = str(spaman.facade.water_heater.current_operation).lower()
                    heater_dict['temperature'] = float(spaman.facade.water_heater.current_temperature)
                    heater = Heater.heater_from_dict(heater_dict)
                    self.send_heater_status(heater)
                    counter = 0
                else:
                    counter += 1

                await asyncio.sleep(1)

async def main() -> None:
    s = Spa()
    await s.spa_control()

if __name__ == "__main__":
    asyncio.run(main())