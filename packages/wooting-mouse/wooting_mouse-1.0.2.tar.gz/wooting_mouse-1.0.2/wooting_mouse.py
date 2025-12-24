"""
Script to use Wooting Gamepad as Mouse
"""
import asyncio
import collections
import signal
import sys
import math
import colorsys
import time
import os
import selectors

import libwootility.device_linux as libwootility_device
import libwootility.libwootility_feature
import libwootility.libwootility_report

import evdev
import pyudev

import hsluv


class Mouse:
    """
    Virtual Mouse
    """

    def __init__(self, state, device):
        self.ui_mouse = evdev.UInput(
            evdev.util.find_ecodes_by_regex(
                r"(REL_X|REL_Y|REL_WHEEL|REL_WHEEL_HI_RES|REL_HWHEEL|"
                r"REL_HWHEEL_HI_RES|BTN_RIGHT|BTN_MIDDLE|BTN_LEFT|"
                r"KEY_CAPSLOCK|KEY_LEFTCTRL|KEY_LEFTALT|BTN_BACK|BTN_FORWARD)$"
            ),
            name="Wooting Virtual Mouse for Gamepad",
        )
        self.state = state
        self.device = device
        self.enabled = False
        self.enable_event = asyncio.Event()
        self.speed = 10
        self.sleep = 0.05
        self.config_mtime = None
        self.config_reload = 1 / self.sleep

    def handle(self, from_event, to_event):
        """
        Handle event, translate analog keypress to relative movement
        """
        value = self.state[evdev.ecodes.ecodes["EV_ABS"]][from_event]

        self.ui_mouse.write(
            evdev.ecodes.ecodes["EV_REL"],
            to_event,
            int(math.tan(value * (math.pi / 2) / 34000) * self.speed),
        )

    def write(self, typ: int, code: int, value: int) -> None:
        """
        Write event
        """
        self.ui_mouse.write(typ, code, value)

    async def run(self) -> None:
        """
        Main loop
        """
        counter = 0
        while True:
            if self.enabled:
                await asyncio.sleep(self.sleep)
            else:
                await self.enable_event.wait()

            if counter % self.config_reload == 0:
                try:
                    new_mtime = os.lstat('/etc/wooting-mouse.conf').st_mtime
                except FileNotFoundError:
                    pass
                else:
                    if new_mtime != self.config_mtime:
                        with open('/etc/wooting-mouse.conf', encoding='utf8') as f:
                            speed, sleep = f.read().split('\n')[:2]
                        self.speed = int(speed)
                        self.sleep = float(sleep)
                        self.config_reload = 1 / self.sleep
                        self.config_mtime = new_mtime

            self.handle(evdev.ecodes.ecodes["ABS_X"], evdev.ecodes.ecodes["REL_X"])
            self.handle(evdev.ecodes.ecodes["ABS_Y"], evdev.ecodes.ecodes["REL_Y"])
            self.handle(
                evdev.ecodes.ecodes["ABS_RX"], evdev.ecodes.ecodes["REL_HWHEEL_HI_RES"]
            )
            self.handle(
                evdev.ecodes.ecodes["ABS_RY"], evdev.ecodes.ecodes["REL_WHEEL_HI_RES"]
            )

            self.ui_mouse.syn()
            counter += 1

    def enable(self):
        """
        Enable mouse
        """
        self.enabled = True
        self.enable_event.set()

    def disable(self):
        """
        Disable mouse
        """
        self.device.send_feature(libwootility.libwootility_feature.activate_profile(0))
        self.enabled = False
        self.enable_event.clear()


async def gamepad(
    wooting_gamepad,
    state,
    mouse,
    rgb_lighting,
    ev_key_mouse_write_map,
    ev_abs_mouse_write_map,
):
    """
    Watch Gamepad events
    """
    ev_key = evdev.ecodes.ecodes["EV_KEY"]
    ev_abs = evdev.ecodes.ecodes["EV_ABS"]

    pressed_keys = {
        evdev.ecodes.ecodes["BTN_BACK"]: False,
        evdev.ecodes.ecodes["BTN_FORWARD"]: False,
    }

    async for event in wooting_gamepad.async_read_loop():
        if event.value > 0:
            mouse.enable()
            rgb_lighting.mouse()
        state[event.type][event.code] = event.value

        if event.type == ev_key and event.code in ev_key_mouse_write_map:
            mouse.write(
                ev_key,
                evdev.ecodes.ecodes[ev_key_mouse_write_map[event.code]],
                event.value,
            )
        elif (
            event.type == ev_key
            and event.code == evdev.ecodes.ecodes["BTN_START"]
            and event.value > 0
        ):
            mouse.disable()
            time.sleep(0.1)
            rgb_lighting.time_of_day()
        elif event.type == ev_abs and event.code in ev_abs_mouse_write_map:
            if event.value == 0:
                for pressed_key, pressed in pressed_keys.items():
                    if pressed:
                        mouse.write(ev_key, pressed_key, 0)
                        pressed_keys[pressed_key] = False
            else:
                if event.value < 0:
                    pressed_key = evdev.ecodes.ecodes[
                        ev_abs_mouse_write_map[event.code][0]
                    ]
                else:
                    pressed_key = evdev.ecodes.ecodes[
                        ev_abs_mouse_write_map[event.code][1]
                    ]
                mouse.write(ev_key, pressed_key, 1)
                pressed_keys[pressed_key] = True


def time_of_day(device):
    """
    Color keyboard according to time of day
    """
    values = []
    localtime = time.localtime()
    hue = (localtime.tm_hour * 60 + localtime.tm_min) / (24 * 60)
    rgb = colorsys.hls_to_rgb(hue, 0.5, 1)
    hslv = hsluv.rgb_to_hsluv(rgb)

    for i in range(21):
        if i < 10:
            rgbv = hsluv.hsluv_to_rgb((hslv[0] + 0, hslv[1], hslv[2]))
        elif i < 12:
            rgbv = hsluv.hsluv_to_rgb((hslv[0] + 10, hslv[1], hslv[2]))
        elif i < 14:
            rgbv = hsluv.hsluv_to_rgb((hslv[0] + 20, hslv[1], hslv[2]))

        values.append(
            (int(rgbv[0] * 255), int(rgbv[1] * 255), int(rgbv[2] * 255)),
        )

    payload = libwootility.libwootility_report.set_upper_rows_rgb(values, values, values)
    device.send_buffer(payload)

    payload = libwootility.libwootility_report.set_lower_rows_rgb(values, values, values)
    device.send_buffer(payload)


class RGBLighting:
    """
    RGB Lighting
    """

    def __init__(self, device):
        self.device = device
        self.time_of_day()
        self.do_time_of_day = True

    def time_of_day(self):
        """
        Color keyboard according to time of day
        """
        self.do_time_of_day = True
        time_of_day(self.device)

    def mouse(self):
        """
        Mouse mode (disable time of day)
        """
        self.do_time_of_day = False

    async def run(self) -> None:
        """
        Main loop
        """
        while 1:
            await asyncio.sleep(60)
            if self.do_time_of_day:
                self.time_of_day()


def main():
    """
    Main function
    """
    context = pyudev.Context()
    # run: udevadm info -t
    # search for "event-joystick"
    # Use the child of this device (event*) (P:):
    # /devices/pci0000:00/0000:00:14.0/usb2/2-5/2-5.2/2-5.2:1.0/input/input33/event3
    udev = pyudev.Devices.from_path(context, sys.argv[1])
    wooting_gamepad = evdev.InputDevice(udev.device_node)
    wooting_gamepad.grab()

    state = {
        evdev.ecodes.ecodes["EV_SYN"]: collections.defaultdict(int),
        evdev.ecodes.ecodes["EV_ABS"]: collections.defaultdict(int),
        evdev.ecodes.ecodes["EV_KEY"]: collections.defaultdict(int),
    }
    device = libwootility_device.get_device("/".join(sys.argv[1].split("/")[:-4]))

    mouse = Mouse(state, device)

    rgb_lighting = RGBLighting(device)

    tasks = asyncio.gather(
        mouse.run(),
        gamepad(
            wooting_gamepad,
            state,
            mouse,
            rgb_lighting,
            {
                evdev.ecodes.ecodes["BTN_SOUTH"]: "KEY_CAPSLOCK",
                evdev.ecodes.ecodes["BTN_TL"]: "KEY_LEFTCTRL",
                evdev.ecodes.ecodes["BTN_TR"]: "KEY_LEFTALT",
                evdev.ecodes.ecodes["BTN_EAST"]: "BTN_LEFT",
                evdev.ecodes.ecodes["BTN_NORTH"]: "BTN_MIDDLE",
                evdev.ecodes.ecodes["BTN_WEST"]: "BTN_RIGHT",
            },
            {evdev.ecodes.ecodes["ABS_HAT0X"]: ("BTN_BACK", "BTN_FORWARD")},
        ),
        rgb_lighting.run(),
    )

    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGTERM, tasks.cancel)

    loop.run_until_complete(tasks)

def read_stdin(stdin, _mask):
    """
    Call back to read from stdin
    """
    buf = stdin.read()
    if not buf:
        sys.exit()
    for i in buf.split("\n"):
        if i == "keyboard":
            yield i


def wooting_mouse_handler():
    """
    Wooting Mouse Handler
    """
    device = libwootility_device.get_device(
        pyudev.Devices.from_sys_path(pyudev.Context(), sys.argv[1])
        .find_parent("usb", "usb_device")
        .sys_path
    )

    sel = selectors.DefaultSelector()
    sel.register(sys.stdin, selectors.EVENT_READ, read_stdin)

    os.set_blocking(sys.stdin.fileno(), False)

    last = 0
    current_profile = 0
    while 1:
        now = time.monotonic()
        if current_profile == 0 and ((now - last) > 60):
            time_of_day(device)
            last = now

        events = sel.select(60)
        commands = ()
        for key, mask in events:
            callback = key.data
            commands = callback(key.fileobj, mask)

        for command in commands:
            if command == "keyboard":
                payload = libwootility.libwootility_feature.activate_profile(0)
                device.send_feature(payload)
                time.sleep(.1)
                time_of_day(device)

        payload = libwootility.libwootility_feature.get_current_keyboard_profile_index()
        current_profile = device.send_feature(payload)[7]
