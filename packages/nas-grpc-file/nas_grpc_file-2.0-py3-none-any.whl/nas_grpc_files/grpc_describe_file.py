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
from NASGrpcFileSystem.grpc_create_file import _gen_file
from .proto import files_pb2
from .proto.files_pb2_grpc import FileWorkerStub
if sys.version.startswith("2."):
    FileNotFoundError = IOError


def describe_file(caller_code, remote_full_path, req_url, local_full_path=None,
                  recovery_full_path=None, return_file=True, timeout=3, logger=logging, stub=None, channel=None):
    code, err, ret_file = None, None, " "
    try:
        logger = logger if logger else logging
        if not remote_full_path or not req_url or not caller_code:
            code = 128502
            return code, code_dict.get(str(code)), "", stub, channel
        if req_url.startswith("http"):
            req_url = urlparse(req_url).netloc
        if recovery_full_path and not os.path.isfile(recovery_full_path):
            code = 128506
            return code, code_dict.get(str(code)), "", stub, channel
        if not return_file:
            if not local_full_path:
                code = 128502
                return code, code_dict.get(str(code)), "", stub, channel
            else:
                if os.path.exists(local_full_path):
                    code = 128507
                    return code, code_dict.get(str(code)), "", stub, channel
                if not str(os.path.split('./demo.py')[-1]).split(".")[1]:
                    code = 128503
                    return code, code_dict.get(str(code)), "", stub, channel
        if not stub:
            channel = grpc.insecure_channel(req_url, options=OPTIONS)
            stub = FileWorkerStub(channel)
        code, err, ret_file = _call_des_handle(stub, remote_full_path, caller_code, timeout, logger, local_full_path, return_file)
        if code in [128509, 128512, 1]:
            if channel:
                channel.close()
            channel = grpc.insecure_channel(req_url, options=OPTIONS)
            stub = FileWorkerStub(channel)
            code, err, ret_file = _call_des_handle(stub, remote_full_path, caller_code, timeout, logger,
                                                   local_full_path, return_file)
    except Exception as exc:
        logger.error(traceback.format_exc())
        raise_(Exception, exc)
    finally:
        try:
            if (code in [128509, 128512, 1] or not code_dict.get(str(code), None)) and recovery_full_path:
                code, err, ret_file = _recovery_handle(recovery_full_path, local_full_path, return_file, logger)
        except Exception as exc:
            logger.error(traceback.format_exc())
            raise_(Exception, exc)

    return code, err, ret_file, stub, channel


def _call_des_handle(stub, remote_full_path, caller_code, timeout, logger, local_full_path, return_file):
    try:
        response = stub.describeFile(files_pb2.describe_request(
            locate_file=remote_full_path.encode('utf-8'), f_code=caller_code), timeout=timeout)
    except grpc.RpcError as e:
        status_code = e.code()
        if grpc.StatusCode.DEADLINE_EXCEEDED == status_code:
            # 请求超时
            code, err, ret_file = 128512, code_dict.get("128512"), ""
        elif grpc.StatusCode.UNAVAILABLE == status_code:
            # 服务短时不可用，重试一次
            try:
                response = stub.describeFile(files_pb2.describe_request(
                    locate_file=remote_full_path.encode('utf-8'), f_code=caller_code), timeout=timeout)
            except grpc.RpcError as e:
                logger.error("Grpc retried and error again，%s, details=%s", status_code, e.details())
                code = 1
                err = "请求失败"
                ret_file = b""
            else:
                code = response.code
                err = response.err
                ret_file = response.file
                if code == 0 and local_full_path:
                    if not os.path.exists(local_full_path):
                        try:
                            with open(local_full_path, "wb") as f:
                                f.write(ret_file)
                        except IOError:
                            code = 128513
                            return code, code_dict.get(str(code)), ""
                    else:
                        code = 128507
                        return code, code_dict.get(str(code)), ""
        elif grpc.StatusCode.INVALID_ARGUMENT == status_code:
            # 参数异常
            code = 128501
            return code, code_dict.get(str(code)), ""
        else:
            logger.error("Grpc error，%s, details=%s", status_code, e.details())
            code = 1
            err = "请求失败"
            ret_file = b""
    else:
        code = response.code
        err = response.err
        ret_file = response.file
        if code == 0 and local_full_path:
            if not os.path.exists(local_full_path):
                try:
                    with open(local_full_path, "wb") as f:
                        f.write(ret_file)
                except IOError:
                    code = 128513
                    return code, code_dict.get(str(code)), ""
            else:
                code = 128507
                return code, code_dict.get(str(code)), ""
        ret_file = ret_file if return_file else ""

    return code, err, ret_file


def _recovery_handle(recovery_full_path, local_full_path, return_file, logger):
    try:
        recovery_file = _gen_file(recovery_full_path)
        if local_full_path:
            if not os.path.exists(local_full_path):
                with open(local_full_path, "wb") as f:
                    for fc in recovery_file:
                        f.write(fc)
            else:
                return 128507, code_dict.get("128507"), ""
        code = 0
        err = '操作成功'
        if return_file:
            with open(recovery_full_path, "rb") as f:
                ret_file = f.read()
        else:
            ret_file = ""
        return code, err, ret_file
    except FileNotFoundError:
        return 128505, code_dict.get("128505"), ""
    except IOError:
        return 128513, code_dict.get("128513"), ""
    except Exception as exc:
        logger.error(traceback.format_exc())
        raise_(Exception, exc)