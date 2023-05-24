import re
import os
import json
import requests
import paho.mqtt.client as mqtt

def get_custom_config(file_location:str):
    with open(file_location, "r") as config_file:
        config = {}
        for line in config_file:
            key_value_pair = line.strip("\n").split("=")
            config[key_value_pair[0]] = key_value_pair[1]
    return config

# opening and extracing contents from config file
config_file_location = os.getenv("ARAMARKCONFIG")
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

def test():
    test_pommes_menu = '{"Date":"2023-05-16T00:00:00Z","Categories":[{"Id":88080,"Name":"suppen-topf","Products":[{"Id":14729635,"Name":"Gemüsecremesuppe ","Allergens":[6],"SubAllergens0":[],"SubAllergens7":[],"Additives":[],"CustomTags":[],"Prices":[{"Id":57790,"InternalName":"Preis","Price":0.65,"LocalizablePrice":{"CurrencyCode":"EUR","Amount":65}}],"CoverUrls":[],"NutritionFacts":{"KCalPer100":41,"KJPer100":172,"FatsPer100":1.7,"SatsPer100":1,"CarbsPer100":5,"SugarPer100":2.3,"ProteinsPer100":1.3,"SaltPer100":0.5},"Infos":[],"LabelGroups":[],"IsSoldOut":false,"Quantity":1,"Ratings":{}}],"IsHidden":false},{"Id":88081,"Name":"klassik-mix","Products":[{"Id":14729636,"Name":"Hausgemachte Hackfleischpfanne vom Rind | Zartweizen | Mais | Paprika","Allergens":[0],"SubAllergens0":[0],"SubAllergens7":[],"Additives":[],"CustomTags":[{"Id":2225,"Name":"foodboost","IconUrl":"https://qnips.blob.core.windows.net/releaseicons/iconfoodboost20190923141034_2020.10.06_14.56.12.png"},{"Id":5194,"Name":"mit Rind","IconUrl":"https://cdn3.qnips.com/releaseicons/i007iconrind-kalb_2021.09.08_12.24.49.jpg"},{"Id":6167,"Name":"Bäuerliche Erzeugergemeinschaft Schwäbisch Hall ","IconUrl":"https://files.qnips.com/releaseicons/logobeshnurwappen_2022.11.30_13.54.21.jpg"}],"Prices":[{"Id":57790,"InternalName":"Preis","Price":5.5,"LocalizablePrice":{"CurrencyCode":"EUR","Amount":550}}],"CoverUrls":[],"NutritionFacts":{"KCalPer100":117,"KJPer100":489,"FatsPer100":4.6,"SatsPer100":1.9,"CarbsPer100":10.5,"SugarPer100":1.8,"ProteinsPer100":8.2,"SaltPer100":0.3},"Infos":[],"LabelGroups":[],"IsSoldOut":false,"Quantity":1,"Ratings":{}}],"IsHidden":false},{"Id":88083,"Name":"food-factory","Products":[{"Id":14729637,"Name":"Gegrillte Oberländer I hausgemachter Currysauce","Allergens":[2,8,9],"SubAllergens0":[],"SubAllergens7":[],"Additives":[1,2],"CustomTags":[{"Id":1235,"Name":"mit Schwein","IconUrl":"https://cdn3.qnips.com/releaseicons/i008iconschwein_2021.09.08_12.13.51.jpg"}],"Prices":[{"Id":57790,"InternalName":"Preis","Price":3.7,"LocalizablePrice":{"CurrencyCode":"EUR","Amount":370}}],"CoverUrls":[],"NutritionFacts":{"KCalPer100":539,"KJPer100":2251,"FatsPer100":53.5,"SatsPer100":7.9,"CarbsPer100":9.7,"SugarPer100":9.2,"ProteinsPer100":6.1,"SaltPer100":2.5},"Infos":[],"LabelGroups":[],"IsSoldOut":false,"Quantity":1,"Ratings":{}}],"IsHidden":false},{"Id":88438,"Name":"food-factory-beilage","Products":[{"Id":14561024,"Name":"Ofenfrisches Brötchen","Allergens":[0],"SubAllergens0":[0,1],"SubAllergens7":[],"Additives":[],"CustomTags":[],"Prices":[{"Id":57790,"InternalName":"Preis","Price":0.4,"LocalizablePrice":{"CurrencyCode":"EUR","Amount":40}}],"CoverUrls":[],"NutritionFacts":{"KCalPer100":284,"KJPer100":1188,"FatsPer100":1.8,"SatsPer100":0.4,"CarbsPer100":55.9,"SugarPer100":3.1,"ProteinsPer100":10.1,"SaltPer100":1.8},"Infos":[],"LabelGroups":[],"IsSoldOut":false,"Quantity":1,"Ratings":{}}],"IsHidden":false},{"Id":88439,"Name":"beilagen& co","Products":[{"Id":14574876,"Name":"Pommes frites","Allergens":[],"SubAllergens0":[],"SubAllergens7":[],"Additives":[],"CustomTags":[],"Prices":[{"Id":57790,"InternalName":"Preis","Price":1.8,"LocalizablePrice":{"CurrencyCode":"EUR","Amount":180}}],"CoverUrls":[],"NutritionFacts":{"KCalPer100":181,"KJPer100":731,"FatsPer100":9.5,"SatsPer100":2.3,"CarbsPer100":20.6,"SugarPer100":0.2,"ProteinsPer100":2.3,"SaltPer100":0.4},"Infos":[],"LabelGroups":[],"IsSoldOut":false,"Quantity":1,"Ratings":{}}],"IsHidden":false},{"Id":86795,"Name":"v-like","Products":[{"Id":14729638,"Name":"Heckengäu I Linsen I Curry | Kokos | Ingwer | gebackene Süßkartoffel | Koriander","Allergens":[],"SubAllergens0":[],"SubAllergens7":[],"Additives":[],"CustomTags":[{"Id":6207,"Name":"vegetarisch","IconUrl":"https://files.qnips.com/releaseicons/icon8-vegatarisch_2023.05.10_06.58.43.png"}],"Prices":[{"Id":57790,"InternalName":"Preis","Price":4.5,"LocalizablePrice":{"CurrencyCode":"EUR","Amount":450}}],"CoverUrls":[],"NutritionFacts":{"KCalPer100":116,"KJPer100":484,"FatsPer100":3.2,"SatsPer100":0.5,"CarbsPer100":17.1,"SugarPer100":3.2,"ProteinsPer100":4.1,"SaltPer100":0.4},"Infos":[],"LabelGroups":[],"IsSoldOut":false,"Quantity":1,"Ratings":{}}],"IsHidden":false},{"Id":86796,"Name":"veggibar","Products":[{"Id":14402812,"Name":"Frisches Marktgemüse 100g =1,30€","Allergens":[8],"SubAllergens0":[],"SubAllergens7":[],"Additives":[],"CustomTags":[],"Prices":[],"CoverUrls":[],"NutritionFacts":{"KCalPer100":52,"KJPer100":217,"FatsPer100":3.2,"SatsPer100":0.3,"CarbsPer100":4.3,"SugarPer100":3.5,"ProteinsPer100":1.3,"SaltPer100":0.4},"Infos":[],"LabelGroups":[],"IsSoldOut":false,"Quantity":1,"Ratings":{}}],"IsHidden":false},{"Id":86797,"Name":"worldtour","Products":[{"Id":14729639,"Name":"Sojageschnetzeltes | Thai Yellow Curry Sauce | Wokgemüse | Duftreis","Allergens":[5],"SubAllergens0":[],"SubAllergens7":[],"Additives":[1],"CustomTags":[{"Id":1241,"Name":"vegan","IconUrl":"https://qnips.blob.core.windows.net/releaseicons/iconvegan20190923134836_2020.10.06_14.53.42.png"}],"Prices":[{"Id":57790,"InternalName":"Preis","Price":4.9,"LocalizablePrice":{"CurrencyCode":"EUR","Amount":490}}],"CoverUrls":[],"NutritionFacts":{"KCalPer100":120,"KJPer100":503,"FatsPer100":1.3,"SatsPer100":0.2,"CarbsPer100":14.5,"SugarPer100":2.8,"ProteinsPer100":10.6,"SaltPer100":0.7},"Infos":[],"LabelGroups":[],"IsSoldOut":false,"Quantity":1,"Ratings":{}}],"IsHidden":false},{"Id":86799,"Name":"dessertbar","Products":[{"Id":14405558,"Name":"Hausgemachter Schokoladenpudding","Allergens":[6],"SubAllergens0":[],"SubAllergens7":[],"Additives":[],"CustomTags":[],"Prices":[{"Id":57790,"InternalName":"Preis","Price":0.65,"LocalizablePrice":{"CurrencyCode":"EUR","Amount":65}}],"CoverUrls":[],"NutritionFacts":{"KCalPer100":115,"KJPer100":481,"FatsPer100":3.1,"SatsPer100":2,"CarbsPer100":18.5,"SugarPer100":11,"ProteinsPer100":2.9,"SaltPer100":0.2},"Infos":[],"LabelGroups":[],"IsSoldOut":false,"Quantity":1,"Ratings":{}}],"IsHidden":false},{"Id":87169,"Name":"salatgarten","Products":[{"Id":14689921,"Name":"Salatbar 100g = 1,30 €\\nRohkost I Hausgemachte Salate  I Topping I Dressing ","Allergens":[],"SubAllergens0":[],"SubAllergens7":[],"Additives":[],"CustomTags":[],"Prices":[],"CoverUrls":[],"WeightInGrams":0,"Infos":[],"LabelGroups":[],"IsSoldOut":false,"Quantity":1,"Ratings":{}},{"Id":14405547,"Name":"Beilagensalat","Allergens":[],"SubAllergens0":[],"SubAllergens7":[],"Additives":[],"CustomTags":[],"Prices":[{"Id":57790,"InternalName":"Preis","Price":0.7,"LocalizablePrice":{"CurrencyCode":"EUR","Amount":70}}],"CoverUrls":[],"NutritionFacts":{"KCalPer100":100,"KJPer100":420,"FatsPer100":10,"SatsPer100":1.2,"CarbsPer100":2.1,"SugarPer100":2,"ProteinsPer100":0.7,"SaltPer100":1},"Infos":[],"LabelGroups":[],"IsSoldOut":false,"Quantity":1,"Ratings":{}},{"Id":14405550,"Name":"Großer Salat Balkankäse I Oliven I Gurke I Tomate","Allergens":[6],"SubAllergens0":[],"SubAllergens7":[],"Additives":[5],"CustomTags":[{"Id":6207,"Name":"vegetarisch","IconUrl":"https://files.qnips.com/releaseicons/icon8-vegatarisch_2023.05.10_06.58.43.png"}],"Prices":[{"Id":57790,"InternalName":"Preis","Price":4.5,"LocalizablePrice":{"CurrencyCode":"EUR","Amount":450}}],"CoverUrls":[],"Infos":[],"LabelGroups":[],"IsSoldOut":false,"Quantity":1,"Ratings":{}},{"Id":14409560,"Name":"Großer Salat I Schinken I Käse","Allergens":[2,6],"SubAllergens0":[],"SubAllergens7":[],"Additives":[1,2,7],"CustomTags":[{"Id":1235,"Name":"mit Schwein","IconUrl":"https://cdn3.qnips.com/releaseicons/i008iconschwein_2021.09.08_12.13.51.jpg"}],"Prices":[{"Id":57790,"InternalName":"Preis","Price":6,"LocalizablePrice":{"CurrencyCode":"EUR","Amount":600}}],"CoverUrls":[],"Infos":[],"LabelGroups":[],"IsSoldOut":false,"Quantity":1,"Ratings":{}},{"Id":14405549,"Name":"Großer Salat I Thunfisch I Ei","Allergens":[2,3,8],"SubAllergens0":[],"SubAllergens7":[],"Additives":[],"CustomTags":[{"Id":4405,"Name":"mit Fisch","IconUrl":"https://qnips.blob.core.windows.net/releaseicons/fisch_2021.04.14_12.25.28.jpg"}],"Prices":[{"Id":57790,"InternalName":"Preis","Price":6.5,"LocalizablePrice":{"CurrencyCode":"EUR","Amount":650}}],"CoverUrls":[],"Infos":[],"LabelGroups":[],"IsSoldOut":false,"Quantity":1,"Ratings":{}}],"IsHidden":false}],"IsPhotoManagementAllowed":false,"MenuCardId":16413,"StoreId":28947,"TimeZoneId":"Europe/Berlin","Name":"Thales Management & Services","DisplayOptions":1118104,"ComponentDisplayOptions":0,"Type":0,"WeeksToPreview":2,"WeeksToReview":0,"WeekDays":[0,1,2,3,4],"NutritionLabels":[],"RatingLabels":[],"HasStock":false,"HasDayDocs":false,"HasProductSearch":false,"IsFavoriteProductsEnabled":false}'
    aramark_menu = get_aramark_menu()
    main_categories = get_main_categories(aramark_menu)
    main_pommes_categories = get_main_categories(aramark_menu)
    print(json.dumps(main_categories))
    print(json.dumps(main_pommes_categories))
    pommes_bool = get_pommes_bool(aramark_menu)
    print(pommes_bool)
    pommes_bool = get_pommes_bool(json.loads(test_pommes_menu))
    print(pommes_bool)


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
