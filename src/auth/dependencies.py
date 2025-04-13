from fastapi import Request, status, Depends
from fastapi.security import HTTPBearer
from fastapi.exceptions import HTTPException
from fastapi.security.http import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from db.mongo import token_in_blocklist
from db.main import get_session
from .utils import decode_token
from customer.services import CustomerService
from driver.services import DriverService
from admin.services import AdminService
from typing import Any, Union


admin_service = AdminService()
customer_service = CustomerService()
driver_service = DriverService()


class TokenBearer(HTTPBearer):
    def __init__(self, auto_error=True):
        super().__init__(auto_error=auto_error)
        
    async def __call__(self, request: Request) -> Union[HTTPAuthorizationCredentials, None]:
        creds = await super().__call__(request)
        token = creds.credentials
        token_data = decode_token(token)
        if not self.token_valid(token):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or Expired Token")
        if await token_in_blocklist(token_data["jti"]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or Expired Token")
        self.verify_token_data(token_data)
        return token_data
    
    def token_valid(self, token: str) -> bool:
        token_data = decode_token(token)
        return token_data is not None
    
    def verify_token_data(self, token_data):
        raise NotImplementedError("Please Override this method in child classes")
            

class AccessTokenBearer(TokenBearer):
    def verify_token_data(self, token_data: dict) -> None:
        if token_data and token_data["refresh"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Please provide a valid access token")

class RefreshTokenBearer(TokenBearer):
    def verify_token_data(self, token_data: dict) -> None:
        if token_data and not token_data["refresh"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Please provide a valid refresh token")
            
async def get_current_user(
    token_details: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    payload = token_details["user"]
    if 'admin_id' in payload:
        admin_id = payload['admin_id']
        admin = await admin_service.get_admin_user_by_id(session, admin_id)
        if not admin:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin user not found")
        admin.role = "admin"
        return admin
    elif 'customer_id' in payload:
        customer_id = payload['customer_id']
        customer = await customer_service.get_customer_by_id(session, customer_id)
        if not customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        customer.role = "customer"
        return customer
    elif 'driver_id' in payload:
        driver_id = payload['driver_id']
        driver = await driver_service.get_driver_by_id(session, driver_id)
        if not driver:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
        driver.role = "driver"
        return driver
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user payload in token")

def require_role(allowed_roles: list):
    def dependency(current_user: object = Depends(get_current_user)):
        if not hasattr(current_user, 'role') or current_user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this endpoint")
        return current_user
    return dependency
