import os

VLLM_ENGINE_PATH = "/state/vllm/vllm_api_server.py"
max_model_len=8192

def start_vllm_engine(port, model, dtype, max_num_seqs, cuda_visible_devices, 
                        enable_chunked_prefill=False, tensor_parallel_size=1, gpu_memory_utilization=0.9):
    cuda_visible_devices_str = ""
    for devices in cuda_visible_devices:
        if cuda_visible_devices_str == "":
            cuda_visible_devices_str += str(devices)
        else:
            cuda_visible_devices_str += "," + str(devices)

    command = (
    f"CUDA_VISIBLE_DEVICES={cuda_visible_devices_str} "
    f"python3 {VLLM_ENGINE_PATH} "
    f"--port {port} "
    f"--model {model} "
    f"--dtype {dtype} "
    f"--max_num_seqs {max_num_seqs} "
    f"--enable-chunked-prefill {enable_chunked_prefill} "
    f"--max-model-len {max_model_len} "
    f"--tensor-parallel-size {tensor_parallel_size} "
    f"--gpu-memory-utilization {gpu_memory_utilization}"
)
    print(command)
    os.system(command)


def start_vllm_engine_remote(
    host,
    port, model, dtype, max_num_seqs, cuda_visible_devices, 
                        enable_chunked_prefill=False, tensor_parallel_size=1, gpu_memory_utilization=0.9):
    
    cuda_visible_devices_str = ""
    for devices in cuda_visible_devices:
        if cuda_visible_devices_str == "":
            cuda_visible_devices_str += str(devices)
        else:
            cuda_visible_devices_str += "," + str(devices)

    command = (
    f"CUDA_VISIBLE_DEVICES={cuda_visible_devices_str} "
    f"python3 {VLLM_ENGINE_PATH} "
    f"--port {port} "
    f"--model {model} "
    f"--dtype {dtype} "
    f"--max_num_seqs {max_num_seqs} "
    f"--enable-chunked-prefill {enable_chunked_prefill} "
    f"--max-model-len {max_model_len} "
    f"--tensor-parallel-size {tensor_parallel_size} "
    f"--gpu-memory-utilization {gpu_memory_utilization}"
)

    remote_cmd = f"{command}"
    ssh_command = f"ssh {host} '{remote_cmd}'"

    print("[Remote Launch]", ssh_command)
    os.system(ssh_command)
