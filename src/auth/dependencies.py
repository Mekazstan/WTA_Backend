from fastapi import Request, status, Depends
from fastapi.security import HTTPBearer
from fastapi.exceptions import HTTPException
from fastapi.security.http import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from db.mongo import token_in_blocklist
from db.main import get_session
from db.models import Customer
from .utils import decode_token
from customer.services import CustomerService
from driver.services import DriverService
from typing import Any, List, Union



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
            
async def get_current_customer(
    token_details: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    customer_email = token_details["user"]["email"]

    customer = await customer_service.get_customer_by_email(customer_email, session)

    return customer


async def get_current_driver(
    token_details: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    driver_id = token_details["user"]["driver_id"]

    driver = await driver_service.get_driver_by_id(driver_id, session)

    return driver