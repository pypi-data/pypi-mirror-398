import sys
import re
from inspect import signature, Parameter
from json import loads
from typing import Callable, Union, List, Tuple, Dict, Set, Any, Optional, get_args, get_origin
from types import MappingProxyType
from ast import literal_eval
from .output import prt, NbCmdIO

re_int = re.compile(r"^-?\d+$")
re_float = re.compile(r"^-?\d+\.\d+$")
re_keyword = re.compile(r"^([a-zA-Z_]\w{0,12})=(.*)$")  # 默认参数名不超过13个字符


# 可用函数字典
FUNCTIONS: Dict[object, list[str]] = {
    prt: [
        "setTitle",
        "cls",
        "print",
        "reset",
        "end",
        "loc",
        "col",
        "getLoc",
        "hideCursor",
        "showCursor",
        "bold",
        "dim",
        "italics",
        "underline",
        "blink",
        "invert",
        "strike",
        "fg_black",
        "bg_black",
        "fg_red",
        "bg_red",
        "fg_green",
        "bg_green",
        "fg_yellow",
        "bg_yellow",
        "fg_blue",
        "bg_blue",
        "fg_magenta",
        "bg_magenta",
        "fg_cyan",
        "bg_cyan",
        "fg_grey",
        "bg_grey",
        "fg_rgb",
        "bg_rgb",
        "fg_hex",
        "bg_hex",
        "getSize",
        "alignCenter",
        "alignRight",
        "setOrigin",
        "setOriginTerm",
        "drawNL",
        "drawHLine",
        "drawVLine",
        "drawRect",
        "printLines",
        "drawHGrad",
        "drawVGrad",
        "drawImage",
        "drawImageStr",
        "playGif",
        "playVideo",
        "clearRegion",
        "test",
        "fun",
    ]
}
def param_test(a, i:int, s:str, t:tuple, u:Union[list,tuple,str], *args, n=None, l=[], f=0.1, d={"k":1}, **kwds):
    print(f"a:{a}, i:{i}, s:{s}, t:{t}, u:{u}, args:{args}, n:{n}, l:{l}, f:{f}, d:{d}, kwds:{kwds}")

setattr(prt, 'fun', param_test)

AllFun = []


def get_fun(func: str) -> Callable:
    for obj in FUNCTIONS:
        if func in FUNCTIONS[obj]:
            return getattr(obj, func)
    return lambda *_: None


def list_functions():
    prt.bold().fg_hex("cff")("Functions:\n\n")
    sty_name = prt.bold().fg_hex("6f6").makeStyle()
    sty_args = prt.reset().fg_hex("ccf").makeStyle()
    for obj in FUNCTIONS:
        funs = "\n".join(
            [
                f"    {sty_name}{i}{sty_args}{str(signature(get_fun(i)))}\n"
                for i in FUNCTIONS[obj]
            ]
        )
        prt(funs).drawNL()
    prt("For detailed information about function, type:\n\n")
    prt.bold().fg_yellow("    help <function>\n").end()


def help_function(func=None):
    if func == None:
        yellow = prt.fg_yellow().makeStyle()
        prt.bold().drawHGrad(
            (220, 110, 80),
            (80, 150, 230),
            string=f"  NbCmdIO({prt.__version__}) prt cli.  ",
        ).drawNL()
        prt.bold("Usage")(": prt func1 args func2 args...\n")
        prt("Example:\n\n")
        prt.col(4).fg_blue(f"prt {yellow}loc{prt.RESET} 3 4 {yellow}drawImage{prt.RESET} filepath\n")
        prt.col(4).fg_blue(f'prt {yellow}fg_hex{prt.RESET} "#ccf" {yellow}bold{prt.RESET} "text"\n\n')
        prt.bold().fg_yellow("prt list")(": list all available functions\n")
        prt.bold().fg_yellow("prt help <function>")(
            ": get help information of function\n"
        ).end()
        return
    fun = get_fun(func)
    prt("Function ").bold().fg_yellow(func)(":\n")
    prt.col(5).bold().fg_hex("6f6")(func)(str(signature(fun))).drawNL()
    prt.col(7)(fun.__doc__).drawNL().end()


def parse_type(s: str, target_type: Any) -> Any:
    if s is None or s == 'null':
        return None
    origin = get_origin(target_type)
    args = get_args(target_type)
    # Optional (Union[T, None])
    if origin is Union and type(None) in args:
        actual_type = [t for t in args if t is not type(None)][0]
        return parse_type(s, actual_type)
    
    # Union 
    if origin is Union:
        for possible_type in args:
            try:
                return parse_type(s, possible_type)
            except (ValueError, TypeError):
                continue
        raise ValueError(f"Can not parse '{s}' as {target_type}.")
    
    # List
    if origin is list or target_type is list:
        item_type = args[0] if args else Any
        try:
            lst = literal_eval(s)
            if not isinstance(lst, list):
                raise ValueError(f"'{s}' is not a valid list.")
            return [parse_type(str(item), item_type) for item in lst]
        except (ValueError, SyntaxError):
            raise ValueError(f"Can not parse '{s}' as list")
    
    # Tuple
    if origin is tuple or target_type is tuple:
        try:
            tpl = literal_eval(s)
            if not isinstance(tpl, tuple):
                raise ValueError(f"'{s}' is not a valid tuple.")
            type_args = args
            if not type_args:
                return tpl
            if len(type_args) == 1 and type_args[0] == ():  # empty tuple
                return ()
            if len(tpl) != len(type_args):
                raise ValueError(f"Tuple length not match, expected {len(type_args)} but got {len(tpl)}.")
                
            return tuple(parse_type(str(item), type_args[i]) for i, item in enumerate(tpl))
        except (ValueError, SyntaxError):
            raise ValueError(f"Can not parse '{s}' as tuple.")
    
    # Dict
    if origin is dict or target_type is dict:
        try:
            d = literal_eval(s)
            if not isinstance(d, dict):
                raise ValueError(f"'{s}' is not a valid dict.")
            type_args = args
            if not type_args:  # normal dict
                return d
            key_type, value_type = type_args
            return {
                parse_type(str(k), key_type): parse_type(str(v), value_type)
                for k, v in d.items()
            }
        except (ValueError, SyntaxError):
            raise ValueError(f"Can not parse '{s}' as dict.")
    
    # Set
    if origin is set or target_type is set:
        try:
            item_type = args[0] if args else Any
            set_value = literal_eval(s)
            if not isinstance(set_value, (set, list, tuple)):
                raise ValueError(f"'{s}' is not a valid set.")
            return {parse_type(str(item), item_type) for item in set_value}
        except (ValueError, SyntaxError):
            raise ValueError(f"Can not parse '{s}' as set.")
    
    # base type
    if target_type is str:
        return s
        
    if target_type is int:
        try:
            return int(s)
        except ValueError:
            raise ValueError(f"Can not parse '{s}' as int.")
    
    if target_type is float:
        try:
            return float(s)
        except ValueError:
            raise ValueError(f"Can not parse '{s}' as float.")
    
    if target_type is bool:
        s_lower = s.lower()
        if s_lower in ('true', 't', 'yes', 'y', '1'):
            return True
        elif s_lower in ('false', 'f', 'no', 'n', '0'):
            return False
        raise ValueError(f"Can not parse '{s}' as bool.")
    
    # (Literal)
    if hasattr(target_type, '__args__'):
        if s in target_type.__args__:
            return s
        raise ValueError(f"'{s}' is not valid {target_type}.")
    
    return s

def get_param_type(param:Parameter) -> Any:
    if param.kind == param.VAR_POSITIONAL:
        return param.VAR_POSITIONAL
    if param.kind == param.VAR_KEYWORD:
        return param.VAR_KEYWORD
    if param.annotation != param.empty:
        return param.annotation
    if param.default is not param.empty:
        return type(param.default)
    return Any

def parse_args(args: List[str], params:MappingProxyType):
    """解析参数列表为参数字典
    目前*args和**kwds均解析为字符串，是否依据模式自定义解析有待商榷"""
    POS_ANY, KEY_ANY, KEY = False, False, False
    pos_args, key_args = [], {}
    pi = 0
    keys = list(params.keys())
    kvs = list(params.items())
    tps = [get_param_type(t) for _, t in kvs]
    has_kwds = Parameter.VAR_KEYWORD in tps
    for arg in args:
        m = re_keyword.match(arg)
        if KEY or m:
            KEY = True
            if not m:
                raise ValueError(f"Positional parameter after Keywords parameter: {arg}")
            key, value = m[1], m[2]
            if KEY_ANY:
                key_args[key] = parse_type(value, Any)
                continue
            if key in keys:
                tp = get_param_type(params[key])
                if tp == 0xe: 
                    KEY_ANY, tp = True, Any
                key_args[key] = parse_type(value, tp)
            elif has_kwds:
                key_args[key] = parse_type(value, Any)
            else:
                raise NameError(f"Unknown parameter keyword: {key}")
            continue
        if POS_ANY: tp = Any
        else: 
            tp = tps[pi]
            pi += 1
            if tp == Parameter.VAR_POSITIONAL: 
                POS_ANY, tp = True, Any
        pos_args.append(parse_type(arg, tp))
    return pos_args, key_args


def call_function(func_name: str, args: List[str]) -> None:
    """调用指定函数"""
    func = get_fun(func_name)
    sig = signature(func)
    params = sig.parameters

    pos_args, key_args = parse_args(args, params)
    try:
        res = func(*pos_args, **key_args)
    except KeyboardInterrupt:
        sys.exit(0)
    if func_name == "getSize":
        prt(str(res))


def parse_cmd_argv(argv: list[str]):
    l = len(argv)
    fun = argv[0]
    if fun not in AllFun:
        prt("Unknown function: ").fg_red(fun)
        return []
    args, funs = [], []
    for i in range(1, l):
        if argv[i] in AllFun:
            funs.append((fun, args))
            fun = argv[i]
            args = []
        else:
            args.append(argv[i])
    funs.append((fun, args))
    return funs


def cli(argv=[]):
    """主函数，处理命令行参数"""
    argv = sys.argv[1:] or argv
    if not argv:
        row, col = prt.getSize()
        if row > 13 and col > 42:
            NbCmdIO()
        help_function()
        return
    
    if not sys.stdin.isatty():  # 如果stdin不是终端(说明有管道输入)
        data = sys.stdin.read()
        if isinstance(data, str):
            argv.append(data)

    for obj in FUNCTIONS:
        AllFun.extend(FUNCTIONS[obj])

    if argv[0] in ("-h", "--help", "help", "/h", "/?"):
        if len(argv) > 1:
            if argv[1] in AllFun:
                help_function(argv[1])
            else:
                prt("Unknown function: ").fg_red(argv[1])
        else:
            help_function()
        return
    elif argv[0] in ("-l", "--list", "list"):
        list_functions()
        return

    funs = parse_cmd_argv(argv)
    try:
        for fun, args in funs:
            call_function(fun, args)
    except Exception as e:
        print(f"{fun}: {str(e)}")
        help_function(fun)


if __name__ == "__main__":
    cli()
