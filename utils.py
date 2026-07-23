# -*- coding: utf-8 -*-
import os
import sys
import logging
import re
import datetime

def get_logger(site_name, log_dir, filename):
    logs_path = os.path.join(log_dir, "run_log")
    if not os.path.exists(logs_path):
        os.makedirs(logs_path)
    log_file_name = filename
    logger = logging.getLogger(site_name + " Logs")
    logger.handlers.clear()
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(os.path.join(logs_path, log_file_name))
    sh = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("[%(asctime)s] - %(funcName)s - %(name)s - %(levelname)s - %(message)s",
                                    datefmt='%a, %d %b %Y %H:%M:%S')
    fh.setFormatter(formatter)
    sh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(sh)
    logger.propagate = False
    return logger

def create_raw_file(filename, columns, item):
    line_items = list()
    for column in columns:
        try:
            line = " ".join(str(item[column]).strip().replace("\n", " ").replace("\r", " ").split())
            line = re.sub(r"<style[^>]*>[^<]+</style>", " ", line)
            line = re.sub(r"<script[^>]*>[^<]+</script>", " ", line)
            value = re.sub(r"<![^>]*>", " ", line)
        except KeyError:
            value = ""
        line_items.append(value)
        
    line = "|".join(line_items)+"\r"        
    with open(filename, "a+", encoding="utf-8") as file:
        file.write(line)

def create_file(filename, content=""): 
    with open(filename, "w", encoding="utf-8") as file:
        file.write(content)

def save_source_content(directory, filename, content=b""):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except Exception as e:
        print('ERR_SAVE_SOURCE_CONTENT_FOLDER_CREATION', e, directory)

    try:
        filepath = os.path.join(directory, filename)
        # Ensure content is written as bytes
        mode = "wb" if isinstance(content, bytes) else "w"
        encoding = None if isinstance(content, bytes) else "utf-8"
        with open(filepath, mode, encoding=encoding) as file:
            file.write(content)
    except Exception as e:
        print('ERR_SAVE_SOURCE_CONTENT_FILE_CREATION', e, filename)
