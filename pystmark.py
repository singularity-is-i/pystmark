# -*- coding: ascii -*-

'''
    pystmark
    --------

    Postmark API library built on :mod:`requests`

    :copyright: 2013, see AUTHORS for more details
    :license: MIT, see LICENSE for more details

    :TODO:
        Support for bounce and inbound hooks? These should be mostly handled
        in a framework specific manner but there might be some common utilities
        to provide.
        Optionally verify attachment size <=10MB
        Wrapper class for PystMessage attachments and headers?
'''

from collections import Mapping
from base64 import b64encode
import requests
import mimetypes
import os.path
import sys
if sys.version_info[0] >= 3:
    from urllib.parse import urljoin
    basestring = str
    iteritems = dict.items
else:
    from urlparse import urljoin
    iteritems = dict.iteritems

try:
    import simplejson as json
except ImportError:
    import json


__title__ = 'pystmark'
__version__ = '0.2'
__license__ = 'MIT'

# Constant defined in the Postmark docs:
#   http://developer.postmarkapp.com/developer-build.html
POSTMARK_API_URL = 'http://api.postmarkapp.com/'
POSTMARK_API_URL_SECURE = 'https://api.postmarkapp.com/'
POSTMARK_API_TEST_KEY = 'POSTMARK_API_TEST'
MAX_RECIPIENTS_PER_MESSAGE = 20
MAX_BATCH_MESSAGES = 500

bounce_types = {
    'HardBounce': 1,
    'Transient': 2,
    'Unsubscribe': 16,
    'Subscribe': 32,
    'AutoResponder': 64,
    'AddressChange': 128,
    'DnsError': 256,
    'SpamNotification': 512,
    'OpenRelayTest': 1024,
    'Unknown': 2048,
    'SoftBounce': 4096,
    'VirusNotification': 8192,
    'ChallengeVerification': 16384,
    'BadEmailAddress': 100000,
    'SpamComplaint': 100001,
    'ManuallyDeactivated': 100002,
    'Unconfirmed': 100003,
    'Blocked': 100006,
    'SMTPApiError': 100007,
    'InboundError': 100008
}


''' Simple API '''


def send(message, api_key=None, secure=None, test=None, **request_args):
    '''Send a message.

    :param message: Message to send.
    :type message: `dict` or :class:`PystMessage`
    :param api_key: Your Postmark API key. Required, if `test` is not `True`.
    :param secure: Use the https scheme for the Postmark API.
        Defaults to `True`
    :param test: Use the Postmark Test API. Defaults to `False`.
    :param \*\*request_args: Keyword arguments to pass to
        :func:`requests.request`.
    :rtype: :class:`PystSendResponse`
    '''
    return _default_pyst_sender.send(message=message, api_key=api_key,
                                     secure=secure, test=test, **request_args)


def send_batch(messages, api_key=None, secure=None, test=None, **request_args):
    '''Send a batch of messages.

    :param messages: Messages to send.
    :type message: A list of `dict` or :class:`PystMessage`
    :param api_key: Your Postmark API key. Required, if `test` is not `True`.
    :param secure: Use the https scheme for the Postmark API.
        Defaults to `True`
    :param test: Use the Postmark Test API. Defaults to `False`.
    :param \*\*request_args: Keyword arguments to pass to
        :func:`requests.request`.
    :rtype: :class:`PystBatchSendResponse`
    '''
    return _default_pyst_batch_sender.send(messages=messages, api_key=api_key,
                                           secure=secure, test=test,
                                           **request_args)


def get_delivery_stats(api_key=None, secure=None, test=None, **request_args):
    '''Get delivery stats for your Postmark account.

    :param api_key: Your Postmark API key. Required, if `test` is not `True`.
    :param secure: Use the https scheme for the Postmark API.
        Defaults to `True`
    :param test: Use the Postmark Test API. Defaults to `False`.
    :param \*\*request_args: Keyword arguments to pass to
        :func:`requests.request`.
    :rtype: :class:`PystDeliveryStatsResponse`
    '''
    return _default_delivery_stats.get(api_key=api_key, secure=secure,
                                       test=test, **request_args)


def get_bounces(api_key=None, secure=None, test=None, **request_args):
    '''Get a paginated list of bounces.

    :param api_key: Your Postmark API key. Required, if `test` is not `True`.
    :param secure: Use the https scheme for the Postmark API.
        Defaults to `True`
    :param test: Use the Postmark Test API. Defaults to `False`.
    :param \*\*request_args: Keyword arguments to pass to
        :func:`requests.request`.
    :rtype: :class:`PystBouncesResponse`
    '''
    return _default_bounces.get(api_key=api_key, secure=secure,
                                test=test, **request_args)


def get_bounce(bounce_id, api_key=None, secure=None, test=None,
               **request_args):
    '''Get a single bounce.

    :param bounce_id: The bounce's id. Get the id with :func:`get_bounces`.
    :param api_key: Your Postmark API key. Required, if `test` is not `True`.
    :param secure: Use the https scheme for the Postmark API.
        Defaults to `True`
    :param test: Use the Postmark Test API. Defaults to `False`.
    :param \*\*request_args: Keyword arguments to pass to
        :func:`requests.request`.
    :rtype: :class:`PystBounceResponse`
    '''
    return _default_bounce.get(bounce_id, api_key=api_key, secure=secure,
                               test=test, **request_args)


def get_bounce_dump(bounce_id, api_key=None, secure=None, test=None,
                    **request_args):
    '''Get the raw email dump for a single bounce.

    :param bounce_id: The bounce's id. Get the id with :func:`get_bounces`.
    :param api_key: Your Postmark API key. Required, if `test` is not `True`.
    :param secure: Use the https scheme for the Postmark API.
        Defaults to `True`
    :param test: Use the Postmark Test API. Defaults to `False`.
    :param \*\*request_args: Keyword arguments to pass to
        :func:`requests.request`.
    :rtype: :class:`PystBounceDumpResponse`
    '''
    return _default_bounce_dump.get(bounce_id, api_key=api_key, secure=secure,
                                    test=test, **request_args)


def get_bounce_tags(api_key=None, secure=None, test=None, **request_args):
    '''Get a list of tags for bounces associated with your Postmark server.

    :param api_key: Your Postmark API key. Required, if `test` is not `True`.
    :param secure: Use the https scheme for the Postmark API.
        Defaults to `True`
    :param test: Use the Postmark Test API. Defaults to `False`.
    :param \*\*request_args: Keyword arguments to pass to
        :func:`requests.request`.
    :rtype: :class:`PystBounceTagsResponse`
    '''
    return _default_bounce_tags.get(api_key=api_key, secure=secure, test=test,
                                    **request_args)


def activate_bounce(bounce_id, api_key=None, secure=None, test=None,
                    **request_args):
    '''Activate a deactivated bounce.

    :param bounce_id: The bounce's id. Get the id with :func:`get_bounces`.
    :param api_key: Your Postmark API key. Required, if `test` is not `True`.
    :param secure: Use the https scheme for the Postmark API.
        Defaults to `True`
    :param test: Use the Postmark Test API. Defaults to `False`.
    :param \*\*request_args: Keyword arguments to pass to
        :func:`requests.request`.
    :rtype: :class:`PystBounceActivateResponse`
    '''
    return _default_bounce_activate.activate(bounce_id, api_key=api_key,
                                             secure=secure, test=test,
                                             **request_args)


''' Messages '''


class PystMessage(object):
    ''' A container for message(s) to send to the Postmark API.
    You can populate this message with defaults for initializing a
    :class:`PystInterface`. The message will be combined with the final message
    and verified before transmission.

    :param sender: Email address of the sender.
    :param to: Destination email address.
    :param cc: A list of cc'd email addresses.
    :param bcc: A list of bcc'd email address.
    :param subject: The message subject.
    :param tag: Tag your emails with this.
    :param html: HTML body content.
    :param text: Text body content.
    :param reply_to: Email address to reply to.
    :param headers: Additional headers to include with the email. If you do
        not have the headers formatted for the Postmark API, use
        :meth:`PystMessage.add_header`.
    :type headers: A list of `dict`, each with the keys 'Name' and
        'Value'.
    :param attachments: Attachments to include with the email. If you do not
        have the attachments formatted for the Postmark API, use
        :meth:`PystMessage.attach_file` or :meth:`PystMessage.attach_binary`.
    :type attachments: A list of `dict`, each with the keys 'Name',
        'Content' and 'ContentType'.
    :param verify: Verify the message when initialized.
        Defaults to `False`.
    '''

    _fields = {
        'to': 'To',
        'sender': 'From',
        'cc': 'Cc',
        'bcc': 'Bcc',
        'subject': 'Subject',
        'tag': 'Tag',
        'html': 'HtmlBody',
        'text': 'TextBody',
        'reply_to': 'ReplyTo',
        'headers': 'Headers',
        'attachments': 'Attachments',
    }

    _allowed_extensions = ['gif', 'jpeg', 'png', 'swf', 'dcr', 'tiff', 'bmp',
                           'ico', 'page-icon', 'wav', 'mp3', 'flv', 'avi',
                           'mpg', 'wmv', 'rm', 'mov', '3gp', 'mp4', 'm4a',
                           'ogv', 'txt', 'rtf', 'html', 'xml', 'ics', 'pdf',
                           'log', 'csv', 'docx', 'dotx', 'pptx', 'xlsx', 'odt',
                           'psd', 'ai', 'vcf', 'mobi', 'epub', 'pgp', 'ods',
                           'wps', 'pages', 'prn', 'eps', 'license', 'zip',
                           'dcm', 'enc', 'cdr', 'css', 'pst', 'mobileconfig',
                           'eml', 'gpx', 'kml', 'kmz', 'msl', 'rb', 'js',
                           'java', 'c', 'cpp', 'py', 'php', 'fl', 'jar', 'ttf',
                           'vpv', 'iif', 'timo', 'autorit', 'cathodelicense',
                           'itn', 'freshroute']

    _to = None
    _cc = None
    _bcc = None
    _default_content_type = 'application/octet-stream'

    def __init__(self, sender=None, to=None, cc=None, bcc=None, subject=None,
                 tag=None, html=None, text=None, reply_to=None, headers=None,
                 attachments=None, verify=False):
        self.sender = sender
        self.to = to
        self.cc = cc
        self.bcc = bcc
        self.subject = subject
        self.tag = tag
        self.html = html
        self.text = text
        self.reply_to = reply_to
        self.headers = headers
        self.attachments = attachments
        if verify:
            self.verify()

    def data(self):
        '''Returns data formatted for a POST request to the Postmark send API.

        :rtype: `dict`
        '''
        d = {}
        for val, key in self._fields.items():
            val = getattr(self, val)
            if val is not None:
                d[key] = val
        return d

    def json(self):
        '''Return json-encoded string of message data.

        :rtype: `unicode`
        '''
        return json.dumps(self.data(), ensure_ascii=False)

    @classmethod
    def load_message(self, message, **kwargs):
        '''Create a :class:`PystMessage` from a message data `dict`.

        :param message: A `dict` of message data.
        :param \*\*kwargs: Additional keyword arguments to construct
            :class:`PystMessage` with.
        :rtype: :class:`PystMessage`
        '''
        kwargs.update(message)
        message = kwargs
        try:
            message = PystMessage(**message)
        except TypeError as e:
            message = self._convert_postmark_to_native(kwargs)
            if message:
                message = PystMessage(**message)
            else:
                raise e
        return message

    def load_from(self, other, **kwargs):
        '''Create a :class:`PystMessage` by merging `other` with `self`.
        Values from `other` will be copied to `self` if the value was not
        set on `self` and is set on `other`.

        :param other: The :class:`PystMessage` to copy defaults from.
        :type other: :class:`PystMessage`
        :param \*\*kwargs: Additional keyword arguments to construct
            :class:`PystMessage` with.
        :rtype: :class:`PystMessage`
        '''
        data = self.data()
        other_data = other.data()
        for k, v in iteritems(other_data):
            if data.get(k) is None:
                data[k] = v
        return self.load_message(data, **kwargs)

    def add_header(self, name, value):
        '''Attach an email header to send with the message.

        :param name: The name of the header value.
        :param value: The header value.
        '''
        if self.headers is None:
            self.headers = []
        self.headers.append(dict(Name=name, Value=value))

    def attach_binary(self, data, filename, content_type=None):
        '''Attach a file to the message given raw binary data.

        :param data: Raw data to attach to the message.
        :param filename: Name of the file for the data.
        :param content_type: mimetype of the data. It will be guessed from the
            filename if not provided.
        '''
        if self.attachments is None:
            self.attachments = []
        if content_type is None:
            content_type = self._detect_content_type(filename)
        attachment = {
            'Name': filename,
            'Content': b64encode(data).decode('utf-8'),
            'ContentType': content_type
        }
        self.attachments.append(attachment)

    def attach_file(self, filename, content_type=None):
        '''Attach a file to the message given a filename.

        :param filename: Name of the file to attach.
        :param content_type: mimetype of the data. It will be guessed from the
            filename if not provided.
        '''
        # Open the file, grab the filename, detect content type
        name = os.path.basename(filename)
        if not name:
            err = 'Filename not found in path: {0}'
            raise PystMessageError(err.format(filename))
        with open(filename, 'rb') as f:
            data = f.read()
        self.attach_binary(data, name, content_type=content_type)

    def verify(self):
        '''Verifies the message data based on rules and restrictions defined
        in the Postmark API docs.  There can be no more than 20 recipients
        in total. NOTE: This does not check that your attachments total less
        than 10MB, you must do that yourself.
        '''
        if self.to is None:
            raise PystMessageError('"to" is required')
        if self.html is None and self.text is None:
            err = 'At least one of "html" or "text" must be provided'
            raise PystMessageError(err)
        self._verify_headers()
        self._verify_attachments()
        if (MAX_RECIPIENTS_PER_MESSAGE and
                len(self.recipients) > MAX_RECIPIENTS_PER_MESSAGE):
            err = 'No more than {0} recipients accepted.'
            raise PystMessageError(err.format(MAX_RECIPIENTS_PER_MESSAGE))

    @property
    def recipients(self):
        '''A list of all recipients for this message.
        '''
        cc = self._cc or []
        bcc = self._bcc or []
        return self._to + cc + bcc

    @property
    def to(self):
        '''A comma delimited string of receivers for the message 'To'
        field.
        '''
        if self._to is not None:
            return ','.join(self._to)

    @to.setter
    def to(self, to):
        '''
        :param to: Email addresses for the 'To' API field.
        :type to: :keyword:`list` or `str`
        '''
        if isinstance(to, basestring):
            to = to.split(',')
        self._to = to

    @property
    def cc(self):
        '''A comma delimited string of receivers for the message 'Cc'
        field.
        '''
        if self._cc is not None:
            return ','.join(self._cc)

    @cc.setter
    def cc(self, cc):
        '''
        :param cc: Email addresses for the 'Cc' API field.
        :type cc: :keyword:`list` or `str`
        '''
        if isinstance(cc, basestring):
            cc = cc.split(',')
        self._cc = cc

    @property
    def bcc(self):
        '''A comma delimited string of receivers for the message 'Bcc'
        field.
        '''
        if self._bcc is not None:
            return ','.join(self._bcc)

    @bcc.setter
    def bcc(self, bcc):
        '''
        :param bcc: Email addresses for the 'Bcc' API field.
        :type bcc: :keyword:`list` or `str`
        '''
        if isinstance(bcc, basestring):
            bcc = bcc.split(',')
        self._bcc = bcc

    @classmethod
    def _convert_postmark_to_native(cls, message):
        '''Converts Postmark message API field names to their corresponding
        :class:`PystMessage` attribute names.

        :param message: Postmark message data, with API fields using Postmark
            API names.
        :type message: `dict`
        '''
        d = {}
        for dest, src in cls._fields.items():
            if src in message:
                d[dest] = message[src]
        return d

    def _detect_content_type(self, filename):
        '''Determine the mimetype for a file.

        :param filename: Filename of file to detect.
        '''
        name, ext = os.path.splitext(filename)
        if not ext:
            raise PystMessageError('File requires an extension.')
        ext = ext.lower()
        if ext.lstrip('.') not in self._allowed_extensions:
            err = 'Extension "{0}" is not allowed.'
            raise PystMessageError(err.format(ext))
        if not mimetypes.inited:
            mimetypes.init()
        try:
            mimetype = mimetypes.types_map[ext]
        except KeyError:
            mimetype = self._default_content_type
        return mimetype

    def _verify_headers(self):
        '''Verify that header values match the format expected by the Postmark
        API.
        '''
        if self.headers is None:
            return
        self._verify_dict_list(self.headers, ('Name', 'Value'), 'Header')

    def _verify_attachments(self):
        '''Verify that attachment values match the format expected by the
        Postmark API.
        '''
        if self.attachments is None:
            return
        keys = ('Name', 'Content', 'ContentType')
        self._verify_dict_list(self.attachments, keys, 'Attachment')

    def _verify_dict_list(self, values, keys, name):
        '''Validate a list of `dict`, ensuring it has specific keys
        and no others.

        :param values: A list of `dict` to validate.
        :param keys: A list of keys to validate each `dict` against.
        :param name: Name describing the values, to show in error messages.
        '''
        keys = set(keys)
        name = name.title()
        for value in values:
            if not isinstance(value, Mapping):
                raise PystMessageError('Invalid {0} value'.format(name))
            for key in keys:
                if key not in value:
                    err = '{0} must contain "{1}"'
                    raise PystMessageError(err.format(name, key))
            if set(value) - keys:
                err = '{0} must contain only {1}'
                words = ['"{0}"'.format(r) for r in sorted(keys)]
                words = ' and '.join(words)
                raise PystMessageError(err.format(name, words))

    def __eq__(self, other):
        '''If comparing to a `dict`, convert to a :class:`PystMessage`
        then compare data fields.
        '''
        if isinstance(other, Mapping):
            other = self.__class__.load_message(other)
        return self.data() == other.data()

    def __ne__(self, other):
        return not self.__eq__(other)


class PystBouncedMessage(object):
    '''Bounced message data wrapper.

    :param bounce_data: Raw bounced message data retrieved from
        :class:`PystBounce` or :class:`PystBounces`.
    :param sender: The :class:`PystInterface` that made the request for the
        bounce data. Defaults to `None`.
    '''
    def __init__(self, bounce_data, sender=None):
        self._data = bounce_data
        self._sender = sender
        self.id = bounce_data['ID']
        self.type = bounce_data['Type']
        self.message_id = bounce_data['MessageID']
        self.type_code = bounce_data['TypeCode']
        self.details = bounce_data['Details']
        self.email = bounce_data['Email']
        self.bounced_at = bounce_data['BouncedAt']
        self.dump_available = bounce_data['DumpAvailable']
        self.inactive = bounce_data['Inactive']
        self.can_activate = bounce_data['CanActivate']
        self.content = bounce_data.get('Content')
        self.subject = bounce_data['Subject']

    def dump(self, sender=None, **kwargs):
        '''Retrieve raw email dump for this bounce.

        :param sender: A :class:`PystBounceDump` object to get dump with.
            Defaults to `None`.
        :param \*\*kwargs: Keyword arguments passed to
            :func:`requests.request`.
        '''
        if sender is None:
            if self._sender is None:
                sender = _default_bounce_dump
            else:
                sender = PystBounceDump(api_key=self._sender.api_key,
                                        test=self._sender.test,
                                        secure=self._sender.secure)
        return sender.get(self.id, **kwargs)


class PystMessageConfirmation(object):
    '''Wrapper around data returned from Postmark after sending

    :param data: Data returned from Postmark upon sending a message
    '''

    def __init__(self, data):
        self._data = data
        self.error_code = data.get('ErrorCode', 0)
        self.message = data.get('Message', 'OK')
        self.id = data.get('MessageID', '')
        self.submitted_at = data.get('SubmittedAt', '')
        # TODO -- find out if 'To' is returned comma delimited list of
        # emails when sent that way
        self.to = data.get('To', '')


class PystBounceTypeData(object):
    '''Bounce type data wrapper.

    :param bounce_type_data: Raw bounce type data retrieved from
        :class:`PystDeliveryStats`.
    '''
    def __init__(self, bounce_type_data):
        self.count = bounce_type_data.get('Count', 0)
        self.name = bounce_type_data['Name']
        self.type = bounce_type_data.get('Type', 'All')


''' Response Wrappers '''


class PystResponse(object):
    '''Base class for API response wrappers. The wrapped
    :class:`requests.Response` object interface is exposed by this class,
    unless the attribute is defined in `self._attrs`.

    :param response: Response returned from :func:`requests.request`.
    :type response: :class:`requests.Response`
    :param sender: The API interface wrapper that generated the request.
        Defaults to `None`.
    :type sender: :class:`PystInterface`
    '''
    _attrs = []

    def __init__(self, response, sender=None):
        attrs = self._attrs
        attrs += ['sender', '_data']
        self._attrs = list(set(attrs))
        self.sender = sender
        try:
            self._data = response.json()
        except ValueError:
            self._data = None
        self._requests_response = response

    def __getattribute__(self, k):
        '''Gets attribute from `self` if attribute key is in `self._attrs`,
        else get it from the wrapped :class:`requests.Response`.
        '''
        if k == '_attrs' or k in object.__getattribute__(self, '_attrs'):
            return object.__getattribute__(self, k)
        r = object.__getattribute__(self, '_requests_response')
        if k == '_requests_response':
            return r
        return r.__getattribute__(k)

    def __setattr__(self, k, v):
        '''Sets attribute on `self` if attribute key is in `self._attrs`,
        else sets it on the wrapped :class:`requests.Response`.
        '''
        if k in ['_attrs', '_requests_response'] or k in self._attrs:
            object.__setattr__(self, k, v)
        else:
            self._requests_response.__setattr__(k, v)

    def raise_for_status(self):
        '''Raise Postmark-specific HTTP errors. If there isn't one, the
        standard HTTP error is raised.

        HTTP 401 raises :class:`PystUnauthorizedError`

        HTTP 422 raises :class:`PystUnprocessableEntityError`

        HTTP 500 raises :class:`PystInternalServerError`
        '''
        if self.status_code == 401:
            raise PystUnauthorizedError(self._requests_response)
        elif self.status_code == 422:
            raise PystUnprocessableEntityError(self._requests_response)
        elif self.status_code == 500:
            raise PystInternalServerError(self._requests_response)
        return self._requests_response.raise_for_status()


class PystSendResponse(PystResponse):
    '''Wrapper around :func:`PystSender.send` and :func:`PystBatchSender.send`

    :param response: Response returned from :func:`requests.request`.
    :type response: :class:`requests.Response`
    :param sender: The API interface wrapper that generated the request.
        Defaults to `None`.
    :type sender: :class:`PystInterface`
    '''
    _attrs = ['message', 'raise_for_status']

    def __init__(self, response, sender=None):
        super(PystSendResponse, self).__init__(response, sender=sender)
        data = self._data or {}
        self.message = PystMessageConfirmation(data)


class PystBatchSendResponse(PystResponse):
    '''Wrapper around :func:`PystSender.send` and :func:`PystBatchSender.send`

    :param response: Response returned from :func:`requests.request`.
    :type response: :class:`requests.Response`
    :param sender: The API interface wrapper that generated the request.
        Defaults to `None`.
    :type sender: :class:`PystInterface`
    '''
    _attrs = ['messages', 'raise_for_status']

    def __init__(self, response, sender=None):
        super(PystBatchSendResponse, self).__init__(response, sender=sender)
        data = self._data or []
        self.messages = [PystMessageConfirmation(msg) for msg in data]


class PystBouncesResponse(PystResponse):
    '''Wrapper for responses from :func:`PystBounces.get`.

    :param response: Response returned from :func:`requests.request`.
    :type response: :class:`requests.Response`
    :param sender: The API interface wrapper that generated the request.
        Defaults to `None`.
    :type sender: :class:`PystInterface`
    '''
    _attrs = ['bounces', 'total']

    def __init__(self, response, sender=None):
        super(PystBouncesResponse, self).__init__(response, sender=sender)
        data = self._data or {}
        self.total = data.get('TotalCount', 0)
        bounces = data.get('Bounces', [])
        self.bounces = [PystBouncedMessage(bounce, sender=sender)
                        for bounce in bounces]


class PystBounceResponse(PystResponse):
    '''Wrapper for responses from :func:`PystBounce.get`.

    :param response: Response returned from :func:`requests.request`.
    :type response: :class:`requests.Response`
    :param sender: The API interface wrapper that generated the request.
        Defaults to `None`.
    :type sender: :class:`PystInterface`
    '''
    _attrs = ['bounce']

    def __init__(self, response, sender=None):
        super(PystBounceResponse, self).__init__(response, sender=sender)
        if self._data is None:
            self.bounce = None
        else:
            self.bounce = PystBouncedMessage(self._data, sender=sender)


class PystBounceDumpResponse(PystResponse):
    '''Wrapper for responses from :func:`PystBounceDump.get`.

    :param response: Response returned from :func:`requests.request`.
    :type response: :class:`requests.Response`
    :param sender: The API interface wrapper that generated the request.
        Defaults to `None`.
    :type sender: :class:`PystInterface`
    '''
    def __init__(self, response, sender=None):
        super(PystBounceDumpResponse, self).__init__(response, sender=sender)
        data = self._data or {}
        self.dump = data.get('Body')


class PystBounceTagsResponse(PystResponse):
    '''Wrapper for responses from :func:`PystBounceTags.get`.

    :param response: Response returned from :func:`requests.request`.
    :type response: :class:`requests.Response`
    :param sender: The API interface wrapper that generated the request.
        Defaults to `None`.
    :type sender: :class:`PystInterface`
    '''
    def __init__(self, response, sender=None):
        super(PystBounceTagsResponse, self).__init__(response, sender=sender)
        self.tags = self._data or []


class PystDeliveryStatsResponse(PystResponse):
    '''Wrapper for responses from :func:`PystBounceActivate.activate`.

    :param response: Response returned from :func:`requests.request`.
    :type response: :class:`requests.Response`
    :param sender: The API interface wrapper that generated the request.
        Defaults to `None`.
    :type sender: :class:`PystInterface`
    '''
    def __init__(self, response, sender=None):
        super(PystDeliveryStatsResponse, self).__init__(response,
                                                        sender=sender)
        data = self._data or {}
        self.inactive = data.get('InactiveMails', 0)
        self.total = 0
        bounces = data.get('Bounces', [])
        self.bounces = {}
        for bounce in bounces:
            bounce = PystBounceTypeData(bounce)
            self.bounces[bounce.type] = bounce
            if bounce.type == 'All':
                self.total = bounce.count


class PystBounceActivateResponse(PystResponse):
    '''Wrapper for responses from the bounce activate endpoint.

    :param response: Response returned from :func:`requests.request`.
    :type response: :class:`requests.Response`
    :param sender: The API interface wrapper that generated the request.
        Defaults to `None`.
    :type sender: :class:`PystInterface`
    '''
    def __init__(self, response, sender=None):
        super(PystBounceActivateResponse, self).__init__(response,
                                                         sender=sender)
        data = self._data or {}
        self.message = data.get('Message', '')
        bounce = data.get('Bounce')
        if bounce is None:
            self.bounce = None
        else:
            self.bounce = PystBouncedMessage(data['Bounce'], sender=sender)


''' Interfaces '''


class PystInterface(object):
    '''Base class interface for Postmark API endpoint wrappers

    :param api_key: Your Postmark API key. Defaults to `None`.
    :param secure: Use the https scheme for API requests.
        Defaults to `True`.
    :param test: Use the Postmark test API. Defaults to `False`.
    '''

    method = None
    endpoint = None
    response_class = PystResponse

    _headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    _api_key_header_name = 'X-Postmark-Server-Token'

    def __init__(self, api_key=None, secure=True, test=False):
        self.api_key = api_key
        self.secure = secure
        self.test = test

    def _request(self, url, **kwargs):
        '''Inner :func:`requests.request` wrapper.

        :param url: Endpoint url
        :param \*\*kwargs: Keyword arguments to pass to
            :func:`requests.request`.
        '''
        if self.method is None:
            raise NotImplementedError('method must be defined on a subclass')
        response = requests.request(self.method, url, **kwargs)
        return self.response_class(response, sender=self)

    def _get_api_url(self, secure=None, **formatters):
        '''Constructs Postmark API url

        :param secure: Use the https Postmark API.
        :param \*\*formatters: :func:`string.format` keyword arguments to
            format the url with.
        :rtype: Postmark API url
        '''
        if self.endpoint is None:
            raise NotImplementedError('endpoint must be defined on a subclass')
        if secure is None:
            secure = self.secure
        if secure:
            api_url = POSTMARK_API_URL_SECURE
        else:
            api_url = POSTMARK_API_URL
        url = urljoin(api_url, self.endpoint)
        if formatters:
            url = url.format(**formatters)
        return url

    def _get_headers(self, api_key=None, test=None, request_args=None):
        '''Constructs the headers to use for the request.

        :param api_key: Your Postmark API key. Defaults to `None`.
        :param test: Use the Postmark test API. Defaults to `self.test`.
        :param request_args: Keyword args to pass to :func:`requests.request`.
            Defaults to `None`.
        :rtype: `dict` of header values.
        '''
        if request_args is None:
            request_args = {}
        headers = request_args.pop('headers', {})
        if (test is None and self.test) or test:
            headers[self._api_key_header_name] = POSTMARK_API_TEST_KEY
        elif api_key is not None:
            headers[self._api_key_header_name] = api_key
        else:
            headers[self._api_key_header_name] = self.api_key
        headers.update(self._headers)
        if not headers.get(self._api_key_header_name):
            raise ValueError('Postmark API Key not provided')
        return headers


class PystGetInterface(PystInterface):
    '''Base interface class for Postmark API endpoints that use GET'''
    method = 'GET'

    def get(self, api_key=None, secure=None, test=None, **request_args):
        '''Make a GET request to the Postmark API

        :param api_key: Your Postmark API key.
        :param secure: Use the https scheme for Postmark API.
            Defaults to `True`
        :param test: Make a test request to the Postmark API.
            Defaults to `False`.
        :param \*\*request_args: Keyword arguments to pass to
            :func:`requests.request`.
        :rtype: :class:`PystResponse`
        '''
        url = self._get_api_url(secure=secure)
        headers = self._get_headers(api_key=api_key, test=test,
                                    request_args=request_args)
        return self._request(url, headers=headers, **request_args)


''' Send API '''


class PystSender(PystInterface):
    '''Sends a single message via the Postmark API.

    All of the arguments used in constructing this object are
    used as defaults in the final call to :meth:`PystSender.send`.
    You can override any of them at that time.

    :param message: Default message data, such as sender and reply_to.
    :type message: `dict` or :class:`PystMessage`
    :param api_key: Your Postmark API key.
    :param secure: Use the https scheme for Postmark API.
        Defaults to `True`
    :param test: Make a test request to the Postmark API.
        Defaults to `False`.
    '''

    method = 'POST'
    endpoint = '/email'
    response_class = PystSendResponse

    def __init__(self, message=None, api_key=None, secure=True, test=False):
        super(PystSender, self).__init__(api_key=api_key, secure=secure,
                                         test=test)
        self._load_initial_message(message=message)

    def send(self, message=None, api_key=None, secure=None, test=None,
             **request_args):
        '''Send request to Postmark API.
        Returns result of :func:`requests.post`.

        :param message: Your Postmark message data.
        :type message: `dict` or :class:`PystMessage`
        :param api_key: Your Postmark API key.
        :type api_key: `str`
        :param test: Make a test request to the Postmark API.
        :param secure: Use the https Postmark API.
        :param \*\*request_args: Passed to :func:`requests.post`
        :rtype: :class:`requests.Response`
        '''
        headers = self._get_headers(api_key=api_key, test=test,
                                    request_args=request_args)
        data = self._get_request_content(message)
        url = self._get_api_url(secure=secure)
        return self._request(url, data=data, headers=headers, **request_args)

    def _load_initial_message(self, message=None):
        '''Converts message to :class:`PystMessage` and sets it on `self`'''
        if message is None:
            message = PystMessage(verify=False)
        if isinstance(message, Mapping):
            message = PystMessage.load_message(message)
        self.message = message

    def _cast_message(self, message=None):
        '''Convert message data to :class:`PystMessage` if needed, and
        merge with the default message.

        :param message: Message to merge with the default message.
        :rtype: :class:`PystMessage`
        '''
        if message is None:
            message = {}
        if isinstance(message, Mapping):
            message = PystMessage.load_message(message)
        return message.load_from(self.message, verify=True)

    def _get_request_content(self, message=None):
        '''Updates message with default message paramaters.

        :param message: Postmark message data
        :type message: `dict`
        :rtype: JSON encoded `unicode`
        '''
        message = self._cast_message(message=message)
        return message.json()


class PystBatchSender(PystSender):
    '''Sends a batch of messages via the Postmark API.

    All of the arguments used in constructing this object are
    used as defaults in the final call to :meth:`PystBatchSender.send`.
    You can override any of them at that time.

    :param message: Default message data, such as sender and reply_to.
    :type message: `dict` or :class:`PystMessage`
    :param api_key: Your Postmark API key.
    :param secure: Use the https scheme for Postmark API.
        Defaults to `True`
    :param test: Make a test request to the Postmark API.
        Defaults to `False`.
    '''

    endpoint = '/email/batch'
    response_class = PystBatchSendResponse

    def send(self, messages=None, api_key=None, secure=None, test=None,
             **request_args):
        '''Send batch request to Postmark API.
        Returns result of :func:`requests.post`.

        :param messages: Batch messages to send to the Postmark API.
        :type messages: A list of :class:`PystMessage`
        :param api_key: Your Postmark API key. Defaults to `self.api_key`.
        :param test: Make a test request to the Postmark API.
            Defaults to `self.test`.
        :param secure: Use the https Postmark API. Defaults to `self.secure`.
        :param \*\*request_args: Passed to :func:`requests.request`
        :rtype: :class:`PystBatchSendResponse`
        '''
        return super(PystBatchSender, self).send(message=messages,
                                                 test=test,
                                                 api_key=api_key,
                                                 secure=secure,
                                                 **request_args)

    def _get_request_content(self, message=None):
        '''Updates all messages in message with default message
        parameters.

        :param message: A collection of Postmark message data
        :type message: a collection of message `dict`s
        :rtype: JSON encoded `unicode`
        '''
        if not message:
            raise PystMessageError('No messages to send.')
        if len(message) > MAX_BATCH_MESSAGES:
            err = 'Maximum {0} messages allowed in batch'
            raise PystMessageError(err.format(MAX_BATCH_MESSAGES))
        message = [self._cast_message(message=msg) for msg in message]
        message = [msg.data() for msg in message]
        return json.dumps(message, ensure_ascii=False)


''' Bounce API '''


class PystBounces(PystGetInterface):
    '''Multiple bounce retrieval endpoint wrapper.

    :param api_key: Your Postmark API key. Defaults to `None`.
    :param secure: Use the https scheme for Postmark API.
        Defaults to `True`.
    :param test: Make a test request to the Postmark API.
        Defaults to `False`.
    '''
    endpoint = '/bounces'
    response_class = PystBouncesResponse

    def __init__(self, api_key=None, secure=True, test=False):
        super(PystBounces, self).__init__(api_key=api_key, secure=secure,
                                          test=test)
        self._last_response = None

    def get(self, bounce_type=None, inactive=None, email_filter=None,
            message_id=None, count=None, offset=None, api_key=None,
            secure=None, test=None, **request_args):
        '''Builds query string params from inputs. It handles offset and
        count defaults and validation.

        :param bounce_type: The type of bounces retrieve. See `bounce_types`
            for a list of types, or read the Postmark API docs. Defaults to
            `None`.
        :param inactive: If `True`, retrieves inactive bounces only.
            Defaults to `None`.
        :param email_filter: A string to filter emails by.
            Defaults to `None`.
        :param message_id: Retrieve a bounce for a single message's ID.
            Defaults to `None`.
        :param count: The number of bounces to retrieve in this request.
            Defaults to 25 if `message_id` is not provided.
        :param offset: The page offset for bounces to retrieve. Defaults to 0
            if `message_id` is not provided.
        :param api_key: Your Postmark API key. Defaults to `self.api_key`.
        :param secure: Use the https scheme for Postmark API.
            Defaults to `self.secure`.
        :params test: Use the Postmark test API. Defaults to `self.test`.
        :rtype: :class:`PystBouncesResponse`
        '''
        params = self._construct_params(bounce_type=bounce_type,
                                        inactive=inactive,
                                        email_filter=email_filter,
                                        message_id=message_id,
                                        count=count,
                                        offset=offset)
        url = self._get_api_url(secure=secure)
        headers = self._get_headers(api_key=api_key, test=test,
                                    request_args=request_args)
        response = self._request(url, headers=headers, params=params,
                                 **request_args)
        return response

    def _request(self, url, **kwargs):
        '''Makes request to :func:`PystInterface.request` and caches it.

        :param url: endpoint url
        :params \*\*kwargs: kwargs to pass to :func:`requests.request`
        '''
        response = super(PystBounces, self)._request(url, **kwargs)
        self._last_response = response
        return response

    def _construct_params(self, bounce_type=None, inactive=None,
                          email_filter=None, message_id=None, count=None,
                          offset=None):
        '''Builds query string params from inputs. It handles offset and
        count defaults and validation.

        :param bounce_type: The type of bounces retrieve. See `bounce_types`
            for a list of types, or read the Postmark API docs. Defaults to
            `None`.
        :param inactive: If `True`, retrieves inactive bounces only.
            Defaults to `None`.
        :param email_filter: A string to filter emails by.
            Defaults to `None`.
        :param message_id: Retrieve a bounce for a single message's ID.
            Defaults to `None`.
        :param count: The number of bounces to retrieve in this request.
            Defaults to 25 if `message_id` is not provided.
        :param offset: The page offset for bounces to retrieve. Defaults to 0
            if `message_id` is not provided.
        '''
        params = {}
        if bounce_type is not None:
            if bounce_type not in bounce_types:
                err = 'Invalid bounce type "{0}".'
                raise PystBounceError(err.format(bounce_type))
            else:
                params['type'] = bounce_type
        if inactive is not None:
            params['inactive'] = inactive
        if email_filter is not None:
            params['emailFilter'] = email_filter
        if message_id is None:
            # If the message_id is given, count and offset are not
            # required, so we postpone assigning defaults to here
            if count is None:
                count = 25
            if offset is None:
                offset = 0
        else:
            params['messageID'] = message_id
        if count is not None:
            params['count'] = count
        if offset is not None:
            params['offset'] = offset
        return params


class PystBounce(PystGetInterface):
    '''Single bounce retrieval endpoint wrapper.

    :param api_key: Your Postmark API key. Defaults to `None`.
    :param secure: Use the https scheme for Postmark API.
        Defaults to `True`.
    :param test: Make a test request to the Postmark API.
        Defaults to `False`.
    '''
    endpoint = '/bounces/{bounce_id}'
    response_class = PystBounceResponse

    def __init__(self, api_key=None, secure=True, test=False):
        super(PystBounce, self).__init__(api_key=api_key, secure=secure,
                                         test=test)

    def get(self, bounce_id, api_key=None, secure=None, test=None,
            **request_args):
        '''Retrieves a single bounce's data.

        :param bounce_id: A bounce's ID retrieved with :class:`PystBounces`.
        :param api_key: Your Postmark API key. Defaults to `self.api_key`.
        :param secure: Use the https scheme for Postmark API.
            Defaults to `self.secure`.
        :param test: Make a test request to the Postmark API.
            Defaults to `self.test`.
        :param \*\*request_args: Keyword args to pass to
            :func:`requests.request`.
        :rtype: :class:`PystBounceResponse`
        '''
        url = self._get_api_url(secure=secure, bounce_id=bounce_id)
        headers = self._get_headers(api_key=api_key, test=test,
                                    request_args=request_args)
        return self._request(url, headers=headers, **request_args)


class PystBounceDump(PystBounce):
    '''Bounce dump endpoint wrapper.'''
    response_class = PystBounceDumpResponse
    endpoint = '/bounces/{bounce_id}/dump'


class PystBounceTags(PystGetInterface):
    '''Bounce tags endpoint wrapper.'''
    response_class = PystBounceTagsResponse
    endpoint = '/bounces/tags'


class PystDeliveryStats(PystGetInterface):
    '''Delivery Stats endpoint wrapper.'''
    response_class = PystDeliveryStatsResponse
    endpoint = '/deliverystats'


class PystBounceActivate(PystInterface):
    '''Bounce Activation endpoint wrapper.

    :param bounce_id: A bounce's ID retrieved with :class:`PystBounces`.
        Defaults to `None`.
    :param api_key: Your Postmark API key. Defaults to `None`.
    :param secure: Use the https scheme for Postmark API.
        Defaults to `True`.
    :param test: Make a test request to the Postmark API.
        Defaults to `False`.
    '''
    response_class = PystBounceActivateResponse
    method = 'PUT'
    endpoint = '/bounces/{bounce_id}/activate'

    def __init__(self, api_key=None, secure=True, test=False):
        super(PystBounceActivate, self).__init__(api_key=api_key, test=test,
                                                 secure=secure)

    def activate(self, bounce_id, api_key=None, secure=None, test=None,
                 **request_args):
        '''Activates a bounce.

        :param bounce_id: A bounce's ID retrieved with :class:`PystBounces`.
        :param api_key: Your Postmark API key. Defaults to `self.api_key`.
        :param secure: Use the https scheme for Postmark API.
            Defaults to `self.secure`.
        :param test: Make a test request to the Postmark API.
            Defaults to `self.test`.
        :param \*\*request_args: Keyword args to pass to
            :func:`requests.request`.
        :rtype: :class:`PystBounceActivateResponse`
        '''
        url = self._get_api_url(secure=secure, bounce_id=bounce_id)
        headers = self._get_headers(api_key=api_key, test=test,
                                    request_args=request_args)
        return self._request(url, headers=headers, **request_args)


''' Exceptions '''


class PystError(Exception):
    '''Base `Exception` for :mod:`pystmark` errors.

    :param message: Message to raise with the Exception. Defaults to
        `None`.
    '''
    message = ''

    def __init__(self, message=None):
        if message is not None:
            self.message = message

    def __str__(self):
        return str(self.message)


class PystMessageError(PystError):
    ''' Raised when a message meant to be sent to Postmark API looks
        malformed
    '''
    message = 'Refusing to send malformed message'


class PystBounceError(PystError):
    ''' Raised when a bounce API method fails '''
    message = 'Bounce API failure'


class PystResponseError(PystError):
    '''Base `Exception` for errors received from Postmark API

    :param response: A :class:`PystResponse`.
    :param message: Message to raise with the Exception.
        Defaults to `None`.
    '''

    def __init__(self, response, message=None):
        self.response = response
        try:
            self.data = response.json()
        except ValueError:
            self.data = {}
        self.error_code = self.data.get('ErrorCode', -1)
        self.message = self.data.get('Message', '')
        self.message_id = self.data.get('MessageID', '')
        self.submitted_at = self.data.get('SubmittedAt', '')
        self.to = self.data.get('To', '')
        super(PystResponseError, self).__init__(message=message)

    def __str__(self):
        if not self.data:
            msg = 'Not a valid JSON response. Status: {0}'
            return msg.format(self.response.status_code)
        msg = '{1} [ErrorCode {0}]'
        return msg.format(self.error_code, self.message)


class PystUnauthorizedError(PystResponseError):
    '''Raised when Postmark responds with a :attr:`status_code` of 401
    Indicates a missing or incorrect API key.
    '''
    pass


class PystUnprocessableEntityError(PystResponseError):
    '''Raised when Postmark responds with a :attr:`status_code` of 422.
    Indicates message(s) received by Postmark were malformed.
    '''
    pass


class PystInternalServerError(PystResponseError):
    '''Raised when Postmark responds with a :attr:`status_code` of 500
    Indicates an error on Postmark's end. Any messages sent
    in the request were not received by them.
    '''
    pass


''' Singletons '''

_default_pyst_sender = PystSender()
_default_pyst_batch_sender = PystBatchSender()
_default_bounces = PystBounces()
_default_bounce = PystBounce()
_default_bounce_dump = PystBounceDump()
_default_bounce_tags = PystBounceTags()
_default_delivery_stats = PystDeliveryStats()
_default_bounce_activate = PystBounceActivate()
