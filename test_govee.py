import asyncio
from govee_api_laggat import Govee

API_KEY = "332fe7ca-0995-436d-ad33-c837ae8af443"

async def main():
    print("332fe7ca-0995-436d-ad33-c837ae8af443")
    
    async with Govee(API_KEY) as govee:
        print("\nFetching your devices...\n")
        
        devices, err = await govee.get_devices()
        
        if err:
            print(f"Error: {err}")
        else:
            print(f"Found {len(devices)} Govee device(s):\n")
            for device in devices:
                print(f"Name: {device.device_name}")
                print(f"Model: {device.model}")
                print(f"Device ID: {device.device}")
                print(f"Controllable: {device.controllable}")
                print(f"Online: {device.online}")
                print("-" * 40)

asyncio.run(main())

