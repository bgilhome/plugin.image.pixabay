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

_CONSUMER_KEY = str(xbmcplugin.getSetting(pixabayutils.xbmc.addon_handle, 'key'))
_RPP = int(xbmcplugin.getSetting(pixabayutils.xbmc.addon_handle, 'rpp'))
_LIMITP = str(xbmcplugin.getSetting(pixabayutils.xbmc.addon_handle, 'limitpages'))
_MAXP = int(xbmcplugin.getSetting(pixabayutils.xbmc.addon_handle, 'maxpages'))
_ORIENTATION = int(xbmcplugin.getSetting(pixabayutils.xbmc.addon_handle, 'orientation'))
_EDITORS_CHOICE = str(xbmcplugin.getSetting(pixabayutils.xbmc.addon_handle, 'editorschoice'))
_SAFESEARCH = str(xbmcplugin.getSetting(pixabayutils.xbmc.addon_handle, 'safesearch'))
_ORDER = int(xbmcplugin.getSetting(pixabayutils.xbmc.addon_handle, 'order'))
_IMGSIZE = int(xbmcplugin.getSetting(pixabayutils.xbmc.addon_handle, 'imgsize'))
_TMBSIZE = int(xbmcplugin.getSetting(pixabayutils.xbmc.addon_handle, 'tmbsize'))

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
		# No image title in Pixabay, use tags
		self.name = str(photo_json['id']) + ": " + photo_json['tags']
		self.thumb_url = photo_json['previewURL'] if _TMBSIZE == 150 else photo_json['webformatURL'].replace('_640', '_' + _TMBSIZE)
		self.url = photo_json['largeImageURL'] if _IMGSIZE == 1280 else photo_json['webformatURL'].replace('_640', '_' + _IMGSIZE)
		self.username = photo_json['user']

	def __repr__(self):
		return str(self.__dict__)



def feature():
	""" Lists photos for the chosen feature and category """
	params = pixabayutils.xbmc.addon_params
	feature = params['feature']
	category = params.get('category', None)
	page = int(params.get('page', 1))

	# Set order & editors choice params
	order = feature if feature in ["popular", "latest"] else _ORDER
	editors_choice = "true" if feature == "editors" else _EDITORS_CHOICE

	resp = do_search(category=category, order=order, editors_choice=editors_choice, page=page)
	if resp:
		pixabayutils.xbmc.xbmcplugin.setContent(pixabayutils.xbmc.addon_handle, 'images')
		for image in map(Image, resp['hits']):
			pixabayutils.xbmc.add_image(image)

		# Pager
		if not (_LIMITP == 'true' and (page >= _MAXP)):
			if page * _RPP < resp['totalHits']:
				next_page = page + 1
				url = pixabayutils.xbmc.encode_child_url('feature', feature=feature, category=category, page=next_page)
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

	# Get term or show modal if empty
	if 'term' not in params:
		term = getTerm()
		if term == None:
			return
		page = 1
	else:
		term = params['term']
		page = int(params.get('page', 1))

	resp = do_search(term=term, page=page)
	if resp:
		pixabayutils.xbmc.xbmcplugin.setContent(pixabayutils.xbmc.addon_handle, 'images')
		for image in map(Image, resp['hits']):
			pixabayutils.xbmc.add_image(image)

		# Pager
		if not (_LIMITP == 'true' and (page >= _MAXP)):
			if page * _RPP < resp['totalHits']:
				next_page = page + 1
				if 'ctxsearch' in params:
					url = pixabayutils.xbmc.encode_child_url('search', term=term, page=next_page, ctxsearch=True)
				else:
					url = pixabayutils.xbmc.encode_child_url('search', term=term, page=next_page)
				pixabayutils.xbmc.add_dir('Next page', url)

	pixabayutils.xbmc.end_of_directory()

def do_search(term=None, category=None, page=None, order=None, editors_choice=None, per_page=_RPP, orientation=_ORIENTATION, safesearch=_SAFESEARCH):
	""" Runs a query via the API """
	# Defaults
	term = term or ''
	category = category or ''
	page = page or 1
	order = order or _ORDER
	editors_choice = editors_choice or _EDITORS_CHOICE

	# Run the query
	try:
		resp = API.image_search(q=term, category=category, per_page=_RPP, orientation=_ORIENTATION, page=page, order=order, editors_choice=editors_choice, safesearch=_SAFESEARCH)
	except Exception, e:
		xbmc.executebuiltin('Notification(%s, %s,,%s)' % (__addonname__, 'Error from API: '+str(e.status),__icon__))
		xbmc.log(__addonname__+' - Error from API: '+str(e), xbmc.LOGERROR)
		return

	# Handle results
	if (resp['totalHits'] == 0):
		xbmc.executebuiltin('Notification(%s, %s,,%s)' % (__addonname__, "Your search returned no matches.",__icon__))
		return

	return resp

def features():
	""" Lists all available features. Main menu. """
	features = (
		"editors",
		"popular",
		"latest",
	)

	for feature in features:
		url = pixabayutils.xbmc.encode_child_url('categories', feature=feature)
		pixabayutils.xbmc.add_dir(feature, url)

	url = pixabayutils.xbmc.encode_child_url('search')
	pixabayutils.xbmc.add_dir('Search', url)

	pixabayutils.xbmc.end_of_directory()


def categories():
	""" Lists all available photo categories. """
	categories = [
		"fashion",
		"nature",
		"backgrounds",
		"science",
		"education",
		"people",
		"feelings",
		"religion",
		"health",
		"places",
		"animals",
		"industry",
		"food",
		"computer",
		"sports",
		"transportation",
		"travel",
		"buildings",
		"business",
		"music",
	]

	params = pixabayutils.xbmc.addon_params
	feature = params['feature']

	url = pixabayutils.xbmc.encode_child_url('feature', feature=feature)
	pixabayutils.xbmc.add_dir('All', url)

	for category in sorted(categories):
		url = pixabayutils.xbmc.encode_child_url('feature', feature=feature, category=category)
		pixabayutils.xbmc.add_dir(category, url)

	pixabayutils.xbmc.end_of_directory()


try:
	modes = {
		'feature': feature,
		'categories': categories,
		'search': search,
	}

	params = pixabayutils.xbmc.addon_params
	mode_name = params['mode']
	modes[mode_name]()
except KeyError:
	features()
