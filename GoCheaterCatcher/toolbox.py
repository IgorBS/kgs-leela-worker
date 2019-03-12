# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from traceback import format_exc
from gomill import sgf, sgf_moves
import string
import os
import threading
import codecs
import sys
import Queue
import time
import ConfigParser
from Tkconstants import *
import urllib2
from Tkinter import *

class GRPException(Exception):
    def __init__(self, msg):
        if type(msg) == type(u"abc"):
            self.utf_msg = msg
            self.str_msg = msg.encode("utf-8", errors='replace')
        else:
            self.str_msg = msg
            self.utf_msg = msg.decode("utf-8", errors='replace')
        log("===")
        log(format_exc())
        log("===")
        Exception.__init__(self, self.str_msg)

    def __unicode__(self):
        return self.utf_msg

loglock = threading.Lock()


def process_exists(process_name):
    # print subprocess.check_output('tasklist')
    printable = set(string.printable)
    output = filter(lambda x: x in printable, os.popen("tasklist").read())
    return process_name in output


def log(*args):
    global loglock
    loglock.acquire()
    encoding = sys.stdout.encoding
    for arg in args:
        try:
            if type(arg) == type(str('abc')):
                arg = arg.decode('utf-8', errors='replace')
            elif type(arg) != type(u'abc'):
                try:
                    arg = str(arg)
                except:
                    arg = unicode(arg, errors='replace')
                arg = arg.decode('utf-8', errors='replace')
            arg = arg.encode(encoding, errors='replace')
            print arg,
        except:
            print "?" * len(arg),
    print
    loglock.release()


def linelog(*args):
    global loglock
    loglock.acquire()
    encoding = sys.stdout.encoding
    for arg in args:
        try:
            if type(arg) == type(str('abc')):
                arg = arg.decode('utf-8', errors='replace')
            elif type(arg) != type(u'abc'):
                try:
                    arg = str(arg)
                except:
                    arg = unicode(arg, errors='replace')
                arg = arg.decode('utf-8', errors='replace')
            arg = arg.encode(encoding, errors='replace')
            print arg,
        except:
            print "?" * len(arg),
    loglock.release()


def get_moves_number(move_zero):
    k = 0
    move = move_zero
    while move:
        move = move[0]
        k += 1
    return k


def go_to_move(move_zero, move_number=0):
    if move_number == 0:
        return move_zero
    move = move_zero
    k = 0
    while k != move_number:
        if not move:
            log("The end of the sgf tree was reached before getting to move_number", move_number)
            log("Could only reach move_number", k)
            return False
        move = move[0]
        k += 1
    return move


def gtp2ij(move):
    try:
        letters = "ABCDEFGHJKLMNOPQRSTUVWXYZ"
        return int(move[1:]) - 1, letters.index(move[0])
    except:
        raise GRPException("Cannot convert GTP coordinates " + str(move) + " to grid coordinates!")


def ij2gtp(m):
    # (17,0) => a18
    try:
        if m == None:
            return "pass"
        i, j = m
        letters = "ABCDEFGHJKLMNOPQRSTUVWXYZ"
        return letters[j] + str(i + 1)
    except:
        raise GRPException("Cannot convert grid coordinates " + str(m) + " to GTP coordinates!")


def sgf2ij(m):
    # cj => 8,2
    a, b = m
    letters = "abcdefghjklmnopqrstuvwxyz"
    i = letters.index(b)
    j = letters.index(a)
    return i, j


def ij2sgf(m):
    # (17,0) => ???
    try:
        if m == None:
            return "pass"
        i, j = m
        letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't']
        return letters[j] + letters[i]
    except:
        raise GRPException("Cannot convert grid coordinates " + str(m) + " to SGF coordinates!")

filelock = threading.Lock()
c = 0

def write_sgf(filename, sgf_content):
    filelock.acquire()
    try:
        log("Saving SGF file", filename)
        if type(sgf_content) == type("abc"):
            content = sgf_content
        else:
            content = sgf_content.serialise()
        filename2 = filename
        if type(filename2) == type(u"abc"):
            if sys.getfilesystemencoding() != "mbcs":
                filename2 = filename2.encode(sys.getfilesystemencoding())
        try:
            new_file = open(filename2, 'w')
            new_file.write(content)
        except:
            new_file = codecs.open(filename2, "w", "utf-8")
            new_file.write(content)

        new_file.close()
        filelock.release()
    except IOError, e:
        filelock.release()
        log("Could not save the SGF file", filename)
        log("=>", e.errno, e.strerror)
        raise GRPException(_("Could not save the RSGF file: ") + filename + "\n" + e.strerror)
    except Exception, e:
        filelock.release()
        log("Could not save the RSGF file", filename)
        log("=>", e)
        raise GRPException(_("Could not save the SGF file: ") + filename + "\n" + unicode(e))


def convert_sgf_to_utf(content):
    game = sgf.Sgf_game.from_string(content)
    gameroot = game.get_root()
    sgf_moves.indicate_first_player(game)  # adding the PL property on the root
    if node_has(gameroot, "CA"):
        ca = node_get(gameroot, "CA")
        if ca == "UTF-8":
            # the sgf is already in UTF, so we accept it directly
            return game
        else:
            log("Encoding is", ca)
            log("Converting from", ca, "to UTF-8")
            encoding = (
                codecs.lookup(ca).name.replace("_", "-").upper().replace("ISO8859", "ISO-8859"))  # from gomill code
            content = game.serialise()
            content = content.decode(encoding, errors='ignore')  # transforming content into a unicode object
            content = content.replace("CA[" + ca + "]", "CA[UTF-8]")
            game = sgf.Sgf_game.from_string(
                content.encode("utf-8"))  # sgf.Sgf_game.from_string requires str object, not unicode
            return game
    else:
        log("the sgf has no declared encoding, we will enforce UTF-8 encoding")
        content = game.serialise()
        content = content.decode("utf", errors="replace").encode("utf")
        game = sgf.Sgf_game.from_string(content, override_encoding="UTF-8")
        return game


def open_sgf(filename):
    filelock.acquire()
    try:
        # log("Opening SGF file",filename)
        filename2 = filename
        if type(filename2) == type(u"abc"):
            if sys.getfilesystemencoding() != "mbcs":
                filename2 = filename2.encode(sys.getfilesystemencoding())
        txt = open(filename2, 'r')
        content = clean_sgf(txt.read())
        txt.close()
        filelock.release()
        game = convert_sgf_to_utf(content)
        return game
    except IOError, e:
        filelock.release()
        log("Could not open the SGF file", filename)
        log("=>", e.errno, e.strerror)
        raise GRPException(_("Could not open the RSGF file: ") + filename + "\n" + e.strerror)
    except Exception, e:
        log("Could not open the SGF file", filename)
        log("=>", e)
        try:
            filelock.release()
        except:
            pass
        raise GRPException(_("Could not open the SGF file: ") + filename + "\n" + unicode(e))


def clean_sgf(txt):
    # txt is still of type str here....

    # https://github.com/pnprog/goreviewpartner/issues/56
    txt = txt.replace(str(";B[  ])"), str(";B[])")).replace(str(";W[  ])"), str(";W[])"))

    # https://github.com/pnprog/goreviewpartner/issues/71
    txt = txt.replace(str("KM[]"), str(""))
    txt = txt.replace(str("B[**];"), str("B[];")).replace(str("W[**];"), str("W[];"))

    return txt


def get_all_sgf_leaves(root, deep=0):
    if len(root) == 0:
        # this is a leave
        return [(root, deep)]

    leaves = []
    deep += 1
    for leaf in root:
        leaves.extend(get_all_sgf_leaves(leaf, deep))

    return leaves


def keep_only_one_leaf(leaf):
    while 1:
        try:
            parent = leaf.parent
            for other_leaf in parent:
                if other_leaf != leaf:
                    log("deleting...")
                    other_leaf.delete()
            leaf = parent
        except:
            # reached root
            return


def check_selection(selection, nb_moves):
    move_selection = []
    selection = selection.replace(" ", "")
    for sub_selection in selection.split(","):
        if sub_selection:
            try:
                if "-" in sub_selection:
                    a, b = sub_selection.split('-')
                    a = int(a)
                    b = int(b)
                else:
                    a = int(sub_selection)
                    b = a
                if a <= b and a > 0 and b <= nb_moves:
                    move_selection.extend(range(a, b + 1))
            except Exception, e:
                print e
                return False
    move_selection = list(set(move_selection))
    move_selection = sorted(move_selection)
    return move_selection


def check_selection_for_color(move_zero, move_selection, color):
    if color == "black":
        new_move_selection = []
        for m in move_selection:
            player_color = guess_color_to_play(move_zero, m)
            if player_color.lower() == 'b':
                new_move_selection.append(m)
        return new_move_selection
    elif color == "white":
        new_move_selection = []
        for m in move_selection:
            player_color = guess_color_to_play(move_zero, m)
            if player_color.lower() == 'w':
                new_move_selection.append(m)
        return new_move_selection
    else:
        return move_selection


def we_are_frozen():
    """Returns whether we are frozen via py2exe.
    This will affect how we find out where we are located."""

    return hasattr(sys, "frozen")


def module_path():
    """ This will get us the program's directory,
    even if we are frozen using py2exe"""

    if we_are_frozen():
        log("Apparently running from the executable.")
        return os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding()))

    return os.path.dirname(unicode(__file__, sys.getfilesystemencoding()))

try:
    pathname = module_path()
except:
    pathname = os.path.dirname(__file__)

log('GRP path:', os.path.abspath(pathname))
config_file = os.path.join(os.path.abspath(pathname), "config.ini")
log('Config file:', config_file)


log("Checking availability of config file")
conf = ConfigParser.ConfigParser()
try:
    conf.readfp(codecs.open(config_file, "r", "utf-8"))
except Exception, e:
    log("Could not open the config file of Go Cheater Catcher" + "\n" + unicode(e))  # this cannot be translated
    sys.exit()


class MyConfig():
    def __init__(self, config_file):
        self.config = ConfigParser.ConfigParser()
        self.config.read(config_file)
        self.config_file = config_file

        self.default_values = {}
        self.default_values["general"] = {}
        self.default_values["general"]["language"] = ""
        self.default_values["general"]["sgffolder"] = ""
        self.default_values["general"]["rsgffolder"] = ""
        self.default_values["general"]["pngfolder"] = ""
        self.default_values["general"]["livefolder"] = ""
        self.default_values["general"]["stonesound"] = ""

        self.default_values["analysis"] = {}
        self.default_values["analysis"]["maxvariations"] = "26"
        self.default_values["analysis"]["savecommandline"] = "False"
        self.default_values["analysis"]["stopatfirstresign"] = "False"
        self.default_values["analysis"]["novariationifsamemove"] = "False"
        self.default_values["analysis"]["analyser"] = ""

        self.default_values["review"] = {}
        self.default_values["review"]["fuzzystoneplacement"] = "0.2"
        self.default_values["review"]["realgamesequencedeepness"] = "5"
        self.default_values["review"]["leftgobanratio"] = "0.4"
        self.default_values["review"]["rightgobanratio"] = "0.4"
        self.default_values["review"]["rightpanelratio"] = "0.4"
        self.default_values["review"]["opengobanratio"] = "0.4"
        self.default_values["review"]["maxvariations"] = "26"
        self.default_values["review"]["variationscoloring"] = "blue_for_winning"
        self.default_values["review"]["variationslabel"] = "letter"
        self.default_values["review"]["invertedmousewheel"] = "False"
        self.default_values["review"]["lastgraph"] = ""
        self.default_values["review"]["yellowbar"] = "#F39C12"
        self.default_values["review"]["lastbot"] = ""
        self.default_values["review"]["lastmap"] = ""
        self.default_values["review"]["oneortwopanels"] = "1"

        self.default_values["live"] = {}
        self.default_values["live"]["livegobanratio"] = "0.4"
        self.default_values["live"]["size"] = "19"
        self.default_values["live"]["komi"] = "7.5"
        self.default_values["live"]["handicap"] = "0"
        self.default_values["live"]["nooverlap"] = "False"
        self.default_values["live"]["analyser"] = ""
        self.default_values["live"]["black"] = ""
        self.default_values["live"]["white"] = ""
        self.default_values["live"]["thinkbeforeplaying"] = "0"

    def set(self, section, key, value):
        if type(value) in (type(1), type(0.5), type(True)):
            value = unicode(value)
        if type(section) != type(u"abc"):
            print section, "Warning: A non utf section string sent to my config:", section
        if type(key) != type(u"abc"):
            print key, "A non utf key string sent to my config:", key
        if type(value) != type(u"abc"):
            print value, "A non utf value string sent to my config:", value
        section = unicode(section)
        key = unicode(key)
        value = unicode(value)
        self.config.set(section.encode("utf-8"), key.encode("utf-8"), value.encode("utf-8"))
        self.config.write(open(self.config_file, "w"))

    def get(self, section, key):
        try:
            value = self.config.get(section, key)
            value = value.decode("utf-8")
        except:
            log("Could not read", str(section) + "/" + str(key), "from the config file")
            log("Using default value")
            value = self.default_values[section.lower()][key.lower()]
            self.add_entry(section, key, value)
        return value

    def getint(self, section, key):
        try:
            value = self.config.getint(section, key)
        except:
            log("Could not read", str(section) + "/" + str(key), "from the config file")
            log("Using default value")
            value = self.default_values[section.lower()][key.lower()]
            self.add_entry(section, key, value)
            value = self.config.getint(section, key)
        return value

    def getfloat(self, section, key):
        try:
            value = self.config.getfloat(section, key)
        except:
            log("Could not read", str(section) + "/" + str(key), "from the config file")
            log("Using default value")
            value = self.default_values[section.lower()][key.lower()]
            self.add_entry(section, key, value)
            value = self.config.getfloat(section, key)
        return value

    def getboolean(self, section, key):
        try:
            value = self.config.getboolean(section, key)
        except:
            log("Could not read", str(section) + "/" + str(key), "from the config file")
            log("Using default value")
            value = self.default_values[section.lower()][key.lower()]
            self.add_entry(section, key, value)
            value = self.config.getboolean(section, key)
        return value

    def add_entry(self, section, key, value):
        # normally section/key/value should all be unicode here
        # but just to be sure:
        section = unicode(section)
        key = unicode(key)
        value = unicode(value)
        # then, let's turn every thing in str
        section = section.encode("utf-8")
        key = key.encode("utf-8")
        value = value.encode("utf-8")
        if not self.config.has_section(section):
            log("Adding section", section, "in config file")
            self.config.add_section(section)
        log("Setting", section, "/", key, "in the config file")
        self.config.set(section, key, value)
        self.config.write(open(self.config_file, "w"))

    def get_sections(self):
        return [section.decode("utf-8") for section in self.config.sections()]

    def get_options(self, section):
        return [option.decode("utf-8") for option in self.config.options(section)]

    def remove_section(self, section):
        result = self.config.remove_section(section)
        self.config.write(open(self.config_file, "w"))
        return result


grp_config = MyConfig(config_file)


class MasterAnalyze():
    def __init__(self, dir, start_move):
        self.filenames = [os.path.join(dir, file) for file in os.listdir(dir) if file.endswith(".sgf")]
        self.start_move = start_move
        self.StopAtFirstResign = True
        self.playouts = 10000
        self.threads = 4

    def start(self):
        for filename in self.filenames:
            #while process_exists('leelaz.exe'):  # dirty hack, see for better options
            #    time.sleep(5)
            g = open_sgf(filename)
            move_zero = g.get_root()
            nb_moves = get_moves_number(move_zero)
            komi = g.get_komi()

            intervals = "all moves (both colors)"
            move_selection = range(nb_moves)
            self.bot = get_available()[0]
            print self.bot
            if os.path.exists(filename + "_{0}.asgf".format(self.bot["name"])):
                pass
            else:
                # self.bot['runanalysis']((filename, filename + "_{0}.asgf".format(self.bot["name"])),
                #         move_selection[self.start_move:], intervals, 0, komi, {self.bot['name'] + " - " + self.bot['profile']}, self.playouts, self.threads)
                self.bot['runanalysis']((filename, filename + "_{0}.asgf".format(self.bot["name"])),
                        move_selection[self.start_move:], intervals, 0, komi, self.bot, self.playouts, self.threads)


class RunAnalysisBase():
    def __init__(self, filenames, move_range, intervals, variation, komi, profile, playouts, threads):
        self.filename = filenames[0]
        self.rsgf_filename = filenames[1]
        self.move_range = move_range
        self.update_queue = Queue.Queue(1)
        self.intervals = intervals
        self.variation = variation
        self.komi = komi
        self.profile = profile
        self.playouts = playouts
        self.threads = threads
        self.g = None
        self.move_zero = None
        self.current_move = None
        self.time_per_move = None
        self.no_variation_if_same_move = False
        self.error = None
        self.maxvariations = 15

        try:
            self.g = open_sgf(self.filename)
            self.move_zero = self.g.get_root()
            self.max_move = get_moves_number(self.move_zero)

            leaves = get_all_sgf_leaves(self.g.get_root())
            log("keeping only variation", self.variation)
            keep_only_one_leaf(leaves[self.variation][0])

            size = self.g.get_size()
            log("size of the tree:", size)
            self.size = size

            log("Setting new komi")
            node_set(self.g.get_root(), "KM", self.komi)
        except Exception, e:
            self.error = unicode(e)
            self.abort()
            return

        try:
            self.bot = self.initialize_bot()
        except Exception, e:
            log("Error while initializing the GTP bot:")
            self.abort()
            return

        if not self.bot:
            return

        self.total_done = 0
        self.stop_at_first_resign = True
        self.completed = False

        # threading.Thread(target=self.run_all_analysis).start()  # multithread disabled
        self.run_all_analysis()


    def initialize_bot(self):
        pass

    def run_analysis(self, current_move):
        log("Analysis of move", current_move)
        log("Analysis for this move is completed")

    def play(self, gtp_color, gtp_move):
        if gtp_color == 'w':
            self.bot.place_white(gtp_move)
        else:
            self.bot.place_black(gtp_move)

    def run_all_analysis(self):
        self.current_move = 1

        f = file(str(self.rsgf_filename), 'a')
        f.write("Rank of white: {0}, rank of black: {1} \n".format(self.g.get_player_rank('w'), self.g.get_player_rank('b')))
        lost_percent = 0
        previous_best = 47
        position_evaluation = dict()
        if self.current_move in self.move_range and self.current_move > 1:
            answer, next_moves, previous_position_evaluation = self.run_analysis(self.current_move - 1)
            wrs = [pos['value network win rate'] for pos in position_evaluation['variations']]
            previous_best = max([float(wr.strip(' \t\n\r%')) for wr in wrs])
            lost_percent = 0

        while self.current_move <= self.max_move:
            answer = ""
            if self.current_move in self.move_range:
                parent = go_to_move(self.move_zero, self.current_move - 1)
                if len(parent) > 1:
                    log("Removing existing", len(parent) - 1, "variations")
                    for other_leaf in parent[1:]:
                        other_leaf.delete()
                answer, next_moves, position_evaluation = self.run_analysis(self.current_move)

                self.total_done += 1

                log("For this position,", self.bot.bot_name, "would play:", answer)
                log("Analysis for this move is completed")
            elif self.move_range:
                log("Move", self.current_move, "not in the list of moves to be analysed, skipping")

            if self.current_move in self.move_range:
                game_move = go_to_move(self.move_zero, self.current_move).get_move()[1]

                wrs = [pos['value network win rate'] for pos in position_evaluation['variations']]
                current_best = max([float(wr.strip(' \t\n\r%')) for wr in wrs])
                lost_percent = 100 - previous_best - current_best
                if lost_percent > 0:
                    lost_percent = '+{0}'.format(lost_percent)
                previous_best = current_best
                if self.current_move > self.move_range[0]:
                    if self.current_move % 2 == 1:
                        f.write('Move #{0}, made by b: Played at {1}, {2}% in WR. All stats: {3} \n'.format(
                            str(self.current_move - 1),
                            str(ij2gtp(go_to_move(self.move_zero, self.current_move - 1).get_move()[1])),
                            str(lost_percent), str(previous_position_evaluation)))
                        f.flush()
                    else:
                        f.write('Move #{0}, made by w: Played at {1}, {2}% in WR. All stats: {3} \n'.format(
                            str(self.current_move - 1),
                            str(ij2gtp(go_to_move(self.move_zero, self.current_move - 1).get_move()[1])),
                            str(lost_percent), str(previous_position_evaluation)))
                        f.flush()

                previous_position_evaluation = position_evaluation
                wrs = [pos['value network win rate'] for pos in position_evaluation['variations']]
                current_best = max([float(wr.strip(' \t\n\r%')) for wr in wrs])
                lost_percent = 100 - previous_best - current_best
                previous_best = current_best

                if game_move:
                    if self.no_variation_if_same_move:
                        if ij2gtp(game_move) == answer:
                            log(
                                "Bot move and game move are the same (" + answer + "), removing variations for this move")
                            parent = go_to_move(self.move_zero, self.current_move - 1)
                            for child in parent[1:]:
                                child.delete()

            if answer == "RESIGN":
                log("")
                log("The analysis will stop now")
                log("")
                self.move_range = []
            # the bot has proposed to resign, and resign_at_first_stop is ON
            elif self.move_range:
                one_move = go_to_move(self.move_zero, self.current_move)
                player_color, player_move = one_move.get_move()
                if player_color in ('w', "W"):
                    log("now asking " + self.bot.bot_name + " to play the game move: white at", ij2gtp(player_move))
                    self.play('w', ij2gtp(player_move))
                else:
                    log("now asking " + self.bot.bot_name + " to play the game move: black at", ij2gtp(player_move))
                    self.play('b', ij2gtp(player_move))

            self.current_move += 1

        f.close()
        return True

    def abort(self):
        log("Leaving follow_anlysis()")

    def terminate_bot(self):
        try:
            log("killing", self.bot.bot_name)
            self.bot.close()
        except Exception, e:
            log(e)

    def close(self):
        log("RunAnalysis closed")
        self.completed = True


class BotOpenMove():
    def __init__(self, sgf_g, profile):
        self.name = 'Bot'
        self.bot = None
        self.okbot = False
        self.sgf_g = sgf_g
        self.profile = profile

    def start(self, silentfail=True):
        try:
            result = self.my_starting_procedure(self.sgf_g, profile=self.profile, silentfail=silentfail)
            if result:
                self.bot = result
                self.okbot = True
            else:
                self.okbot = False
        except Exception, e:
            log("Could not launch " + self.name)
            log(e)
            self.okbot = False
        return

    def undo(self):
        if self.okbot:
            self.bot.undo()

    def place(self, move, color):
        if self.okbot:
            if not self.bot.place(move, color):
                # self.config(state='disabled')
                return False
            return True

    def quick_evaluation(self, color):
        return self.bot.quick_evaluation(color)

    def click(self, color):
        log(self.name, "play")
        n0 = time.time()
        if color == 1:
            move = self.bot.play_black()
        else:
            move = self.bot.play_white()
        log("move=", move, "in", time.time() - n0, "s")
        return move

    def close(self):
        if self.okbot:
            log("killing", self.name)
            self.bot.close()


def bot_starting_procedure(bot_name, bot_gtp_name, bot_gtp, sgf_g, profile, silentfail=False):
    log("Bot starting procedure started with profile =", profile["profile"])
    log("\tbot name:", bot_name)
    log("\tbot gtp name", bot_gtp_name)

    command_entry = profile["command"]
    parameters_entry = profile["parameters"]

    size = sgf_g.get_size()

    try:

        log("Starting " + bot_name + "...")
        try:
            # bot_command_line=[grp_config.get(bot_name, command_entry)]+grp_config.get(bot_name, parameters_entry).split()
            bot_command_line = [command_entry] + parameters_entry.split()
            bot = bot_gtp(bot_command_line)
        except Exception, e:
            raise GRPException((_(
                "Could not run %s using the command from config.ini file:") % bot_name) + "\n" + command_entry + " " + parameters_entry + "\n" + unicode(
                e))

        log(bot_name + " started")
        log(bot_name + " identification through GTP...")
        try:
            answer = bot.name()
        except Exception, e:
            raise GRPException(
                (_("%s did not reply as expected to the GTP name command:") % bot_name) + "\n" + unicode(e))

        if bot_gtp_name != 'GtpBot':
            if answer != bot_gtp_name:
                raise GRPException((_(
                    "%s did not identify itself as expected:") % bot_name) + "\n'" + bot_gtp_name + "' != '" + answer + "'")
        else:
            bot_gtp_name = answer

        log(bot_name + " identified itself properly")
        log("Checking version through GTP...")
        try:
            bot_version = bot.version()
        except Exception, e:
            raise GRPException(
                (_("%s did not reply as expected to the GTP version command:") % bot_name) + "\n" + unicode(e))

        log("Version: " + bot_version)
        log("Setting goban size as " + str(size) + "x" + str(size))
        try:
            ok = bot.boardsize(size)
        except:
            raise GRPException((_(
                "Could not set the goboard size using GTP command. Check that %s is running in GTP mode.") % bot_name))

        if not ok:
            raise GRPException(_("%s rejected this board size (%ix%i)") % (bot_name, size, size))

        log("Clearing the board")
        bot.reset()

        log("Checking for existing stones or handicap stones on the board")
        gameroot = sgf_g.get_root()
        if node_has(gameroot, "HA"):
            nb_handicap = node_get(gameroot, "HA")
            log("The SGF indicates", nb_handicap, "stone(s)")
        else:
            nb_handicap = 0
            log("The SGF does not indicate handicap stone")
        # import pdb; pdb.set_trace()
        board, unused = sgf_moves.get_setup_and_moves(sgf_g)
        nb_occupied_points = len(board.list_occupied_points())
        log("The SGF indicates", nb_occupied_points, "occupied point(s)")

        free_handicap_black_stones_positions = []
        already_played_black_stones_position = []
        already_played_white_stones_position = []

        for color, move in board.list_occupied_points():
            if move != None:
                row, col = move
                move = ij2gtp((row, col))
                if color.lower() == 'b':
                    if nb_handicap > 0:
                        free_handicap_black_stones_positions.append(move)
                        nb_handicap -= 1
                    else:
                        already_played_black_stones_position.append(move)
                else:
                    already_played_white_stones_position.append(move)

        if len(free_handicap_black_stones_positions) > 0:
            log("Setting handicap stones at", " ".join(free_handicap_black_stones_positions))
            bot.set_free_handicap(free_handicap_black_stones_positions)

        for stone in already_played_black_stones_position:
            log("Adding a black stone at", stone)
            bot.place_black(stone)

        for stone in already_played_white_stones_position:
            log("Adding a white stone at", stone)
            bot.place_white(stone)

        log("Setting komi at", sgf_g.get_komi())
        bot.komi(sgf_g.get_komi())

        log(bot_name + " initialization completed")

        bot.bot_name = bot_gtp_name
        bot.bot_version = bot_version
    except Exception, e:
        if silentfail:
            log(e)
        else:
            log(unicode(e))
        return False
    return bot


def parse_command_line(filename, argv):
    g = open_sgf(filename)

    move_zero = g.get_root()

    leaves = get_all_sgf_leaves(move_zero)

    found = False

    # argv=[(unicode(p,errors="replace"),unicode(v,errors="replace")) for p,v in argv] #ok, this is maybe overkill...
    variation = 1

    nb_moves = leaves[variation - 1][1]
    log("Moves for this variation:", nb_moves)

    if nb_moves == 0:
        log("This variation is empty (0 move), the analysis cannot be performed!")
        sys.exit()

    # nb_moves=get_moves_number(move_zero)

    move_selection = range(1, nb_moves + 1)
    intervals = "all moves"
    log("Range: all")

    found = False
    for p, v in argv:
        if p == "--color":

            if v in ["black", "white"]:
                log("Color:", v)
                move_selection = check_selection_for_color(move_zero, move_selection, v)
                intervals += " (" + v + "only)"
                found = True
                break
            elif v == "both":
                break
            else:
                print("Wrong color parameter\n")
                sys.exit()
    if not found:
        intervals += " (both colors)"
        log("Color: both")

    found = False
    for p, v in argv:
        if p == "--komi":
            try:
                komi = float(v)
                found = True
            except:
                print("Wrong komi parameter\n")
                sys.exit()
    if not found:
        try:
            komi = g.get_komi()
        except Exception, e:
            msg = "Error while reading komi value, please check:\n" + unicode(e)
            msg += "\nPlease indicate komi using --komi parameter"
            log(msg)
            print("Error! " + msg)
            sys.exit()

    log("Komi:", komi)

    found = False
    for p, v in argv:
        if p == "--profile":
            profile = v
            found = True
    if not found:
        profile = None
    log("Profile:", profile)

    nogui = False
    for p, v in argv:
        if p == "--no-gui":
            nogui = True
            break

    return move_selection, intervals, variation, komi, nogui, profile


def opposite_rate(value):
    return str(100 - float(value[:-1])) + "%"


def get_position_short_comments(current_move, gameroot):
    # One line comment
    comments = ""

    node = get_node(gameroot, current_move)
    game_move_color, game_move = node.get_move()

    if not game_move_color:
        game_move_color = guess_color_to_play(gameroot, current_move)
    comments += "%i/%i: " % (current_move, get_node_number(gameroot))

    if node_has(node, "BWWR"):
        comments += node_get(node, "BWWR") + "\n"
    elif node_has(node, "VNWR"):
        comments += node_get(node, "VNWR") + "\n"
    elif node_has(node, "MCWR"):
        comments += node_get(node, "MCWR") + "\n"
    elif node_has(node, "ES"):
        comments += node_get(node, "ES") + "\n"
    else:
        comments += "\n"

    comments += "\n"
    if game_move_color.lower() == "b":
        if node_has(gameroot, "PB"):
            player = node_get(gameroot, "PB")
        else:
            player = _("Black")
    else:
        if node_has(gameroot, "PW"):
            player = node_get(gameroot, "PW")
        else:
            player = _("White")

    comments += "%s: %s" % (player, ij2gtp(game_move))

    if node_has(node, "CBM"):
        bot = node_get(gameroot, "BOT")
        comments += "\n%s: %s" % (bot, node_get(node, "CBM"))
        try:
            if node_has(node[1], "BKMV"):
                if node_get(node[1], "BKMV") == "yes":
                    comments += ": " + _("Book move")
        except:
            pass
    else:
        comments += "\n"
    return comments


def get_node_number(node):
    return get_moves_number(node)


def get_node(root, number=0):
    if number == 0: return root
    node = root
    k = 0
    while k != number:
        if not node:
            return False
        node = node[0]
        k += 1
    return node


def node_set(node, property_name, value):
    if type(value) == type(u"abc"):
        value = value.encode("utf-8")
    if property_name.lower() in ("w", "b"):
        node.set_move(property_name.encode("utf-8"), value)
    elif property_name.upper() in ("TBM", "TWM", "IBM", "IWM"):
        new_list = []
        for ij in value:
            new_list.append(ij2sgf(ij).encode("utf-8"))
        if type(property_name) == type(u"abc"):
            property_name = property_name.encode("utf-8")
        node.set_raw_list(property_name, new_list)
    else:
        if type(property_name) == type(u"abc"):
            property_name = property_name.encode("utf-8")
        node.set(property_name, value)


def node_get(node, property_name):
    if type(property_name) == type(u"abc"):
        property_name = property_name.encode("utf-8")
    value = node.get(property_name)
    if type(value) == type(str("abc")):
        value = value.decode("utf-8")
    return value


def node_has(node, property_name):
    if type(property_name) == type(u"abc"):
        property_name = property_name.encode("utf-8")
    return node.has_property(property_name)


def guess_color_to_play(move_zero, move_number):
    one_move = go_to_move(move_zero, move_number)

    if one_move == False:
        previous_move_color = guess_color_to_play(move_zero, move_number - 1)
        if previous_move_color.lower() == 'b':
            return "w"
        else:
            return "b"

    player_color, unused = one_move.get_move()
    if player_color != None:
        return player_color

    if one_move is move_zero:
        if node_has(move_zero, "PL"):
            if node_get(move_zero, "PL").lower() == "b":
                return "w"
            if node_get(move_zero, "PL").lower() == "w":
                return "b"
        else:
            return "w"

    previous_move_color = guess_color_to_play(move_zero, move_number - 1)

    if previous_move_color.lower() == 'b':
        return "w"
    else:
        return "b"


def get_available():
    from leela_zero_analysis import LeelaZero

    bots = []
    for bot in [LeelaZero]:
        profiles = get_bot_profiles(bot["name"])
        for profile in profiles:
            bot2 = dict(bot)
            bots.append(bot2)
            for key, value in profile.items():
                bot2[key] = value
    return bots


def get_bot_profiles(bot="", withcommand=True):
    sections = grp_config.get_sections()
    if bot != "":
        bots = [bot]
    else:
        bots = ["Leela", "GnuGo", "Ray", "AQ", "LeelaZero", "Pachi", "PhoenixGo"]
    profiles = []
    for section in sections:
        for bot in bots:
            if bot + "-" in section:
                command = grp_config.get(section, "command")
                if (not command) and (withcommand == True):
                    continue
                data = {"bot": bot, "command": "", "parameters": "", "timepermove": "", "variations": "4",
                        "deepness": "4"}
                for option in grp_config.get_options(section):
                    value = grp_config.get(section, option)
                    data[option] = value
                profiles.append(data)

    return profiles


class BotProfiles(Frame):
    def __init__(self, parent, bot):
        Frame.__init__(self, parent)
        self.parent = parent
        self.bot = bot
        self.profiles = get_bot_profiles(bot, False)
        profiles_frame = self

        self.listbox = Listbox(profiles_frame)
        self.listbox.grid(column=10, row=10, rowspan=10)
        self.update_listbox()

        row = 10
        Label(profiles_frame, text=_("Profile")).grid(row=row, column=11, sticky=W)
        self.profile = StringVar()
        Entry(profiles_frame, textvariable=self.profile, width=30).grid(row=row, column=12)

        row += 1
        Label(profiles_frame, text=_("Command")).grid(row=row, column=11, sticky=W)
        self.command = StringVar()
        Entry(profiles_frame, textvariable=self.command, width=30).grid(row=row, column=12)

        row += 1
        Label(profiles_frame, text=_("Parameters")).grid(row=row, column=11, sticky=W)
        self.parameters = StringVar()
        Entry(profiles_frame, textvariable=self.parameters, width=30).grid(row=row, column=12)

        row += 10
        buttons_frame = Frame(profiles_frame)
        buttons_frame.grid(row=row, column=10, sticky=W, columnspan=3)
        Button(buttons_frame, text=_("Add profile"), command=self.add_profile).grid(row=row, column=1, sticky=W)
        Button(buttons_frame, text=_("Modify profile"), command=self.modify_profile).grid(row=row, column=2, sticky=W)
        Button(buttons_frame, text=_("Delete profile"), command=self.delete_profile).grid(row=row, column=3, sticky=W)
        Button(buttons_frame, text=_("Test"),
               command=lambda: self.parent.parent.test(self.bot_gtp, self.command, self.parameters)).grid(row=row,
                                                                                                          column=4,
                                                                                                          sticky=W)
        self.listbox.bind("<Button-1>", lambda e: self.after(100, self.change_selection))

        self.index = -1

    def clear_selection(self):
        self.index = -1
        self.profile.set("")
        self.command.set("")
        self.parameters.set("")

    def change_selection(self):
        try:
            index = self.listbox.curselection()[0]
            self.index = index
            log("Profile", index, "selected")
        except:
            log("No selection")
            self.clear_selection()
            return
        data = self.profiles[index]
        self.profile.set(data["profile"])
        self.command.set(data["command"])
        self.parameters.set(data["parameters"])

    def empty_profiles(self):
        profiles = self.profiles
        sections = grp_config.get_sections()
        for bot in [profile["bot"] for profile in profiles]:
            for section in sections:
                if bot + "-" in section:
                    grp_config.remove_section(section)
        self.update_listbox()

    def create_profiles(self):
        profiles = self.profiles
        p = 0
        for profile in profiles:
            bot = profile["bot"]
            for key, value in profile.items():
                if key != "bot":
                    grp_config.add_entry(bot + "-" + str(p), key, value)
            p += 1
        self.update_listbox()

    def add_profile(self):
        profiles = self.profiles
        if self.profile.get() == "":
            return
        data = {"bot": self.bot}
        data["profile"] = self.profile.get()
        data["command"] = self.command.get()
        data["parameters"] = self.parameters.get()
        self.empty_profiles()
        profiles.append(data)
        self.create_profiles()
        self.clear_selection()

    def modify_profile(self):
        profiles = self.profiles
        if self.profile.get() == "":
            return

        if self.index < 0:
            log("No selection")
            return
        index = self.index

        profiles[index]["profile"] = self.profile.get()
        profiles[index]["command"] = self.command.get()
        profiles[index]["parameters"] = self.parameters.get()

        self.empty_profiles()
        self.create_profiles()
        self.clear_selection()

    def delete_profile(self):
        profiles = self.profiles

        if self.index < 0:
            log("No selection")
            return
        index = self.index

        self.empty_profiles()
        del profiles[index]
        self.create_profiles()
        self.clear_selection()

    def update_listbox(self):
        profiles = self.profiles
        self.listbox.delete(0, END)
        for item in [profile["bot"] + " - " + profile["profile"] for profile in profiles]:
            self.listbox.insert(END, item)
