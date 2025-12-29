import hashlib
import jwt
from jwt import exceptions

class Token:
    def __init__(self, secret):
        self.secret = secret

    def create_token(self, data:dict):
        '''生成token'''
        headers = {'alg': "HS256", 'typ': "JWT"}
        payload = data
        token = jwt.encode(payload=payload, key=self.secret, algorithm='HS256', headers=headers)
        return token
    
    def validate_token(self, token):
        '''验证token'''
        try:
            payload = jwt.decode(jwt=token, key=self.secret, algorithms=['HS256'])
        except exceptions.ExpiredSignatureError:
            raise ValueError('token已失效')
        except jwt.DecodeError:
            raise ValueError('token认证失败')
        except jwt.InvalidTokenError:
            raise ValueError('非法的token')
        if not payload:
            raise ValueError('token出现错误')
        return payload