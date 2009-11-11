from pymongo.dbref import DBRef
from nested import Nested
from platform import python_version
from orm import relation, RelationDataType

import types
import datetime
import time

# define global for optimization purpose (reduce overcall frequently)
_pyver_lt_260 = map(int, python_version().split('.')) < [2, 6, 0]
allowed_data_types = [list, str, unicode, int, long, time.struct_time, datetime.datetime, bool]


class Doc(object):
    """The Doc class represents a single document and its features.
    """
    
    
    def __init__(self, data):
        """A documents gets initialized with its collection and the data.
        """
        
        self.__dict__['_data'] = Nested(data)


    def __getattr__(self, key):
        """Return value from data attribute.
        """
        
        if hasattr(self.__dict__['_data'], key):
            
            obj = getattr(self.__dict__['_data'], key)
            
            if type( obj ) == RelationDataType:
                return object.__getattribute__(self, key)
    
            return obj
        
        return object.__getattribute__(self, key)
        

    def __setattr__(self, key, value):
        """Convert dicts to Nested object on setting the attribute.
        """
        
        obj_type = type(value)
        
        if obj_type == dict:
            value = Nested(value)
            
        elif obj_type == relation:
            object.__setattr__(self, key, value)
            value = RelationDataType(value)
            
        else:
            global allowed_data_types
            
            if obj_type in allowed_data_types:
                setattr(self.__dict__['_data'], key, value)
            else:    
                object.__setattr__(self, key, value)

    
    def to_dict(self):
        """Public wrapper for converting an Nested object into a dict.
        """
        
        dict = self.__to_dict(self.__dict__['_data'])

        if hasattr(self.__dict__['_data'], '_id'):
            dict['_id'] = getattr(self.__dict__['_data'], '_id')

        return dict
    
    def __to_dict(self, obj):
        """Iterate over the nested object and convert it to an dict.
        """
        
        d = {}
        for k in dir(obj):
            # ignore values with a beginning underscore. these are private.
            if k.startswith('__'): continue
    
            # get value an type
            value = getattr(obj, k)
            obj_type = type(value)
            
            # preocess Nested objects
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
                        if not hasattr(i,'_id'):
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

    def keys(self):
        """Get a list of keys for the current level.
        """
        
        keys = []
        for i in dir(self.__dict__['_data']):
            # skip private members
            if not i.startswith('_') and i != '_id':
                keys.append(i)

        return keys

    def save(self):
        """Save document to collection. 
        If document is new, set generated ID to document _id.
        """

        self.__dict__['_data']._id = self._db[self._collection_name].save(self.to_dict())
        
    def delete(self):
        """Remove document from collection if a document id exists.
        """
        
        if hasattr(self.__dict__['_data'], '_id'):
            rv = self._db[self._collection_name].remove(
                {'_id': self.__dict__['_data']['_id']}
            )
            self.__dict__['_data']._id = None
            return rv
        
    def __repr__(self):
        """String representation of a document.
        """
        
        if not hasattr(self.__dict__['_data'], '_id'):
            return 'Doc(id=<not_saved>)'
            
        
        # use format for python versions above 2.5
        global _pyver_lt_260
        if _pyver_lt_260:
            if hasattr(self.__dict__['_data']._id,'url_encode'):
                return 'Doc(id=%s)' % self.__dict__['_data']._id.url_encode()
            else:
                # handle bad/unrecognized id format either
                return 'Doc(id=%s)' % self.__dict__['_data']._id
        else:
            return 'Doc(id={0})'.format(
                self.__dict__['_data']._id.url_encode()
            )
            
