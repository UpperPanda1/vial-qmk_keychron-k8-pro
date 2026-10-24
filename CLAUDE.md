# CLAUDE.md: Keychron K8 Pro Vial firmware

This repo is a vial-qmk fork for the **Keychron K8 Pro** (STM32L432, CKBT51 Bluetooth, TKL).
The work happens in `keyboards/keychron/k8_pro/` and the shared legacy stack in `keyboards/keychron/bluetooth/`.
Develop on branch `bluetooth_playground`.

**Before reading or changing Keychron/Vial code, load the project skill `reading-keychron-vial-firmware`**
(`.claude/skills/reading-keychron-vial-firmware/`). It has the reading order, Vial checklist and seam checks,
and `audit_custom_keycodes.py`.

## Lineage (verified with git, 2026-10-24)
This repo is byte-identical to **Vil4/vial-qmk_keychron-k8-pro@`dc042491`** in `keyboards/keychron/`.
- lokher (Keychron) Aug 2022 K8 Pro + `bluetooth/` stack (last: `5c61a8b0` 2022-08-10)
- \+ vial-qmk `vial` branch @ `d835ad15` (2022-08-13), merged by solid-pixel (`eb2e459d`, 2022-08-15)
- \+ solid-pixel Vial keymap `ansi/rgb/keymaps/vial` (Aug 2022)
- \+ Vil4 `a8ed9cd1` (EEPROM `+1` offset, "fixes tap dance/combos/mouse") and `dc042491` (more RGB effects), Mar 2023

It does **not** contain Keychron's 2023-03-09 rework of `Keychron/vial-qmk` `bluetooth_playground`. That branch was rebuilt,
so lokher's 2022 commits are no longer on its HEAD.

## Build (verified in this container)
```bash
apt-get install -y gcc-arm-none-eabi binutils-arm-none-eabi libnewlib-arm-none-eabi dfu-util
python3 -m venv <scratch>/venv && <scratch>/venv/bin/pip install -U pip setuptools wheel qmk -r requirements.txt
git submodule update --init --filter=blob:none lib/chibios lib/chibios-contrib lib/printf lib/lufa lib/vusb
PATH=<scratch>/venv/bin:$PATH make keychron/k8_pro/ansi/rgb:vial SKIP_GIT=yes -j8   # -> .build/*.bin
```
- System pip fails to build `halo` (Debian setuptools `install_layout` bug), so use a venv.
- Without `dfu-util` the `.bin` is still produced but make exits 127 at `dfu-suffix`.
- Use `make`, not `qmk compile`. `:via` keymaps cannot build in vial-qmk (`#error` in `quantum/via.c`).

| Target | Result | Notes |
|---|---|---|
| `ansi/rgb:vial` | ✅ builds, no warnings | 72.6 KB of 256 KB flash |
| `ansi/rgb:default` | ✅ | |
| `ansi/rgb:via` | ❌ | `VIAL_ENABLE=yes` in `keymaps/via/rules.mk` but no `vial.json` (solid-pixel leftover) |
| `ansi/white:*`, `iso/white:*` | ❌ | `bluetooth/factory_test.c:184` missing `;` (LED-matrix only) |
| ISO/JIS/White Vial keymaps | — | do not exist; only `ansi/rgb/keymaps/vial` |

## Hardware facts (from `k8_pro/config.h`)
6×17 matrix, ROW2COL; rows `B5 B4 B3 A15 A14 A13`; columns via a 74HC595 shift register in `matrix.c` (`CUSTOM_MATRIX = lite`).
DIP switch `A8` picks the Mac (layer 0) or Win (layer 2) default layer. Mode switch `A10`, CKBT51 int `A5`/`A6`, USB sense `B1`.
LED driver CKLED2001 ×2 (RGB: 47+40 LEDs; White: 87). Layers: `MAC_BASE, MAC_FN, WIN_BASE, WIN_FN`.
Factory/EEPROM reset: hold **Fn+J+Z for 3 s** (`factory_test.c` → `eeconfig_init()`), or Bootmagic (hold Esc while plugging in).

## Current fork: audit findings
Evidence: build, `arm-none-eabi-nm` on the ELF, and source.
1. **Hooks hijacked (proven).** `k8_pro.c` defines `process_record_user`, `keyboard_post_init_user` and `matrix_scan_user`.
   A keymap defining any of them fails to link ("multiple definition … k8_pro.c:70").
   Fix: rename to `_kb` and call the `_user` hook, as the official 2023 and tymon forks do.
2. **`VIAL_INSECURE = yes`, no unlock combo.** The Vial docs advise against this: it unprotects macro editing,
   bootloader jump and RESET assignment. Official/tymon use `VIAL_UNLOCK_COMBO_ROWS {0,3}` / `COLS {0,13}` (Esc+Enter).
3. **EEPROM `+1` hack** (`config.h`: `DYNAMIC_KEYMAP_EEPROM_ADDR … + 1`) moves the keymap base from 39 to 40, so
   every Vial section after it moves too. The root cause is **unverified**: the L4 FEE driver handles odd addresses in a code read.
   Both newer forks replace that driver with QMK `wear_leveling` and need no offset.
   Changing the offset scrambles stored settings until an EEPROM reset.
4. **Caps Word is not compiled** (0 symbols in the ELF). `DOUBLE_TAP_SHIFT_TURNS_ON_CAPS_WORD` in `ansi/rgb/config.h` does nothing
   because `CAPS_WORD_ENABLE` is commented out in the vial `rules.mk`.
5. Compiled in and working at build level: tap dance, combos, key overrides, QMK Settings, VialRGB (`nm`).
6. `customKeycodes` match the enum (15/15, audit script). The `shortName`s are long (docs say keep them short).
7. Old base: Vial protocol **5**, QMK mid-2022. `BT_HST1-3` act in USB mode too (official adds a transport check).
   The BT stack lacks the official 2023 RTC‑timer fix and other `bluetooth/` changes (about 1000 diff lines).

## Other forks (cloned and diffed 2026-10-24)
| | Current (Vil4) | Official Keychron/vial-qmk `bluetooth_playground` (2023-03-09) | tymon3310/vial-qmk `vial-updated-keychron` (2026-09-12) |
|---|---|---|---|
| Base | vial-qmk 2022-08, Vial proto 5 | rebuilt on vial-qmk 2023-03, Vial proto 5 | current vial-qmk + Keychron `qmk_firmware` **2025q3**, Vial proto **6** |
| Keychron stack | `bluetooth/` 2022 | `bluetooth/` 2023 (+rtc_timer, gpio_uart) | `common/` + `common/wireless/` (shared by 98 boards) |
| Vial keymaps | ansi/rgb | ansi/rgb, ansi/white | **all 6**: ansi/iso/jis × rgb/white |
| Vial-only features | TD/combos/KO/QMK settings | — | + Caps Word, Alt Repeat Key, Layer Lock, chordal hold |
| Macro buffer | 676 B | — | 1098 B |
| Hooks | `_user` hijacked | `_kb` chain | `_kb` chain (`keychron_task_kb`) |
| EEPROM | L4 FEE + `+1` hack | wear_leveling 2 KB | wear_leveling 3 KB |
| Security | insecure | unlock combo | unlock combo |
| RGB effects enabled | 43 (Vil4) | 21 | 21 (Keychron default set) |
| Extras | — | — | Keychron Launcher raw HID (coexists with Vial `0xFE`), snap click, dynamic debounce, report rate, language, adaptive NKRO |
| Builds here | ansi/rgb:vial ✅ | not built | all 6 `:vial` ✅ (with patch) |

- **Does the current fork just build on the others?** It builds on the *2022* Keychron code plus solid-pixel. It is *not* built on
  the 2023 official rework, and it is unrelated to tymon's lineage. Its only unique content is Vil4's EEPROM offset and the bigger RGB effect list.
## tymon K8 Pro: second-pass audit (2026-10-24, user owns **ANSI RGB**)
tymon's K8 Pro board files (`info.json`, `keyboard.json`, `config.h`, `rgb.c`, `k8_pro.c`, keymaps) are **identical to Keychron
`qmk_firmware` 2025q3**; only the six `keymaps/vial/` folders are tymon's. tymon also edits `common/` (raw HID, weak `_kb` hooks,
VialRGB Keychron effects, wireless XOR for LKBT51; the XOR path is not compiled for K8 Pro).

**Vial features in `ansi/rgb:vial`** (ELF symbols plus compile-time probe): tap dance 16, combos 16, key overrides 16,
Alt Repeat Key 16, macros 16 (1098-byte buffer), 4 layers, QMK Settings, Auto Shift, Caps Word, Layer Lock, VialRGB, NKRO,
mouse keys. EEPROM map: core 0–36 · Keychron data 37–537 · VIA header 538–541 · keymaps from 542 (no overlap; Keychron's
hardcoded base 37 equals `EECONFIG_BASE_SIZE`).

| # | Finding (ANSI RGB unless noted) | Severity | Status |
|---|---|---|---|
| 1 | `vial.json` `customKeycodes` 13 vs enum 15 (`MCtl`/`LPad` missing). vial-gui maps `USERxx = QK_KB(0x7E00)+i` (`keycodes.py:833`), so labels from "Task" on are off by two. White variants: 13 vs 17 (`BL_SPI`/`BL_SPD`). All six variants affected | High | **Fixed:** `patches/tymon3310-vial-qmk/0001-*.patch`. Audit 15/15 and 17/17, all 6 `:vial` build with 0 warnings, decoded embedded definition checked |
| 2 | Raw HID `0xAA` (CKBT51 DFU) and `0xAB` (factory test) reply twice: the handler sends, then `via.c:455` echoes. Upstream avoided this with `via_command_kb()`, which vial-qmk never calls | Low–Med | Open (code trace only). Fix idea: suppress the next `via_raw_hid_send` after a self-sending handler |
| 3 | VialRGB Keychron effects: table hardcodes `{48,24},{49,25}`, but the enum gives `PER_KEY_RGB=45`, `MIXED_RGB=46` (compiler probe). vial-gui only knows IDs ≤ 44, so Per-Key/Mixed RGB can't be reached from Vial, and the HSV exemption at `vialrgb.c:175` never fires. QMK side 24/25 is correct for this board | Low | Open |
| 4 | Debounce `"debounce": 50` = **50 ms, sym_eager_per_key** (Keychron default on most boards; release held ≤ 50 ms). Can only be changed through Keychron raw HID (`DEBOUNCE_SET`), not Vial | Behavior | **Set to 10 ms** in ANSI RGB vial `config.h` (patch 0002, `#undef` first because `info_config.h` is included earlier). Stored in EEPROM, so it applies after Fn+J+Z. Disassembly: `debounce_set(4, 10, …)` |
| 8 | `RGB_MATRIX_BRIGHTNESS_TURN_OFF_VAL=48` (`-D` in `keychron_common.mk`; `VAL_STEP` 16) turns brightness ≤ 48 off | Behavior | **Set to 32** (= Vil4) in patch 0002, so the lowest lit step is 48. Disassembly: `cmp r3, #32` |
| 5 | `SC_TOGG` (tymon `#define … NEW_SAFE_RANGE`) has **no handler** anywhere: do not list it in `vial.json` | Trivial | Leave unlisted |
| 6 | `"menus"`/`"keycodes"` in `vial.json` are ignored by vial-gui (it reads only `lighting`, `customKeycodes`, …) | Trivial | Harmless |
| 7 | `-DVIA_INSECURE` from `keychron_common.mk` has no code consumer. Vial lock intact (`vial_unlocked` in .bss = 0) | None | OK |

Verified OK: layouts match `info.json` for all six variants (87/88/91 keys, x/w), UIDs unique, unlock combos valid
(ANSI Esc+Enter `[3,13]`; ISO/JIS `[2,13]`), `_user` hooks weak, Vial keymap = Keychron `keychron` keymap.

**Vil4 features missing from tymon:** 22 RGB effects (ALPHAS_MODS, BAND_SAT/VAL, BAND_PINWHEEL_SAT/VAL, BAND_SPIRAL_SAT,
GRADIENT_UP_DOWN/LEFT_RIGHT, HUE_BREATHING/PENDULUM/WAVE, MULTISPLASH, PIXEL_FLOW/FRACTAL, RAINBOW_PINWHEELS, RAINDROPS,
SOLID_MULTISPLASH, SOLID_REACTIVE, SOLID_REACTIVE_CROSS/MULTICROSS/NEXUS/WIDE); `NK_TOGG` on Fn+N;
5 ms debounce; no unlock needed (`VIAL_INSECURE`); LED turn-off threshold 32 (patch 0002 restores 32).
The double-tap-Shift Caps Word define is dead in Vil4 anyway. Effects can be added back via `keyboard.json` `rgb_matrix.animations`.

**NKRO:** Vil4 has standard QMK NKRO with no `FORCE_NKRO`, so it starts in 6KRO and `NK_TOGG` (Fn+N) switches modes.
tymon has `-DAPDAPTIVE_NKRO_ENABLE`: keys fill the 6KRO report, and only the 7th+ key goes to the NKRO report
(`report.c:192`). `keymap_config.nkro` is ignored on USB (`action_util.c:318`), so `NK_TOGG` is effectively a no-op. Don't add it.

**Macros:** count = `DYNAMIC_KEYMAP_MACRO_COUNT` (default 16, `quantum/dynamic_keymap.h:30`, `#ifndef`-guarded; neither fork sets it).
All macros share one buffer (tymon 1098 B, Vil4 676 B); count does not change the EEPROM layout. Hard limit 128
(`QK_MACRO` 0x7700–0x777F). Defining it twice fails the build (`-Werror` "redefined"). `40` is set in patch 0002.

## Recommendation
For ANSI RGB: use tymon plus `patches/tymon3310-vial-qmk/0001` (keycodes) and `0002` (10 ms debounce, brightness 32),
applied in order with `git am`. 0002 also sets `DYNAMIC_KEYMAP_MACRO_COUNT 40` (verified: firmware reports 40, buffer 1098 B). Optionally re-enable the Vil4 effects you want.
Keymap overrides of values that arrive via `info_config.h` or `-D` need `#undef` first (`-Werror`).
If you stay on the current base: fix finding 1, add an unlock combo, fix `factory_test.c:184`, and decide on Caps Word.
Either way, after flashing a firmware with a different EEPROM layout, do an EEPROM reset.
**Not yet tested on hardware:** Bluetooth, battery, tap dance persistence, the `+1` root cause, raw-HID double reply impact.

## Conventions
- Smallest correct change and match the Keychron code style. Never commit `.build/`.
- Check every claim with a build or `nm`. Build all affected variants, not just ansi/rgb.
- New Vial keymap: `keymaps/vial/{rules.mk,config.h,vial.json,keymap.c}`, a fresh UID from `util/vial_generate_keyboard_uid.py`,
  and run the custom keycode audit.
