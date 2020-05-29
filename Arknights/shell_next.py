import itertools
import sys
from .fancycli import fancywait


def skipcallback(handler):
    raise StopIteration


def delay_impl_factory(helper, statusline, show_toggle):
    togglelabel = lambda: '<r>切换自动补充理智(%s)' % ('ON' if helper.use_refill else 'OFF')

    def togglecallback(handler):
        helper.use_refill = not helper.use_refill
        handler.label = togglelabel()

    skiphandler = fancywait.KeyHandler('<ENTER>跳过', b'\r', skipcallback)
    skipdummy   = fancywait.KeyHandler('           ', b'', lambda x: None)
    if show_toggle and helper.use_refill:
        togglehandler = fancywait.KeyHandler(togglelabel(), b'r', togglecallback)
    else:
        togglehandler = fancywait.KeyHandler(None, None, None)

    def delay_impl(timeout):
        fancywait.fancy_delay(timeout, statusline, [skiphandler if timeout > 9 else skipdummy, togglehandler])

    return delay_impl


def _create_helper(show_toggle=False):
    from Arknights.helper import ArknightsHelper
    helper = ArknightsHelper()

    io = sys.stdout.buffer
    if hasattr(io, 'raw'):
        io = io.raw
    line = fancywait.StatusLine(io)
    helper._shellng_with = line
    helper.delay_impl = delay_impl_factory(helper, line, show_toggle)
    return helper


def quick(argv):
    """
    quick [n]
        重复挑战当前画面关卡特定次数或直到理智不足
    """
    if len(argv) == 2:
        count = int(argv[1])
    else:
        count = 114514
    helper = _create_helper(True)
    with helper._shellng_with:
        helper.module_battle_slim(
            c_id=None,
            set_count=count,
        )
    return 0


class ItemsWrapper:
    def __init__(self, obj):
        self.obj = obj
    def __len__(self):
        return len(self.obj)
    def items(self):
        return self.obj


def auto(argv):
    """
    auto stage1 count1 [stage2 count2] ...
        按顺序挑战指定关卡特定次数直到理智不足
    """
    from Arknights.click_location import MAIN_TASK_SUPPORT
    arglist = argv[1:]
    if len(arglist) % 2 != 0:
        print('usage: auto stage1 count1 [stage2 count2] ...')
        return 1
    it = iter(arglist)
    tasks = [(stage.upper(), int(counts)) for stage, counts in zip(it, it)]
    # for stage, count in tasks:
    #     if stage not in MAIN_TASK_SUPPORT:
    #         print('stage %s not supported' % stage)
    #         return 1
    helper = _create_helper(True)
    with helper._shellng_with:
        helper.main_handler(
            clear_tasks=False,
            task_list=tasks,
            auto_close=False
        )
    return 0


def collect(argv):
    """
    collect
        收集每日任务奖励
    """
    helper = _create_helper()
    with helper._shellng_with:
        helper.clear_daily_task()
    return 0


def recruit(argv):
    """
    recruit [tags ...]
        公开招募识别/计算，不指定标签则从截图中识别
    """
    from . import recruit_calc

    if 2 <= len(argv) <= 6:
        tags = argv[1:]
        result = recruit_calc.calculate(tags)
    elif len(argv) == 1:
        helper = _create_helper()
        with helper._shellng_with:
            result = helper.recruit()
    else:
        print('要素过多')
        return 1

    colors = ['\033[36m', '\033[90m', '\033[37m', '\033[32m', '\033[93m', '\033[91m']
    reset = '\033[39m'
    for tags, operators, rank in result:
        taglist = ','.join(tags)
        if rank >= 1:
            taglist = '\033[96m' + taglist + '\033[39m'
        print("%s: %s" % (taglist, ' '.join(colors[op[1]] + op[0] + reset for op in operators)))


def interactive(argv):
    """
    interactive
        进入交互模式，减少按键次数（
    """
    import shlex
    import traceback
    while True:
        try:
            cmdline = input("akhelper> ")
            argv = shlex.split(cmdline)
            if len(argv) == 0 or argv[0] == '?' or argv[0] == 'help':
                print(' '.join(x.__name__ for x in interactive_cmds))
                continue
            cmd = match_cmd(argv[0], interactive_cmds)
            if cmd is not None:
                cmd(argv)
        except EOFError:
            break
        except (Exception, KeyboardInterrupt):
            traceback.print_exc()
            continue



def help(argv):
    """
    help
        输出本段消息
    """
    print("usage: %s command [command args]" % help.argv0)
    print("commands (prefix abbreviation accepted):")
    for cmd in global_cmds:
        print("    " + str(cmd.__doc__.strip()))


def exit(argv):
    sys.exit()

help.argv0 = 'placeholder'

global_cmds = [quick, auto, collect, recruit, interactive, help]
interactive_cmds = [quick, auto, collect, recruit, exit]

def match_cmd(first, avail_cmds):
    targetcmd = [x for x in avail_cmds if x.__name__.startswith(first)]
    if len(targetcmd) == 1:
        return targetcmd[0]
    elif len(targetcmd) == 0:
        print("unrecognized command: " + first)
        return None
    else:
        print("ambiguous command: " + first)
        print("matched commands: " + ','.join(x.__name__ for x in targetcmd))
        return None

def main(argv):
    help.argv0 = argv[0]
    if len(argv) < 2:
        help(argv)
        return 1
    targetcmd = match_cmd(argv[1], global_cmds)
    if targetcmd is not None:
        return targetcmd(argv[1:])
    return 1


if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))

__all__ = ['main']
