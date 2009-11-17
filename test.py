#!/usr/bin/env python

from fma import MongoDB, SuperDoc, Collection
from fma.orm import relation, mapper
from fma.antypes import *

import datetime

datetime_type = datetime.datetime

    

class PostMany(SuperDoc):
    
    _collection_name = 'test'
    
    tag_id = unicode
    sub_post_id = unicode
    isi = unicode
    nomor = int
    yatidak = bool
    
    tags = relation('Tags',pk='pm_id==_id',cascade='delete')
    posts = relation('PostMany',pk='sub_post_id==_id')
    
    _opt = dict(strict=True)
    
    
class Tags(SuperDoc):
    
    _collection_name = 'test'
    
    pm_id = unicode
    isi = list
    
    posts = relation('PostMany',pk='sub_post_id==_id')
    
    
    def get_related_tags(self):
        return Collection( self._db, Tags ).find(isi__in=self.isi,_id__ne=self._id)
        
    

class PostFlip(SuperDoc):
    
    _collection_name = 'test'
    
    
    tags = relation('TagFlip',type='many-to-many',keyrel='_tags:_id',backref='_posts:_id')
    
    
class TagFlip(SuperDoc):
    
    _collection_name = 'test'
    
    posts = relation('PostFlip',type='many-to-many',keyrel='_posts:_id',backref='_tags:_id')
    
    

class User(SuperDoc):

    _collection_name = 'test'
    
    #''' User authority definition
    #1=admin, 2=operator, 3=inspector, 4=corporate user, 5=delivery operator, 6=registered, 7 = guest
    #'''
    USER_POS_ADMIN = 1
    USER_POS_OPERATOR = 2
    USER_POS_INSPECTOR = 3
    USER_POS_CORPORATE = 4
    USER_POS_DELIVER_OPERATOR = 5
    USER_POS_REGISTERED = 6
    USER_POS_GUEST = 7
    
    name = unicode
    first_name = unicode
    last_name = unicode
    email = unicode
    birth_date = datetime_type
    pic_avatar = unicode
    lang_id = unicode
    contact = dict
    settings = dict
    
    _creation_time = datetime_type
    _authority = int
    _pass_hash = unicode
    _last_activity = datetime_type
    _last_login_time = datetime_type
    _reputation_level = int
    _warning_level = int
    _advertiser = bool
    _banned = bool
    _banned_type = int # 1 = permanent, 2 = with expiration
    _banned_expiration_time = datetime_type
    _hash = int
    
    wallposts = relation('WallPost',pk='wuid==_id',cond=or_(wuid=':_id',ruid=':_id'),listmode=True,cascade="delete")
    friends = relation('User',type='many-to-many',keyrel='_friends:_id',backref='_friends:_id')
    market = relation('Market',pk='owner_user_id==_id',type='one-to-one',cascade='delete')
    bids = relation('Item',pk='bidder_id==_id',cond=and_(item_class='Bid'))
    warnings = relation('Item',pk='user_id==_id',cond=and_(item_class='UserWarning'),cascade='delete')
    messages = relation('Message',pk='to_user_id==_id')
    sent_messages = relation('Message',pk='from_user_id==_id')
    
    
    _opt = {
        'req' : ['name'],
        'default' : dict(name='', _creation_time=datetime.datetime.utcnow),
        'strict' : True
    }
    
    @property
    def creation_time(self):
        return self._creation_time and self._creation_time.strftime("%a, %d/%m/%Y %H:%M:%S %p") or 'unknown'
        
    @property
    def join_time(self):
        return self.creation_time
    
    def get_token(self):
       import hashlib
       utoken = hashlib.sha1('%s-x-%s-%s' % (self._id, self.name, str(self._creation_time))).hexdigest()
       return utoken

    @property
    def have_market(self):
        return self.market and True or False

    @property
    def full_name(self):
        '''Get formated user name
        '''
        rv = self.first_name
        if self.last_name:
            rv = '%s %s' % (rv, self.last_name)
        return rv

    @property
    def last_login_time(self):
        '''Formated date for user last login, use _last_login instead for get raw data
        '''
        if self._last_login_time:
            return self._last_login_time.strftime('%a, %d/%m/%Y %H:%M:%S')
        return None

    @property
    def profile_link(self):
        '''Mendapatkan alamat link profile dari pengguna
        contoh: http://ansvia.com/user
        '''
        return "/%s" % self.name

    @property
    def avatar_image_link(self):
        '''Mendapatkan alamat gambar avatar
        '''
        pass
        
    @property
    def have_avatar(self):
        return self.pic_avatar and True or False

    @property
    def join_date(self):
        '''Mendapatkan waktu join terformat
        Gunakan _join_time untuk akses secara langsung
        '''
        return self._creation_time.strftime("%d/%m/%Y")

    @property
    def hash(self):
        '''Get hash for caching perform
        '''
        return self._hash

    @property
    def authority(self):
        return self._authority

    @property
    def authority_name(self):
        return {
            self.USER_POS_ADMIN: "Admin",
            self.USER_POS_OPERATOR: "Operator",
            self.USER_POS_INSPECTOR: "Inspector",
            self.USER_POS_CORPORATE: "Corporate user",
            self.USER_POS_DELIVER_OPERATOR: "Delivery operator",
            self.USER_POS_REGISTERED: "Registered user",
            self.USER_POS_GUEST: "Guest"
        }.get(self._authority, (lambda: "Unknown"))()

    @property
    def banned(self):
        return (self._banned and (datetime.datetime.now() < self._banned_expiration_time)) and True or False

    @property
    def banned_type(self):
        return self._banned_type

    @property
    def banned_expiration_time(self):
        '''Mendapatkan waktu kadaluarsa terformat user yang dibanned
        '''
        return self._banned_expiration_time and self._banned_expiration_time.strftime("%a, %d/%m/%Y %H:%M:%S") or 'unknown'

    @property
    def reputation_level(self):
        return self._reputation_level

    @property
    def warning_level(self):
        return self._warning_level
    

class WallPost(SuperDoc):

    _collection_name = 'test'
    
    wuid = unicode
    ruid = unicode
    
    message = unicode
    via = unicode
    _creation_time = datetime.datetime
    
    writter = relation('User',pk='_id==wuid', listmode=False)
    receiver = relation('User',pk='_id==ruid', listmode=False)
    comments = relation('Comment',pk='itemid==_id', cascade='delete')
    
    _opt = {
        'req' : ['wuid','ruid','message','via'],
        'default' : dict(_creation_time=datetime.datetime.utcnow),
        'strict' : True
    }
    
    @property
    def creation_time(self):
        return self._creation_time and self._creation_time.strftime("%a, %d/%m/%Y %H:%M:%S %p") or 'unknown'
   
    @property
    def formatted_message(self):
        return self.message
        
class Message(SuperDoc):
    
    _collection_name = 'test'
    
    to_user_id = unicode
    from_user_id = unicode
    subject = unicode
    content = unicode
    
    _readed = bool
    _replied = bool
    _deleted = bool
    _deleted_time = datetime_type
    _allow_html = bool

    owner = relation('User', pk='_id==to_user_id', listmode=False)
    sender =  relation('User', pk='_id==from_user_id', listmode=False)

    @property
    def readed(self):
        return self._readed

    @property
    def replied(self):
        return self._replied

    @property
    def deleted(self):
        return self._deleted

    
class ChatMessage(SuperDoc):
    
    _collection_name = 'test'
    
    chat_msg_id = long
    from_user_id = long
    to_user_id = long
    message = unicode
    received = bool
    sent = datetime.datetime
    
    _opt = {
        'req' : ['chatdata_id','message'],
        'default' : {'sent':datetime.datetime.now},
        'strict' : True
    }
    
class UserNotification(SuperDoc):
    
    _collection_name = 'test'
    
    TYPE_GENERAL = 0
    TYPE_COMMENT = 1
    TYPE_BID = 2
    TYPE_TESTIMONIAL = 3
    TYPE_WARNING = 4
    TYPE_ERROR = 5
    TYPE_PRODUCT_ITEM_UPDATED = 6

    user_id = unicode
    subject = unicode
    message = unicode
    email_notification = bool
    
    _received_time = datetime_type
    _expired = bool
    _closed = bool
    _closed_time = datetime_type
    _readed = bool
    _type = int # TYPE_*

    user = relation('User',pk='_id==user_id',listmode=False)

    _opt = {
        'default' : dict(_creation_time=datetime.datetime.utcnow,_received_time=datetime.datetime.now)
    }

    @property
    def notification_type(self):
        return self._type

    @property
    def received_time(self):
        global _standard_time_format
        return self._received_time.strftime(_standard_time_format)

class UserCart(SuperDoc):
    
    _collection_name = 'test'
    
    user_id = unicode
    product_item_id = unicode
    _added_time = datetime_type

    user = relation('User',pk='_id==user_id',listmode=False)
    product_item = relation('ProductItem',pk='_id==user_id',listmode=False)

class UserActivity(SuperDoc):
    
    _collection_name = 'test'
    
    ACCESS_PUBLIC = 0
    ACCESS_PRIVATE = 1
    ACCESS_INTERNAL = 2

    TYPE_GENERAL = 0
    TYPE_MAKE_BID = 1
    TYPE_WRITE_COMMENT = 2
    TYPE_MAKE_RECOMMENDATION = 3
    TYPE_WRITE_TESTIMONIAL = 4
    TYPE_MAKE_ABUSE = 5

    user_id = unicode
    last_time = datetime_type
    info = unicode
    
    _access = int   # ACCESS_*
    _type = int

    user = relation('User',pk='_id==user_id',listmode=False)

class Market(SuperDoc):
    
    _collection_name = 'test'
    
    owner_user_id = unicode
    name = unicode
    description = unicode
    pic_logo = unicode
    address = unicode
    city = unicode
    province = unicode
    country = unicode
    zip_postal_code = unicode
    phone1 = unicode
    phone2 = unicode
    fax = unicode
    email = unicode
    
    settings = dict
    bad_bidders = list  # list of User
    
    _creation_time = datetime_type
    _closed = bool
    _closed_time = datetime_type
    
    _certified = bool
    _certification_type = int
    _certified_since = datetime_type
    
    _reputation_level = int
    _popularity_level = int
    _suspended = bool
    _suspended_info = unicode
    _first_time_add_product_item = bool

    owner = relation('User',pk='_id==owner_user_id',listmode=False)
    product_items = relation('ProductItem',pk='owner_market_id==_id')
    abuser = relation('Abuser',pk='item_id==_id')
    visitors = relation('Visitor',pk='item_id==_id',cond=and_(item_class='Visitor'))
    posts = relation('MarketPost',pk='market_id==_id',cond=and_(item_class='Post'))
    testi = relation('Testimonial',pk='market_id==_id')


    @property
    def permalink(self):
        '''Untuk mendapatkan url terformat alamat market
        '''

        return '/%s/market' % self.owner.name
    
    @property
    def first_time_add_product_item(self):
        return self._first_time_add_product_item and True or False

    def short_description(self,width=100):
        '''Untuk mendapatkan deskripsi yang dipendekkan dan ditambah '...'
        '''
        if len(self.description) > width:
            return "%s..." % self.description[:width]
        return self.description


class MarketPost(SuperDoc):
    
    _collection_name = 'test'
    
    market_id = unicode
    poster_user_id = unicode
    title = unicode
    _content = unicode
    order = int
    _creation_time = datetime_type
    _closed = bool
    _closed_time = datetime_type
    _deleted = bool
    _deleted_time = datetime_type
    _allow_comment = bool
    _published = bool

    market = relation('Market',pk='_id==market_id',listmode=False)
    author = relation('User', pk='poster_user_id==_id',listmode=False)
    comments = relation('Comment', pk='itemid==_id')

    @property
    def content(self):
        '''Synonym for _content, get formated (encoded) content text,
        format includes encode like spoiler, emoticon, etc
        '''
        return self._content

    @property
    def editable_content(self):
        '''Show content in original editing format purpose
        '''
        return self._content

    @property
    def permalink(self):
        import re
        rv = re.sub(r'\W+', '-', self.title).strip('-')
        return "/%s/market/post/%d/%s.html" % (self.market.owner.name,self.id,rv)


    @property
    def published(self):
        '''Untuk mendapatkan info apakah postingan telah
        dipublish atau tidak dalam mode terformat
        '''

        return self._published and _("Yes") or _("No")

    @property
    def comment_allowed(self):
        return self._allow_comment

class Testimonial(SuperDoc):
    
    _collection_name = 'test'
    
    market_id = unicode
    poster_user_id = unicode
    subject = unicode
    content = unicode
    
    _approved = bool
    _creation_date = datetime_type
    _deleted = bool
    _deletion_date = datetime_type
    _responsible_mod_id = unicode
    _deletion_reason = unicode

    poster = relation('User',pk='_id==poster_user_id',listmode=False)
    market = relation('Market',pk='_id==market_id',listmode=False)

class Visitor(SuperDoc):
    
    _collection_name = 'test'
    
    item_id = unicode
    user_id = unicode
    
    user = relation('User',pk='_id==user_id',listmode=False)
    

class Abuser(SuperDoc):
    
    _collection_name = 'test'
    
    item_id = unicode
    user_id = unicode
    
    user = relation('User',pk='_id==user_id',listmode=False)

class ProductItem(SuperDoc):
    
    _collection_name = 'test'
    
    # prduct state = 1.new, 2.second, 3.builtup etc

    NEW = 1
    SECOND = 2
    BUILTUP = 3

    market_id = unicode
    name = unicode
    description = unicode
    category_id = int
    _overview = unicode
    currency_id = unicode
    _price = float
    _stock = int
    auction = bool
    auction_expired = bool
    _starter_bid = float
    _min_bid_addition = float
    keywords = unicode
    condition = int  # prduct condition = 1.new, 2.second, 3.buuiltup etc
    related_review_link = unicode
    _permalink = unicode
    _allow_comment = bool
    pic_thumbnail = unicode
    status = int # prduct status = 1.available 2.sold 3.booked 4.delivered 5.pending 6.blank
    status_relatedto_user_id = int # ex. sold to kocakboy
    top_order = int
    _auto_approve_bid = bool
    _creation_time = datetime_type
    _last_updated = datetime_type
    _last_updated_by = unicode
    _update_reason = unicode
    _closed = bool
    _closed_permanently = bool
    _closed_time = datetime_type
    _sold = bool
    _sold_time = datetime_type
    _out_of_stock = bool
    _rank_level = int
    _suspended = bool
    _suspended_info = unicode
    _deleted = bool
    _deleted_time = datetime_type
    _last_bid_update = datetime_type
    _hash = int
    
    recommenders = list
    viewers = list

    market = relation('Market', pk='_id==market_id',listmode=False)
    bids = relation('Bidder', pk='product_item_id==_id')
    abuser = relation('Abuser', pk='product_item_id==_id')
    currency = relation('Currency', pk='_id==currency_id')
    comments = relation('Comment', pk='product_item_id==_id')
    category = relation('ProductItemCategory', pk='_id==category_id',listmode=False)
    last_editor = relation('User',pk='_last_updated_by==_id')
    blacklist_user_bids = relation('BadBidder',pk='product_item_id==_id')
    subscribers = relation('Subscription',pk='product_item_id==_id')

    @property
    def condition_str(self):
        '''Buat dapetin string kondisi barang
        '''
        return {
            self.SECOND: _("Second"),
            self.NEW: _("New"),
            self.BUILTUP: _("Built up")
        }.get(self.status,self.SECOND)

    @property
    def closed_permanently(self):
        '''Untuk memeriksa apakah item ditutup oleh system admin dan tidak bisa dikembalikan lagi.
        Gunakan _closed_permanently untuk akses secara langsung
        '''
        return self._closed_permanently and True or False

    @property
    def closed(self):
        '''Untuk memeriksa apakah item ditutup oleh pemilik (seller), masih bisa dikembalikan lagi oleh seller
        Gunakan _closed untuk akses secara langsung
        '''
        return (self._closed or self._closed_permanently) and True or False

    @property
    def deleted(self):
        '''Untuk memeriksa apakah item telah dihapus
        Gunakan _deleted untuk akses secara langsung
        '''
        return self._deleted and True or False

    @property
    def deleted_time(self):
        '''Untuk mendapatkan waktu terformat kapan item dihapus
        gunakan _deleted_time untuk akses secara langsung
        '''
        return self._deleted_time.strftime('%a, %d/%m/%Y %H:%M:%S')

    @property
    def sold(self):
        '''Untuk memeriksa apakah produk item telah terjual atau tidak,
        sinonim dari _sold. gunakan _sold untuk akses secara langsung
        '''

        return self._sold and True or False

    @property
    def sold_time(self):
        '''Untuk mendapapatkan waktu terformat kapan produk item telah terjual
        '''

        return self._sold_time.strftime('%a, %d/%m/%Y %H:%M:%S')

    @property
    def suspended(self):
        '''Untuk mengetahui apakah item di-suspend atau tidak
        Gunakan _suspended untuk akses secara langsung
        '''
        return self._suspended and True or False

    @property
    def suspend_reason(self):
        '''Untuk mendapatkan iformasi kenapa item di-suspend
        Gunakan _suspended_info untuk akses secara langsung
        '''
        return self._suspended_info

    @property
    def out_of_stock(self):
        '''Untuk memeriksa apakan item habis (out of stock)
        Gunakan _out_of_stock untuk akses secara langsung
        '''
        return self._out_of_stock and True or False


    @property
    def permalink(self):
        '''Get product link. Use _permalink instead for direct modification
        '''
        return "/%s/%d/%s" % (link_pitem_permalink_prefix,self.id, self._permalink.encode('utf-8'))

    @property
    def bid_permalink(self):
        '''Get product bid permalink. use _permalink instead for direct modification
        '''
        pass

    @property
    def thumbnail_path(self):
        '''Get thumbnail image path/url. use thumbnail instead for modification
        '''

        rv = ""

        if self.pic_thumbnail:
            rv = "%s%s" % (link_pitem_thumbnail_path,self.pic_thumbnail.encode('utf-8'))
        else:
            rv = "%sno_image.gif" % link_pitem_thumbnail_path

        return rv

    @property
    def auction_expiration_time(self):

        return self.auction_expired.strftime('%a, %d/%m/%Y %H:%M:%S')


    @property
    def owner_permalink(self):
        '''Get owner home link
        '''

        return "/%s" % self.market.owner.name

    @property
    def market_permalink(self):
        '''Get owner market link
        '''

        return "/%s/market/" % self.market.owner.name

    @property
    def expired(self):
        import datetime

        # generate auction status (expired or not)
        if self.auction:
            return self.auction_expired <= datetime.datetime.now()
        return False

    def stockable(self):
        if not self._stock:
            return False
        if self._stock > 0:
            return True
        return False

    @property
    def price(self):
        '''Synonym for _price that will automatically format currency.
        If you want to directly access to this attribute, use _price instead.
        '''


        if self._price==0:
            return "Free"

        if self.currency:
            rv = "%s %s %s" % (self.currency.sign_first, format_numeric(self._price), self.currency.sign_last)
        else:
            rv = _('various')

        return rv

    @property
    def starter_bid(self):
        '''Synonym for _starter_bid that will automatically format currency.
        If you want to directly access to this attribute, use _starter_bid instead.
        '''

        rv = "%s %s %s" % (self.currency.sign_first, format_numeric(self._starter_bid), self.currency.sign_last)

        return rv

    @property
    def min_bid_addition(self):
        '''Synonym for _min_bid_addition that will automatically format currency.
        If you want to directly access to this attribute, use _min_bid_addition instead.
        '''

        rv = "%s %s %s" % (self.currency.sign_first, format_numeric(self._min_bid_addition), self.currency.sign_last)

        return rv

    @property
    def overview(self):
        '''Synonym for _overview that will automatically format overview, to encode first for spoiler, emoticon, etc...
        If you want to directly access to this attribute, use _overview instead.
        '''

        if self.have_overview:
            self._overview

        return _("doesn't have overview")
    
    @property
    def have_overview(self):
        
        return (self._overview and len(self._overview)>0)


    def short_name(self,width=100):
        '''nggo jeneng ning format sing dipendekake + ...
        '''
        if len(self.name) > width:
            return '%s...' % self.name[:width]
        return self.name

    def short_description(self, width):
        '''Untuk mendapatkan deskripsi yang dipendekkan dan ditambah '...'
        '''
        if len(self.description) > width:
            return "%s..." % self.description[:width]
        return self.description

    @property
    def creation_time(self):
        '''Mendapatkan informasi tanggal dan waktu pembuatan dalam format yang standar
        '''
        return self._creation_time.strftime('%a, %d/%m/%Y %H:%M:%S')

    @property
    def updated_time(self):
        '''Untuk mendapatkan info kapan terakhir item diperbaharui
        Gunakan _updated_time untuk akses secara langsung
        '''
        return self._last_updated_by.strftime('%a, %d/%m/%Y %H:%M:%S')

    @property
    def last_bid_updated_time(self):
        '''Untuk mendapatkan kapan terakhir bid diperbaharui
        Gunakan _last_bid_update untuk akses secara langsung
        '''
        return self._last_bid_update.strftime('%a, %d/%m/%Y %H:%M:%S')

    @property
    def comment_allowed(self):
        '''Untuk memeriksa apakah produk item boleh dikomentari.
        berdasarkan atribut .`_allow_comment`
        '''
        return self._allow_comment and True or False

    @property
    def keywords_list(self):
        '''Mengembalikan keywords in separated list
        '''
        if self.keywords and len(self.keywords)>0:
            return tuple(map(lambda x: x.strip(),self.keywords.split(',')))
        return tuple()

    @property
    def hash(self):
        '''Get hash, synonym for ._hash
        '''
        return self._hash

class Viewer(SuperDoc):
    
    _collection_name = 'test'
    
    user_id = unicode

    user = relation('User',pk='_id==user_id',listmode=False)


class Bidder(SuperDoc):
    
    _collection_name = 'test'
    
    product_item_id = unicode
    bidder_user_id = unicode
    _amount = float
    bid_datetime = datetime_type
    additional_info = unicode
    _approved = bool

    product_item = relation('ProductItem', pk='_id==product_item_id')
    user = relation('User',pk='_id==user_id',listmode=False)

    @property
    def amount(self):
        '''Synonym for _amount. get formated amount in currency format.
        for direct access, use _amount instead
        '''
        return "%s %s %s" % (self.product_item.currency.sign_first, format_numeric(self._amount), self.product_item.currency.sign_last)

    @property
    def applied_on(self):
        '''mendapatkan waktu bid (bid_datetime) yang terformat
        '''
        return self.bid_datetime.strftime("%a, %d/%m/%Y %H:%M:%S")

class Recommend(SuperDoc):
    
    _collection_name = 'test'
    
    product_item_id = unicode
    user_id = unicode

    user = relation('User',pk='_id==user_id',listmode=False)
    item = relation('ProductItem',pk='_id==product_item_id',listmode=False)

class ProductItemCategory(SuperDoc):
    
    _collection_name = 'test'
    
    name = unicode
    keywords = list
    parent_id = unicode
    active = bool

    parent = relation('ProductItemCategory',pk='_id==parent_id',listmode=False)
    subcategory = relation('ProductItemCategory',pk='parent_id==_id',listmode=False)
    product_items = relation('ProductItem',pk='category_id==_id')

    @property
    def product_item_count(self):
        return self.product_items.count()

    @property
    def url(self):
        '''Mendapatkan url terformat alamat link ke kategori produk item
        '''

        category = self

        p = []
        while category:
            p.append(category.name)
            category = category.parent

        p.reverse()

        import urllib
        rv = urllib.quote('/%s/category/%s/' %
                          ( product,
                           '/'.join(p)),
                          '/:?&='
                          )
        return rv


class Subscription(SuperDoc):
    
    _collection_name = 'test'
    
    user_id = unicode
    product_item_id = unicode
    active = bool

    user = relation('User',pk='_id==user_id')
    item = relation('ProductItem',pk='_id==product_item_id')

class Currency(SuperDoc):
    
    _collection_name = 'test'
    
    name = unicode
    sign_first = unicode
    sign_last = unicode


class BadBidder(SuperDoc):
    
    _collection_name = 'test'
    
    user_id = unicode
    _active = bool

    
class Comment(SuperDoc):
    
    _collection_name = 'test'
    
    itemid = unicode
    wuid = long
    message = unicode
    _creation_time = datetime.datetime
    
    item = relation('Item',pk='_id==itemid',listmode=False)
    writter = relation('User',pk='_id==wuid',listmode=False)
    
    _opt = {
        'req' : ['itemid','wuid','content'],
        'default' : {'_creation_time':datetime.datetime.now}
    }
    

class parent(SuperDoc):
    _collection_name = 'test'

    childs = relation('child',pk='parent_id==_id',type='one-to-many')

class child(SuperDoc):
    _collection_name = 'test'
    
    parent_id = unicode
    
    parent = relation('child',pk='_id==parent_id',type='one-to-one')
    

mapper(User,
       WallPost,
       Message,
       ChatMessage,
       UserNotification,
       UserCart,
       UserActivity,
       Market,
       MarketPost,
       Testimonial,
       Visitor,
       Abuser,
       ProductItem,
       Viewer,
       Bidder,
       Recommend,
       ProductItemCategory,
       Subscription,
       Currency,
       BadBidder,
       Comment,
       PostMany,
       Tags,
       PostFlip,
       TagFlip,
       parent,
       child
       )


if __name__ == '__main__':
    
    
    monga = MongoDB('anvie','','','127.0.0.1',27017)
    print 'connected:',monga.connected
    
    #user = monga.col(User).find_one(name='anvie')
    #print user.wallposts
    
    import unittest
    
    class mongo_test(unittest.TestCase):
        
        def setUp(self):
            self.monga = monga
            monga._db.test.remove({})
            
        def test_chain_effects(self):
            
            post = monga.col(PostMany).new(isi='root')
            post.posts.append(PostMany(isi='sub1a'))
            post.posts.append(PostMany(isi='sub1b'))
            post.tags.append(Tags(isi=['mouse','cat']))
            post.tags[0].posts.append(PostMany(isi='post at mouse and cat tags'))
            post.posts[0].posts.append(PostMany(isi='sub2a'))
            post.posts[0].posts.append(PostMany(isi='sub2b'))
            post.posts[0].posts.append(PostMany(isi='sub2c'))
            post.posts[1].tags.append(Tags(isi=['sub1b tags']))
            post.tags[0].posts[0].tags.append(Tags(isi=['anvie','luna','exa']))
            post.tags[0].posts[0].tags.append(Tags(isi=['sky','walker']))
            
            post.save()
            
            del post
            
            post = monga.col(PostMany).find_one(isi='root')
            
            self.assertEqual(post.isi,'root')
            self.assertTrue( hasattr(post,'_id') )
            self.assertEqual( post.posts.count(), 2 )
            self.assertEqual( post.posts[0].isi, 'sub1a')
            self.assertEqual( post.posts[1].isi, 'sub1b')
            self.assertEqual( post.tags.count(), 1 )
            self.assertEqual( post.tags[0].posts[0].isi, 'post at mouse and cat tags' )
            self.assert_( 'mouse' in post.tags[0].isi and 'cat' in post.tags[0].isi )
            self.assertEqual( post.posts[1].tags[0].isi, ['sub1b tags'] )
            self.assert_( 'exa' in post.tags[0].posts[0].tags[0].isi )
            self.assertEqual( post.posts[1].posts.count(), 0  )
            subpost = post.tags[0].posts[0]
            self.assertEqual( subpost.tags.count(), 2 )
            self.assertEqual( post.tags[0].posts.count(), 1 )
            del post.tags[0].posts[0]
            post.save()
            self.assertEqual( post.tags[0].posts.count(), 0 )
            
            
        def test_user_wallpost_comment(self):
            
            usercol = monga.col(User)
            
            usercol.query(name='tester').remove()
            
            tester = User(name='tester')
            usercol.insert(tester)
            
            user = usercol.find_one(name='tester')
            
            self.assertTrue( user, None )
            
            user.wallposts.append(WallPost(message='tester is test',via='unitest'))
            user.save()
            
            self.assertEqual( user.wallposts.count(), 1 )
            self.assertEqual( user.wallposts[0].message, 'tester is test' )
            
            del user.wallposts[0]
            user.save()
            
            self.assertEqual( user.wallposts.count(), 0 )
            user.delete()

            self.assertEqual( usercol.find(name='tester').count(), 0 )
            
            
        def test_single_relation(self):
            
            monga._db.test.remove({})
            
            usercol = monga.col(User)
            
            obin = usercol.new(name='Obin MF')
            obin.save()
            
            market = monga.col(Market).new(name='Market Keren')
            market.save()
            
            obin.market = market
            
            obin.save()
            
            self.assertEqual( obin.market.name, 'Market Keren' )
            self.assertEqual( market.owner.name, 'Obin MF' )

        def test_metaname(self):
            
            monga.col(PostMany).query().remove()
            monga.col(Tags).query().remove()
            
            self.assertEqual( monga.col(Tags).find().count() , 0 )
            
            monga.col(User).query().remove()
            
            user = monga.col(User).new(name='new_user')
            post = monga.col(PostMany).new(isi='apakekdah')
            post.posts.append(PostMany(isi='apaya'))
            post.tags.append(Tags(isi=['tags ajah']))
            
            user.save()
            post.save()
            
            del user
            del post
            
            user = monga.col(User).find_one(name='new_user')
            post = monga.col(PostMany).find_one(isi='apakekdah')
            
            self.assertEqual( user.name, 'new_user' )
            self.assertEqual( post.isi, 'apakekdah' )
            self.assertEqual( post.posts.count(), 1 )
            self.assertEqual( post.posts[0].isi, 'apaya' )
            self.assertEqual( post.tags.count(), 1 )
            self.assertEqual( post.tags[0].isi, ['tags ajah'] )
            self.assert_( hasattr(user.__dict__['_data'], '_metaname_') )
            self.assertEqual( user.__dict__['_data']._metaname_, 'User' )
            self.assertEqual( post.__dict__['_data']._metaname_, 'PostMany' )
            self.assertEqual( post.tags[0].__dict__['_data']._metaname_, 'Tags' )
            
            self.assertEqual( monga.col(Tags).find().count() , 1 )
            
            post.tags.append(Tags(isi=['tags ajah-2']))
            
            post.save()
            
            self.assertEqual( monga.col(Tags).find().count() , 2 )
            
            monga.col(User).query(user_id=55).remove()
            
            monga.col(PostMany).query().remove()
            
            self.assertEqual( monga.col(Tags).count(), 2 )
            
            monga.col(Tags).query(isi='tags ajah').remove()
            
            self.assertEqual( monga.col(Tags).count(), 1 )
            
            monga.col(Tags).query(isi='tags ajah-2').remove()
            
            self.assertEqual( monga.col(Tags).count(), 0 )
            
            post.tags.append( Tags(isi=['123a']) )
            post.tags.append( Tags(isi=['123a']) )
            post.tags.append( Tags(isi=['123b']) )
            post.tags.append( Tags(isi=['123b']) )
            
            post.save()
            
            self.assertEqual( post.tags.count(), 4 )
            self.assertEqual( monga.col(Tags).count(), 4 )
            self.assertEqual( monga.col(Tags).count(isi='123a'), 2 )
            self.assertEqual( monga.col(Tags).count(isi='123b'), 2 )
            
            monga.col(Tags).query(isi='123a').remove()
            
            self.assertEqual( monga.col(Tags).count(), 2 )
            
            monga.col(Tags).query(isi='123b').remove()
            
            self.assertEqual( monga.col(Tags).count(), 0 )
            
            
        def test_extended(self):
            
            monga.col(Tags).query().remove()
            
            tags1 = monga.col(Tags).new(isi=['cat','lazy','dog'])
            tags2 = monga.col(Tags).new(isi=['animal','cat','pet'])
            tags3 = monga.col(Tags).new(isi=['pet','health','cat'])
            tags4 = monga.col(Tags).new(isi=['bird','animal'])
            
            tags1.save()
            tags2.save()
            tags3.save()
            tags4.save()
            
            self.assertEqual( tags1.get_related_tags().count(), 2 )
            self.assertEqual( tags4.get_related_tags().count(), 1 )
            
        def test_flipflap_relation(self):
            
            monga._db.test.remove({})
            
            post1 = monga.col(PostFlip).new(isi='post-1')
            post2 = monga.col(PostFlip).new(isi='post-2')
            post3 = monga.col(PostFlip).new(isi='post-3')
            post4 = monga.col(PostFlip).new(isi='post-4')
            
            cat = TagFlip(isi='cat')
            lazy = TagFlip(isi='lazy')
            dog = TagFlip(isi='dog')
            animal = TagFlip(isi='animal')
            bird = TagFlip(isi='bird')
            
            monga.col(TagFlip).insert(cat)
            monga.col(TagFlip).insert(lazy)
            monga.col(TagFlip).insert(dog)
            monga.col(TagFlip).insert(animal)
            monga.col(TagFlip).insert(bird)
            
            post1.tags.append(cat)
            post1.tags.append(lazy)
            post1.tags.append(dog)
            
            post2.tags.append(animal)
            post2.tags.append(cat)
            post2.tags.append(bird)
            
            post3.tags.append(animal)
            post3.tags.append(bird)
            
            post4.tags.append(animal)
            
            post1.save()
            post2.save()
            post3.save()
            post4.save()
            
            self.assertEqual( post1.tags.count(), 3 )
            self.assertEqual( post2.tags.count(), 3 )
            self.assertEqual( post3.tags.count(), 2 )
            
            self.assertEqual( post1.tags[0].isi, 'cat' )
            
            post1.tags[0].refresh()
            post3.tags[0].refresh()
            
            self.assertEqual( post1.tags[0].posts.count(), 2 )
            self.assertEqual( post3.tags[0].posts.count(), 3 )
            
            post5 = PostFlip(isi='sky')
            
            monga.col(PostFlip).insert(post5)
            
            bird.posts.append(post5)
            bird.save()
            
            self.assertEqual( bird.posts.count(), 3 )
            
            # enter same tag test
            bird.posts.append(post5)
            bird.save()
            
            # seharusnya gak nambah
            self.assertEqual( bird.posts.count(), 3 )
            
            bird.posts.append(post1)
            bird.save()
            
            # test refresh
            self.assertTrue( post1.refresh() )
            
            self.assertEqual( post1.tags.count(), 4 )
            
            #
            # test relation many-to-many but uses model it self
            #
            user = monga.col(User).new(name='ada-deh')
            
            exa = monga.col(User).new(name='exa-tester')
            didit = monga.col(User).new(name='didit-tester')
            
            exa.save()
            didit.save()
            
            user.friends.append(exa)
            user.friends.append(didit)
            
            user.save()
            
            self.assertEqual( user.friends.count(), 2 )
            
            exa.refresh()
            didit.refresh()
            
            self.assertEqual( exa.friends.count(), 1 )
            self.assertEqual( didit.friends.count(), 1 )
            
            exa.friends.append( didit )
            exa.save()
            
            self.assertEqual( exa.friends.count(), 2 )
            
            exa.friends.remove( didit )
            
            exa.save()
            #exa.refresh()
            
            self.assertEqual( exa.friends.count(), 1 )
            self.assertEqual( exa.friends[0].name, 'ada-deh')
            
            self.assertTrue( exa in user.friends )
            self.assertTrue( didit in user.friends )
            
            didit.delete()
            
            user.refresh()
            
            self.assertTrue( didit not in user.friends )
            self.assertTrue( exa in user.friends )
            
            exa.delete()
            
            user.refresh()
            
            self.assertTrue( exa not in user.friends )
            self.assertEqual( user.friends.count(), 0 )
            
            del user
            
        
        def test_data_type(self):
            
            monga._db.test.remove({})
            
            post = monga.col(PostMany).new(isi='test')
            post.save()
            
            post.nomor = 5
            post.yatidak = True
            
            post.save()
            del post
            
            post = monga.col(PostMany).find_one(isi='test')
            
            self.assertEqual( post.nomor, 5 )
            
            
        def test_many_child(self):
            
            monga._db.test.remove({})
            
            pa = monga.col(parent).new(name='anvie-keren')
            
            pa.childs.append(child(name='c1'))
            pa.childs.append(child(name='c2'))
            pa.childs.append(child(name='c3'))
            pa.childs.append(child(name='c4'))
            pa.childs.append(child(name='c5'))
            pa.childs.append(child(name='c6'))
            pa.childs.append(child(name='c7'))
            pa.childs.append(child(name='c8'))
            pa.childs.append(child(name='c9'))
            pa.childs.append(child(name='c10'))
            pa.childs.append(child(name='c11'))
            pa.childs.append(child(name='c12'))
            pa.childs.append(child(name='c13'))
            pa.childs.append(child(name='c14'))
            pa.childs.append(child(name='c15'))
            pa.childs.append(child(name='c16'))
            
            pa.save()
            
            del pa
            pa = monga.col(parent).find_one(name='anvie-keren')
            
            self.assertEqual( pa.name, 'anvie-keren' )
            self.assertEqual( pa.childs[0].name, 'c1')
            self.assertEqual( pa.childs[13].name, 'c14') # lazy load test memory cache
            self.assertEqual( pa.childs[13].name, 'c14')
            self.assertEqual( pa.childs[12].name, 'c13') # lazy load test memory cache
            self.assertEqual( pa.childs[12].name, 'c13')
            
            # test pencarian di SuperDocList
            self.assertEqual( pa.childs.find(name='c3'), pa.childs[2] )
            
        def test_list_dict(self):
            
            monga._db.test.remove({})
            
            u = monga.col(User).new(name='anvie-keren')
            u.settings.test = 'is'
            u.save()
            
            del u
            
            u = monga.col(User).find_one(name='anvie-keren')
            
            self.assertEqual( u.name, 'anvie-keren' )
            self.assertEqual( u.settings.test, 'is')
            
            u.settings.oi = 'yeah'
            u.save()
            
            del u
            
            u = monga.col(User).find_one(name='anvie-keren')
            
            self.assertEqual( u.settings.oi, 'yeah' )

        
    def main():
        suite = unittest.TestLoader().loadTestsFromTestCase(mongo_test)
        unittest.TextTestRunner(verbosity=2).run(suite)
        
        # clean up
        #monga._db.test.remove({})
        
    main()
    #import cProfile
    #cProfile.run('main()','fooprof')
    #import pstats
    #p = pstats.Stats('fooprof')
    #p.strip_dirs().sort_stats(-1).print_stats()


    #raise 'test'
    
    
    
