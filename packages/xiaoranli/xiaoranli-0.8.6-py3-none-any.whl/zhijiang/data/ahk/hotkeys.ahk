^SPACE:: Winset, Alwaysontop, , A

F10::WinGet,ID,ID, A

F11::
    WinSet, Style, ^0x40000 , ah_id %ID% ; ReSize
    WinSet, Style, ^0xC00000, ahk_id %ID% ; Caption
    WinSet, Style, ^0x800000, ahk_id %ID% ; Border
Return
