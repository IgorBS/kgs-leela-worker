# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from toolbox import *
from optparse import OptionParser


def params():
    """get options from console"""
    usage = "usage: %prog directory bot threads/gpu [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("-d", "--directory",
                      action="store", type="string", dest="sgf_directory", default=None,
                      help="Указание директории с .sgf-файлами. Данные, собранные во время анализа этих партий будут являться рефернсными")
    parser.add_option("-s", "--start_move",
                      action="store", type="int", dest="start_move", default=20,
                      help="Указание хода, с которого будет осуществлен анализ, по умолчанию 20")
    # parser.add_option("-f", "--file",
    #                   action="store", type="string", dest="sgf_file", default=None,
    #                   help="Указание .sgf-файла, который будет анализироваться и сопоставляться с рефернсными данными")
    # parser.add_option("-r", "--reference",
    #                   action="store", type='string', dest='reference', default=None,
    #                   help="Указание файла с рефернсными данными, накопленынми раннее")
    # parser.add_option("-b", "--bot",
    #                   action="store", type='string', dest='bot', default=None,
    #                   help="Указание бота, который будет анализировать партии")
    # parser.add_option("-t", "--time",
    #                   action="store", type='string', dest='time', default=5,
    #                   help="Указание времени, которое бот будет анализировать каждый ход в партии")
    #parser.add_option("-v", "--visits",
    #                   action="store", type='int', dest='visits', default=10000,
    #                   help="Указание количества плейаутов на ход")
    #parser.add_option("--threads",
    #                  action="store", type='int', dest='threads', default=4,
    #                  help="Указание количество ядер CPU, которое будет использовать бот")
    #parser.add_option("-g", "--gpu",
    #                  action="store", type='int', dest='gpu', default=6,
    #                  help="Указание количество ядер GPU, которое будет использовать бот")

    (options, args) = parser.parse_args()
    return options, args


def main():
    options, args = params()
    dir = options.sgf_directory
    start_move = options.start_move
    # visits = options.visits
    # threads = options.threads
    # gpu = options.gpu
    if dir is not None:
        if os.path.exists(dir) == False:
            log("dir doesn't exists")
            sys.exit()
        else:
            leela = MasterAnalyze(dir, start_move)
            leela.start()

main()

