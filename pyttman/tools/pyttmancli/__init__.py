import argparse
import sys
from typing import List

from pyttman.core.parsing.routing import FirstMatchingRouter
from pyttman.tools.pyttmancli.executor import Runner
from pyttman.tools.pyttmancli.terraforming import TerraFormer, bootstrap_environment

#     MIT License
#
#      Copyright (c) 2021-present Simon Olofsson
#
#      Permission is hereby granted, free of charge, to any person obtaining a copy
#      of this software and associated documentation files (the "Software"), to deal
#      in the Software without restriction, including without limitation the rights
#      to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#      copies of the Software, and to permit persons to whom the Software is
#      furnished to do so, subject to the following conditions:
#
#      The above copyright notice and this permission notice shall be included in all
#      copies or substantial portions of the Software.
#
#      THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#      IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#      FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#      AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#      LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#      OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#      SOFTWARE.

"""
This file contains Intents and Ability classes which make out
the Pyttman cli tool, used to administer, bootstrap and create
Pyttman app for users of the framework.

Are you a Pyttman developer or a contributor and want to extend
the 'pyttman' terminal tool with new functionality?

Add Intents to the PyttmanCLI Ability and ensure that you
overload the 'description' and 'example' fields of the Intent
classes, since they provide essential data for users when
using the tool in the terminal.

"""
import pathlib
import typing

import pyttman
from pyttman.core.ability import Ability
from pyttman.core.communication.models.containers import Message, Reply, ReplyStream
from pyttman.core.intent import Intent
from pyttman.core.parsing.parsers import ValueParser
from pyttman.tools.pyttmancli import Runner, bootstrap_environment, TerraFormer


class CreateNewApp(Intent):
    """
    Intent class for creating a new Pyttman app.
    The directory is terraformed and prepared
    with a template project.
    """
    lead = ("new",)
    trail = ("app",)
    ordered = True
    description = "Creates a new Pyttman app project in current directory " \
                  "from a template."
    example = "pyttman new app <app name>"

    class EntityParser:
        app_name = ValueParser()

    def respond(self, message: Message) -> typing.Union[Reply, ReplyStream]:
        if (app_name := self.entities.get("app_name")) is not None:
            print(f"- Creating project '{app_name}'...", end=" ")
            try:
                terraformer = TerraFormer(app_name=app_name)
                terraformer.terraform()
            except Exception as e:
                print("errors occurred.")
                return Reply(f"{e.__class__.__name__}: {e}")
            print("done.")
            return Reply(f"- Check out your new app '{app_name}' in "
                         f"the current directory. Feel free to visit the "
                         f"Pyttman Wiki to follow our Get Started guide at "
                         f"https://github.com/dotchetter/Pyttman/wiki/Tutorial")
        return Reply(self.storage.get("NO_APP_NAME_MSG"))


class RunAppInDevMode(Intent):
    """
    Intent class for running a Pyttman app in dev mode,
    meaning the "DEV_MODE" flag is set to True in the app
    to provide verbose outputs which are user defined
    and the CliClient is used as the primary front end.
    """
    lead = ("dev",)
    ordered = True
    example = "pyttman dev <app name>"
    description = "Run a Pyttman app in dev mode. Dev mode sets " \
                  "'pyttman.DEBUG' to True, enabling verbose outputs " \
                  "as defined in your app. The app is started using " \
                  "a CliClient for you to start chatting with your app " \
                  "with minimal overhead."

    class EntityParser:
        app_name = ValueParser()

    def respond(self, message: Message) -> typing.Union[Reply, ReplyStream]:
        if (app_name := self.entities.get("app_name")) is not None:
            if not pathlib.Path(app_name).exists():
                return Reply(f"- App '{app_name}' was not found here, "
                             f"verify that a Pyttman app directory named "
                             f"'{app_name}' exists.")
            try:
                runner = bootstrap_environment(devmode=True, module=app_name)
            except Exception as e:
                print("errors occurred:")
                return Reply(f"\t{e.__class__.__name__}: {e}")
            self.storage.put("runner", runner)
            self.storage.put("ready", True)
            return Reply(f"- Starting app '{app_name}' in dev mode...")
        return Reply(self.storage.get("NO_APP_NAME_MSG"))


class RunAppInClientMode(Intent):
    """
    Intent class for running Pyttman Apps
    in Client mode.
    """
    lead = ("runclient",)
    ordered = True
    example = "pyttman runclient <app name>"
    description = "Run a Pyttman app in client mode. This is the " \
                  "standard production mode for Pyttman apps. The " \
                  "app will be started using the client defined in " \
                  "settings.py under 'CLIENT'."

    class EntityParser:
        app_name = ValueParser()

    def respond(self, message: Message) -> typing.Union[Reply, ReplyStream]:
        if (app_name := self.entities.get("app_name")) is not None:
            if not pathlib.Path(app_name).exists():
                return Reply(f"- App '{app_name}' was not found here, "
                             f"verify that a Pyttman app directory named "
                             f"'{app_name}' exists.")
            try:
                runner = bootstrap_environment(devmode=False, module=app_name)
            except Exception as e:
                print("errors occurred:")
                return Reply(f"\t{e.__class__.__name__}: {e}")
            self.storage.put("runner", runner)
            self.storage.put("ready", True)
            return Reply(f"- Starting app '{app_name}' in client mode...")
        return Reply(self.storage.get("NO_APP_NAME_MSG"))


# TODO - Not finished in 1.1.8
class CreateNewAbilityIntent(Intent):
    lead = ("new",)
    trail = ("ability",)
    ordered = True
    example = "pyttman new ability <ability name> app <app name>"
    description = "Create a new file with an Ability class as " \
                  "a template for new Ability classes for your app."

    class EntityParser:
        ability_name = ValueParser()
        app_name = ValueParser(prefixes=("app",))

    def respond(self, message: Message) -> typing.Union[Reply, ReplyStream]:
        raise NotImplementedError


class PyttmanCli(Ability):
    """
    Encapsulates the Pyttman CLI tool 'pyttman'
    used in the terminal by framework users.
    """
    intents = (CreateNewApp, RunAppInDevMode, RunAppInClientMode)
    description = f"Pyttman v{pyttman.__version__}" \
                  f"\nSupported commands:"

    def configure(self):
        responses = {"NO_APP_NAME_MSG": "Please provide a name for your app. "
                                        "For help, type: 'pyttman help new app'"}
        self.storage.put("runner", None)
        self.storage.put("ready", False)
        self.storage |= responses

    def run_application(self) -> None:
        """
        Runs a Pyttman application with its Runner context
        as provided.
        :return: None
        """
        # noinspection PyTypeChecker, PyUnusedLocal
        # #(used for attribute access in completion)
        runner: Runner = None
        if (runner := self.storage.get("runner")) is not None:
            print(f"- Ability classes loaded: {runner.client.message_router.abilities}")
            runner.run()
        else:
            raise RuntimeError("No Runner provided, app cannot start. Exiting...")


def run(argv=None, dev_args: List = None):
    """
    This function utilized the Pyttman framework itself,
    to administrate, bootstrap and create Pyttman apps.

    The method is designed to be implicitly called through
    the terminal shell, as argparse is used to extract
    values for parsing.

    For testing purposes if you're a Pyttman developer;
    provide your arguments as a single list of strings
    in the 'dev_args' kwarg instead of using 'argv'.

    This allows the Pyttman cli to work without actual
    terminal arguments.

    :param argv: Args from a terminal shell.
    :param dev_args: Optional developer args in a list of
                     strings, for unit testing the Pyttman CLI
                     or otherwise using it outside of a terminal
                     shell. Defining this argument will automatically
                     disregarg the 'argv' arguments
    :return: None
    """
    terminal_message: Message = Message()
    pyttman_cli: Ability = PyttmanCli()
    dot = "\u2022"
    default_response = [pyttman_cli.description]
    default_response.extend([f"\n{dot} {i.example}" \
                             f"\n\t{i.description}"
                             for i in pyttman_cli.intents])
    default_response = str(" ").join(default_response)

    router = FirstMatchingRouter(abilities=[pyttman_cli], help_keyword="help",
                                 intent_unknown_responses=[default_response])

    # Extract args from terminal shell
    if argv is None:
        argv = sys.argv[:]
        argparser = argparse.ArgumentParser(prog="Pyttman CLI", usage="%(prog)s command",
                                            add_help=False, allow_abbrev=False)
        argparser.add_argument("args", nargs="*")

        try:
            command = argv[1]
        except IndexError:
            command = ""

        options, args = argparser.parse_known_args(argv[2:])
        terminal_message = Message(command.split() + options.args)

    elif dev_args is not None:
        terminal_message = Message(dev_args)

    # Let the Pyttman cli parse the command. If a Runner is created, it's started.
    reply = router.get_reply(terminal_message)
    print(reply.as_str())

    if pyttman_cli.storage.get("ready"):
        pyttman_cli.run_application()
