import zmq
import time
import torch
from tensordict import TensorDict
from transfer_queue.utils.zmq_utils import ZMQMessage, ZMQRequestType
from tensordict.tensorclass import NonTensorData
import random
import multiprocessing

def create_complex_test_case(batch_size=None, seq_length=None, field_num=None):
    tensor_field_size_bytes = batch_size * seq_length * 4
    tensor_field_size_gb = tensor_field_size_bytes / (1024 ** 3)

    num_tensor_fields = (field_num + 1) // 2
    num_nontensor_fields = field_num // 2

    total_tensor_size_gb = tensor_field_size_gb * num_tensor_fields
    total_nontensor_size_gb = (batch_size * 1024 / (1024 ** 3)) * num_nontensor_fields
    total_size_gb = total_tensor_size_gb + total_nontensor_size_gb


    fields = {}

    for i in range(field_num):
        field_name = f"field_{i}"

        if i % 2 == 0:  # tensor字段
            tensor_data = torch.randn(batch_size, seq_length, dtype=torch.float32)
            fields[field_name] = tensor_data
        else:  # NonTensorData字段
            str_length = 1024
            non_tensor_data = [
                ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=str_length))
                for _ in range(batch_size)
            ]
            fields[field_name] = NonTensorData(data=non_tensor_data, batch_size=(batch_size,), device=None)

    batch_size_tuple = (batch_size,)
    prompt_batch = TensorDict(
        fields,
        batch_size=batch_size_tuple,
        device=None,
    )

    return prompt_batch, total_size_gb


# -------------------------- Server（ROUTER Socket） --------------------------
def router_server():
    context = zmq.Context()
    router_socket = context.socket(zmq.ROUTER)
    router_socket.bind("tcp://127.0.0.1:5555")
    print("ROUTER Server is ready, binding：tcp://127.0.0.1:5555")


    print("\n=== start communication（send_multipart/recv_multipart）===")
    messages = router_socket.recv_multipart()
    id = messages.pop(0)
    response_msg = ZMQMessage.deserialize(messages)
    print(response_msg)

    # Try to do in-place modification to see if it's allowed
    td = response_msg.body['data']
    print( td['field_0'] )
    td['field_0'] += 9999999
    print( td['field_0'] )
    # it's safe to do in-place modification even we set
    # arr = torch.frombuffer(buffer, dtype=torch.uint8)


    router_socket.send_multipart([
        id,
        b"ack",
    ])


    time.sleep(1)
    router_socket.close()
    context.term()

# -------------------------- Client（DEALER Socket） --------------------------
def dealer_client():
    context = zmq.Context()
    dealer_socket = context.socket(zmq.DEALER)
    # set client identity
    dealer_socket.setsockopt_string(zmq.IDENTITY, "client_001")
    dealer_socket.connect("tcp://127.0.0.1:5555")
    print("DEALER Client is ready, connecting：tcp://127.0.0.1:5555")
    time.sleep(0.5)

    test_data, total_data_size_gb = create_complex_test_case(
        batch_size=4096,
        seq_length=128000,
        field_num=2
    )

    request_msg = ZMQMessage.create(
        request_type=ZMQRequestType.PUT_DATA,
        sender_id='123',
        receiver_id='456',
        body={"data":test_data},
    )


    dealer_socket.send_multipart(request_msg.serialize(),copy=False)


    response_frames = dealer_socket.recv_multipart()
    response_frame1 = response_frames[0]
    print(f"DEALER Receive → Frame: {response_frame1}")

    dealer_socket.close()
    context.term()

# -------------------------- Start all processes --------------------------
if __name__ == "__main__":
    # Start server process
    server_process = multiprocessing.Process(target=router_server)
    server_process.start()
    time.sleep(0.5)

    # Start client process
    client_process = multiprocessing.Process(target=dealer_client)
    client_process.start()


    server_process.join()
    client_process.join()
    print("Test Finish！")