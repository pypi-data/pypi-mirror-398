# coding: utf-8
import logging
import grpc
from .proto.files_pb2_grpc import FileWorkerStub
from .grpc_create_file import create_file
from .grpc_describe_file import describe_file
from .grpc_modify_file import modify_file
from .grpc_copy_move_file import copy_file, move_file


try:
    from urllib.parse import urlparse
except BaseException:
    from urlparse import urlparse


# 文件大小限制
MAX_MESSAGE_LENGTH = 256 * 1024 * 1024
INITIAL_WINDOW_SIZE = 5 * 1024 * 1024


class FileHandler:

    def __init__(self, req_url):
        """
        :param req_url: 请求服务的 ip:port
        """
        self.req_url = req_url
        self.channel = grpc.insecure_channel(req_url, options=[
            ('grpc.max_send_message_length', MAX_MESSAGE_LENGTH),
            ('grpc.max_receive_message_length', MAX_MESSAGE_LENGTH),
            ('grpc.initial_window_size', INITIAL_WINDOW_SIZE),
            ('grpc.initial_conn_window_size', INITIAL_WINDOW_SIZE),
            ('grpc.write_buffer_size', 5 * 1024 * 1024),
            ('grpc.read_buffer_size', 5 * 1024 * 1024),
            ])
        self.stub = FileWorkerStub(self.channel)

    def create_file(self, caller_code, remote_path, x_type, file=None, filename=None,
                    file_path=None, mount_path=None, replace=True,
                    recovery_path=None, timeout=3, logger=logging):
        """
        在服务器创建文件
        :param caller_code: 调用方编码
        :param remote_path: 远程存储目录
        :param x_type: 业务类型
        :param file: 文件流，若不选择文件路径则必传文件流，也可以是base64编码的文件
        :param filename: 文件名称， 当上传对象为文件流时必传
        :param file_path: 本地文件路径，可以选择文件路径或者文件流
        :param mount_path: 服务器mount地址
        :param replace: 当文件已在服务器存在时是否强制替换，默认替换
        :param recovery_path: 容灾路径，当文件上传非正常失败时（调用接口非正常错误码），将文件存储的本地地址，此时返回的mount_path为空
        :param timeout: 超时时间，默认3秒
        :param logger: 日志对象
        :return:
        """
        code, err, ret_mount_path, stub, channel = create_file(caller_code, remote_path, x_type, self.req_url,
                                                               file=file, filename=filename,
                                                               file_path=file_path, mount_path=mount_path, replace=replace,
                                                               recovery_path=recovery_path, timeout=timeout, logger=logger,
                                                               stub=self.stub, channel=self.channel)
        self.channel = channel
        self.stub = stub
        return code, err, ret_mount_path

    def describe_file(self, caller_code, remote_full_path, local_full_path=None,
                      recovery_full_path=None, return_file=True, timeout=3, logger=logging):
        """
        返回文件信息
        :param caller_code: 调用方编码
        :param remote_full_path: 远程文件存储路径及完整文件名称，全地址
        :param recovery_full_path: 容灾目录文件，当非正常错误发生时，读取此文件
        :param local_full_path: 下载的文件本地存储路径包含文件名，全地址
        :param return_file: 是否需要将文件流返回, 如不返回则需要传入local_full_path，同时返回""
        :param timeout: 超时时间
        :param logger: 日志对象
        :return:
        """
        code, err, ret_file, stub, channel = describe_file(caller_code, remote_full_path, self.req_url,
                                                           local_full_path=local_full_path,
                                                           recovery_full_path=recovery_full_path, return_file=return_file,
                                                           timeout=timeout, logger=logger, stub=self.stub, channel=self.channel)
        self.channel = channel
        self.stub = stub
        return code, err, ret_file

    def modify_file(self, caller_code, remote_full_path, modified_file_name, recovery_full_path=None, replace=True, timeout=3, logger=logging):
        """
        修改文件名
        :param caller_code: 调用方编码
        :param remote_full_path: 远程文件存储路径及完整文件名称，全地址
        :param modified_file_name: 修改后的文件名
        :param recovery_full_path: 容灾目录文件，当服务器修改文件名称失败时，修改此文件名称
        :param replace: 如果服务器已有要改的文件名，是否强制覆盖，默认覆盖
        :param timeout: 超时时间
        :param logger: 日志对象
        :return:
        """
        return modify_file(caller_code, remote_full_path, self.req_url, modified_file_name,
                           recovery_full_path=recovery_full_path, replace=replace,
                           timeout=timeout, logger=logger, stub=self.stub)

    def copy_file(self, caller_code, original_full_path, new_full_path, timeout=3, logger=logging):
        """
        复制文件
        :param caller_code: 调用方编码
        :param original_full_path: 远程文件存储路径及完整文件名称，全地址
        :param new_full_path: 复制后的文件路径（传文件名则变更文件名称，不传则为原文件名称）；路径存在直接移动，不存在则创建
        :param timeout: 超时时间
        :param logger: 日志对象
        :return:
        """
        return copy_file(caller_code, original_full_path, self.req_url, new_full_path,
                         timeout=timeout, logger=logger, stub=self.stub)

    def move_file(self, caller_code, original_full_path, new_full_path, timeout=3, logger=logging):
        """
        移动文件
        :param caller_code: 调用方编码
        :param original_full_path: 远程文件存储路径及完整文件名称，全地址
        :param new_full_path: 移动后的文件存储路径（存在直接移动，不存在则创建），不包含文件名（移动后文件名称与原文件名一致）
        :param timeout: 超时时间
        :param logger: 日志对象
        :return:
        """
        return move_file(caller_code, original_full_path, self.req_url, new_full_path, timeout=timeout,
                         logger=logger, stub=self.stub)

    def __del__(self):
        if self.channel:
            self.channel.close()
