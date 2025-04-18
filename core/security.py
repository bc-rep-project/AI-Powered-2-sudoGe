import logging
from typing import Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from api.core.config import Settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')


def verify_token(token: str = Depends(oauth2_scheme), settings: Settings = Depends()) -> Dict:
    """
    Verifies a JWT token and returns the decoded payload.

    Args:
        token: The JWT token to verify.
        settings: The application settings.

    Returns:
        The decoded payload.

    Raises:
        HTTPException: If the token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'])
        logging.info("Token verified successfully.")
        return payload
    except JWTError as e:
        logging.error(f"Invalid token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except Exception as e:
        logging.error(f"Error during token verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e