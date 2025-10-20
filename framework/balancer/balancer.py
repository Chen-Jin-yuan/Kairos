import json
import requests
import threading
import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import asyncio
import uvicorn

from framework.logger import FileLogger
from framework.utils import ThreadSafeDeque
from .balancer_setting import PRIORITY_TABLE, PREDICT_TIME_TABLE
from .metrics import MetricsManager
from .memory_perceptor import MemoryPerceptorManager
from .token_counter import TokenCounter

is_queue = False
class LoadBalancerServer:
    def __init__(self, node_name, llm_urls, agents_use_model, host="0.0.0.0", port=8080, root_path=None, mode="balancing"):
        self.node_name = node_name
        self.llm_urls = llm_urls
        self.agents_use_model = agents_use_model
        self.host = host
        self.port = port
        self.root_path = root_path
        self.mode = mode
        self.total_waiting_time = 0
        self.waiting_time_lock = threading.Lock()
        assert mode == "balancing"

        self.current_normal_url_indexes = {model: 0 for model in self.llm_urls}

        self.app = FastAPI()
        self._setup_routes()
        self.lock = threading.Lock()

        self.logger = FileLogger(f"logs/balancer.log")
        self.logger.log(f"balancer '{self.node_name}' initialized with mode '{mode}'")
        self.logger.log(f"llm_urls_info {self.llm_urls}")
        self.logger.log(f"agents_use_model {self.agents_use_model}")

        # init MetricsManager
        url_list = []
        for sub_dict in self.llm_urls.values():
            for urls in sub_dict.values():
                url_list.extend(urls)

        self.metrics_manager = MetricsManager(url_list)
        self.logger.log(f"init MetricsManager with llm urls: {url_list}")

        self.memory_predictor_manager = MemoryPerceptorManager(self.metrics_manager)
        self.logger.log(f"init MemoryPerceptorManager with llm urls: {url_list}")

        self.token_counter = TokenCounter(agents_use_model)
        self.logger.log(f"init TokenCounter")

        self.waiting = ThreadSafeDeque()
        self.event_lock = threading.Lock()
        self.event_dict = {}
        self.req_url_lock = threading.Lock()
        self.req_url_dict = {}

        if self.mode == "balancing":
            self.balancing_decide_thread = threading.Thread(target=self.select_req_and_decide_llm)
            self.balancing_decide_thread.daemon = True
            self.balancing_decide_thread.start()


    def _setup_routes(self):
        @self.app.get("/health")
        def health():
            """Health check."""
            return JSONResponse({"status": "healthy"}, status_code=200)

        @self.app.post("/generate")
        async def generate(request: Request):
            """Generate completion for the request.

            The request should be a JSON object with the necessary fields for LLM request.
            """
            request_dict = await request.json()
            loop = asyncio.get_running_loop()

            future = loop.create_future()

            def handle_request():
                result = self._generate(request_dict)
                loop.call_soon_threadsafe(future.set_result, result)

            thread = threading.Thread(target=handle_request)
            thread.start()

            result = await future

            return JSONResponse(result)

    def decide(self, agent_name):
        with self.lock:
            model = self.agents_use_model.get(agent_name)
            if model is None:
                return None

            normal_urls = self.llm_urls.get(model, {}).get('normal')
            if not normal_urls:
                return None

            current_index = self.current_normal_url_indexes[model]
            current_url = normal_urls[current_index]

            self.current_normal_url_indexes[model] = (current_index + 1) % len(normal_urls)

            return current_url


    def wait_and_get_llm_url(self, metadata):
        msg_id = metadata["msg_id"]
        agent_name = metadata["agent_name"]

        # get priority
        metadata["priority"] = PRIORITY_TABLE[agent_name]

        # create event
        event = threading.Event()
        with self.event_lock:
            self.event_dict[msg_id] = event

        # append queue
        self.waiting.append(metadata)

        # self.logger.log(f"req {msg_id} 'start' waiting. \n\twaiting: {len(self.waiting)} \n\tevent dict: {self.event_dict} \n\turl: {self.req_url_dict}")                
        # waiting
        event.wait()
        # self.logger.log(f"req {msg_id} 'end' waiting. \n\twaiting: {len(self.waiting)} \n\tevent dict: {self.event_dict} \n\turl: {self.req_url_dict}")   

        # get url
        llm_url = None
        with self.req_url_lock:
            llm_url = self.req_url_dict.pop(msg_id, None)
        return llm_url

    def select_req_and_decide_llm(self):
        global is_queue
        while True:
            if is_queue:
                time.sleep(0.1) # Prevent busy-waiting

            # have reqs
            if not self.waiting.empty():
                self.waiting.sort_priority()
                req_metadata = self.waiting.peek_front()


                agent_name = req_metadata["agent_name"]
                model = self.agents_use_model.get(agent_name)

                msg_id = req_metadata["msg_id"]
                prompt_len = req_metadata["prompt_len"]
                predicted_time = PREDICT_TIME_TABLE[agent_name]


                normal_urls = self.llm_urls.get(model, {}).get('normal')

                llm_url = self.memory_predictor_manager.try_add_request(normal_urls, msg_id, prompt_len, predicted_time)

                if llm_url is None:
                    # self.logger.log(f"【waiting】")
                    is_queue = True
                    continue

                # pop req
                req_metadata = self.waiting.popleft()
                msg_id = req_metadata["msg_id"]

                with self.req_url_lock:
                    self.req_url_dict[msg_id] = llm_url

                # set event
                with self.event_lock:
                    event = self.event_dict.pop(msg_id)
                event.set()


    def _generate(self, data):
        metadata = data.pop("metadata")
        agent_name = metadata["agent_name"]
        msg_id = metadata["msg_id"]
        prompt_len = self.token_counter.count_tokens(agent_name, data["prompt"])
        metadata["prompt_len"] = prompt_len


        if self.mode == "balancing":
            url = self.wait_and_get_llm_url(metadata)


        self.logger.log(f"Extracted metadata: {metadata}, decide to llm url: {url}")

        if url is None:
            return {"error": "No LLM URLs available"}

        headers = {
            "Content-Type": "application/json"
        }

        json_data = json.dumps(data)
        try:
            response = requests.post(url, data=json_data, headers=headers)
            if response.status_code == 200:
                result = response.json()

                if self.mode == "balancing":
                    self.memory_predictor_manager.remove_request(msg_id, url)


                all_text_len = self.token_counter.count_tokens(agent_name, result["text"][0])

                return result
            else:
                return {"error": f"Error during LLM request. error code: {response.status_code}, info: {response.text}"}
        except requests.RequestException as e:
            return {"error": f"Error during LLM request: {e}"}

    def increase_waiting_time(self, add_waiting_time):
        with self.waiting_time_lock:
            self.total_waiting_time += add_waiting_time

    def start_server(self):
        self.app.root_path = self.root_path
        uvicorn.run(self.app, host=self.host, port=self.port)