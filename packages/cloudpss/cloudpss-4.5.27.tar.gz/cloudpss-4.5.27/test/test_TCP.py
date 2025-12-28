import socket

def tcp_client():
    host = '10.101.10.102'  # 服务器 IP 地址
    port = 8802        # 服务器端口

    # 创建 socket 对象
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # 连接到服务器
        client_socket.connect((host, port))
        print(f"已连接到服务器 {host}:{port}")
        # 接收服务器返回的数据
        while True:
            rec_msg = client_socket.recv(1024)
            hex_representation = ' '.join(f'{byte:02x}' for byte in rec_msg)
            print(' 客户端消息的十六进制表示: ', hex_representation)
            # print(f"接收到来自服务器的消息: {data.decode()}")
            
            client_socket.send(rec_msg)

    except ConnectionRefusedError:
        print("连接失败，服务器可能未启动。")
    finally:
        # 关闭连接
        client_socket.close()
        print("客户端已关闭连接。")

if __name__ == '__main__':
    tcp_client()