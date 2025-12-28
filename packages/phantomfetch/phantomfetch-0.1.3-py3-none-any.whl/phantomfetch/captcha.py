import asyncio
import logging
from typing import TYPE_CHECKING, Protocol

import httpx

if TYPE_CHECKING:
    from playwright.async_api import Page

    from .types import Action

logger = logging.getLogger(__name__)


class CaptchaSolver(Protocol):
    async def solve(self, page: "Page", action: "Action") -> str | None:
        """
        Solve a CAPTCHA on the page.

        Args:
            page: Playwright page instance
            action: Action configuration containing API key etc.

        Returns:
            Solution token if successful, None otherwise
        """
        ...

    async def detect(self, page: "Page") -> str | None:
        """
        Detect presence of a CAPTCHA.

        Returns:
            Type of CAPTCHA detected (e.g. "recaptcha", "hcaptcha") or None
        """
        ...


class TwoCaptchaSolver:
    """
    Solver using 2Captcha API.
    """

    API_URL = "http://2captcha.com/in.php"
    RES_URL = "http://2captcha.com/res.php"

    async def solve(self, page: "Page", action: "Action") -> str | None:
        if not action.api_key:
            logger.error("[captcha] No API key provided for 2Captcha")
            return None

        captcha_type = await self.detect(page)
        if not captcha_type:
            logger.info("[captcha] No supported CAPTCHA detected")
            return None

        sitekey = await self._get_sitekey(page, captcha_type)
        if not sitekey:
            logger.error(f"[captcha] Could not find sitekey for {captcha_type}")
            return None

        logger.info(
            f"[captcha] Solving {captcha_type} with 2Captcha (key={sitekey[:5]}...)"
        )

        try:
            async with httpx.AsyncClient() as client:
                # 1. Submit request
                params = {
                    "key": action.api_key,
                    "method": "userrecaptcha",  # Default to reCaptcha fallback
                    "googlekey": sitekey,
                    "pageurl": page.url,
                    "json": 1,
                }

                if captcha_type == "hcaptcha":
                    params["method"] = "hcaptcha"
                elif captcha_type == "turnstile":
                    params["method"] = "turnstile"

                resp = await client.post(self.API_URL, params=params)
                data = resp.json()

                if data.get("status") != 1:
                    logger.error(f"[captcha] Submission failed: {data}")
                    return None

                request_id = data["request"]

                # 2. Poll for result
                for _ in range(30):  # Wait up to 150s
                    await asyncio.sleep(5)
                    resp = await client.get(
                        self.RES_URL,
                        params={
                            "key": action.api_key,
                            "action": "get",
                            "id": request_id,
                            "json": 1,
                        },
                    )
                    data = resp.json()

                    if data.get("status") == 1:
                        token = data["request"]
                        logger.info("[captcha] Solved successfully")
                        await self._inject_token(page, token, captcha_type)
                        return token

                    if data.get("request") != "CAPCHA_NOT_READY":
                        logger.error(f"[captcha] Error polling: {data}")
                        return None

                logger.error("[captcha] Timed out waiting for solution")
                return None
        except Exception as e:
            logger.error(f"[captcha] Error: {e}")
            return None

    async def detect(self, page: "Page") -> str | None:
        if await page.locator(".g-recaptcha").count() > 0:
            return "recaptcha"
        if await page.locator("[data-sitekey]").count() > 0:
            # Could be hcaptcha or recaptcha
            if await page.locator('iframe[src*="hcaptcha"]').count() > 0:
                return "hcaptcha"
            return "recaptcha"
        if await page.locator(".cf-turnstile").count() > 0:
            return "turnstile"
        return None

    async def _get_sitekey(self, page: "Page", captcha_type: str) -> str | None:
        try:
            if captcha_type == "recaptcha":
                el = page.locator(".g-recaptcha").first
                return await el.get_attribute("data-sitekey")
            elif captcha_type == "hcaptcha":
                # hCaptcha often puts sitekey on a div with class h-captcha or data-sitekey
                el = page.locator("[data-sitekey]").first
                return await el.get_attribute("data-sitekey")
            elif captcha_type == "turnstile":
                el = page.locator(".cf-turnstile").first
                return await el.get_attribute("data-sitekey")
        except Exception:
            pass
        return None

    async def _inject_token(self, page: "Page", token: str, captcha_type: str) -> None:
        """Inject token into the form."""
        if captcha_type == "recaptcha":
            await page.evaluate(
                f'document.getElementById("g-recaptcha-response").innerHTML="{token}";'
            )
            # Try to find callback
            # This is tricky without knowing specific page implementation
        elif captcha_type == "hcaptcha":
            await page.evaluate(
                f'document.querySelector("[name=h-captcha-response]").innerHTML="{token}";'
            )
            await page.evaluate(
                f'document.querySelector("[name=g-recaptcha-response]").innerHTML="{token}";'
            )
        elif captcha_type == "turnstile":
            await page.evaluate(
                f'document.querySelector("[name=cf-turnstile-response]").value="{token}";'
            )
