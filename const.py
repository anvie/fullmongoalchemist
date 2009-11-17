import datetime, time

allowed_data_types = [list, str, unicode, int, long, float, time.struct_time, datetime.datetime, bool]
relation_reserved_words = ('_parent_class','listmode','_type','_keyrel','rel_class','_cond',)
superdoc_reserved_words = ('_db','_id','_metaname_','_echo','_pending_ops')