"""
Tencent is pleased to support the open source community by making 蓝鲸智云 - PaaS平台 (BlueKing - PaaS System) available.
Copyright (C) 2022 THL A29 Limited, a Tencent company. All rights reserved.
Licensed under the MIT License (the "License"); you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://opensource.org/licenses/MIT
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
"""


class BkflowSDKException(Exception):
    CODE = None
    MESSAGE = None
    STATUS_CODE = 500

    def __init__(self, message="", errors=""):
        if message:
            self.MESSAGE = message
        if self.MESSAGE and errors:
            self.message = f"{self.MESSAGE}: {errors}"
        elif self.MESSAGE:
            self.message = self.MESSAGE
        else:
            self.message = f"{errors}"

    def __str__(self):
        return self.message


class APIException(BkflowSDKException):
    """Exception for API"""

    def __init__(self, errors, resp=None, url=""):
        self.url = url
        self.error_message = errors
        self.resp = resp

        if self.resp is not None:
            errors = "%s, resp=%s" % (errors, self.resp.text)
        super(APIException, self).__init__(errors)


class ValidationError(BkflowSDKException):
    pass
