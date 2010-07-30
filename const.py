import datetime, time
from antypes import Binary, options
import types

allowed_data_types = [list, dict, str, unicode, int, long, float,
                      time.struct_time, datetime.time, datetime.datetime, bool,
                      Binary, options, types.NoneType]

relation_reserved_words = ('_parent_class','listmode','_type',
                           '_keyrel','rel_class','_cond','_order','_pk',
                           '_cascade','_backref','_old_hash','_post_save','_internal_params',
                           '_current_hash','_rel_class_name','_polymorphic'
                           )
superdoc_reserved_words = ('_monga','_id','_metaname_','_echo','_pending_ops')
restrict_attribute_names = ('_data','_type')