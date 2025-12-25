# coding: utf-8

import logging
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


def move_file(caller_code, original_full_path, req_url, new_full_path, timeout=3, logger=logging, stub=None):
    code, err, channel = None, None, None
    try:
        logger = logger if logger else logging
        if not original_full_path or not req_url or not new_full_path or not caller_code:
            code = 128502
            return code, code_dict.get(str(code))
        if req_url.startswith("http"):
            req_url = urlparse(req_url).netloc
        if not stub:
            channel = grpc.insecure_channel(req_url, options=OPTIONS)
            stub = FileWorkerStub(channel)
        try:
            response = stub.moveFile(files_pb2.move_request(
                                        original_file_path=original_full_path.encode('utf-8'),
                                        new_file_path=new_full_path.encode('utf-8'), f_code=caller_code), timeout=timeout)
        except grpc.RpcError as e:
            status_code = e.code()
            if grpc.StatusCode.DEADLINE_EXCEEDED == status_code:
                # 请求超时
                code, err = 128512, code_dict.get("128512")
            elif grpc.StatusCode.UNAVAILABLE == status_code:
                # 服务短时不可用，重试一次
                try:
                    response = stub.moveFile(files_pb2.move_request(
                        original_file_path=original_full_path.encode('utf-8'),
                        new_file_path=new_full_path.encode('utf-8'), f_code=caller_code), timeout=timeout)
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
    if channel:
        channel.close()
    return code, err


def copy_file(caller_code, original_full_path, req_url, new_full_path, timeout=3, logger=logging, stub=None):
    code, err, channel = None, None, None
    try:
        logger = logger if logger else logging
        if not original_full_path or not req_url or not new_full_path or not caller_code:
            code = 128502
            return code, code_dict.get(str(code))
        if req_url.startswith("http"):
            req_url = urlparse(req_url).netloc
        if not stub:
            channel = grpc.insecure_channel(req_url, options=OPTIONS)
            stub = FileWorkerStub(channel)
        try:
            response = stub.copyFile(files_pb2.copy_request(
                                        original_file_path=original_full_path.encode('utf-8'),
                                        new_file_path=new_full_path.encode('utf-8'),
                                        f_code=caller_code), timeout=timeout)
        except grpc.RpcError as e:
            status_code = e.code()
            if grpc.StatusCode.DEADLINE_EXCEEDED == status_code:
                # 请求超时
                code, err = 128512, code_dict.get("128512")
            elif grpc.StatusCode.UNAVAILABLE == status_code:
                # 服务短时不可用，重试一次
                try:
                    response = stub.copyFile(files_pb2.copy_request(
                        original_file_path=original_full_path.encode('utf-8'),
                        new_file_path=new_full_path.encode('utf-8'),
                        f_code=caller_code), timeout=timeout)
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
    if channel:
        channel.close()
    return code, err
