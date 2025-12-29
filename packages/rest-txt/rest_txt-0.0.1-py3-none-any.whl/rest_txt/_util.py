
from werkzeug.exceptions import BadRequest
from werkzeug.wrappers import Request


def get_content(req: Request):
	if req.mimetype != 'text/plain':
		raise BadRequest('MIME type (via the Content-Type header) must be text/plain')

	content = req.data

	if len(content) == 0:
		raise BadRequest('request body must not be empty')

	try:
		content.decode('utf_8')
	except:
		raise BadRequest('request body must be valid UTF-8')

	return content


def parse_id(req: Request):
	if '?' in req.environ['RAW_URI']:
		raise BadRequest('URL must not contain a query')

	id_str = req.path

	if len(id_str) < 2:
		raise BadRequest('identifier must not be empty')

	if id_str[0] != '/':
		raise BadRequest

	return id_str[1:]


