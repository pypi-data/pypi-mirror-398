import difflib
import json

import datamazing.pandas as pdz
from azure.servicebus import ServiceBusMessage

from warpzone.blobstorage.client import BlobData
from warpzone.servicebus.data.client import DataMessage
from warpzone.servicebus.events.client import EventMessage


def assert_event_msg_similar(
    left: EventMessage,
    right: EventMessage,
    check_message_id: bool = False,
):
    """
    Assert if two event messages are similar, meaning equal
    - event
    - subject
    - message id [optional]
    """
    assert (
        left.event == right.event
    ), f"Events are different: {left.event} != {right.event}"
    assert (
        left.subject == right.subject
    ), f"Subjects are different: {left.subject} != {right.subject}"
    if check_message_id:
        assert (
            left.message_id == right.message_id
        ), f"Message ids are different: {left.message_id} != {right.message_id}"


def assert_data_msg_similar(
    left: DataMessage,
    right: DataMessage,
    check_message_id: bool = False,
):
    """
    Assert if two data messages are similar, meaning equal
    - content
    - subject
    - message id [optional]
    """
    assert (
        left.subject == right.subject
    ), f"Subjects are different: {left.subject} != {right.subject}"
    assert (
        left.extension == right.extension
    ), f"Extensions are different: {left.extension} != {right.extension}"
    if check_message_id:
        assert (
            left.message_id == right.message_id
        ), f"Message ids are different: {left.message_id} != {right.message_id}"

    if left.extension == "parquet":
        # for parquet files, check if the resulting pandas DataFrames are equal
        left_pandas, right_pandas = left.to_pandas(), right.to_pandas()
        pdz.testing.assert_frame_equal(
            left=left_pandas,
            right=right_pandas,
        )
    elif left.extension == "json":
        # for json files, check if the parsed data is equal
        left_json, right_json = json.loads(left.content), json.loads(right.content)
        assert (
            left_json == right_json
        ), f"JSON is different: {left_json} != {right_json}"
    elif left.extension in ["xml", "csv"]:
        # For human readable files,
        # use difflib to check if the files are equal
        diffs = list(
            difflib.unified_diff(
                left.content.decode().splitlines(),
                right.content.decode().splitlines(),
            )
        )
        assert len(diffs) == 0, "Files are different:\n" + "\n".join(diffs)
    else:
        # for binary files, check if the bytes are equal
        assert (
            left.content == right.content
        ), f"Content is different: {left.content} != {right.content}"


def assert_blob_data_similar(
    left: BlobData,
    right: BlobData,
):
    """
    Assert if two blob data are similar, meaning equal
    - content
    - name
    - metadata [optional]
    """
    assert (
        left.content == right.content
    ), f"Contents are different: {left.content} != {right.content}"
    assert (
        left.name == right.name
    ), f"Blob names are different: {left.name} != {right.name}"
    assert (
        left.metadata == right.metadata
    ), f"Metadatas are different: {left.metadata} != {right.metadata}"


def assert_func_msg_similar(
    left: ServiceBusMessage,
    right: ServiceBusMessage,
    check_message_id: bool = False,
):
    """
    Assert if two service bus messages are similar, meaning equal
    - content
    - subject
    - message_id [optional]
    """
    assert (
        list(left.body)[0] == list(right.body)[0]
    ), f"Body is different: {left.body} != {right.body}"
    assert (
        left.subject == right.subject
    ), f"Subject is different: {left.subject} != {right.subject}"
    if check_message_id:
        assert (
            left.message_id == right.message_id
        ), f"Message ids are different: {left.message_id} != {right.message_id}"
