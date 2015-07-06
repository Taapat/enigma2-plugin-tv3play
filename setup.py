# -*- coding: utf-8 -*-

from distutils.core import setup
import os
import setup_translate


setup (name = 'enigma2-plugin-extensions-tv3play',
	version='1.0',
	author='Taapat',
	author_email='taapat@gmail.com',
	package_dir = {'Extensions.TV3Play': 'src'},
	packages=['Extensions.TV3Play'],
	package_data={'Extensions.TV3Play': ['*.png']},
	description = 'Watch TV3 play online services',
	cmdclass = setup_translate.cmdclass,
)
