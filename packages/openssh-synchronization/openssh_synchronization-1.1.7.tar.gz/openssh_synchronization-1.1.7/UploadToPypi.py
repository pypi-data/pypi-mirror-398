# -*- encoding: utf-8 -*-
"""
@File    :   UploadToPypi.py
@Time    :   2025年9月22日21:45:30
@Author  :   坐公交也用券
@Version :   1.0.3
@Contact :   faith01238@hotmail.com
@Homepage : https://liumou.site
@Desc    :   当前文件作用
"""
import platform
from os import system, path, getcwd
from shutil import rmtree
from subprocess import getstatusoutput
from pathlib import Path

from loguru import logger


class UploadToPypi:
	def __init__(self):
		"""
		上传项目到pypi
		"""
		self.logger = logger
		self.work = 'openssh_sync'
		self.dist = path.join(getcwd(), 'dist')
		self.home = Path().home()
		# self.logger.info(self.home)
		# 这是保存用户密码的文件，将pypi的账号保存到这个文件即可(第一行: 用户名，第二行: 密码)
		file = path.join(self.home, 'pypi.txt')
		r = open(file=file, mode='r', encoding='utf-8')
		data = r.read()
		r.close()
		self.user = str(data).split("\n")[0]
		self.pd = str(data).split("\n")[1]

	def install_twine(self):
		"""
		:return:
		"""
		for pac in ["twine", "build"]:
			cmd = f"pip install {pac} --upgrade -i https://pypi.tuna.tsinghua.edu.cn/simple"
			# if self.check_twine():
			if platform.system().lower() == 'linux':
				cmd = f"pip3 install {pac} --upgrade  -i https://pypi.tuna.tsinghua.edu.cn/simple"
				system(cmd)
			else:
				system(cmd)

	def check_twine(self):
		"""
		检查是否需要安装twine工具
		:return:
		"""
		cmd = "twine -h"
		res = getstatusoutput(cmd)[0]
		if int(res) == 0:
			self.logger.info('twine installed')
			return False
		self.logger.warning('Twine is not installed')
		return True

	def delete(self, dir_=None):
		"""
		删除文件夹
		:param dir_:
		:return:
		"""
		if dir_ is None:
			dir_ = self.dist
		for d in ["ssh_auto_upgrade.egg-info", "dist"]:
			d = path.join(getcwd(), d)
			if path.exists(d):
				self.logger.info('Delete %s' % dir_)
				try:
					rmtree(dir_)
				except Exception as e:
					self.logger.error(e)

	def build(self):
		"""
		开始构建
		:return:
		"""
		c = "py -m build"
		upload = f"py -m twine upload --username {self.user} --password {self.pd} --repository pypi dist/*"
		if platform.system().lower() == 'linux':
			c = "python3 -m build"
			upload = f"python3 -m twine upload --username {self.user} --password {self.pd}  --repository pypi dist/*"
		res = system(c)
		if int(res) == 0:
			self.logger.info("Build successful")
			self.logger.info("用户名: ", self.user)
			self.logger.info("密码: ", self.pd)
			res = system(upload)
			if int(res) == 0:
				self.logger.info("Upload succeeded")
			else:
				self.logger.error("Upload failed")
				print(upload)
		else:
			self.logger.error("Build failed")
			print(c)

	def start(self):
		"""
		开始处理
		:return:
		"""
		self.install_twine()
		self.delete()
		self.build()
		self.delete()


if __name__ == "__main__":
	upload = UploadToPypi()
	upload.start()
