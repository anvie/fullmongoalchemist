#!/usr/bin/env python

from fma import MongoDB, SuperDoc, Collection
from fma.orm import relation, mapper
from fma.antypes import *

import datetime

#monga = MongoDB('anvie', '', '', '127.0.0.1', 27017)
#print 'mongoDB connected: ', monga.connected

class User(SuperDoc):

    _collection_name = 'test'
    
    user_id = int
    name = unicode
    pic_avatar = unicode
    profile_link = unicode
    _creation_time = datetime.datetime
    
    wallposts = relation('WallPost',pk='wuid==user_id',cond=or_(wuid=':user_id',ruid=':user_id'),listmode=True,cascade="delete")
    friends = relation('User',type='many-to-many',keyrel='_friends:_id',backref='_friends:_id')
    
    _opt = {
        'req' : ['user_id','name'],
        'default' : dict(name='', _creation_time=datetime.datetime.utcnow)
    }
    
    @property
    def creation_time(self):
        return self._creation_time and self._creation_time.strftime("%a, %d/%m/%Y %H:%M:%S %p") or 'unknown'
    
    
class WallPost(SuperDoc):

    _collection_name = 'test'
    
    wuid = int
    ruid = int
    
    message = unicode
    via = unicode
    _creation_time = datetime.datetime
    
    writter = relation('User',pk='user_id==wuid',listmode=False)
    receiver = relation('User',pk='user_id==ruid',listmode=False)
    comments = relation('WallPostComment',pk='puid==_id', cascade='delete')
    
    
    _opt = {
        'req' : ['wuid','ruid','message','via'],
        'default' : dict(_creation_time=datetime.datetime.utcnow),
        'strict' : True
    }
    
    @property
    def creation_time(self):
        return self._creation_time and self._creation_time.strftime("%a, %d/%m/%Y %H:%M:%S %p") or 'unknown'


class WallPostComment(SuperDoc):
    
    _collection_name = 'test'
    
    puid = unicode
    wuid = int
    
    message = unicode
    _creation_time = datetime.datetime
    
    post = relation('WallPost',pk='_id==puid',listmode=False)
    writter = relation('User',pk='user_id==wuid',listmode=False)
    
    
    _opt = {
        'req' : ['puid','wuid','message'],
        'default' : dict(_creation_time=datetime.datetime.utcnow),
        'strict' : True
    }
    
    @property
    def creation_time(self):
        return self._creation_time and self._creation_time.strftime("%a, %d/%m/%Y %H:%M:%S %p") or 'unknown'
    

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
    
    
    
mapper(User, WallPost, WallPostComment, PostMany, Tags, PostFlip, TagFlip)

if __name__ == '__main__':
    
    
    monga = MongoDB('anvie','','','127.0.0.1',27017)
    print 'connected:',monga.connected
    
    #user = monga.col(User).find_one(name='anvie')
    #print user.wallposts
    
    import unittest
    
    class mongo_test(unittest.TestCase):
        
        def setUp(self):
            self.monga = monga
            monga.col(PostMany).query().remove()
            
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
            
            user.wallposts.append(WallPost(message='tester is test',via='unitest',ruid=2,wuid=2))
            user.save()
            
            self.assertEqual( user.wallposts.count(), 1 )
            self.assertEqual( user.wallposts[0].message, 'tester is test' )
            
            del user.wallposts[0]
            user.save()
            
            self.assertEqual( user.wallposts.count(), 0 )
            user.delete()

            self.assertEqual( usercol.find(name='tester').count(), 0 )
            
            
        def test_single_relation(self):
            
            usercol = monga.col(User)
            
            usercol.query(name='tester').remove()
            monga.col(WallPost).query(ruid=77).remove()
            monga.col(WallPostComment).query(wuid=77).remove()
            
            tester = User(name='tester',user_id=77)
            usercol.insert(tester)
            
            
            tester.wallposts.append(WallPost(message='tester is test',via='unitest',ruid=77))
            
            tester.save()
            
            self.assertEqual( tester.wallposts.count(), 1 )
            
            tester.wallposts[0].comments.append(WallPostComment(message='hai hai-1',wuid=77))
            tester.wallposts[0].comments.append(WallPostComment(message='hai hai-2',wuid=77))
            
            tester.save()
            
            self.assertEqual( tester.wallposts[0].writter.name, 'tester' )
            self.assertEqual( tester.wallposts[0].comments.count(), 2 )
            self.assertEqual( tester.wallposts[0].comments[0].writter.name, 'tester')
            
            del tester.wallposts[0]
            tester.save()
            
            self.assertEqual( tester.wallposts.count(), 0 )
            self.assertEqual( monga.col(WallPostComment).find(wuid=77).count(), 0 )
            
        def test_metaname(self):
            
            monga.col(PostMany).query().remove()
            monga.col(Tags).query().remove()
            
            self.assertEqual( monga.col(Tags).find().count() , 0 )
            
            monga.col(User).query(user_id=55).remove()
            
            user = monga.col(User).new(name='new_user',user_id=55)
            post = monga.col(PostMany).new(isi='apakekdah')
            post.posts.append(PostMany(isi='apaya'))
            post.tags.append(Tags(isi=['tags ajah']))
            
            user.save()
            post.save()
            
            del user
            del post
            
            user = monga.col(User).find_one(user_id=55)
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
            user = monga.col(User).new(name='ada-deh',user_id=100)
            
            exa = monga.col(User).new(name='exa-tester',user_id=101)
            didit = monga.col(User).new(name='didit-tester',user_id=102)
            
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
            
        def test_smart_object_relation(self):
            
            user = monga.col(User).new(name='tester-smart-obj',user_id=55)
            user.save()
            
            user.wallposts.append(WallPost(message='test',writter=user))
            user.save()
            
            post = WallPost(monga._db,message='post-smart-obj')
            
            post.save()
            
            self.assertEqual( post.writter, None )
            
            post.writter = user
            post.save()
            
            self.assertEqual( post.writter.name, user.name )
            
            class parent(SuperDoc):
                _collection_name = 'test'
            
                child_id = unicode
            
                anak = relation('child',pk='_id==child_id',listmode=False)
            
            class child(SuperDoc):
                _collection_name = 'test'
                
            mapper(parent,child)
                
            ayah = parent(monga._db,name='ayah-exa')
            exa = monga.col(child).new(name='exa-kun')
            exa.save()
            ayah.anak = exa
            ayah.save()
            
            ayah = monga.col(parent).find_one(name='ayah-exa')
            
            self.assertEqual( ayah.anak.name, 'exa-kun' )
            
            post = monga.col(WallPost).find_one(message='post-smart-obj')
            
            self.assertEqual( post.writter.name, 'tester-smart-obj')
            
            self.assertEqual( user.wallposts[0].writter.name, 'tester-smart-obj' )
            
            user.delete()
            
            self.assertEqual( monga.col(User).count(name='tester-smart-obj'), 0 )
            
        
        
    def main():
        suite = unittest.TestLoader().loadTestsFromTestCase(mongo_test)
        unittest.TextTestRunner(verbosity=2).run(suite)
        
    main()
    #import cProfile
    #cProfile.run('main()','fooprof')
    #import pstats
    #p = pstats.Stats('fooprof')
    #p.strip_dirs().sort_stats(-1).print_stats()


    #raise 'test'
    
    
    
