import sdb_connector as sdb_conn
import time
import pandas as pd

def main():
    start = time.time()
    result = sdb_conn.select_additional_info_data("192.168.2.63", "8000", 
                "root", "root","main", "data", "amv_tag_49", "run_info:01J4XRFVTY9XSBCECW2NHWHMGK")
    df = pd.DataFrame(result, columns=['Column1', 'Column2', 'Column3', 'Column4'])
    print(df)
    end = time.time()
    print("Time taken result: ", end - start)

    start = time.time()
    result = sdb_conn.select_measurement_data("192.168.2.63", "8000", 
                "root", "root","main", "data", "amv_tag_41", "run_info:01J4XRFVTY9XSBCECW2NHWHMGK")
    df = pd.DataFrame(result, columns=['Column1', 'Column2', 'Column3'])
    print(df)
    end = time.time()
    print("Time taken result: ", end - start)

    start = time.time()
    result = sdb_conn.select_raw_data("192.168.2.63", "8000", 
                "root", "root","main", "data", "amv_raw_data", "run_info:01J4T6N37WD0SBGG09CY26EX8Y")
    df = pd.DataFrame(result, columns=['Column1', 'Column2', 'Column3'])
    print(df)
    end = time.time()
    print("Time taken result: ", end - start)


if __name__ == "__main__":
    main()