# -*- coding: utf-8 -*-
import os
import io
import time
import traceback

sample_key_list = [
    '/library/recentlyAdded',
    '/playlists/tvh'
]

class TVHeadend(object):
    streaming_list = None

    @classmethod
    def tvhm3u(cls, host, token):
        m3u = '#EXTM3U\n' 
        for index, value in enumerate(sample_key_list):
            m3u += '#EXTINF:-1,PLEX %s\n' % (index+1)
            m3u += 'pipe:///usr/bin/ffmpeg -loglevel fatal -i http://%s/:/plugins/com.plexapp.plugins.SJVA/function/tvhfile?key=%s&X-Plex-Token=%s -codec copy -acodec copy -metadata service_provider=PLEX -metadata service_name=PLEX -tune zerolatency -f mpegts pipe:1\n' % (host, value, token)
        return m3u
        
    @classmethod
    def init_list(cls):
        #if cls.streaming_list is None:
        cls.streaming_list = []
        for _ in sample_key_list:
            cls.streaming_list.append(Broadcast(_))
        return len(cls.streaming_list)

    @classmethod
    def tvhfile(cls, key, host, token):
        if cls.streaming_list is None or len(cls.streaming_list) == 0:
            cls.init_list()
        for _ in cls.streaming_list:
            if _.key == key:
                return Redirect(_.get_file(host, token))
    
class Broadcast(object):
    def __init__(self, key):
        self.key = key
        self.video_list = []
        self.timestamp = time.time()
        self.total_duration = 0
        try:
            if key.startswith('/playlists'):
                tmp_key = '/playlists' 
                data = JSON.ObjectFromURL('http://127.0.0.1:32400' + tmp_key)
                for metadata in data['MediaContainer']['Metadata']:
                    if metadata['title'] == key.split('/')[-1]:
                        key = metadata['key']
            data = JSON.ObjectFromURL('http://127.0.0.1:32400' + key)
            #Log(data)
            for metadata in data['MediaContainer']['Metadata']:
                try:
                    sub_data = JSON.ObjectFromURL('http://127.0.0.1:32400' + metadata['key'])
                    #Log(sub_data)
                    episode = sub_data['MediaContainer']['Metadata'][0]
                    self.video_list.append({'key':episode['key'], 'duration':int(episode['duration'])})
                    self.total_duration = self.total_duration + int(episode['duration'])
                    Log(episode['duration'])
                except:
                    pass 
            #Log(self.video_list)
            Log('TOTAL_DURATION : %s', self.total_duration)
        except Exception as e:
            Log('Exception : %s', e) 
            Log(traceback.format_exc()) 

    def get_file(self, host, token):
        #duration은 ms   timestamp는 s.. 쿼리는 초
        offset = (time.time() - self.timestamp) * 1000 % self.total_duration
        tmp = 0
        for _ in self.video_list:
            Log('offset %s tmp %s duration %s', offset, tmp, _['duration'])
            if offset + 5*1000 < tmp + _['duration']:
                url = 'http://%s/video/:/transcode/universal/start.m3u8?X-Plex-Platform=Chrome&mediaIndex=0&offset=%s&path=%s&X-Plex-Token=%s' % (host, ((offset-tmp)/1000-1), _['key'], token)
                Log(url)
                return url
            else:
                tmp = tmp + _['duration']

        
"""
#멀티 접근??
@classmethod
    def tvhfile(cls, host, token): 
        if cls.video_list is None or len(cls.video_list) == 0:
            cls.init_list(host, token)
        url = None
        if cls.video_list is not None and len(cls.video_list) > 0:
            url = cls.video_list[cls.index % len(cls.video_list)]
            cls.index = cls.index + 1
        Log('tvhfile %s %s' % (cls.index, url))     
        return Redirect(url)
        #return url
"""