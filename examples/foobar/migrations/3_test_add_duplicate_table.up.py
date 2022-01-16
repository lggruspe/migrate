USER_VERSION = 3


def main(m):
    m.execute("CREATE TABLE Data (key)")
    m.execute("CREATE TABLE ThisShouldntExist (key)")
