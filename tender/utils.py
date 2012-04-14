# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
import re

### Found on http://code.activestate.com/recipes/440698-split-string-on-capitalizeduppercase-char/
def split_on_caps(str):
    
    rs = re.findall('[A-Z][^A-Z]*',str)
    fs = ""
    for word in rs:
        fs += " "+word
    
    return fs
    
### Utility function
def message(title, message, pagetitle="Message"):
    _message = { 'pagetitle':pagetitle,
                 'title': title,
                 'message':message}

    return render_to_response(  'message.html',
                              { 'message':_message }
                            )

