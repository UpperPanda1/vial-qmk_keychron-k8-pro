---
name: reading-keychron-vial-firmware
description: Use when reading, auditing, porting, building or comparing Keychron keyboard firmware in vial-qmk or QMK forks (K Pro / K Max / Q / V series, CKBT51 Bluetooth, STM32L432), or when touching keymaps/vial, vial.json, customKeycodes, Vial unlock combos, or EEPROM layout of a Keychron board.
---

# Reading Keychron Vial Firmware

## Overview
A Keychron Vial port has three layers: **vial-qmk core** (`quantum/vial*.c`, `quantum/dynamic_keymap.c`), **Keychron board code** (per-board `.c`/`config.h` plus a shared Keychron stack), and the **Vial keymap** (`keymaps/vial/`). Most bugs live at the seams between those layers. Read each seam deliberately, and settle every claim by building or with `nm` rather than reading alone.

## First: identify the code generation
| Clue | Legacy (2022–23 forks) | Modern (Keychron `2025q3` based) |
|---|---|---|
| Shared stack | `keyboards/keychron/bluetooth/` | `keyboards/keychron/common/` + `common/wireless/` |
| BT flag | `BLUETOOTH_ENABLE` (QMK name) or `KC_BLUETOOTH_ENABLE` | `KC_BLUETOOTH_ENABLE` / `LK_WIRELESS_ENABLE` |
| Board config | `config.h` + `rules.mk` | `info.json` / `keyboard.json` (data driven) |
| Custom keycode base | `USER00` / `SAFE_RANGE` (board `.h`) | `QK_KB_0` (`common/keychron_common.h`) |
| EEPROM | `platforms/chibios/eeprom_stm32_l4.c` (FEE), or `wear_leveling` in the Mar‑2023 official fork | `wear_leveling` + `embedded_flash` |
| Vial protocol | `quantum/vial.h` `VIAL_PROTOCOL_VERSION` 5 | 6 |

## Reading order (one board)
1. `keymaps/vial/{rules.mk,config.h,vial.json,keymap.c}`: the Vial contract.
2. Board `rules.mk`/`info.json` → which shared `.mk` it includes, and so which `.c` files compile.
3. Board `.c`: hook functions and `raw_hid_receive_kb`/`via_command_kb`.
4. `quantum/dynamic_keymap.c` top: the EEPROM layout macros (`DYNAMIC_KEYMAP_EEPROM_ADDR` → keymaps → encoders → QMK settings → tap dance → combos → key overrides → macros).
5. `builddefs/common_features.mk`, `VIAL_ENABLE` block: features Vial turns on by default.

## Vial port checklist (get.vial.today/docs)
- `keymaps/vial/rules.mk`: `VIA_ENABLE = yes`, `VIAL_ENABLE = yes`; `VIALRGB_ENABLE = yes` + `"lighting": "vialrgb"` for RGB matrix.
- `keymaps/vial/config.h`: `VIAL_KEYBOARD_UID` (`python3 util/vial_generate_keyboard_uid.py`), and `VIAL_UNLOCK_COMBO_ROWS/COLS` (≥2 keys that exist in every layout). `VIAL_INSECURE = yes` removes the protection on macros, bootloader jump and RESET.
- `vial.json` `customKeycodes` map **by position** to the enum (`QK_KB_0`/`USER00` + i): same order, same count.
- `vial.json` `matrix` equals `MATRIX_ROWS/COLS`; every `"r,c"` exists in the `LAYOUT_*` macro.

## Seam checks (run these, don't eyeball)
```bash
# customKeycodes vs firmware enum (pass -D for flags that gate enum members)
python3 -I .claude/skills/reading-keychron-vial-firmware/audit_custom_keycodes.py \
  <board>/keymaps/vial/vial.json <header-with-enum> -D KC_BLUETOOTH_ENABLE
# Board code must define *_kb hooks; *_user in board code blocks keymaps from adding their own
arm-none-eabi-nm .build/<target>.elf | grep -E ' T (process_record|keyboard_post_init|matrix_scan)_(user|kb)$'
# Is a feature really compiled in?
arm-none-eabi-nm .build/<target>.elf | grep -c -i caps_word
```
`#define` aliases such as `SC_TOGG NEW_SAFE_RANGE` occupy an enum slot without being listed in the enum, so count them by hand.

## Build
Build from the repo root with `make <kb>:vial`, not `qmk compile`. `:via` keymaps cannot build in vial-qmk (`#error` in `quantum/via.c`). Environment setup is in the repo `CLAUDE.md`.

## Common mistakes
- Treating a shifted `DYNAMIC_KEYMAP_EEPROM_ADDR` as harmless: it moves every Vial section, so existing EEPROM data reads back as garbage until reset.
- Trusting "it builds": a short `customKeycodes` list builds fine and mislabels keys.
- Comparing forks by commit message alone: diff the `k8_pro/`, shared-stack and `quantum/` trees, and check `VIAL_PROTOCOL_VERSION`.
- Assuming a variant works because ANSI RGB does: build every `ansi|iso|jis` × `rgb|white` target.
