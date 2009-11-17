

class PendingOperation(object):
    
    def __init__(self, doc):
        self.doc = doc
        self._ops = []
    
    def add_op(self, doc, action='save', **kwargs):
        op = dict(doc=doc, op=dict(action=action, **kwargs))
        self._ops.append(op)
    
    def clear(self):
        del self._ops[:]
        
    def empty(self):
        return len(self._ops)==0
    
    def apply_op_all(self):
        
        for i, op in enumerate(self._ops):
            doc = op['doc']
            o = op['op']
            
            def save():
                return doc.save()
            def set_attr():
                return setattr( doc, o['key'], o['value'])
            def call_method():
                return apply( getattr( doc, o['key']), *o['args'], **o['kwargs'] )
            
            self._ops[i]['rv'] = {
                'save' : save,
                'setattr' : set_attr,
                'call' : call_method
            }.get(o['action'], (lambda: None) )()
            
        self.clear()
