
from pymongo.dbref import DBRef
from doc import Doc
from nested import Nested
from collection import Collection
from monga import MongoDB
from superdoc import SuperDoc
from orm import mapper, relation, RelationDataType
from pymongo import ASCENDING, DESCENDING
from const import allowed_data_types


VERSION = '0.2'
COPYRIGHT = 'AnLab Software'
CONTACT = 'robin@nosql.asia'




def to_dict(self, obj):
    """Iterate over the nested object and convert it to an dict.
    """
    
    d = {}
    for k in dir(obj):
        # ignore values with a beginning underscore. these are private.
        if k.startswith('__') and k != '__meta_pcname__':
            continue

        # get value an type
        value = getattr(obj, k)
        obj_type = type(value)
        
        # process Nested objects
        if obj_type == Nested:
            d[k] = self.__to_dict(value)
        # items
        elif obj_type == Doc:
            d[k] = DBRef( value._collection, value._id )
        # lists, that can consist of Nested objects, 
        # Docs (references) or primitive values
        elif obj_type == list:
            d[k] = []
            for i in value:
                if type(i) == Nested:
                    d[k].append(self.__to_dict(i))
                elif type(i) == Doc:
                    if getattr(i,'_id') is None:
                        # may unsaved object?? try to save it first
                        i.save()
                    
                    d[k].append(DBRef( i._collection, i._id ))
                else:
                    d[k].append(i)
        # primitive values
        
        elif obj_type == RelationDataType:
            d[k] = str(value)
        
        else:
            if obj_type in allowed_data_types:
                d[k] = value
        
    return d

Nested.to_dict = to_dict


