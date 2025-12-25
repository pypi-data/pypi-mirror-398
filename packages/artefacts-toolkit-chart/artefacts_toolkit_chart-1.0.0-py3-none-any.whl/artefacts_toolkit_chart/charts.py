import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
import csv
from typing import Union

from pathlib import Path

from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

from artefacts_toolkit_utilities.utils import _extract_attribute_data


def _split_topic_name_and_attributes(topic):
    """Split a topic string into name and attributes parts.

    For 'time' special case, returns ('time', '').
    For regular topics like 'topic.attribute1.attribute2',
    returns ('topic', 'attribute1.attribute2').
    """
    if topic.lower() == "time":
        return "time", ""
    else:
        return topic.split(".", 1)


def _append_axis_data(
    axis_data, axis_topics, rosbag_connection_topic, rosbag_msg, timestamp, is_time_axis
):
    # append new entry into axis_data based on current ROSbag connection topic
    for topic in axis_topics:
        topic_name, topic_attributes = _split_topic_name_and_attributes(topic)

        if rosbag_connection_topic == topic_name:
            if is_time_axis:
                axis_data[topic_name].append(timestamp)
            else:
                axis_data[topic_name].append(
                    _extract_attribute_data(rosbag_msg, topic_attributes)
                )

    return axis_data


def _plot_data(x_data, y_data, x_title, y_title, output_filepath, chart_name):
    title = chart_name

    fig = go.Figure()

    # assign labels for axes
    x_axis_label = x_title
    y_axis_label = y_title

    # handling multiple topics
    if x_data.dtype == np.dtype("O") and y_data.dtype == np.dtype("O"):
        x_data = x_data.item()
        y_data = y_data.item()

        for k in x_data.keys():
            legend = k
            fig.add_trace(
                go.Scatter(
                    x=x_data[k], y=y_data[k], mode="lines+markers", name=f"{legend}"
                )
            )

    # handling single topic
    else:
        legend = x_title.split(".")[0]

        fig.add_trace(
            go.Scatter(x=x_data, y=y_data, mode="lines+markers", name=f"{legend}")
        )

    fig.update_layout(
        title=title,
        xaxis_title=x_axis_label,
        yaxis_title=y_axis_label,
    )

    pio.write_html(fig, file=output_filepath, auto_open=False)


def _save_as_csv(x_data, y_data, x_title, y_title, output_filepath):
    with open(output_filepath, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        # Write header row
        writer.writerow([x_title, y_title])
        # Write data rows
        for x, y in zip(x_data, y_data):
            writer.writerow([x, y])


"""
Makes a chart based on provided topics (x, y) where each topic is a string with the format
"topic.attribute1.attribute2...". Attributes are split by "." Any depth of attributes can be used.
If the attribute is a list, the index can be specified in square brackets (e.g., "topic.attribute[0]").
If one of the topics is time, the other topic will be plotted against its timestamps.
"""


def _make_rosbag_chart(
    filepath,
    topic_x,
    topic_y,
    axis_x_name,
    axis_y_name,
    field_unit,
    output_dir,
    chart_name,
    output_format="html",
):
    try:
        typestore = get_typestore(Stores.LATEST)
        initial_timestamp = None

        if isinstance(topic_x, list) or isinstance(topic_y, list):
            # ensure each axis has a list of topics (topics_x, topics_y), even though one axis can be "time" -> for code minimalism
            #   - if topics-vs-topics -> as intended
            #   - if topics-vs-time -> ensure "time" axis has an abstract list to correspond to each item in the other "topics" axis (both axes have same topics)
            topics_x = (
                topic_y
                if (isinstance(topic_x, str) and topic_x.lower() == "time")
                else topic_x
            )
            topics_y = (
                topic_x
                if (isinstance(topic_y, str) and topic_y.lower() == "time")
                else topic_y
            )

            x_data = {topic.split(".", 1)[0]: [] for topic in topics_x}
            y_data = {topic.split(".", 1)[0]: [] for topic in topics_y}

        else:
            x_data = []
            y_data = []

            axis_x_name = f"{topic_x} ({field_unit})" if field_unit else topic_x
            axis_y_name = f"{topic_y} ({field_unit})" if field_unit else topic_y

            # Override plot names if one of the topics is time
            topic_x_name, topic_x_attributes = _split_topic_name_and_attributes(topic_x)
            topic_y_name, topic_y_attributes = _split_topic_name_and_attributes(topic_y)

            # If the topic is time, set the plot name to "Time (s)"
            if topic_x_name == "time":
                axis_x_name = "Time (s)"
            if topic_y_name == "time":
                axis_y_name = "Time (s)"

        with Reader(filepath) as reader:
            for connection, timestamp, rawdata in reader.messages():
                msg = typestore.deserialize_cdr(rawdata, connection.msgtype)

                # Use the rosbag2 timestamp (epoch) if no header
                if not hasattr(msg, "header"):
                    msg_timestamp = timestamp / 1e9  # nanoseconds to seconds
                    if initial_timestamp is None:
                        initial_timestamp = msg_timestamp
                    normalized_timestamp = msg_timestamp - initial_timestamp

                else:
                    normalized_timestamp = (
                        msg.header.stamp.sec + msg.header.stamp.nanosec / 1e9
                    )

                # If only one actual topic is provided, use that topic's timestamps or rosbag time

                if isinstance(topic_x, list) or isinstance(topic_y, list):
                    # handling multiple topics
                    x_data = _append_axis_data(
                        x_data,
                        topics_x,
                        connection.topic,
                        msg,
                        normalized_timestamp,
                        topic_x == "time",
                    )

                    y_data = _append_axis_data(
                        y_data,
                        topics_y,
                        connection.topic,
                        msg,
                        normalized_timestamp,
                        topic_y == "time",
                    )

                else:
                    # handling single topic
                    if topic_x_name == "time" and connection.topic == topic_y_name:
                        x_data.append(normalized_timestamp)
                    elif connection.topic == topic_x_name:
                        x_data.append(_extract_attribute_data(msg, topic_x_attributes))
                    if topic_y_name == "time" and connection.topic == topic_x_name:
                        y_data.append(normalized_timestamp)
                    elif connection.topic == topic_y_name:
                        y_data.append(_extract_attribute_data(msg, topic_y_attributes))

        x_data = np.array(x_data)
        y_data = np.array(y_data)

        if output_format.lower() == "html":
            output_filepath = f"{output_dir}/{chart_name}.html"

            _plot_data(
                x_data, y_data, axis_x_name, axis_y_name, output_filepath, chart_name
            )

        elif output_format.lower() == "csv":
            output_filepath = f"{output_dir}/{chart_name}.csv"
            _save_as_csv(x_data, y_data, axis_x_name, axis_y_name, output_filepath)

    except Exception as e:
        print(f"ERROR: Unable to create chart for {chart_name}. {e}")


def make_chart(
    filepath,
    topic_x: Union[str, list],
    topic_y: Union[str, list],
    axis_x_name="",
    axis_y_name="",
    field_unit=None,
    output_dir="output",
    chart_name="chart",
    file_type="rosbag",
    output_format="html",
):
    """
    Note: axis_x_name, axis_y_name can be provided for complex multiple plots case. If not, such as in single plot case, the axis name can still be generated
    """

    supported_formats = ["html", "csv"]
    supported_file_types = ["rosbag"]

    if output_format.lower() not in supported_formats:
        raise ValueError(
            f"Unsupported output format '{output_format}'. Supported formats are: {supported_formats}"
        )
    if file_type not in supported_file_types:
        raise NotImplementedError(
            "At present, charts can only be created from rosbags."
        )
    if (
        isinstance(topic_x, list) and isinstance(topic_y, str) and topic_y != "time"
    ) or (isinstance(topic_y, list) and isinstance(topic_x, str) and topic_x != "time"):
        raise NotImplementedError(
            "At present, the multi-plot feature for 1 axis can support only topics-vs-time, please make sure the other single-topic axis is 'time'."
        )

    try:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        # Clean up
        extensions = [".html", ".csv"]
        for ext in extensions:
            for p in Path(output_dir).glob(f"{chart_name}{ext}"):
                p.unlink()
    except Exception as e:
        print(e)

    if file_type == "rosbag":
        _make_rosbag_chart(
            filepath,
            topic_x,
            topic_y,
            axis_x_name,
            axis_y_name,
            field_unit,
            output_dir,
            chart_name,
            output_format,
        )
