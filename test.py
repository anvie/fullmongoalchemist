#!/usr/bin/env python

from fma import MongoDB, SuperDoc, Collection
from fma.orm import relation, query, this, mapper
from fma.antypes import *
from fma import connector
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
        return Collection( connector.db_instance,Tags ).find(isi__in=self.isi,_id__ne=self._id)
        
    

class PostFlip(SuperDoc):
    
    _collection_name = 'test'
    
    
    tags = relation('TagFlip',type='many-to-many',keyrel='_tags:_id',backref='_posts:_id')
    
    
class TagFlip(SuperDoc):
    
    _collection_name = 'test'
    
    posts = relation('PostFlip',type='many-to-many',keyrel='_posts:_id',backref='_tags:_id')
    
    

class User(SuperDoc):

    _collection_name = 'test'
    
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


class WallPost(SuperDoc):

    _collection_name = 'test'
    
    wuid = unicode
    ruid = unicode
    
    message = unicode
    via = unicode
    _creation_time = datetime.datetime
    
    writer = relation('User',pk='_id==wuid', listmode=False)
    receiver = relation('User',pk='_id==ruid', listmode=False)
    comments = relation('Comment',pk='itemid==_id', cascade='delete')
    
    _opt = {
        'req' : ['message','via'],
        'default' : dict(_creation_time=datetime.datetime.utcnow),
        'strict' : True
    }
    

        
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

    owner = relation('User', pk='_id==to_user_id', type='one-to-one')
    sender =  relation('User', pk='_id==from_user_id', type='one-to-one')

    @property
    def readed(self):
        return self._readed

    @property
    def replied(self):
        return self._replied

    @property
    def deleted(self):
        return self._deleted

    
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
    posts = relation('MarketPost',pk='market_id==_id',type="one-to-many")
    testi = relation('Testimonial',pk='market_id==_id')



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
    category_code = int
    _overview = unicode
    currency_code = int
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
    _last_updated_by = unicode  # user id
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
    guest_view_count = int

    market = relation('Market', pk='_id==market_id',listmode=False)
    bids = relation('Bidder', pk='product_item_id==_id')
    abuser = relation('Abuser', pk='product_item_id==_id')
    currency = relation('Currency', pk='code==currency_code',type='one-to-one')
    comments = relation('Comment', pk='item_id==_id')
    category = relation('ProductItemCategory', pk='code==category_code',type='one-to-one')
    last_editor = relation('User',pk='_id==_last_updated_by',type='one-to-one')
    blacklist_user_bids = relation('BadBidder',pk='product_item_id==_id')
    subscribers = relation('ProductItemSubscription',pk='product_item_id==_id')


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
    code = int
    parent_code = unicode
    active = bool

    parent = relation('ProductItemCategory',pk='code==parent_code',listmode=False)
    subcategories = relation('ProductItemCategory',pk='parent_code==code',type='one-to-many')
    product_items = relation('ProductItem',pk='category_code==code',type='one-to-many')


class ProductItemSubscription(SuperDoc):
    
    _collection_name = 'test'
    
    user_id = unicode
    product_item_id = unicode
    active = bool

    user = relation('User',pk='_id==user_id',type='one-to-one')
    item = relation('ProductItem',pk='_id==product_item_id',type='one-to-one')

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
    
    item_id = unicode
    writer_id = unicode
    message = unicode
    _creation_time = datetime_type
    _last_edited = datetime_type
    
    writer = relation('User',pk='_id==writer_id',listmode=False)
    
    _opt = {
        'req' : ['item_id','writer_id','message','_creation_time'],
        'default' : {'_creation_time':datetime.datetime.utcnow}
    }
    

class parent(SuperDoc):
    _collection_name = 'test'

    childs = relation('child',pk='parent_id==_id',type='one-to-many',cascade='delete')
    childs_spec = query("child",dict(_teacher_ids = this("_id")))
    childs_co = query("child",dict(gender="pria"))
    childs_ce = query("child",dict(gender="wanita"))

# untuk test many-to-one
class another_parent1(SuperDoc):
    _collection_name = 'test'
    
    
    childs = relation('child',pk='another_parent_id==_id',type='one-to-many',cascade='delete', backref = 'another_parent')

class another_parent2(SuperDoc):
    _collection_name = 'test'
    
    childs = relation('child',pk='another_parent_id==_id',type='one-to-many',cascade='delete', backref = 'another_parent')



class child(SuperDoc):
    
    _collection_name = 'test'
    
    parent_id = unicode
    another_parent_id = unicode
    gender = options("pria","wanita")
    _teacher_ids = list
    
    parent = relation('child',pk='_id==parent_id',type='one-to-one')
    another_parent = relation(pk='another_parent_id',type='many-to-one')
    
    
#
# test inheritance
#
class Employee(SuperDoc):
    
    _collection_name = "test"
    
    name = unicode
    age = int
    _position = unicode
    _credential_id = unicode
    
    def get_sallary(self):
        return self.sallary
    
class OutSourcer(SuperDoc):
    
    _active = bool
    
    _opt = {
        "default" : {
            "_active" : True
        }
    }
    
    def set_active(self,active):
        self._active = active
        
    
class Programmer(Employee, OutSourcer):
    
    sallary = 8000000
    
    division = unicode
    
    tools = relation("Resource",pk="user_id==_id",type="one-to-many")
    
    
class Marketing(Employee):
    
    sallary = 5000000
    
class CoProgrammer(Programmer):
    
    salarry = 5000000
    _position = "Co Programmer"
    
    @property
    def position(self):
        return self._position
    
class Resource(SuperDoc):
    
    _collection_name = "test"
    
    user_id = unicode
    name = unicode
    price = long
    
    
    owner = relation("Programmer",pk="_id==user_id",type="one-to-one")
    
    
class VariantTest(SuperDoc):
    _collection_name = "test"
    
    value = variant()
    

mapper(User,
       WallPost,
       Message,
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
       ProductItemSubscription,
       Currency,
       BadBidder,
       Comment,
       PostMany,
       Tags,
       PostFlip,
       TagFlip,
       parent,
       child,
       another_parent1,
       another_parent2,
       Employee, Programmer, CoProgrammer, Marketing,
       Resource
       )


if __name__ == '__main__':
    
    
    #self.db = MongoDB('anvie','','','127.0.0.1',27017,dict(nometaname=False))
    #print 'connected:',self.db.connected
    
    from fma import connect
    global db_connection
    db_connection = connect("test")
    
    ## using python remote debugger
    #from dbgp.client import brk; brk()
    
    import unittest
    
    class mongo_test(unittest.TestCase):
        
        def setUp(self):
            from fma import connector
            #from dbgp.client import brk; brk()
            global db_connection
            self.connected = db_connection
            connector.db_instance._db.test.remove({})
            self.db = connector.db_instance
            
        def test_chain_effects(self):
            
            post = self.db.col(PostMany).new(isi='root')
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
            
            post = self.db.col(PostMany).find_one(isi='root')
            
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
            
            usercol = self.db.col(User)
            
            usercol.query(name='tester').remove()
            
            tester = User(name='tester')
            usercol.insert(tester)
            
            user = usercol.find_one(name='tester')
            
            self.assertTrue( user, None )
            #from dbgp.client import brk; brk()
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
            '''Single relation (one-to-one) test
            '''
            
            self.db._db.test.remove({})
            
            usercol = self.db.col(User)
            
            obin = usercol.new(name='Obin MF')
            obin.save()
            
            market = self.db.col(Market).new(name='Market Keren')
            market.save()
            
            #from dbgp.client import brk; brk()
            obin.market = market
            
            obin.save()
            
            self.assertEqual( obin.market.name, 'Market Keren' )
            self.assertEqual( market.owner.name, 'Obin MF' )

        def test_metaname(self):
            '''Metaname test
            '''
            
            self.db.col(PostMany).query().remove()
            self.db.col(Tags).query().remove()
            
            self.assertEqual( self.db.col(Tags).find().count() , 0 )
            
            self.db.col(User).query().remove()
            
            user = self.db.col(User).new(name='new_user')
            post = self.db.col(PostMany).new(isi='apakekdah')
            post.posts.append(PostMany(isi='apaya'))
            post.tags.append(Tags(isi=['tags ajah']))
            
            user.save()
            post.save()
            
            del user
            del post
            
            user = self.db.col(User).find_one(name='new_user')
            post = self.db.col(PostMany).find_one(isi='apakekdah')
            
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
            
            self.assertEqual( self.db.col(Tags).find().count() , 1 )
            
            post.tags.append(Tags(isi=['tags ajah-2']))
            
            post.save()
            
            self.assertEqual( self.db.col(Tags).find().count() , 2 )
            
            self.db.col(User).query(user_id=55).remove()
            
            self.db.col(PostMany).query().remove()
            
            self.assertEqual( self.db.col(Tags).count(), 2 )
            
            self.db.col(Tags).query(isi='tags ajah').remove()
            
            self.assertEqual( self.db.col(Tags).count(), 1 )
            
            self.db.col(Tags).query(isi='tags ajah-2').remove()
            
            self.assertEqual( self.db.col(Tags).count(), 0 )
            
            post.tags.append( Tags(isi=['123a']) )
            post.tags.append( Tags(isi=['123a']) )
            post.tags.append( Tags(isi=['123b']) )
            post.tags.append( Tags(isi=['123b']) )
            
            post.save()
            
            self.assertEqual( post.tags.count(), 4 )
            self.assertEqual( self.db.col(Tags).count(), 4 )
            self.assertEqual( self.db.col(Tags).count(isi='123a'), 2 )
            self.assertEqual( self.db.col(Tags).count(isi='123b'), 2 )
            
            self.db.col(Tags).query(isi='123a').remove()
            
            self.assertEqual( self.db.col(Tags).count(), 2 )
            
            self.db.col(Tags).query(isi='123b').remove()
            
            self.assertEqual( self.db.col(Tags).count(), 0 )
            
            
        def test_extended(self):
            
            self.db.col(Tags).query().remove()
            
            tags1 = self.db.col(Tags).new(isi=['cat','lazy','dog'])
            tags2 = self.db.col(Tags).new(isi=['animal','cat','pet'])
            tags3 = self.db.col(Tags).new(isi=['pet','health','cat'])
            tags4 = self.db.col(Tags).new(isi=['bird','animal'])
            
            tags1.save()
            tags2.save()
            tags3.save()
            tags4.save()
            
            self.assertEqual( tags1.get_related_tags().count(), 2 )
            self.assertEqual( tags4.get_related_tags().count(), 1 )
            
        def test_flipflap_relation(self):
            
            self.db._db.test.remove({})
            
            post1 = self.db.col(PostFlip).new(isi='post-1')
            post2 = self.db.col(PostFlip).new(isi='post-2')
            post3 = self.db.col(PostFlip).new(isi='post-3')
            post4 = self.db.col(PostFlip).new(isi='post-4')
            
            cat = TagFlip(isi='cat')
            lazy = TagFlip(isi='lazy')
            dog = TagFlip(isi='dog')
            animal = TagFlip(isi='animal')
            bird = TagFlip(isi='bird')
            
            self.db.col(TagFlip).insert(cat)
            self.db.col(TagFlip).insert(lazy)
            self.db.col(TagFlip).insert(dog)
            self.db.col(TagFlip).insert(animal)
            self.db.col(TagFlip).insert(bird)
            
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
            
            self.db.col(PostFlip).insert(post5)
            
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
            user = self.db.col(User).new(name='ada-deh')
            
            exa = self.db.col(User).new(name='exa-tester')
            didit = self.db.col(User).new(name='didit-tester')
            
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
            #from dbgp.client import brk; brk()
            self.assertTrue( exa in user.friends )
            
            exa.delete()
            
            user.refresh()
            
            self.assertTrue( exa not in user.friends )
            self.assertEqual( user.friends.count(), 0 )
            
            del user
            
        
        def test_data_type(self):
            
            self.db._db.test.remove({})
            
            post = self.db.col(PostMany).new(isi='test')
            post.save()
            
            post.nomor = 5
            post.yatidak = True
            post.yatidak = 1
            post.yatidak = 0
            
            
            post.save()
            del post
            
            post = self.db.col(PostMany).find_one(isi='test')
            
            self.assertEqual( post.nomor, 5 )
            
            
        def test_many_child(self):
            
            self.db._db.test.remove({})
            
            pa = self.db.col(parent).new(name='anvie-keren')
            
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
            
            #from dbgp.client import brk; brk()
            
            del pa
            pa = self.db.col(parent).find_one(name='anvie-keren')
            
            self.assertEqual( pa.name, 'anvie-keren' )
            self.assertEqual( pa.childs[0].name, 'c1')
            
            #from dbgp.client import brk; brk()
            
            self.assertEqual( pa.childs[13].name, 'c14') # lazy load test memory cache
            self.assertEqual( pa.childs[12].name, 'c13') # lazy load test memory cache
            self.assertEqual( pa.childs[12].name, 'c13')
            
            # test pencarian single item
            self.assertEqual( pa.childs.find(name='c3'), pa.childs[2] )
            
            # test pencarian menggunakan metode filter
            rv = pa.childs.filter(name__in=['c5','c12'])
            self.assertEqual( rv.count(), 2 )
            self.assertEqual( rv.all()[0].name, 'c5' )
            
            # test clear all
            self.assertNotEqual(pa.childs.count(),0)
            pa.childs.clear()
            self.assertEqual(pa.childs.count(),0)
            
        def test_list_dict(self):
            
            self.db._db.test.remove({})
            
            u = self.db.col(User).new(name='anvie-keren')
            u.settings.test = 'is'
            u.save()
            
            del u
            
            u = self.db.col(User).find_one(name='anvie-keren')
            
            self.assertEqual( u.name, 'anvie-keren' )
            self.assertEqual( u.settings.test, 'is')
            
            u.settings.oi = 'yeah'
            u.save()
            
            del u
            
            u = self.db.col(User).find_one(name='anvie-keren')
            
            self.assertEqual( u.settings.oi, 'yeah' )
            
        def test_default_value(self):
            """Default and required value"""
            
            self.db._db.test.remove({})
            
            wp = WallPost(message='test',via='jakarta')
            wp.save()
            
            writer = User(name='anvie')
            
            #from dbgp.client import brk; brk()
            comment = self.db.col(Comment).new(message="hai test", item_id = wp._id, writer = writer)
            
            comment.save()
            
            self.assertNotEqual( comment._creation_time , None )
            
        def test_none_type(self):
            
            self.db._db.test.remove({})
            
            #from dbgp.client import brk; brk()
            
            msg = Message(subject='subject-test',content='content-test')
            msg.save()
            
            self.assertEqual( msg.owner, None)
            
            del msg
            
            msg = self.db.col(Message).find_one( subject = 'subject-test' )
            
            self.assertEqual( msg.owner, None)
            
            user = User(name='test-user')
            
            msg.owner = user
            
            msg.save()
            
            del msg
            
            msg = self.db.col(Message).find_one( subject = 'subject-test' )
            
            self.assertEqual( msg.owner.name, 'test-user')
            
            pitem_category = ProductItemCategory(name='Elektronik', code=38, parent_code=0, active=True)
            pitem_category.save()
            
            prod = self.db.col(ProductItem).new( name='test',description='test',category_code=38 )
            prod.save()
            
            del prod
            
            prod = self.db.col(ProductItem).find_one(name='test')
            
            self.assertEqual( prod.category.name, 'Elektronik')
            
        def test_map_reduce(self):
            '''about to test map reduce functionality.
            if your mongod become crash, please update your mongo to version >= 1.2.0,
            this test work fine in 1.2.0
            '''
            
            # from dbgp.client import brk; brk()
            
            self.db._db.test.remove({})
            
            class Item(SuperDoc):
                _collection_name = 'test'
                
                name = unicode
                tags = list
                
            self.db.col(Item).insert(Item(name='obin',tags=['keren','cool','nerd']))
            self.db.col(Item).insert(Item(name='imam',tags=['keren','funny','brother']))
            self.db.col(Item).insert(Item(name='nafid',tags=['brother','funny','notbad']))
            self.db.col(Item).insert(Item(name='uton',tags=['smart','cool','notbad']))
            self.db.col(Item).insert(Item(name='alfen',tags=['fat','nocool','huge']))
            
            map_ = '''function () {
              this.tags.forEach(function(z) {
                emit(z, 1 );
              });
            }'''
            
            reduce_ = '''function (key, values) {
              var total = 0;
              for (var i = 0; i < values.length; i++) {
                total += values[i];
              }
              return total;
            }'''

            rv = self.db.col(Item).map_reduce( map_, reduce_ )
            
            true_result = [
                {u'_id': u'brother', u'value': 2.0},
                {u'_id': u'cool', u'value': 2.0},
                {u'_id': u'fat', u'value': 1.0},
                {u'_id': u'funny', u'value': 2.0},
                {u'_id': u'huge', u'value': 1.0},
                {u'_id': u'keren', u'value': 2.0},
                {u'_id': u'nerd', u'value': 1.0},
                {u'_id': u'nocool', u'value': 1.0},
                {u'_id': u'notbad', u'value': 2.0},
                {u'_id': u'smart', u'value': 1.0}
            ]
            
            cr = rv.find()
            
            for i, x in enumerate(cr):
                self.assertEqual( x, true_result[i] )
                
            self.db._db.drop_collection(rv.result)
            

        def test_cascade(self):
            
            
            self.db._db.test.remove({})
            
            # from dbgp.client import brk; brk()
            
            obin = parent( name = 'obin' )
            
            obin.save()
            
            # from dbgp.client import brk; brk()
            anvie = child(name='anvie')
            anvie2 = child(name='anvie2')
            anvie3 = child(name='anvie3')
            
            
            obin.childs.append(anvie)
            obin.childs.append(anvie2)
            obin.childs.append(anvie3)
            
            
            obin.save()
            
            self.assertEqual(obin.childs.count(), 3)
            del obin.childs[-1]
            obin.save()
            self.assertEqual(obin.childs.count(), 2)
            self.assertEqual(obin.childs[0].name,'anvie')
            self.assertEqual(obin.childs[1].name,'anvie2')
            
            self.assertEqual(self.db.col(child).find(name='anvie').count(),1)
            
            #from dbgp.client import brk; brk()
            
            obin.delete()
            
            self.assertEqual(self.db.col(child).find(name='anvie').count(),0)
            self.assertEqual(self.db.col(child).find(name='anvie2').count(),0)
            
            
        def test_many_to_one(self):
            
                self.db._db.test.remove({})
                
                
                parent1 = another_parent1(name = 'parent1')
                
                parent2 = another_parent2(name = 'parent2')
                
                
                anvie1 = child(name='anvie1')
                anvie2 = child(name='anvie2')
                
                
                parent1.childs.append(anvie1)
                parent2.childs.append(anvie2)
                
                parent1.save()
                parent2.save()
                
                
                self.assertEqual( anvie1.another_parent.name, 'parent1' )
                self.assertEqual( anvie2.another_parent.name, 'parent2' )
                
        def test_options_type(self):
            
            self.db._db.test.remove({})
            
            #from dbgp.client import brk; brk()
            
            anvie = child(name="anvie", gender="wanita")
            try:
                anvie = child(name="anvie", gender="laki-laki")
            except:
                anvie = None
                
            self.assertEqual( anvie, None )
            
            anvie = child(name="anvie", gender="pria")
            
            anvie.save()
            
            self.assertEqual( anvie.gender, "pria" )
            
            
        def test_inheritance(self):
            """Inheritance
            """
            
            self.db._db.test.remove({})
            
            anvie = Employee(
                name = "anvie",
                age = 23
            )
            didit = Programmer(
                name = "didit",
                age = 23,
                division = "engine"
            )
            exa = Programmer(
                name = "exa",
                age = 27,
                division = "ui"
            )
            tommy = Marketing(
                name = "tommy",
                age = 31
            )
            mac = Resource(
                name = "macbook pro",
                price = 13000000
            )
            
            didit.tools.append(mac)
            
            # from dbgp.client import brk; brk()
            
            anvie.save()
            didit.save()
            exa.save()
            tommy.save()
            
            self.assertEqual(anvie.name,"anvie")
            self.assertEqual(didit.name,'didit')
            self.assertEqual(didit.sallary, 8000000)
            
            didit = self.db.col(Programmer).find_one(name="didit")
            
            self.assertNotEqual(didit, None)
            self.assertEqual(type(didit), Programmer)
            self.assertEqual(didit.get_sallary(), 8000000)
            
            self.assertEqual( didit.tools.count(), 1 )
            self.assertEqual( didit.tools[0].name, "macbook pro" )
            self.assertEqual( didit.tools[0].owner.name, "didit" )
        
            misbah = CoProgrammer(self.db,name="misbah")
            misbah.save()
            
            self.assertEqual(misbah.age,None)
            self.assertEqual(misbah.division,None)
            self.assertEqual(misbah.name,"misbah")
            self.assertEqual(misbah.position,"Co Programmer")
            self.assertEqual(misbah._credential_id,None)
            
            # test multiple inheritance
        
            self.assertEqual(exa._active,True)
            
            
        def test_query(self):
            '''Test query for update and delete.
            '''
            self.db._db.test.remove({})
            
            market = Market(name = "arcane")
            post = MarketPost(
                title = "Kartu keren",
                _content = "Content of Kartu keren"
            )
            post2 = MarketPost(
                title = "Kartu keren 2",
                _content = "Content of Kartu keren 2"
            )
            
            market.posts.append(post)
            market.posts.append(post2)
            
            market.save()
            
            market = self.db.col(Market).find_one(name="arcane")
            
            self.assertNotEqual(market,None)
            
            #from dbgp.client import brk; brk()
            
            posts = market.posts.all()
            
            self.assertEqual(len(posts),2)
            
            post_ids = [str(x._id) for x in posts]
            
            market.posts.query(_id__in = post_ids).remove()
            
            self.assertEqual(market.posts.count(),0)
            
            
        def test_query_relation(self):
            '''Relation query mode
            '''
            
            self.db._db.test.remove({})
            
            #from dbgp.client import brk; brk()
            
            p = parent(
                name = "robin"
            )
            p.childs.append(
                child(name = "imam",gender="pria")
            )
            p.childs.append(
                child(name = "yani",gender="wanita")
            )
            p.childs.append(child(name="anis",gender="wanita"))
            
            p.save()
            
            #from dbgp.client import brk; brk()
            
            self.assertEqual(p.childs_co.count(), 1)
            self.assertEqual(p.childs_ce.count(), 2)
            
            a = child(name="a",_teacher_ids=["ab8203faad","023984a5ee"]).save()
            b = child(name="b",_teacher_ids=["ab8203faad",str(p._id)]).save()

            
            self.assertEqual(p.childs_spec.count(),1)
            
            x = p.childs_spec.next()
            
            self.assertEqual(x,b)
            
            child(name="c",_teacher_ids=["ab8203faad",str(p._id)]).save()
            child(name="d",_teacher_ids=["ab8203faad",str(p._id)]).save()
            child(name="e",_teacher_ids=["ab8203faad",str(p._id)]).save()
            
            
            self.assertEqual(p.childs_spec.count(),4)
            
            child_names = ["b","c","d","e"]
            
            for i,son in enumerate(p.childs_spec):
                self.assertEqual(son.name, child_names[i])
                
            males = p.childs_co()
            females = p.childs_ce()
            
            self.assertEqual(males.count(), 1)
            self.assertEqual(females.count(), 2)
            
            
        def test_variant(self):
            """Variant type"""
            
            #from dbgp.client import brk; brk()
            a = VariantTest(value = 5)
            a.save()

            self.assertEqual(a.value, 5)
            
        
    def main():
        suite = unittest.TestLoader().loadTestsFromTestCase(mongo_test)
        unittest.TextTestRunner(verbosity=2).run(suite)
        
        # clean up
        #self.db._db.test.remove({})
        
    main()
    #import cProfile
    #cProfile.run('main()','fooprof')
    #import pstats
    #p = pstats.Stats('fooprof')
    #p.strip_dirs().sort_stats(-1).print_stats()


    #raise 'test'
    
    
    
