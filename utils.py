
import simplejson as json

__bool_type = ('true','false','1','0')


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

# taken from paste.deploy.converter
def asbool(obj):
    if isinstance(obj, (str, unicode)):
        obj = obj.strip().lower()
        if obj in ['true', 'yes', 'on', 'y', 't', '1']:
            return True
        elif obj in ['false', 'no', 'off', 'n', 'f', '0']:
            return False
        else:
            raise ValueError(
                "String is not true/false: %r" % obj)
    return bool(obj)
    
    
def type_converter(options):
    
    for k in options.keys():
        
        if options[k].lower() in __bool_type:
            options[k] = asbool(options[k])
            continue
        
        # jsonify it if possible
        jsonify_obj = None
        try:
            jsonify_obj = json.loads(options[k])
        except:
            pass
        
        if jsonify_obj:
            options[k] = jsonify_obj
        
    return options

def dump_config(configuration, prefix):
    '''Dump nilai pada konfigurasi file ini kedalam bentuk dict {}
    '''
    
    options = dict((x[len(prefix):],configuration[x]) for x in configuration if x.startswith(prefix))
    
    return type_converter(options)