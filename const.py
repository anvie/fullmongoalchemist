import datetime, time

allowed_data_types = [list, dict, str, unicode, int, long, float, time.struct_time, datetime.time, datetime.datetime, bool]
relation_reserved_words = ('_parent_class','listmode','_type','_keyrel','rel_class','_cond','_order')
superdoc_reserved_words = ('_db','_id','_metaname_','_echo','_pending_ops')