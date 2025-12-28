# coding: utf-8


MAX_MESSAGE_LENGTH = 256 * 1024 * 1024
INITIAL_WINDOW_SIZE = 5 * 1024 * 1024


OPTIONS = [
        ('grpc.max_send_message_length', MAX_MESSAGE_LENGTH),
        ('grpc.max_receive_message_length', MAX_MESSAGE_LENGTH),
        ('grpc.initial_window_size', INITIAL_WINDOW_SIZE),
        ('grpc.initial_conn_window_size', INITIAL_WINDOW_SIZE),
        ('grpc.write_buffer_size', 5 * 1024 * 1024),
        ('grpc.read_buffer_size', 5 * 1024 * 1024),
        ]
