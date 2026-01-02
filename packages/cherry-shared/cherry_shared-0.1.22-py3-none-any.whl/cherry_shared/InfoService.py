import json
import logging
from typing import Any, Dict, Literal, Optional
import aiohttp
from cherry_shared.launchpads import LaunchPad
from cherry_shared.types.dexscreener import Pair
from cherry_shared.types.launchpad import LaunchpadToken


class InfoService:

    def __init__(self, info_url: str, helper_url: str, logger: logging.Logger = None):
        self.info_url = info_url
        self.helper_url = helper_url
        if logger is None:
            self._logger = logging.getLogger(__name__)
        else:
            self._logger = logger

    async def process_request(
        self,
        url: str,
        body: Dict[str, Any] = None,
        method: str = "GET",
        query: Dict[str, str] = None,
        headers: Dict[str, str] = None,
        timeout: int = 60,
    ):
        if headers is None:
            headers = {"Content-Type": "application/json"}
        # Define a custom timeout
        custom_timeout = aiohttp.ClientTimeout(total=timeout)

        async with aiohttp.ClientSession(
            headers=headers, timeout=custom_timeout
        ) as session:
            try:
                if method == "GET":
                    async with session.get(
                        url, params=query, data=json.dumps(body) if body else None
                    ) as resp:
                        if resp.status >= 400:
                            return False, resp.reason
                        if "application/json" in resp.headers.get("Content-Type", ""):
                            res = await resp.json()
                        else:
                            res = await resp.text()
                            return (
                                False,
                                f"Unexpected Content-Type: {resp.headers.get('Content-Type')}, Response: {res}",
                            )
                elif method == "POST":
                    async with session.post(url, data=json.dumps(body)) as resp:
                        if resp.status >= 400:
                            return False, resp.reason
                        if "application/json" in resp.headers.get("Content-Type", ""):
                            res = await resp.json()
                        else:
                            res = await resp.text()
                            return (
                                False,
                                f"Unexpected Content-Type: {resp.headers.get('Content-Type')}, Response: {res}",
                            )

                return True, res
            except Exception as e:
                self._logger.error(f"Error in InfoService.process_request(): {e}")
                return False, "Exception: " + str(e)

    async def search_address(self, address: str):
        url = f"{self.info_url}/info/{address}"
        success, data = await self.process_request(url)
        if success:
            return [Pair.from_dexsc_dict(item) for item in data["data"][:10]]

    async def get_address_type(self, address: str):
        url = f"{self.info_url}/address"
        body = {"address": address}
        success, res = await self.process_request(url, body)
        if success:
            return res["data"]

    async def get_pair_by_pair_address(self, address: str, chainId: str):
        url = f"{self.info_url}/info/pair"
        success, res = await self.process_request(
            url, {"address": address, "chainId": chainId}, "POST"
        )

        if not success:
            self._logger.error(res)
            return None
        return Pair.from_dexsc_dict(res["data"])

    async def get_chains_data(self):
        url = f"{self.info_url}/chains"
        success, data = await self.process_request(url)
        if success:
            return data

    async def get_total_supply(self, chain: str, address: str):
        url = self.helper_url + "/totalsupply"
        body = {"chain": chain, "address": address}
        success, data = await self.process_request(url, body, "POST")
        if success:
            return data["supply"], data["decimals"]
        return None, None

    async def get_trending(self):
        url = self.helper_url + "/trending"
        success, data = await self.process_request(url)
        if success:
            return data
        return None

    async def send_confirm_req(
        self, pair_address: str, contract_address: str, chain_id: str, chat_id: int
    ):
        url = self.helper_url + "/confirm"
        self._logger.debug(f"{pair_address}, {chain_id}, {chat_id}")
        body = {
            "pairAddress": pair_address,
            "tokenAddress": contract_address,
            "chainId": chain_id,
            "chatId": chat_id,
        }
        self._logger.debug(f"send_confirm_req: {body}")
        success, data = await self.process_request(url, body, "POST")
        if not success:
            self._logger.error(f"failed to send confirm req: {data}")

    async def send_delete_req(self, tokenAddress: str, chat_id: int):
        url = self.helper_url + "/delete"
        body = {
            "tokenAddress": tokenAddress,
            "chatId": chat_id,
        }
        success, data = await self.process_request(url, body, "POST")
        if not success:
            self._logger.error(f"failed delete token req: {data}")

    async def send_update_supply(self, tokenAddress: str, chat_id: int, supply: int):
        self._logger.debug(f"{tokenAddress}, {chat_id}, {supply}")
        url = self.helper_url + "/updatesupply"
        body = {
            "address": tokenAddress,
            "chatId": chat_id,
            "supply": supply,
        }
        success, data = await self.process_request(url, body, "POST")
        if not success:
            self._logger.error(f"failed updatesupply req: {data}")

    async def generate_wallet(self, wallet_type: str):
        wallet_endpoints = {
            "solana": "/generatesolanawallet",
            "tron": "/generatetronwallet",
            "ton": "/generatestonwallet",
            "sui": "/generatesuiawallet",
        }

        if wallet_type not in wallet_endpoints:
            self._logger.error(f"wallet endpoint not provided: {wallet_type}")
            return

        url = self.helper_url + wallet_endpoints[wallet_type]
        success, data = await self.process_request(url)

        if not success:
            self._logger.error(f"Failed {wallet_type} wallet request: {data}")
            return
        self._logger.debug(f"generated new wallet {data['publicKey'][:10]}")
        return data["publicKey"], data["privateKey"]

    async def get_balance(self, wallet_address: str, chain: str):
        url = self.helper_url + "/balance"
        success, data = await self.process_request(
            url, query={"tokenAddress": wallet_address, "chain": chain}
        )
        if not success:
            self._logger.error(f"failed to get balance: {data}")
            return None
        return float(data["balance"])

    async def buyNburn(
        self,
        raid_id: int,
        chat_id: int,
        amount: float,
        token_address: str,
        pair_address: str,
        chain: str,
        pk: str,
    ):
        url = self.helper_url + "/burn"
        body = {
            "raidId": raid_id,
            "chatId": chat_id,
            "amount": amount,
            "tokenAddress": token_address,
            "pairAddress": pair_address,
            "chain": chain,
            "privateKey": pk,
        }
        success, data = await self.process_request(url, body, "POST")
        if not success:
            self._logger.error(f"failed to send confirm req: {data}")
            return False, data

        status: bool = data["status"]
        self._logger.debug(f"buyNburn status = {status}")
        return status, None

    async def check_status(self, raid_id: int):
        try:
            url = self.helper_url + f"/status?raidId={raid_id}"
            success, data = await self.process_request(url)
            if not success:
                self._logger.error(f"failed to send confirm req: {data}")
                return "error", data
            res = data["status"], (
                data["buyTx"],
                data["burnTx"],
                data["finalBountyAmount"],
            )
            return res
        except Exception as e:
            self._logger.error(
                f"Error in InfoService.check_status(): {e}", exc_info=True
            )
            return "error", str(e)

    async def withdraw(self, chain: str, toAddress: str, userId: int):
        url = self.helper_url + "/withdraw"
        query = {"chain": chain, "toAddress": toAddress, "userId": userId}
        success, res = await self.process_request(url, query=query)
        if not success:
            self._logger.error(f"Info Withdraw: {res}")
            return False, res
        tx_hash = res["txHash"]
        return True, tx_hash

    async def validate_purchase(
        self,
        user_id: int,
        value: float,
        chain: str,
        promo_code: str = None,
        payout_value: float = None,
        token_id: int = None,
        trendingId: int = None,
        volume_bot=0,
        status: Literal["normal", "volume", "holder"] = "normal",
        hours=None,
        base_amount: float = 0.01,
        **kwargs,
    ):
        url = self.helper_url + "/trendingslot/verify"
        body = {
            "chain": chain,
            "value": value,
            "userId": user_id,
            "promoCode": promo_code,
            "payoutValue": payout_value,
            "tokenId": token_id,
            "trendingId": trendingId,
            "volumeBot": 1 if status == "holder" else volume_bot,
            "status": status,
            "hours": hours,
            "baseAmount": base_amount,
        }

        # Add any additional key-value arguments to the body
        body.update(kwargs)

        success, res = await self.process_request(url, body, "POST")
        if not success:
            self._logger.error(f"Info validate_purchase: {res}")
            return -1, res

        code = int(res["code"])
        message = res["message"] if code == 0 else res["error"]

        return code, message

    async def get_token_info(self, address: str, chain: str):
        url = self.info_url + "/info/tokeninfo"
        body = {"address": address, "chain": chain}
        success, res = await self.process_request(url, body=body, method="POST")
        if not success:
            self._logger.error(f"get_token_info: {res}")
            return None

        code = int(res["code"])
        if code == 0:
            self._logger.debug(f"get_token_info: {res['data']}")
            return res["data"]

    async def get_launchpad_data(self, launchpad: LaunchPad, address: str):
        url = self.info_url + f"/{launchpad.info_route}"
        body = {"address": address, "chatId": 0}
        success, res = await self.process_request(url, body=body, method="POST")
        if not success:
            self._logger.error(f"get {launchpad.name} info: {res}")
            return None

        code = int(res["code"])
        self._logger.debug(f"get_launchpad_data: {res['data']}")
        if code == 0:
            return LaunchpadToken.create_token_info(res["data"])

    async def get_fees(self, address: str):
        try:
            url = self.helper_url + f"/getFees"
            body = {"address": address}
            success, res = await self.process_request(url, body=body, method="POST")
            if not success:
                self._logger.error(f"get_fees info for address {address}: {res}")
                return None
            self._logger.debug(f"get_fees: {res}")
            return round(float(res.get("fee", 1)), 2)
        except Exception as e:
            self._logger.error(f"Error in InfoService.get_fees(): {e}", exc_info=True)
            return 1

    async def send_message(self, chat_id: int, message: str, thread_id: str = None):
        url = self.helper_url + "/sendtrendingmessage"
        body = {
            "chat_id": chat_id,
            "text": message,
            "thread_id": thread_id,
        }
        success, res = await self.process_request(url, body=body, method="POST")
        if not success:
            self._logger.error(f"send_message: {res}")
            return False, res
        return True, res

    async def edit_message(
        self, chat_id: int, message_id: int, message: str, thread_id: str = None
    ):
        url = self.helper_url + "/sendtrendingmessage"
        body = {
            "chat_id": chat_id,
            "msg_id": message_id,
            "text": message,
            "thread_id": thread_id,
        }

        success, res = await self.process_request(url, body=body, method="POST")
        if not success:
            self._logger.error(f"edit_message: {res}")
            return False, res
        return True, res

    async def check_rate_limit(
        self,
        chat_id: Optional[int] = None,
        priority: Literal["high", "normal", "low"] = "normal",
    ):
        url = self.helper_url + "/check-rate-limit"
        body = {
            "chat_id": chat_id,
            "priority": priority,
        }
        success, res = await self.process_request(url, body=body, method="POST")
        if not success:
            self._logger.error(f"check_rate_limit: {res}")
            return 0
        delay = int(res.get("delay_ms", 0)) / 1000.0
        return delay
