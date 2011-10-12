'''
wsdlFinder.py

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

from core.data.parsers.urlParser import url_object

from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
from core.controllers.w3afException import w3afException

from core.data.bloomfilter.bloomfilter import scalable_bloomfilter


class wsdlFinder(baseDiscoveryPlugin):
    '''
    Find web service definitions files.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        # Internal variables
        self._already_tested = scalable_bloomfilter()
        self._new_fuzzable_requests = []
        
    def discover(self, fuzzableRequest ):
        '''
        If url not in _tested, append a ?wsdl and check the response.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        url = fuzzableRequest.getURL().uri2url()
        url_string = url.url_string
        
        if url_string not in self._already_tested:
            self._already_tested.add( url_string )
            
            # perform the requests
            for wsdl_parameter in self._get_WSDL():
                url_to_request = url_string + wsdl_parameter
                url_instance = url_object(url_to_request)
                
                #   Send the requests using threads:
                targs = ( url_instance, )
                self._tm.startFunction( target=self._do_request, args=targs, ownerObj=self )
        
            # Wait for all threads to finish
            self._tm.join( self )
        
        return self._new_fuzzable_requests

    def _do_request(self, url_to_request):
        '''
        Perform an HTTP request to the url_to_request parameter.
        @return: None.
        '''
        try:
            self._url_opener.GET( url_to_request, useCache=True )
        except w3afException:
            om.out.debug('Failed to request the WSDL file: ' + url_to_request)
        else:
            # The response is analyzed by the wsdlGreper plugin
            pass

    def _get_WSDL( self ):
        '''
        @return: A list of parameters that are used to request the WSDL
        '''
        res = []
        
        res.append( '?wsdl' )
        res.append( '?WSDL' )
        
        return res
        
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
        @return: A list with the names of the plugins that should be run before the
        current one.
        '''
        return ['grep.wsdlGreper']
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin finds new web service descriptions and other web service related files
        by appending "?WSDL" to all URL's and checking the response.
        '''
