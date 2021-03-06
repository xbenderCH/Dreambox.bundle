ART = 'art-default.jpg'
ICON = 'icon-default.png'
REGEX = '%s = new Array\((.+?)\);'
ZAP_TO_URL = 'http://%s:%s/cgi-bin/zapTo?path=%s&curBouquet=%d&curChannel=%d'
STREAM_URL = 'http://%s:%s'

####################################################################################################
def Start():

	Plugin.AddViewGroup('List', viewMode='List', mediaType='items')
	ObjectContainer.art = R(ART)
	ObjectContainer.title1 = 'Dreambox'
	DirectoryObject.thumb = R(ICON)

####################################################################################################
@handler('/video/dreambox', 'Dreambox', art=ART, thumb=ICON)
def MainMenu():

	oc = ObjectContainer(view_group='List', no_cache=True)

	if Prefs['host'] and Prefs['port_web'] and Prefs['port_video']:
		categories = GetDataList(name='bouquets')

		if categories:
			for bouquet_index, title in enumerate(categories):
				channels = GetDataList(name='channels\[%d\]' % bouquet_index)

				if channels[0].lower() == 'none':
					continue

				oc.add(DirectoryObject(
					key = Callback(Bouquet, title=title, bouquet_index=bouquet_index),
					title = title
				))
		else:
			Log("Couldn't connect to host.")

	oc.add(PrefsObject(title='Preferences', thumb=R('icon-prefs.png')))

	return oc

####################################################################################################
@route('/video/dreambox/bouquet/{bouquet_index}', bouquet_index=int)
def Bouquet(title, bouquet_index):

	oc = ObjectContainer(title2=title, view_group='List', no_cache=True)
	channels = GetDataList(name='channels\[%d\]' % bouquet_index)
	channel_refs = GetDataList(name='channelRefs\[%d\]' % bouquet_index)

	for channel_index, title in enumerate(channels):
		video = CreateVideoClipObject(channel_ref=channel_refs[channel_index], bouquet_index=bouquet_index, channel_index=channel_index, title=title)
		oc.add(video)

	return oc

####################################################################################################
def GetDataList(name):

	url = 'http://%s:%s/body' % (Prefs['host'], Prefs['port_web'])

	try:
		body = HTTP.Request(url, cacheTime=30).content
	except:
		return None

	list = Regex(REGEX % name, Regex.DOTALL).search(body)
	if list:
		list = list.group(1).strip()
		list = list.strip('"').split('", "')

		return list

	return None

####################################################################################################
def CreateVideoClipObject(channel_ref, bouquet_index, channel_index, title, thumb=R(ICON), include_oc=False):

	video = VideoClipObject(
		key = Callback(CreateVideoClipObject, channel_ref=channel_ref, bouquet_index=bouquet_index, channel_index=channel_index, title=title, thumb=thumb, include_oc=True),
		rating_key = channel_ref,
		title = title,
		thumb = thumb,
		items = [
			MediaObject(
				container = 'mpegts',
				video_codec = VideoCodec.H264,
				audio_codec = AudioCodec.AAC,
				audio_channels = 2,
				parts = [
					PartObject(
						key = HTTPLiveStreamURL(Callback(PlayVideo, channel_ref=channel_ref, bouquet_index=bouquet_index, channel_index=channel_index))
					)
				]
			)
		]
	)

	if include_oc:
		oc = ObjectContainer()
		oc.add(video)
		return oc
	else:
		return video

####################################################################################################
def PlayVideo(channel_ref, bouquet_index, channel_index):

	# Change the channel
	zap_to = ZAP_TO_URL % (Prefs['host'], Prefs['port_web'], channel_ref, bouquet_index, channel_index)
	zap = HTTP.Request(zap_to, cacheTime=0, sleep=2.0).content

	# Tune in to the stream
	stream = STREAM_URL % (Prefs['host'], Prefs['port_video'])
	return Redirect(stream)
