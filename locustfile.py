from locust import TaskSet, task, HttpLocust


class UserBehavior(TaskSet):
    def on_start(self):  # 当模拟用户开始执行TaskSet类的时候，on_start方法会被调用
        self.index = 0

    @task
    def test_visit(self):
        url = self.locust.share_data[
            self.index]  # 取 self.locust.share_data<等于 WebsiteUser 类定义的 share_data >中的第self.index 个元素
        self.index = (self.index + 1) % len(
            self.locust.share_data)  # self.index 的值小于 self.locust.share_data 的长度，循环生成 <0.1.2.3.4、0.1.2.3.4...>
        r = self.client.get(url)  # TaskSet类有一个client属性，返回self.locust.client
        assert r.status_code == 200


class WebsiteUser(HttpLocust):
    host = 'http://debugtalk.com'
    task_set = UserBehavior
    share_data = ['/', '/archives/', '/about/', '/archives/2018/05/', '/archives/2018/02/']  # 共享数据，循环遍历使用
    min_wait = 1000
    max_wait = 3000
