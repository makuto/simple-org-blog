#!/usr/bin/env python3

import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.httpclient
import tornado.httpserver
import tornado.gen

import os
from datetime import datetime

import ContentConverter

#
# Tornado handlers
#

class HomeHandler(tornado.web.RequestHandler):
    def get(self):
        allPosts = ContentConverter.getAllPostsList()
        self.render("templates/Home.html", allPosts=allPosts)

class BlogHandler(tornado.web.RequestHandler):
    def get(self, request):
        contentTitle = "Blog: " + request
        renderedBody = ContentConverter.getRenderedBody(request)
        if not renderedBody:
            renderedBody = "<p>The post under '{}' does not exist.</p>".format(request)
            
        self.render("templates/BlogPost.html", title=contentTitle, postBody=renderedBody)
    
#
# Startup
#

def make_app():
    return tornado.web.Application([
        # Home page
        (r'/', HomeHandler),

        (r'/blog/(.*)', BlogHandler),

        # # Handles messages for run script
        # (r'/runScriptWebSocket', RunScriptWebSocket),

        # Upload handler
        # (r'/upload', UploadHandler),

        # # Don't change this 'output' here without changing the other places as well
        # (r'/output/(.*)', tornado.web.StaticFileHandler, {'path' : 'output'}),

        # Static files. Keep this at the bottom because it handles everything else
        # TODO put these in a subdir so everything isn't accessible
        (r'/webResources/(.*)', tornado.web.StaticFileHandler, {'path' : 'webResources'}),
    ],
                                   xsrf_cookies=True,
                                   cookie_secret='this is my org blog')

if __name__ == '__main__':

    # Before startup, convert anything which needs to be converted
    ContentConverter.checkForContentChange()
    
    port = 8888
    print('\nStarting Simple Org Blog Server on port {}...'.format(port))
    app = make_app()

    #
    # Notes on SSL
    #
    # Certificate generation (for localhost) (didn't actually work):
    #  https://medium.freecodecamp.org/how-to-get-https-working-on-your-local-development-environment-in-5-minutes-7af615770eec?gi=bd966500e56a
    # Tornado instructions:
    #  https://stackoverflow.com/questions/18307131/how-to-create-https-tornado-server
    # Note that I added the rootCA to Certificates trust in Firefox Preferences as well (didn't do anything)
    #
    # What I actually did:
    # openssl req -x509 -nodes -days 365 -newkey rsa:1024 -keyout certificates/server_jupyter_based.crt.key -out certificates/server_jupyter_based.crt.pem
    # (from https://jupyter-notebook.readthedocs.io/en/latest/public_server.html)
    # I then had to tell Firefox to trust this certificate even though it is self-signing (because
    # I want a free certificate for this non-serious project)
    useSSL = True
    if useSSL:
        app.listen(port, ssl_options={"certfile":"certificates/server_jupyter_based.crt.pem",
                                      "keyfile":"certificates/server_jupyter_based.crt.key"})
    else:
        # Show the warning only if SSL is not enabled
        print('\n\tWARNING: Do NOT run this server on the internet (e.g. port-forwarded)'
          ' nor when\n\t connected to an insecure LAN! It is not protected against malicious use.\n')
        
        app.listen(port)
        
    ioLoop = tornado.ioloop.IOLoop.current()
    
    # Periodically check to see if anything has changed which needs to be converted to .html
    # Check every fifteen minutes
    checkForContentChangeCallback = tornado.ioloop.PeriodicCallback(ContentConverter.checkForContentChange,
                                                                    15 * 60 * 1000)
    checkForContentChangeCallback.start()
    
    ioLoop.start()

# Local Variables:
# compile-command: "./SimpleBlogServer.py"
# End:
