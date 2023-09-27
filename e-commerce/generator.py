import random, itertools
from datetime import date, timedelta, datetime
from faker import Faker
import calendar, pytz
from elasticsearch import Elasticsearch, helpers
import csv

normalMap = {'À': 'A', 'Á': 'A', 'Â': 'A', 'Ã': 'A', 'Ä': 'A',
             'à': 'a', 'á': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a', 'ª': 'A',
             'È': 'E', 'É': 'E', 'Ê': 'E', 'Ë': 'E',
             'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e',
             'Í': 'I', 'Ì': 'I', 'Î': 'I', 'Ï': 'I',
             'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
             'Ò': 'O', 'Ó': 'O', 'Ô': 'O', 'Õ': 'O', 'Ö': 'O',
             'ò': 'o', 'ó': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o', 'º': 'O',
             'Ù': 'U', 'Ú': 'U', 'Û': 'U', 'Ü': 'U',
             'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u',
             'Ñ': 'N', 'ñ': 'n',
             'Ç': 'C', 'ç': 'c',
             '§': 'S',  '³': '3', '²': '2', '¹': '1'}
normalize = str.maketrans(normalMap)

customer_ids = []
order_ids = []
order_ids = []
sku_ids = []

fake = Faker()

def generate_hour(scope_date):
    if random.randint(1,100) < 76 :
        if random.randint(1, 100) < 66:
            hrs = random.randint(18, 20)
        else:
            hrs = random.randint(10, 18)
    else:
        nums = list(itertools.chain(
            range(0, 9),
            range(21, 23)))
        hrs = random.choices(nums, k=1)[0]
    mins = random.randint(0, 59)
    secs = random.randint(0, 59)

    scope_date = datetime(scope_date.year, scope_date.month, scope_date.day, hrs, mins, secs)

    return scope_date

def generate_profile(gender, country):

    if country == 'FR':
        fake = Faker('fr_FR')

    Faker.seed(random.randint(1, 99999))

    profile = {}
    profile["geoip"] = {}
    profile["geoip"]["country_iso_code"] = "FR"
    profile["currency"] = "EUR"

    id_exists = True
    while id_exists:
        customer_id = random.randint(10000, 99999)
        if customer_id not in customer_ids:
            id_exists = False
            customer_ids.append(customer_id)
    profile["customer_id"] = customer_id

    profile["customer_gender"] = gender
    profile["customer_phone"] = fake.phone_number()
    if gender == "M":
        profile["customer_name"] = fake.name_male()
    else:
        profile["customer_name"] = fake.name_female()
    profile["customer_email"] = profile["customer_name"].split()[-1].lower().translate(normalize) + str(random.randint(10,99)) + "@" + fake.free_email_domain()

    if country == 'FR':

        with open('data/french_cities.csv') as f:
            reader = csv.reader(f, delimiter=';')

            reader_list = list(reader)
            has_coordinates = False
            while not has_coordinates:

                random_row = reader_list[random.randint(0,39191)]

                if random_row[5] != "":
                    has_coordinates = True

            profile["geoip"]["city_name"] = random_row[1]
            profile["geoip"]["zip_code"] = random_row[2]
            profile["geoip"]["location"] = {}
            profile["geoip"]["location"]["lat"] = random_row[5].split(',')[0]
            profile["geoip"]["location"]["lon"] = random_row[5].split(',')[1]

    return profile


def generate_order(gender, scope_date):
    order = {}

    order["day_of_week_i"] = scope_date.weekday()
    order["day_of_week"] = calendar.day_name[scope_date.weekday()]
    order["order_date"] = datetime.strftime(pytz.timezone("Europe/Paris").localize(scope_date, is_dst=True).astimezone(pytz.utc), "%Y-%m-%dT%H:%M:%S") + "+00:00"

    id_exists = True
    while id_exists:
        order_id = random.randint(10000, 99999)
        if order_id not in order_ids:
            id_exists = False
            order_ids.append(order_id)
    order["order_id"] = order_id

    order["products"] = generate_products(gender, scope_date)

    order["taxful_total_price"] = 0
    order["taxless_total_price"] = 0
    order["total_quantity"] = 0
    order["total_unique_products"] = 0

    order["sku"] = []
    order["manufacturer"] = []
    order["categories"] = []

    for product in order["products"]:
        order["taxful_total_price"] += product["taxful_price"] * product["quantity"]
        order["taxless_total_price"] += product["taxless_price"] * product["quantity"]
        order["total_quantity"] += product["quantity"]
        order["total_unique_products"] += 1
        order["sku"].append(product["sku"])
        order["manufacturer"].append(product["manufacturer"])
        order["categories"].append(product["main_category"])

    order["taxless_total_price"] = float("{0:.2f}".format(order["taxless_total_price"]))
    order["taxful_total_price"] = float("{0:.2f}".format(order["taxless_total_price"]))

    order["type"] = "order"

    return order


def generate_products(gender, scope_date):

    products = []

    tmp = random.randint(1, 100)
    if tmp < 74:
        items_count = random.randint(1,3)
    else:
        items_count = random.randint(3,5)

    import json

    with open('data/items_decathlon.fr-2021-11-18T02_47_18.726000.json') as f:
        data = json.load(f)

        for i in range(0, items_count):

            product_is_ok = False
            while not product_is_ok:
                try:

                    item = data[random.randint(0,8900)]
                    product = {}


                    if 'regularPrice' in item["offers"][0]:
                        product["base_price"] = float("{0:.2f}".format(float(item["offers"][0]["regularPrice"])))
                        product["discount_percentage"] = float("{0:.2f}".format(1 - (( float(item["offers"][0]["price"]) * 100 / float(item["offers"][0]["regularPrice"]) / 100 ))))
                    else:
                        product["base_price"] = float("{0:.2f}".format(float(item["offers"][0]["price"])))
                        product["discount_percentage"] = 0.0

                    tmp = random.randint(1,100)
                    if tmp > 72 and float(item["offers"][0]["price"]) < 30:
                        product["quantity"] = random.randint(2,3)
                    else:
                        product["quantity"] = 1
                    if "brand" in item:
                        product["manufacturer"] = item["brand"]
                    else:
                        product["manufacturer"] = -1
                    product["tax_amount"] = float("{0:.2f}".format((float(item["offers"][0]["price"]) * 0.8) * 0.2))

                    product["main_category"] = item["breadcrumbs"][2]["name"]
                    product["categories"] = []

                    for j in item["breadcrumbs"]:
                        if j["name"] != "Accueil" and j["name"] != "Tous les sports" and j["name"] != "Decathlon":
                            product["categories"].append(j["name"])

                    if "sku" in item:
                        product["sku"] = item['sku']
                    else:
                        id_exists = True
                        while id_exists:
                            sku_id = random.randint(10000, 99999)
                            if sku_id not in sku_ids:
                                id_exists = False
                                product["sku"] = sku_id
                                product["product_id"] = sku_id
                                sku_ids.append(sku_id)

                    product["taxless_price"] = float("{0:.2f}".format(float(item["offers"][0]["price"]) * 0.8))

                    if 'regularPrice' in item["offers"][0]:
                        product["discount_amount"] = float("{0:.2f}".format(float(item["offers"][0]["regularPrice"]) - float(item["offers"][0]["price"])))
                    else:
                        product["discount_amount"] = 0

                    product["product_name"] = item['name']
                    product["price"] = float("{0:.2f}".format(float(item["offers"][0]["price"])))
                    product["taxful_price"] = float("{0:.2f}".format(float(item["offers"][0]["price"])))

                    if scope_date.month < 11:
                        if any("ski" in s.lower() for s in product["categories"]):
                            if random.randint(0,100) < 80:
                                product_is_ok = False

                    if scope_date.month < 11:
                        if any("gants" in s.lower() for s in product["categories"]):
                            if random.randint(0,100) < 60:
                                product_is_ok = False

                    product_is_ok = True

                except Exception as e:
                    print(e)
                    pass

            products.append(product)


    return products



generate_customers = False
if generate_customers:
    # count = random.randint(19000,21000)
    count = 20
    male_count = int(count * (random.randint(55,67)/10))
    female_count = count - male_count

    customers = []

    for i in range(1, male_count):
        customers.append(generate_profile('M', 'FR'))
    for i in range(1, female_count):
        customers.append(generate_profile('F', 'FR'))

    keys = customers[0].keys()

    import json

    with open('data/customers.json', 'w', encoding='utf-8') as f:
        json.dump(customers, f, ensure_ascii=False, indent=4)


current_date = date(2023, 2, 7)
from_date = date(2022, 11, 7)

generate_orders = True
if generate_orders:

    orders = []

    for i in range((current_date - from_date).days + 1):

        scope_date = from_date + timedelta(days=i)

        if scope_date.weekday() > 4:
            count_orders = random.randint(127,172)
            #count_orders = random.randint(10, 20)
        if scope_date.weekday() <= 4:
            count_orders = random.randint(58,87)
            #count_orders = random.randint(5, 10)

        male_count = int(count_orders * (random.randint(52, 62) / 100))
        female_count = count_orders - male_count

        for i in range(0, male_count):
            order = generate_order("H", generate_hour(scope_date))
            order.update(generate_profile("M", "FR"))
            orders.append(order)
        for i in range(0, female_count):
            order = generate_order("F", generate_hour(scope_date))
            order.update(generate_profile("F", "FR"))
            orders.append(order)

        print(order)

    upload = False
    if upload:
        es = Elasticsearch(hosts="http://elastic:changeme@localhost:9200/")

        res = helpers.bulk(
            es,
            orders,
            index="decathlon",
        )