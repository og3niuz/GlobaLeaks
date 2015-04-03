# -*- coding: utf-8 -*-
#
#  admlangfiles
#  **************
#
# Backend supports for jQuery File Uploader, and implementation of the
# file language statically uploaded by the Admin

#`This code differs from handlers/file.py because files here are not tracked in the DB

from __future__ import with_statement
import os
import time

from twisted.internet import threads
from twisted.internet.defer import inlineCallbacks

from globaleaks.settings import GLSetting
from globaleaks.handlers.admin.staticfiles import dump_static_file
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import transport_security_check, authenticated, unauthenticated
from globaleaks.utils.utility import log
from globaleaks.rest import errors
from globaleaks.security import directory_traversal_check

class AdminLanguageFileHandler(BaseHandler):
    """
    This class is used to return the custom translation files;
    if the file are not present, default translations are returned
    """
    def langfile_path(self, lang):
        return os.path.abspath(os.path.join(GLSetting.glclient_path, 'l10n', '%s.json' % lang))

    def custom_langfile_path(self, lang):
        return os.path.abspath(os.path.join(GLSetting.static_path_l10n, '%s.json' % lang))

    @transport_security_check('admin')
    @authenticated('admin')
    def get(self, lang):
        self.set_status(204)
        self.finish()

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def post(self, lang):
        """
        Upload a custom language file
        """
        uploaded_file = self.get_file_upload()
        if uploaded_file is None:
            self.set_status(201)
            self.finish()
            return

        path = self.custom_langfile_path(lang)
        directory_traversal_check(GLSetting.static_path_l10n, path)

        try:
            dumped_file = yield threads.deferToThread(dump_static_file, uploaded_file, path)
        except OSError as excpd:
            log.err("OSError while create a new custom lang file [%s]: %s" % (path, excpd))
            raise errors.InternalServerError(excpd.strerror)
        except Exception as excpd:
            log.err("Unexpected exception: %s" % excpd)
            raise errors.InternalServerError(excpd)

        log.debug("Admin uploaded new lang file: %s" % dumped_file['filename'])

        self.set_status(201) # Created
        self.finish(dumped_file)

    @transport_security_check('admin')
    @authenticated('admin')
    def delete(self, lang):
        """
        Parameter: filename
        Errors: LangFileNotFound
        """
        path = self.custom_langfile_path(lang)
        directory_traversal_check(GLSetting.static_path_l10n, path)

        if not os.path.exists(path):
            raise errors.LangFileNotFound

        os.remove(path)

        self.set_status(200)
        self.finish()
