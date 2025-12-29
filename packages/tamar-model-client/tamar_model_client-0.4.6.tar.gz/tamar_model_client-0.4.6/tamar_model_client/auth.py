import time
import jwt
from typing import Optional


# JWT 处理类
class JWTAuthHandler:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self._token_cache: Optional[str] = None
        self._token_exp_time: Optional[int] = None

    def encode_token(self, payload: dict, expires_in: int = 3600) -> str:
        """生成带过期时间的 JWT Token"""
        payload = payload.copy()
        exp_time = int(time.time()) + expires_in
        payload["exp"] = exp_time
        token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        
        # 缓存token和过期时间
        self._token_cache = token
        self._token_exp_time = exp_time
        
        return token
    
    def is_token_expiring_soon(self, buffer_seconds: int = 60) -> bool:
        """检查token是否即将过期
        
        Args:
            buffer_seconds: 提前多少秒认为token即将过期，默认60秒
            
        Returns:
            bool: True表示token即将过期或已过期
        """
        if not self._token_exp_time:
            return True
        
        current_time = int(time.time())
        return current_time >= (self._token_exp_time - buffer_seconds)
    
    def get_cached_token(self) -> Optional[str]:
        """获取缓存的token"""
        return self._token_cache
