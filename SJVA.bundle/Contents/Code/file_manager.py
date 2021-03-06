# -*- coding: utf-8 -*-
import os
import threading
import time
import datetime
import traceback

import base
from scan_queue import ScanQueue
from entity import EntityScan

class FileManager(threading.Thread):
    def __init__(self): 
        self.flag_stop = False
        self.entity_list = []
        self.thread = threading.Thread(target=self.thread_function, args=())
        self.thread.daemon = True  
        self.thread.start()

    def stop(self):
        self.flag_stop = True
        if self.thread is not None:
            self.flag_stop = True
            self.thread.join()
        #self.start_scan_queue()
        Log('Stop FileManager!!')

    def thread_function(self):
        while(self.flag_stop == False):
            try:
                for i in range(60):
                    if self.flag_stop:
                        return
                    time.sleep(1)
                #time.sleep(60)
                #Log('run...')
                for _ in self.entity_list:
                    delta = datetime.datetime.now() - datetime.datetime.strptime(_.time_make, '%Y-%m-%d %H:%M:%S')
                    if delta.days > 1: 
                        self.entity_list.remove(_)
                    elif _.wait_status == 'READY_ADD':
                        if os.path.exists(_.filename):
                            Log(_.filename)
                            Log('SHOW_IN_FILELIST : %s', _.filename)
                            _.wait_status = 'SHOW_IN_FILELIST'
                            # 2019-03-10 폴더도 들어옴. (구글 폴더이동 이벤트)
                            if os.path.isfile(_.filename):
                                t = FileSizeCheckThread()
                                t.set_entity(self, _)
                                t.daemon = True
                                t.start()
                            else:
                                # 폴더면 현 위치.. 
                                _.wait_status = 'REAL_ADD'
                                _.directory = _.filename
                                base.scan_queue.in_queue(_)
                        else:
                            Log(_.filename)
                            Log('file not exist : %s', _.status)
                    elif _.wait_status == 'READY_REMOVE':
                        if os.path.exists(_.filename):
                            Log(_.filename)
                            Log('file still exist : %s', _.status)
                        else:
                            Log(_.filename)
                            _.wait_status = 'REAL_REMOVE'
                            ret = base.scan_queue.in_queue(_)
                    elif _.wait_status == 'WRONG_PATH' or _.wait_status == 'EXCEPT_PATH':
                        self.entity_list.remove(_)
            except Exception, e:
                Log('Exception:%s', e)
                Log(traceback.format_exc())

    def add(self, section_id, filename, callback, callback_id, type_add_remove, call_from):
        # 2019-06-24
        filename = self.get_change_filename(filename)
        entity = EntityScan(section_id, filename, callback, callback_id, call_from)
        if type_add_remove == 'ADD':
            entity.wait_status = 'READY_ADD'
        else:
            entity.wait_status = 'READY_REMOVE'
        for _ in self.entity_list:
            if _.status == '' and _.filename == entity.filename :
                return 'ALREADY_IN_LIST'
        #ret = sql_command('SELECT_FILENAME', filename)
        #if ret is not None:
        #    if ret.strip() != '':
        #        return 'ALREADY_IN_LIBRARY'
        if base.is_windows():
            if filename[0] == '/':
                entity.wait_status = 'WRONG_PATH'
        else:
            if filename[0] != '/':
                entity.wait_status = 'WRONG_PATH'
        if filename.startswith('NONE'):
            entity.wait_status = 'EXCEPT_PATH'
        self.entity_list.append(entity)
        return 'ADD_OK'
    
    def therad_callback(self, entity):
        entity.wait_status = 'REAL_ADD'
        ret = base.scan_queue.in_queue(entity)
        #time.sleep(1)
    
    def get_change_filename(self, filename):
        try:
            if base.get_setting('use_scan_filename_change_rule'):
                rule_string = base.get_setting('scan_filename_change_rule')
                rules = [x.strip() for x in rule_string.split('|')]
                for rule in rules:
                    source, target = [x.strip() for x in rule.split(',')]
                    if filename.startswith(source):
                        ret = filename.replace(source, target)
                        if target == 'NONE':
                            return 'NONE ' + filename
                        else:
                            if target[0] == '/':
                                ret = ret.replace('\\', '/')
                            else:
                                ret = ret.replace('/', '\\')
                        Log('filename %s -> %s', filename, ret)
                        return ret
                return filename
            else:
                return filename
        except Exception, e:
            Log('Exception:%s', e)
            Log(traceback.format_exc())
            return filename


class FileSizeCheckThread(threading.Thread):
    filemanager_instance = None
    file_size = 0
    entity = None
    
    def run(self):
        while True:
            time.sleep(30)            
            current_size = os.path.getsize(self.entity.filename)
            if self.file_size == current_size:
                Log('FileSizeCheckThread size match!!')
                self.filemanager_instance.therad_callback(self.entity)
                break
            else:
                Log('FileSizeCheckThread size not match %s, %s', self.file_size, current_size)
                self.file_size = current_size

    def set_entity(self, filemanager_instance, entity):
        self.filemanager_instance = filemanager_instance
        self.entity = entity
        self.file_size = os.path.getsize(self.entity.filename)
        Log( 'FILESIZE : %s', self.file_size)
