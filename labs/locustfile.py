import os

from locust import HttpUser, between, task


BMC_USER = os.getenv("BMC_USER", "root")
BMC_PASSWORD = os.getenv("BMC_PASSWORD", "0penBmc")


class OpenBMCRedfishUser(HttpUser):
    host = os.getenv("BMC_URL", "https://127.0.0.1:2443")
    wait_time = between(1, 3)

    def on_start(self):
        self.client.verify = False
        self.client.auth = (BMC_USER, BMC_PASSWORD)

    @task(3)
    def get_system_information(self):
        self.client.get("/redfish/v1/Systems/system", name="OpenBMC /Systems/system")

    @task(2)
    def get_redfish_root(self):
        self.client.get("/redfish/v1/", name="OpenBMC /redfish/v1")

    @task(1)
    def request_power_state(self):
        self.client.get("/redfish/v1/Systems/system", name="OpenBMC PowerState")


class PublicApiUser(HttpUser):
    host = "https://jsonplaceholder.typicode.com"
    wait_time = between(1, 2)

    @task(3)
    def posts(self):
        self.client.get("/posts", name="JSONPlaceholder /posts")

    @task(1)
    def single_post(self):
        self.client.get("/posts/1", name="JSONPlaceholder /posts/1")
