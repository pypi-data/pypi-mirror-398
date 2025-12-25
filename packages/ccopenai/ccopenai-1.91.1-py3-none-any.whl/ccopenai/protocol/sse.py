# Copyright 2024 Ant Group Co., Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License"),
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


class SSEFormat:
    """
    Parse sse format.
    Format is event: {event_type}{separator}data: {data}

    For example:
    if event_type=message and separator=\r\n,
        format is event: message\r\ndata: {data}
    if event_type=error and separator=\r\n,
        format is event: error\r\ndata: {data}

    """

    def __init__(
        self,
        error_type: str = "error",
        message_type: str = "message",
        separator: str = "\r\n",
    ):
        self.error_type = error_type
        self.message_type = message_type
        self.separator = separator

    def check_format(self, event: str):
        """
        check whether the format of sse is valid
        """
        if not event:
            return False
        parts = event.split(self.separator, 1)
        # check format
        if len(parts) != 2:
            return False
        # check event_type
        if not parts[0] or not parts[0].startswith("event:"):
            return False
        event_type = parts[0].split(":", 1)[1].strip()
        if event_type not in [self.error_type, self.message_type]:
            return False
        # check data
        if not parts[1] or not parts[1].startswith("data:"):
            return False

        return True

    def check_error(self, event: str):
        """
        check whether the sse is error
        """
        parts = event.split(self.separator, 1)
        return parts[0].split(":", 1)[1].strip() == self.error_type

    def get_message(self, event: str):
        event_data = event.split(self.separator, 1)[1]
        return event_data.split("data:", 1)[1]
