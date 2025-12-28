from litestar import Controller, get
import msgspec

from auth.guards import is_debug_guard


class E2EActivateCodeSchemeResponse(msgspec.Struct):
    code: str

class E2EController(Controller):
    guards = [is_debug_guard]
    path = "e2e"

    @get('/activate-code')
    async def get_activate_code(self) -> E2EActivateCodeSchemeResponse:
        return E2EActivateCodeSchemeResponse(code='super code')
