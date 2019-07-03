#!/usr/bin/env python3

import os
import tornado.httpserver
import tornado.web
import tornado.ioloop

# From https://stackoverflow.com/questions/18353035/redirect-http-requests-to-https-in-tornado
class MainHandler(tornado.web.RequestHandler):

    def prepare(self):
        if self.request.protocol == 'http':
            self.redirect('https://' + self.request.host, permanent=False)

    def get(self):
        self.write("Redirecting to HTTPS")


if __name__ == "__main__":
    application = tornado.web.Application([
        (r'/', MainHandler)
    ])
    application.listen(80)
    
    tornado.ioloop.IOLoop.current().start()
