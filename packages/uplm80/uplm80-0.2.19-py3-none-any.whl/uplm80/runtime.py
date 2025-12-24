"""
Runtime library for PL/M-80.

Contains assembly code for runtime support routines that are too complex
to generate inline (multiply, divide, etc.).
"""

# 16-bit unsigned multiply: HL = HL * DE
# Uses BC as temp
RUNTIME_MUL16 = """\
??mul16:
	; 16-bit multiply: HL = HL * DE
	; Input: HL = multiplicand, DE = multiplier
	; Output: HL = product (low 16 bits)
	; Destroys: A, B, C, D, E
	ld	b,h
	ld	c,l		; BC = multiplicand
	ld	hl,0		; HL = result = 0
??mul16l:
	ld	a,e
	or	d		; DE == 0?
	ret	z		; Yes, done
	ld	a,e
	rra			; LSB of multiplier into carry
	jp	nc,??mul16s	; If bit 0 clear, skip add
	add	hl,bc		; HL = HL + BC
??mul16s:
	; Shift multiplicand left
	ld	a,c
	rla
	ld	c,a
	ld	a,b
	rla
	ld	b,a
	; Shift multiplier right
	ld	a,d
	rra
	ld	d,a
	ld	a,e
	rra
	ld	e,a
	jp	??mul16l
"""

# 16-bit unsigned divide: HL = HL / DE, DE = HL % DE
RUNTIME_DIV16 = """\
??div16:
	; 16-bit divide: HL = HL / DE, remainder in BC
	; Input: HL = dividend, DE = divisor
	; Output: HL = quotient, BC = remainder
	; Destroys: A
	ld	a,d
	or	e
	jp	z,??div16z	; Divide by zero
	push	de		; Save divisor
	ld	bc,0		; BC = remainder = 0
	ld	a,16		; 16 bits to process
??div16l:
	push	af		; Save counter
	; Shift HL left, MSB into remainder
	add	hl,hl		; HL = HL * 2, carry = old H bit 7
	ld	a,c
	rla
	ld	c,a		; C = C<<1 + carry (from HL)
	ld	a,b
	rla
	ld	b,a		; B = B<<1 + carry (from C), BC shifted left with HL carry in
	; Shift carry into bit 0 of dividend (will be quotient)
	; Actually we need to track if remainder >= divisor
	; Compare BC with DE
	ld	a,c
	sub	e
	ld	a,b
	sbc	a,d
	jp	c,??div16n	; BC < DE, don't subtract
	; BC >= DE, subtract and set quotient bit
	ld	a,c
	sub	e
	ld	c,a
	ld	a,b
	sbc	a,d
	ld	b,a
	inc	hl		; Set quotient bit
??div16n:
	pop	af		; Restore counter
	dec	a
	jp	nz,??div16l
	pop	de		; Restore divisor (not needed, but balance stack)
	ret
??div16z:
	; Divide by zero - return FFFF
	ld	hl,0ffffh
	ld	bc,0
	ret
"""

# 16-bit modulo: HL = HL MOD DE
RUNTIME_MOD16 = """\
??mod16:
	; 16-bit modulo: HL = HL MOD DE
	; Input: HL = dividend, DE = divisor
	; Output: HL = remainder
	; Destroys: A, B, C
	call	??div16
	ld	h,b
	ld	l,c		; Move remainder to HL
	ret
"""

# 8-bit unsigned multiply: A = A * E
RUNTIME_MUL8 = """\
??mul8:
	; 8-bit multiply: A = A * E (result in HL low byte)
	; Input: A = multiplicand, E = multiplier
	; Output: HL = product (16-bit)
	ld	d,a
	ld	a,0
	ld	hl,0
	ld	b,8
??mul8l:
	ld	a,e
	rra
	ld	e,a
	jp	nc,??mul8s
	ld	a,l
	add	a,d
	ld	l,a
	ld	a,h
	adc	a,0
	ld	h,a
??mul8s:
	ld	a,d
	rla
	ld	d,a
	dec	b
	jp	nz,??mul8l
	ret
"""

# Block move: MOVE(count, source, dest)
RUNTIME_MOVE = """\
??move:
	; Block move: Move count bytes from source to dest
	; Stack: ret, dest, source, count
	; Destroys: A, B, C, D, E, H, L
	pop	hl		; Return address
	pop	de		; Destination
	pop	bc		; Source -> BC temporarily
	ex	(sp),hl		; HL = count, ret addr on stack
	ld	a,h
	or	l
	jp	z,??movex	; Count = 0, done
	push	de		; Save dest
	ld	d,b
	ld	e,c		; DE = source
	pop	bc		; BC = dest
??movel:
	ld	a,(de)		; A = (source)
	ld	(bc),a		; (dest) = A
	inc	de		; source++
	inc	bc		; dest++
	dec	hl		; count--
	ld	a,h
	or	l
	jp	nz,??movel
??movex:
	ret
"""

# 16-bit subtract: HL = HL - DE (Z80 version)
# Uses the Z80-specific SBC HL,DE instruction
RUNTIME_SUBDE = """\
??subde:
	; 16-bit subtract: HL = HL - DE (Z80)
	; Input: HL, DE
	; Output: HL = HL - DE, flags set
	or	a		; Clear carry
	sbc	hl,de
	ret
"""

# Compare strings for equality
RUNTIME_STRCMP = """\
??strcmp:
	; Compare two strings
	; DE = string1, HL = string2, BC = length
	; Returns Z flag set if equal
??strcml:
	ld	a,b
	or	c
	ret	z		; Length = 0, strings equal
	ld	a,(de)		; A = (string1)
	cp	(hl)		; Compare with (string2)
	ret	nz		; Not equal
	inc	de
	inc	hl
	dec	bc
	jp	??strcml
"""

def get_runtime_library(needed: set[str] | None = None) -> str:
    """Get the runtime library assembly code.

    Args:
        needed: Set of routine names that are needed (e.g., {"mul16", "subde"}).
                If None, includes all routines.
    """
    routines = {
        "mul16": RUNTIME_MUL16,
        "div16": RUNTIME_DIV16,
        "mod16": RUNTIME_MOD16,
        "mul8": RUNTIME_MUL8,
        "move": RUNTIME_MOVE,
        "subde": RUNTIME_SUBDE,
    }

    parts = ["; PL/M-80 Runtime Library", ""]

    if needed is None:
        # Include all
        for code in routines.values():
            parts.append(code)
    else:
        # Include only what's needed
        for name, code in routines.items():
            if name in needed:
                parts.append(code)

    return "\n".join(parts)


# Built-in function signatures for reference
BUILTIN_FUNCTIONS = {
    # (name, return_type, param_types, inline_capable)
    "INPUT": ("BYTE", ["BYTE"], True),
    "OUTPUT": ("BYTE", ["BYTE"], True),  # OUTPUT is special - used as lvalue
    "LOW": ("BYTE", ["ADDRESS"], True),
    "HIGH": ("BYTE", ["ADDRESS"], True),
    "DOUBLE": ("ADDRESS", ["BYTE"], True),
    "LENGTH": ("ADDRESS", ["ARRAY"], True),
    "LAST": ("ADDRESS", ["ARRAY"], True),
    "SIZE": ("ADDRESS", ["ARRAY"], True),
    "SHL": ("ADDRESS", ["ADDRESS", "BYTE"], True),
    "SHR": ("ADDRESS", ["ADDRESS", "BYTE"], True),
    "ROL": ("BYTE", ["BYTE", "BYTE"], True),
    "ROR": ("BYTE", ["BYTE", "BYTE"], True),
    "SCL": ("BYTE", ["BYTE", "BYTE"], True),
    "SCR": ("BYTE", ["BYTE", "BYTE"], True),
    "MOVE": (None, ["ADDRESS", "ADDRESS", "ADDRESS"], False),
    "TIME": (None, ["ADDRESS"], True),
    "CARRY": ("BYTE", [], True),
    "SIGN": ("BYTE", [], True),
    "ZERO": ("BYTE", [], True),
    "PARITY": ("BYTE", [], True),
    "DEC": ("BYTE", ["BYTE"], True),
    "STACKPTR": ("ADDRESS", [], True),  # Actually a variable, not function
}
