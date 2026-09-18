# Firmware slow-controller timeout: hardware test plan

Verifies commit `0559258`, which fixed the unit of `maxExtraDelayPress` in
`arduino/MiSTer_USB_Latency_Test_Lemonici/MiSTer_USB_Latency_Test_Lemonici.ino`.
Nothing here has been run on hardware yet.

## What changed

The wait loop compared `maxExtraDelayPress` (documented as 200 ms) against
`micros()`, so the firmware waited 200 us, not 200 ms, for a late response
before starting the next press. The fix scales the comparison to microseconds.

Consequence of the bug: when a controller answers later than the press cycle
(`2 * delayPress` = 32 ms), the pending interrupt lands after `startMicros` has
already been reset for the next press, and the reading is written against the
wrong start time. Controllers that answer within 32 ms set `pressRegistered`
before the wait loop is reached, so the timeout branch never runs for them and
their results are unaffected either way.

## Equipment

- The latency rig: Pro Micro on the test hat, DE10-nano running
  `test_core/NES_Lag_Tester.rbf`, button line soldered to the device under test.
- A controller whose average exceeds the 32 ms press cycle. From the published
  catalog, candidates are Microsoft Wireless Controller (max 87.8 ms), Hori
  Fighting Commander Wii Classic (max 103.7 ms), Nintendo Wii U Pro (avg
  35.3 ms), Microsoft SideWinder Game Pad USB (avg 40.7 ms).
- A fast wired controller as a no-change check. Any Diamond or Platinum tier
  device works; iBuffalo Classic sits at 0.69 ms.

## Procedure

1. Record the current sketch identity before flashing:
   `arduino-cli compile --fqbn arduino:avr:leonardo arduino/MiSTer_USB_Latency_Test_Lemonici`
   The fixed sketch builds to 7246 bytes; the hex md5 is `ef99cfa7...`, where
   the pre-fix hex was `22b05169...`.
2. Confirm the button under test is mapped in the NES core before capturing.
3. Flash the fixed firmware and capture at least 2000 samples from the slow
   controller. Save to `captures/<device>.csv` only if the result is meant to
   be published; otherwise keep it out of the tree.
4. Capture at least 2000 samples from the fast controller.
5. Negative control: flash the pre-fix sketch (`git show 0559258^:arduino/...`)
   and repeat step 3 on the same slow controller, then reflash the fixed build.

## Pass criteria

- Slow controller, fixed firmware: a single cluster around the expected average,
  no readings below 1 ms, and no maxima near 233 ms.
- Slow controller, pre-fix firmware: the bad signature returns, meaning a mix of
  sub-1 ms readings and very large maxima. Without this control a quiet rig or an
  unmapped button would look like a pass.
- Fast controller: average and standard deviation match the published values for
  that device within normal run-to-run spread. The fix must not move these.

## Recording the outcome

Note the controller, sample counts and the three observed distributions in the
commit or issue that closes this out, and state plainly that the result is a
bench measurement on one rig rather than a qualification of every build.
