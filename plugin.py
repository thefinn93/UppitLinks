###
# Copyright (c) 2010, Christopher Slowe
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import re 
from reddit import RedditSession
import urllib

reddit = RedditSession()

reddit_re = re.compile(r"(http://([^/]*\.)?reddit.com/\S*)")
redditsub_re = re.compile(r"(http://([^/]*\.)?reddit.com/(r/[^/]+/)?comments/(?P<id>[^/]+))")
reddituser_re = re.compile(r"(http://([^/]*\.)?reddit.com/user/(?P<username>[^/]+))")

def find_links(text):
    def present_listing_first(res):
        d = res.get("data", {}).get("children", [{}])[0].get("data",{}) 
        if d:
            info = "(%(score)s) \""+ircutils.bold("%(title)s")+"\" -- http://www.reddit.com/r/%(subreddit)s/comments/%(id)s/"
            return (info % d)
        

    links = utils.web.urlRe.findall(text)
    for link in links:
        link_m = reddit_re.match(link)
        if link_m:
            user_m = reddituser_re.match(link)
            sub_m = redditsub_re.match(link)
            if user_m:
                d = user_m.groupdict()   
                res = reddit.API_GET("/user/%s/about.json" % urllib.quote(d['username']))
                d = res.get("data")
                if d:
                    yield ("User \"%(name)s\" has karma %(link_karma)s" % d)
            
            elif sub_m:
                d = sub_m.groupdict()
                res = reddit.API_GET("/by_id/t3_%s.json" % urllib.quote(d['id']))
                yield present_listing_first(res)
            
        else:
            res = reddit.API_GET("/api/info.json?limit=1&url=%s" %
                                 urllib.quote(link))
            yield present_listing_first(res)


class RedditLinks(callbacks.Plugin):
    """Add the help for "@plugin help RedditLinks" here
    This should describe *how* to use this plugin."""
        
    def doPrivmsg(self, irc, msg):
        if ircmsgs.isCtcp(msg) and not ircmsgs.isAction(msg):
            return
        channel = msg.args[0]
        if irc.isChannel(channel):
            if ircmsgs.isAction(msg):
                text = ircmsgs.unAction(msg)
            else:
                text = msg.args[1]
            for info in find_links(text):
                irc.reply(info, prefixNick=False)

Class = RedditLinks


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
