from codev.installation import Installation, BaseInstallation
import shutil
from time import time


class ActualInstallation(BaseInstallation):
    def install(self, performer):
        # gunzip is in default ubuntu
        # performer.execute('apt-get install gunzip -y --force-yes')
        directory = '{home_dir}/repository'.format(home_dir=performer.home_dir)
        archive = shutil.make_archive(directory, 'gztar')
        performer.send_file(archive, archive)
        performer.execute('mkdir -p {directory}'.format(directory=directory))
        performer.execute('tar -xzf {archive} --directory {directory}'.format(archive=archive, directory=directory))

        return directory

    def process_options(self, options):
        self.name = options or str(time())

    @property
    def ident(self):
        return self.name

Installation.register('actual', ActualInstallation)
