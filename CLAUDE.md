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
| Hooks | `_user` hijacked | `_kb` chain | `_kb` chain (`keychron_task_kb`) |
| EEPROM | L4 FEE + `+1` hack | wear_leveling 2 KB | wear_leveling 3 KB |
| Security | insecure | unlock combo | unlock combo |
| RGB effects enabled | 43 (Vil4) | 21 | 21 (Keychron default set) |
| Extras | — | — | Keychron Launcher raw HID (coexists with Vial `0xFE`), snap click, dynamic debounce, report rate, language, adaptive NKRO |
| Builds here | ansi/rgb:vial ✅ | not built | ansi/rgb, ansi/white, iso/rgb `:vial` ✅ |

- **Does the current fork just build on the others?** It builds on the *2022* Keychron code plus solid-pixel. It is *not* built on
  the 2023 official rework, and it is unrelated to tymon's lineage. Its only unique content is Vil4's EEPROM offset and the bigger RGB effect list.
- **tymon bug (proven by audit script and Vial docs):** `k8_pro/*/keymaps/vial/vial.json` lists 13 `customKeycodes`, but the enum
  has 15 (`MCtl`, `LPad` missing). From "Task" onward every Vial label is off by two (GUI "BTH1" = `KC_WIN_CORTANA`).
  `SC_TOGG` (slot 15) is also unlisted. tymon's K8 Max JSON is correct (16/16).

## Recommendation
Move to the tymon base for full features, and fix its K8 Pro `vial.json` first (add `MCtl`, `LPad` after `RCmd`;
optionally Snap Click toggle). If you stay on the current base: fix finding 1, add an unlock combo, fix `factory_test.c:184`, and
decide on Caps Word. Either way, after flashing a firmware with a different EEPROM layout, do an EEPROM reset.
**Not yet tested on hardware:** Bluetooth, battery, tap dance persistence, the `+1` root cause.

## Conventions
- Smallest correct change and match the Keychron code style. Never commit `.build/`.
- Check every claim with a build or `nm`. Build all affected variants, not just ansi/rgb.
- New Vial keymap: `keymaps/vial/{rules.mk,config.h,vial.json,keymap.c}`, a fresh UID from `util/vial_generate_keyboard_uid.py`,
  and run the custom keycode audit.
