#This file is part of trytontasks_userdoc. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import os
import glob
import webbrowser
from invoke import task, run
from blessings import Terminal
from path import path
from string import Template
from trytontasks_modules import read_config_file

t = Terminal()

def create_symlinks(origin, destination, lang='es', remove=True):
    if remove:
        # Removing existing symlinks
        for link_file in path(destination).listdir():
            if link_file.islink():
                link_file.remove()

    for module_doc_dir in glob.glob('%s/*/doc/%s' % (origin, lang)):
        module_name = str(path(module_doc_dir).parent.parent.basename())
        symlink = path(destination).joinpath(module_name)
        if not symlink.exists():
            path(destination).relpathto(path(module_doc_dir)).symlink(symlink)

def make_link(origin, destination):
    directory = os.path.dirname(destination)
    if not os.path.exists(destination):
        path(directory).relpathto(path(origin)).symlink(destination)

@task
def install():
    'Install User DOC'
    run('pip install sphinx')
    run('pip install sphinxcontrib-inheritance')
    run('pip install trydoc --no-dependencies') # force not install proteus from pypi
    #~ run('which sphinx-build')
    run('hg clone https://bitbucket.org/trytonspain/trytond-doc')

    print t.bold('Done')

@task
def make(modules='modules', user_doc_path='trytond-doc',
        source_doc='doc-src', doc_path="doc", lang="es", project_name=None,
        version=None, copyright=None):
    'Make User DOC'
    if not os.path.exists(modules):
        print t.bold('Not found modules dir')
        exit()
    if not os.path.exists(user_doc_path):
        print t.bold('Clone https://bitbucket.org/trytonspain/trytond-doc')
        exit()
    if not os.path.exists(source_doc):
        run("mkdir %(source_doc)s" % locals())
    if not os.path.exists(doc_path):
        run("mkdir %(doc_path)s" % locals())

    # create symlinks from modules.
    create_symlinks(modules, source_doc, lang, True)
    # create symlinks from core modeules.
    create_symlinks(user_doc_path, source_doc, lang, False)

    conf_file = '%s/conf.py' % source_doc
    if not os.path.exists(conf_file):
        template = '%s/conf.py.template' % user_doc_path
        with open(template, 'r') as f:
            tpl_config = f.read()

        vals = {
            'PROJECT': project_name or 'Tryton Doc',
            'COPYRIGHT': copyright or 'Tryton ERP',
            'VERSION': version or '3.8',
            }
        tpl = Template(tpl_config).substitute(vals)
        with open(conf_file, 'w') as f:
            f.write(tpl)

    # create symlink for index
    index = os.path.join(user_doc_path, 'index.rst')
    link = os.path.join(source_doc, 'index.rst')
    make_link(index, link)

    print t.bold('Done')

@task
def build(source_doc='doc-src', doc_path="doc", buildername='html'):
    'Build User DOC (html, singlehtml...)'
    dbname = os.environ.get('DB_NAME')
    if not dbname:
        print t.red('Select a database name:')
        print t.green('export DB_NAME=databasename')
        exit()
    print 'Database: ' + t.bold(dbname)

    # Sphinx Build options: http://www.sphinx-doc.org/en/stable/invocation.html
    cmd = 'sphinx-build -b %s %s %s' % (buildername, source_doc, doc_path)
    run(cmd)

    print t.bold('Done')

@task
def open(server):
    'Open User DOC in browser'
    Servers = read_config_file('servers.cfg', type='servers')
    servers = Servers.sections()
    servers.sort()

    if not server in servers:
        print 'Not found %s' % server
        return

    url = Servers.get(server, 'doc')
    if url:
        webbrowser.open(url, new=1)
