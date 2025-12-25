import sdb_connector as sdb_conn
import time
import pandas as pd

#RUN_ID = "run_info:01JKG9806ABN68BXD7MW2Y8SPP"
RUN_ID = "run_info:01K6AXV99C0DF6KCA6V8GWFFMT"
#RUN_ID = "run_info:01JKG9D3G88RNH3V8E03DZ6CZW"
# PROJECT_ID = "project_info:01JKG94AKGTX28RSZC1Y17K4NJ"
IP = "192.168.2.67"

def main():
    start = time.time()
    result = sdb_conn.select_additional_info_data(IP, "8005", 
                "root", "root","main", "data", "amv_tag_49", RUN_ID, "additional_info.xlsx", 0)
    df = pd.DataFrame(result, columns=['run_counter', 'len_trigger', 'channel', 'peak', 'peak_positon', \
                                       'positon_over', 'positon_under', 'offset_after', 'offset_before', 'timestamp']).sort_values(by=['run_counter', 'channel'])
    print(df)
    end = time.time()
    print("Time taken result: ", end - start)
    
    start = time.time()
    result = sdb_conn.select_measurement_data(IP, "8005", 
                "root", "root","main", "data", "amv_tag_41", RUN_ID, "measurement.xlsx", 0)
    df = pd.DataFrame(result, columns=['run_counter', 'channel', 'integral', 'mass',"offset", "offset1", "offset2", "tolerance_bottom",\
                                       "tolerance_top", "timestamp", "status"]).sort_values(by=['run_counter', 'channel'])
    print(df)
    end = time.time()
    print("Time taken result: ", end - start)
    
    # start = time.time()
    # result = sdb_conn.select_raw_data(IP, "8005", 
    #             "root", "root","main", "data", "amv_raw_data", RUN_ID)
    # df = pd.DataFrame(result, columns=['run_counter', 'channel', 'data', 'datetime', 'duration']).sort_values(by=['run_counter', 'channel'])
    # df["run_id"] = RUN_ID
    # print(df)
    # end = time.time()
    # print("Time taken result: ", end - start)
    
    result = sdb_conn.select_ai_data(IP, "8005", 
                "root", "root","main", "data", "ai", RUN_ID, "", 0)
    df = pd.DataFrame(result, columns=['port', 'pin', 'timestamp', 'value', 'run_counter']).sort_values(by=['run_counter', 'port'])
    df["run_id"] = RUN_ID
    print(df)

    result = sdb_conn.select_di_data(IP, "8005", 
                "root", "root","main", "data", "di", RUN_ID, "", 0)
    df = pd.DataFrame(result, columns=['port', 'pin', 'timestamp', 'value', 'run_counter']).sort_values(by=['run_counter', 'port'])
    df["run_id"] = RUN_ID
    print(df)

if __name__ == "__main__":
    main()