import os

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

__addon__       = xbmcaddon.Addon()
__addonname__   = __addon__.getAddonInfo('name')
__icon__ = __addon__.getAddonInfo('icon')
__cwd__        = __addon__.getAddonInfo('path').decode("utf-8")
__resource__   = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib' ).encode("utf-8") ).decode("utf-8")
sys.path.append(__resource__)

import pixabayutils
import pixabayutils.xbmc
import python_pixabay

_CONSUMER_KEY = int(xbmcplugin.getSetting(pixabayutils.xbmc.addon_handle, 'key'))
_RPP = int(xbmcplugin.getSetting(pixabayutils.xbmc.addon_handle, 'rpp'))
_LIMITP = str(xbmcplugin.getSetting(pixabayutils.xbmc.addon_handle, 'limitpages'))
_MAXP = int(xbmcplugin.getSetting(pixabayutils.xbmc.addon_handle, 'maxpages'))
_ORIENTATION = int(xbmcplugin.getSetting(pixabayutils.xbmc.addon_handle, 'orientation'))
_ORDER = int(xbmcplugin.getSetting(pixabayutils.xbmc.addon_handle, 'order'))
_IMGSIZE = int(xbmcplugin.getSetting(pixabayutils.xbmc.addon_handle, 'imgsize'))
_TMBSIZE = int(xbmcplugin.getSetting(pixabayutils.xbmc.addon_handle, 'tmbsize'))
_USERNAME = str(xbmcplugin.getSetting(pixabayutils.xbmc.addon_handle, 'username'))
_TMBFOLDERS = str(xbmcplugin.getSetting(pixabayutils.xbmc.addon_handle, 'tmbfolders'))

API = python_pixabay.Pixabay(_CONSUMER_KEY)

# Get the string key for orientation from the index
orientations = ['all', 'horizontal', 'vertical']
_ORIENTATION = orientations[_ORIENTATION]

# Get the string key for order from the index
orders = ['popular', 'latest']
_ORDER = orders[_ORDER]

class Image(object):
    """ Holds information about a single image """
    def __init__(self, photo_json):
        self.name = photo_json['name']
        self.thumb_url = photo_json['images'][0]['url']
        self.url = photo_json['images'][1]['url']
        self.username = photo_json['user']['username']
        self.userfullname = photo_json['user']['fullname']

    def __repr__(self):
        return str(self.__dict__)


class User(object):
    """ Holds information about a user object. Looks up info via api """
    def __init__(self, userid=None, username=None):
        super(User, self).__init__()
        self._lookupid = userid
        self._lookupusername = username
        self.info = None
        self.id = None
        self.username = None
        self.fullname = None
        self.picture = None
#        self._lookup_user()

    def __repr__(self):
        return str(self.__dict__)

#    def _lookup_user(self):
#        try:
#            self.info = API.users_show(consumer_key=_CONSUMER_KEY, id=self._lookupid, username=self._lookupusername)
#            self.id = self.info['user']['id']
#            self.username = self.info['user']['username']
#            self.fullname = self.info['user']['fullname']
#            if _TMBFOLDERS == 'true':
#                self.picture = self.info['user']['userpic_url']
#        except Exception, e:
#            _lookupvar = None
#            if self._lookupusername:
#                _lookupvar = self._lookupusername
#            elif self._lookupid:
#                _lookupvar = self._lookupid
#
#            if e.status == 404:
#                xbmc.executebuiltin('Notification(%s, %s,,%s)' % (__addonname__, 'Could not find user '+str(_lookupvar),__icon__))
#                xbmc.log(__addonname__+' - '+'Could not find user (userid/username: '+str(self._lookupid)+'/'+str(self._lookupusername)+')' , xbmc.LOGERROR)
#            else:
#                xbmc.executebuiltin('Notification(%s, %s,,%s)' % (__addonname__, 'Error from API: '+str(e.status),__icon__))
#                xbmc.log(__addonname__+' - Error from API: '+str(e), xbmc.LOGERROR)




def feature():
    """ Lists photos for the chosen feature, category and user_id """
    params = pixabayutils.xbmc.addon_params
    feature = params['feature']
    category = params.get('category', None)
    page = int(params.get('page', 1))
    user_id = params.get('user_id', None)

    try:
        resp = API.photos(feature=feature, only=category, user_id=user_id, rpp=_RPP, consumer_key=_CONSUMER_KEY, image_size=[_TMBSIZE, _IMGSIZE], page=page)
    except Exception, e:
        xbmc.executebuiltin('Notification(%s, %s,,%s)' % (__addonname__, 'Error from API: '+str(e.status),__icon__))
        xbmc.log(__addonname__+' - Error from API: '+str(e), xbmc.LOGERROR)
        return
    pixabayutils.xbmc.xbmcplugin.setContent(pixabayutils.xbmc.addon_handle, 'images')
    for image in map(Image, resp['photos']):
        pixabayutils.xbmc.add_image(image)

    if not (_LIMITP == 'true' and (resp['current_page'] >= _MAXP)):
        if resp['current_page'] < resp['total_pages']:
            next_page = page + 1
            url = pixabayutils.xbmc.encode_child_url('feature', feature=feature, category=category, user_id=user_id, page=next_page)
            pixabayutils.xbmc.add_dir('Next page', url)

    pixabayutils.xbmc.end_of_directory()


def search():
    """ Shows a search box and lists resulting photos """
    def getTerm():
        kb = xbmc.Keyboard(heading='Search pixabay')
        kb.doModal()
        text = kb.getText()
        return text if kb.isConfirmed() and text else None

    params = pixabayutils.xbmc.addon_params

    if 'term' not in params:
        term = getTerm()
        if term == None:
            return
        page = 1
    else:
        term = params['term']
        page = int(params.get('page', 1))

    try:
        resp = API.photos_search(term=term, rpp=_RPP, consumer_key=_CONSUMER_KEY, image_size=[_TMBSIZE, _IMGSIZE], page=page)
    except Exception, e:
        xbmc.executebuiltin('Notification(%s, %s,,%s)' % (__addonname__, 'Error from API: '+str(e.status),__icon__))
        xbmc.log(__addonname__+' - Error from API: '+str(e), xbmc.LOGERROR)
        return

    if (resp['total_items'] == 0):
        xbmc.executebuiltin('Notification(%s, %s,,%s)' % (__addonname__, "Your search returned no matches.",__icon__))
        return
    pixabayutils.xbmc.xbmcplugin.setContent(pixabayutils.xbmc.addon_handle, 'images')
    for image in map(Image, resp['photos']):
        pixabayutils.xbmc.add_image(image)

    if not (_LIMITP == 'true' and (resp['current_page'] >= _MAXP)):
        if resp['current_page'] < resp['total_pages']:
            next_page = page + 1
            if 'ctxsearch' in params:
                url = pixabayutils.xbmc.encode_child_url('search', term=term, page=next_page, ctxsearch=True)
            else:
                url = pixabayutils.xbmc.encode_child_url('search', term=term, page=next_page)
            pixabayutils.xbmc.add_dir('Next page', url)

    pixabayutils.xbmc.end_of_directory()


def features():
    """ Lists all available features. Main menu. """
    features = (
        "editors",
        "popular",
        "highest_rated",
        "upcoming",
        "fresh_today",
        "fresh_yesterday",
        "fresh_week"
    )

    for feature in features:
        url = pixabayutils.xbmc.encode_child_url('categories', feature=feature)
        pixabayutils.xbmc.add_dir(feature, url)

    if _USERNAME != "":
        user = User(username=_USERNAME)
        if user.id:
            url = pixabayutils.xbmc.encode_child_url('user_features', user_id=user.id)
            pixabayutils.xbmc.add_dir(user.fullname, url, user.picture)

            url = pixabayutils.xbmc.encode_child_url('friends', user_id=user.id)
            pixabayutils.xbmc.add_dir(user.fullname+'\'s friends', url)

    url = pixabayutils.xbmc.encode_child_url('search')
    pixabayutils.xbmc.add_dir('Search', url)

    pixabayutils.xbmc.end_of_directory()


def categories():
    """ Lists all available photo categories. """
    categories = {
        'Uncategorized': 0,
        'Abstract': 10,
        'Animals': 11,
        'Black and White': 5,
        'Celebrities': 1,
        'City and Architecture': 9,
        'Commercial': 15,
        'Concert': 16,
        'Family': 20,
        'Fashion': 14,
        'Film': 2,
        'Fine Art': 24,
        'Food': 23,
        'Journalism': 3,
        'Landscapes': 8,
        'Macro': 12,
        'Nature': 18,
        'Nude': 4,
        'People': 7,
        'Performing Arts': 19,
        'Sport': 17,
        'Still Life': 6,
        'Street': 21,
        'Transportation': 26,
        'Travel': 13,
        'Underwater': 22,
        'Urban Exploration': 27,
        'Wedding': 25,
    }

    params = pixabayutils.xbmc.addon_params
    feature = params['feature']
    user_id = params.get('user_id', None)

    url = pixabayutils.xbmc.encode_child_url('feature', feature=feature, user_id=user_id)
    pixabayutils.xbmc.add_dir('All', url)

    for category in sorted(categories):
        url = pixabayutils.xbmc.encode_child_url('feature', feature=feature, category=category, user_id=user_id)
        pixabayutils.xbmc.add_dir(category, url)

    pixabayutils.xbmc.end_of_directory()


def user_features():
    """ Lists features for a single user identified by user_id """
    params = pixabayutils.xbmc.addon_params
    user_id = params.get('user_id', None)

    if user_id:
        user = User(user_id)

        url = pixabayutils.xbmc.encode_child_url('feature', feature='user', user_id=user.id)
        pixabayutils.xbmc.add_dir(user.fullname+'\'s photos', url, user.picture)

        url = pixabayutils.xbmc.encode_child_url('list_galleries', user_id=user.id)
        pixabayutils.xbmc.add_dir(user.fullname+'\'s galleries', url, user.picture)

        url = pixabayutils.xbmc.encode_child_url('categories', feature='user_friends', user_id=user.id)
        pixabayutils.xbmc.add_dir(user.fullname+'\'s friends\' photos', url, user.picture)

    pixabayutils.xbmc.end_of_directory()


def list_galleries():
    """ List public galleries for a user identified by user_id """
    params = pixabayutils.xbmc.addon_params
    page = int(params.get('page', 1))
    user_id = params.get('user_id', None)

    try:
        resp = API.galleries(consumer_key=_CONSUMER_KEY, user_id=user_id, sort='position',sort_direction='asc', include_cover=1, cover_size=_TMBSIZE, page=page, rpp=_RPP)
    except Exception, e:
        xbmc.executebuiltin('Notification(%s, %s,,%s)' % (__addonname__, 'Error from API: '+str(e.status),__icon__))
        xbmc.log(__addonname__+' - Error from API: '+str(e), xbmc.LOGERROR)
        return

    if (resp['total_items'] == 0):
        xbmc.executebuiltin('Notification(%s, %s,,%s)' % (__addonname__, "No galleries found for "+user_id, __icon__))
        return

    for gallery in resp['galleries']:
        url = pixabayutils.xbmc.encode_child_url('gallery', gallery_id=gallery['id'], user_id=gallery['user_id'])
        cover_photo = None
        if (_TMBFOLDERS == 'true' and gallery['cover_photo']):
            cover_photo = gallery['cover_photo'][0]['url']
        pixabayutils.xbmc.add_dir(gallery['name'], url, cover_photo)

    if not (_LIMITP == 'true' and (resp['current_page'] >= _MAXP)):
       if resp['current_page'] < resp['total_pages']:
           next_page = page + 1
           url = pixabayutils.xbmc.encode_child_url('list_galleries', user_id=user_id, page=next_page)
           pixabayutils.xbmc.add_dir('Next page', url)

    pixabayutils.xbmc.end_of_directory()


def gallery():
    """ Lists photos in a gallery identified by user_id and gallery_id """
    params = pixabayutils.xbmc.addon_params
    user_id = params['user_id']
    gallery_id = params['gallery_id']
    page = int(params.get('page', 1))

    try:
        resp = API.galleries_id_items(id=gallery_id, user_id=user_id, sort='position', sort_direction='asc', rpp=_RPP, consumer_key=_CONSUMER_KEY, image_size=[_TMBSIZE, _IMGSIZE], page=page)
    except Exception, e:
        xbmc.executebuiltin('Notification(%s, %s,,%s)' % (__addonname__, 'Error from API: '+str(e.status),__icon__))
        xbmc.log(__addonname__+' - Error from API: '+str(e), xbmc.LOGERROR)
        return
    pixabayutils.xbmc.xbmcplugin.setContent(pixabayutils.xbmc.addon_handle, 'images')
    for image in map(Image, resp['photos']):
        pixabayutils.xbmc.add_image(image)

    if not (_LIMITP == 'true' and (resp['current_page'] >= _MAXP)):
        if resp['current_page'] < resp['total_pages']:
            next_page = page + 1
            url = pixabayutils.xbmc.encode_child_url('gallery', gallery_id=gallery_id, user_id=user_id, page=next_page)
            pixabayutils.xbmc.add_dir('Next page', url)

    pixabayutils.xbmc.end_of_directory()


def friends():
    """ Lists friends of a user identified by user_id """
    params = pixabayutils.xbmc.addon_params
    page = int(params.get('page', 1))
    user_id = params.get('user_id', None)

    try:
        resp = API.users_friends(consumer_key=_CONSUMER_KEY, id=user_id, page=page, rpp=_RPP)
    except Exception, e:
        xbmc.executebuiltin('Notification(%s, %s,,%s)' % (__addonname__, 'Error from API: '+str(e.status),__icon__))
        xbmc.log(__addonname__+' - Error from API: '+str(e), xbmc.LOGERROR)
        return

    if (resp['friends_count'] == 0):
        xbmc.executebuiltin('Notification(%s, %s,,%s)' % (__addonname__, "No friends found for "+user_id, __icon__))
        return

    for friend in resp['friends']:
        #xbmc.log(__addonname__+' - friend info '+str(friend), 0)
        url = pixabayutils.xbmc.encode_child_url('user_features', user_id=friend['id'])
        userpicture = None
        if _TMBFOLDERS == 'true':
            userpicture = friend['userpic_url']
        pixabayutils.xbmc.add_dir(friend['fullname'], url, userpicture)

    if not (_LIMITP == 'true' and (resp['page'] >= _MAXP)):
       if resp['page'] < resp['friends_pages']:
           next_page = page + 1
           url = pixabayutils.xbmc.encode_child_url('friends', user_id=user_id, page=next_page)
           pixabayutils.xbmc.add_dir('Next page', url)

    pixabayutils.xbmc.end_of_directory()




try:
    modes = {
        'feature': feature,
        'categories': categories,
        'search': search,
        'list_galleries': list_galleries,
        'gallery': gallery,
        'user_features': user_features,
        'friends': friends,
    }

    params = pixabayutils.xbmc.addon_params
    mode_name = params['mode']
    modes[mode_name]()
except KeyError:
    features()
