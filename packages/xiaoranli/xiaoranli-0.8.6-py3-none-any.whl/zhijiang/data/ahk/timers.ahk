#Persistent
; interval sets the time until the first pop-up appears (in milliseconds) 60000 = 1 minute.
interval:=60000

; oldVar sets the default period between pop-ups after the first (in minutes)
oldVar:=20

SetTimer, movement, 1
;MsgBox, First Timer Ran
return

movement:
		MsgBox, 3, GetUpAndMove Timer - %oldVar% minutes, take 20 Seconds relax!, 20
		IfMsgBox, Cancel
			ExitApp

		IfMsgBox, No
			{InputBox, inVar, Interval, Enter a new time (in minutes):,,,,,,,,%oldVar%
			oldVar:=inVar
			}

		interval:=oldVar*60000
		SetTimer, movement, %interval%
		return
