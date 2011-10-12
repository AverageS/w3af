'''
urllist_txt.py

Copyright 2006 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

'''

import core.controllers.outputManager as om

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
from core.controllers.w3afException import w3afRunOnce, w3afException
from core.controllers.coreHelpers.fingerprint_404 import is_404

import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info


class urllist_txt(baseDiscoveryPlugin):
    '''
    Analyze the urllist.txt file and find new URLs
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        # Internal variables
        self._exec = True

    def discover(self, fuzzableRequest ):
        '''
        Get the urllist.txt file and parse it.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains
                                                      (among other things) the URL to test.
        '''
        if not self._exec:
            # This will remove the plugin from the discovery plugins to be runned.
            raise w3afRunOnce()
        else:
            # Only run once
            self._exec = False
            
            dirs = []
            self._new_fuzzable_requests = []         
            
            base_url = fuzzableRequest.getURL().baseUrl()
            urllist_url = base_url.urlJoin( 'urllist.txt' )
            http_response = self._url_opener.GET( urllist_url, useCache=True )
            
            if not is_404( http_response ):

                # Work with it...
                dirs.append( urllist_url )
                is_urllist = 5
                for line in http_response.getBody().split('\n'):
                    
                    line = line.strip()
                    
                    if not line.startswith('#') and line:    
                        try:
                            url = base_url.urlJoin( line )
                        except:
                            is_urllist -= 1
                            if not is_urllist:
                                break
                        else:
                            dirs.append( url )

                if is_urllist:
                    # Save it to the kb!
                    i = info.info()
                    i.setPluginName(self.name)
                    i.setName('urllist.txt file')
                    i.setURL( urllist_url )
                    i.setId( http_response.id )
                    i.setDesc( 'A urllist.txt file was found at: "'+ urllist_url +'".' )
                    kb.kb.append( self.name, 'urllist.txt', i )
                    om.out.information( i.getDesc() )

            for url in dirs:
                #   Send the requests using threads:
                targs = ( url,  )
                self._tm.startFunction( target=self._get_and_parse, args=targs, ownerObj=self )
                
            # Wait for all threads to finish
            self._tm.join( self )
            
            return self._new_fuzzable_requests
            
    def _get_and_parse(self, url):
        '''
        GET and URL that was found in the robots.txt file, and parse it.
        
        @parameter url: The URL to GET.
        @return: None, everything is saved to self._new_fuzzable_requests.
        '''
        try:
            http_response = self._url_opener.GET( url, useCache=True )
        except KeyboardInterrupt, k:
            raise k
        except w3afException, w3:
            msg = 'w3afException while fetching page in discovery.urllist_txt, error: "'
            msg += str(w3) + '"'
            om.out.debug( msg )
        else:
            if not is_404( http_response ):
                fuzz_reqs = self._createFuzzableRequests( http_response )
                self._new_fuzzable_requests.extend( fuzz_reqs )
        
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol
        
    def setOptions( self, OptionList ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        pass

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return []

    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin searches for the urllist.txt file, and parses it. The urllist.txt file is/was used
        by Yahoo's search engine.
        '''
