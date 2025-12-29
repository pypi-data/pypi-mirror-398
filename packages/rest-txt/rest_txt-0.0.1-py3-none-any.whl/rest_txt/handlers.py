
import uuid

# https://werkzeug.palletsprojects.com/en/stable/

from werkzeug.exceptions import BadRequest, NotFound, NotImplemented
from werkzeug.wrappers import Request, Response

from rest_txt.db.text import TextStorage
from rest_txt._util import get_content, parse_id


def _handle_delete(req: Request, txts: TextStorage):
	target_id = parse_id(req)

	txts.tx_begin()

	if txts.has_entry(target_id):
		txts.delete_entry(target_id)
		txts.tx_commit()

		return Response(status=204)
	else:
		txts.tx_commit()
		return Response(status=404)


def _handle_get(req: Request, txts: TextStorage):
	target_id = parse_id(req)

	result = txts.read_entry(target_id)

	if result is None:
		raise NotFound

	content, lastmod = result

	res = Response(
		content,
		mimetype='text/plain'
	)
	res.last_modified = lastmod

	return res


def _handle_head(req: Request, txts: TextStorage):
	target_id = parse_id(req)

	result = txts.entry_info(target_id)

	if result is None:
		raise NotFound

	length, lastmod = result

	res = Response()
	res.content_length = length
	res.last_modified = lastmod

	return res


def _handle_post(req: Request, txts: TextStorage):
	if req.environ['RAW_URI'] != '/':
		raise BadRequest

	content = get_content(req)
	entry_id = str(uuid.uuid4())

	txts.tx_begin()
	txts.create_entry(entry_id, content)
	txts.tx_commit()

	return Response(entry_id, status=201)


def _handle_put(req: Request, txts: TextStorage):
	target_id = parse_id(req)
	content = get_content(req)

	txts.tx_begin()

	if txts.has_entry(target_id):
		txts.update_entry(target_id, content)
		txts.tx_commit()

		return Response(status=204)
	else:
		txts.create_entry(target_id, content)
		txts.tx_commit()

		return Response(status=201)


_idem = dict()
_idem['DELETE'] = _handle_delete
_idem['GET'] = _handle_get
_idem['HEAD'] = _handle_head
_idem['POST'] = _handle_post
_idem['PUT'] = _handle_put


def get_handler(req: Request):
	try:
		handler = _idem[req.method]
	except:
		raise NotImplemented

	return handler

