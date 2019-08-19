import logging


basic_format = '%(name)s - %(levelname)s - %(message)s'

logging.basicConfig(level=logging.INFO, format=basic_format)


f_handler = logging.FileHandler('../wilber.log')
f_handler.setLevel(logging.DEBUG)
f_format = logging.Formatter('%(asctime)s - %(levelname)-7s - %(name)s -  %(funcName)s [%(lineno)d] - %(message)s')
f_handler.setFormatter(f_format)


logger = logging.getLogger('wilber')


logger.addHandler(f_handler)
