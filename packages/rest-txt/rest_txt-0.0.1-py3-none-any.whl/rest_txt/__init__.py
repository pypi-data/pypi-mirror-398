
from time import monotonic_ns
import traceback

# https://werkzeug.palletsprojects.com/en/stable/

from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import InternalServerError
from werkzeug.wrappers import Request, Response

from rest_txt import config
from rest_txt.db import text as dtl
from rest_txt.db.text import TextStorage
from rest_txt.handlers import get_handler


_db_path = f'{config.DATA_DIR}/idem.db'

_txts = TextStorage(_db_path)
dtl._init(_txts)
_txts.close()
del _txts


@Request.application
def app(req: Request):
	try:
		handler = get_handler(req)

		txts = TextStorage(_db_path)

		tic = monotonic_ns()
		res: Response = handler(req, txts)
		toc = monotonic_ns()

		txts.close()

		delta_ms = (toc - tic) / 1_000_000
		res.headers.set('Server-Timing', f'handling;dur={delta_ms:.2f}')
		return res
	except Exception as exc:
		if isinstance(exc, HTTPException):
			raise

		traceback.print_exc()

		raise InternalServerError

