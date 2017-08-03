import logging


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
sh = logging.StreamHandler()
fh = logging.FileHandler('music.log', encoding='utf-8')
sh.setLevel(logging.DEBUG)
fh.setLevel(logging.INFO)
sh.setFormatter(formatter)
fh.setFormatter(formatter)
logger.addHandler(sh)
logger.addHandler(fh)
