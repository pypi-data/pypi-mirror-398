# Copyright (c) [2023] [Tenny]
# [ph-utils] is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#         http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.
import hashlib
import base64


def hash(d: str, method="sha1", upper=False, result="hex"):
    """进行 md5、sha1、sha256 数据摘要签名

    Args:
        d (str): 待加密的数据
        method (str, optional): 签名算法, md5、sha1、sha256. Defaults to "md5".
        upper (bool, optional): 返回的结果是否需要大写. Defaults to False.
        result (str, optional): 返回数据, hex 转换为 HEX 返回

    Raises:
        Exception: method只允许为 md5、sha1中的一个

    Returns:
        str: 加密后的结果
    """
    if method in ("md5", "sha1", "sha256"):
        func = getattr(hashlib, method)
        althorithm = func()
        althorithm.update(d.encode("utf-8"))
        if result == "hex":
            rd = althorithm.hexdigest()
            return rd if upper is False else rd.upper()
        else:
            return althorithm.digest()
    else:
        raise Exception("unsupport_althorithm_method")


def b64encode(data, result="str"):
    """base64加密

    Args:
        data (str): 待base64加密数据
        result (str, optional): 加密返回结果, str、bytes. Defaults to "str".

    Returns:
        str|bytes: base64加密后的数据
    """
    if not data:
        return None
    encode_data = data
    if isinstance(encode_data, str):
        encode_data = encode_data.encode()
    encoded = base64.b64encode(encode_data)
    return encoded.decode() if result == "str" else encoded


def b64decode(data, result="str"):
    """base64解密

    Args:
        data (str|bytes): base64加密后的数据
        result (str, optional): str、bytes. Defaults to "str".

    Returns:
        str|bytes: base64解密后的数据
    """
    if not data:
        return None
    decoded = base64.b64decode(data)
    return decoded.decode() if result == "str" else decoded
