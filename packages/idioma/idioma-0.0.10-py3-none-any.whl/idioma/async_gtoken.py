# -*- coding: utf-8 -*-

from idioma.base_gtoken import BaseTokenAcquirer


class AsyncTokenAcquirer(BaseTokenAcquirer):
    async def _update(self):
        """update tkk
        """
        if not self._get_current_time():
            return

        r = await self.client.get(self.host)

        self._set_tkk_from_response(r)

    async def do(self, text):
        await self._update()
        tk = self.acquire(text)
        return tk
