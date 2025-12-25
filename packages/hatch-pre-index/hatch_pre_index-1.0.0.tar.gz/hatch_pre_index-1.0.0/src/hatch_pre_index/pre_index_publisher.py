# ================================================================================
#
#   PreIndexPublisher class
#
#   object for handling PyPI API tokens and tracking the project version 
#   before it invokes the index publisher.
#
#   MIT License
#
#   Copyright (c) 2025 krokoreit (krokoreit@gmail.com)
#
#   Permission is hereby granted, free of charge, to any person obtaining a copy
#   of this software and associated documentation files (the "Software"), to deal
#   in the Software without restriction, including without limitation the rights
#   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#   copies of the Software, and to permit persons to whom the Software is
#   furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in all
#   copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#   SOFTWARE.
#
# ================================================================================

import os
import keyring
import click

from hatch.publish.index import IndexPublisher
from .utils import read_published_version, write_published_version, get_git_tag, get_hatch_version


PRINT_DEBUG_ALLOWED = False
PRINT_DEBUG_TAG = "[PreIndexPublisher]"

def print_debug(*args, **kwargs):
    """Prints messages if PRINT_DEBUG_ALLOWED is True."""
    if PRINT_DEBUG_ALLOWED:
        print(PRINT_DEBUG_TAG + ": " + " ".join(map(str,args)), **kwargs)


class PreIndexPublisher(IndexPublisher):
    # use config in [tool.hatch.publish.pre_index]
    PLUGIN_NAME = "pre_index"

    def publish(self, artifacts, options):

        print_debug("root =", self.root)
        print_debug("cache_dir =", self.cache_dir)
        print_debug("project_config =", self.project_config)
        print_debug("plugin_config =", self.plugin_config)

        project_tag = "unknown"
        if os.path.isdir(self.root):
            f_head, f_tail = os.path.split(self.root)
            if len(f_tail) > 0:
                project_tag = f_tail


        
        repo = ""
        if 'repo' in options:
            repo = options['repo']
        elif 'repo' in self.project_config:
            repo = self.project_config['repo']

        print_debug("repo =", repo)

        new_pw = False
        if 'pw' in options:
            new_pw = options['pw'] == 'new'
        elif 'pw' in self.project_config:
            new_pw = self.project_config['pw'] == 'new'


        # Determine what version we are publishing
        git_tag = get_git_tag()
        print_debug(f"git tag         = {git_tag}")

        # ToDo: may want to use hatch version later
        #hatch_version = get_hatch_version()
        #print_debug(f"hatch version   = {hatch_version}")
        
        published = read_published_version()
        print_debug(f"published       = {published}")

        # Only publish when git tag != last published
        if git_tag and published and git_tag == published:
            print("[PreIndexPublisher] Version", git_tag, "already published. Run 'hatch build' to build a new version.")
            exit(1)

        if len(repo) > 0:
            service_name_repo = repo
        else:
            service_name_repo = 'main'
        service_name = project_tag + "_" + service_name_repo

        if new_pw:
            # handle new credentials after trying to delete old one
            try:
                keyring.delete_password("pre_index_publisher_" + service_name, "__token__")
            except:
                pass
            password = None
            token_prompt = "Enter a new API token for " + service_name + "."
        else:
            # handle stored credentials
            password = keyring.get_password("pre_index_publisher_" + service_name, "__token__")
            token_prompt = "No API token is currently stored for " + service_name + "."

        store_token = False
        if password is None:
            print(token_prompt)
            print("You can provide an API token to be stored and reused or just use it for this time.")
            store_token = click.confirm("Do you want to store an API token?", default="y")
            if store_token:
                token_prompt = "Enter API token to store"
            else:
                token_prompt = "Enter one time use API token"
            password = click.prompt(token_prompt, default="")

        if len(password) == 0:
            print("[PreIndexPublisher] No API token entered. Publishing aborted.")
            exit(1)


        # Continue with standard index publishing
        index_options = {'no_prompt': options['no_prompt'], 'initialize_auth': options['initialize_auth']}
        index_options['user'] = "__token__"
        index_options['auth'] = password
        if len(repo) > 0:
            index_options['repo'] = repo

        super().publish(artifacts, index_options)


        # on succesful completion, store published version
        if git_tag:
            print("[PreIndexPublisher] Writing published version:", git_tag)
            write_published_version(git_tag)

        # on succesful completion, store credentials
        if store_token:
            keyring.set_password("pre_index_publisher_" + service_name, "__token__", password)


