"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import wx
import logging
from pathlib import Path

from ..PyTranslate import _
from . import Parser, Expression

class Calculator(wx.Frame):
    """
    Calculator/Array creator

    With this calculator, you can create arrays and perform operations on them.
    It is possible because the operations are parsed and evaluated by the math_parser module
    and mathematic operators are allowed directly on WolfArrays.

    """

    def __init__(self, mapviewer=None):

        from ..PyDraw import WolfMapViewer, draw_type, WolfArray

        super(Calculator, self).__init__(None, title='Calculator', size=(500, 300))

        self._memory = {} # dictionary containing the arrays and local stored variables

        self._parser = Parser()
        self._parsed_command:Expression = None

        self._mapviewer:WolfMapViewer = mapviewer
        self._last_command = None

        keys = '()C<789/456*123-.0=+'
        self._btns:list[list[wx.Button]] = [[wx.Button(self, label=c) for c in keys[i:i+4]] for i in range(0,20,4)]

        self._disp = wx.TextCtrl(self, style=wx.TE_RIGHT|wx.TE_RICH2|wx.TE_MULTILINE)

        self._comment = wx.TextCtrl(self, style=wx.TE_RIGHT|wx.TE_RICH2|wx.TE_MULTILINE)
        self._comment.SetToolTip(_('Comment block'))

        self._memory_txtctrl   = wx.TextCtrl(self, style=wx.TE_RIGHT|wx.TE_RICH2|wx.TE_MULTILINE)
        self._memory_txtctrl.SetToolTip(_('Memory positions (contains the ids of the arrays and local variables)'))

        self.btn_reset_memory = wx.Button(self, label='Reset Memory')

        self.Bind(wx.EVT_BUTTON, lambda v: self.bt_press(v.EventObject.Label))

        self._btns[-1][-2].SetDefault()

        self.Bind(wx.EVT_CHAR_HOOK, self.char_press)
        self.btn_reset_memory.Bind(wx.EVT_BUTTON, self.memory_clear_event)

        self.SetSizer(self.pack([self._disp] + [self.pack(x) for x in self._btns] + [self.pack([self._comment, self.btn_reset_memory, self._memory_txtctrl])], orient=wx.VERTICAL))

        self._disp.SetFocus()

        icon = wx.Icon()
        icon_path = Path(__file__).parent.parent / "apps/wolf.ico"
        icon.CopyFromBitmap(wx.Bitmap(str(icon_path), wx.BITMAP_TYPE_ANY))
        self.SetIcon(icon)

        self.memory_clear()
        self.Show()

    def pack(self, items, orient=wx.HORIZONTAL):
        """ Pack items in a sizer """
        sizer = wx.BoxSizer(orient)
        sizer.AddMany((i, 1, wx.EXPAND|wx.ALL, 0) for i in items)
        return sizer

    @property
    def command(self) -> str:
        return self._disp.Value

    @command.setter
    def command(self, value):
        self._disp.Value = str(value)
        self._disp.SetInsertionPointEnd()

    @property
    def comment(self) -> str:
        return self._comment.Value

    @comment.setter
    def comment(self, value):
        self._comment.Value += str(value)

    def reset_comment(self):
        self._comment.Value = ''

    @property
    def memory_txt(self):
        return self._memory_txtctrl.Value

    @memory_txt.setter
    def memory_txt(self, value):
        self._memory_txtctrl.Value += str(value)+'\n'

    def reset_memory(self):
        self._memory_txtctrl.Value = ''

    def memory_clear(self):
        self.reset_memory()
        self._memory.clear()

        if self._mapviewer is not None:
            from ..PyDraw import draw_type
            ids = self._mapviewer.get_list_keys(drawing_type=draw_type.ARRAYS, checked_state=None)
            for id in ids:
                self.memory_txt = id

    def memory_clear_event(self, e):
        self.memory_clear()

    def check_command(self) -> bool:
        """ Check if the command is valid """

        from ..PyDraw import draw_type

        if '\n' in self.command:
            self.evaluate_multilines()
            return False
        else:

            self._parsed_command = self._parser.parse(self.command)

            symbols = self._parsed_command.symbols()
            variables = self._parsed_command.variables()
            functions = self._parsed_command.functions

            if self._mapviewer is not None:
                id_arrays = self._mapviewer.get_list_keys(drawing_type=draw_type.ARRAYS,
                                                       checked_state=None)

                for id_array in id_arrays:
                    self._memory[id_array] = self._mapviewer.get_obj_from_id(id_array, drawing_type=draw_type.ARRAYS)

            if len(variables) > 0:
                for var in variables:
                    if var not in self._memory:
                        self.comment = f'Variable {var} not defined'
                        return False

            return True

    def evaluate_multilines(self):
        """ Evaluate multiline commands """

        self._last_command = self.command

        commands = self.command.split('\n')

        ret = []
        for command in commands:
            if command == '': continue
            self.command = command
            ret.append(str(self.evaluate(mem_last_command=False)))

        self.command = '\n'.join(ret)

    def evaluate(self, mem_last_command=True):
        """ Evaluate the command """

        from ..PyDraw import WolfArray, draw_type

        if mem_last_command:
            self._last_command = self.command

        ret = self.check_command()

        if ret:
            args = {var:self._memory[var] for var in self._parsed_command.variables()}
            res = self._parsed_command.evaluate(args)

            if isinstance(res, dict):

                comment = 'Storing\n'

                for key, value in res.items():
                    self._memory[key] = value

                    self.comment += f'{key} = {value}\n'
                    self.memory_txt  += key

                self.command = ''

            elif isinstance(res, str|int|float):
                self.command = res

            elif isinstance(res, WolfArray):

                ids = self._mapviewer.get_list_keys(drawing_type=draw_type.ARRAYS, checked_state=None)
                id = self.command
                while id in ids:
                    id += '_'

                res.set_nullvalue_in_mask()
                self._mapviewer.add_object('array', newobj=res, id = id)
                self.command = ''

            return res

    def char_press(self, e:wx.KeyEvent):
        """ Handle key press """

        egal = '='
        egal_code = [ord(egal)]

        unicodekey = e.GetUnicodeKey()
        key = e.GetKeyCode()

        ctrl = e.ControlDown()
        alt  = e.AltDown()
        shift= e.ShiftDown()

        if unicodekey in egal_code:
            if not shift :
                self.evaluate()
                return

        e.Skip()

    def bt_press(self, key):
        """ Handle button press  """
        if   key == 'C': self._disp.Value = ''
        elif key == '<': self.command =self._last_command
        elif key == '=': self.evaluate()
        else           : self._disp.Value += key
