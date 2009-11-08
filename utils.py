

def parse_query(kwargs):
    """Parse argument list into mongo query. 
    
    Examples:
        (user='jack')  =>  {'user': 'jack'}
        (comment__user='john') => {'comment.user': 'john'}
        (comment__rating__lt=10) => {'comment.rating': {'$lt': 10}}
        (user__in=[10, 20]) => {'user': {'$in': [10, 20]}}
    """
    
    q = {}
    # iterate over kwargs and build query dict
    for k, v in kwargs.items():
        # handle query operators
        op = k.split('__')[-1]
        if op in ('lte', 'gte', 'lt', 'gt', 'ne',
            'in', 'nin', 'all', 'size', 'exists'):
            v = {'$' + op: v}
            k = k[:k.find('__' + op)]
        
        # XXX dunno if we really need this?
        if type(v) == list:
            v = str(v)
        
        # convert django style notation into dot notation
        key = k.replace('__', '.')
        
        # convert mongodbobject SuperDoc type to pymongo DBRef type.
        # it's necessary for pymongo search working correctly
        #if type(v) == SuperDoc:
        #    v = DBRef(v._collection,v._id)
        
        q[key] = v
    return q