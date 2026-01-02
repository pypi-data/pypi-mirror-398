import requests


class Requests(object):
    def __init__(self, config_data):
        self.config_data = config_data

    def patch_request(
        self, url, patch_content_type, kwargs, add_metadata=False, sl_metadata=None
    ):
        kwargs.update({"verify": False, "timeout": 120})
        if self.config_data.proxy:
            kwargs["proxies"] = {
                "http": self.config_data.proxy,
                "https": self.config_data.proxy,
            }
        headers = kwargs.setdefault("headers", {})
        if patch_content_type:
            headers["Content-Type"] = "application/json"
        headers["Authorization"] = "Bearer %s" % self.config_data.token
        if add_metadata:
            headers["x-sl-appname"] = self.config_data.appName
            headers["x-sl-branchname"] = self.config_data.branchName
            headers["x-sl-buildname"] = self.config_data.buildName
            headers["x-sl-bsid"] = self.config_data.buildSessionId
            headers["x-sl-messagetype"] = "1003"
            if self.config_data.labId:
                headers["x-sl-labid"] = self.config_data.labId
        if sl_metadata:
            headers["X-SL-METADATA"] = sl_metadata.to_json()
        if self.config_data.testProjectId:
            headers["x-sl-testprojectid"] = self.config_data.testProjectId
        if (url is not None) and (
            url.lower().startswith("http://") or url.lower().startswith("https://")
        ):
            return url
        return self.config_data.server + url

    def get(
        self,
        url,
        params=None,
        patch_content_type=True,
        add_metadata=False,
        sl_metadata=None,
        **kwargs,
    ):
        url = self.patch_request(
            url, patch_content_type, kwargs, add_metadata, sl_metadata
        )
        return requests.get(url, params=params, **kwargs)

    def post(
        self,
        url,
        data=None,
        json=None,
        patch_content_type=True,
        add_metadata=False,
        sl_metadata=None,
        **kwargs,
    ):
        url = self.patch_request(
            url, patch_content_type, kwargs, add_metadata, sl_metadata
        )
        return requests.post(url, data=data, json=json, **kwargs)

    def put(
        self,
        url,
        data=None,
        patch_content_type=True,
        add_metadata=False,
        sl_metadata=None,
        **kwargs,
    ):
        url = self.patch_request(
            url, patch_content_type, kwargs, add_metadata, sl_metadata
        )
        return requests.put(url, data=data, **kwargs)

    def patch(
        self,
        url,
        data=None,
        patch_content_type=True,
        add_metadata=False,
        sl_metadata=None,
        **kwargs,
    ):
        url = self.patch_request(
            url, patch_content_type, kwargs, add_metadata, sl_metadata
        )
        return requests.patch(url, data=data, **kwargs)

    def delete(
        self,
        url,
        patch_content_type=True,
        add_metadata=False,
        sl_metadata=None,
        **kwargs,
    ):
        url = self.patch_request(
            url, patch_content_type, kwargs, add_metadata, sl_metadata
        )
        return requests.delete(url, **kwargs)
