# coding: utf-8

import logging
import os
import sys
import traceback

from NASGrpcFileSystem.grpc_options import OPTIONS

try:
    from urllib.parse import urlparse
except:
    from urlparse import urlparse
import grpc
from future.utils import raise_
from NASGrpcFileSystem.code_dict import code_dict
from .proto import files_pb2
from .proto.files_pb2_grpc import FileWorkerStub
if sys.version.startswith("2."):
    FileNotFoundError = IOError


def modify_file(caller_code, remote_full_path, req_url, modified_file_name, recovery_full_path=None, replace=True, timeout=3, logger=logging, stub=None):
    """
    修改文件名
    :param caller_code: 调用方编码
    :param remote_full_path: 远程文件存储路径及完整文件名称，全地址
    :param req_url: 请求IP:PORT
    :param modified_file_name: 修改后的文件名
    :param recovery_full_path: 容灾目录文件，当服务器修改文件名称失败时，修改此文件名称
    :param replace: 如果服务器已有要改的文件名，是否强制覆盖，默认覆盖
    :param timeout: 超时时间
    :param logger: 日志对象
    :return:
    """
    code, err, channel = None, None, None
    try:
        logger = logger if logger else logging
        if not remote_full_path or not req_url or not modified_file_name or not caller_code:
            code = 128502
            return code, code_dict.get(str(code))
        if req_url.startswith("http"):
            req_url = urlparse(req_url).netloc
        if recovery_full_path and not os.path.isfile(recovery_full_path):
            code = 128506
            return code, code_dict.get(str(code))
        _, old_name = os.path.split(remote_full_path)
        if old_name == modified_file_name:
            code = 128507
            return code, code_dict.get(str(code))
        if not stub:
            channel = grpc.insecure_channel(req_url, options=OPTIONS)
            stub = FileWorkerStub(channel)
        try:
            response = stub.modifyFile(files_pb2.modify_request(file_path=remote_full_path.encode('utf-8'),
                                                                file_name=modified_file_name.encode('utf-8'),
                                                                is_replace=replace, f_code=caller_code),
                                       timeout=timeout)
        except grpc.RpcError as e:
            status_code = e.code()
            if grpc.StatusCode.DEADLINE_EXCEEDED == status_code:
                # 请求超时
                code, err = 128512, code_dict.get("128512")
            elif grpc.StatusCode.UNAVAILABLE == status_code:
                # 服务短时不可用，重试一次
                try:
                    response = stub.modifyFile(files_pb2.modify_request(file_path=remote_full_path.encode('utf-8'),
                                                                        file_name=modified_file_name.encode(
                                                                            'utf-8'),
                                                                        is_replace=replace, f_code=caller_code),
                                               timeout=timeout)
                except grpc.RpcError as e:
                    logger.error("Grpc retried and error again，%s, details=%s", status_code, e.details())
                    code = 1
                    err = "请求失败"
                else:
                    code = response.code
                    err = response.err
            elif grpc.StatusCode.INVALID_ARGUMENT == status_code:
                # 参数异常
                code = 128501
                return code, code_dict.get(str(code))
            else:
                logger.error("Grpc error，%s, details=%s", status_code, e.details())
                code = 1
                err = "请求失败"
        else:
            code = response.code
            err = response.err
    except Exception as exc:
        logger.error(traceback.format_exc())
        raise_(Exception, exc)
    finally:
        try:
            if (code in [128509, 128512, 1] or not code_dict.get(str(code), None)) and recovery_full_path:
                try:
                    recovery_path, recovery_name = os.path.split(recovery_full_path)
                    if recovery_name == modified_file_name:
                        if not replace:
                            return 128507, code_dict.get("128507")
                    new_recovery_full = os.path.join(recovery_path, modified_file_name)
                    os.rename(recovery_full_path, new_recovery_full)
                    code, err = 0, code_dict.get("0")
                except FileNotFoundError:
                    return 128505, code_dict.get("128505")
                except OSError:
                    return 128507, code_dict.get("128507")
                except Exception as exc:
                    logger.error(traceback.format_exc())
                    raise_(Exception, exc)
        except Exception as exc:
            logger.error(traceback.format_exc())
            raise_(Exception, exc)
        if channel:
            channel.close()
    return code, err
