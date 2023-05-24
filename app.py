import re
import os
import json
import requests
import paho.mqtt.client as mqtt

def get_custom_config(file_location):
    with open(file_location, "r") as config_file:
        config = {}
        for line in config_file:
            key_value_pair = line.strip("\n").split("=")
            config[key_value_pair[0]] = key_value_pair[1]
    return config

# opening and extracing contents from config file
config_file_location = os.getenv("ARAMARKCONFIG") # for this to work you need to MAKE an environment variable called ARAMARKCONFIG with the value exact filepath to your config
if config_file_location:
    ara_config = get_custom_config(config_file_location)
    
    broker = ara_config["broker"]
    port = int(ara_config["port"])
    topic_prefix = ara_config["topic_prefix"]
    api_key = ara_config["api_key"]
    base_url = ara_config["base_url"]
    menu_id = ara_config["menu_id"]
else:
    raise RuntimeError('environment variable not found: ARAMARKCONFIG is probably undefined')

def main():
    aramark_menu = get_aramark_menu()
    main_categories = get_main_categories(aramark_menu)

    client = connect_mqtt()
    # loop_start > loop_forever | loop_forever is blocking till the client calls disconnect vs loop_start runs in a background thread
    client.loop_start()

    send_all_dishes(client=client, categories=main_categories)

    # don't even know if I need to call this when useing loop_start and loop_stop but doing it anyways just in case
    client.disconnect()
    # idk but I wanna stop it when I'm done
    client.loop_stop()


def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def send_all_dishes(client, categories):
    for category in categories:
        for key, value in category.items():
            if not key == "topic":
                topic = topic_prefix + category["topic"] + "/" + key
                print(topic, value)
                send_message = client.publish(topic, value)
                send_message.wait_for_publish()


def get_aramark_menu():
    response = requests.get(
        base_url + menu_id,
        headers={
            "Authorization": api_key,
            "App-Brand": "Aramark",
            "Response-Version": "v3",
            "Accept-Language": "de",
        },
    )
    return response.json()


def get_main_categories(json_data):
    for category in json_data["Categories"]:
        if category["Name"] == "klassik-mix":
            klassik_mix_data = category
        elif category["Name"] == "food-factory":
            food_factory_data = category
        elif category["Name"] == "v-like":
            v_like_data = category
        elif category["Name"] == "worldtour":
            worldtour_data = category

    klassik_mix = {
        "name": klassik_mix_data["Products"][0]["Name"],
        "price": (klassik_mix_data["Products"][0]["Prices"][0]["LocalizablePrice"][
            "Amount"
        ] / 100),
        "topic": "klassik-mix",
    }
    food_factory = {
        "name": food_factory_data["Products"][0]["Name"],
        "price": (food_factory_data["Products"][0]["Prices"][0]["LocalizablePrice"][
            "Amount"
        ] / 100),
        "topic": "food-factory",
    }
    v_like = {
        "name": v_like_data["Products"][0]["Name"],
        "price": (v_like_data["Products"][0]["Prices"][0]["LocalizablePrice"]["Amount"] / 100),
        "topic": "v-like",
    }
    worldtour = {
        "name": worldtour_data["Products"][0]["Name"],
        "price": (worldtour_data["Products"][0]["Prices"][0]["LocalizablePrice"][
            "Amount"
        ] / 100),
        "topic": "worldtour",
    }
    return (klassik_mix, food_factory, v_like, worldtour)


def get_pommes_bool(json_data):
    boolean = False
    for category in json_data["Categories"]:
        for product in category["Products"]:
            if re.match(r"Pommes", product["Name"]):
                boolean = True
    return boolean


if __name__ == "__main__":
    main()
