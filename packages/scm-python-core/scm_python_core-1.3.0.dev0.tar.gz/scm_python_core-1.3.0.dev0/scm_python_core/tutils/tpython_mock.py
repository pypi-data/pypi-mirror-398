import random, string, datetime


def get_random_value_by_java_datatype(java_datatype: str):
    if "int" == java_datatype:
        return random.randint(1, 100)
    if "long" == java_datatype:
        return random.randint(1, 100)
    if "boolean" == java_datatype:
        return random.choice([True, False])
    if "String" == java_datatype:
        return "".join(random.choice(string.ascii_letters) for _ in range(8))
    if java_datatype == "float":
        return random.uniform(1.0, 100.0)
    if java_datatype == "double":
        return random.uniform(1.0, 100.0)
    if java_datatype == "Date":
        return datetime.date.today()
    if java_datatype == "LocalTime":
        return datetime.date.today()
