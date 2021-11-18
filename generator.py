import random, time, itertools
import csv
from datetime import date, timedelta, datetime
from faker.factory import Factory
import calendar, pytz
from elasticsearch import Elasticsearch, helpers


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

Faker = Factory.create


def generate_hour(scope_date):
    if random.randint(1,100) < 75 :
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

    fake.seed(random.randint(1, 99999))

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
            profile["geoip"]["location"]["lon"] = random_row[5].split(',')[0]
            profile["geoip"]["location"]["lat"] = random_row[5].split(',')[1]

    return profile


def generate_order(gender, scope_date):
    order = {}

    order["day_of_week_i"] = scope_date.weekday()
    order["day_of_week"] = calendar.day_name[scope_date.weekday()]
    order["order_date"] = datetime.strftime(pytz.timezone("Europe/Paris").localize(scope_date, is_dst=True).astimezone(pytz.utc), "%Y-%m-%dT%H:%M:%S") + "+00:00"
    order["order_id"] = random.randint(100000, 999999)

    id_exists = True
    while id_exists:
        order_id = random.randint(10000, 99999)
        if order_id not in order_ids:
            id_exists = False
            order_ids.append(order_id)
    order["order_id"] = order_id

    order["products"] = []

    order["taxful_total_price"] = 0
    order["taxless_total_price"] = 0
    order["total_quantity"] = 0
    order["total_unique_products"] = 0

    order["sku"] = []

    order["type"] = "order"

    return order


generate_customers = True
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

    import csv

    keys = customers[0].keys()

    with open('data/customers.csv', 'w', newline='', encoding='utf-8') as output_file:
        dict_writer = csv.DictWriter(output_file, keys, delimiter=';')
        dict_writer.writeheader()
        dict_writer.writerows(customers)


current_date = date(2021, 12, 15)
from_date = date(2021, 8, 1)

generate_orders = False
if generate_orders:
    for i in range((current_date - from_date).days + 1):

        orders = []

        scope_date = from_date + timedelta(days=i)

        if scope_date.weekday() > 4:
            count_orders = random.randint(240,360)
        if scope_date.weekday() <= 4:
            count_orders = random.randint(60,120)

        male_count = int(count_orders * (random.randint(50, 60) / 100))
        female_count = count_orders - male_count

        for i in range(0, male_count):
            order = generate_order("H", generate_hour(scope_date))
            orders.append(order)
        for i in range(0, male_count):
            order = generate_order("F", generate_hour(scope_date))
            orders.append(order)

        upload = False
        if upload:
            es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

            res = helpers.bulk(
                es,
                orders,
                index="heptathlon",
            )
