import json
import keyring
import requests
import asyncio
import aiohttp
from dataclasses import dataclass, asdict
from backend.local_storage import LocalStorage
from backend.http import Http, HttpMethod, GenericErrorBody, ResultType, E, Result, S
from backend.session_manager import SessionManager, User


@dataclass
class AuthMethodResp:
    email: bool
    password: bool
    sms: bool

async def login(username: str) -> AuthMethodResp:
    print("Getting auth methods")
    result = await Http(
            HttpMethod.GET,
            f"user/authOptions?unameMailPhone={username}",
            None,
            AuthMethodResp
        )

    if result.type == ResultType.SUCCESS:
        return result.success
    else:
        raise ValueError("API Returned An Error")

async def password_auth(username: str, password: str):
    print("Authenticating with password")
    result =  await Http(
        HttpMethod.POST,
        "v2/user/loginPasswordAuth",
        asdict(PasswordAuthReq(
            unameMailPhone=username,
            password=password,
            os="Linux",
            language="en"
        )),
        LoginResp,
    )

    if result.type == ResultType.SUCCESS:
        SessionManager.instance().addSession(result.success.token, User(
            username=result.success.username,
            displayName=result.success.displayName,
            pfp=result.success.pfp,
            userid=result.success.userid
        ))
    else:
        raise ValueError("Error")

async def otp_send_code(type: int, unameMailPhone: str):
    result = await Http(
        HttpMethod.POST,
        "v2/user/otpSendCode",
        asdict(SendOTPCode(
            usernamePhoneMail=unameMailPhone,
            type=type
        ))
    )

    if result.type == ResultType.SUCCESS:
        print("OTP Sent Successfully")
    else:
        raise ValueError(f"API Returned An Error {result.error}")

async def otp_verify_code(type: int, unameMailPhone: str, code: int):
    result = await Http(
        HttpMethod.POST,
        "v2/user/otpVerifyCode",
        asdict(VerifyOTPCodeReq(
            usernamePhoneMail=unameMailPhone,
            type=type,
            code=code,
            os="Linux",
            language="en"
        )),
        LoginResp,
    )

    if result.type == ResultType.SUCCESS:
        SessionManager.instance().addSession(result.success.token, User(
            username=result.success.username,
            displayName=result.success.displayName,
            pfp=result.success.pfp,
            userid=result.success.userid
        ))
    else:
        raise ValueError(f"API Returned An Error {result.error}")

    return result

@dataclass()
class PasswordAuthReq:
    unameMailPhone: str
    password: str
    os: str
    language: str

@dataclass()
class LoginResp:
    token: str
    userid: str
    username: str
    displayName: str
    pfp: str

@dataclass()
class SendOTPCode:
    usernamePhoneMail: str
    type: int

@dataclass()
class VerifyOTPCodeReq:
    usernamePhoneMail: str
    type: int
    code: int
    os: str
    language: str
