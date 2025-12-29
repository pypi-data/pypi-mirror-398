from collections.abc import Container as _Container
from time import sleep as _sleep
from typing import Any as _Any, List as _List, Union as _Union, Callable as _Callable, Tuple as _Tuple, Dict as _Dict
from warnings import warn as _warn
from types import FunctionType as _Function, ModuleType as _Lib, FrameType as _FrameType
from traceback import print_exc as _perr
from sys import version as _ver, platform as _plat, version_info as _vin, executable as _ee, argv as _a, exit as _exit
from os import system as _system
from signal import signal as _signal, SIGQUIT as _sigquit
import builtins as _built
import math as _math
import random as _random
import time as _time
import datetime as _datetime
import cmath as _cmath
try:
    from sys import ps1 as _ps1
except ImportError:
    _ps1 = ">>> "
try:
    from sys import ps2 as _ps2
except ImportError:
    _ps2 = "... "

class _ExitError(BaseException):
    def __init__(self, message: str = "进程被退出 / Process exit"):
        self.message = message
        super().__init__(message)

def _er(signum: int, frame: _FrameType | None) -> None:
    raise _ExitError

_signal(_sigquit, _er)

def _tests() -> None:
    """t"""
    pass
__O__: bool = __debug__ and not _tests.__doc__ is None
__OO__: bool = _tests.__doc__ is None
__OP__: bool = not __debug__

_clear: str = "\033[2J\033[H"
__all__: _Tuple[str, ...] = (
    "string_byte_dance",
    "str_byte_dance",
    "bd",
    "sbd",
    "byte_dance",
    "container_byte_dance",
    "cbd",
    "helps",
    "install",
    "upgrade",
    "versions",
    "execute"
)
__version__: str = "1.3.0a3"
__requires__: str = ">=3.6"
__anchor__: str = "nousername"
__email__: str = "2467906561@qq.com"
__url__: str = "https://pypi.org/project/byteprint"
__license__: str = "MIT"
__doc__: str = f"""
字节跳动系列 / ByteDance Series
支持字符串、容器 / Supports strings and containers
你甚至还可以设置延迟是毫秒还是秒 / You can even set the delay to milliseconds or seconds
字节跳动，也就是类似打字机的效果 / ByteDance, which is similar to a typewriter
bd支持所有了哦！也有对应的全名了！/ bd support everything! There is also a corresponding full name!
byteprint库，全名byte print，也就是说，对应BytePrint库，缩写bp / Byteprint library, full name byte print, that is, corresponding to BytePrint library, abbreviated as bp
提示：可以使用`import byteprint as bp` / Tip: You can use `import byteprint as bp`
mypy 测试通过（如果不信，可以前往 {__url__}/{__version__}/#files 下载源码进行查看）/
The mypy test passed (if you don't believe it, you can to {__url__}/{__version__}/#files to download the source code to check it
其中，AnyConNstr代表“所有可迭代对象，除了字符串” / Where, AnyConNstr stands for "All iterable objects, except str"

对应系列 / Correspondence series
> 1.x
> 1.3.x
> 1.3.0.x
对应正式版 / Corresponding to the official version
> 1.3.0
上一个正式版 / Previous official version
> 1.2.7.1
上一个 a.b.c / Previous a.b.c.
> 1.2.7
再上一个 a.b.c / The previous a.b.c.
> 1.2.6
上一个测试版 / Previous beta version
> 1.3.0a2
"""
__play__: str = """
你说得对
但是BytePrint库是由nousername基于print，结合Python开发的BytePrint库
运行在一个叫做「Python >= 3.6」，在这里，被选中的人将被授予「字节跳动能力」，导引「节奏打印之力」
你将扮演程序员，在byteprint库中进行探索，同时逐步发掘未找到的bug。

you're right
However, the BytePrint library is a BytePrint library developed by nousername based on print and in conjunction with Python
Running on a computer called "Python >= 3.6," where the selected person will be awarded the "ByteDance Ability" to guide the "power of rhythm printing."
You will play the role of a programmer, exploring the byteprint library while gradually discovering undiscovered bugs.
"""

def string_byte_dance(content: _Any, speed: _Union[int, float] = 30, end: _Any = "\n", ms_mode: bool = True) -> None:
    """
    :note: 别看我只是一个简简单单的str类型，实际我支持所有 / Don't be fooled by the simple STR type - I actually support all types
    :param Any content: 内容，建议为str类型 / Content, str type is recommended
    :param int|float speed: 打印速度，默认30 / Printing speed, default 30
    :param Any end: 结尾参数，默认换行 / End parameter, default line wrap
    :param bool ms_mode: 是否设置为毫秒模式，默认True / Whether to set millisecond mode, default True
    :note: 参数除了content，其他都是位置参数，ms_mode关闭时建议同时修改speed / Parameters except contentExcept for content, all parameters are locationExcept for content, all parameters are location parametersExcept for content, all parameters are location parameters; it's recommended to modify speed when ms_mode is disabled
    :return: None: 仅限打印内容 / Only for printing content
    :raises TypeError: speed强制，必须为int或float类型，否则报错 / speed is mandatory, must be int or float type, otherwise an error is raised
    :raises ValueError: speed必须≥0，否则报错 / speed must be ≥ 0, otherwise an error is raised
    :warning: speed不能为0，否则警告提醒你 / speed cannot be 0, otherwise a warning is issued
    :warning: ms_mode为布尔值，建议传入bool类型 / ms_mode should be a boolean value, it's recommended to pass bool type
    :warning: ms_mode为布尔值，建议传入bool类型 / ms_mode should be a boolean value, it's recommended to pass bool type
    """
    if not isinstance(speed, (int, float)):
        raise TypeError(f"不合适的参数类型：{type(speed).__name__}\n请确保它的参数类型为：int 或 float\nInappropriate parameter type: {type(speed).__name__}\nPlease ensure it is int or float type")
    if speed < 0:
        raise ValueError(f"不合适的范围：{speed}，你必须得确保它大于等于0以上\nInappropriate range: {speed}\nPlease ensure it is greater than or equal to 0")
    if speed == 0:
        _warn("speed数值为0时你干脆直接使用print算了！\nWhen speed is 0, you might as well use print directly!", UserWarning, stacklevel=2)
    if not isinstance(ms_mode, bool):
        _warn(f"ms_mode建议为布尔值，不然可能偏离预想，结果你的输入却是{type(ms_mode).__name__}类型\nms_mode is recommended to be boolean, otherwise results may deviate from expectations. Your input is {type(ms_mode).__name__} type", UserWarning, stacklevel=2)
        ms_mode = bool(ms_mode)
    content = str(content)
    if ms_mode:
        speed /= 1000
    for i in content:
        print(end = i, flush = True)
        _sleep(speed)
    print(end = str(end))

def str_byte_dance(content: _Any, speed: _Union[int, float] = 30, end: _Any = "\n", ms_mode: bool = True) -> None:
    """
    :note: 这是一个名称简化的string_byte_dance函数 / This is a simplified-named version of str_byte_dance
    :param Any content: 对应content / Corresponded content
    :param int|float speed: 对应speed，默认为30 / Corresponded speed, default 30
    :param Any e: 对应end，默认换行 / Corresponded end , default line wrap
    :param bool ms_mode: 对应ms_mode，默认为True / Corresponded ms_mode, default True
    :note: 具体内容请看被简化的函数 / For details, refer to the original function
    :return: None: 与原函数机制一致 / Consistent with the original function mechanism
    :raises TypeError: 与原函数机制一致 / Consistent with the original function mechanism
    :raises ValueError: 与原函数机制一致 / Consistent with the original function mechanism
    :warning: 与原函数机制一致 / Consistent with the original function mechanism
    """
    string_byte_dance(content, speed = speed, end = end, ms_mode = ms_mode)

def bd(c: _Any, s: _Union[int, float] = 30, e: _Any = "\n", m: bool = True, p: _Any = "") -> None:
    """
    :note: 这是一个融合的sbd和cbd的函数 / This is a function that combines sbd and cbd
    :param Any c: 简化版content / Simplified content
    :param int|float s: 简化版speed，默认为30 / Simplified speed, default 30
    :param Any e: 简化版end，默认换行 / Simplified end , default line wrap
    :param bool m: 简化版ms_mode，默认为True / Simplified ms_mode, default True
    :param Any p: 简化版sep，字符串被忽略，默认空字符串 / Simplified sep, string ignored, default empty string
    :note: 具体内容请看被简化的函数 / For details, refer to the original function
    :return: None: 与原函数机制一致 / Consistent with the original function mechanism
    :raises TypeError: 与原函数机制一致 / Consistent with the original function mechanism
    :raises ValueError: 与原函数机制一致 / Consistent with the original function mechanism
    :warning: 与原函数机制一致 / Consistent with the original function mechanism
    :note: 会自动判断应该使用哪一类的 / will automatically determine which type to use
    """
    try:
        if isinstance(c, str):
            raise TypeError
        if not isinstance(c, dict):
            for i in c:
                break
        cbd(c, s = s, e = e, m = m, p = p)
    except TypeError:
        sbd(c, s = s, e = e, m = m)

def byte_dance(content: _Any, speed: _Union[int, float] = 30, end: _Any = "\n", ms_mode: bool = True, sep: _Any = "") -> None:
    """
    :note: 这是一个融合的sbd和cbd的函数 / This is a function that combines sbd and cbd
    :param Any content: 对应content / Corresponded c
    :param int|float speed: 对应s，默认为30 / Corresponded s, default 30
    :param Any end: 对应e，默认换行 / Corresponded e, default line wrap
    :param bool ms_mode: 对应m，默认为True / Corresponded m, default True
    :param Any sep: 对应p，默认空字符串 / Corresponded sep, default empty string
    :note: 具体内容请看被简化的函数 / For details, refer to the original function
    :return: None: 与原函数机制一致 / Consistent with the original function mechanism
    :raises TypeError: 与原函数机制一致 / Consistent with the original function mechanism
    :raises ValueError: 与原函数机制一致 / Consistent with the original function mechanism
    :warning: 与原函数机制一致 / Consistent with the original function mechanism
    :note: 会自动判断应该使用哪一类的 / will automatically determine which type to use
    """
    bd(content, s = speed, e = end, m = ms_mode, p = sep)

def sbd(c: _Any, s: _Union[int, float] = 30, e: _Any = "\n", m: bool = True) -> None:
    """
    :note: 这是一个名称简化的str_byte_dance函数 / This is a simplified-named version of str_byte_dance
    :param Any c: 简化版content / Simplified content
    :param int|float s: 简化版speed，默认为30 / Simplified speed, default 30
    :param Any e: 简化版end，默认换行 / Simplified end , default line wrap
    :param bool m: 简化版ms_mode，默认True / Simplified ms_mode, default True
    :note: 具体内容请看被简化的函数 / For details, refer to the original function
    :return: None: 与原函数机制一致 / Consistent with the original function mechanism
    :raises TypeError: 与原函数机制一致 / Consistent with the original function mechanism
    :raises ValueError: 与原函数机制一致 / Consistent with the original function mechanism
    :warning: 与原函数机制一致 / Consistent with the original function mechanism
    """
    str_byte_dance(c, speed = s, end = e, ms_mode = m)

def container_byte_dance(content: _Container[_Any], speed: _Union[int, float] = 30, end: _Any = "\n", ms_mode: bool = True, sep: _Any = "") -> None:
    """
    :note: 这是一个容器迭代方式，通过遍历来打印 / This is a container iteration method, printing through traversal
    :param AnyConNstr content: 一个容器，比如list, tuple（str不建议） / A container, e.g., list, tuple (str is not recommended)
    :param int|float speed: 打印速度，默认为30 / Printing speed, default 30
    :param Any end: 结尾参数，默认换行 / End parameter, default line wrap
    :param bool ms_mode: 是否设置为毫秒模式，默认True / Whether to set millisecond mode, default True
    :param Any sep: 每个之间的间隔填充，会占用，默认空字符串 / The interval between each is filled, which will occupy, and the default empty string
    :note: 参数除了content，其他都是位置参数，ms_mode关闭时建议同时修改speed / Except for content, all parameters are location parameters; it's recommended to modify speed when ms_mode is disabled
    :return: None: 仅限打印内容 / Only for printing content
    :raises TypeError: speed强制，必须为int或float类型，否则报错 / speed is mandatory, must be int or float type, otherwise an error is raised
    :raises TypeError: 强制内容content，必须可迭代，否则报错 / content must be iterable, otherwise an error is raised
    :raises ValueError: speed必须≥0，否则报错 / speed must be ≥ 0, otherwise an error is raised
    :warning: speed不能为0，否则警告提醒你 / speed cannot be 0, otherwise a warning is issued
    :warning: 如果content为Str类型，则发个警告 / If content is str type, a warning is issued
    :warning: ms_mode为布尔值，建议传入bool类型 / ms_mode should be a boolean value, it's recommended to pass bool type
    :note: 处理dict类型时，会先打印key，再打印value / When processing dict type, keys are printed first, then values
    """
    if not isinstance(speed, (int, float)):
        raise TypeError(f"不合适的参数类型：{type(speed).__name__}\n请确保它的参数类型为：int 或 float\nInappropriate parameter type: {type(speed).__name__}\nPlease ensure it is int or float type")
    if speed < 0:
        raise ValueError(f"不合适的范围：{speed}，你必须确保它大于等于0以上\nInappropriate range: {speed}\nPlease ensure it is greater than or equal to 0")
    if speed == 0:
        _warn("数值为0时，你干脆直接使用print算了！\nWhen speed is 0, you might as well use print directly!", UserWarning, stacklevel=2)
    if isinstance(content, str):
        _warn("这里是容器玩的地方，不是Str能来的地方\nThis is for containers, not str type!", UserWarning, stacklevel=2)
    if isinstance(content, dict):
        d: _List[_Any] = []
        e: _List[_Any] = []
        for a, b in content.items():
            d.append(a)
            e.append(b)
        content = d + e
    k: _List[_Any] = []
    try:
        for i in content:  # type: ignore[attr-defined]
            k.extend([i, str(sep)])
        k.pop()
        content = k
    except TypeError:
        raise TypeError(f"你这迭代对象可真特别呢：{type(content).__name__}\nThis iterable object is quite special: {type(content).__name__}")
    if not isinstance(ms_mode, bool):
        _warn(f"ms_mode建议为布尔值，不然可能偏离预想，结果你的输入却是{type(ms_mode).__name__}类型\nms_mode is recommended to be boolean, otherwise results may deviate from expectations. Your input is {type(ms_mode).__name__} type", UserWarning, stacklevel=2)
        ms_mode = bool(ms_mode)
    if ms_mode:
        speed /= 1000
    for i in content:
        print(end = str(i), flush = True)
        _sleep(speed)
    print(end = str(end))

def cbd(c: _Container[_Any], s: _Union[int, float] = 30, e: _Any = "\n" , m: bool = True, p: _Any = "") -> None:
    """
    :note: 这是一个名称简化的container_byte_dance函数 / This is a simplified-named version of container_byte_dance
    :param AnyConNstr c: 简化版content / Simplified content
    :param int|float s: 简化版speed，默认为30 / Simplified speed, default 30
    :param Any e: 简化版end，默认换行 / Simplified end , default line wrap
    :param bool m: 简化版ms_mode，默认为True / Simplified ms_mode, default True
    :param Any p: 简化版sep，默认空字符串 / Simplified sep, default empty string
    :note: 具体内容请看被简化的函数 / For details, refer to the original function
    :return: None: 与原函数机制一致 / Consistent with the original function mechanism
    :raises TypeError: 与原函数机制一致 / Consistent with the original function mechanism
    :raises ValueError: 与原函数机制一致 / Consistent with the original function mechanism
    :warning: 与原函数机制一致 / Consistent with the original function mechanism
    """
    container_byte_dance(c, speed = s, end = e, ms_mode = m, sep = p)

def helps(func: _Union[_Function, None] = None) -> None:
    """
    :note: 查看对应函数的文档（function）/用法的帮助（None） / View the corresponding function's documentation (function)/usage help (None)
    :param function|None func: 决定是查看函数的文档（function）还是用法的帮助（None）（默认） / Decide whether to view the function's documentation (function) or usage help (None)(default)
    :return: None: 单纯的文本输出 / Pure text output
    :raises TypeError: 输入的类型不是function或None / The type entered is not function or None
    :note: 只适用于内置的函数 / Only applies to built-in functions
    """
    if isinstance(func, _Function) and func.__module__ == "byteprint":
        sbd(f"{func.__name__}函数文档帮助 / {func.__name__} Function Documentation Help \n\n\n {func.__doc__}")
    elif func is None:
        sbd(f"""
        {_clear}
        欢迎来到函数帮助界面，这里将给予教程 /
        Welcome to the function help interface, where you will provide tutorials.
        
        我尽量保持真实！ / I try to be real!
        {'\0'*30}
        {_clear}
        首先，请看三个有功能的函数 /
        First, look at three functional functions

        > string_byte_dance
        > container_byte_dance
        > bd
        核心都是(c, s, e, m) / The core is all (c, s, e, m)
        c -> content (/)  [(存在差异) / there are differences]
        s -> speed  [int | float]
        e -> end  [_Any]
        m -> ms_mode  [bool]
        
        其中，容器还支持 / Among them, the container also supports
        p -> sep  [_Any]
        「“/” 代表 建议为位置参数 / '/' epresentative suggested location parameters」
        {'\0'*30}
        {_clear}
        接下来介绍 / then introduced

        > string_byte_dance
        
        对应缩写 / Corresponding abbreviation

        > sbd

        你可以把缩写看成一个快捷方式 /
        You can think of abbreviations as a shortcut
        
        示例 / example：
        {_ps1}from byteprint import sbd
        {_ps1}sbd('Hello world, python')""")
        sbd("        Hello world, python")
        sbd(f"        {_ps1}sbd('这是慢性 / This is chronic', 50)")
        sbd("        这是慢性 / This is chronic", 50)
        sbd(f"        {_ps1}sbd('秒级模式 / Second-level mode', 0.1, True)  # 具体规则请看帮助 / Please see Help for specific rules")
        sbd("        秒级模式 / Second-level mode", 0.1, True)
        sbd(f"        {_ps1}sbd('字符串 / String', '50')")
        print(f"""        Traceback (most recent call last):
          File \'<python-input-4>\', line 1, in <module>
            sbd('字符串 / String', '50')
            ~~~^^^^^^^^^^^^^^^^^^^^^^^^^
          File \'.../site-packages/byteprint.py\', line 117, in sbd
            str_byte_dance(c, s, ms_mode = m)
            ~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^
          File \'.../site-packages/byteprint.py\', line 67, in str_byte_dance
            string_byte_dance(content, speed, ms_mode = ms_mode)
            ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
          File \'.../site-packages/byteprint.py\', line 39, in string_byte_dance
            raise TypeError(f\'不合适的参数类型：{{type(speed).__name__}}\\n请确保它的参数类型为：int 或 float\\nInappropriate parameter type: {{type(speed).__name__}}\\nPlease ensure it is int or float type\')
        TypeError: 不合适的参数类型：str
        请确保它的参数类型为：int 或 float
        Inappropriate parameter type: str
        Please ensure it is int or float type""")
        sbd(f"""
        {_ps1}# 更多文档帮助，请使用 / For more documentation assistance, please use
        {_ps1}from byteprint import sbd
        {_ps1}help(sbd)
        {_ps1}# 或 / or
        {_ps1}import byteprint
        {_ps1}byteprint.helps(byteprint.sbd)
        {_ps1}# 或 查看源码 / or View source code {'\0'*60}
        {_clear}
        接下来介绍 / then introduced
        
        > container_byte_dance
        
        对应缩写 / Corresponding abbreviation
        
        > cbd
        
        示例 / example：
        {_ps1}from byteprint import cbd
        {_ps1}cbd(['中英', 'Sino-British', 'Hi'])""")
        cbd(['        ', '中英', 'Sino-British', 'Hi'])
        sbd(f"        {_ps1}cbd(['你好', '！', 'Hello', '!'], 120)")
        cbd(['        ', '你好', '！', 'Hello', '!'], 120)
        sbd(f"""
        {_ps1}# 更多文档帮助，请使用 / For more documentation assistance, please use
        {_ps1}from byteprint import cbd
        {_ps1}help(cbd)
        {_ps1}# 或 / or
        {_ps1}import byteprint
        {_ps1}byteprint.helps(byteprint.cbd)
        {_ps1}# 或 查看源码 / or View source code {'\0'*60}
        {_clear}
        最牛逼的还得是 / The best thing is
        
        > bd
        
        全称 / full name
        
        > byte_dance
        
        能厉害到什么程度？ / How powerful can it be?
        融合了sbd函数和cbd函数 / Fusion of sbd function and cbd function
        核心判断就是是否可迭代 / The core judgment is whether it is iterable or not
        可以算比较智能的了 / It can be regarded as relatively intelligent
        {_ps1}# 更多文档帮助，请使用 / For more documentation assistance, please use
        {_ps1}from byteprint import bd
        {_ps1}help(bd)
        {_ps1}# 或 / or
        {_ps1}import byteprint
        {_ps1}byteprint.helps(byteprint.bd)
        {_ps1}# 或 查看源码 / or View source code {'\0'*60}
        {_clear}
        要说压轴题啊，还得是 / To talk about the final question, it has to be
        
        > execute
        
        功能实在是太齐全了！ / The functions are so complete!
        里面就有一个特性没讲：续行符 / There is one feature not mentioned in it: continuation character
        
        {_ps1}from byteprint import execute
        {_ps1}execute(False)
        (省略 / omitted)
        (byteprint){_ps1}\
        (byteprint){_ps2}# 续行符非常神奇，在哪里都能用 /\
        (byteprint){_ps2}The continuation symbol is very magical and can be used anywhere
        (byteprint){_ps1}# 你甚至还能这么玩 / You can even play like this
        (byteprint){_ps1}bd(\"不许走，不许走\
        (byteprint){_ps2}Don't go, don't go'\", s = 300)
        """)
        bd("        不许走，不许走Don't go, don't go", s = 300)
        bd(f"""
        (byteprint){_ps1}# 麻烦的还得是它
        (byteprint){_ps1}[ \
        (byteprint){_ps2}  2, 3, 4, 5, 6, 7\
        (byteprint){_ps2}]
        
        {_ps1}# 更多文档帮助，请使用 / For more documentation assistance, please use
        {_ps1}from byteprint import execute
        {_ps1}help(execute)
        {_ps1}# 或 / or
        {_ps1}import byteprint
        {_ps1}byteprint.helps(byteprint.execute)
        {_ps1}# 或 查看源码 / or View source code {'\0'*60}
        {_clear}
        好啦，教程就到这里 / Okay, that's all for the tutorial
        祝你用库愉快！ / I wish you a happy use of the library!
        
        提示：使用execute函数进行内部执行方式 /
        Tip: Use the execute function for internal execution
        你甚至都能玩出花样 / You can even play tricks
        [Version {__version__}] [__all__ length : {len(__all__)}
        """)
    else:
        raise TypeError(f"请确保输入的类型为None或者Function，你输入类型的是{type(func).__name__}\nPlease make sure the type you enter is None or Function, and the type you enter is {type(func).__name__}")

def install(vers: str) -> None:
    """
    :param str vers: 下载的版本号 / Downloaded version number
    :return None: 自我下载没有返回 / Self-download did not return
    :note: 通过调用系统pip来进行自我下载 / Self-download by calling the system pip
    """
    _system(f"{_ee} -m pip install byteprint=={vers} --pre")

def upgrade(lib: str = "byteprint") -> None:
    """
    :param str lib: 进行更新的库，默认byteprint / Library to be updated, byteprint by default
    :return None: 自我更新没有返回 / Self-update did not return
    :note: 通过调用系统pip来进行自我更新 / Self-update by calling system pip
    """
    _system(f"{_ee} -m pip install {lib.lower()} --upgrade --pre")

def versions() -> None:
    """
    :return None: 自我检查没有返回 / Self-inspection did not return
    :note: 通过调用系统pip来进行自我检查 / Self-check by calling system pip
    """
    try:
        _system(f"{_ee} -m pip index versions byteprint --pre")
    except Exception:
        _system(f"{_ee} -m pip install pip --upgrade")
        _system(f"{_ee} -m pip index versions byteprint --pre")

def execute(inp: _Union[str, bool, None] = None, *args: _Any, **kwargs: _Any) -> _Any:
    """
    :note: 执行代码的方式其一，在一个简易交互式进行byteprint交互 / One way to execute code is to interact byteprint in a simple interactive format
    :param str|bool|None inp: 决定方式，str代表执行内部内容，None|bool代表进入交互，其中，bool决定是否用提示，None是询问 / Decision method, str represents execution of internal content, and Nonebool represents entry into interaction, where bool determines whether to use a prompt, and None is a query
    :param Any args: 你最好不要传多余的位置参数 / You'd better not pass unnecessary location parameters
    :param Any **kwargs: 接受任何参数导入环境之中 / Accept any parameters and import them into the environment
    :return Any: 使用exit函数可以传出东西了！ / Use the exit function to pass things out!
    :raises ValueError: 有别的位置参数闯入 / Another location parameter broke in
    :raises TypeError: 输入的类型不是str或None或bool / The type entered is not str or None or bool
    :note: >
        可交互内容如下： / The interactive content is as follows:
            'string_byte_dance' -> string_byteprint_dance.__doc__
            'str_byte_dance' -> 'string_byte_dance'
            'bd' -> bd.__doc__
            'sbd' -> 'str_byte_dance'
            'byte_dance' -> 'bd'
            'container_byte_dance'
            'cbd' -> 'container_byte_dance'
            'helps' -> helps.__doc__
            'help' -> '原版 / original help'
            'print' -> '原版 / original print'
            'clear' -> '清屏 / clear screen'
            'm' -> '颜色渲染 / color rendering'
            ...
            'eq' -> '赋值 / assignment'
            'globals' -> '查看全局变量 / View global variables'
            'rm' -> '删除 / remove'
            '__import__' -> '导入模块（math, cmath, random, time, datetime均已经导入） /\
            Import modules (math, cmath, random, time, datetime have all been imported'
            'lambda' -> '简易函数 / simple function'
            ...
            'info' (交互式 / interactive) -> '交互存在 / interactive existence'
            'exit' 顾名思义 / Hence the name and meaning
        ------
        其中，m函数用法特殊，只重点讲这个
        他本质就是一个字符串
        用法：
        m('渲染代码')
        示例：
        print(m('31') + '红色' + m(0)) -> \033[31m红色\033[0m
        就这么好用
        --
        Among them, the m function has a special usage, so I only focus on this
        He is essentially a string
        Usage:
        m('Render code')
        Example:
        print(m('31') + 'Red'+ m(0)) -> \033[31mRed\033[0m
        It works so well
        ------
        可以使用续行符，具体看helps()
        提示：使用多行时必须用续行符 / Tip: When using multiple lines, you must use a continuation character
        
        如果自己作死，本库概不负责 / If you die, we will not be responsible
    <
    """
    if args:
        raise ValueError(f"传了冗余位置参数：“{args}” / Redundant position parameters were passed: “{args}”")
    def _form(a: str) -> str:
        strs: bool = True
        b: str = ""
        for d in a.split(";"):
            cs: str = ""
            for i in d:
                if i in ["'", '"']:
                    strs = not strs
                if i in "#" and strs:
                    break
                cs += i
            b += cs.strip() + ";"
        return b[:-1]
    sl: _List[str] = ["functools", "itertools", "math", "cmath", "time", "datetime", "random", "tqdm", "sympy", "scipy", "numpy", "pandas", "mpmath"]
    def _run(c: str, use: _Dict[str, _Any]) -> _Any:
        r: bool = True
        m: _Callable[[_Any], str] = lambda x: f"\033[{str(x).replace(':', ';')}m"
        def _imp(lib: str, glos: _Any = None, lols: _Any = None, forml: _Any = (), level: int = 0) -> _Union[_Lib, None]:
            if lib in sl:
                return __import__(lib, glos, lols, forml, level)
            elif _vin.minor < 7:
                raise ImportError(f"No module named '{lib}'")
            else:
                raise ModuleNotFoundError(f"No module named '{lib}'")
        use = {**use, "m": m, "clear": lambda: print(_clear)}
        gs: _Dict[str, _Any] = {"__builtins__": {**use, "__import__": _imp}, **var}
        for l, d in enumerate(c.split(";"), start = 1):
            if not d or d.isspace():
                continue
            elif d == "clear" or d == "clear()":
                print(f"{_clear}")
            try:
                b = eval(d.replace("；", ";"), gs, kwargs)
                try:
                    if b[2] == "s" and b[3] == "r":
                        return (b[0], b[1])
                except:
                    pass
            except BaseException:
                print()
                _perr()
                print(f"\n\033[31m错误在第{l}个分号：{d} / Error at {l} semicolon: {d}\033[0m")
    a: str
    su: str
    rt: _Any = None
    var: _Dict[str, _Any] = {}
    def _eq(n: _Any, v: _Any) -> None:
        var[str(n)] = v
    def _et(*args: _Any) -> _Any:
        return (args, "因为exit / Because exit", "s", "r")
    alls: _List[str] = list(__all__)
    alls.pop()
    alls.extend(["help", "print", "clear", "m", "input", "len", "str", "repr", "int", "float", "tuple", "list", "dict", "set", "complex", "None", "bool", "True", "False",
            "min", "max", "round", "range", "eq", "globals", "rm", "__import__ ", "lambda", "切片 / slice", "slice", "iter"
            "{a: b for c in d [if e]（可选 / optional）}", "[a for b in c [if d]（可选 / optional）]", "a if b else c"])
    glo: _Dict[str, _Any] = {i: globals()[i] for i in alls if i in globals()}
    glo = {**glo, **{i: getattr(_built, i) for i in alls if hasattr(_built, i)}}
    glo = {**glo, **{"math": _math, "random": _random, "cmath": _cmath, "time": _time, "datetime": _datetime, "eq": _eq}}
    glo["repr"] = lambda x: print(repr(x))
    glo["globals"] = lambda: print(var)
    glo["rm"] = lambda v: var.pop(v, None)
    if inp is None or isinstance(inp, bool):
        alls.extend(["exit", "info"])
        glo["exit"] = _et
        print(f'BytePrint {__version__} [Python {_ver.replace("main", "main" if __name__ == "__main__" else "byteprint")} on {_plat}]')
        infs: _Callable[[], None] = lambda: print(f"""
        使用“exit”退出，无需括号 / Use 'exit' to exit without parentheses
        只支持： / only supports: {alls}
        以下命令禁止“;” / The following order prohibits ';'
        > info
        “#”就是注释 / '#' is a comment
        报错形式原汁原味 / The original form of error reporting
        byteprint库，Ctrl+C，Ctrl+D，'exit' 都可以退出 / byteprint library, Ctrl+C, Ctrl+D, 'exit' can be exited
        还有更多方式，你慢慢探索 / There are more ways that you can explore slowly
        提示：可以用helps(execute)哦！ / Tip: You can use helps(execute)!
        
        使用 “info” 再现 / Use 'info' reproduction
        为了防止m函数渲染异常，使用“:”代替“;” / In order to prevent m-function rendering exceptions, use ':' instead of ';'
        现在，“；” <{hex(ord('；'))}> 可以替换成“;”了！ / Now, '；'<{hex(ord('；'))}> can be replaced with ';'
        函数“eq”替代赋值 / Function "eq" replaces assignment
        允许的库 / Allowed libraries
        > {sl}
        """)
        bra: str = ""
        if inp is None:
            if __OP__:
                print("跳过（确定为n） / Skip（determine as n）")
            else:
                try:
                    if input("是否需要提示？(y/其他) / Do you need a prompt? (y/Other)：").lower() == "y":
                        infs()
                except (KeyboardInterrupt, EOFError):
                    print("跳过（确定为n） / Skip (determine as n)")
        elif __OO__:
            print("跳过（确认为n） / Skip (determine as n)")
        elif inp:
            infs()
        else:
            print("跳过（确认为n） / Skip (determine as n)")
        while True:
            try:
                c: bool = True
                su = ""
                a = _form(input(f"\033[38;5;129m(byteprint){_ps1}\033[0m"))
                while True:
                    if not a or a.isspace():
                        break
                    elif a == "info" or a == "info()":
                        c = False
                        infs()
                    elif a[-1] == "\\":
                        su += a[:-1]
                        a = _form(input(f"\033[38;5;168m(byteprint){_ps2}\033[0m"))
                        continue
                    break
                if bra:
                    break
                if c:
                    try:
                        rt, bra = _run(su + a.strip(), glo)
                    except:
                        pass
                    if bra:
                        break
            except KeyboardInterrupt:
                bra = "因为ctrl + c / Because ctrl + c"
                break
            except EOFError:
                bra = "因为ctrl + d / Because ctrl + d"
                break
            except _ExitError:
                bra = "因为ctrl + \\ / Because ctrl + \\"
                break
        print("\n已退出byteprint交互式 / Byteprint interactive has been exited\n" + bra)
        return rt
    elif isinstance(inp, str):
        a = _form(inp)
        if not a or a.isspace():
            return
        _run(a, glo)
    else:
        raise TypeError(f"请确保输入的类型为None或者str或者bool，你输入类型的是{type(inp).__name__}\nPlease make sure the type you enter is None or str or bool, and the type you enter is {type(inp).__name__}")

__init__ = (bd, helps, execute, versions, upgrade, install)

if __name__ == "__main__":
    if len(_a[2:]) > 0:
        print("\033[31mERROR: 不支持多个参数，目前只支持一个参数 \n Multiple parameters are not supported, currently only one parameter is supported\033[0m")
        print(f"\033[34m备注：多余的内容如下： / Note: The superfluous content is as follows: \n {_a[2:]}\033[0m")
        _exit(-1)
    try:
        x: _Union[str, None] = _a[1].lower()
    except IndexError:
        x = None
    y: _Union[str, bool, None] = x
    if x == "false":
        y = False
    elif x == "true":
        y = True
    elif x == "none" or x == "null" or x is None:
        y = None
    execute(y)