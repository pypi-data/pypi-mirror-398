# -*- coding: utf-8 -*-

from idioma.base_gtoken import BaseTokenAcquirer


class TokenAcquirer(BaseTokenAcquirer):
    def _update(self):
        """update tkk
        """
        if not self._get_current_time():
            return

        r = self.client.get(self.host)

        self._set_tkk_from_response(r)

    def do(self, text):
        self._update()
        tk = self.acquire(text)
        return tk
