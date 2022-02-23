
# parsetab.py
# This file is automatically generated. Do not edit.
# pylint: disable=W,C,R
_tabversion = '3.10'

_lr_method = 'LALR'

_lr_signature = 'ACTION ASSIGN BEGIN COMMENT CSEP ELSE END FALSE FI IF INT LET LPAREN NAME NEWLINE RPAREN SPACE STRING THEN TRUE\n    commandlist : command CSEP commandlist\n                | command NEWLINE\n    \n    command : ACTION SPACE paramlist\n            | ACTION\n    \n    command : NAME ASSIGN param\n    \n    paramlist : param SPACE paramlist\n    \n    paramlist : param\n    \n    param : STRING\n    \n    param : INT\n    \n    param : NAME\n    \n    param : ACTION\n    '
    
_lr_action_items = {'ACTION':([0,5,7,8,17,],[3,3,10,10,10,]),'NAME':([0,5,7,8,17,],[4,4,15,15,15,]),'$end':([1,6,9,],[0,-2,-1,]),'CSEP':([2,3,10,11,12,13,14,15,16,18,],[5,-4,-11,-3,-7,-8,-9,-10,-5,-6,]),'NEWLINE':([2,3,10,11,12,13,14,15,16,18,],[6,-4,-11,-3,-7,-8,-9,-10,-5,-6,]),'SPACE':([3,10,12,13,14,15,],[7,-11,17,-8,-9,-10,]),'ASSIGN':([4,],[8,]),'STRING':([7,8,17,],[13,13,13,]),'INT':([7,8,17,],[14,14,14,]),}

_lr_action = {}
for _k, _v in _lr_action_items.items():
   for _x,_y in zip(_v[0],_v[1]):
      if not _x in _lr_action:  _lr_action[_x] = {}
      _lr_action[_x][_k] = _y
del _lr_action_items

_lr_goto_items = {'commandlist':([0,5,],[1,9,]),'command':([0,5,],[2,2,]),'paramlist':([7,17,],[11,18,]),'param':([7,8,17,],[12,16,12,]),}

_lr_goto = {}
for _k, _v in _lr_goto_items.items():
   for _x, _y in zip(_v[0], _v[1]):
       if not _x in _lr_goto: _lr_goto[_x] = {}
       _lr_goto[_x][_k] = _y
del _lr_goto_items
_lr_productions = [
  ("S' -> commandlist","S'",1,None,None,None),
  ('commandlist -> command CSEP commandlist','commandlist',3,'p_commad_list','parser.py',36),
  ('commandlist -> command NEWLINE','commandlist',2,'p_commad_list','parser.py',37),
  ('command -> ACTION SPACE paramlist','command',3,'p_command_action_param','parser.py',45),
  ('command -> ACTION','command',1,'p_command_action_param','parser.py',46),
  ('command -> NAME ASSIGN param','command',3,'p_command_assign','parser.py',53),
  ('paramlist -> param SPACE paramlist','paramlist',3,'p_paramlist_rec','parser.py',59),
  ('paramlist -> param','paramlist',1,'p_paramlist_base','parser.py',66),
  ('param -> STRING','param',1,'p_param_string','parser.py',72),
  ('param -> INT','param',1,'p_param_int','parser.py',78),
  ('param -> NAME','param',1,'p_param_var','parser.py',84),
  ('param -> ACTION','param',1,'p_param_action','parser.py',90),
]
