#pragma once

#define VIAL_KEYBOARD_UID {0x6F, 0x1D, 0xC2, 0xC4, 0xBE, 0x0C, 0x31, 0x92}
#define VIAL_UNLOCK_COMBO_ROWS { 0, 3 }
#define VIAL_UNLOCK_COMBO_COLS { 0, 13 }

/* 10 ms eager per-key debounce (Keychron default is 50 ms from info.json).
 * Stored in EEPROM: takes effect after an EEPROM reset (Fn+J+Z for 3 s). */
#undef DEBOUNCE
#define DEBOUNCE 10

/* Keep the lower brightness steps lit (keychron_common.mk passes 48 via -D) */
#undef RGB_MATRIX_BRIGHTNESS_TURN_OFF_VAL
#define RGB_MATRIX_BRIGHTNESS_TURN_OFF_VAL 32

/* 40 macro slots (default 16); all share the same macro buffer */
#define DYNAMIC_KEYMAP_MACRO_COUNT 40
