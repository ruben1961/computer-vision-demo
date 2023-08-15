import quixstreams as qx
import os
import pandas as pd
import time
from io import StringIO
import datetime


client = qx.QuixStreamingClient()

topic_consumer = client.get_topic_consumer(os.environ["input"], consumer_group = "empty-transformation")
topic_producer = client.get_topic_producer(os.environ["output"])

pd.set_option('display.max_columns', None)

window_data = {}
stream_vehicles = {}

start_of_window = None
end_of_window = None
window_length_days = 2

def update_window():
    global end_of_window
    global start_of_window

    end_of_window = datetime.datetime.utcnow()
    start_of_window = end_of_window - datetime.timedelta(days = 2)


def ts_to_date(ts):
    sec = ts / 1_000_000_000
    dt = datetime.datetime.utcfromtimestamp(sec)
    #print(dt)
    return dt


def process_data(stream_id, new_data_frame):
    global window_data

    #for new_data_frame in incoming_dataframes:
    update_window()
    for i, row in new_data_frame.iterrows():
        # convert the nanosecond timestamp to a datetime
        check_date = ts_to_date(row["timestamp"])

        # add to the dictionary if the new data is inside the window.
        # it should be.
        if start_of_window <= check_date <= end_of_window:
            # add to dict
            window_data[check_date] = row

    # remove any data outside the new start and end window values
    window_data_inside = {key: value for key, value in window_data.items() if start_of_window <= key <= end_of_window}
    #print(window_data_inside)
    window_data = window_data_inside

    # Find the highest number of vehicles across all DataFrames
    highest_vehicles = float('-inf')  # Initialize with negative infinity

    for key, df in window_data_inside.items():
        if 'car' in df: #remove if when using 'vehicles'
            max_vehicles_in_df = df['car']
            highest_vehicles = max(highest_vehicles, max_vehicles_in_df)
            print(df['car'])

    print("Highest Number of Vehicles:", highest_vehicles)
    #if stream_id in stream_vehicles:
    stream_vehicles[stream_id] = highest_vehicles

    print(stream_vehicles)
    #else:
    #    stream_vehicles[stream_id] 


def on_dataframe_received_handler(stream_consumer: qx.StreamConsumer, df: pd.DataFrame):
    print(stream_consumer.stream_id)
    #if stream_consumer.stream_id == "JamCams_00001.01404":
    #    print("HERE!")
    
    update_window()
    process_data(stream_consumer.stream_id, df)


def on_stream_received_handler(stream_consumer: qx.StreamConsumer):
    stream_consumer.timeseries.on_dataframe_received = on_dataframe_received_handler


# subscribe to new streams being received
topic_consumer.on_stream_received = on_stream_received_handler

print("Listening to streams. Press CTRL-C to exit.")

# Handle termination signals and provide a graceful exit
qx.App.run()